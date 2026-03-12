VERSION_ACTUAL = "1.0.0"

CAMBIOS_POR_VERSION = {
    "1.0.0": [
        "Se agregó sistema de notificación de actualizaciones.",
        "Se detecta automáticamente la carpeta base.",
        "Se agregó verificación de conexión a VPN."
    ]
}

def obtener_partes_version():
    major, minor, patch = VERSION_ACTUAL.split(".")
    return int(major), int(minor), int(patch)