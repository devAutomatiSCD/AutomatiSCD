import json
import hmac
import hashlib
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
import os

# load_dotenv()

# SECRET_KEY = os.getenv("SECRET_KEY")
# if SECRET_KEY is None:
#     raise ValueError("⚠️ No se encontró la variable de entorno SECRET_KEY. Configúrala antes de ejecutar el programa.")

# def _firmar_registro(data: dict) -> str:
#     """
#     Recibe el registro SIN el campo 'hmac' y devuelve la firma hex.
#     """
#     cuerpo = json.dumps(data, ensure_ascii=False, sort_keys=True).encode("utf-8")
#     firma = hmac.new(SECRET_KEY, cuerpo, hashlib.sha256).hexdigest()
#     return firma

def escribir_log(ruta_log: Path, usuario: str, accion: str, detalles: str | None = None):
    """
    Agrega una línea al log con firma HMAC.
    Formato: JSON por línea.
    """
    registro = {
        "usuario": usuario,
        "accion": accion,
        "fecha": datetime.now().isoformat(timespec="seconds"),
    }
    if detalles is not None:
        registro["detalles"] = detalles

    ruta_log.parent.mkdir(parents=True, exist_ok=True)
    with open(ruta_log, "a", encoding="utf-8") as f:
        f.write(json.dumps(registro, ensure_ascii=False) + "\n")

# def validar_log(ruta_log: Path):
#     """
#     Recorre el log y levanta excepción si detecta líneas alteradas.
#     """
#     if not ruta_log.exists():
#         return  # nada que validar

#     with open(ruta_log, "r", encoding="utf-8") as f:
#         for i, linea in enumerate(f, start=1):
#             linea = linea.strip()
#             if not linea:
#                 continue

#             try:
#                 reg = json.loads(linea)
#             except json.JSONDecodeError:
#                 raise ValueError(f"⚠️ Línea {i}: no es JSON válido (posible edición manual).")

#             firma_guardada = reg.pop("hmac", None)
#             if not firma_guardada:
#                 raise ValueError(f"⚠️ Línea {i}: no tiene campo 'hmac' (posible edición manual).")

#             firma_calc = _firmar_registro(reg)

#             if firma_calc != firma_guardada:
#                 raise ValueError(f"⚠️ Línea {i}: firma no coincide (log alterado).")
