#!/usr/bin/env python3
"""Boleta semanal de pagos (planilla de la semana) con la marca ZH Construcciones, hoja A4 vertical.

Uso:
    python3 generar_planilla_zh.py datos.json salida.pdf

datos.json (mismos campos que generar_planilla_pdf.py, más opcionales):
    {"obra": "Galpon Yanussi",
     "fecha": "20/11/2026",
     "proyecto": "GALPONES SAN SEVERINO",          # opcional (B3 de Recibos M.O.)
     "formato_nombre": "Pagos {dd}-{mm}-{aa} Galpon Yanussi. Monto ${monto}.pdf",   # opcional
     "con_recibo": 2,                               # opcional: cuántos pagos llevan recibo
     "filas": [[M.O., Tarea, Observaciones, Forma de pago, monto], ...]}

Imprime el nombre del archivo según la convención de la carpeta de esa obra.
"""
import json
import os
import sys

from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph, Table, TableStyle

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from generar_recibo_pdf import cargar_fuentes, miles  # noqa: E402
from generar_planilla_pdf import nombre_archivo  # noqa: E402

NAVY = HexColor("#13243F")
NARANJA = HexColor("#F07C1E")
NARANJA_SUAVE = HexColor("#FFF1E6")
NARANJA_OSCURO = HexColor("#9A4A08")
TEXTO = HexColor("#1D2433")
GRIS = HexColor("#6B7385")
LINEA = HexColor("#E3E7EE")
SUB = HexColor("#9FB0C9")
EMPRESA_SUB = "Arq. Josué Araoz - MP 15192  |  Arq. Bernabé Alessandrini - MP 16166  |  Oncativo, Córdoba"
W, H = A4
M = 34


def fecha_4(fecha):
    d, m, y = fecha.split("/")
    y = y if len(y) == 4 else "20" + y
    return f"{int(d):02d}/{int(m):02d}/{y}"


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    d = json.load(open(sys.argv[1], encoding="utf-8"))
    filas = d["filas"]
    if not filas:
        sys.exit("No hay filas de pago para esta semana.")
    reg, bold = cargar_fuentes()
    fecha = fecha_4(d["fecha"])
    total = sum(float(f[4]) for f in filas)
    nombre = nombre_archivo(d["obra"], fecha, total, d.get("formato_nombre"))

    c = canvas.Canvas(sys.argv[2], pagesize=A4)
    c.setTitle(nombre[:-4])

    # Encabezado
    hh = 58
    c.setFillColor(NAVY)
    c.rect(0, H - hh, W, hh, stroke=0, fill=1)
    c.setFillColor(NARANJA)
    c.rect(0, H - hh - 4, W, 4, stroke=0, fill=1)
    c.setFont(reg, 18)
    c.drawString(M, H - 30, "ZH")
    c.setFillColor(HexColor("#FFFFFF"))
    c.drawString(M + pdfmetrics.stringWidth("ZH ", reg, 18), H - 30, "CONSTRUCCIONES")
    c.setFillColor(SUB)
    c.setFont(reg, 7)
    c.drawString(M, H - 45, EMPRESA_SUB)
    c.setFillColor(NARANJA)
    c.setFont(bold, 14)
    c.drawRightString(W - M, H - 30, "PLANILLA DE PAGOS")
    c.setFillColor(HexColor("#FFFFFF"))
    c.setFont(reg, 8.5)
    c.drawRightString(W - M, H - 45, f"Semana del viernes {fecha}")

    # Datos generales
    y = H - hh - 4 - 30
    con_recibo = d.get("con_recibo")
    datos = [("Obra", d["obra"]), ("Proyecto", d.get("proyecto") or "—"),
             ("Fecha de pago", fecha),
             ("Pagos", f"{len(filas)}" + (f"  ·  {con_recibo} con recibo" if con_recibo is not None else ""))]
    pesos = [1, 2.1, 0.9, 1]          # el proyecto suele ser largo
    unidad = (W - 2 * M) / sum(pesos)
    x = M
    for (et, va), pz in zip(datos, pesos):
        cw = unidad * pz
        c.setFillColor(GRIS)
        c.setFont(reg, 7)
        c.drawString(x, y + 12, et.upper())
        c.setFillColor(TEXTO)
        tam = 10
        while pdfmetrics.stringWidth(va, bold, tam) > cw - 12 and tam > 7:
            tam -= 0.5
        while pdfmetrics.stringWidth(va, bold, tam) > cw - 12 and len(va) > 4:
            va = va[:-2].rstrip() + "…"
        c.setFont(bold, tam)
        c.drawString(x, y, va)
        x += cw
    c.setStrokeColor(LINEA)
    c.setLineWidth(0.8)
    c.line(M, y - 12, W - M, y - 12)

    # Tabla de pagos
    st = ParagraphStyle("c", fontName=reg, fontSize=8.5, leading=11, textColor=TEXTO)
    sb = ParagraphStyle("b", parent=st, fontName=bold)
    sh = ParagraphStyle("h", parent=st, fontName=bold, fontSize=7.5, textColor=NARANJA_OSCURO)
    shr = ParagraphStyle("hr", parent=sh, alignment=2)
    sr = ParagraphStyle("r", parent=sb, alignment=2)
    esc = lambda t: str(t or "").replace("&", "&amp;").replace("<", "&lt;").replace("\n", "<br/>")
    rows = [[Paragraph("M.O.", sh), Paragraph("TAREA", sh), Paragraph("OBSERVACIONES", sh),
             Paragraph("FORMA DE PAGO", sh), Paragraph("MONTO", shr)]]
    for f in filas:
        rows.append([Paragraph(esc(f[0]), sb), Paragraph(esc(f[1]), st), Paragraph(esc(f[2]), st),
                     Paragraph(esc(f[3]), st), Paragraph(f"$ {miles(f[4])}", sr)])
    stt = ParagraphStyle("t", parent=sb, fontSize=10, textColor=HexColor("#FFFFFF"))
    sttr = ParagraphStyle("tr", parent=stt, alignment=2)
    rows.append([Paragraph("TOTAL DE LA SEMANA", stt), "", "", "", Paragraph(f"$ {miles(total)}", sttr)])
    anchos = [100, 110, 150, 95, W - 2 * M - 455]
    t = Table(rows, colWidths=anchos, repeatRows=1)
    n = len(rows)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NARANJA_SUAVE),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 7), ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("LEFTPADDING", (0, 0), (-1, -1), 6), ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("LINEBELOW", (0, 1), (-1, n - 3), 0.6, LINEA),
        ("SPAN", (0, n - 1), (3, n - 1)),
        ("BACKGROUND", (0, n - 1), (-1, n - 1), NAVY),
        ("TOPPADDING", (0, n - 1), (-1, n - 1), 9), ("BOTTOMPADDING", (0, n - 1), (-1, n - 1), 9),
    ]))
    tw, th = t.wrapOn(c, W - 2 * M, H)
    y = y - 26 - th
    t.drawOn(c, M, y)

    # Firmas
    yf = max(y - 70, 90)
    c.setStrokeColor(HexColor("#9AA3B5"))
    c.setLineWidth(0.6)
    fw = 190
    c.line(M + 10, yf, M + 10 + fw, yf)
    c.line(W - M - 10 - fw, yf, W - M - 10, yf)
    c.setFillColor(GRIS)
    c.setFont(reg, 7.5)
    c.drawCentredString(M + 10 + fw / 2, yf - 11, "Dirección de obra")
    c.drawCentredString(W - M - 10 - fw / 2, yf - 11, "Administración")

    # Pie
    c.setStrokeColor(LINEA)
    c.line(M, 40, W - M, 40)
    c.setFillColor(GRIS)
    c.setFont(reg, 7)
    c.drawString(M, 28, "ZH Construcciones  ·  Oncativo, Córdoba")
    c.drawRightString(W - M, 28, nombre[:-4])
    c.showPage()
    c.save()
    print(nombre)


if __name__ == "__main__":
    main()
