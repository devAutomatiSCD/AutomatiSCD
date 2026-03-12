import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinter.scrolledtext import ScrolledText

from logic.logic_pda import find, save, firstPDA, exportarExcel
from utils.config_manager import obtener_usuario
from datetime import datetime
from utils.log_manager import escribir_log

class uiPDA(ttk.Frame):
    def __init__(self, master, on_volver_menu, ruta_pda_f, ruta_pda_w, ruta_registro_web, ruta_registro_fisico, **kwargs):
        super().__init__(master, **kwargs)
        
        main = ttk.Frame(self, padding=20)
        main.pack(fill="both", expand=True)
        
        ttk.Button(main, text="⬅ Volver al menú", command=on_volver_menu).pack(
            anchor="w", padx=10, pady=(10, 0)
        )
        
        self.ruta_pdaW = ruta_pda_w
        self.ruta_pdaF = ruta_pda_f
        self.ruta_registro_web = ruta_registro_web
        self.ruta_registro_fisico = ruta_registro_fisico
        self.cantidadPDA = tk.StringVar(value=20)
        self.PDAs = []
        self.rutaExcelExport = tk.StringVar()
        self.datoFirstPDAW = tk.StringVar(value=firstPDA(self.ruta_pdaW))
        self.datoFirstPDAF = tk.StringVar(value=firstPDA(self.ruta_pdaF))
        self.activoPDAW = tk.BooleanVar(value=False)
        self.activoPDAF = tk.BooleanVar(value=True)
        self.ahora = datetime.now()
        
        frm = ttk.Frame(main, padding=10)
        
        style = ttk.Style()
        style.configure("Big.TEntry", font=("Arial", 14))
        
        frm.pack(fill="x")
        
        fila1 = ttk.Frame(frm)
        fila1.grid(row=0, column=0, sticky="w", pady=(0, 10))

        self.text_pda = ttk.Label(fila1, text="PDA Web:")
        self.text_pda.pack(side="left", padx=5)

        self.pda = ttk.Label(fila1, textvariable=self.datoFirstPDAW)
        self.pda.pack(side="left", padx=5)
        
        self.text_pda = ttk.Label(fila1, text="PDA Físico:")
        self.text_pda.pack(side="left", padx=5)

        self.pda = ttk.Label(fila1, textvariable=self.datoFirstPDAF)
        self.pda.pack(side="left", padx=5)
        
        fila2 = ttk.Frame(frm)
        fila2.grid(row=1, column=0, sticky="w", pady=(0, 10))
        
        self.button_PDAw = ttk.Checkbutton(
            fila2, text="PDA Web", variable=self.activoPDAW, command=self.on_toggle_pdaW
        )
        self.button_PDAw.pack(side="left", padx=5)

        self.button_PDAf = ttk.Checkbutton(
            fila2, text="PDA Físico", variable=self.activoPDAF, command=self.on_toggle_pdaF
        )
        self.button_PDAf.pack(side="left", padx=5)

        fila3 = ttk.Frame(frm)
        fila3.grid(row=2, column=0, sticky="w")

        ttk.Label(fila3, text="Ingresa cantidad de PDAs:").pack(side="left")
        ttk.Entry(fila3, textvariable=self.cantidadPDA, width=30).pack(side="left")

        btns = ttk.Frame(main, padding=(10, 0))
        btns.pack(fill="x")
        self.btn_find = ttk.Button(btns, text="Buscar", command=self.on_find)
        self.btn_find.pack(side="left", padx=5)
        self.btn_save = ttk.Button(btns, text="Guardar", command=self.on_save)
        self.btn_save.pack(side="left", padx=5)
        self.btn_exp_excel = ttk.Button(btns, text="Exportar Excel", command=self.on_export_excel)
        self.btn_exp_excel.pack(side="left")
        
        self.txt_resultado = ScrolledText(frm, width=40, height=5, wrap="word")
        self.txt_resultado.grid(row=3, column=0, sticky="we", pady=(10,0))
        self.txt_resultado.configure(state="disabled")
        
    def on_find(self):
        # cantidad = self.cantidadPDA.get()
        cantidad = int(self.cantidadPDA.get())
        self.limpiar_resultado()
        
        print(self.activoPDAF.get(), self.activoPDAW.get())
        
        if self.activoPDAW.get():
            self.PDAs = find(cantidad, self.ruta_pdaW)
        elif self.activoPDAF.get():
            self.PDAs = find(cantidad, self.ruta_pdaF)
        else:
            notificacion = tk.Toplevel(self)
            notificacion.title("Aviso")

            frm = ttk.Frame(notificacion, padding=10)
            frm.pack()

            ttk.Label(frm, text="Activa uno de los 2 PDA").pack(pady=10)
            ttk.Button(frm, text="Cerrar", command=notificacion.destroy).pack()
            
            notificacion.transient(self)   # se "pega" a la ventana principal
            notificacion.grab_set()         # BLOQUEA todo lo demás
            self.wait_window(notificacion)  # espera hasta que se cierre

            
        self.txt_resultado.configure(state="normal")  # habilitar edición
        self.txt_resultado.delete("1.0", tk.END)      # limpiar
        self.txt_resultado.insert(tk.END, ", ".join(str(x) for x in self.PDAs)) # insertar texto
        self.txt_resultado.configure(state="disabled")  # bloquear   # ← actualizar el StringVar

    def on_save(self):
        if self.activoPDAW.get():
            guardado = save(self.PDAs, self.ruta_pdaW)
            if guardado:
                messagebox.showinfo("Información", "El PDA fue guardado con exito")
            else:
                messagebox.showerror("Error", "Primero presiona el botón buscar")
            nuevo_pda = firstPDA(self.ruta_pdaW)
            self.datoFirstPDAW.set(nuevo_pda)
            detalles = f"PDAs creados {self.PDAs[0]}...{self.PDAs[-1]}"
            
            escribir_log(self.ruta_registro_web, obtener_usuario(), accion="Crear_PDA", detalles=detalles)
            
        elif self.activoPDAF.get():
            guardado = save(self.PDAs, self.ruta_pdaF)
            if guardado:
                messagebox.showinfo("Información", "El PDA fue guardado con exito")
            else:
                messagebox.showerror("Error", "Primero presiona el botón buscar")
            nuevo_pda = firstPDA(self.ruta_pdaF)
            self.datoFirstPDAF.set(nuevo_pda)
            detalles = f"PDAs creados {self.PDAs[0]}...{self.PDAs[-1]}"
            
            escribir_log(self.ruta_registro_web, obtener_usuario(), accion="Crear_PDA", detalles=detalles)
        
        else:
            notificacion = tk.Toplevel(self)
            notificacion.title("Aviso")

            frm = ttk.Frame(notificacion, padding=10)
            frm.pack()

            ttk.Label(frm, text="Activa uno de los 2 PDA").pack(pady=10)
            ttk.Button(frm, text="Cerrar", command=notificacion.destroy).pack()
            
            notificacion.transient(self)   # se "pega" a la ventana principal
            notificacion.grab_set()         # BLOQUEA todo lo demás
            self.wait_window(notificacion)  # espera hasta que se cierre
        
    def on_export_excel(self):
        ventana = tk.Toplevel()
        ventana.title("Exportar Excel")
        
        ventana.update_idletasks()
        ventana.geometry("")
        ventana.resizable(False, False)
        
        frm = ttk.Frame(ventana, padding=10)
        frm.grid()
        
        ttk.Label(frm, text="Ruta: ").grid(row=0, column=0, padx=5, pady=5)
        ent_dest = ttk.Entry(frm, textvariable=self.rutaExcelExport, width=50)
        ent_dest.grid(row=0, column=1, sticky="we", padx=5, pady=5)
        ttk.Button(frm, text="Elegir...", command=self.elegir_destino).grid(row=0, column=2)
        
        ttk.Button(frm, text="Exportar", command=self.exportarExcel).grid(row=1, column=0)
        
        ventana.transient(self)   # se "pega" a la ventana principal
        ventana.grab_set()         # BLOQUEA todo lo demás
        self.wait_window(ventana)  # espera hasta que se cierre
        
    def elegir_destino(self):
        dpath = filedialog.askdirectory(title="Selecciona la carpeta destino")
        if dpath:
            self.rutaExcelExport.set(dpath)
            
    def exportarExcel(self):
        print(self.rutaExcelExport.get())
        exportado = exportarExcel(self.PDAs, self.rutaExcelExport.get())
        if exportado:
            messagebox.showinfo("Información", f"El archivo Excel fue creado con exito \n ruta: {self.rutaExcelExport.get()}")
        else:
            messagebox.showerror("Error", f"Ingrese la RUTA para exportar el Excel")
            
    def limpiar_resultado(self):
        self.PDAs = []
        self.txt_resultado.configure(state="normal")
        self.txt_resultado.delete("1.0", tk.END)
        self.txt_resultado.configure(state="disabled")

    def on_toggle_pdaW(self):
        if self.activoPDAW.get():
            self.activoPDAF.set(False)
        if not self.activoPDAW.get() and not self.activoPDAF.get():
            self.activoPDAW.set(True)

        self.limpiar_resultado()

    def on_toggle_pdaF(self):
        if self.activoPDAF.get():
            self.activoPDAW.set(False)
        if not self.activoPDAW.get() and not self.activoPDAF.get():
            self.activoPDAF.set(True)

        self.limpiar_resultado()
