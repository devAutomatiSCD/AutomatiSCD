import pdfplumber
import re, os, csv

# =========================
# Parsers
# =========================

def parse_porcentaje(p):
    soc1, p1, soc2, p2 = p.split()
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
    return re.sub(r"\s+", " ", n).strip()

def parse_pct(v: str) -> float:
    # "12,50" -> 12.5
    return float(v.replace(",", "."))

def fmt_pct(v: float) -> str:
    # 12.5 -> "12,50"
    return f"{v:.2f}".replace(".", ",")

# =========================
# Scanner
# =========================

def scanner(ruta_pdf, stop_event=None):
    
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

    reporte_porcentajes(obras, stop_event=stop_event)
    export_excel(obras, stop_event=stop_event)
    
# =========================
# Reporte
# =========================   

def reporte_porcentajes(obras, stop_event=None):
    
    def check_cancel():
        return stop_event is not None and stop_event.is_set()
    
    obras_100 = 0
    obras_no_100 = 0
    detalle_no_100 = {}

    for nombre_obra, datas in obras.items():
        if check_cancel():
            return {"cancelado": True}
        total = sum(
            r["porcentaje_1"]
            for r in datas["reparto"].values()
        )

        # tolerancia por decimales (muy importante)
        if abs(total - 100.0) < 0.01:
            obras_100 += 1
        else:
            obras_no_100 += 1
            detalle_no_100[nombre_obra] = round(total, 2)

    print("\n===== REPORTE PORCENTAJES =====")
    print(f"Obras al 100: {obras_100}")
    print(f"Obras no al 100: {obras_no_100}")

    if detalle_no_100:
        print("\nObras no al 100:")
        for nombre, total in detalle_no_100.items():
            print(f" - {nombre}: {str(total).replace('.', ',')}")

# =========================
# Export
# =========================

def export_excel(obras, stop_event=None):
    
    def check_cancel():
        return stop_event is not None and stop_event.is_set()
    
    escritorio = os.path.join(
        os.path.expanduser("~"),
        r"OneDrive - Sociedad Chilena de Autores e Interpretes Musicales\Escritorio"
    )
    os.makedirs(escritorio, exist_ok=True)
    
    with open(
        os.path.join(escritorio, "mm_sgae.csv"),
        "w",
        newline="",
        encoding="latin-1"
    ) as f:
        writer = csv.writer(f, delimiter=";")

        for _, datas in obras.items():
            if check_cancel():
                return {"cancelado": True}
            # Título de obra (estructura compatible SCD)
            writer.writerow([datas["obra"], "", "", "", "", ""])
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
