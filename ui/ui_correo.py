import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.scrolledtext import ScrolledText
from utils.config_manager import cargar_config, guardar_correos_config, guardar_cuerpo_config


class Correo(ttk.Frame):
    def __init__(self, master, on_volver_menu, **kwargs):
        super().__init__(master, **kwargs)
        
        self.selected_emails = []
        self.selected_body = []

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
        
        ttk.Label(self.frame_para, text="CC:").grid(row=1, column=0, sticky="e", padx=5, pady=5)

        self.entry_cc = ttk.Entry(self.frame_para, width=50, style="Big.TEntry")
        self.entry_cc.grid(row=1, column=1, padx=5, pady=5)

        self.frame_destinos = ttk.Frame(frm)
        self.frame_destinos.grid(row=1, column=0, columnspan=2, pady=10, sticky="w")

        ttk.Label(self.frame_destinos, text="Destinatarios:").grid(
            row=0, column=0, sticky="w", padx=5, pady=(0, 5)
        )
        
        self.refrescar_destinatarios_rapidos("correoNuevo")
        
        self.frame_cuerpo = ttk.Frame(frm)
        self.frame_cuerpo.grid(row=2, column=0, columnspan=2, pady=10, sticky="w")
        
        ttk.Label(self.frame_cuerpo, text="Cuerpos:").grid(
            row=0, column=0, sticky="w", padx=5, pady=(0, 5)
        )
        
        self.refrescar_destinatarios_rapidos("cuerpo")

        self.frame_body = ttk.Frame(frm)
        self.frame_body.grid(row=3, column=0, columnspan=2, pady=10, sticky="w")
        
        self.body = ScrolledText(self.frame_body, width=60, height=10, font=("Arial", 10))
        self.body.grid(row=0, column=0, sticky="w", padx=5, pady=(0, 5))
        
        self.frame_footer = ttk.Frame(frm)
        self.frame_footer.grid(row=4, column=0, columnspan=2, pady=10, sticky="w")
        
        self.enviar = ttk.Button(self.frame_footer, text="Enviar")
        self.enviar.grid(row=0, column=0, pady=5, sticky="w")

    def refrescar_destinatarios_rapidos(self, tipo):

        if tipo == "correoNuevo":
            frame = self.frame_destinos
        elif tipo == "cuerpo":
            frame = self.frame_cuerpo
        else:
            return

        for w in frame.grid_slaves():
            fila = int(w.grid_info().get("row", 1))
            if fila > 0:
                w.destroy()

        cfg = cargar_config()

        if tipo == "correoNuevo":
            destino = cfg.get("correos_destino", [])
            selected = self.selected_emails
        else:  
            destino = cfg.get("body_correos", [])
            selected = self.selected_body

        def actualizar_para():
            if tipo != "correoNuevo":
                return
            self.entry_para.delete(0, tk.END)
            self.entry_para.insert(0, "; ".join(selected))

        def toggle_destino(nombre: str, email: str, cuerpo_texto: str, button: tk.Button):
            if tipo == "correoNuevo":
                valor = email

                if valor in selected:
                    selected.remove(valor)
                    button.config(relief="raised")
                else:
                    selected.append(valor)
                    button.config(relief="sunken")

                actualizar_para()

            else:
                for w in frame.grid_slaves():
                    f = int(w.grid_info().get("row", 1))
                    if f > 0:
                        w.config(relief="raised")

                selected.clear()
                selected.append(nombre)
                button.config(relief="sunken")

                self.body.delete("1.0", "end")
                self.body.insert("1.0", cuerpo_texto)

        for idx, item in enumerate(destino, start=1):
            nombre = item.get("nombre", f"Item {idx}")

            if tipo == "correoNuevo":
                email = item.get("email", "")
                cuerpo_texto = ""
                if not email:
                    continue
            else:  # cuerpo
                email = ""
                cuerpo_texto = item.get("cuerpo", "")
                if not cuerpo_texto:
                    continue

            btn = tk.Button(frame, text=nombre, width=18)

            btn.config(
                command=lambda n=nombre, e=email, c=cuerpo_texto, b=btn: toggle_destino(n, e, c, b)
            )

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

        self.refrescar_destinatarios_rapidos("correoNuevo")
        ventana.destroy()
        
    
    def _guardar_cuerpo_config_ui(self, nombre, cuerpo, ventana):
        cuerpo = cuerpo.get("1.0", "end-1c").strip()
        nombre = nombre.get().strip()
        
        if not cuerpo or not nombre:
            messagebox.showerror("Error", "Nombre y cuerpo de correo son obligatorios.")
            return

        resultado = guardar_cuerpo_config(nombre, cuerpo)

        if resultado:
            messagebox.showinfo("Información", "El cuerpo de correo se creó correctamente.")
        else:
            messagebox.showinfo("Información", "El cuerpo ya estaba registrado, se eliminó de la lista.")

        self.refrescar_destinatarios_rapidos("cuerpo")
        ventana.destroy()

    def mostrar_config_cuerpo(self):
        ventana = tk.Toplevel(self)
        ventana.title("Correos")
        ventana.resizable(False, False)

        frm = ttk.Frame(ventana, padding=10)
        frm.grid(row=0, column=0, sticky="w")

        # 🔧 Esta línea es CLAVE para que no queden espacios raros
        frm.columnconfigure(1, weight=1)

        ttk.Label(
            frm,
            text="Agregar Cuerpo",
            padding=10,
            font=("Arial", 10, "bold")
        ).grid(row=0, column=0, columnspan=2)

        ttk.Label(frm, text="Nombre:").grid(row=1, column=0, sticky="w")

        eyNombre = ttk.Entry(frm)
        eyNombre.grid(row=1, column=1, sticky="w", padx=0)

        body = ScrolledText(frm, width=60, height=10, font=("Arial", 10))
        body.grid(row=2, column=0, columnspan=2, sticky="w", pady=(2, 0))

        ttk.Button(
            frm,
            text="Crear",
            command=lambda: self._guardar_cuerpo_config_ui(eyNombre, body, ventana)
        ).grid(row=3, column=0, sticky="w", padx=10, pady=10)

        ventana.transient(self)    # se "pega" a la ventana principal
        ventana.grab_set()         # BLOQUEA todo lo demás
        self.wait_window(ventana) # espera hasta que se cierre
    
    def config_avanzada(self):
        ventana = tk.Toplevel(self)
        ventana.title("Configuración Avanzada")
        ventana.resizable(False, False)

        frm = ttk.Frame(ventana, padding=10)
        frm.grid(row=0, column=0, sticky="w")

        cfg = cargar_config()
        correos = cfg.get("correos_destino", [])
        cuerpos = cfg.get("body_correos", [])

        # =======================
        # TABLA CORREOS
        # =======================
        ttk.Label(frm, text="Correos").grid(row=0, column=0, sticky="w")

        tv_correos = ttk.Treeview(frm, columns=("nombre", "email"), show="headings", height=6)
        tv_correos.grid(row=1, column=0, sticky="w")

        tv_correos.heading("nombre", text="Nombre")
        tv_correos.heading("email", text="Email")

        tv_correos.column("nombre", width=150)
        tv_correos.column("email", width=220)

        for item in correos:
            tv_correos.insert("", "end", values=(item["nombre"], item["email"]))

        frame_btn_correos = ttk.Frame(frm)
        frame_btn_correos.grid(row=2, column=0, pady=5, sticky="w")

        ttk.Button(
            frame_btn_correos,
            text="Editar",
            command=lambda: self._editar_correo(tv_correos)
        ).grid(row=0, column=0, padx=5)

        ttk.Button(
            frame_btn_correos,
            text="Eliminar",
            command=lambda: self._eliminar_correo(tv_correos)
        ).grid(row=0, column=1, padx=5)

        # =======================
        # TABLA CUERPOS
        # =======================
        ttk.Label(frm, text="Cuerpos").grid(row=0, column=1, padx=20, sticky="w")

        tv_cuerpos = ttk.Treeview(frm, columns=("nombre",), show="headings", height=6)
        tv_cuerpos.grid(row=1, column=1, sticky="w", padx=20)

        tv_cuerpos.heading("nombre", text="Nombre")
        tv_cuerpos.column("nombre", width=220)

        for item in cuerpos:
            tv_cuerpos.insert("", "end", values=(item["nombre"],))

        frame_btn_cuerpos = ttk.Frame(frm)
        frame_btn_cuerpos.grid(row=2, column=1, pady=5, sticky="w", padx=20)

        ttk.Button(
            frame_btn_cuerpos,
            text="Editar",
            command=lambda: self._editar_cuerpo(tv_cuerpos)
        ).grid(row=0, column=0, padx=5)

        ttk.Button(
            frame_btn_cuerpos,
            text="Eliminar",
            command=lambda: self._eliminar_cuerpo(tv_cuerpos)
        ).grid(row=0, column=1, padx=5)

        ventana.transient(self)
        ventana.grab_set()
        self.wait_window(ventana)

    def _eliminar_correo(self, tree):
        sel = tree.selection()
        if not sel:
            messagebox.showerror("Error", "Selecciona un correo")
            return

        nombre, email = tree.item(sel[0])["values"]
        guardar_correos_config(nombre, email)  # tu función ya elimina si existe
        tree.delete(sel[0])
        self.refrescar_destinatarios_rapidos("correoNuevo")


    def _editar_correo(self, tree):
        sel = tree.selection()
        if not sel:
            messagebox.showerror("Error", "Selecciona un correo")
            return

        nombre, email = tree.item(sel[0])["values"]
        messagebox.showinfo("Editar", f"Aquí puedes abrir un modal para editar:\n{nombre} - {email}")


    def _eliminar_cuerpo(self, tree):
        sel = tree.selection()
        if not sel:
            messagebox.showerror("Error", "Selecciona un cuerpo")
            return

        nombre = tree.item(sel[0])["values"][0]
        guardar_cuerpo_config(nombre, "")  # tu función ya elimina si existe
        tree.delete(sel[0])
        self.refrescar_destinatarios_rapidos("cuerpo")


    def _editar_cuerpo(self, tree):
        sel = tree.selection()
        if not sel:
            messagebox.showerror("Error", "Selecciona un cuerpo")
            return

        nombre = tree.item(sel[0])["values"][0]
        messagebox.showinfo("Editar", f"Aquí puedes abrir un modal para editar:\n{nombre}")
