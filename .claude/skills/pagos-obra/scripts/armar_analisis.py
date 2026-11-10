#!/usr/bin/env python3
"""Arma las llamadas para crear, en una planilla de obra, las pestañas
'ICC Córdoba' y 'Presupuesto vs Pagado' con el método de ajuste de saldo:

    Cada mes, al cerrar: saldo = (saldo anterior - pagos del mes) x (1 + variación
    mensual del ICC Nivel general del MES ANTERIOR).
    Ej.: presupuesto 100, se pagan 10 en octubre -> 90; al cerrar octubre se aplica
    la variación de septiembre (10%) -> 99.

No llama a ninguna API: escribe un JSON con pasos que se ejecutan con el
conector de Google Sheets, en orden:

  1. update_spreadsheet  pasos["crear_pestanas"]
  2. update_formulas     pasos["icc"]             (range + formulas)
  3. update_formulas     pasos["analisis_arriba"]
  4. update_formulas     pasos["matriz"]
  5. update_spreadsheet  pasos["copiar_y_formato"]

Uso:
    python3 icc_cordoba.py --desde 1/1/2025 > icc.json
    python3 armar_analisis.py --icc icc.json --mes-inicio 1/10/2026 [--obra "Duplex Scorza"] \
        [--id-analisis 900004] [--id-icc 900005] [--indice-analisis 4] \
        [--pagos "Datos Pagos"] [--presupuestos "Presupuestos M.O."] [--fecha-consulta DD/MM/AAAA] > pasos.json

Supuestos (ver references/estructura-planilla.md):
  - Pagos: datos desde la fila 4; A fecha pedido, C M.O., G monto, H fecha de pago.
    El mes de cada pago sale de la fecha de pago (H); si está vacía, de la fecha de pedido.
  - Presupuestos: contratistas en B3:B30, presupuesto en C3:C30.
  - Locale es_ES / es_AR: fórmulas con ";".
"""
import argparse
import json

N_MO = 28      # contratistas (filas 11..38 de la tabla y 46..73 de la matriz)
N_MESES = 24   # columnas C..Z de la matriz
COLS = [chr(ord("C") + i) for i in range(N_MESES)]  # C..Z
AMARILLO_TIT = {"red": 1, "green": 0.898, "blue": 0.596}
AMARILLO_INPUT = {"red": 1, "green": 1, "blue": 0}
AZUL = {"red": 0, "green": 0, "blue": 1}
GRIS = {"red": 0.847, "green": 0.847, "blue": 0.847}
GRIS_TXT = {"red": 0.349, "green": 0.349, "blue": 0.349}
BORDE = {"style": "SOLID", "color": {"red": 0.749, "green": 0.749, "blue": 0.749}}


def q(nombre):
    return "'" + nombre.replace("'", "''") + "'"


def gr(sid, r0, r1, c0, c1):
    g = {"sheetId": sid, "startColumnIndex": c0, "endColumnIndex": c1, "startRowIndex": r0}
    if r1 is not None:
        g["endRowIndex"] = r1
    return g


def fmt(sid, r0, r1, c0, c1, **f):
    uf, fields, tf = {}, [], {}
    for k, path in (("bold", "bold"), ("italic", "italic"), ("size", "fontSize"), ("font", "fontFamily")):
        if k in f:
            tf[path] = f[k]
            fields.append(f"userEnteredFormat.textFormat.{path}")
    if "fg" in f:
        tf["foregroundColor"] = f["fg"]
        fields.append("userEnteredFormat.textFormat.foregroundColor")
    if tf:
        uf["textFormat"] = tf
    if "bg" in f:
        uf["backgroundColor"] = f["bg"]
        fields.append("userEnteredFormat.backgroundColor")
    if "num" in f:
        uf["numberFormat"] = {"type": "NUMBER", "pattern": f["num"]}
        fields.append("userEnteredFormat.numberFormat")
    if "align" in f:
        uf["horizontalAlignment"] = f["align"]
        fields.append("userEnteredFormat.horizontalAlignment")
    if "valign" in f:
        uf["verticalAlignment"] = f["valign"]
        fields.append("userEnteredFormat.verticalAlignment")
    if f.get("wrap"):
        uf["wrapStrategy"] = "WRAP"
        fields.append("userEnteredFormat.wrapStrategy")
    return {"repeatCell": {"range": gr(sid, r0, r1, c0, c1), "cell": {"userEnteredFormat": uf},
                           "fields": ",".join(fields)}}


def bordes(sid, r0, r1, c0, c1):
    b = {k: BORDE for k in ("top", "bottom", "left", "right", "innerHorizontal", "innerVertical")}
    return {"updateBorders": {"range": gr(sid, r0, r1, c0, c1), **b}}


def ancho(sid, c0, c1, px, dim="COLUMNS"):
    return {"updateDimensionProperties": {"range": {"sheetId": sid, "dimension": dim, "startIndex": c0, "endIndex": c1},
                                          "properties": {"pixelSize": px}, "fields": "pixelSize"}}


def nota(sid, r, c, texto):
    return {"updateCells": {"rows": [{"values": [{"note": texto}]}], "fields": "note",
                            "start": {"sheetId": sid, "rowIndex": r, "columnIndex": c}}}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--icc", required=True, help="salida de icc_cordoba.py")
    ap.add_argument("--mes-inicio", required=True, help="mes de inicio del ajuste por defecto, 1/M/AAAA")
    ap.add_argument("--obra", default="Duplex Scorza")
    ap.add_argument("--id-analisis", type=int, default=900004)
    ap.add_argument("--id-icc", type=int, default=900005)
    ap.add_argument("--indice-analisis", type=int, default=4)
    ap.add_argument("--pagos", default="Datos Pagos")
    ap.add_argument("--presupuestos", default="Presupuestos M.O.")
    ap.add_argument("--fecha-consulta", default="")
    a = ap.parse_args()

    icc_rows = json.load(open(a.icc, encoding="utf-8"))
    SA, SI = a.id_analisis, a.id_icc
    P, PR = q(a.pagos), q(a.presupuestos)
    ICC = q("ICC Córdoba")
    pasos = {"crear_pestanas": [
        {"addSheet": {"properties": {"sheetId": SA, "title": "Presupuesto vs Pagado", "index": a.indice_analisis,
                                     "gridProperties": {"rowCount": 200, "columnCount": 31}}}},
        {"addSheet": {"properties": {"sheetId": SI, "title": "ICC Córdoba",
                                     "gridProperties": {"rowCount": 600, "columnCount": 4}}}},
    ]}

    # --- ICC Córdoba: A mes, B nivel general, C variación mensual (fórmula)
    icc = [["Índice del Costo de la Construcción, Córdoba (ICC-Cba): nivel general", None, None],
           ["Fuente: Dirección General de Estadística y Censos de Córdoba. Se agrega cada mes nuevo cuando se publica.", None, None],
           [None, None, None],
           ["Mes", "Nivel general (índice)", "Variación mensual"]]
    for i, r in enumerate(icc_rows):
        icc.append([r[0], r[1], "=ARRAYFORMULA(IF(A6:A=\"\";;B6:B/OFFSET(B5;0;0;ROWS(B6:B))-1))" if i == 1 else None])
    pasos["icc"] = {"range": f"{ICC}!A1:C{len(icc)}", "formulas": icc}

    # --- Parte de arriba: parámetros, tabla por contratista (fila 11 = plantilla) y detalle de pagos (AB:AE)
    cond = f"ISNUMBER({P}!G4:G)"
    W = 31
    def fila(*v):
        return list(v) + [None] * (W - len(v))
    arriba = [
        fila(f"{a.obra}: presupuesto vs pagado de mano de obra, con ajuste mensual del saldo por ICC Córdoba"),
        fila("Al cerrar cada mes, el saldo por pagar se ajusta con la variación mensual del ICC nivel general del mes "
             "anterior (en octubre se aplica la de septiembre). Celdas amarillas: datos a completar."),
        fila(), fila("Parámetros"),
        fila("Redondear la variación a un decimal (como se publica)", "Sí"),
        fila("Último ICC publicado", f"=MAX({ICC}!A5:A)"),
        fila("Mes en curso", "=EOMONTH(TODAY();-1)+1"),
        fila("Último mes ajustado", "=ARRAYFORMULA(IFERROR(LOOKUP(2;1/(C44:Z44=\"Sí\");C42:Z42);\"Ninguno todavía\"))"),
        fila("Presupuesto vs pagado por mano de obra", *[None] * 26, "Detalle de pagos (se completa solo desde " + a.pagos + ")"),
        fila("Mano de obra", "Presupuesto original", "Mes de inicio del ajuste", "Pagado", "Ajustes por ICC acumulados",
             "Saldo por pagar actual", "Presupuesto actualizado", "% ejecutado", *[None] * 19,
             "Fecha de pago", "Mes", "Mano de obra", "Monto"),
        fila(f"=IF({PR}!B3=\"\";\"\";{PR}!B3)",
             f"=IF(A11=\"\";\"\";N({PR}!C3))",
             a.mes_inicio,
             "=IF(A11=\"\";\"\";SUMIFS($AE$11:$AE;$AD$11:$AD;A11))",
             "=IF(N(B11)=0;\"\";F11-(B11-D11))",
             "=IF(N(B11)=0;\"\";XLOOKUP($B$7;$C$42:$Z$42;C46:Z46;\"\"))",
             "=IF(N(B11)=0;\"\";D11+F11)",
             "=IF(N(G11)=0;\"\";D11/G11)",
             *[None] * 19,
             f"=FILTER(IF(ISNUMBER({P}!H4:H);{P}!H4:H;{P}!A4:A);{cond})",
             "=ARRAYFORMULA(IF(AB11:AB=\"\";;EOMONTH(AB11:AB;-1)+1))",
             f"=FILTER({P}!C4:C;{cond})",
             f"=FILTER({P}!G4:G;{cond})"),
    ]
    pasos["analisis_arriba"] = {"range": f"{q('Presupuesto vs Pagado')}!A1:AE11", "formulas": arriba}

    # --- Total (39) y matriz de saldos (41..46; la fila 46 es plantilla)
    tot = ["Total", "=SUM(B11:B38)", None, "=SUM(D11:D38)", "=SUM(E11:E38)", "=SUM(F11:F38)", "=SUM(G11:G38)",
           "=IF(N(G39)=0;\"\";SUMIFS(D11:D38;B11:B38;\">0\")/G39)"]
    m = [tot + [None] * (26 - len(tot)), [None] * 26,
         ["Saldo por pagar al cierre de cada mes (solo contratistas con presupuesto)"] + [None] * 25]
    r42 = ["Mes", None]
    r43 = ["Variación aplicada (ICC del mes anterior)", None]
    r44 = ["¿Mes cerrado y ajustado?", None]
    r46 = ["=A11", "=B11"]
    for i, c in enumerate(COLS):
        prev_c = COLS[i - 1] if i else None
        r42.append("=EOMONTH(MIN(C11:C38);-1)+1" if i == 0 else f"=EDATE({prev_c}42;1)")
        r43.append(f"=IFERROR(LET(v;XLOOKUP(EDATE({c}42;-1);{ICC}!$A$5:$A;{ICC}!$C$5:$C);IF($B$5=\"Sí\";ROUND(v;3);v));\"\")")
        r44.append(f"=IF(AND(EOMONTH({c}42;0)<TODAY();{c}43<>\"\");\"Sí\";\"No\")")
        prev = "$B46" if i == 0 else f"{prev_c}46"
        r46.append(
            f"=IF(OR(N($B46)=0;{c}$42>$B$7);\"\";IF({c}$42<$C11;$B46;"
            f"({prev}-SUMIFS($AE$11:$AE;$AD$11:$AD;$A46;$AC$11:$AC;{c}$42))*(1+IF({c}$44=\"Sí\";{c}$43;0))))")
    m += [r42, r43, r44, ["Mano de obra", "Presupuesto"] + [None] * 24, r46]
    # Solo se escriben las columnas A:D; el resto de los meses se completa copiando D (y C en 43:44) hacia la derecha.
    m = [r[:4] for r in m]
    m[0] = tot  # fila total, A:H
    pasos["matriz"] = {"range": f"{q('Presupuesto vs Pagado')}!A39:H46",
                       "formulas": [r + [None] * (8 - len(r)) for r in m]}

    fuente = ("Fuente: Dirección General de Estadística y Censos de Córdoba, ICC-Cba nivel general. Servicio de datos: "
              "https://smart-geo-data.cba.gov.ar/server/rest/services/Sitio_Web_Estadistica/ICC/FeatureServer/0 . Página: "
              "https://estadistica.cba.gov.ar/portal/apps/sites/#/estadistica/pages/indice-del-costo-de-la-construccion"
              + (f" . Consultado el {a.fecha_consulta}." if a.fecha_consulta else "."))
    R = [
        {"copyPaste": {"source": gr(SA, 41, 42, 3, 4), "destination": gr(SA, 41, 42, 4, 26), "pasteType": "PASTE_NORMAL"}},
        {"copyPaste": {"source": gr(SA, 42, 44, 2, 3), "destination": gr(SA, 42, 44, 3, 26), "pasteType": "PASTE_NORMAL"}},
        {"copyPaste": {"source": gr(SA, 45, 46, 3, 4), "destination": gr(SA, 45, 46, 4, 26), "pasteType": "PASTE_NORMAL"}},
        {"copyPaste": {"source": gr(SA, 10, 11, 0, 8), "destination": gr(SA, 11, 10 + N_MO, 0, 8), "pasteType": "PASTE_NORMAL"}},
        {"copyPaste": {"source": gr(SA, 45, 46, 0, 26), "destination": gr(SA, 46, 45 + N_MO, 0, 26), "pasteType": "PASTE_NORMAL"}},
        {"setDataValidation": {"range": gr(SA, 4, 5, 1, 2), "rule": {"condition": {"type": "ONE_OF_LIST", "values": [
            {"userEnteredValue": "Sí"}, {"userEnteredValue": "No"}]}, "strict": True, "showCustomUi": True}}},
        nota(SI, 3, 0, fuente),
        nota(SA, 9, 2, "Primer mes en que corre el ajuste para ese contratista (normalmente el mes en que se firmó el "
                       "presupuesto o arrancó el trabajo). Se cargó el inicio de obra por defecto: confirmar o corregir."),
        nota(SA, 4, 1, "Sí: se usa la variación redondeada a un decimal, como la publica Estadística (1,2%). "
                       "No: se usa la variación exacta calculada con el índice."),
        fmt(SA, 0, 80, 0, W, font="Montserrat", size=10, valign="MIDDLE"),
        fmt(SA, 0, 1, 0, 1, bold=True, size=14), fmt(SA, 1, 2, 0, 1, italic=True, fg=GRIS_TXT),
        fmt(SA, 3, 4, 0, 1, bold=True, size=11), fmt(SA, 8, 9, 0, 1, bold=True, size=11),
        fmt(SA, 8, 9, 27, 28, bold=True, size=11), fmt(SA, 40, 41, 0, 1, bold=True, size=11),
        fmt(SA, 4, 8, 0, 1, bold=True),
        fmt(SA, 4, 5, 1, 2, bg=AMARILLO_INPUT, fg=AZUL, align="CENTER"),
        fmt(SA, 5, 8, 1, 2, num="mmmm yyyy", align="CENTER"),
        fmt(SA, 9, 10, 0, 8, bold=True, bg=AMARILLO_TIT, align="CENTER", wrap=True),
        fmt(SA, 9, 10, 27, 31, bold=True, bg=AMARILLO_TIT, align="CENTER", wrap=True),
        fmt(SA, 10, 39, 1, 2, num="$ #,##0"), fmt(SA, 10, 39, 3, 7, num="$ #,##0"),
        fmt(SA, 10, 38, 2, 3, num="mmm-yyyy", align="CENTER", bg=AMARILLO_INPUT, fg=AZUL),
        fmt(SA, 10, 39, 7, 8, num="0.0%"),
        fmt(SA, 38, 39, 0, 8, bold=True, bg=GRIS),
        fmt(SA, 10, None, 27, 28, num="d/m/yyyy", align="CENTER"), fmt(SA, 10, None, 28, 29, num="mmm-yyyy", align="CENTER"),
        fmt(SA, 10, None, 30, 31, num="$ #,##0"),
        fmt(SA, 41, 42, 0, 26, bold=True, bg=AMARILLO_TIT, align="CENTER", num="mmm-yyyy"),
        fmt(SA, 42, 43, 2, 26, num="0.0%", align="CENTER"), fmt(SA, 43, 44, 2, 26, align="CENTER"),
        fmt(SA, 41, 46, 0, 1, bold=True, wrap=True),
        fmt(SA, 44, 45, 0, 26, bold=True, bg=AMARILLO_TIT, align="CENTER"),
        fmt(SA, 45, 45 + N_MO, 1, 26, num="$ #,##0"),
        bordes(SA, 9, 39, 0, 8), bordes(SA, 9, 40, 27, 31), bordes(SA, 41, 44, 0, 26), bordes(SA, 44, 45 + N_MO, 0, 26),
        ancho(SA, 0, 1, 230), ancho(SA, 1, 8, 130), ancho(SA, 8, 26, 110), ancho(SA, 26, 27, 30), ancho(SA, 27, 31, 115),
        ancho(SA, 9, 10, 48, "ROWS"),
        {"updateSheetProperties": {"properties": {"sheetId": SA, "gridProperties": {"frozenColumnCount": 1}},
                                   "fields": "gridProperties.frozenColumnCount"}},
        fmt(SI, 0, 600, 0, 3, font="Montserrat", size=10),
        fmt(SI, 0, 1, 0, 1, bold=True, size=14), fmt(SI, 1, 2, 0, 1, italic=True, fg=GRIS_TXT),
        fmt(SI, 3, 4, 0, 3, bold=True, bg=AMARILLO_TIT, align="CENTER", wrap=True),
        fmt(SI, 4, None, 0, 1, num="mmm-yyyy", align="CENTER"), fmt(SI, 4, None, 1, 2, num="#,##0.00"),
        fmt(SI, 4, None, 2, 3, num="0.00%", align="CENTER"),
        {"updateSheetProperties": {"properties": {"sheetId": SI, "gridProperties": {"frozenRowCount": 4}},
                                   "fields": "gridProperties.frozenRowCount"}},
        ancho(SI, 0, 1, 100), ancho(SI, 1, 3, 150), ancho(SI, 3, 4, 40, "ROWS"),
    ]
    pasos["copiar_y_formato"] = R
    json.dump(pasos, open(1, "w", encoding="utf-8", closefd=False), ensure_ascii=False)
    print()


if __name__ == "__main__":
    main()
