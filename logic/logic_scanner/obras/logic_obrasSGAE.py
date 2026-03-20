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
    return p.replace(".", "").strip()

def parse_name(n: str) -> str:
    n = n.replace("\n", " ").replace("\r", " ")
    n = re.sub(r"\s+PAG\.\-\s*\d+$", "", n)

    n = unicodedata.normalize("NFD", n)
    n = n.encode("ascii", "ignore").decode("utf-8")

    return re.sub(r"\s+", " ", n).strip()

def parse_pct(v: str) -> float:
    if not v:
        return 0.0
    try:
        return float(v.replace(",", ".").strip())
    except ValueError:
        return 0.0

def fmt_pct(v: float) -> str:
    # 12.5 -> "12,50"
    return f"{v:.2f}".replace(".", ",")

def normalizar_nombre(texto: str) -> str:
    texto = unicodedata.normalize("NFKD", texto)
    
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    
    texto = re.sub(r"[^A-Za-z\s]", "", texto)
    
    texto = re.sub(r"\s+", " ", texto).strip()

    return texto

def revisar_porcentajes(obras: dict):
    alertas = []

    for obra in obras.values():
        titulo = obra.get("obra") or "(sin título)"
        iswc = obra.get("iswc") or "(sin ISWC)"

        reparto = obra.get("reparto", {}).values()

        suma_p = sum(r.get("porcentaje_1", 0.0) for r in reparto)
        suma_m = sum(r.get("porcentaje_2", 0.0) for r in reparto)

        suma_p = round(suma_p, 2)
        suma_m = round(suma_m, 2)

        if abs(suma_p - 100) > 0.01 or (suma_m > 0 and abs(suma_m - 100) > 0.01):
            alertas.append((titulo, iswc, suma_p, suma_m))

    return alertas

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
                    
    alertas = revisar_porcentajes(obras)
    cantidad_obras = len(obras)

    res = export_excel(obras, folio, stop_event=stop_event)

    if res.get("ok"):
        return {
            "ok": True,
            "alertas": alertas,
            "cantidad_obras": cantidad_obras,
            "ruta_destino": res.get("ruta_destino")
        }
    
# =========================
# Export
# =========================

def export_excel(obras, folio, stop_event=None):
    
    def check_cancel():
        return stop_event is not None and stop_event.is_set()
    
    carpeta_base = obtener_carpeta_base()
    ruta_destino = carpeta_base / "MMs" / f"mm_sgae_{folio}.csv"
    
    fila_por_obra = {}
    fila = 1
    
    with open(ruta_destino, "w", newline="", encoding="latin-1") as f:
        writer = csv.writer(f, delimiter=";")

        for key, datas in obras.items():
            if check_cancel():
                return {"cancelado": True}

            fila_por_obra[key] = fila

            writer.writerow([normalizar_nombre(datas["obra"]), "", "", "", "", ""])
            fila += 1

            writer.writerow([])
            writer.writerow([])
            writer.writerow([])
            fila += 3

            suma_m_obra = round(
                sum((x.get("porcentaje_2") or 0.0) for x in datas["reparto"].values()),
                2
            )
            mostrar_m = suma_m_obra > 0

            for ipi, r in datas["reparto"].items():
                if check_cancel():
                    return {"cancelado": True}

                m_cell = fmt_pct(r["porcentaje_2"]) if mostrar_m else ""

                writer.writerow([
                    r["caes"],
                    r["nombre"],
                    fmt_pct(r["porcentaje_1"]),
                    m_cell,
                    "",
                    ipi,
                ])
                fila += 1

            writer.writerow([])
            fila += 1
            
    return {"fila_por_obra": fila_por_obra, "ok": True, "ruta_destino": ruta_destino}