import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from threading import Thread, Event

from logic.logic_scanner.cuesheets.logic_cs_amazon import scanner

class ScannerCueSheetsAmazon(ttk.Frame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self.var_ruta_pdf = tk.StringVar()
        self.var_folio = tk.StringVar()
        self.var_director = tk.StringVar()
        self.var_antagonista = tk.StringVar()
        self.var_protagonista = tk.StringVar()
        self.var_capitulo = tk.StringVar()
        self.var_anio = tk.StringVar()

        self.stop_event = Event()
        self.trabajando = False

        main = ttk.Frame(self)
        main.pack(fill="both", expand=True)

        frm = ttk.Frame(main, padding=10)
        frm.pack(fill="x")

        # fila archivo
        top_file = ttk.Frame(frm)
        top_file.pack(fill="x", pady=(0, 10))

        ttk.Label(top_file, text="Archivo AMAZON (.pdf):").pack(side="left", padx=(0, 5))
        ttk.Entry(top_file, textvariable=self.var_ruta_pdf, width=70).pack(side="left", fill="x", expand=True, padx=(0, 5))
        ttk.Button(top_file, text="Elegir...", command=self.elegir_pdf).pack(side="left")

        # contenedor central de ambos bloques
        datos = ttk.Frame(frm)
        datos.pack(anchor="center")  # <- esto ayuda a centrar el conjunto

        izq = ttk.Frame(datos)
        izq.pack(side="left", padx=(0, 20))
        
        cent = ttk.Frame(datos)
        cent.pack(side="left", padx=(0, 20))

        der = ttk.Frame(datos)
        der.pack(side="left")

        # bloque izquierdo
        ttk.Label(izq, text="N° FOLIO:").grid(row=0, column=0, sticky="e", padx=(0, 5), pady=5)
        ttk.Entry(izq, textvariable=self.var_folio, width=10).grid(row=0, column=1, sticky="w", pady=5)

        ttk.Label(izq, text="Protagonista:").grid(row=1, column=0, sticky="e", padx=(0, 5), pady=5)
        ttk.Entry(izq, textvariable=self.var_protagonista, width=25).grid(row=1, column=1, sticky="w", pady=5)
        
        # bloque centro
        ttk.Label(cent, text="Año:").grid(row=0, column=0, sticky="e", padx=(0, 5), pady=5)
        ttk.Entry(cent, textvariable=self.var_anio, width=10).grid(row=0, column=1, sticky="w", pady=5)
        
        ttk.Label(cent, text="Antagonista:").grid(row=1, column=0, sticky="e", padx=(0, 5), pady=5)
        ttk.Entry(cent, textvariable=self.var_antagonista, width=25).grid(row=1, column=1, sticky="w", pady=5)

        # bloque derecho
        ttk.Label(der, text="Capitulo:").grid(row=0, column=0, sticky="e", padx=(0, 5), pady=5)
        ttk.Entry(der, textvariable=self.var_capitulo, width=10).grid(row=0, column=1, sticky="w", pady=5)
        
        ttk.Label(der, text="Director:").grid(row=1, column=0, sticky="e", padx=(0, 5), pady=5)
        ttk.Entry(der, textvariable=self.var_director, width=25).grid(row=1, column=1, sticky="w", pady=5)

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
            return
        
        self.stop_event.clear()

        self.trabajando = True
        self.lbl.config(text="Procesando…")
        self.pb.start(10)

        self.btn_run.config(state="disabled")
        self.btn_cancel.config(state="normal")
        
        datos = {
            "folio": folio,
            "dir": self.var_director.get().strip(),
            "antog": self.var_antagonista.get().strip(),
            "protag": self.var_protagonista.get().strip(),
            "cap": self.var_capitulo.get().strip(),
            "anio": self.var_anio.get().strip(),
        }

        def worker():
            res = scanner(ruta_boletines, datos, stop_event=self.stop_event)
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
        if isinstance(res, dict) and res.get("ok"):
            cantidad = res.get("cantidad_obras", 0)
            ruta = res.get("ruta_destino", "desconocida")
            self.lbl.config(text=f"Terminado ✅ ({cantidad} obras)")
            messagebox.showinfo("Notificación", f"Excel creado en {ruta}.\nObras procesadas: {cantidad}")
        else:
            self.lbl.config(text="Error ❌")
            messagebox.showerror("Error", "Error al exportar Excel")