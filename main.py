import tkinter as tk
from tkinter import ttk, messagebox, PhotoImage
import os, sys, threading, socket

APP_PORT = 35304
APP_HOST = "127.0.0.1"

def notify_running_instance():
    """Devuelve True si logró avisar a una instancia ya corriendo."""
    try:
        with socket.create_connection((APP_HOST, APP_PORT), timeout=0.25) as s:
            s.sendall(b"SHOW")
        return True
    except OSError:
        return False

def start_instance_server(app):
    """Corre en la instancia principal: escucha mensajes y trae la ventana al frente."""
    def bring_to_front():
        try:
            app.deiconify()
            app.lift()
            app.attributes("-topmost", True)
            app.update_idletasks()
            app.focus_force()
            app.after(150, lambda: app.attributes("-topmost", False))
        except Exception:
            pass

    def server():
        srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind((APP_HOST, APP_PORT))
        srv.listen(5)

        while True:
            conn, _ = srv.accept()
            try:
                data = conn.recv(1024)
                if data.startswith(b"SHOW"):
                    app.after(0, bring_to_front)
            finally:
                try: conn.close()
                except: pass

    threading.Thread(target=server, daemon=True).start()

from ui.ui_procesador_carpetas import ProcesadorCarpetas
from ui.ui_limpiar_excel import LimpiarExcel
from ui.ui_pda import uiPDA
from ui.ui_correo import Correo
from ui.ui_scanner.ui_scanner import ScannerContainer
from utils.config_manager import guardar_correos_config, verificar_estructura, obtener_carpeta_base, guardar_usuario, obtener_usuario

class MenuInicial(ttk.Frame):
    def __init__(
        self, master,
        mostrar_procesador_carpetas,
        mostrar_limpiar_excel,
        mostrar_PDA,
        mostrar_correo,
        mostrar_scanner,
        **kwargs
    ):
        super().__init__(master, **kwargs)

        # Dos columnas iguales
        self.grid_columnconfigure(0, weight=1, uniform="x")
        self.grid_columnconfigure(1, weight=1, uniform="x")

        ttk.Label(
            self,
            text="AutomatiSCD",
            font=("Arial", 20, "bold")
        ).grid(row=0, column=0, columnspan=2, pady=(30, 25))

        ttk.Button(self, text="Procesador de Carpetas",
            command=mostrar_procesador_carpetas
        ).grid(row=1, column=0, padx=10, pady=5, sticky="nsew")

        ttk.Button(self, text="Procesador de Excel",
            command=mostrar_limpiar_excel
        ).grid(row=1, column=1, padx=10, pady=5, sticky="nsew")

        ttk.Button(self, text="PDA",
            command=mostrar_PDA
        ).grid(row=2, column=0, padx=10, pady=5, sticky="nsew")

        ttk.Button(self, text="Correo (en proceso)",
            command=mostrar_correo
        ).grid(row=2, column=1, padx=10, pady=5, sticky="nsew")

        ttk.Button(self, text="Scanner",
            command=mostrar_scanner
        ).grid(row=3, column=0, columnspan=2, padx=10, pady=5, sticky="nsew")


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

        if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))

        icon_path = os.path.join(base_path, "assets", "app.png")
        self.iconphoto(True, PhotoImage(file=icon_path))

        self.menu_inicial = MenuInicial(
            self, 
            self.mostrar_procesador_carpetas, 
            self.mostrar_limpiar_excel, 
            self.mostrar_PDA,
            self.mostrar_correo,
            self.mostrar_scanner
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
        
        self.scanner = ScannerContainer(
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
        self.update_idletasks()
        self.geometry("")
        self.resizable(False, False)

    def mostrar_procesador_carpetas(self):
        self._ocultar_todos()
        self.procesador_carpetas.pack(fill="both", expand=True)
        self.update_idletasks()
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
        
    def mostrar_scanner(self):
        self._ocultar_todos()
        self.scanner.pack(fill="both", expand=True)
        self.geometry("250x150")    
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
    if notify_running_instance():
        sys.exit(0)

    app = App()
    start_instance_server(app) 
    app.mainloop()