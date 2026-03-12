import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from threading import Thread, Event
from utils.image_tooltip import ImageTooltip
from utils.paths import resource_path
from PIL import Image, ImageTk

from logic.logic_scanner.logic_obrasPEER import scanner

class ScannerObrasPEER(ttk.Frame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        self.var_ruta_pdf = tk.StringVar()
        self.var_folio = tk.StringVar()
        
        self.stop_event = Event()
        self.trabajando = False

        main = ttk.Frame(self)
        main.pack(fill="both", expand=True)

        frm = ttk.Frame(main, padding=10)
        frm.pack(fill="x")
        frm.grid_columnconfigure(1, weight=1)
        
        ttk.Label(frm, text="Archivo obras PEER (.pdf): ").grid(row=0, column=0, sticky="e", padx=5, pady=5)
        ttk.Entry(frm, textvariable=self.var_ruta_pdf, width=70).grid(
            row=0, column=1, sticky="we", padx=5, pady=5
        )
        ttk.Button(frm, text="Elegir...", command=self.elegir_pdf).grid(row=0, column=2, padx=5, pady=5)
        
        icono_path = resource_path("assets", "info.png")

        img = Image.open(icono_path)
        img = img.resize((24, 24), Image.LANCZOS)
        self.help_icon_img = ImageTk.PhotoImage(img)
        
        self.btn_help = ttk.Label(frm, image=self.help_icon_img, cursor="hand2")
        self.btn_help.grid(row=0, column=3, padx=(6, 0), pady=5, sticky="w")
        
        self.tooltip = ImageTooltip(
            self.btn_help,
            image_path=resource_path("assets", "info_obras", "peer", "img1.png"),
            text="El PDF debe contener esta estructura\n para que se pueda procesar"
        )
        
        ttk.Label(frm, text="N° GLPI:").grid(row=1, column=0, sticky="e", padx=5, pady=5)
        ttk.Entry(frm, textvariable=self.var_folio, width=10).grid(row=1, column=1, sticky="w", padx=5, pady=5)
        
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
    
    def elegir_pdf(self):
        dpath = filedialog.askopenfilename(title="Selecciona el archivo PDF", filetypes=[("PDF files", "*.pdf")])
        if dpath:
            self.var_ruta_pdf.set(dpath)
        
    def scanner(self):
        if self.trabajando:
            return

        ruta_boletines = self.var_ruta_pdf.get().strip()
        folio = self.var_folio.get().strip()
        
        if not ruta_boletines:
            messagebox.showwarning("Atención", "Debe seleccionar un archivo PDF.")
            return
        
        if not folio:
            messagebox.showwarning("Atención", "Debe ingresar folio")
        
        self.stop_event.clear()

        self.trabajando = True
        self.lbl.config(text="Procesando…")
        self.pb.start(10)

        self.btn_run.config(state="disabled")
        self.btn_cancel.config(state="normal")

        def worker():
            res = scanner(ruta_boletines, folio, stop_event=self.stop_event)
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