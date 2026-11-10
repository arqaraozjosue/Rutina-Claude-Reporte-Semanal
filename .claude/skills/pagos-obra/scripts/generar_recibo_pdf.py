#!/usr/bin/env python3
"""Genera el recibo de pago para que firme la mano de obra (dos copias por hoja
A4, con el encabezado "RECIBO" de la empresa), igual a los de la carpeta
"Pagos Semanales".

Uso:
    python3 generar_recibo_pdf.py recibo.json salida.pdf [--encabezado encabezado.jpg]

recibo.json:
    {"obra": "Duplex Scorza",                                   # para el nombre del archivo
     "proyecto": "D.G.D DESARROLLO / DUPLEX – SCORZA ANDRES",
     "ubicacion": "LOTEO SAN SEVERINO",                         # opcional
     "nombre": "ALESSANDRINI RUBEN",
     "concepto": "ALBAÑILERÍA",
     "rubro_archivo": "ALBAÑIL",                                # va en el nombre del archivo
     "fecha_pago": "13/11/2026",                                # viernes de pago
     "monto": 1400000}

La fecha del recibo queda en blanco (FECHA: ____ DE <año>) para completarla a mano
al firmar, como en los recibos originales.

Imprime el nombre de archivo según la convención de la carpeta:
    PAGO VIERNES 13.11.2026 (1.400.000) ALBAÑIL - Duplex Scorza.pdf
"""
import argparse
import json
import os
import tempfile
import urllib.request

from reportlab.lib.colors import Color
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

FONT_URLS = {
    "Montserrat": "https://fonts.gstatic.com/s/montserrat/v31/JTUHjIg1_i6t8kCHKm4532VJOt5-QNFgpCtr6Ew-.ttf",
    "Montserrat-Bold": "https://fonts.gstatic.com/s/montserrat/v31/JTUHjIg1_i6t8kCHKm4532VJOt5-QNFgpCuM70w-.ttf",
}
ROJO = Color(1, 0, 0)
AQUI = os.path.dirname(os.path.abspath(__file__))
ENCABEZADO = os.path.join(AQUI, "..", "assets", "encabezado_recibo.jpg")

UNIDADES = ["", "UN", "DOS", "TRES", "CUATRO", "CINCO", "SEIS", "SIETE", "OCHO", "NUEVE", "DIEZ",
            "ONCE", "DOCE", "TRECE", "CATORCE", "QUINCE", "DIECISÉIS", "DIECISIETE", "DIECIOCHO",
            "DIECINUEVE", "VEINTE", "VEINTIÚN", "VEINTIDÓS", "VEINTITRÉS", "VEINTICUATRO",
            "VEINTICINCO", "VEINTISÉIS", "VEINTISIETE", "VEINTIOCHO", "VEINTINUEVE"]
DECENAS = ["", "", "", "TREINTA", "CUARENTA", "CINCUENTA", "SESENTA", "SETENTA", "OCHENTA", "NOVENTA"]
CENTENAS = ["", "CIENTO", "DOSCIENTOS", "TRESCIENTOS", "CUATROCIENTOS", "QUINIENTOS", "SEISCIENTOS",
            "SETECIENTOS", "OCHOCIENTOS", "NOVECIENTOS"]


def _menor_mil(n):
    if n == 0:
        return ""
    if n == 100:
        return "CIEN"
    c, r = divmod(n, 100)
    partes = [CENTENAS[c]] if c else []
    if r < 30:
        partes.append(UNIDADES[r])
    else:
        d, u = divmod(r, 10)
        partes.append(DECENAS[d] + (f" Y {UNIDADES[u]}" if u else ""))
    return " ".join(p for p in partes if p)


def en_letras(n):
    """1400000 -> 'UN MILLON CUATROCIENTOS MIL' (sin tilde en MILLON, como en los recibos)."""
    n = int(round(n))
    if n == 0:
        return "CERO"
    millones, resto = divmod(n, 1_000_000)
    miles, unidades = divmod(resto, 1000)
    partes = []
    if millones:
        partes.append("UN MILLON" if millones == 1 else f"{_menor_mil(millones)} MILLONES")
    if miles:
        partes.append("MIL" if miles == 1 and not millones else f"{_menor_mil(miles)} MIL")
    if unidades:
        u = _menor_mil(unidades)
        partes.append(u + "O" if u.endswith(" UN") or u == "UN" else u.replace("VEINTIÚN", "VEINTIUNO") if u.endswith("VEINTIÚN") else u)
    return " ".join(partes)


def miles(n):
    return f"{int(round(n)):,}".replace(",", ".")


def cargar_fuentes():
    try:
        d = tempfile.mkdtemp()
        for name, url in FONT_URLS.items():
            p = os.path.join(d, name + ".ttf")
            urllib.request.urlretrieve(url, p)
            pdfmetrics.registerFont(TTFont(name, p))
        return "Montserrat", "Montserrat-Bold"
    except Exception:
        return "Helvetica", "Helvetica-Bold"


def copia(c, top, d, reg, bold, encabezado):
    """Dibuja una copia del recibo; top = distancia desde el borde superior de la hoja (pt)."""
    H = A4[1]
    y = lambda t: H - t
    c.drawImage(encabezado, 14, y(top + 89), width=567, height=89)
    c.setFillColor(ROJO)
    anio = d["fecha_pago"].split("/")[2]
    c.setFont(reg, 10)
    c.drawRightString(559, y(top + 130), f"FECHA: {'_' * 38} DE {anio}")

    def campo(t, etiqueta, valor):
        c.setFont(bold, 10)
        c.drawString(36, y(top + t), etiqueta)
        if valor:
            w = pdfmetrics.stringWidth(etiqueta + " ", bold, 10)
            c.setFont(reg, 10)
            c.drawString(36 + w, y(top + t), valor)

    t = 172
    c.setFont(bold, 10)
    c.drawString(36, y(top + t), f"PROYECTO: {d['proyecto']}")
    if d.get("ubicacion"):
        t += 21
        c.drawString(36, y(top + t), f"UBICACIÓN: {d['ubicacion']}")
    t += 21
    campo(t, "APELLIDO Y NOMBRE:", d["nombre"])
    t += 21
    campo(t, "CONCEPTO:", d["concepto"])

    # Texto del monto, cortado a lo ancho como en el original
    texto = f"Recibí conforme la suma de pesos: {en_letras(d['monto'])} PESOS. Son: $ {miles(d['monto'])}."
    c.setFont(reg, 10)
    lineas, linea = [], ""
    for palabra in texto.split():
        prueba = (linea + " " + palabra).strip()
        if pdfmetrics.stringWidth(prueba, reg, 10) > 520:
            lineas.append(linea)
            linea = palabra
        else:
            linea = prueba
    lineas.append(linea)
    t += 40
    for ln in lineas:
        c.drawString(36, y(top + t), ln)
        t += 21

    c.setLineWidth(0.6)
    c.setStrokeColor(ROJO)
    c.line(410, y(top + 360), 560, y(top + 360))
    c.setFont(reg, 8)
    c.drawCentredString(485, y(top + 376), "Firma y Aclaración")


def nombre_archivo(d):
    dd, mm, aa = d["fecha_pago"].split("/")
    return (f"PAGO VIERNES {int(dd):02d}.{int(mm):02d}.{aa} ({miles(d['monto'])}) "
            f"{d['rubro_archivo']} - {d['obra']}.pdf")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("datos")
    ap.add_argument("salida")
    ap.add_argument("--encabezado", default=ENCABEZADO, help="imagen del encabezado RECIBO")
    a = ap.parse_args()
    d = json.load(open(a.datos, encoding="utf-8"))
    reg, bold = cargar_fuentes()
    c = canvas.Canvas(a.salida, pagesize=A4)
    c.setTitle(nombre_archivo(d)[:-4])
    copia(c, 20, d, reg, bold, a.encabezado)
    copia(c, 430, d, reg, bold, a.encabezado)
    c.showPage()
    c.save()
    print(nombre_archivo(d))


if __name__ == "__main__":
    main()
