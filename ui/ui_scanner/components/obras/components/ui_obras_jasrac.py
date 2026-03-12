import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from threading import Thread, Event

from logic.logic_scanner.logic_obrasSGAE import scanner

class ScannerObrasJASRAC(ttk.Frame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        main = ttk.Frame(self)
        main.pack(fill="both", expand=True)
        
        frm = ttk.Frame(main, padding=10)
        frm.pack(fill="x")
        frm.grid_columnconfigure(1, weight=1)

        ttk.Label(self, text="Obras JASRAC - EN CONSTRUCCIÓN").pack(padx=10, pady=10)