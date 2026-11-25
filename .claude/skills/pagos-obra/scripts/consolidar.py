#!/usr/bin/env python3
"""Arma la planilla central "Control de Obras" a partir de las planillas de pagos de todas las obras.

Uso:
    python3 consolidar.py --obras config/obras.json --exportados DIR --salida control.xlsx [--hoy DD/MM/AAAA]

- obras.json: registro de obras (obra, codigo, planilla, carpeta_planillas, carpeta_recibos, ...).
- DIR: una exportación .xlsx de cada planilla de obra, con nombre <codigo>.xlsx
  (Drive download_file_content con exportMimeType xlsx).

Todas las planillas de obra tienen el mismo formato estándar:
  Datos Pagos: A fecha pedido, B mes, C M.O., D tarea, E observaciones, F forma de pago,
               G monto, H fecha de pago. Datos desde la fila 4.
  Presupuesto vs Pagado: filas 11-38, A:H (M.O., presupuesto, mes inicio, pagado, ajustes ICC,
               saldo por pagar, presupuesto actualizado, % ejecutado).
  Recibos M.O.: desde la fila 9, A M.O., B apellido y nombre, E hace recibo.

Genera las pestañas:
  Resumen        una fila por obra (fórmulas sobre Pagos y Saldos M.O.).
  Pagos          todos los pagos de todas las obras en una sola tabla (base para el tablero).
  Saldos M.O.    presupuesto, pagado y saldo ajustado por ICC de cada contratista de cada obra.
  Alertas        datos a revisar (fechas raras, nombres que no coinciden, recibos sin datos...).
  Obras          registro de obras con links a planillas y carpetas.
"""
import argparse
import datetime as dt
import json
import os
import sys
import warnings

import openpyxl
from openpyxl.styles import Alignment, Font, PatternFill, Border, Side
from openpyxl.utils import get_column_letter

warnings.filterwarnings("ignore")

FUENTE = "Montserrat"
AMARILLO = "FFE598"
GRIS = "D8D8D8"
AZUL = "1F3864"
MONEDA = '"$" #,##0'
HOY = dt.date.today()
# Conceptos que no son contratistas con presupuesto propio
GENERICOS = {"otros", "obrador", "baño quimico", "baño químico", "volquete", "pozo y sondeo"}
FECHA = "dd/mm/yyyy"


def pesos(n):
    return ("-" if n < 0 else "") + "$" + f"{abs(n):,.0f}".replace(",", ".")


def viernes_de(fecha):
    """Viernes de la semana de pago (lunes a domingo)."""
    return fecha + dt.timedelta(days=(4 - fecha.weekday()))


def leer_obra(ruta, obra):
    wb = openpyxl.load_workbook(ruta, data_only=True)
    pagos, alertas, sin_fecha = [], [], []
    ws = wb["Datos Pagos"]
    for i, r in enumerate(ws.iter_rows(min_row=4, max_col=8, values_only=True), start=4):
        fped, _mes, mo, tarea, obs, forma, monto, fpago = (list(r) + [None] * 8)[:8]
        if not isinstance(monto, (int, float)) or monto == 0:
            continue
        fped = fped if isinstance(fped, dt.datetime) else None
        fpago = fpago if isinstance(fpago, dt.datetime) else None
        mo = (mo or "").strip() if isinstance(mo, str) else (mo or "")
        if fpago is None:
            sin_fecha.append((i, monto))
        if fped and fpago and abs((fpago.date() - fped.date()).days) > 45:
            alertas.append((obra, "Fecha mal cargada (pedido y pago muy separados)",
                            f"Fila {i}: {mo}, pedido {fped:%d/%m/%Y}, pago {fpago:%d/%m/%Y}"))
        elif fped and fpago and fpago.date() < fped.date():
            alertas.append((obra, "Fecha de pago anterior al pedido",
                            f"Fila {i}: {mo}, pedido {fped:%d/%m/%Y}, pago {fpago:%d/%m/%Y}"))
        ref = fpago or fped
        if ref and (ref.year < 2020 or (ref.date() - HOY).days > 90):
            alertas.append((obra, "Fecha imposible", f"Fila {i}: {mo}, fecha {ref:%d/%m/%Y}"))
        semana = viernes_de(ref).date() if ref else None
        pagos.append({
            "obra": obra, "fila": i, "fecha_pedido": fped.date() if fped else None,
            "fecha_pago": fpago.date() if fpago else None, "semana": semana,
            "mes": dt.date(ref.year, ref.month, 1) if ref else None,
            "mo": mo, "tarea": tarea or "", "obs": obs or "",
            "forma": (forma or "").replace("\n", " ").strip() if isinstance(forma, str) else "",
            "monto": float(monto),
        })

    if sin_fecha:
        filas = ", ".join(str(f) for f, _ in sin_fecha[:12]) + ("..." if len(sin_fecha) > 12 else "")
        total = sum(m for _, m in sin_fecha)
        alertas.append((obra, f"Pagos sin fecha de pago ({len(sin_fecha)})",
                        f"Total {pesos(total)}; se toman con la fecha de pedido. Filas: {filas}"))

    saldos, vistos = [], set()
    if "Presupuesto vs Pagado" in wb.sheetnames:
        wa = wb["Presupuesto vs Pagado"]
        for r in wa.iter_rows(min_row=11, max_row=38, max_col=8, values_only=True):
            mo, pres, inicio, pagado, ajuste, saldo, actualizado, pct = r
            if not mo or str(mo).strip() in vistos:
                continue
            vistos.add(str(mo).strip())
            saldos.append({"obra": obra, "mo": str(mo).strip(), "presupuesto": pres or 0,
                           "inicio": inicio.date() if isinstance(inicio, dt.datetime) else None,
                           "pagado": pagado or 0, "ajuste": ajuste if isinstance(ajuste, (int, float)) else None,
                           "saldo": saldo if isinstance(saldo, (int, float)) else None,
                           "actualizado": actualizado if isinstance(actualizado, (int, float)) else None,
                           "pct": pct if isinstance(pct, (int, float)) else None})

    recibos = {}
    if "Recibos M.O." in wb.sheetnames:
        wr = wb["Recibos M.O."]
        for r in wr.iter_rows(min_row=9, max_row=60, max_col=5, values_only=True):
            if r[0]:
                recibos[str(r[0])] = (r[1] or "", (r[4] or "").strip())

    # Alertas de cruce
    nombres_pres = {s["mo"] for s in saldos}
    for mo in sorted({p["mo"] for p in pagos}):
        if mo and mo not in nombres_pres:
            alertas.append((obra, "M.O. que no figura en Presupuestos M.O.",
                            f"'{mo}': revisá si está escrito distinto (sus pagos no entran al análisis)"))
        if mo in recibos and recibos[mo][1] == "Sí" and not recibos[mo][0]:
            alertas.append((obra, "Recibo sin apellido y nombre", f"'{mo}': completalo en Recibos M.O."))
    for s in saldos:
        if s["presupuesto"] and s["pct"] is not None and s["pct"] > 0.9:
            alertas.append((obra, "Contratista con más del 90% ejecutado",
                            f"{s['mo']}: {s['pct']:.0%} (saldo ${(s['saldo'] or 0):,.0f})".replace(",", ".")))
        if s["presupuesto"] and s["saldo"] is not None and s["saldo"] < 0:
            alertas.append((obra, "Saldo negativo (se pagó más que el presupuesto actualizado)",
                            f"{s['mo']}: ${s['saldo']:,.0f}".replace(",", ".")))
        if not s["presupuesto"] and s["pagado"] and s["mo"].lower() not in GENERICOS:
            alertas.append((obra, "Pagos a contratista sin presupuesto",
                            f"{s['mo']}: pagado ${s['pagado']:,.0f}".replace(",", ".")))
    return pagos, saldos, alertas


def estilo_encabezado(ws, fila, ncols):
    for c in range(1, ncols + 1):
        cel = ws.cell(fila, c)
        cel.font = Font(name=FUENTE, bold=True, color="FFFFFF", size=10)
        cel.fill = PatternFill("solid", fgColor=AZUL)
        cel.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    ws.row_dimensions[fila].height = 32


def titulo(ws, texto, sub=None):
    ws["A1"] = texto
    ws["A1"].font = Font(name=FUENTE, bold=True, size=14, color=AZUL)
    if sub:
        ws["A2"] = sub
        ws["A2"].font = Font(name=FUENTE, italic=True, size=9, color="595959")


def fuente_base(ws, desde, hasta, ncols):
    for r in range(desde, hasta + 1):
        for c in range(1, ncols + 1):
            cel = ws.cell(r, c)
            if cel.font is None or cel.font.name != FUENTE:
                cel.font = Font(name=FUENTE, size=10, bold=cel.font.bold if cel.font else False)


def anchos(ws, lista):
    for i, w in enumerate(lista, start=1):
        ws.column_dimensions[get_column_letter(i)].width = w


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--obras", required=True)
    ap.add_argument("--exportados", required=True)
    ap.add_argument("--salida", required=True)
    ap.add_argument("--hoy", default="")
    ap.add_argument("--json", default="", help="además, escribe las filas de Pagos, Saldos M.O. y Alertas "
                    "en un JSON para actualizar la planilla central existente con update_values")
    a = ap.parse_args()
    hoy = dt.datetime.strptime(a.hoy, "%d/%m/%Y").date() if a.hoy else dt.date.today()
    global HOY
    HOY = hoy
    obras = json.load(open(a.obras, encoding="utf-8"))
    obras = obras["obras"] if isinstance(obras, dict) else obras

    todos_pagos, todos_saldos, todas_alertas = [], [], []
    for o in obras:
        ruta = os.path.join(a.exportados, f"{o['codigo']}.xlsx")
        if not os.path.exists(ruta):
            todas_alertas.append((o["obra"], "Planilla no exportada", ruta))
            continue
        p, s, al = leer_obra(ruta, o["obra"])
        todos_pagos += p
        todos_saldos += s
        todas_alertas += al

    todos_pagos.sort(key=lambda p: (p["semana"] or dt.date.min, p["obra"], p["fila"]))
    wb = openpyxl.Workbook()

    # ---------- Resumen ----------
    ws = wb.active
    ws.title = "Resumen"
    titulo(ws, "Control de Obras: pagos de mano de obra",
           f"Actualizado al {hoy:%d/%m/%Y}. Los totales salen de las pestañas Pagos y Saldos M.O.")
    ws["A3"] = "Semana (viernes)"
    ws["B3"] = viernes_de(dt.datetime.combine(hoy, dt.time())).date()
    ws["B3"].number_format = FECHA
    ws["B3"].fill = PatternFill("solid", fgColor=AMARILLO)
    ws["C3"] = "Mes"
    ws["D3"] = dt.date(hoy.year, hoy.month, 1)
    ws["D3"].number_format = "mmmm yyyy"
    ws["D3"].fill = PatternFill("solid", fgColor=AMARILLO)
    for c in ("A3", "C3"):
        ws[c].font = Font(name=FUENTE, bold=True, size=10)
    enc = ["Obra", "Estado", "Pagado semana", "Pagado en el mes", "Pagado total",
           "Presupuesto M.O. original", "Saldo por pagar (ajustado ICC)", "Presupuesto actualizado",
           "% ejecutado", "Última semana pagada", "Cant. pagos", "Planilla"]
    ws.append([])
    ws.append(enc)
    f0 = 5
    estilo_encabezado(ws, f0, len(enc))
    for i, o in enumerate(obras, start=f0 + 1):
        n = o["obra"]
        ws.cell(i, 1, n).font = Font(name=FUENTE, bold=True, size=10)
        ws.cell(i, 2, o.get("estado", "En curso"))
        ws.cell(i, 3, f'=SUMIFS(Pagos!$J:$J,Pagos!$A:$A,$A{i},Pagos!$D:$D,$B$3)')
        ws.cell(i, 4, f'=SUMIFS(Pagos!$J:$J,Pagos!$A:$A,$A{i},Pagos!$E:$E,$D$3)')
        ws.cell(i, 5, f'=SUMIFS(Pagos!$J:$J,Pagos!$A:$A,$A{i})')
        ws.cell(i, 6, f"=SUMIFS('Saldos M.O.'!$C:$C,'Saldos M.O.'!$A:$A,$A{i})")
        ws.cell(i, 7, f"=SUMIFS('Saldos M.O.'!$G:$G,'Saldos M.O.'!$A:$A,$A{i})")
        ws.cell(i, 8, f"=SUMIFS('Saldos M.O.'!$H:$H,'Saldos M.O.'!$A:$A,$A{i})")
        ws.cell(i, 9, f"=IF(H{i}=0,\"\",SUMIFS('Saldos M.O.'!$E:$E,'Saldos M.O.'!$A:$A,$A{i},'Saldos M.O.'!$C:$C,\">0\")/H{i})")
        ws.cell(i, 10, f'=IFERROR(MAXIFS(Pagos!$D:$D,Pagos!$A:$A,$A{i}),"")')
        ws.cell(i, 11, f'=COUNTIFS(Pagos!$A:$A,$A{i})')
        url = f"https://docs.google.com/spreadsheets/d/{o['planilla']}/edit"
        ws.cell(i, 12, f'=HYPERLINK("{url}","Abrir")')
    ft = f0 + len(obras) + 1
    ws.cell(ft, 1, "TOTAL").font = Font(name=FUENTE, bold=True, size=10)
    for c in (3, 4, 5, 6, 7, 8, 11):
        L = get_column_letter(c)
        ws.cell(ft, c, f"=SUM({L}{f0 + 1}:{L}{ft - 1})").font = Font(name=FUENTE, bold=True, size=10)
    for r in range(f0 + 1, ft + 1):
        for c in (3, 4, 5, 6, 7, 8):
            ws.cell(r, c).number_format = MONEDA
        ws.cell(r, 9).number_format = "0.0%"
        ws.cell(r, 10).number_format = FECHA
        if r == ft:
            for c in range(1, len(enc) + 1):
                ws.cell(r, c).fill = PatternFill("solid", fgColor=GRIS)
                ws.cell(r, c).border = Border(top=Side(style="medium"))
    fuente_base(ws, 3, ft, len(enc))
    anchos(ws, [26, 11, 16, 17, 17, 20, 22, 20, 11, 15, 10, 10])
    ws.freeze_panes = "B6"

    # ---------- Pagos ----------
    wp = wb.create_sheet("Pagos")
    enc = ["Obra", "Fecha pedido", "Fecha de pago", "Semana (viernes)", "Mes", "M.O.", "Tarea",
           "Observaciones", "Forma de pago", "Monto", "Fila en Datos Pagos"]
    wp.append(enc)
    estilo_encabezado(wp, 1, len(enc))
    for p in todos_pagos:
        wp.append([p["obra"], p["fecha_pedido"], p["fecha_pago"], p["semana"], p["mes"], p["mo"],
                   p["tarea"], p["obs"], p["forma"], p["monto"], p["fila"]])
    for r in range(2, wp.max_row + 1):
        for c in (2, 3, 4):
            wp.cell(r, c).number_format = FECHA
        wp.cell(r, 5).number_format = "mmm-yyyy"
        wp.cell(r, 10).number_format = MONEDA
    fuente_base(wp, 2, wp.max_row, len(enc))
    anchos(wp, [24, 12, 12, 13, 11, 24, 28, 50, 28, 14, 10])
    wp.freeze_panes = "B2"
    wp.auto_filter.ref = f"A1:{get_column_letter(len(enc))}{wp.max_row}"

    # ---------- Saldos M.O. ----------
    wsal = wb.create_sheet("Saldos M.O.")
    enc = ["Obra", "Mano de obra", "Presupuesto original", "Mes inicio ajuste", "Pagado",
           "Ajustes ICC acumulados", "Saldo por pagar actual", "Presupuesto actualizado", "% ejecutado"]
    wsal.append(enc)
    estilo_encabezado(wsal, 1, len(enc))
    for s in todos_saldos:
        if not s["presupuesto"] and not s["pagado"]:
            continue
        wsal.append([s["obra"], s["mo"], s["presupuesto"], s["inicio"], s["pagado"], s["ajuste"],
                     s["saldo"], s["actualizado"], s["pct"]])
    for r in range(2, wsal.max_row + 1):
        for c in (3, 5, 6, 7, 8):
            wsal.cell(r, c).number_format = MONEDA
        wsal.cell(r, 4).number_format = "mmm-yyyy"
        wsal.cell(r, 9).number_format = "0.0%"
    fuente_base(wsal, 2, wsal.max_row, len(enc))
    anchos(wsal, [24, 26, 18, 13, 16, 18, 18, 18, 11])
    wsal.freeze_panes = "C2"
    wsal.auto_filter.ref = f"A1:I{wsal.max_row}"

    # ---------- Alertas ----------
    wal = wb.create_sheet("Alertas")
    enc = ["Obra", "Tipo", "Detalle"]
    wal.append(enc)
    estilo_encabezado(wal, 1, 3)
    for al in todas_alertas:
        wal.append(list(al))
    fuente_base(wal, 2, wal.max_row, 3)
    anchos(wal, [24, 44, 90])
    wal.freeze_panes = "A2"
    wal.auto_filter.ref = f"A1:C{wal.max_row}"

    # ---------- Obras ----------
    wo = wb.create_sheet("Obras")
    enc = ["Código", "Obra", "Estado", "Planilla (Google Sheets)", "ID planilla", "Carpeta planillas semanales",
           "Carpeta recibos", "Excel original (respaldo)"]
    wo.append(enc)
    estilo_encabezado(wo, 1, len(enc))
    for o in obras:
        wo.append([o["codigo"], o["obra"], o.get("estado", "En curso"),
                   f'=HYPERLINK("https://docs.google.com/spreadsheets/d/{o["planilla"]}/edit","Abrir planilla")',
                   o["planilla"],
                   f'=HYPERLINK("https://drive.google.com/drive/folders/{o["carpeta_planillas"]}","Pagos {o["obra"]}")',
                   f'=HYPERLINK("https://drive.google.com/drive/folders/{o["carpeta_recibos"]}","Pagos Semanales")',
                   f'=HYPERLINK("https://drive.google.com/file/d/{o["excel_original"]}/view","Excel")' if o.get("excel_original") else ""])
    fuente_base(wo, 2, wo.max_row, len(enc))
    anchos(wo, [18, 26, 11, 18, 48, 30, 18, 14])
    wo.freeze_panes = "C2"

    wb.save(a.salida)
    if a.json:
        f = lambda d: d.strftime("%d/%m/%Y") if isinstance(d, (dt.date, dt.datetime)) else ("" if d is None else d)
        filas = lambda ws: [[f(c) for c in r] for r in ws.iter_rows(min_row=2, values_only=True)]
        json.dump({"actualizado": f"Actualizado al {hoy:%d/%m/%Y}. Los totales salen de las pestañas Pagos y Saldos M.O.",
                   "semana": f(viernes_de(dt.datetime.combine(hoy, dt.time())).date()),
                   "mes": f(dt.date(hoy.year, hoy.month, 1)),
                   "pagos": filas(wp), "saldos": filas(wsal), "alertas": filas(wal)},
                  open(a.json, "w", encoding="utf-8"), ensure_ascii=False)
    print(json.dumps({"pagos": len(todos_pagos), "saldos": wsal.max_row - 1, "alertas": len(todas_alertas)}))


if __name__ == "__main__":
    main()
