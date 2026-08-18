#!/usr/bin/env python3
import json
import os
import uuid
from datetime import date, datetime, timedelta
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

from caldav import DAVClient

ROOT = Path(__file__).resolve().parents[1]
WEB_DIR = ROOT / "web"
CONFIG = Path.home() / ".tuus_icloud"
TODO_STORE = Path.home() / ".tuus_todos.json"
TZ = ZoneInfo("Europe/Amsterdam")
CALENDAR_NAME = "Thuis/werk"
WEATHER_LAT = 52.72
WEATHER_LON = 6.25

# Huishoudtaken. Aquarium en filter wisselen elkaar om de 14 dagen af,
# waardoor elk ongeveer iedere 4 weken terugkomt.
MAINTENANCE_ANCHOR = date(2026, 8, 18)  # aquarium
MAINTENANCE_INTERVAL_DAYS = 14

# AREA-adres staat klaar voor koppeling. De publieke site/app gebruikt Ximmio,
# maar de provider-identificatie is nog niet betrouwbaar genoeg vastgesteld om
# automatisch afvaldata op te halen zonder risico op verkeerde ophaaldagen.
AREA_POSTCODE = "7961LX"
AREA_HOUSE_NUMBER = "11"


def load_config():
    cfg = {}
    with CONFIG.open(encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if line and "=" in line:
                key, value = line.split("=", 1)
                cfg[key] = value
    return cfg


def as_local_datetime(value):
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=TZ)
        return value.astimezone(TZ)
    return None


def get_agenda():
    cfg = load_config()
    client = DAVClient(url="https://caldav.icloud.com/", username=cfg["APPLE_ID"], password=cfg["APPLE_APP_PASSWORD"])
    calendars = client.principal().calendars()
    calendar = next((cal for cal in calendars if cal.name == CALENDAR_NAME), None)
    if calendar is None:
        raise RuntimeError(f"Agenda '{CALENDAR_NAME}' niet gevonden")
    now = datetime.now(TZ)
    today = now.date()
    last_day = today + timedelta(days=1)
    query_start = datetime.combine(today, datetime.min.time(), TZ)
    query_end = datetime.combine(last_day + timedelta(days=1), datetime.min.time(), TZ)
    found = calendar.search(start=query_start, end=query_end, event=True, expand=True)
    items = []
    seen = set()
    for event in found:
        try:
            vevent = event.vobject_instance.vevent
            summary = str(getattr(vevent, "summary", "Zonder titel").value)
            start_value = vevent.dtstart.value
            uid = str(getattr(vevent, "uid", "").value) if hasattr(vevent, "uid") else ""
            if isinstance(start_value, datetime):
                local = as_local_datetime(start_value)
                event_day = local.date()
                if event_day < today or event_day > last_day:
                    continue
                item = {"title": summary, "date": event_day.isoformat(), "all_day": False, "time": local.strftime("%H:%M")}
                identity = (uid, item["date"], item["time"], summary)
            elif isinstance(start_value, date):
                event_day = start_value
                if event_day < today or event_day > last_day:
                    continue
                item = {"title": summary, "date": event_day.isoformat(), "all_day": True, "time": None}
                identity = (uid, item["date"], "all-day", summary)
            else:
                continue
            if identity not in seen:
                seen.add(identity)
                items.append(item)
        except Exception as exc:
            print(f"Agenda-item overgeslagen: {exc}")
    items.sort(key=lambda x: (x["date"], x["all_day"] is False, x["time"] or "00:00", x["title"].lower()))
    return {"calendar": CALENDAR_NAME, "today": today.isoformat(), "tomorrow": last_day.isoformat(), "events": items}


def get_weather():
    fields = "temperature_2m,relative_humidity_2m,apparent_temperature,weather_code,wind_speed_10m,wind_direction_10m,is_day"
    url = ("https://api.open-meteo.com/v1/forecast"
           f"?latitude={WEATHER_LAT}&longitude={WEATHER_LON}"
           f"&current={fields}&temperature_unit=celsius&wind_speed_unit=kmh&timezone=Europe%2FAmsterdam")
    req = Request(url, headers={"User-Agent": "Tuus-home-dashboard/1.0"})
    with urlopen(req, timeout=8) as response:
        data = json.load(response)
    current = data.get("current", {})
    return {
        "location": "Ruinerwold",
        "updated": current.get("time"),
        "temperature": current.get("temperature_2m"),
        "apparent_temperature": current.get("apparent_temperature"),
        "humidity": current.get("relative_humidity_2m"),
        "weather_code": current.get("weather_code"),
        "wind_speed": current.get("wind_speed_10m"),
        "wind_direction": current.get("wind_direction_10m"),
        "is_day": current.get("is_day"),
    }


def load_todo_store():
    if not TODO_STORE.exists():
        return {"tasks": []}
    try:
        with TODO_STORE.open(encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict) or not isinstance(data.get("tasks"), list):
            raise ValueError("ongeldig todo-bestand")
        return data
    except Exception as exc:
        print(f"Todo-opslag kon niet worden gelezen: {exc}")
        return {"tasks": []}


def save_todo_store(store):
    tmp = TODO_STORE.with_suffix(".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(store, f, ensure_ascii=False, indent=2)
    tmp.replace(TODO_STORE)


def has_open_rule(tasks, rule_key):
    return any(t.get("rule_key") == rule_key and not t.get("completed_date") for t in tasks)


def add_generated_task(tasks, title, due, rule_key, kind="recurring", marker=None):
    identity = f"{rule_key}:{due.isoformat()}"
    if any(t.get("identity") == identity for t in tasks):
        return
    if has_open_rule(tasks, rule_key):
        return
    tasks.append({
        "id": uuid.uuid4().hex,
        "identity": identity,
        "title": title,
        "due_date": due.isoformat(),
        "created_date": due.isoformat(),
        "completed_date": None,
        "kind": kind,
        "rule_key": rule_key,
        "marker": marker,
    })


def ensure_recurring_tasks(store, today):
    tasks = store["tasks"]

    # Planten: elke zondag. Als een vorige planten-taak nog openstaat,
    # komt er niet nog een tweede identieke taak bij.
    if today.weekday() == 6:
        add_generated_task(tasks, "Planten water geven", today, "plants-weekly")

    # Aquarium / filter: om en om iedere 14 dagen vanaf de vaste ankerdatum.
    if today >= MAINTENANCE_ANCHOR:
        delta_days = (today - MAINTENANCE_ANCHOR).days
        if delta_days % MAINTENANCE_INTERVAL_DAYS == 0:
            slot = delta_days // MAINTENANCE_INTERVAL_DAYS
            if slot % 2 == 0:
                add_generated_task(tasks, "Aquarium schoonmaken", today, "aquarium-monthly")
            else:
                add_generated_task(tasks, "Filter schoonmaken", today, "filter-monthly")

    save_todo_store(store)


def cleanup_old_completed(store, today):
    before = len(store["tasks"])
    store["tasks"] = [t for t in store["tasks"] if not t.get("completed_date") or t.get("completed_date") == today.isoformat()]
    if len(store["tasks"]) != before:
        save_todo_store(store)


def todo_sort_key(task, today):
    completed = bool(task.get("completed_date"))
    due = date.fromisoformat(task["due_date"])
    # Afval (straks) mag altijd bovenaan, daarna doorgeschoven open taken,
    # dan taken van vandaag, dan afgevinkt.
    waste_rank = 0 if task.get("kind") == "waste" and not completed else 1
    overdue_rank = 0 if due < today and not completed else 1
    completed_rank = 1 if completed else 0
    return (waste_rank, overdue_rank, completed_rank, task.get("due_date", ""), task.get("created_date", ""), task.get("title", "").lower())


def get_todos():
    today = datetime.now(TZ).date()
    store = load_todo_store()
    cleanup_old_completed(store, today)
    ensure_recurring_tasks(store, today)
    visible = []
    for task in store["tasks"]:
        due = date.fromisoformat(task["due_date"])
        if task.get("completed_date") == today.isoformat() or (not task.get("completed_date") and due <= today):
            item = dict(task)
            item["overdue"] = due < today and not item.get("completed_date")
            visible.append(item)
    visible.sort(key=lambda t: todo_sort_key(t, today))
    done = sum(1 for t in visible if t.get("completed_date"))
    return {
        "today": today.isoformat(),
        "tasks": visible,
        "done": done,
        "total": len(visible),
        "area": {"postcode": AREA_POSTCODE, "house_number": AREA_HOUSE_NUMBER, "status": "provider-id-pending"},
    }


def add_manual_todo(title):
    title = " ".join(str(title or "").split()).strip()
    if not title:
        raise ValueError("Taak mag niet leeg zijn")
    if len(title) > 80:
        raise ValueError("Taak is te lang")
    today = datetime.now(TZ).date().isoformat()
    store = load_todo_store()
    task = {
        "id": uuid.uuid4().hex,
        "identity": None,
        "title": title,
        "due_date": today,
        "created_date": today,
        "completed_date": None,
        "kind": "manual",
        "rule_key": None,
        "marker": None,
    }
    store["tasks"].append(task)
    save_todo_store(store)
    return task


def toggle_todo(task_id, completed):
    store = load_todo_store()
    today = datetime.now(TZ).date().isoformat()
    for task in store["tasks"]:
        if task.get("id") == task_id:
            task["completed_date"] = today if completed else None
            save_todo_store(store)
            return task
    raise KeyError("Taak niet gevonden")


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WEB_DIR), **kwargs)

    def end_headers(self):
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()

    def send_json(self, payload, status=200):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def read_json_body(self):
        length = int(self.headers.get("Content-Length", "0") or 0)
        if length <= 0:
            return {}
        raw = self.rfile.read(length)
        return json.loads(raw.decode("utf-8"))

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/api/agenda":
            try:
                self.send_json(get_agenda())
            except Exception as exc:
                self.send_json({"error": str(exc)}, 500)
            return
        if path == "/api/weather":
            try:
                self.send_json(get_weather())
            except Exception as exc:
                self.send_json({"error": str(exc)}, 500)
            return
        if path == "/api/todos":
            try:
                self.send_json(get_todos())
            except Exception as exc:
                self.send_json({"error": str(exc)}, 500)
            return
        super().do_GET()

    def do_POST(self):
        path = urlparse(self.path).path
        try:
            payload = self.read_json_body()
            if path == "/api/todos":
                task = add_manual_todo(payload.get("title"))
                self.send_json(task, 201)
                return
            if path == "/api/todos/toggle":
                task = toggle_todo(str(payload.get("id", "")), bool(payload.get("completed")))
                self.send_json(task)
                return
            self.send_json({"error": "Niet gevonden"}, 404)
        except KeyError as exc:
            self.send_json({"error": str(exc)}, 404)
        except Exception as exc:
            self.send_json({"error": str(exc)}, 400)


if __name__ == "__main__":
    os.chdir(WEB_DIR)
    server = ThreadingHTTPServer(("127.0.0.1", 8765), Handler)
    print("Tuus server: http://127.0.0.1:8765")
    print(f"Agenda: {CALENDAR_NAME} (alleen lezen)")
    print("Weer: Ruinerwold via Open-Meteo")
    print(f"TO DO opslag: {TODO_STORE}")
    print(f"AREA-adres voorbereid: {AREA_POSTCODE} {AREA_HOUSE_NUMBER}")
    server.serve_forever()
