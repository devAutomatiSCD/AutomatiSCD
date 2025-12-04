import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinter.scrolledtext import ScrolledText
from threading import Thread, Event
from queue import Queue, Empty
from pathlib import Path
import textwrap

from logic.logic_pc import procesar

class ProcesadorCarpetas(ttk.Frame):
    def __init__(self, master, on_volver_menu, **kwargs):
        super().__init__(master, **kwargs)
        
        
        ttk.Button(self, text="⬅ Volver al menú", command=on_volver_menu).pack(
            anchor="w", padx=10, pady=(10, 0)
        )

        self.var_excel = tk.StringVar()
        self.var_destino = tk.StringVar()
        self.var_columna = tk.StringVar(value="4")
        self.var_textGemi = tk.StringVar()
        self.queue_logs = Queue()
        self.trabajando = False
        self.stop_event = Event() 
        self.buffer_log = []
        self.var_check = tk.BooleanVar(value=True)

        frm = ttk.Frame(self, padding=10)

        style = ttk.Style()
        style.configure("Big.TEntry", font=("Arial", 14))
                
        frm.pack(fill="x")

        ttk.Label(frm, text="Archivo Excel:").grid(row=0, column=0, sticky="e", padx=5, pady=5)
        ent_excel = ttk.Entry(frm, textvariable=self.var_excel, width=70)
        ent_excel.grid(row=0, column=1, sticky="we", padx=5, pady=5)
        ttk.Button(frm, text="Elegir...", command=self.elegir_excel).grid(row=0, column=2, padx=5, pady=5)

        ttk.Label(frm, text="Carpeta destino:").grid(row=1, column=0, sticky="e", padx=5, pady=5)
        ent_dest = ttk.Entry(frm, textvariable=self.var_destino, width=70)
        ent_dest.grid(row=1, column=1, sticky="we", padx=5, pady=5)
        ttk.Button(frm, text="Elegir...", command=self.elegir_destino).grid(row=1, column=2, padx=5, pady=5)

        ttk.Label(frm, text="Columna (1=A):").grid(row=2, column=0, sticky="e", padx=5, pady=5)
        ttk.Entry(frm, textvariable=self.var_columna, width=10).grid(row=2, column=1, sticky="w", padx=5, pady=5)
        
        ttk.Label(frm, text="Prompt:").grid(row=3, column=0, sticky="n", padx=5, pady=5)
        self.text_prompt = tk.Text(frm, width=70, height=10) 
        self.text_prompt.grid(row=3, column=1, sticky="w", padx=5, pady=5)
        
        chk = ttk.Checkbutton(frm, text="Procesar con Gemini", variable=self.var_check)
        chk.grid(row=4, column=1, sticky="w", padx=5, pady=(5,10))
        
        default_prompt = textwrap.dedent("""\
        En estas carpetas puedes encontrar 4 archivos o no, los cuales son:
        Letra, Partitura, Certificado (mayormente no vienen) y audio.

        Lo que te pido es que verifiques si corresponde a dicho caso, que la letra sea letra, partitura partitura y así...
        En el caso específico quiero que me des el idioma de la letra, esta la podrás encontrar en el archivo que dice "letra"

        Tambien existe un archivo con nombre x, el cual contiene dentro de su contenido el titulo "boletin de declaracion de obra"
        de este archivo en la filas siguientes: 
        I. TITULO: Nombre de la obra
        II. Titulo original: Nombre de la obra original. Normalmente no viene.
        III. Duracion: tipo de musica y su duracion min:segundos
        V. DERECHOSHABIENTES: la clase de la persona (C o CA), nombre, porcentaje y su numero cae xxxxxxxx-x
        VI. Grabaciones: Interprete
        
        Pueden haber de 1 a 10 personas.
        
        Tambien puedes identificar si el archivo "boletin de declaracion de obra" esta escrito con lapiz o un archivo 100 porciento digital.
        
        Dame los resultados así:
        
        Tipo archivo: Escrito
        Letra: verificada, español
        Audio: verificado
        Partitura: verificado
        Certificado: verificado
        Boletin: Titulo: Hello cro
                 Titulo original: Algo x, si es que no existe, agrega "No existe"
                 Duracion: 3:32 
                 Tipo: Electronica
                 DH: CA_Vicente-Barra_100_20155458-6
                 Interprete: Hello
                 
                 o con más
                 
                 Titulo: Hello cro
                 Titulo original: Algo x, si es que no existe, agrega "No existe"
                 Duracion: 3:32 
                 Tipo: Electronica
                 DH: CA_Vicente-Barra_50_20155458-6
                     CA_Mauricio-Zuñiga_50_19874747-5
                 Interprete: Hello
                     
                 y asi con los porcentaje si es que son más, la idea es que sea 100 porciento el final.
                 
        Si no llega a existir un archivo pones "no existe"
        Solo responde con resultados, NADA MÁS.
        """).strip()
        
        self.text_prompt.insert("1.0", default_prompt)
        
        textoGemi = self.text_prompt.get("1.0", "end-1c")
        self.var_textGemi.set(textoGemi)     
    
        btns = ttk.Frame(self, padding=(10, 0))
        btns.pack(fill="x")
        self.btn_run = ttk.Button(btns, text="Ejecutar", command=self.on_ejecutar)
        self.btn_run.pack(side="left")

        self.btn_cancel = ttk.Button(btns, text="Cancelar", command=self.on_cancel, state="disabled") 
        self.btn_cancel.pack(side="left", padx=8)

        ttk.Button(btns, text="Guardar log...", command=self.guardar_log).pack(side="left", padx=8)

        self.pb = ttk.Progressbar(btns, mode="indeterminate")
        self.pb.pack(fill="x", padx=10, pady=8)

        self.txt = ScrolledText(self, height=22, wrap="word")
        self.txt.pack(fill="both", expand=True, padx=10, pady=(0,10))
        self.txt.config(state="disabled")

        self.after(100, self._poll_logs)

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

    def append_log(self, msg: str):
        """Recibe logs desde el hilo de trabajo (vía cola) y los pinta en el Text."""
        self.txt.config(state="normal")
        self.txt.insert("end", msg + "\n")
        self.txt.see("end")
        self.txt.config(state="disabled")
        self.buffer_log.append(msg)
        
    def _poll_logs(self):
        """Consulta la cola y vuelca a la UI sin bloquear."""
        try:
            while True:
                msg = self.queue_logs.get_nowait()
                self.append_log(msg)
        except Empty:
            pass
        finally:
            self.after(100, self._poll_logs) 

    def on_ejecutar(self):
        if self.trabajando:
            return
        
        self.stop_event.clear()

        ruta_excel = self.var_excel.get().strip()
        ruta_destino = self.var_destino.get().strip()
        columna_txt = self.var_columna.get().strip()
        gemi_txt = self.text_prompt.get("1.0", "end-1c").strip()
        check_box = self.var_check.get()
    
        if not ruta_excel or not ruta_destino:
            messagebox.showwarning("Faltan datos", "Debes seleccionar el Excel y la carpeta destino.")
            return
        
        try:
            col = int(columna_txt)
            if col < 1:
                raise ValueError()
        except ValueError:
            messagebox.showerror("Columna inválida", "La columna debe ser un entero >= 1 (1=A, 2=B, ...).")
            return
        
        try:
            if gemi_txt == "":
                raise ValueError()
        except ValueError:
            messagebox.showerror("Debe ingresar un prompt")
            return

        self.txt.config(state="normal")
        self.txt.delete("1.0", "end")
        self.txt.config(state="disabled")
        self.buffer_log.clear()
        self.btn_cancel.config(state="normal")
        
        self.trabajando = True
        self.pb.start(8) 
        self.btn_run.config(state="disabled")

        def worker():
            def log_cb(m):
                self.queue_logs.put(m)

            resumen = procesar(
                ruta_excel,
                ruta_destino,
                check_box,
                gemi_txt,
                col,
                on_log=log_cb,
                stop_event=self.stop_event 
            )
            
            if resumen and resumen.get("cancelado"):
                self.queue_logs.put("⏹ Proceso cancelado por el usuario.")
            elif resumen and "error" in resumen:
                self.queue_logs.put(f"⛔ Finalizado con error: {resumen['error']}")
            else:
                self.queue_logs.put("🎉 Proceso terminado.")

            self.after(0, self._fin_trabajo)

        Thread(target=worker, daemon=True).start()

    def _fin_trabajo(self):
        self.trabajando = False
        self.pb.stop()
        self.btn_run.config(state="normal")
        self.btn_cancel.config(state="disabled")

    def guardar_log(self):
        if not self.buffer_log:
            messagebox.showinfo("Sin contenido", "No hay log para guardar aún.")
            return
        fpath = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Texto", "*.txt"), ("Todos", "*.*")],
            title="Guardar log como..."
        )
        if not fpath:
            return
        try:
            Path(fpath).write_text("\n".join(self.buffer_log), encoding="utf-8")
            messagebox.showinfo("OK", f"Log guardado en:\n{fpath}")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar el log:\n{e}")
            
    def on_cancel(self):
        if self.trabajando:
            self.stop_event.set()        
            self.queue_logs.put("🔁 Solicitando cancelación...")  

