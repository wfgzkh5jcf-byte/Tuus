import tkinter as tk

from dashboard import Dashboard

root = tk.Tk()
root.title("Tuus Dashboard")
root.attributes("-fullscreen", True)

Dashboard(root)

root.mainloop()
