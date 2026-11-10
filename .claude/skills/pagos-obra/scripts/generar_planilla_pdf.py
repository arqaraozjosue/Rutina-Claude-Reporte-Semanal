#!/usr/bin/env python3
"""Genera la planilla semanal de pagos de una obra en PDF, con el formato de
las planillas que se guardan en Drive (título amarillo, M.O. en gris, total).

Uso:
    python3 generar_planilla_pdf.py datos.json salida.pdf

datos.json:
    {"obra": "Duplex Scorza",            # opcional, por defecto "Duplex Scorza"
     "fecha": "13/11/2026",              # viernes de pago, DD/MM/AAAA
     "filas": [["Albañil Alessandrini", "Armaduras", "Corte de hierros...",
                "Transferencia \\nruben.alessa", 1400000], ...]}
    Cada fila: [M.O., Tarea/rubro, Observaciones, Forma de pago, Monto].

Imprime el nombre de archivo según la convención de la carpeta:
    Pagos DD-MM-YY <obra>. Monto $X.XXX.XXX.pdf
"""
import json
import os
import sys
import tempfile
import urllib.request

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Table, TableStyle

FONT_URLS = {
    "Montserrat": "https://fonts.gstatic.com/s/montserrat/v31/JTUHjIg1_i6t8kCHKm4532VJOt5-QNFgpCtr6Ew-.ttf",
    "Montserrat-Bold": "https://fonts.gstatic.com/s/montserrat/v31/JTUHjIg1_i6t8kCHKm4532VJOt5-QNFgpCuM70w-.ttf",
}
AMARILLO = colors.Color(1, 0.898, 0.596)
GRIS = colors.Color(0.847, 0.847, 0.847)


def cargar_fuentes():
    """Montserrat, como en la planilla; si no se puede descargar, Helvetica."""
    try:
        d = tempfile.mkdtemp()
        for name, url in FONT_URLS.items():
            p = os.path.join(d, name + ".ttf")
            urllib.request.urlretrieve(url, p)
            pdfmetrics.registerFont(TTFont(name, p))
        return "Montserrat", "Montserrat-Bold"
    except Exception:
        return "Helvetica", "Helvetica-Bold"


def pesos(n):
    """1400000 -> '1.400.000,00'."""
    s = f"{n:,.2f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def pesos_entero(n):
    """1400000 -> '1.400.000' (para el nombre del archivo)."""
    return f"{round(n):,}".replace(",", ".")


def nombre_archivo(obra, fecha, total):
    d, m, y = fecha.split("/")
    return f"Pagos {int(d):02d}-{int(m):02d}-{y[-2:]} {obra}. Monto ${pesos_entero(total)}.pdf"


def main(src, out):
    data = json.load(open(src, encoding="utf-8"))
    obra = data.get("obra", "Duplex Scorza")
    fecha = data["fecha"]
    filas = data["filas"]
    if not filas:
        sys.exit("No hay filas de pago para esta semana.")
    total = sum(float(f[4]) for f in filas)

    reg, bold = cargar_fuentes()

    def st(font, align):
        return ParagraphStyle("s", fontName=font, fontSize=7.5, leading=10, alignment=align)

    c_bold, c_reg, l_reg = st(bold, TA_CENTER), st(reg, TA_CENTER), st(reg, TA_LEFT)

    # Anchos proporcionales a las columnas A:E de la hoja (116,151,179,96,105 px)
    px = [116, 151, 179, 96, 105]
    cw = [542 * p / sum(px) for p in px]

    rows = [[Paragraph(f"{obra} - Pagos semana {fecha}", c_bold), "", "", "", ""]]
    for mo, rubro, desc, forma, monto in filas:
        rows.append([
            Paragraph(str(mo), c_bold),
            Paragraph(str(rubro), c_reg),
            Paragraph(str(desc).strip(), l_reg),
            Paragraph(str(forma).strip().replace("\n", "<br/>"), c_reg),
            Paragraph(f"$&nbsp;&nbsp;&nbsp;&nbsp;{pesos(float(monto))}", l_reg),
        ])
    rows.append(["", "", "", "", Paragraph(f"$&nbsp;&nbsp;{pesos(total)}", st(bold, TA_LEFT))])

    n = len(rows)
    t = Table(rows, colWidths=cw)
    t.setStyle(TableStyle([
        ("SPAN", (0, 0), (4, 0)),
        ("BACKGROUND", (0, 0), (4, 0), AMARILLO),
        ("BACKGROUND", (0, 1), (0, n - 2), GRIS),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BOX", (0, 0), (4, 0), 1.2, colors.black),
        ("BOX", (0, 1), (4, n - 2), 1.2, colors.black),
        ("INNERGRID", (0, 1), (4, n - 2), 0.5, colors.black),
        ("BOX", (0, n - 1), (4, n - 1), 1.2, colors.black),
        ("BOX", (4, n - 1), (4, n - 1), 1.2, colors.black),
        ("TOPPADDING", (0, 0), (-1, -1), 1.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1.5),
        ("LEFTPADDING", (0, 0), (-1, -1), 2),
        ("RIGHTPADDING", (0, 0), (-1, -1), 2),
    ]))

    SimpleDocTemplate(out, pagesize=A4, leftMargin=26, rightMargin=26, topMargin=50,
                      bottomMargin=40, title=f"Pagos {fecha} {obra}").build([t])
    print(nombre_archivo(obra, fecha, total))


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])
