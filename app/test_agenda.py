import tkinter as tk
from widgets.agenda import AgendaWidget

root = tk.Tk()
root.title("Agenda test")
root.geometry("700x450")
root.configure(bg="#0B1114")

agenda = AgendaWidget(root)
agenda.frame.pack(expand=True, fill="both", padx=20, pady=20)

root.mainloop()
