#!/usr/bin/env python3
import json
import os
import uuid
from datetime import date, datetime, timedelta
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

from caldav import DAVClient

ROOT = Path(__file__).resolve().parents[1]
WEB_DIR = ROOT / "web"
CONFIG = Path.home() / ".tuus_icloud"
TODO_STORE = Path.home() / ".tuus_todos.json"
AREA_CACHE = Path.home() / ".tuus_area_cache.json"
TZ = ZoneInfo("Europe/Amsterdam")
CALENDAR_NAME = "Thuis/werk"
WEATHER_LAT = 52.72
WEATHER_LON = 6.25

# Huishoudtaken. Aquarium en filter wisselen elkaar om de 14 dagen af,
# waardoor elk ongeveer iedere 4 weken terugkomt.
MAINTENANCE_ANCHOR = date(2026, 8, 18)  # aquarium
MAINTENANCE_INTERVAL_DAYS = 14

# AREA gebruikt de Ximmio-afvalkalender.
AREA_POSTCODE = "7961LX"
AREA_HOUSE_NUMBER = "11"
AREA_COMPANY_CODE = "adc418da-d19b-11e5-ab30-625662870761"
AREA_API = "https://wasteapi.ximmio.com/api"
AREA_CACHE_HOURS = 6


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


def ximmio_post(endpoint, fields):
    body = urlencode(fields).encode("utf-8")
    req = Request(
        f"{AREA_API}/{endpoint}",
        data=body,
        headers={
            "User-Agent": "Tuus-home-dashboard/1.0",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        },
        method="POST",
    )
    with urlopen(req, timeout=12) as response:
        return json.load(response)


def fetch_area_calendar():
    address_data = ximmio_post("FetchAdress", {
        "postCode": AREA_POSTCODE,
        "houseNumber": AREA_HOUSE_NUMBER,
        "companyCode": AREA_COMPANY_CODE,
    })
    addresses = address_data.get("dataList") or []
    if not addresses:
        raise RuntimeError("AREA-adres niet gevonden")
    address = addresses[0]
    start = datetime.now(TZ).date()
    end = start + timedelta(days=70)
    cal_data = ximmio_post("GetCalendar", {
        "uniqueAddressID": address["UniqueId"],
        "startDate": start.isoformat(),
        "endDate": end.isoformat(),
        "companyCode": AREA_COMPANY_CODE,
        "community": address.get("Community", ""),
    })
    collections = []
    for waste_type in cal_data.get("dataList") or []:
        label = str(waste_type.get("_pickupTypeText") or waste_type.get("pickupTypeText") or "Afval").strip()
        for raw_date in waste_type.get("pickupDates") or []:
            try:
                pickup = datetime.fromisoformat(str(raw_date).replace("Z", "+00:00")).date()
            except Exception:
                pickup = datetime.strptime(str(raw_date)[:10], "%Y-%m-%d").date()
            collections.append({"date": pickup.isoformat(), "label": label})
    result = {
        "fetched_at": datetime.now(TZ).isoformat(),
        "address": {"postcode": AREA_POSTCODE, "house_number": AREA_HOUSE_NUMBER},
        "collections": collections,
    }
    try:
        with AREA_CACHE.open("w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
    except Exception as exc:
        print(f"AREA-cache kon niet worden opgeslagen: {exc}")
    return result


def get_area_calendar():
    if AREA_CACHE.exists():
        try:
            with AREA_CACHE.open(encoding="utf-8") as f:
                cached = json.load(f)
            fetched = datetime.fromisoformat(cached["fetched_at"])
            if fetched.tzinfo is None:
                fetched = fetched.replace(tzinfo=TZ)
            if datetime.now(TZ) - fetched.astimezone(TZ) < timedelta(hours=AREA_CACHE_HOURS):
                return cached
        except Exception as exc:
            print(f"AREA-cache genegeerd: {exc}")
    return fetch_area_calendar()


def classify_waste(label):
    text = str(label or "").strip().casefold()
    # AREA/Ximmio levert voor dit adres ook korte kleurcodes zoals GREEN.
    if text in ("green", "groen") or any(x in text for x in ("gft", "groente", "tuinafval", "organisch")):
        return "green", "Groene container buitenzetten", "area-gft"
    if text in ("orange", "oranje") or any(x in text for x in ("pmd", "plastic", "verpakking", "drankkarton", "metaal")):
        return "orange", "Oranje container buitenzetten", "area-pmd"
    if text in ("blue", "blauw") or any(x in text for x in ("papier", "karton")):
        return "blue", "Blauwe container buitenzetten", "area-paper"
    if text in ("gray", "grey", "grijs") or any(x in text for x in ("rest", "grijs")):
        return "gray", "Grijze container buitenzetten", "area-rest"
    return None


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
    if today.weekday() == 6:
        add_generated_task(tasks, "Planten water geven", today, "plants-weekly")
    if today >= MAINTENANCE_ANCHOR:
        delta_days = (today - MAINTENANCE_ANCHOR).days
        if delta_days % MAINTENANCE_INTERVAL_DAYS == 0:
            slot = delta_days // MAINTENANCE_INTERVAL_DAYS
            if slot % 2 == 0:
                add_generated_task(tasks, "Aquarium schoonmaken", today, "aquarium-monthly")
            else:
                add_generated_task(tasks, "Filter schoonmaken", today, "filter-monthly")


def ensure_area_tasks(store, today):
    calendar = get_area_calendar()
    tomorrow = today + timedelta(days=1)
    for entry in calendar.get("collections", []):
        if entry.get("date") != tomorrow.isoformat():
            continue
        classified = classify_waste(entry.get("label", ""))
        if not classified:
            print(f"Onbekende AREA-afvalstroom: {entry.get('label')}")
            continue
        marker, title, rule_key = classified
        identity_key = f"{rule_key}-pickup-{tomorrow.isoformat()}"
        add_generated_task(store["tasks"], title, today, identity_key, kind="waste", marker=marker)
    return {"status": "ok", "fetched_at": calendar.get("fetched_at")}


def cleanup_old_completed(store, today):
    before = len(store["tasks"])
    store["tasks"] = [t for t in store["tasks"] if not t.get("completed_date") or t.get("completed_date") == today.isoformat()]
    return len(store["tasks"]) != before


def todo_sort_key(task, today):
    completed = bool(task.get("completed_date"))
    due = date.fromisoformat(task["due_date"])
    waste_rank = 0 if task.get("kind") == "waste" and not completed else 1
    overdue_rank = 0 if due < today and not completed else 1
    completed_rank = 1 if completed else 0
    return (waste_rank, overdue_rank, completed_rank, task.get("due_date", ""), task.get("created_date", ""), task.get("title", "").lower())


def get_todos():
    today = datetime.now(TZ).date()
    store = load_todo_store()
    changed = cleanup_old_completed(store, today)
    before = json.dumps(store, sort_keys=True)
    ensure_recurring_tasks(store, today)
    area_status = {"status": "unavailable"}
    try:
        area_status = ensure_area_tasks(store, today)
    except Exception as exc:
        area_status = {"status": "error", "error": str(exc)}
        print(f"AREA niet bereikbaar: {exc}")
    if changed or json.dumps(store, sort_keys=True) != before:
        save_todo_store(store)
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
        "area": {
            "postcode": AREA_POSTCODE,
            "house_number": AREA_HOUSE_NUMBER,
            **area_status,
        },
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
    print(f"AREA: {AREA_POSTCODE} {AREA_HOUSE_NUMBER} via Ximmio")
    server.serve_forever()
