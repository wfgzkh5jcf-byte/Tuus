import tkinter as tk
from datetime import datetime
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT_DIR))

from config import theme


class ClockWidget:

    def __init__(self, parent):

        self.frame = tk.Frame(
            parent,
            bg=theme.BACKGROUND
        )

        self.time_label = tk.Label(
            self.frame,
            text="00:00",
            font=(theme.FONT, 78, "bold"),
            fg=theme.TEXT,
            bg=theme.BACKGROUND,
        )
        self.time_label.pack(
            pady=(10, 10)
        )

        self.date_label = tk.Label(
            self.frame,
            text="",
            font=(theme.FONT, 20),
            fg=theme.GREEN,
            bg=theme.BACKGROUND,
        )
        self.date_label.pack()

        self.update_clock()

    def update_clock(self):

        now = datetime.now()

        dagen = [
            "Maandag", "Dinsdag", "Woensdag",
            "Donderdag", "Vrijdag", "Zaterdag", "Zondag"
        ]

        maanden = [
            "januari", "februari", "maart", "april",
            "mei", "juni", "juli", "augustus",
            "september", "oktober", "november", "december"
        ]

        datum = (
            f"{dagen[now.weekday()]} "
            f"{now.day} "
            f"{maanden[now.month - 1]} "
            f"{now.year}"
        )

        self.time_label.config(
            text=now.strftime("%H:%M")
        )

        self.date_label.config(
            text=datum
        )

        self.frame.after(
            1000,
            self.update_clock
        )

