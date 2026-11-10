#!/usr/bin/env python3
"""Descarga el Índice del Costo de la Construcción de Córdoba (ICC-Cba) del
servicio de datos oficial de la Dirección General de Estadística y Censos.

Uso:
    python3 icc_cordoba.py                      # todos los meses disponibles
    python3 icc_cordoba.py --desde 1/9/2026     # solo meses POSTERIORES a esa fecha

Imprime JSON: lista de filas listas para escribir en 'ICC Córdoba'!A:B,
ordenadas del mes más viejo al más nuevo:
    [["1/10/2026", nivel_general], ...]
Con --capitulos agrega mano de obra, materiales y varios:
    [["1/10/2026", nivel_general, mano_de_obra, materiales, varios], ...]
Solo incluye meses con las cuatro categorías publicadas.

La página pública (https://estadistica.cba.gov.ar/portal/apps/sites/#/estadistica/pages/indice-del-costo-de-la-construccion)
es una app ArcGIS que lee de este mismo servicio.
"""
import argparse
import datetime
import json
import sys
import urllib.parse
import urllib.request

URL = ("https://smart-geo-data.cba.gov.ar/server/rest/services/"
       "Sitio_Web_Estadistica/ICC/FeatureServer/0/query")
CAT = {"A": 0, "C": 1, "B": 2, "D": 3}  # orden de columnas: NG, M.O., Materiales, Varios


def descargar():
    feats, offset = [], 0
    while True:
        q = urllib.parse.urlencode({
            "f": "json", "where": "1=1",
            "outFields": "fecha,categoría,valor",
            "orderByFields": "fecha DESC",
            "resultOffset": offset, "resultRecordCount": 200,
        })
        with urllib.request.urlopen(f"{URL}?{q}", timeout=60) as r:
            d = json.load(r)
        if "error" in d:
            sys.exit(f"Error del servicio: {d['error']}")
        feats += d.get("features", [])
        if not d.get("exceededTransferLimit"):
            return feats
        offset += len(d["features"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--desde", help="último mes ya cargado, D/M/AAAA")
    ap.add_argument("--capitulos", action="store_true", help="incluir mano de obra, materiales y varios")
    a = ap.parse_args()
    desde = None
    if a.desde:
        d, m, y = (int(x) for x in a.desde.split("/"))
        desde = datetime.date(y, m, d)

    meses = {}
    for f in descargar():
        at = f["attributes"]
        fecha = datetime.datetime.fromtimestamp(at["fecha"] / 1000, datetime.UTC).date()
        letra = at["categoría"].strip()[0]
        meses.setdefault(fecha, [None] * 4)[CAT[letra]] = at["valor"]

    out = []
    for fecha in sorted(meses):
        vals = meses[fecha]
        if None in vals or (desde and fecha <= desde):
            continue
        out.append([f"1/{fecha.month}/{fecha.year}", *(vals if a.capitulos else vals[:1])])
    json.dump(out, sys.stdout)
    print()


if __name__ == "__main__":
    main()
