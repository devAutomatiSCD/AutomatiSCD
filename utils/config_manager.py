# utils/config_manager.py
import json
import os
from pathlib import Path
from tkinter import filedialog, messagebox
from datetime import datetime

RUTA_CONFIG = Path(os.getenv("APPDATA")) / "AutomatiSCD" / "config.json"
RUTA_CONFIG.parent.mkdir(parents=True, exist_ok=True)
ahora = datetime.now()

def cargar_config():
    if not RUTA_CONFIG.exists():
        return {
            "correos_destino": [],
            "body_correos": []
        }
    with open(RUTA_CONFIG, "r", encoding="utf-8") as f:
        return json.load(f)

def guardar_config(cfg):
    with open(RUTA_CONFIG, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=4, ensure_ascii=False)

def obtener_carpeta_base(root):
    while True:
        cfg = cargar_config()
        carpeta_guardada = cfg.get("carpeta_base")

        if carpeta_guardada and Path(carpeta_guardada).exists():
            return Path(carpeta_guardada)

        if carpeta_guardada and not Path(carpeta_guardada).exists():
            messagebox.showwarning(
                "Carpeta base no válida",
                "La carpeta base ya no existe o fue movida.\nSelecciona una nueva."
            )
        else:
            messagebox.showinfo(
                "Seleccionar carpeta base",
                "Selecciona la carpeta BASE que contiene Reporte y PDAs."
            )

        carpeta = filedialog.askdirectory(
            initialdir="C:/",
            title="Seleccionar carpeta base"
        )

        if not carpeta:
            reintentar = messagebox.askyesno(
                "Sin carpeta seleccionada",
                "¿Quieres volver a intentar?"
            )
            if reintentar:
                continue
            else:
                return None
        else:
            cfg["carpeta_base"] = carpeta
            guardar_config(cfg)
            return Path(carpeta)

def verificar_estructura(carpeta_base: Path):
    errores = []

    carpetas = {
        "Registro": carpeta_base / "Registro",
        "PDA": carpeta_base / "PDA",
    }

    # for nombre, ruta in carpetas.items():
    #     if not ruta.exists():
    #         errores.append(f"Falta carpeta: {nombre}")
    #         continue

    #     txts = list(ruta.glob("*.txt"))
    #     if len(txts) < 2:
    #         errores.append(f"{nombre} debe tener al menos 2 archivos .txt (tiene {len(txts)})")

    return errores


def guardar_usuario(usuario: str):
    cfg = cargar_config()
    cfg["usuario"] = usuario
    cfg["hora_user_creara"] = ahora.strftime("%d-%m-%Y - %H:%M:%S") 
    guardar_config(cfg)
    
def obtener_usuario():
    cfg = cargar_config()
    return cfg.get("usuario")


def guardar_correos_config(usuario, email):
    cfg = cargar_config()
    lista = cfg.get("correos_destino", [])

    print(usuario, email)

    item = {
        "nombre": usuario,
        "email": email
    }

    if item in lista:
        lista.remove(item)
        cfg["correos_destino"] = lista
        guardar_config(cfg)
        return False
    else:
        lista.append(item)
        cfg["correos_destino"] = lista
        guardar_config(cfg)
        return True
    