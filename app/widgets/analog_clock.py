import tkinter as tk
from datetime import datetime
import math
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT_DIR))

from config import theme


class AnalogClock(tk.Canvas):
    def __init__(self, parent, size=280):
        super().__init__(
            parent,
            width=size,
            height=size,
            bg=theme.BACKGROUND,
            highlightthickness=0,
            bd=0,
        )

        self.size = size
        self.center = size / 2
        self.radius = size * 0.43

        self.draw_face()
        self.update_clock()

    def point_on_circle(self, angle_degrees, radius):
        angle = math.radians(angle_degrees - 90)

        x = self.center + math.cos(angle) * radius
        y = self.center + math.sin(angle) * radius

        return x, y

    def draw_face(self):
        # Minuut- en uurmarkeringen
        for minute in range(60):
            angle = minute * 6

            if minute % 5 == 0:
                outer = self.radius
                inner = self.radius - 15
                width = 3
                color = theme.TEXT
            else:
                outer = self.radius
                inner = self.radius - 7
                width = 1
                color = theme.TEXT_MUTED

            x1, y1 = self.point_on_circle(angle, inner)
            x2, y2 = self.point_on_circle(angle, outer)

            self.create_line(
                x1,
                y1,
                x2,
                y2,
                fill=color,
                width=width,
                capstyle=tk.ROUND,
            )

        # Cijfers 1 t/m 12
        for hour in range(1, 13):
            angle = hour * 30

            x, y = self.point_on_circle(
                angle,
                self.radius - 35
            )

            self.create_text(
                x,
                y,
                text=str(hour),
                fill=theme.TEXT,
                font=(theme.FONT, 18, "bold"),
            )

    def update_clock(self):
        now = datetime.now()

        hours = now.hour % 12
        minutes = now.minute
        seconds = now.second + now.microsecond / 1_000_000

        # Vloeiende hoeken
        second_angle = seconds * 6
        minute_angle = (minutes + seconds / 60) * 6
        hour_angle = (hours + minutes / 60 + seconds / 3600) * 30

        self.delete("hands")

        # Uurwijzer
        hour_x, hour_y = self.point_on_circle(
            hour_angle,
            self.radius * 0.50
        )

        self.create_line(
            self.center,
            self.center,
            hour_x,
            hour_y,
            fill=theme.TEXT,
            width=8,
            capstyle=tk.ROUND,
            tags="hands",
        )

        # Minuutwijzer
        minute_x, minute_y = self.point_on_circle(
            minute_angle,
            self.radius * 0.72
        )

        self.create_line(
            self.center,
            self.center,
            minute_x,
            minute_y,
            fill=theme.TEXT,
            width=5,
            capstyle=tk.ROUND,
            tags="hands",
        )

        # Secondewijzer
        second_x, second_y = self.point_on_circle(
            second_angle,
            self.radius * 0.82
        )

        self.create_line(
            self.center,
            self.center,
            second_x,
            second_y,
            fill=theme.ORANGE,
            width=2,
            capstyle=tk.ROUND,
            tags="hands",
        )

        # Middelpunt
        center_radius = 7

        self.create_oval(
            self.center - center_radius,
            self.center - center_radius,
            self.center + center_radius,
            self.center + center_radius,
            fill=theme.ORANGE,
            outline="",
            tags="hands",
        )

        # ~30 updates per seconde: vloeiend genoeg en licht voor de Pi
        self.after(33, self.update_clock)
