import tkinter as tk
from tkinter import ttk

from ui.ui_scanner.components.conexos.ui_conexos import ScannerConexos
from ui.ui_scanner.components.obras.ui_obras_selector import ObrasSelector
from ui.ui_scanner.components.obras.ui_obras_main import ObrasMain
from ui.ui_scanner.components.cuesheets.ui_cue_sheets_selector import CueSheetsSelector
from ui.ui_scanner.components.cuesheets.ui_cue_sheets_main import CueSheetsMain


class ScannerContainer(ttk.Frame):
    def __init__(self, master, on_volver_menu, **kwargs):
        super().__init__(master, **kwargs)

        # Layout del container
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)
        self.grid_rowconfigure(2, weight=1)

        ttk.Button(self, text="⬅ Volver al menú", command=on_volver_menu).grid(
            row=0, column=0, columnspan=2, sticky="w", padx=10, pady=(10, 0)
        )

        # Selector principal (izquierda)
        self.mb = ttk.Menubutton(self, text="Seleccionar")
        menu = tk.Menu(self.mb, tearoff=0)
        self.mb["menu"] = menu
        for s in ["CONEXOS", "OBRAS", "CUE-SHEETS"]:
            menu.add_command(label=s, command=lambda s=s: self.cargar_modulo(s))
        self.mb.grid(row=1, column=0, sticky="w", padx=10, pady=10)

        # Slot derecho para selectores
        self.frmSelect = ttk.Frame(self)
        self.frmSelect.grid(row=1, column=1, sticky="w", padx=10, pady=10)
        self.frmSelect.grid_remove()

        # Body principal
        self.body = ttk.Frame(self)
        self.body.grid(row=2, column=0, sticky="nsew", padx=10, pady=10)
        self.body.grid_rowconfigure(0, weight=1)
        self.body.grid_columnconfigure(0, weight=1)

        # Vistas grandes (van en body)
        self.conexos = ScannerConexos(self.body)
        self.obras_main = ObrasMain(self.body)
        self.cue_sheets_main = CueSheetsMain(self.body)

        self.vistas = {
            "CONEXOS": self.conexos,
            "OBRAS": self.obras_main,
            "CUE-SHEETS": self.cue_sheets_main,
        }

        # Selectores (viven en frmSelect)
        self.obras_selector = ObrasSelector(self.frmSelect, on_select=self.on_select_sociedad)
        self.obras_selector.grid(row=0, column=0, sticky="w")
        self.obras_selector.grid_remove()

        self.cue_sheets_selector = CueSheetsSelector(self.frmSelect, on_select=self.on_select_cs)
        self.cue_sheets_selector.grid(row=0, column=0, sticky="w")
        self.cue_sheets_selector.grid_remove()

    def ocultar_todo(self):
        for v in self.vistas.values():
            v.grid_remove()  # mejor que grid_forget()

    def _ocultar_selectores(self):
        self.obras_selector.grid_remove()
        self.cue_sheets_selector.grid_remove()

    def on_select_sociedad(self, sociedad: str):
        self.obras_main.cargar(sociedad)
        self.master.update_idletasks()
        self.master.geometry("")

    def on_select_cs(self, sociedad: str):
        self.cue_sheets_main.cargar(sociedad)
        self.master.update_idletasks()
        self.master.geometry("")

    def cargar_modulo(self, modulo: str):
        # Manejo del panel derecho (selectores)
        self.frmSelect.grid_remove()
        self._ocultar_selectores()

        if modulo == "OBRAS":
            self.frmSelect.grid()
            self.obras_selector.grid()
        elif modulo == "CUE-SHEETS":
            self.frmSelect.grid()
            self.cue_sheets_selector.grid()

        # Mostrar la vista principal
        self.ocultar_todo()
        self.vistas[modulo].grid(row=0, column=0, sticky="nsew")

        self.master.update_idletasks()
        self.master.geometry("")