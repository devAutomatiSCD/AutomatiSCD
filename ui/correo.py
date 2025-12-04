import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.scrolledtext import ScrolledText
from utils.config_manager import cargar_config, guardar_correos_config


class Correo(ttk.Frame):
    def __init__(self, master, on_volver_menu, **kwargs):
        super().__init__(master, **kwargs)
        
        self.selected_emails = []

        main = ttk.Frame(self, padding=20)
        main.pack(fill="both", expand=True)
        
        ttk.Button(main, text="⬅ Volver al menú", command=on_volver_menu).pack(
            anchor="w", padx=10, pady=(10, 0)
        )

        frm = ttk.Frame(main, padding=10)
        frm.pack(fill="x")

        style = ttk.Style()
        style.configure("Big.TEntry", font=("Arial", 14))

        self.frame_para = ttk.Frame(frm)
        self.frame_para.grid(row=0, column=0, sticky="w", pady=(0, 10))

        ttk.Label(self.frame_para, text="Para:").grid(row=0, column=0, sticky="e", padx=5, pady=5)

        self.entry_para = ttk.Entry(self.frame_para, width=50, style="Big.TEntry")
        self.entry_para.grid(row=0, column=1, padx=5, pady=5)

        self.frame_destinos = ttk.Frame(frm)
        self.frame_destinos.grid(row=1, column=0, columnspan=2, pady=10, sticky="w")

        ttk.Label(self.frame_destinos, text="Destinatarios:").grid(
            row=0, column=0, sticky="w", padx=5, pady=(0, 5)
        )

        self.refrescar_destinatarios_rapidos()
        
        self.frame_body = ttk.Frame(frm)
        self.frame_body.grid(row=2, column=0, columnspan=2, pady=10, sticky="w")
        
        self.body = ScrolledText(self.frame_body, width=60, height=10, font=("Arial", 10))
        self.body.grid(row=0, column=0, sticky="w", padx=5, pady=(0, 5))

    def refrescar_destinatarios_rapidos(self):
        """Lee el JSON y repinta los botones de destinatarios rápidos."""
        for w in self.frame_destinos.grid_slaves():
            fila = int(w.grid_info().get("row", 1))
            if fila > 0:
                w.destroy()

        cfg = cargar_config()
        self.correos_destino = cfg.get("correos_destino", [])

        def actualizar_para():
            self.entry_para.delete(0, tk.END)
            self.entry_para.insert(0, "; ".join(self.selected_emails))

        def toggle_destino(email: str, button: tk.Button):
            if email in self.selected_emails:
                self.selected_emails.remove(email)
                button.config(relief="raised")
            else:
                self.selected_emails.append(email)
                button.config(relief="sunken")
            actualizar_para()

        for idx, item in enumerate(self.correos_destino, start=1):
            nombre = item.get("nombre", f"Dest {idx}")
            email = item.get("email", "")
            if not email:
                continue

            btn = tk.Button(
                self.frame_destinos,
                text=nombre,
                width=18,
            )
            btn.config(command=lambda m=email, b=btn: toggle_destino(m, b))

            fila = (idx - 1) // 4 + 1
            col = (idx - 1) % 4
            btn.grid(row=fila, column=col, padx=3, pady=3, sticky="w")

    def mostrar_config_correo(self):
        ventana = tk.Toplevel(self)
        ventana.title("Correos")
        ventana.resizable(False, False)

        frm = ttk.Frame(ventana, padding=10)
        frm.grid(row=0, column=0, sticky="w")

        ttk.Label(frm, text="Agregar correo", padding=10,
                font=("Arial", 10, "bold")).grid(row=0, column=0, columnspan=2)

        ttk.Label(frm, text="Nombre", padding=10).grid(row=1, column=0, sticky="w")
        eyNombre = ttk.Entry(frm)
        eyNombre.grid(row=1, column=1, sticky="w")

        ttk.Label(frm, text="Email", padding=10).grid(row=2, column=0, sticky="w")
        eyEmail = ttk.Entry(frm)
        eyEmail.grid(row=2, column=1, sticky="w")

        ttk.Button(
            frm,
            text="Crear",
            command=lambda: self._guardar_correos_config_ui(eyNombre, eyEmail, ventana)
        ).grid(row=3, column=0, sticky="w", padx=10, pady=10)
        
        ventana.transient(self)   # se "pega" a la ventana principal
        ventana.grab_set()         # BLOQUEA todo lo demás
        self.wait_window(ventana)  # espera hasta que se cierre

    def _guardar_correos_config_ui(self, entry_nombre, entry_email, ventana):
        usuario = entry_nombre.get().strip()
        email = entry_email.get().strip()

        if not usuario or not email:
            messagebox.showerror("Error", "Nombre y correo son obligatorios.")
            return

        resultado = guardar_correos_config(usuario, email)

        if resultado:
            messagebox.showinfo("Información", "El correo se creó correctamente.")
        else:
            messagebox.showinfo("Información", "El usuario ya estaba, se eliminó de la lista.")

        self.refrescar_destinatarios_rapidos()
        ventana.destroy()
