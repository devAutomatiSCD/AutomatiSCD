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
        
CARPETA_BASE_DEFAULT = Path(r"M:\Documentacion\publica\AutomatiSCD")    

def obtener_carpeta_base():
    cfg = cargar_config()

    # 1. Intentar ruta fija
    if CARPETA_BASE_DEFAULT.exists():
        errores = verificar_estructura(CARPETA_BASE_DEFAULT)
        if not errores:
            cfg["carpeta_base"] = str(CARPETA_BASE_DEFAULT)
            guardar_config(cfg)
            return CARPETA_BASE_DEFAULT

    # 2. Intentar ruta guardada en config
    carpeta_guardada = cfg.get("carpeta_base")
    if carpeta_guardada:
        ruta = Path(carpeta_guardada)
        if ruta.exists():
            errores = verificar_estructura(ruta)
            if not errores:
                return ruta

    # 3. Si no existe la unidad M o movieron la carpeta
    messagebox.showwarning(
        "Carpeta no encontrada",
        "No se encontró la carpeta base en o no esta conectado a la VPN:\n\n"
        f"{CARPETA_BASE_DEFAULT}\n\n"
        "Selecciona dónde está ahora."
    )

    carpeta = filedialog.askdirectory(title="Seleccionar carpeta AutomatiSCD")

    if not carpeta:
        return None

    carpeta_path = Path(carpeta)
    errores = verificar_estructura(carpeta_path)

    if errores:
        messagebox.showerror(
            "Estructura incorrecta",
            "\n".join(errores)
        )
        return None

    cfg["carpeta_base"] = str(carpeta_path)
    guardar_config(cfg)

    return carpeta_path


def verificar_estructura(carpeta_base: Path):
    errores = []

    carpetas = {
        "Registro": carpeta_base / "Registro",
        "PDA": carpeta_base / "PDA",
    }

    for nombre, ruta in carpetas.items():
        if not ruta.exists():
            errores.append(f"Falta carpeta: {nombre}")
            continue
        
    return errores

def guardar_usuario(usuario: str):
    cfg = cargar_config()
    cfg["usuario"] = usuario
    cfg["hora_user_creara"] = ahora.strftime("%d-%m-%Y - %H:%M:%S") 
    guardar_config(cfg)
    
def obtener_usuario():
    cfg = cargar_config()
    return cfg.get("usuario")

def set_api_key(API_KEY: str):
    cfg = cargar_config()
    cfg["API_KEY"] = API_KEY
    guardar_config(cfg)
    
def obtener_API_KEY():
    cfg = cargar_config()
    return cfg.get("API_KEY")

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
    
def guardar_cuerpo_config(nombre, cuerpo):
    cfg = cargar_config()
    
    lista = cfg.get("body_correos", [])
    
    item = {
        "nombre": nombre,
        "cuerpo": cuerpo
    }
    
    if item in lista:
        lista.remove(item)
        cfg["body_correos"] = lista
        guardar_config(cfg)
        return False
    else:
        lista.append(item)
        cfg["body_correos"] = lista
        guardar_config(cfg)
        return True
    
def guardar_version_vista(version: str):
    cfg = cargar_config()
    cfg["ultima_version_vista"] = version
    guardar_config(cfg)

def obtener_version_vista():
    cfg = cargar_config()
    return cfg.get("ultima_version_vista")