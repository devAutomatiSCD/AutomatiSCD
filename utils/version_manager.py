from tkinter import messagebox
from utils.config_manager import obtener_version_vista, guardar_version_vista
from utils.app_version import VERSION_ACTUAL, CAMBIOS_POR_VERSION

def obtener_version_actual():
    return VERSION_ACTUAL

def obtener_cambios_version(version: str):
    return CAMBIOS_POR_VERSION.get(version, [])

def mostrar_novedades_si_corresponde():
    version_actual = obtener_version_actual()
    version_vista = obtener_version_vista()

    if version_vista == version_actual:
        return

    cambios = obtener_cambios_version(version_actual)

    encabezado = f"AutomatiSCD v{version_actual}"

    if cambios:
        detalle = "\n".join(f"• {cambio}" for cambio in cambios)
        mensaje = f"{encabezado}\n\nCambios:\n{detalle}"
    else:
        mensaje = f"{encabezado}\n\nNo hay detalles registrados para esta versión."

    messagebox.showinfo("Nueva versión disponible", mensaje)
    guardar_version_vista(version_actual)