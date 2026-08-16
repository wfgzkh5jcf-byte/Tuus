import tkinter as tk
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT_DIR))

from config import theme
from widgets.agenda import AgendaWidget
from widgets.clock import ClockWidget


class Dashboard:

    def __init__(self, root):

        self.root = root
        self.root.configure(
            bg=theme.BACKGROUND
        )

        # Intern nog steeds 2 x 2,
        # maar visueel is er geen raster.
        for column in range(2):
            self.root.grid_columnconfigure(
                column,
                weight=1,
                uniform="columns"
            )

        for row in range(2):
            self.root.grid_rowconfigure(
                row,
                weight=1,
                uniform="rows"
            )

        # Agenda - linksboven
        agenda_zone = tk.Frame(
            root,
            bg=theme.BACKGROUND
        )
        agenda_zone.grid(
            row=0,
            column=0,
            sticky="nsew",
            padx=(65, 35),
            pady=(55, 30)
        )

        agenda = AgendaWidget(
            agenda_zone
        )
        agenda.frame.pack(
            anchor="nw",
            fill="both",
            expand=True
        )

        # Klok - rechtsboven
        clock_zone = tk.Frame(
            root,
            bg=theme.BACKGROUND
        )
        clock_zone.grid(
            row=0,
            column=1,
            sticky="nsew",
            padx=(35, 65),
            pady=(55, 30)
        )

        clock = ClockWidget(
            clock_zone
        )
        clock.frame.pack(
            fill="both",
            expand=True
        )

        # To-do zone - linksonder
        todo_zone = tk.Frame(
            root,
            bg=theme.BACKGROUND
        )
        todo_zone.grid(
            row=1,
            column=0,
            sticky="nsew",
            padx=(65, 35),
            pady=(30, 55)
        )

        tk.Label(
            todo_zone,
            text="TO-DO",
            font=(theme.FONT, 28, "bold"),
            fg=theme.GREEN,
            bg=theme.BACKGROUND,
        ).pack(anchor="nw")

        # Weer zone - rechtsonder
        weather_zone = tk.Frame(
            root,
            bg=theme.BACKGROUND
        )
        weather_zone.grid(
            row=1,
            column=1,
            sticky="nsew",
            padx=(35, 65),
            pady=(30, 55)
        )

        tk.Label(
            weather_zone,
            text="WEER",
            font=(theme.FONT, 28, "bold"),
            fg=theme.GREEN,
            bg=theme.BACKGROUND,
        ).pack(anchor="nw")
