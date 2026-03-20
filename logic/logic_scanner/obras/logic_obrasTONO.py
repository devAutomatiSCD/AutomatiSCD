import pdfplumber, re, csv, os, unicodedata
from collections import defaultdict, OrderedDict
from utils.config_manager import obtener_carpeta_base

# =========================
# Parsers
# =========================

LINE_RE_PDF = re.compile(
    r'^(?P<rol>[A-Z]{1,3})\s+'
    r'(?P<nombre>.+?)\s+'
    r'(?P<ipn>\d{8,12})\s+'
    r'(?P<p_share>\d{1,3},\d{2})\s+'
    r'(?P<p_soc>[A-Za-z]+)\s+'
    r'(?P<m_share>\d{1,3},\d{2})\s+'
    r'(?P<m_soc>[A-Za-z]+)\s*$'
)

TITLE_RE_PDF = re.compile(
    r'^Title:\s*(?P<title>.+?)\s+ISWC\s*:\s*(?P<iswc>T\d+)\s*$'
)

LINE_RE_CAP = re.compile(
    r'^\s*'
    r'\d+\s+'
    r'(?P<rol>[A-Z]{1,3})\s+'
    r'(?P<nombre>.+?)\s+'
    r'(?:(?P<ipn>\d{5,12})\s+)?'
    r'(?:\d{3}:[A-Z]{1,6}\s+){1,2}'
    r'(?P<p_share>\d{1,3}[.,]\d{2})'
    r'(?:\s+(?P<m_share>\d{1,3}[.,]\d{2}))?'
    r'\s*$'
)

TITLE_RE_CAP = re.compile(
    r'^Work\s*Key:\s*(?P<work_key>\d+)\s+Title:\s*(?P<title>.+?)'
    r'(?:\s+ISWC\s*:\s*(?P<iswc>T-\d{3}\.\d{3}\.\d{3}-\d))?\s*$',
    re.IGNORECASE
)

#re.IGNORECASE ignora mayus

def extraer_pdfs(ruta):
    pdfs = []
    for root, _, files in os.walk(ruta):
        for f in files:
            if f.lower().endswith(".pdf"):
                pdfs.append(os.path.join(root, f))
    return pdfs

def parse_lines_pdf(text: str, stop_event=None):
    rows = []
    current_title = None
    current_iswc = None
    current_work_key = None
    
    def check_cancel():
        return stop_event is not None and stop_event.is_set()

    for raw in text.splitlines():
        
        if check_cancel():
            return {"cancelado": True}
        
        line = raw.strip()
        if not line:
            continue

        tm = TITLE_RE_PDF.match(line)
        if tm:
            current_title = tm.group("title")
            current_iswc = tm.group("iswc")
            current_work_key = tm.group("work_key")
            continue

        d = parse_dh_line(line)
        if not d or not current_iswc:
            continue

        d["nombre_obra"] = current_title
        d["iswc"] = current_iswc
        d["work_key"] = current_work_key
        rows.append(d)

    return rows

def parse_lines_carpeta(text: str, stop_event=None):
    rows = []
    current_title = None
    current_iswc = None
    current_work_key = None
    
    def check_cancel():
        return stop_event is not None and stop_event.is_set()

    for raw in text.splitlines():
        
        if check_cancel():
            return {"cancelado": True}
        
        line = raw.strip()
        if not line:
            continue

        tm = TITLE_RE_CAP.match(line)
        if tm:
            current_title = tm.group("title")
            current_iswc = tm.group("iswc")
            current_work_key = tm.group("work_key")
            continue

        d = parse_dh_line(line)
        if not d or not current_work_key:
            continue

        d["nombre_obra"] = current_title
        d["iswc"] = current_iswc
        d["work_key"] = current_work_key
        rows.append(d)

    return rows

def agrupar_por_iswc(rows):
    obras = defaultdict(lambda: {"titulo": None, "work_key": None, "dh": []})

    for r in rows:
        work_key = r["work_key"]
        obras[work_key]["titulo"] = r["nombre_obra"]
        obras[work_key]["work_key"] = work_key
        obras[work_key]["dh"].append(r)

    return dict(obras)

def consolidar_dh(obras: dict) -> dict:
    for _, obra in obras.items():
        acumulado = OrderedDict()

        for r in obra["dh"]:
            ipn = (r.get("ipn") or "").strip()

            if ipn and set(ipn) != {"0"}:
                key = ("IPI", ipn, r.get("rol"))
            else:
                key = ("NOMBRE", r.get("rol"), normalizar_nombre(r.get("nombre")))

            if key not in acumulado:
                acumulado[key] = dict(r)
                
                if not ipn or set(ipn) == {"0"}:
                    acumulado[key]["ipn"] = ""
            else:
                acumulado[key]["p_share"] += r.get("p_share", 0.0)
                acumulado[key]["m_share"] += r.get("m_share", 0.0)

        obra["dh"] = list(acumulado.values())

    return obras

def parse_dh_line(line: str) -> dict | None:
    m = LINE_RE_CAP.match(line.strip())
    if not m:
        return None

    d = m.groupdict()

    d["p_share"] = float(d["p_share"].replace(",", "."))

    if d["m_share"]:
        d["m_share"] = float(d["m_share"].replace(",", "."))
    else:
        d["m_share"] = 0.0
        d["m_soc"] = None 

    return d

def parse_ipi(p):
    return p.lstrip("0")

def parse_name(titulo: str) -> str:
    titulo = titulo.replace("ISWC:", "")
    return re.sub(r"\s*\(.*?\)", "", titulo).strip()

def normalizar_nombre(texto: str) -> str:

    texto = unicodedata.normalize("NFKD", texto)
    
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    
    texto = re.sub(r"[^A-Za-z\s]", "", texto)

    texto = re.sub(r"\s+", " ", texto).strip()

    return texto

def revisar_porcentajes(obras: dict):
    alertas = []

    for key, obra in obras.items():
        titulo = obra.get("titulo") or "(sin título)"
        iswc = obra.get("iswc") or "(sin ISWC)"

        suma_p = sum(r.get("p_share", 0.0) for r in obra["dh"])
        suma_m = sum(r.get("m_share", 0.0) for r in obra["dh"])

        suma_p = round(suma_p, 2)
        suma_m = round(suma_m, 2)
        
        if suma_p != 100 or (suma_m != 100 and suma_m > 0):
            alertas.append((key, titulo, iswc, suma_p, suma_m))

    return alertas

# =========================
# Scanner
# =========================

def scanner_pdf(ruta, folio, stop_event=None):
    
    def check_cancel():
        return stop_event is not None and stop_event.is_set()
    
    obras = []
    
    with pdfplumber.open(ruta) as pdf:
        
        if check_cancel():
            return {"cancelado": True}
            
        texto = "\n".join(
                page.extract_text() or "" for page in pdf.pages
            )
        
        rows = parse_lines_pdf(texto)
        obras = agrupar_por_iswc(rows)
        obras = consolidar_dh(obras)
        
    alertas = revisar_porcentajes(obras)
    cantidad_obras = len(obras)
    res = export_excel(obras, folio, stop_event=stop_event)
    
    if res.get("ok"):
        return {"ok": True, "alertas": alertas, "cantidad_obras": cantidad_obras, "ruta_destino": res.get("ruta_destino")}

    
def scanner_carpetas(obras_pdf, folio, stop_event=None):

    def check_cancel():
        return stop_event is not None and stop_event.is_set()

    all_rows = []

    for ruta in obras_pdf:
        if check_cancel():
            return {"cancelado": True}

        with pdfplumber.open(ruta) as pdf:
            texto = "\n".join(page.extract_text() or "" for page in pdf.pages)

        rows = parse_lines_carpeta(texto, stop_event=stop_event)
        if isinstance(rows, dict) and rows.get("cancelado"):
            return rows

        all_rows.extend(rows)

    obras = agrupar_por_iswc(all_rows)
    obras = consolidar_dh(obras)
    alertas = revisar_porcentajes(obras)
    cantidad_obras = len(obras)

    res = export_excel(obras, folio, stop_event=stop_event)
    
    if res.get("ok"):
        return {"ok": True, "alertas": alertas, "cantidad_obras": cantidad_obras, "ruta_destino": res.get("ruta_destino")}


def scanner(ruta, folio, stop_event=None, modo="file"):
    
    if modo == "file":
        return scanner_pdf(ruta, folio, stop_event=stop_event)

    obras_pdf = extraer_pdfs(ruta)
    
    return scanner_carpetas(obras_pdf, folio, stop_event=stop_event)
    
# =========================
# Export
# =========================

def export_excel(obras, folio, stop_event=None):
    
    def check_cancel():
        return stop_event is not None and stop_event.is_set()
    
    carpeta_base = obtener_carpeta_base()
    
    ruta_destino = carpeta_base / "MMs" / f"mm_tono_{folio}.csv"
    
    fila_por_obra = {}
    fila = 1

    with open(
        ruta_destino,
        "w",
        newline="",
        encoding="latin-1"
    ) as f:
        writer = csv.writer(f, delimiter=";")

        for key, obra in obras.items():
            
            if check_cancel():
                return {"cancelado": True}
            
            fila_por_obra[key] = fila
        
            # Fila título
            writer.writerow([parse_name(obra["titulo"]), "", "", "", "", ""])
            writer.writerow([])
            writer.writerow([])
            writer.writerow([])
            
            suma_m_obra = round(sum((x.get("m_share") or 0.0) for x in obra["dh"]), 2)
            mostrar_m = suma_m_obra > 0

            # DH
            for r in obra["dh"]:
                m_cell = (
                    f"{r['m_share']:.2f}".replace(".", ",")
                    if mostrar_m
                    else ""
                )
                writer.writerow([
                    r["rol"],
                    normalizar_nombre(r["nombre"]),
                    f"{r['p_share']:.2f}".replace(".", ","),
                    m_cell,
                    "",
                    parse_ipi(r["ipn"]),
                ])

            writer.writerow([])
            fila += 1
            
    return {"fila_por_obra": fila_por_obra, "ok": True, "ruta_destino": ruta_destino}

    
