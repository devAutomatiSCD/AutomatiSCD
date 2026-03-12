import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from threading import Thread, Event
from utils.image_tooltip import ImageTooltip
from utils.paths import resource_path
from PIL import Image, ImageTk

from logic.logic_scanner.logic_obrasTONO import scanner

class ScannerObrasTONO(ttk.Frame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self.var_ruta = tk.StringVar()
        self.var_folio = tk.StringVar()

        # "file" o "folder"
        self.var_modo = tk.IntVar(value=1)

        self.stop_event = Event()
        self.trabajando = False

        main = ttk.Frame(self)
        main.pack(fill="both", expand=True)

        frm = ttk.Frame(main, padding=10)
        frm.pack(fill="x")
        frm.grid_columnconfigure(1, weight=1)

        # Modo
        ttk.Label(frm, text="Modo:").grid(row=0, column=0, sticky="e", padx=5, pady=5)
        modo_box = ttk.Frame(frm)
        modo_box.grid(row=0, column=1, sticky="w", padx=5, pady=5)

        ttk.Radiobutton(
            modo_box, text="Archivo PDF", value=1,
            variable=self.var_modo, command=self._on_modo_change
        ).pack(side="left")

        ttk.Radiobutton(
            modo_box, text="Carpeta con PDFs", value=2,
            variable=self.var_modo, command=self._on_modo_change
        ).pack(side="left", padx=(10, 0))

        self.lbl_ruta = ttk.Label(frm, text="Archivo obras TONO (.pdf): ")
        self.lbl_ruta.grid(row=1, column=0, sticky="e", padx=5, pady=5)

        ttk.Entry(frm, textvariable=self.var_ruta, width=70).grid(
            row=1, column=1, sticky="we", padx=5, pady=5
        )

        self.btn_elegir = ttk.Button(frm, text="Elegir...", command=self.elegir_ruta)
        self.btn_elegir.grid(row=1, column=2, padx=5, pady=5)
        
        icono_path = resource_path("assets", "info.png")
        
        img = Image.open(icono_path)
        img = img.resize((24, 24), Image.LANCZOS) 
        self.help_icon_img = ImageTk.PhotoImage(img) 
        
        self.btn_help = ttk.Label(frm, image=self.help_icon_img, cursor="hand2")
        self.btn_help.grid(row=1, column=3, padx=(6, 0), pady=5, sticky="w")
        
        self.tooltip = ImageTooltip(
            self.btn_help,
            image_path_getter=self._get_tooltip_img_path,
            text_getter=self._get_tooltip_text,
        )

        ttk.Label(frm, text="N° GLPI:").grid(row=2, column=0, sticky="e", padx=5, pady=5)
        ttk.Entry(frm, textvariable=self.var_folio, width=10).grid(row=2, column=1, sticky="w", padx=5, pady=5)

        btns = ttk.Frame(main, padding=(10, 0))
        btns.pack(fill="x", pady=(10, 0))

        self.btn_run = ttk.Button(btns, text="Ejecutar", command=self.scanner)
        self.btn_run.pack(side="left")

        self.btn_cancel = ttk.Button(btns, text="Cancelar", command=self.on_cancel, state="disabled")
        self.btn_cancel.pack(side="left", padx=8)

        self.pb = ttk.Progressbar(btns, mode="indeterminate")
        self.pb.pack(side="left", fill="x", expand=True, padx=10)

        self.lbl = ttk.Label(main, text="")
        self.lbl.pack(anchor="w", padx=10, pady=(10, 0))

        self._on_modo_change()

    def _on_modo_change(self):
        modo = self.var_modo.get()
        if modo == 1:
            self.lbl_ruta.config(text="Archivo obras TONO (.pdf): ")
        else:
            self.lbl_ruta.config(text="Carpeta con PDFs: ")

    def elegir_ruta(self):
        modo = self.var_modo.get()
        if modo == "file":
            path = filedialog.askopenfilename(
                title="Selecciona el archivo PDF",
                filetypes=[("PDF files", "*.pdf")]
            )
        else:
            path = filedialog.askdirectory(title="Selecciona la carpeta con PDFs")
        if path:
            self.var_ruta.set(path)

    def scanner(self):
        if self.trabajando:
            return

        ruta = self.var_ruta.get().strip()
        folio = self.var_folio.get().strip()
        modo = self.var_modo.get()

        if not ruta:
            messagebox.showwarning("Atención", "Debe seleccionar un archivo PDF." if modo == "file" else "Debe seleccionar una carpeta.")
            return

        if modo == "file":
            if not ruta.lower().endswith(".pdf") or not os.path.isfile(ruta):
                messagebox.showwarning("Atención", "La ruta no es un PDF válido.")
                return
        else:
            if not os.path.isdir(ruta):
                messagebox.showwarning("Atención", "La ruta no es una carpeta válida.")
                return
            if not any(f.lower().endswith(".pdf") for f in os.listdir(ruta)):
                messagebox.showwarning("Atención", "La carpeta no contiene PDFs.")
                return

        if not folio:
            messagebox.showwarning("Atención", "Debe ingresar folio")
            return

        self.stop_event.clear()

        self.trabajando = True
        self.lbl.config(text="Procesando…")
        self.pb.start(10)

        self.btn_run.config(state="disabled")
        self.btn_cancel.config(state="normal")

        def worker():
            res = scanner(ruta, folio, stop_event=self.stop_event, modo=modo)
            self.after(0, lambda: self._fin_trabajo(res))

        Thread(target=worker, daemon=True).start()

    def on_cancel(self):
        if not self.trabajando:
            return
        self.lbl.config(text="Cancelando…")
        self.stop_event.set()
        self.btn_cancel.config(state="disabled")

    def _fin_trabajo(self, res):
        self.trabajando = False
        self.pb.stop()

        self.btn_run.config(state="normal")
        self.btn_cancel.config(state="disabled")

        if isinstance(res, dict) and res.get("cancelado"):
            self.lbl.config(text="Cancelado ✅")
            messagebox.showinfo("Cancelado", "Proceso cancelado.")
            return

        if res is True:
            self.lbl.config(text="Terminado ✅")
            messagebox.showinfo("Notificación", "Excel creado en Escritorio")
        else:
            self.lbl.config(text="Error ❌")
            messagebox.showerror("Error", "Error al exportar Excel")
            
    def _get_tooltip_img_path(self):
        if self.var_modo.get() == 1:
            return resource_path("assets", "info_obras", "tono", "img1.png")
        return resource_path("assets", "info_obras", "tono", "img2.png")
    
    def _get_tooltip_text(self):
        if self.var_modo.get() == 1:
            return (
                "Modo 1:\n"
                "El PDF debe contener esta estructura\n para que se pueda procesar"
            )
        return (
            "Modo 2:\n"
            "Los PDFs en la carpeta deben contener esta estructura\n para que se pueda procesar"
        )