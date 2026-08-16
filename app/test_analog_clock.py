import tkinter as tk

from widgets.analog_clock import AnalogClock
from config import theme


root = tk.Tk()
root.title("Tuus analoge klok")
root.configure(bg=theme.BACKGROUND)
root.geometry("500x500")

clock = AnalogClock(
    root,
    size=320
)

clock.pack(
    expand=True
)

root.mainloop()
