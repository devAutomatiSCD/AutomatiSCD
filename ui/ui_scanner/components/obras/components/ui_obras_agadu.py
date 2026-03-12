import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from threading import Thread, Event
from utils.image_tooltip import ImageTooltip
from utils.paths import resource_path
from PIL import Image, ImageTk

from logic.logic_scanner.logic_obrasAGADU import scanner

class ScannerObrasAGADU(ttk.Frame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self.var_carpeta_pdfs = tk.StringVar()
        self.var_folio = tk.StringVar()
        
        self.stop_event = Event()
        self.trabajando = False

        main = ttk.Frame(self)
        main.pack(fill="both", expand=True)

        frm = ttk.Frame(main, padding=10)
        frm.pack(fill="x")
        frm.grid_columnconfigure(1, weight=1)
        
        ttk.Label(frm, text="Carpeta obras AGADU: ").grid(row=0, column=0, sticky="e", padx=5, pady=5)
        ttk.Entry(frm, textvariable=self.var_carpeta_pdfs, width=70).grid(
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
            image_path=resource_path("assets", "info_obras", "agadu", "img1.png"),
            text="Los PDFs en la carpeta deben contener esta estructura\n para que se pueda procesar"
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
        dpath = filedialog.askdirectory(title="Seleccionar carpeta")
        if dpath:
            self.var_carpeta_pdfs.set(dpath)
        
    def scanner(self):
        if self.trabajando:
            return

        ruta_boletines = self.var_carpeta_pdfs.get().strip()
        folio = self.var_folio.get().strip()
        
        if not ruta_boletines:
            messagebox.showwarning("Atención", "Debe seleccionar la carpeta con los PDFs.")
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
        if isinstance(res, dict) and res.get("ok"):
            cantidad = res.get("cantidad_obras", 0)
            ruta = res.get("ruta_destino", "desconocida")
            alertas = res.get("alertas", [])
            if alertas:
                self.mostrar_alertas_copiables(alertas)
            self.lbl.config(text=f"Terminado ✅ ({cantidad} obras)")
            messagebox.showinfo("Notificación", f"Excel creado en {ruta}.\nObras procesadas: {cantidad}")
        else:
            self.lbl.config(text="Error ❌")
            messagebox.showerror("Error", "Error al exportar Excel")
            
    def mostrar_alertas_copiables(self, alertas):

        win = tk.Toplevel()
        win.title("⚠️ Alertas de porcentaje")
        win.geometry("700x500")

        txt = tk.Text(
            win,
            wrap="word",
            font=("Consolas", 10),
            undo=True,        
            maxundo=-1       
        )
        txt.pack(expand=True, fill="both")

        scroll = tk.Scrollbar(txt)
        scroll.pack(side="right", fill="y")
        txt.config(yscrollcommand=scroll.set)
        scroll.config(command=txt.yview)

        contenido = []
        contenido.append(f"Hay {len(alertas)} obras con % ≠ 100\n")

        for _, t, iswc, p_s, p_m in alertas:
            contenido.append(f"{t} ({iswc}) → {p_s:.2f}% / {p_m:.2f}%")

        txt.insert("1.0", "\n".join(contenido))
        txt.config(state="normal")

        def select_all(event=None):
            txt.tag_add("sel", "1.0", "end")
            return "break"
        
        def undo(event=None):
            try:
                txt.edit_undo()
            except:
                pass
            return "break"

        def redo(event=None):
            try:
                txt.edit_redo()
            except:
                pass
            return "break"

        txt.bind("<Control-a>", select_all)
        txt.bind("<Control-A>", select_all)
        txt.bind("<Control-z>", undo)
        txt.bind("<Control-y>", redo)
        txt.bind("<Control-Z>", undo)
        txt.bind("<Control-Y>", redo)

        # foco directo
        txt.focus()