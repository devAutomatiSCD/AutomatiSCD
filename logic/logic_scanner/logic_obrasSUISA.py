import pdfplumber
import re, os, csv, unicodedata
from utils.config_manager import obtener_carpeta_base
# =========================
# Parsers
# =========================

def parse_porcentaje(p):
    parts = p.split()

    soc1 = parts[0] if len(parts) > 0 else None
    p1   = parts[1] if len(parts) > 1 else None
    soc2 = parts[2] if len(parts) > 2 else None
    p2   = parts[3] if len(parts) > 3 else None

    return {
        "porcentaje_1": p1,
        "porcentaje_2": p2,
        "soc1": soc1,
        "soc2": soc2
    }

def parse_ipi(p):
    p = p.replace(" ", "")
    p= p.lstrip("0")
    return p.replace(".", "").strip()

def parse_name(n: str) -> str:
    n = n.replace("\n", " ").replace("\r", " ")
    n = n.replace("Title", "").replace("Subtitle", "")

    n = unicodedata.normalize("NFD", n)
    n = n.encode("ascii", "ignore").decode("utf-8")

    return re.sub(r"\s+", " ", n).strip()

def parse_pct(v: str) -> float:
    if v is None:
        return 0.0
    # "12,50" -> 12.5
    return float(v.replace(",", "."))

def fmt_pct(v: float) -> str:
    # 12.5 -> "12,50"
    return f"{v:.2f}".replace(".", ",")

def normalizar_nombre(texto: str) -> str:
    texto = unicodedata.normalize("NFKD", texto)
    
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    
    texto = re.sub(r"[^A-Za-z\s]", "", texto)
    
    texto = re.sub(r"\s+", " ", texto).strip()

    return texto

# =========================
# Scanner
# =========================

def scanner(ruta_pdf, folio, stop_event=None):
    
    def check_cancel():
        return stop_event is not None and stop_event.is_set()
    
    obras = {}

    with pdfplumber.open(ruta_pdf) as pdf:
        tablas = []
        for page in pdf.pages:
            tablas.extend(page.extract_tables() or [])

    for tabla in tablas:
        if check_cancel():
            return {"cancelado": True}
        nombre_obra = parse_name(tabla[0][0])

        if nombre_obra not in obras:
            obras[nombre_obra] = {
                "obra": nombre_obra,
                "reparto": {}  # clave = IPI
            }

        for fila in tabla:
            if check_cancel():
                return {"cancelado": True}
            if not (fila[1] and fila[2] and fila[3]):
                continue

            # -------- CAES --------
            caes = [
                l.strip()
                for l in fila[0].split("\n")[1:]
                if l.strip()
            ]

            # -------- NOMBRES --------
            nombres = [
                l.strip()
                for l in fila[1].split("\n")[1:]
                if l.strip() and not re.fullmatch(r"[A-Z]{2}", l.strip())
            ]

            # -------- IPIs --------
            ipis = [
                l.strip()
                for l in fila[2].split("\n")[1:]
                if l.strip()
            ]

            # -------- PORCENTAJES --------
            porcentajes_raw = [
                l.strip()
                for l in fila[3].split("\n")[3:]
                if l.strip()
            ]

            for nombre, ipi_raw, porc_raw, cae in zip(nombres, ipis, porcentajes_raw, caes):
                if check_cancel():
                    return {"cancelado": True}
                ipi = parse_ipi(ipi_raw)
                p = parse_porcentaje(porc_raw)

                p1 = parse_pct(p["porcentaje_1"])
                p2 = parse_pct(p["porcentaje_2"])

                reparto = obras[nombre_obra]["reparto"]

                if ipi in reparto:
                    reparto[ipi]["porcentaje_1"] += p1
                    reparto[ipi]["porcentaje_2"] += p2
                else:
                    reparto[ipi] = {
                        "nombre": parse_name(nombre),
                        "caes": cae,
                        "porcentaje_1": p1,
                        "porcentaje_2": p2,
                    }

    export = export_excel(obras, folio, stop_event=stop_event)
    
    if export:
        return True
    
# =========================
# Export
# =========================

def export_excel(obras, folio, stop_event=None):
    
    def check_cancel():
        return stop_event is not None and stop_event.is_set()
    
    # escritorio = os.path.join(
    #     os.path.expanduser("~"),
    #     r"OneDrive - Sociedad Chilena de Autores e Interpretes Musicales\Escritorio"
    # )
    # os.makedirs(escritorio, exist_ok=True)
    
    carpeta_base = obtener_carpeta_base()
    
    ruta_destino = carpeta_base / "MMs" / f"mm_suisa_{folio}.csv"
    
    with open(
        ruta_destino,
        "w",
        newline="",
        encoding="latin-1"
    ) as f:
        writer = csv.writer(f, delimiter=";")

        for _, datas in obras.items():
            if check_cancel():
                return {"cancelado": True}
            # Título de obra (estructura compatible SCD)
            writer.writerow([normalizar_nombre(datas["obra"]), "", "", "", "", ""])
            writer.writerow([])
            writer.writerow([])
            writer.writerow([])

            for ipi, r in datas["reparto"].items():
                if check_cancel():
                    return {"cancelado": True}
                writer.writerow([
                    r["caes"],
                    r["nombre"],
                    fmt_pct(r["porcentaje_1"]),
                    fmt_pct(r["porcentaje_2"]),
                    "",
                    ipi,
                ])

            writer.writerow([])
            
    return True
