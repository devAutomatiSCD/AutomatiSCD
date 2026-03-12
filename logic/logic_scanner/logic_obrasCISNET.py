import pdfplumber, re, csv, os
from collections import defaultdict, OrderedDict
import unicodedata
from utils.config_manager import obtener_carpeta_base

# =========================
# Normalización
# =========================
def normalizar_nombre(texto: str) -> str:
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    texto = re.sub(r"[^A-Za-z0-9\s\+\-]", "", texto)  # permite + y -
    texto = re.sub(r"\s+", " ", texto).strip()
    return texto.upper()

# =========================
# Parsers
# =========================

DH_RE = re.compile(
    r'^(?P<nombre>.+?)\s+'
    r'(?:(?P<ipn>\d{8,14})\s+)?'
    r'(?P<rol>[A-Z]{1,3})'
    r'(?:\s+(?P<ap>[A-Z0-9]{1,5}))?'       
    r'(?:\s+(?P<lp>[A-Z0-9]{1,5}))?'
    r'\s+(?P<p_soc>[A-Z0-9\-\+]+)\s+'       
    r'(?P<p_share>\d{1,3},\d{2})%\s*'
    r'(?:\s+(?P<m_soc>[A-Z0-9\-\+]+)\s+'  
    r'(?P<m_share>\d{1,3},\d{2})%)?'
    r'(?:\s+(?P<us_rep>\S+))?'
    r'\s*$'
)

TITLE_RE = re.compile(
    r'^Title:\s*(?P<title>.+?)\s+ISWC:\s*(?P<iswc>T[-\d\.]+-\d+)?\s*$'
)

TERR_RE = re.compile(r'^Territory:\s*(?P<terr>.+?)\s*$', re.IGNORECASE)

def parse_dh_line(line: str) -> dict | None:
    m = DH_RE.match(line.strip())
    if not m:
        return None

    d = m.groupdict()
    
    d["nombre"] = normalizar_nombre(d["nombre"])

    if not d.get("ipn"):
        if d["nombre"] == "EDITOR DESCONOCIDO":
            d["ipn"] = "288936892"

    d["p_share"] = float(d["p_share"].replace(",", "."))

    if d["m_share"]:
        d["m_share"] = float(d["m_share"].replace(",", "."))
    else:
        d["m_share"] = 0.0
        d["m_soc"] = None

    d["nombre"] = normalizar_nombre(d["nombre"])
    return d

def parse_lines(text: str):
    rows = []
    current_title = None
    current_iswc = None
    current_terr = None  # <- NUEVO

    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue

        # Territory
        ttm = TERR_RE.match(line)
        if ttm:
            current_terr = normalizar_nombre(ttm.group("terr"))
            continue

        # Title
        tm = TITLE_RE.match(line)
        if tm:
            current_title = tm.group("title").strip()
            current_iswc = tm.group("iswc") or None
            continue

        d = parse_dh_line(line)
        if not d or not current_title:
            continue

        d["nombre_obra"] = current_title
        d["iswc"] = current_iswc
        d["territory"] = current_terr 

    
        if current_iswc:
            d["_obra_key"] = f"ISWC:{current_iswc}"
        else:
            d["_obra_key"] = f"NOMBRE:{normalizar_nombre(current_title)}"

        rows.append(d)

    return rows

# =========================
# Territorios: selección por prioridad
# =========================

def territory_rank(terr: str | None) -> int:
    """
    Menor = mejor.
    0: contiene 2WL
    1: contiene DEFAULT
    2: otros / None
    """
    if not terr:
        return 2
    terr_u = terr.upper()
    if "2WL" in terr_u:
        return 0
    if "DEFAULT" in terr_u:
        return 1
    return 2

def seleccionar_mejor_territorio_por_obra(rows):
    por_obra = OrderedDict()  
    for r in rows:
        ok = r["_obra_key"]
        terr = r.get("territory") or "(SIN_TERRITORY)"
        if ok not in por_obra:
            por_obra[ok] = OrderedDict()
        if terr not in por_obra[ok]:
            por_obra[ok][terr] = []
        por_obra[ok][terr].append(r)

    filtradas = []
    for ok, terr_map in por_obra.items():
        terr_list = list(terr_map.keys())
        best = min(terr_list, key=lambda t: territory_rank(None if t == "(SIN_TERRITORY)" else t))
        filtradas.extend(terr_map[best])

    return filtradas

# =========================
# Agrupar + consolidar
# =========================

def agrupar_por_obra(rows):
    obras = defaultdict(lambda: {"titulo": None, "iswc": None, "dh": []})

    for r in rows:
        key = r["_obra_key"]
        obras[key]["titulo"] = r["nombre_obra"]
        obras[key]["iswc"] = r["iswc"]
        obras[key]["dh"].append(r)

    return dict(obras)

def consolidar_dh_por_ipn(obras: dict) -> dict:
    for key, obra in obras.items():
        acumulado = OrderedDict()

        for r in obra["dh"]:
            k = (r["ipn"], r["rol"], r.get("p_soc"), r.get("m_soc"))

            if k not in acumulado:
                acumulado[k] = dict(r)
            else:
                acumulado[k]["p_share"] += r["p_share"]
                acumulado[k]["m_share"] += r["m_share"]

        obra["dh"] = list(acumulado.values())

    return obras

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

def parse_ipi(p):
    if p is None or str(p).strip() == "":
        return "SIN_IPI"  
    
    return str(p).strip().lstrip("0")

def parse_name(titulo: str) -> str:
    titulo = titulo.replace("ISWC:", "")

    titulo = titulo.replace("(", " ").replace(")", " ")

    titulo = unicodedata.normalize("NFKD", titulo)
    titulo = "".join(c for c in titulo if not unicodedata.combining(c))

    titulo = titulo.replace("&", " Y ")

    titulo = re.sub(r"[^A-Za-z0-9\s]", "", titulo)

    titulo = re.sub(r"\s+", " ", titulo).strip()

    return titulo.upper()

# =========================
# Export
# =========================

def export_excel(obras, folio, stop_event=None):
    
    def check_cancel():
        return stop_event is not None and stop_event.is_set()
    
    carpeta_base = obtener_carpeta_base()
    
    ruta_destino = carpeta_base / "MMs" / f"mm_cisnet_{folio}.csv"
    
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
            fila += 1

            writer.writerow([]); fila += 1
            writer.writerow([]); fila += 1
            writer.writerow([]); fila += 1
            
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
                    r["nombre"],
                    f"{r['p_share']:.2f}".replace(".", ","),
                    m_cell,
                    "",
                    parse_ipi(r["ipn"]),
                ])
                fila += 1

            writer.writerow([]); fila += 1

    return {"fila_por_obra": fila_por_obra, "ok": True, "ruta_destino": ruta_destino}

# =========================
# Scanner
# =========================

def scanner(ruta, folio, stop_event=None):
    
    def check_cancel():
        return stop_event is not None and stop_event.is_set()
    
    with pdfplumber.open(ruta) as pdf:
        if check_cancel():
                return {"cancelado": True}
        texto = "\n".join(page.extract_text() or "" for page in pdf.pages)
        
    rows = parse_lines(texto)

    rows = seleccionar_mejor_territorio_por_obra(rows)

    obras = agrupar_por_obra(rows)
    obras = consolidar_dh_por_ipn(obras)
    cantidad_obras = len(obras)

    res = export_excel(obras, folio, stop_event=stop_event)
    
    alertas = revisar_porcentajes(obras)
    
    if res.get("ok"):
        return {"ok": True, "alertas": alertas, "cantidad_obras": cantidad_obras, "ruta_destino": res.get("ruta_destino")}
        
