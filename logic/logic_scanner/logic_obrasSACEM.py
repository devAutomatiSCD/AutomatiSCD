import pdfplumber, re, csv, os, unicodedata
from collections import defaultdict, OrderedDict
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
    r'^\s*'
    r'(?P<rol>[A-Z]{1,3})\s+'
    r'(?:[A-Z]{1,3}\s+)?'                  
    r'(?P<nombre>.+?)\s+'
    r'(?P<ipn>\d{8,12})\s+'
    r'(?P<p_soc>.+?)\s+'
    r'(?P<p_share>\d{1,3},\d{2,5})'
    r'(?:\s*(?P<m_soc>.+?)\s+(?P<m_share>\d{1,3},\d{2,5}))?'
    r'\s*$'
)

TITLE_ISWC_RE = re.compile(
    r'^TITLE:\s*(?P<title>.+?)\s+ISWC:\s*(?P<iswc>.+)$'
)

def parse_lines(text: str):
    rows = []
    current_title = None
    current_iswc = None

    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        
        line = limpiar_linea(line)

        tm = TITLE_ISWC_RE.match(line)
        # print(bool(tm))
        if tm:
            current_title = tm.group("title")
            current_iswc = tm.group("iswc")
            continue
        
        
        d = parse_dh_line(line)
        # print(d)
        if not d or not current_iswc:
            continue

        d["nombre_obra"] = current_title
        d["iswc"] = current_iswc
        rows.append(d)

    return rows

def limpiar_linea(linea: str) -> str:
    # separa porcentaje pegado a texto
    linea = re.sub(r'(\d,\d{4,5})([A-Za-zP])', r'\1 \2', linea)

    # repara nombre + IPN pegado tipo LIMITE6D42290754
    linea = re.sub(
        r'([A-Za-z]+)(\d)([A-Za-z])(\d{7,11})',
        r'\1\3 \2\4',
        linea
    )

    return linea

def agrupar_por_obra(rows):
    obras = defaultdict(lambda: {"titulo": None, "iswc": None, "dh": []})

    for r in rows:
        key = (r["archivo"], r["nombre_obra"], r["iswc"])

        obras[key]["titulo"] = r["nombre_obra"]
        obras[key]["iswc"] = r["iswc"]
        obras[key]["dh"].append(r)

    return dict(obras)

def consolidar_dh_por_ipn(obras: dict) -> dict:
    
    for iswc, obra in obras.items():
        acumulado = OrderedDict()

        for r in obra["dh"]:
            key = (r["ipn"], r["rol"], r["p_soc"], r["m_soc"]) 

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

    return texto.upper()

def revisar_porcentajes(obras: dict):
    alertas = []

    for key, obra in obras.items():
        titulo = obra.get("titulo") or "(sin título)"
        iswc = obra.get("iswc") or "(sin ISWC)"

        suma_p = sum(r.get("p_share", 0.0) for r in obra["dh"])
        suma_m = sum(r.get("m_share", 0.0) for r in obra["dh"])

        if abs(suma_p - 100) > 0.01 or (suma_m > 0 and abs(suma_m - 100) > 0.01):
            alertas.append((key, titulo, iswc, suma_p, suma_m))

    return alertas

# =========================
# Scanner
# =========================

def scanner(carpeta_pdf, folio, stop_event=None):
    obras_pdf = extraer_pdfs(carpeta_pdf)

    todas_las_rows = []

    for ruta in obras_pdf:
        with pdfplumber.open(ruta) as pdf:
            texto = "\n".join(page.extract_text() or "" for page in pdf.pages)

            rows = parse_lines(texto)

            nombre_archivo = os.path.basename(ruta)
            for r in rows:
                r["archivo"] = nombre_archivo

            todas_las_rows.extend(rows)
    obras = agrupar_por_obra(todas_las_rows)
    obras = consolidar_dh_por_ipn(obras)
    cantidad_obras = len(obras)

    res = export_excel(obras, folio, stop_event=stop_event)
    
    alertas = revisar_porcentajes(obras)
    
    if res.get("ok"):
        return {"ok": True, "alertas": alertas, "cantidad_obras": cantidad_obras, "ruta_destino": res.get("ruta_destino")}
    
# =========================
# Export
# =========================

def export_excel(obras, folio, stop_event=None):
    
    def check_cancel():
        return stop_event is not None and stop_event.is_set()
    
    carpeta_base = obtener_carpeta_base()
    
    ruta_destino = carpeta_base / "MMs" / f"mm_sacem_{folio}.csv"
    
    fila_por_obra = {}
    fila = 1
    
    with open(
        ruta_destino,
        "w",
        newline="",
        encoding="latin-1"
    ) as f:
        writer = csv.writer(f, delimiter=";")

        for iswc, obra in obras.items():

            # Fila título
            writer.writerow([normalizar_nombre(obra["titulo"]), "", "", "", "", ""])
            writer.writerow([])
            writer.writerow([])
            writer.writerow([])
            
            suma_m_obra = round(sum((x.get("m_share") or 0.0) for x in obra["dh"]), 2)
            mostrar_m = suma_m_obra > 0

            # DH
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




    
