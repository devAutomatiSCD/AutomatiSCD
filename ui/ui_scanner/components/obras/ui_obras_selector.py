import tkinter as tk
from tkinter import ttk

class ObrasSelector(ttk.Frame):
    def __init__(self, master, on_select, **kwargs):
        super().__init__(master, **kwargs)

        mb = ttk.Menubutton(self, text="Obras")
        menu = tk.Menu(mb, tearoff=0)
        mb["menu"] = menu

        sociedades = sorted([
            "AFITAP","AGADU","APDAYC","CISNET","IMRO","JASRAC","KODA","SACEM",
            "SACM","SADAIC","SESAC","SGAE","STIM","SUISA","TONO","PEER","MSG",
            "MESAM","ABRAMUS","APRA","KOMCA"
        ])

        for s in sociedades:
            menu.add_command(label=s, command=lambda s=s: on_select(s))

        mb.grid(row=0, column=0, sticky="w")
