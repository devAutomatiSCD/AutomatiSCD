import pdfplumber, re, csv, os, unicodedata
from collections import defaultdict, OrderedDict
from utils.config_manager import obtener_carpeta_base

# =========================
# Parsers
# =========================

LINE_RE = re.compile(
    r'^\s*'
    r'(?:(?P<prefix>.*?)(?=\d{1,2}(?:,\d{3})+-\d{1,2}\s))?'  
    r'(?P<ipi>\d{1,2}(?:,\d{3})+-\d{1,2})\s+'
    r'(?P<rol>[A-Z]{1,3})\s+'
    r'(?P<nombre>[A-ZÁÉÍÓÚÑ ]+?)\s+'
    r'(?P<p1>\d{1,3}\.\d{2})%(?P<soc1>[A-Z]+)\s*\((?P<n1>\d+)\)\s+'
    r'(?P<p2>\d{1,3}\.\d{2})%(?P<soc2>[A-Z]+)\s*\((?P<n2>\d+)\)\s*'
    r'$'
)

TITLE_RE = re.compile(
    r'^\s*'
    r'\d{1,3}(?:,\d{3})*\s+'                     
    r'(?P<iswc>T-\d{3}\.\d{3}\.\d{3}-\d)\s+'    
    r'(?P<title>.+?)'                            
    r'\s+(?:OT\b.*)?$'                           
)

def parse_lines(text: str, stop_event=None):
    
    def check_cancel():
        return stop_event is not None and stop_event.is_set()
    
    rows = []
    current_title = None
    current_iswc = None

    for raw in text.splitlines():
        
        if check_cancel():
            return {"cancelado": True}
        
        line = raw.strip()
        if not line:
            continue

        tm = TITLE_RE.match(line)
        if tm:
            current_title = tm.group("title")
            current_iswc = tm.group("iswc")
            continue

        d = parse_dh_line(line)
        if not d or not current_iswc:
            continue

        d["nombre_obra"] = current_title
        d["iswc"] = current_iswc
        rows.append(d)

    return rows

def agrupar_por_iswc(rows, stop_event=None):
    
    def check_cancel():
        return stop_event is not None and stop_event.is_set()
    
    obras = defaultdict(lambda: {"titulo": None, "iswc": None, "dh": []})

    for r in rows:
        if check_cancel():
            return {"cancelado": True}
        iswc = r["iswc"]
        obras[iswc]["titulo"] = r["nombre_obra"]
        obras[iswc]["iswc"] = iswc
        obras[iswc]["dh"].append(r)

    return dict(obras)

def consolidar_dh_por_ipn(obras: dict, stop_event=None) -> dict:
    
    def check_cancel():
        return stop_event is not None and stop_event.is_set()
    
    for iswc, obra in obras.items():
        if check_cancel():
            return {"cancelado": True}
        
        acumulado = OrderedDict()

        for r in obra["dh"]:
            if check_cancel():
                return {"cancelado": True}
            key = (r["ipi"], r["rol"]) 

            if key not in acumulado:
                acumulado[key] = dict(r) 
            else:
                acumulado[key]["p1"] += r["p1"]
                acumulado[key]["p2"] += r["p2"]

        obra["dh"] = list(acumulado.values())

    return obras

def parse_dh_line(line: str) -> dict | None:
    m = LINE_RE.match(line.strip())
    if not m:
        return None

    d = m.groupdict()

    d["p1"] = float(d["p1"].replace(",", "."))

    if d["p2"]:
        d["p2"] = float(d["p2"].replace(",", "."))
    else:
        d["p2"] = 0.0

    return d

def parse_ipi(p):
    p = p.replace(",", "").replace("-", "")
    return p.lstrip("0")

def parse_name(titulo: str) -> str:
    return re.sub(r"\s*\(.*?\)", "", titulo).strip()

def normalizar_nombre(texto: str) -> str:

    texto = unicodedata.normalize("NFKD", texto)
    
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    
    texto = re.sub(r"[^A-Za-z\s]", "", texto)
    
    texto = re.sub(r"\s+", " ", texto).strip()

    return texto

# =========================
# Scanner
# =========================

def scanner(ruta, folio, stop_event=None):
    
    def check_cancel():
        return stop_event is not None and stop_event.is_set()
    
    obras = []
    
    with pdfplumber.open(ruta) as pdf:
        
        if check_cancel():
            return {"cancelado": True}
            
        texto = "\n".join(
                page.extract_text() or "" for page in pdf.pages
            )
        
        rows = parse_lines(texto, stop_event=stop_event)
        obras = agrupar_por_iswc(rows, stop_event=stop_event)
        obras = consolidar_dh_por_ipn(obras, stop_event=stop_event)
        
    res = export_excel(obras, folio, stop_event=stop_event)
    
    if res:
        return True
    
# =========================
# Export
# =========================

def export_excel(obras, folio, stop_event=None):
    
    def check_cancel():
        return stop_event is not None and stop_event.is_set()
    
    carpeta_base = obtener_carpeta_base()
    
    ruta_destino = carpeta_base / "MMs" / f"mm_apdayc_{folio}.csv"
    
    with open(
        ruta_destino,
        "w",
        newline="",
        encoding="latin-1"
    ) as f:
        writer = csv.writer(f, delimiter=";")

        for iswc, obra in obras.items():
            
            if check_cancel():
                return {"cancelado": True}

            # Fila título
            writer.writerow([parse_name(obra["titulo"]), "", "", "", "", ""])
            writer.writerow([])
            writer.writerow([])
            writer.writerow([])

            # DH
            for r in obra["dh"]:
                writer.writerow([
                    r["rol"],
                    normalizar_nombre(r["nombre"]),
                    f"{r['p1']:.2f}".replace(".", ","),
                    f"{r['p2']:.2f}".replace(".", ","),
                    "",
                    parse_ipi(r["ipi"]),
                ])

            writer.writerow([])

    return True

    
