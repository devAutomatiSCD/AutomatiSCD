from tkinter import ttk
from ui.ui_scanner.components.cuesheets.components.ui_cs_amazonNac import ScannerCueSheetsAmazon

class CueSheetsMain(ttk.Frame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.body = ttk.Frame(self)
        self.body.grid(row=0, column=0, sticky="nsew")

        self.body.grid_rowconfigure(0, weight=1)
        self.body.grid_columnconfigure(0, weight=1)

        self.vistas_clases = {
            "Amazon": ScannerCueSheetsAmazon,
        }

        self.vistas = {}

    def ocultar_todo(self):
        for vista in self.vistas.values():
            vista.grid_forget()

    def cargar(self, sociedad: str):
        self.ocultar_todo()

        clase = self.vistas_clases.get(sociedad)
        if not clase:
            return  

        if sociedad not in self.vistas:
            self.vistas[sociedad] = clase(self.body)

        vista = self.vistas[sociedad]
        vista.grid(row=0, column=0, sticky="nsew")