import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from threading import Thread, Event

from logic.logic_le import procesar_excel_a_csv

class LimpiarExcel(ttk.Frame):
    def __init__(self, master, on_volver_menu, **kwargs):
        super().__init__(master, **kwargs)
        
        main = ttk.Frame(self, padding=20)
        main.pack(fill="both", expand=True)
        
        ttk.Button(main, text="⬅ Volver al menú", command=on_volver_menu).pack(
            anchor="w", padx=10, pady=(10, 0)
        )
        
        self.var_excel = tk.StringVar()
        self.trabajando = False
        
        frm = ttk.Frame(main, padding=10)
        
        style = ttk.Style()
        style.configure("Big.TEntry", font=("Arial", 14))
        
        frm.pack(fill="x")
        
        ttk.Label(frm, text="Archivo Excel:").grid(row=0, column=0, sticky="e", padx=5, pady=5)
        ent_excel = ttk.Entry(frm, textvariable=self.var_excel, width=70)
        ent_excel.grid(row=0, column=1, sticky="we", padx=5, pady=5)
        ttk.Button(frm, text="Elegir...", command=self.elegir_excel).grid(row=0, column=2, padx=5, pady=5)

        btns = ttk.Frame(main, padding=(10, 0))
        btns.pack(fill="x")
        self.btn_run = ttk.Button(btns, text="Ejecutar", command=self.on_ejecutar)
        self.btn_run.pack(side="left")

        self.btn_cancel = ttk.Button(btns, text="Cancelar", command=self.on_cancel, state="disabled") 
        self.btn_cancel.pack(side="left", padx=8)
        
    def elegir_excel(self):
            fpath = filedialog.askopenfilename(
                title="Selecciona el Excel",
                filetypes=[("Excel", "*.xlsx;*.xlsm;*.xltx;*.xltm"), ("Todos", "*.*")]
            )
            if fpath:
                self.var_excel.set(fpath)

    def elegir_destino(self):
            dpath = filedialog.askdirectory(title="Selecciona la carpeta destino")
            if dpath:
                self.var_destino.set(dpath)
    
    def on_ejecutar(self):
        if self.trabajando:
            return
        
        # self.stop_event.clear()
        
        ruta_excel = self.var_excel.get().strip()
    
        def worker():
            res = procesar_excel_a_csv(ruta_excel)
            self.after(0, lambda: self._fin_trabajo(res))

        Thread(target=worker, daemon=True).start()
        
    def on_cancel(self):
        if self.trabajando:
            self.stop_event.set()        
            # self.queue_logs.put(" Solicitando cancelación...")
            
    def _fin_trabajo(self, res):
        self.trabajando = False
        
        self.btn_run.config(state="normal")
        self.btn_cancel.config(state="disabled")

        if res.get("cancelado"):
            # self.queue_logs.put("Proceso cancelado por el usuario.")
            return
        
        if isinstance(res, dict) and res.get("ok"):
            ruta = res.get("ruta_salida", "desconocida")
            
            messagebox.showinfo("Éxito", f"Archivo procesado exitosamente:\n{ruta}")
            
            alerta = res.get("alerta", [])
            
            if alerta:
                mensaje_alerta = "Alerta: Se encontraron filas con IPI faltante.\n"
                mensaje_alerta += "\n".join(alerta)
                messagebox.showinfo("Atención", mensaje_alerta)
        
            
        
        

