import tkinter as tk
from tkinter import ttk, messagebox
import os, sys

from ui.procesador_carpetas import ProcesadorCarpetas
from ui.limpiar_excel import LimpiarExcel
from ui.pda import uiPDA
from ui.correo import Correo
from utils.config_manager import guardar_correos_config, verificar_estructura, obtener_carpeta_base, guardar_usuario, obtener_usuario

class MenuInicial(ttk.Frame):
    def __init__(self, master, mostrar_procesador_carpetas, mostrar_limpiar_excel, mostrar_PDA, mostrar_correo, **kwargs):
        super().__init__(master, **kwargs)

        ttk.Label(self, text="AutomatiSCD", font=("Arial", 20, "bold")).pack(pady=40)

        ttk.Button(
            self,
            text="Procesador de Carpetas",
            command=mostrar_procesador_carpetas
        ).pack(pady=5)

        ttk.Button(
            self,
            text="Procesador de Excel",
            command=mostrar_limpiar_excel
        ).pack(pady=5)
        
        ttk.Button(
            self,
            text="PDA",
            command=mostrar_PDA
        ).pack(pady=5)
        
        ttk.Button(
            self,
            text="Correo",
            command=mostrar_correo
        ).pack(pady=5)
        

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        
        self.usuario = None
        self.usuario_var = tk.StringVar()
        
        self.carpeta_base = obtener_carpeta_base(self)

        if self.carpeta_base is None:
            messagebox.showinfo("Cerrando", "No se seleccionó una ruta válida. La aplicación se cerrará.")
            self.destroy()
            return
        
        if self.carpeta_base:
            errores = verificar_estructura(self.carpeta_base)

            if errores:
                messagebox.showerror(
                    "Estructura incorrecta",
                    "\n".join(errores)
                )

        # Subcarpetas
        self.carpeta_pdas = self.carpeta_base / "PDA"
        self.carpeta_reporte = self.carpeta_base / "Registro" 

        # Archivos
        self.pda_f = self.carpeta_pdas / "PDAf.txt"
        self.pda_w = self.carpeta_pdas / "PDAw.txt"
        self.registroF = self.carpeta_reporte / "registro_fisico.txt"
        self.registroW = self.carpeta_reporte / "registro_web.txt"


        self.title("AutoCarpetas SCD")
        
        style = ttk.Style(self)
        style.theme_use("clam")
        
        style.configure(
            "Primary.TButton",
            background="#e0e0e0"
        )
        
        style.map(
            "Primary.TButton",
            background=[("active", "#d0d0d0")]
        )
        
        menuBar = tk.Menu(self)

        # ================== Archivo ==================
        archivo_menu = tk.Menu(menuBar, tearoff=0)
        archivo_menu.add_command(label="Volver al menú", command=self.mostrar_menu)
        archivo_menu.add_separator()
        archivo_menu.add_command(label="Salir", command=self.destroy)
        menuBar.add_cascade(label="Archivo", menu=archivo_menu)


        # ================== Herramientas ==================
        herramientas_menu = tk.Menu(menuBar, tearoff=0)
        herramientas_menu.add_command(label="Procesador de Carpetas", command=self.mostrar_procesador_carpetas)
        herramientas_menu.add_command(label="Procesador de Excel", command=self.mostrar_limpiar_excel)
        herramientas_menu.add_command(label="PDA", command=self.mostrar_PDA)
        menuBar.add_cascade(label="Herramientas", menu=herramientas_menu)


        # ================== Configuración ==================
        config_menu = tk.Menu(menuBar, tearoff=0)
        menuBar.add_cascade(label="Configuración", menu=config_menu)

        # --- Submenú Correo ---
        correo_menu = tk.Menu(config_menu, tearoff=0)
        config_menu.add_cascade(label="Correo", menu=correo_menu)

        # Opciones dentro de Correo
        correo_menu.add_command(label="Nuevo correo", command=self.mostrar_config_correo)
        correo_menu.add_command(label="Cuerpo de correo", command=self.mostrar_config_cuerpo)
        correo_menu.add_separator()
        correo_menu.add_command(label="Configuración avanzada", command=self.config_avanzada)

        # ================== Ayuda ==================
        ayuda_menu = tk.Menu(menuBar, tearoff=0)
        ayuda_menu.add_command(
            label="Acerca de",
            command=lambda: tk.messagebox.showinfo(
                "Acerca de",
                "AutomatiSCD - by Mauro 😎\nFunción 'Procesador Excel' creada por Enrique Ahumada"
            )
        )
        menuBar.add_cascade(label="Ayuda", menu=ayuda_menu)

        # Aplicar menú
        self.config(menu=menuBar)

        base_path = getattr(sys, "_MEIPASS", os.path.abspath("."))
        icon_path = os.path.join(base_path, "assets", "app.ico")
        
        self.iconbitmap(icon_path)

        self.menu_inicial = MenuInicial(
            self, 
            self.mostrar_procesador_carpetas, 
            self.mostrar_limpiar_excel, 
            self.mostrar_PDA,
            self.mostrar_correo
            )
        
        self.procesador_carpetas = ProcesadorCarpetas(
            self, self.mostrar_menu, 
        )
        self.limpiar_excel = LimpiarExcel(
            self, self.mostrar_menu
        )
        
        self.pda = uiPDA(
            self, self.mostrar_menu, 
            self.pda_f, self.pda_w, 
            self.registroW, self.registroF
        )
        
        self.correo = Correo(
            self, self.mostrar_menu
        )
        
        usuario_guardado = obtener_usuario()
        if usuario_guardado:
            self.usuario = usuario_guardado
            self.usuario_var.set(usuario_guardado)
            self.mostrar_menu()
        else:
            self.mostrar_login()

    def mostrar_menu(self):
        self._ocultar_todos()
        self.menu_inicial.pack(fill="both", expand=True)
        self.geometry("400x300")
        self.resizable(False, False)

    def mostrar_procesador_carpetas(self):
        self._ocultar_todos()
        self.procesador_carpetas.pack(fill="both", expand=True)
        self.geometry("900x600")
        self.resizable(False, False)
        
    def mostrar_PDA(self):
        self._ocultar_todos()
        self.pda.pack(fill="both", expand=True)
        self.update_idletasks()
        self.geometry("")
        self.resizable(False, False)
        
    def mostrar_limpiar_excel(self):
        self._ocultar_todos()
        self.limpiar_excel.pack(fill="both", expand=True)
        # Ajustado automatico y que no se pueda modificar la ventana
        self.update_idletasks()
        self.geometry("")
        self.resizable(False, False)
        
    def mostrar_correo(self):
        self._ocultar_todos()
        self.correo.pack(fill="both", expand=True)
        self.update_idletasks()
        self.geometry("")
        self.resizable(False, False)
    
    def mostrar_config_correo(self):
        self.correo.mostrar_config_correo()
        
    def mostrar_config_cuerpo(self):
        self.correo.mostrar_config_cuerpo()
        
    def config_avanzada(self):
        self.correo.config_avanzada()
    
    def _ocultar_todos(self):
        for widget in self.winfo_children():
            widget.pack_forget()
            
    def mostrar_login(self):
        self.login_frame = ttk.Frame(self, padding=50)
        self.login_frame.grid(row=0, column=0, sticky="nsew")

        ttk.Label(self.login_frame, text="Nombre de usuario:").grid(
            row=0, column=0, sticky="w"
        )
        self.entry_usuario = ttk.Entry(
            self.login_frame, width=30, textvariable=self.usuario_var
        )
        self.entry_usuario.grid(row=1, column=0, pady=5)
        self.entry_usuario.focus()

        btn = ttk.Button(self.login_frame, text="Entrar", command=self.on_login)
        btn.grid(row=2, column=0, pady=10)
            
    def on_login(self):
        nombre = self.usuario_var.get().strip()
        if not nombre:
            messagebox.showerror("Error", "Ingresa un nombre válido")
            return

        self.usuario = nombre
        guardar_usuario(nombre)  

        self.login_frame.destroy()
        self.mostrar_menu()
        

if __name__ == "__main__":
    App().mainloop()
