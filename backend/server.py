#!/usr/bin/env python3
import json
import os
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
TZ = ZoneInfo("Europe/Amsterdam")
CALENDAR_NAME = "Thuis/werk"
# Ruinerwold / Buitenhuizerweg-omgeving. Voor het weer is plaatsniveau ruim voldoende.
WEATHER_LAT = 52.72
WEATHER_LON = 6.25


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
    now = datetime.now(TZ); today = now.date(); last_day = today + timedelta(days=1)
    query_start = datetime.combine(today, datetime.min.time(), TZ)
    query_end = datetime.combine(last_day + timedelta(days=1), datetime.min.time(), TZ)
    found = calendar.search(start=query_start, end=query_end, event=True, expand=True)
    items=[]; seen=set()
    for event in found:
        try:
            vevent=event.vobject_instance.vevent; summary=str(getattr(vevent,"summary","Zonder titel").value); start_value=vevent.dtstart.value
            uid=str(getattr(vevent,"uid","").value) if hasattr(vevent,"uid") else ""
            if isinstance(start_value,datetime):
                local=as_local_datetime(start_value); event_day=local.date()
                if event_day<today or event_day>last_day: continue
                item={"title":summary,"date":event_day.isoformat(),"all_day":False,"time":local.strftime("%H:%M")}; identity=(uid,item["date"],item["time"],summary)
            elif isinstance(start_value,date):
                event_day=start_value
                if event_day<today or event_day>last_day: continue
                item={"title":summary,"date":event_day.isoformat(),"all_day":True,"time":None}; identity=(uid,item["date"],"all-day",summary)
            else: continue
            if identity not in seen: seen.add(identity); items.append(item)
        except Exception as exc: print(f"Agenda-item overgeslagen: {exc}")
    items.sort(key=lambda x:(x["date"],x["all_day"] is False,x["time"] or "00:00",x["title"].lower()))
    return {"calendar":CALENDAR_NAME,"today":today.isoformat(),"tomorrow":last_day.isoformat(),"events":items}


def get_weather():
    fields = "temperature_2m,relative_humidity_2m,apparent_temperature,weather_code,wind_speed_10m,wind_direction_10m,is_day"
    url = ("https://api.open-meteo.com/v1/forecast"
           f"?latitude={WEATHER_LAT}&longitude={WEATHER_LON}"
           f"&current={fields}&temperature_unit=celsius&wind_speed_unit=kmh&timezone=Europe%2FAmsterdam")
    req = Request(url, headers={"User-Agent":"Tuus-home-dashboard/1.0"})
    with urlopen(req, timeout=8) as response:
        data = json.load(response)
    current = data.get("current", {})
    return {"location":"Ruinerwold","updated":current.get("time"),"temperature":current.get("temperature_2m"),"apparent_temperature":current.get("apparent_temperature"),"humidity":current.get("relative_humidity_2m"),"weather_code":current.get("weather_code"),"wind_speed":current.get("wind_speed_10m"),"wind_direction":current.get("wind_direction_10m"),"is_day":current.get("is_day")}


class Handler(SimpleHTTPRequestHandler):
    def __init__(self,*args,**kwargs): super().__init__(*args,directory=str(WEB_DIR),**kwargs)
    def end_headers(self):
        self.send_header("Cache-Control","no-store, no-cache, must-revalidate, max-age=0"); self.send_header("Pragma","no-cache"); self.send_header("Expires","0"); super().end_headers()
    def send_json(self,payload,status=200):
        body=json.dumps(payload,ensure_ascii=False).encode("utf-8"); self.send_response(status); self.send_header("Content-Type","application/json; charset=utf-8"); self.send_header("Content-Length",str(len(body))); self.end_headers(); self.wfile.write(body)
    def do_GET(self):
        path=urlparse(self.path).path
        if path=="/api/agenda":
            try: self.send_json(get_agenda())
            except Exception as exc: self.send_json({"error":str(exc)},500)
            return
        if path=="/api/weather":
            try: self.send_json(get_weather())
            except Exception as exc: self.send_json({"error":str(exc)},500)
            return
        super().do_GET()


if __name__=="__main__":
    os.chdir(WEB_DIR); server=ThreadingHTTPServer(("127.0.0.1",8765),Handler)
    print("Tuus server: http://127.0.0.1:8765"); print(f"Agenda: {CALENDAR_NAME} (alleen lezen)"); print("Weer: Ruinerwold via Open-Meteo")
    server.serve_forever()
