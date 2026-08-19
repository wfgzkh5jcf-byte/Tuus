#!/usr/bin/env python3
import glob
import os
import select
import struct
import subprocess
import time
from datetime import datetime

TOUCH_NAME = "Silicon Integrated System Co. SiS HID Touch Controller"
OUTPUT = "HDMI-A-1"
SLEEP_HOUR = 22
WAKE_HOUR = 6
WAKE_MINUTE = 30
TOUCH_WAKE_SECONDS = 5 * 60
CHECK_SECONDS = 1
EV_KEY = 0x01
BTN_TOUCH = 330
EVENT_STRUCT = struct.Struct("llHHi")

ENV = os.environ.copy()
ENV["XDG_RUNTIME_DIR"] = "/run/user/1000"
ENV["WAYLAND_DISPLAY"] = "wayland-0"


def is_night(now=None):
    now = now or datetime.now()
    minutes = now.hour * 60 + now.minute
    return minutes >= SLEEP_HOUR * 60 or minutes < WAKE_HOUR * 60 + WAKE_MINUTE


def display(on):
    subprocess.run(
        ["/usr/bin/wlopm", "--on" if on else "--off", OUTPUT],
        env=ENV,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )


def input_name(path):
    event = os.path.basename(path)
    try:
        with open(f"/sys/class/input/{event}/device/name", encoding="utf-8") as f:
            return f.read().strip()
    except OSError:
        return ""


def find_touch():
    for path in sorted(glob.glob("/dev/input/event*")):
        if input_name(path) == TOUCH_NAME:
            return path
    return None


def open_touch():
    while True:
        path = find_touch()
        if path:
            try:
                return open(path, "rb", buffering=0)
            except OSError:
                pass
        time.sleep(5)


def main():
    touch = open_touch()
    awake_until = 0.0
    display(not is_night())

    while True:
        try:
            readable, _, _ = select.select([touch], [], [], CHECK_SECONDS)
            if readable:
                data = touch.read(EVENT_STRUCT.size)
                if len(data) != EVENT_STRUCT.size:
                    raise OSError("touch device disconnected")
                _, _, event_type, code, value = EVENT_STRUCT.unpack(data)
                if event_type == EV_KEY and code == BTN_TOUCH and value == 1 and is_night():
                    awake_until = time.monotonic() + TOUCH_WAKE_SECONDS
                    display(True)

            if is_night():
                if awake_until and time.monotonic() >= awake_until:
                    awake_until = 0.0
                    display(False)
            else:
                if awake_until:
                    awake_until = 0.0
                display(True)
        except (OSError, ValueError):
            try:
                touch.close()
            except Exception:
                pass
            touch = open_touch()


if __name__ == "__main__":
    main()
