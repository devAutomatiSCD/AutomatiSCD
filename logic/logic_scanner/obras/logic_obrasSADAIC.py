import pdfplumber, re, csv, os, unicodedata
from utils.config_manager import obtener_carpeta_base

def extraer_pdfs(ruta):
    obras = []
    
    for carpeta in os.listdir(ruta):
        ruta_pdf = os.path.join(ruta, carpeta)
        if os.path.isfile(ruta_pdf):
            obras.append(ruta_pdf)
                    
    return obras

# =========================
# Parsers
# =========================

LINE_RE = re.compile(
    r'^(?P<tipo>(?:[A-Z]{1,3})?)\s+'
    r'(?:[1-9])?' 
    r'(?P<nombre>.+?)\s+'
    r'(?P<ipi>\d{1,3}(?:,\d{3})*-\d{2})\s+'
    r'(?P<resto>(?:\d{3}\s+\d+(?:\.\d+)?\s*)+)$'
)

PAIR_RE = re.compile(r'(?P<cod>\d{3})\s+(?P<pct>\d+(?:\.\d+)?)')

NOMBRE_OBRA_RE = re.compile(r'^(?P<nombre_obra>.+?)\s+\d+\s*/\s*\d+$', re.MULTILINE)

def parse_lines(text: str):
    rows = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue

        m = LINE_RE.match(line)
        if not m:
            continue

        pairs = [(p.group("cod"), float(p.group("pct"))) for p in PAIR_RE.finditer(m.group("resto"))]
        rows.append({
            "tipo": m.group("tipo"),
            "nombre": m.group("nombre"),
            "ipi": m.group("ipi"),
            "pairs": pairs, 
            "nombre_obra": NOMBRE_OBRA_RE.search(text).group("nombre_obra") if NOMBRE_OBRA_RE.search(text) else "DESCONOCIDO"
        })
        
    return rows

def parse_porcentaje(p):
    soc1, p1, soc2, p2 = p.split()
    return {
        "porcentaje_1": p1,
        "porcentaje_2": p2,
        "soc1": soc1,
        "soc2": soc2
    }

def parse_ipi(p):
    return p.replace(",", "").strip().replace("-", "").strip()

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

def revisar_porcentajes(obras: list):
    alertas = []

    for obra in obras:
        titulo = obra.get("nombre_obra") or "(sin título)"
        iswc = obra.get("iswc") or "(sin ISWC)"

        suma_p = sum(r.get("pct1", 0.0) for r in obra.get("reparto", []))
        suma_m = sum(r.get("pct2", 0.0) for r in obra.get("reparto", []))

        suma_p = round(suma_p, 2)
        suma_m = round(suma_m, 2)

        if abs(suma_p - 100) > 0.01 or (suma_m > 0 and abs(suma_m - 100) > 0.01):
            alertas.append((titulo, iswc, suma_p, suma_m))

    return alertas

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
    
    obras_pdf = extraer_pdfs(ruta_pdf)
    obras = []
    
    for ruta in obras_pdf:
        if check_cancel():
            return {"cancelado": True}

        with pdfplumber.open(ruta) as pdf:
            texto = "\n".join(page.extract_text() or "" for page in pdf.pages)

        DHs = parse_lines(texto)

        if not DHs:
            continue

        obra = {
            "nombre_obra": DHs[0]["nombre_obra"],
            "reparto": {}
        }

        for item in DHs:
            ipi = parse_ipi(item["ipi"])
            nombre = parse_name(item["nombre"])
            tipo = item["tipo"]

            pct1 = item["pairs"][0][1] if len(item["pairs"]) > 0 else 0.0
            pct2 = item["pairs"][1][1] if len(item["pairs"]) > 1 else 0.0

            if ipi in obra["reparto"]:
                obra["reparto"][ipi]["pct1"] += pct1
                obra["reparto"][ipi]["pct2"] += pct2
            else:
                obra["reparto"][ipi] = {
                    "tipo": tipo,
                    "nombre": nombre,
                    "pct1": pct1,
                    "pct2": pct2,
                }

        obra["reparto"] = [
            {
                "tipo": data["tipo"],
                "nombre": data["nombre"],
                "pct1": data["pct1"],
                "pct2": data["pct2"],
                "ipi": ipi
            }
            for ipi, data in obra["reparto"].items()
        ]

        obras.append(obra)

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
    ruta_destino = carpeta_base / "MMs" / f"mm_sadaic_{folio}.csv"
    
    fila_por_obra = {}
    fila = 1
    
    with open(ruta_destino, "w", newline="", encoding="latin-1") as f:
        writer = csv.writer(f, delimiter=";")

        for i, obra in enumerate(obras):
            if check_cancel():
                return {"cancelado": True}
            
            fila_por_obra[obra["nombre_obra"]] = fila
            
            writer.writerow([normalizar_nombre(obra["nombre_obra"]), "", "", "", "", ""])
            fila += 1

            writer.writerow([])
            writer.writerow([])
            writer.writerow([])
            fila += 3
            
            suma_m_obra = round(sum((x.get("pct2") or 0.0) for x in obra["reparto"]), 2)
            mostrar_m = suma_m_obra > 0

            for r in obra["reparto"]:
                if check_cancel():
                    return {"cancelado": True}
                
                m_cell = fmt_pct(r["pct2"]) if mostrar_m else ""
                
                writer.writerow([
                    r["tipo"],
                    r["nombre"],
                    fmt_pct(r["pct1"]),
                    m_cell,
                    "",
                    r["ipi"],
                ])
                fila += 1

            writer.writerow([])
            fila += 1
            
    return {"fila_por_obra": fila_por_obra, "ok": True, "ruta_destino": ruta_destino}
