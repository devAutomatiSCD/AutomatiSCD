# ui/scanner/ui_scanner.py
import tkinter as tk
from tkinter import ttk, messagebox

class ScannerMenu(ttk.Frame):
    def __init__(self, master, ir_conexos, ir_obras, on_volver_menu, **kwargs):
        super().__init__(master, **kwargs)

        main = ttk.Frame(self, padding=10)
        main.pack(fill="both", expand=True)

        ttk.Button(main, text="⬅ Volver al menú", command=on_volver_menu).pack(
            anchor="w", padx=10, pady=(10, 0)
        )

        frm = ttk.Frame(main, padding=10)
        frm.pack(fill="x")

        self.frame_botones = ttk.Frame(frm)
        self.frame_botones.grid(row=0, column=0, sticky="w", pady=(0, 10))

        ttk.Button(self.frame_botones, text="Conexos", command=ir_conexos)\
            .grid(row=1, column=0, padx=10, pady=5, sticky="nsew")

        ttk.Button(self.frame_botones, text="Obras", command=ir_obras)\
            .grid(row=1, column=1, padx=10, pady=5, sticky="nsew")


from ui.ui_scanner.components.ui_conexos import ScannerConexos
from ui.ui_scanner.components.ui_obras_sgae import ScannerObrasSGAE

class ScannerContainer(ttk.Frame):
    def __init__(self, master, on_volver_menu_principal, **kwargs):
        super().__init__(master, **kwargs)

        # Pantallas
        self.menu_scanner = ScannerMenu(
            self,
            ir_conexos=self.mostrar_conexos,
            ir_obras=self.mostrar_obras,
            on_volver_menu=on_volver_menu_principal,
        )

        self.conexos = ScannerConexos(self, on_volver_menu=self.mostrar_menu)
        self.obrasSGAE = ScannerObrasSGAE(self, on_volver_menu=self.mostrar_menu)

        # self.obras = ttk.Frame(self, padding=20)
        # ttk.Label(self.obras, text="Scanner Obras (en construcción)").pack()
        # ttk.Button(self.obras, text="⬅ Volver", command=self.mostrar_menu_scanner).pack(pady=10)

        self.mostrar_menu()

    def _ocultar_todos(self):
        for widget in self.winfo_children():
            widget.pack_forget()

    def mostrar_menu(self):
        self._ocultar_todos()
        self.menu_scanner.pack(fill="both", expand=True)
        self.master.update_idletasks()
        self.master.geometry("250x150")
        self.master.resizable(False, False)

    def mostrar_conexos(self):
        self._ocultar_todos()
        self.conexos.pack(fill="both", expand=True)
        self.master.update_idletasks()
        self.master.geometry("")
        self.master.resizable(False, False)

    def mostrar_obras(self):
        self._ocultar_todos()
        self.obrasSGAE.pack(fill="both", expand=True)
        self.master.update_idletasks()
        self.master.geometry("")
        self.master.resizable(False, False)
        

        

