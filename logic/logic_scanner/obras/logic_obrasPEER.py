import pdfplumber, re, csv, os, unicodedata
from collections import defaultdict, OrderedDict
from utils.config_manager import obtener_carpeta_base
# =========================
# Parsers
# =========================

LINE_RE = re.compile(
    r'^\s*'
    r'\d+\.\s*'                        
    r'(?P<rol>[A-Z]{1,3})\s+'         
    r'(?P<nombre>.+?)\s+'              
    r'(?P<p_share>\d{1,3},\d{2})\s+'
    r'(?P<m_share>\d{1,3},\d{2})%\s+'
    r'(?P<m_soc>[A-Za-z]+)\s+'
    r'(?P<ipn>\d{8,12})\s*$'
)

TITLE_RE = re.compile(
    r'^(?P<iswc>\d+)\s+\d+\.\s+(?P<title>.+)$'
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
        # print(bool(tm))
        if tm:
            current_title = tm.group("title")
            current_iswc = tm.group("iswc")
            continue

        d = parse_dh_line(line)
        print(d)
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
            
            key = (r["ipn"], r["rol"]) 

            if key not in acumulado:
                acumulado[key] = dict(r) 
            else:
                acumulado[key]["p_share"] += r["p_share"]
                acumulado[key]["m_share"] += r["m_share"]

        obra["dh"] = list(acumulado.values())

    return obras

def parse_dh_line(line: str) -> dict | None:
    m = LINE_RE.match(line.strip())
    if not m:
        return None

    d = m.groupdict()

    # P-Share siempre viene
    d["p_share"] = float(d["p_share"].replace(",", "."))

    # M-Share opcional => si no viene, 0
    if d["m_share"]:
        d["m_share"] = float(d["m_share"].replace(",", "."))
    else:
        d["m_share"] = 0.0
        d["m_soc"] = None  # o "NS" si quieres un placeholder

    return d

def parse_ipi(p):
    return p.lstrip("0")

def parse_name(titulo: str) -> str:
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
        
    alertas = revisar_porcentajes(obras)
    cantidad_obras = len(obras)
    res = export_excel(obras, folio, stop_event=stop_event)
    
    if res.get("ok"):
        return {"ok": True, "alertas": alertas, "cantidad_obras": cantidad_obras, "ruta_destino": res.get("ruta_destino")}

# =========================
# Export
# =========================

def export_excel(obras, folio, stop_event=None):

    def check_cancel():
        return stop_event is not None and stop_event.is_set()
    
    carpeta_base = obtener_carpeta_base()
    
    ruta_destino = carpeta_base / "MMs" / f"mm_peer_{folio}.csv"
    
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
            
            writer.writerow([parse_name(obra["titulo"]), "", "", "", "", ""])
            writer.writerow([])
            writer.writerow([])
            writer.writerow([])
            
            suma_m_obra = round(sum((x.get("m_share") or 0.0) for x in obra["dh"]), 2)
            mostrar_m = suma_m_obra > 0

            for r in obra["dh"]:
                
                if check_cancel():
                    return {"cancelado": True}
                
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

    return {"fila_por_obra": fila_por_obra, "ok": True, "ruta_destino": ruta_destino}

    
