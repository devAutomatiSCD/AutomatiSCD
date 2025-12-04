from openpyxl import load_workbook
from pathlib import Path
import os, re, unicodedata

def limpiar_texto(s):
    if s is None:
        return ""

    s = str(s)

    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = re.sub(r"[^A-Za-z ]", " ", s)
    s = re.sub(r"\s{2,}", " ", s)
    s = s.strip()
    s = s.upper()

    return s

def procesar_excel(
    ruta_excel: str,
    ruta_carpeta: str
):
    try:
        rutaExcel = Path(ruta_excel)
        rutaCarpeta = Path(ruta_carpeta)

        if not rutaExcel.exists():
            print (f"El archivo no existe: {rutaExcel}")
            return False, None

        rutaCarpeta.mkdir(parents=True, exist_ok=True)
        dest_resuelto = rutaCarpeta.resolve()

        base_name = rutaExcel.name        
        nombre, ext = os.path.splitext(base_name)
        ruta_salida = dest_resuelto / f"{nombre}_LIMPIO{ext}"

        wb = load_workbook(rutaExcel)
        ws = wb.active

        if ws.max_row > 0:
            ws.delete_rows(1)

        for row in ws.iter_rows():
            for cell in row:
                if cell.value is not None:
                    cell.value = limpiar_texto(cell.value)
                    
        wb.save(ruta_salida)

        print(f"Excel limpio guardado en: {ruta_salida}")
        return True, ruta_salida

    except Exception as e:
        return {"error": str(e)}
