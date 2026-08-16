import tkinter as tk
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT_DIR))

from config import theme
from widgets.agenda import AgendaWidget
from widgets.clock import ClockWidget
from widgets.analog_clock import AnalogClock


class Dashboard:

    def __init__(self, root):

        self.root = root
        self.root.configure(bg=theme.BACKGROUND)

        # Intern 2 x 2, maar visueel blijft het één doorlopend scherm.
        for column in range(2):
            self.root.grid_columnconfigure(column, weight=1, uniform="columns")

        for row in range(2):
            self.root.grid_rowconfigure(row, weight=1, uniform="rows")

        # Agenda - linksboven
        agenda_zone = tk.Frame(root, bg=theme.BACKGROUND)
        agenda_zone.grid(
            row=0, column=0, sticky="nsew",
            padx=(65, 35), pady=(55, 30)
        )

        agenda = AgendaWidget(agenda_zone)
        agenda.frame.pack(anchor="nw", fill="both", expand=True)

        # Klokken - rechtsboven.
        # Linker deel: digitale klok + datum.
        # Rechter deel: prominente analoge klok.
        clock_zone = tk.Frame(root, bg=theme.BACKGROUND)
        clock_zone.grid(
            row=0, column=1, sticky="nsew",
            padx=(35, 65), pady=(35, 20)
        )
        clock_zone.grid_columnconfigure(0, weight=1)
        clock_zone.grid_columnconfigure(1, weight=1)
        clock_zone.grid_rowconfigure(0, weight=1)

        digital_zone = tk.Frame(clock_zone, bg=theme.BACKGROUND)
        digital_zone.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        clock = ClockWidget(digital_zone)
        clock.frame.pack(fill="both", expand=True)

        analog_zone = tk.Frame(clock_zone, bg=theme.BACKGROUND)
        analog_zone.grid(row=0, column=1, sticky="nsew", padx=(10, 0))

        analog_clock = AnalogClock(analog_zone, size=330)
        analog_clock.pack(expand=True)

        # To-do zone - linksonder
        todo_zone = tk.Frame(root, bg=theme.BACKGROUND)
        todo_zone.grid(
            row=1, column=0, sticky="nsew",
            padx=(65, 35), pady=(30, 55)
        )

        tk.Label(
            todo_zone,
            text="TO-DO",
            font=(theme.FONT, 28, "bold"),
            fg=theme.GREEN,
            bg=theme.BACKGROUND,
        ).pack(anchor="nw")

        # Weer zone - rechtsonder
        weather_zone = tk.Frame(root, bg=theme.BACKGROUND)
        weather_zone.grid(
            row=1, column=1, sticky="nsew",
            padx=(35, 65), pady=(30, 55)
        )

        tk.Label(
            weather_zone,
            text="WEER",
            font=(theme.FONT, 28, "bold"),
            fg=theme.GREEN,
            bg=theme.BACKGROUND,
        ).pack(anchor="nw")
