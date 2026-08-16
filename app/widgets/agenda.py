import tkinter as tk
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT_DIR))

from config import theme


class AgendaWidget:

    def __init__(self, parent):

        self.frame = tk.Frame(
            parent,
            bg=theme.BACKGROUND
        )

        title = tk.Label(
            self.frame,
            text="AGENDA",
            font=(theme.FONT, 28, "bold"),
            fg=theme.GREEN,
            bg=theme.BACKGROUND,
        )
        title.pack(
            anchor="w",
            pady=(0, 25)
        )

        afspraken = [
            ("09:00", "Tandarts"),
            ("14:00", "Boodschappen"),
            ("19:30", "Familie BBQ"),
        ]

        for tijd, tekst in afspraken:

            regel = tk.Frame(
                self.frame,
                bg=theme.BACKGROUND
            )
            regel.pack(
                fill="x",
                pady=8
            )

            tk.Label(
                regel,
                text=tijd,
                width=7,
                anchor="w",
                font=(theme.FONT, 20, "bold"),
                fg=theme.ORANGE,
                bg=theme.BACKGROUND,
            ).pack(side="left")

            tk.Label(
                regel,
                text=tekst,
                anchor="w",
                font=(theme.FONT, 20),
                fg=theme.TEXT,
                bg=theme.BACKGROUND,
            ).pack(side="left")
