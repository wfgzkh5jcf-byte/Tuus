import tkinter as tk
from widgets.clock import ClockWidget

root = tk.Tk()
root.title("Test klok")
root.geometry("800x400")
root.configure(bg="#0B1114")

clock = ClockWidget(root)
clock.frame.pack(expand=True, fill="both")

root.mainloop()
