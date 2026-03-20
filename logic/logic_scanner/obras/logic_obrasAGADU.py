import pdfplumber, re, csv, os
from utils.config_manager import obtener_carpeta_base


def extraer_pdfs(ruta):
    obras = []

    for carpeta in os.listdir(ruta):
        ruta_pdf = os.path.join(ruta, carpeta)
        if os.path.isfile(ruta_pdf):
            obras.append(ruta_pdf)

    return obras


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

    nombre_obra_match = NOMBRE_OBRA_RE.search(text)
    nombre_obra = nombre_obra_match.group("nombre_obra") if nombre_obra_match else "DESCONOCIDO"

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
            "nombre_obra": nombre_obra
        })

    return rows


def parse_ipi(p):
    return p.replace(",", "").replace("-", "").strip()


def parse_name(n: str) -> str:
    n = n.replace("\n", " ").replace("\r", " ")
    n = re.sub(r"\s+PAG\.\-\s*\d+$", "", n)
    return re.sub(r"\s+", " ", n).strip()


def fmt_pct(v: float) -> str:
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
                    "porcentajes": (
                        fmt_pct(data["pct1"]),
                        fmt_pct(data["pct2"])
                    ),
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


def export_excel(obras, folio, stop_event=None):

    def check_cancel():
        return stop_event is not None and stop_event.is_set()

    carpeta_base = obtener_carpeta_base()
    ruta_destino = carpeta_base / "MMs" / f"mm_agadu_{folio}.csv"

    with open(
        ruta_destino,
        "w",
        newline="",
        encoding="latin-1"
    ) as f:
        writer = csv.writer(f, delimiter=";")

        for obra in obras:
            if check_cancel():
                return {"cancelado": True}

            writer.writerow([obra["nombre_obra"], "", "", "", "", ""])
            writer.writerow([])
            writer.writerow([])
            writer.writerow([])

            suma_m_obra = round(sum((x.get("pct2") or 0.0) for x in obra["reparto"]), 2)
            mostrar_m = suma_m_obra > 0

            for r in obra["reparto"]:
                if check_cancel():
                    return {"cancelado": True}

                m_cell = fmt_pct(r["pct2"]) if mostrar_m else ""

                writer.writerow([
                    r["tipo"],
                    r["nombre"],
                    r["porcentajes"][0],
                    m_cell,
                    "",
                    r["ipi"],
                ])

            writer.writerow([])

    return {"ok": True, "ruta_destino": ruta_destino}