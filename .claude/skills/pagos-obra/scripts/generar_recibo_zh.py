#!/usr/bin/env python3
"""Recibo de pago de mano de obra con la marca ZH Construcciones: dos copias iguales en una hoja A4
(arriba copia para el obrero, abajo copia para ZH Construcciones) con línea de corte en el medio.

Uso:
    python3 generar_recibo_zh.py recibo.json salida.pdf

recibo.json (mismos campos que generar_recibo_pdf.py, más algunos opcionales):
    {"obra": "Galpon Yanussi", "proyecto": "GALPONES SAN SEVERINO", "ubicacion": "",
     "nombre": "VILLEGAS HECTOR", "concepto": "ALBAÑILERÍA", "rubro_archivo": "ALBAÑIL",
     "fecha_pago": "20/11/2026", "monto": 1200000,
     "mes_a_pagar": "",              # opcional (alquileres)
     "forma_pago": "Efectivo",       # opcional
     "numero": "YAN-20261120-01",    # opcional
     "observaciones": "Cavado de zanjas para vigas riostras laterales"}   # opcional (columna Observaciones de Datos Pagos)

Imprime el nombre del archivo con la misma convención de siempre:
    PAGO VIERNES 20.11.2026 (1.200.000) ALBAÑIL - Galpon Yanussi.pdf
"""
import json
import os
import sys

from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfgen import canvas

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from generar_recibo_pdf import cargar_fuentes, en_letras, fecha_larga, miles, nombre_archivo  # noqa: E402

NAVY = HexColor("#13243F")
NARANJA = HexColor("#F07C1E")
NARANJA_SUAVE = HexColor("#FFF1E6")
NARANJA_BORDE = HexColor("#F6C49A")
TEXTO = HexColor("#1D2433")
GRIS = HexColor("#6B7385")
LINEA = HexColor("#D9DEE7")
SUB = HexColor("#9FB0C9")
EMPRESA_SUB = "Arq. Josué Araoz - MP 15192  |  Arq. Bernabé Alessandrini - MP 16166  |  Oncativo, Córdoba"

W, H = A4
M = 30  # margen lateral


def caja(c, x, y, w, h, etiqueta, valor, reg, bold, tam=10):
    c.setStrokeColor(LINEA)
    c.setLineWidth(0.7)
    c.roundRect(x, y, w, h, 4, stroke=1, fill=0)
    c.setFillColor(GRIS)
    c.setFont(reg, 6.8)
    c.drawString(x + 7, y + h - 10, etiqueta.upper())
    c.setFillColor(TEXTO)
    c.setFont(bold, tam)
    texto = valor or "—"
    while pdfmetrics.stringWidth(texto, bold, tam) > w - 14 and tam > 7:
        tam -= 0.5
        c.setFont(bold, tam)
    c.drawString(x + 7, y + 7, texto)


def copia(c, top, d, reg, bold, leyenda):
    """Dibuja una copia dentro de la mitad de hoja cuyo borde superior es `top`."""
    alto = H / 2
    x0, x1 = M - 8, W - M + 8
    yt, yb = top - 22, top - alto + 22          # recuadro de la copia
    c.setStrokeColor(LINEA)
    c.setLineWidth(0.8)
    c.roundRect(x0, yb, x1 - x0, yt - yb, 8, stroke=1, fill=0)
    # Encabezado (dentro del recuadro, esquinas superiores redondeadas)
    hh = 44
    p = c.beginPath()
    r = 8
    p.moveTo(x0, yt - hh)
    p.lineTo(x0, yt - r)
    p.arcTo(x0, yt - 2 * r, x0 + 2 * r, yt, startAng=180, extent=-90)
    p.lineTo(x1 - r, yt)
    p.arcTo(x1 - 2 * r, yt - 2 * r, x1, yt, startAng=90, extent=-90)
    p.lineTo(x1, yt - hh)
    p.close()
    c.setFillColor(NAVY)
    c.drawPath(p, stroke=0, fill=1)
    c.setFillColor(NARANJA)
    c.rect(x0, yt - hh - 3, x1 - x0, 3, stroke=0, fill=1)
    c.setFont(reg, 15)
    c.drawString(M + 4, yt - 24, "ZH")
    c.setFillColor(HexColor("#FFFFFF"))
    c.drawString(M + 4 + pdfmetrics.stringWidth("ZH ", reg, 15), yt - 24, "CONSTRUCCIONES")
    c.setFillColor(SUB)
    c.setFont(reg, 6.3)
    c.drawString(M + 4, yt - 36, EMPRESA_SUB)
    c.setFillColor(NARANJA)
    c.setFont(bold, 15)
    c.drawRightString(W - M - 4, yt - 24, "RECIBO")
    if d.get("numero"):
        c.setFillColor(HexColor("#FFFFFF"))
        c.setFont(reg, 7.5)
        c.drawRightString(W - M - 4, yt - 36, f"N° {d['numero']}")

    # Leyenda de la copia
    y = yt - hh - 3 - 16
    c.setFillColor(NARANJA)
    c.setFont(bold, 7.5)
    c.drawRightString(W - M, y, leyenda)
    c.setFillColor(GRIS)
    c.setFont(reg, 7.5)
    c.drawString(M, y, f"Obra: {d['obra']}")

    # Datos
    bw = (W - 2 * M - 8) / 2
    bh = 28
    y -= 9 + bh
    caja(c, M, y, bw, bh, "Fecha de pago", fecha_larga(d["fecha_pago"]).capitalize(), reg, bold)
    caja(c, M + bw + 8, y, bw, bh, "Proyecto", d["proyecto"], reg, bold)
    y -= bh + 7
    caja(c, M, y, bw, bh, "Apellido y nombre", d["nombre"], reg, bold)
    caja(c, M + bw + 8, y, bw, bh, "Concepto", d["concepto"], reg, bold)
    extras = []
    if d.get("ubicacion"):
        extras.append(("Ubicación", d["ubicacion"]))
    if d.get("mes_a_pagar"):
        extras.append(("Mes a pagar", d["mes_a_pagar"]))
    if d.get("forma_pago"):
        extras.append(("Forma de pago", d["forma_pago"]))
    if extras:
        y -= bh + 7
        n = len(extras)
        ew = (W - 2 * M - 8 * (n - 1)) / n
        for i, (et, va) in enumerate(extras):
            caja(c, M + i * (ew + 8), y, ew, bh, et, va, reg, bold)

    # Observaciones (texto de la columna Observaciones de Datos Pagos)
    obs = " ".join(str(d.get("observaciones") or "").split())
    if obs:
        ow = W - 2 * M
        maxw = ow - 26
        lineas, linea = [], ""
        for palabra in obs.split():
            prueba = (linea + " " + palabra).strip()
            if pdfmetrics.stringWidth(prueba, reg, 9) > maxw:
                lineas.append(linea)
                linea = palabra
            else:
                linea = prueba
        lineas.append(linea)
        if len(lineas) > 2:
            lineas = lineas[:2]
            while pdfmetrics.stringWidth(lineas[1] + "…", reg, 9) > maxw:
                lineas[1] = lineas[1].rsplit(" ", 1)[0]
            lineas[1] += "…"
        oh = 20 + 11.5 * len(lineas)
        y -= oh + 7
        c.setFillColor(HexColor("#F6F7FA"))
        c.roundRect(M, y, ow, oh, 4, stroke=0, fill=1)
        c.setFillColor(NARANJA)
        c.rect(M, y, 3, oh, stroke=0, fill=1)
        c.setFillColor(GRIS)
        c.setFont(reg, 6.8)
        c.drawString(M + 12, y + oh - 10, "OBSERVACIONES")
        c.setFillColor(TEXTO)
        c.setFont(reg, 9)
        ty = y + oh - 22
        for ln in lineas:
            c.drawString(M + 12, ty, ln)
            ty -= 11.5

    # Monto
    ah = 44
    y -= ah + 12
    c.setFillColor(NARANJA_SUAVE)
    c.setStrokeColor(NARANJA_BORDE)
    c.setLineWidth(0.8)
    c.roundRect(M, y, W - 2 * M, ah, 5, stroke=1, fill=1)
    monto_txt = f"$ {miles(d['monto'])}"
    c.setFillColor(NAVY)
    c.setFont(bold, 20)
    c.drawRightString(W - M - 14, y + ah / 2 - 7, monto_txt)
    ancho_monto = pdfmetrics.stringWidth(monto_txt, bold, 20)
    c.setFillColor(HexColor("#9A4A08"))
    c.setFont(reg, 8.8)
    texto = f"Recibí conforme la suma de pesos {en_letras(d['monto'])} PESOS."
    maxw = W - 2 * M - ancho_monto - 44
    lineas, linea = [], ""
    for palabra in texto.split():
        prueba = (linea + " " + palabra).strip()
        if pdfmetrics.stringWidth(prueba, reg, 8.8) > maxw:
            lineas.append(linea)
            linea = palabra
        else:
            linea = prueba
    lineas.append(linea)
    lineas = lineas[:3]
    ty = y + ah / 2 - 3 + (len(lineas) - 1) * 5.5
    for ln in lineas:
        c.drawString(M + 14, ty, ln)
        ty -= 11

    # Firmas, al pie del recuadro
    yf = yb + 34
    c.setStrokeColor(HexColor("#9AA3B5"))
    c.setLineWidth(0.6)
    fw = 200
    c.line(M + 10, yf, M + 10 + fw, yf)
    c.line(W - M - 10 - fw, yf, W - M - 10, yf)
    c.setFillColor(GRIS)
    c.setFont(reg, 7.5)
    c.drawCentredString(M + 10 + fw / 2, yf - 11, "Firma")
    c.drawCentredString(W - M - 10 - fw / 2, yf - 11, "Aclaración y DNI")


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    d = json.load(open(sys.argv[1], encoding="utf-8"))
    reg, bold = cargar_fuentes()
    c = canvas.Canvas(sys.argv[2], pagesize=A4)
    c.setTitle(nombre_archivo(d)[:-4])
    copia(c, H, d, reg, bold, "COPIA PARA EL OBRERO")
    # Línea de corte
    c.setStrokeColor(HexColor("#B9C0CC"))
    c.setDash(4, 3)
    c.setLineWidth(0.7)
    c.line(20, H / 2, W - 20, H / 2)
    c.setDash()
    c.setFillColor(HexColor("#FFFFFF"))
    c.rect(W / 2 - 34, H / 2 - 5, 68, 10, stroke=0, fill=1)
    c.setFillColor(HexColor("#9AA3B5"))
    c.setFont(reg, 6.5)
    c.drawCentredString(W / 2, H / 2 - 2.3, "cortar aquí")
    copia(c, H / 2, d, reg, bold, "COPIA PARA ZH CONSTRUCCIONES")
    c.showPage()
    c.save()
    print(nombre_archivo(d))


if __name__ == "__main__":
    main()
