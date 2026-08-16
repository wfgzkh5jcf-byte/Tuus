import tkinter as tk
import sys
from pathlib import Path

# Zorg dat config/theme.py gevonden kan worden
ROOT_DIR = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT_DIR))

from config import theme


class Panel(tk.Frame):
    def __init__(self, parent, title=""):
        super().__init__(
            parent,
            bg=theme.PANEL,
            highlightbackground=theme.BORDER,
            highlightthickness=1,
            bd=0,
        )

        self.configure(
            padx=theme.PANEL_PADDING,
            pady=theme.PANEL_PADDING,
        )

        if title:
            self.title_label = tk.Label(
                self,
                text=title,
                font=(theme.FONT, theme.TITLE_SIZE, "bold"),
                fg=theme.GREEN,
                bg=theme.PANEL,
                anchor="w",
            )
            self.title_label.pack(
                fill="x",
                pady=(0, 18),
            )

        self.content = tk.Frame(
            self,
            bg=theme.PANEL,
        )
        self.content.pack(
            fill="both",
            expand=True,
        )
