"""Convierte filas de la pestaña `Pagos` de "Control de Obras - Pagos Mano de Obra"
en propiedades de páginas para la base Finanzas de Notion.

Uso:
    python3 scripts/pagos_a_notion.py pagos.json [ids_existentes.txt] > nuevas.json

- pagos.json: salida de Sheets get_values sobre `Pagos!A2:K` ({"values": [[...], ...]}).
- ids_existentes.txt (opcional): un "ID planilla" por línea, ya cargado en Notion.
  Las filas con esos IDs se omiten para no duplicar.

"ID planilla" = "<Obra>#<Fila en Datos Pagos>" (nombre de obra tal cual figura en la planilla).
"""
import datetime as dt
import json
import sys

OBRA = {
    'Duplex Scorza': '421e5621-96e1-816e-8c65-c1c7a38b6fb6',
    'Quincho Cervelli': '421e5621-96e1-81ca-89b1-ec826ba1fadf',
    'Garaje Martino': '421e5621-96e1-8178-8b89-d3aecaef06e5',
    'Oficinas Martino': '421e5621-96e1-81ae-b67a-dd4abd0c6fff',
    'Galpon Yanussi': '421e5621-96e1-8182-9027-eb4c69e00c57',
    'Vivienda Pilla': '421e5621-96e1-81b9-ac56-ff285b72809e',
    'Vivienda Fraresso-Gallo': '421e5621-96e1-811d-a521-f488016e9454',
}
PROV = {
    'Alessandrini': '421e5621-96e1-81eb-8648-ff62fe640a0f',
    'Villalon': '421e5621-96e1-81b5-a34c-db5fe223817a',
    'Panelo': '421e5621-96e1-8180-b4a7-f1c7b173ea37',
    'Troilo': '421e5621-96e1-8128-ad18-cf3666ea3dd6',
    'Díaz': '421e5621-96e1-8194-a1e0-e18e698cfb0d',
    'Gonella': '421e5621-96e1-81bc-8a15-d31fdeaf1322',
    'Quiroga': '421e5621-96e1-8140-b81c-c2378254a5d5',
    'Papilla Rosas': '421e5621-96e1-8120-889e-eb59067c90ce',
    'Cejas': '421e5621-96e1-8163-9072-ef2d18066abe',
    'Boyero': '421e5621-96e1-8138-ba05-c8f889d3185c',
    'Taborda': '421e5621-96e1-81c8-a8e4-f8185e429c5c',
    'Trucco': '421e5621-96e1-81fb-9817-ebf4c8529510',
    'Prodesarrollo': '421e5621-96e1-81a5-a4e0-ed78b84c1456',
}
ALIAS = {'Alessandrini': 'Albañil Alessandrini', 'Baño Quimico': 'Baño Químico',
         'Nivelacion - Trucco': 'Nivelación - Trucco', '': 'Otros'}


def money(s):
    s = s.replace('$', '').replace('.', '').replace(' ', '').replace(',', '.').strip()
    return float(s) if s else 0.0


def convertir(fila):
    r = [x.strip() for x in fila + [''] * (11 - len(fila))]
    obra, _, fecha_pago, semana, _, mo, tarea, obs, forma, monto, nro = r[:11]
    mo = ALIAS.get(' '.join(mo.split()), ' '.join(mo.split()))
    fecha = dt.datetime.strptime(fecha_pago or semana, '%d/%m/%Y').date().isoformat()
    t = ' '.join(tarea.split())
    if t in ('', 'Otros'):
        first = ' '.join(obs.split('\n')[0].split())
        t = first[:60] + ('…' if len(first) > 60 else '')
    cat = ('Materiales' if mo == 'Prodesarrollo' else
           'Servicios' if mo in ('Baño Químico', 'Obrador') else
           'Otros' if mo == 'Otros' else 'Mano de obra')
    m = money(monto)
    p = {'Concepto': f'{mo} · {t}' if t else mo, 'Obra': [OBRA[obra]], 'Tipo': 'Egreso',
         'Categoría': cat, 'Monto': int(m) if m.is_integer() else m,
         'date:Fecha:start': fecha, 'Pagado': '__YES__', 'ID planilla': f'{obra}#{nro}'}
    prov = [v for k, v in PROV.items() if k in mo]
    if prov:
        p['Proveedor'] = prov
    fl = forma.lower()
    if 'transf' in fl:
        p['Medio de pago'] = 'Transferencia'
    elif 'efect' in fl:
        p['Medio de pago'] = 'Efectivo'
    elif 'cheq' in fl:
        p['Medio de pago'] = 'Cheque'
    notas = obs + (('\n' if obs else '') + 'Forma de pago: ' + forma if forma else '')
    if notas:
        p['Notas'] = notas
    return p


def main():
    filas = json.load(open(sys.argv[1]))['values']
    existentes = set()
    if len(sys.argv) > 2:
        existentes = {l.strip() for l in open(sys.argv[2]) if l.strip()}
    nuevas = [p for p in map(convertir, filas) if p['ID planilla'] not in existentes]
    json.dump([{'properties': p} for p in nuevas], sys.stdout, ensure_ascii=False)


if __name__ == '__main__':
    main()
