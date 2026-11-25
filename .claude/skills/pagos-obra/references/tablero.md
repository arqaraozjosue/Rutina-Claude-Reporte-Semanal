# Planilla central y tablero de obras

Objetivo: ver todas las obras sin abrir archivo por archivo, hoy en la planilla central y más adelante en un tablero o una app de escritorio.

## Arquitectura

```
Planilla de cada obra (Google Sheets, formato estándar)  ──►  consolidar.py  ──►  Control de Obras (Google Sheets)  ──►  Tablero / app
   Datos Pagos · Presupuesto vs Pagado · Recibos M.O.                              Resumen · Pagos · Saldos M.O. · Alertas · Obras
```

- **Fuente de verdad de los pagos:** la pestaña "Datos Pagos" de cada obra (ahí se carga todo).
- **Registro de obras:** pestaña "Obras" de la central (ID `1Z4InsHdZ0IJ41CWlNJe3d09XFNmIAkw5a2MsnhKJmfQ`). Una obra nueva = una fila nueva.
- **Tabla única para el tablero:** pestaña "Pagos" de la central: una fila por pago de cualquier obra.

## Modelo de datos (pestañas de la central)

**Pagos** (una fila por pago)
| Columna | Tipo | Nota |
|---|---|---|
| Obra | texto | nombre como en Obras |
| Fecha pedido | fecha | |
| Fecha de pago | fecha | vacía si no se cargó |
| Semana (viernes) | fecha | viernes de la semana de pago (o de pedido si no hay pago) |
| Mes | fecha (día 1) | mes de pago |
| M.O. | texto | contratista, como en Datos Pagos |
| Tarea, Observaciones, Forma de pago | texto | |
| Monto | número | pesos |
| Fila en Datos Pagos | número | para volver al origen |

**Saldos M.O.**: Obra, Mano de obra, Presupuesto original, Mes inicio ajuste, Pagado, Ajustes ICC acumulados, Saldo por pagar actual, Presupuesto actualizado, % ejecutado (sale de "Presupuesto vs Pagado" de cada obra).

**Alertas**: Obra, Tipo, Detalle.

**Resumen**: fórmulas sobre Pagos y Saldos M.O. B3 = semana a mirar (viernes) y D3 = mes (celdas amarillas, se pueden cambiar a mano).

**Obras**: código, obra, estado, links, ID de planilla, carpetas, Excel original, pestaña de planillas, prefijo del título, formato de fecha, nombre del PDF semanal, inicio.

## Opciones para el tablero

1. **Looker Studio (gratis, sin programar):** fuente de datos = Google Sheets → "Control de Obras" → pestaña Pagos (y otra fuente con Saldos M.O.). Filtros por obra, M.O. y mes; gráficos de pagado por semana y saldo por contratista. Se actualiza solo cuando se actualiza la central.
2. **App de escritorio propia (Python):** leer la central con la API de Google Sheets (cuenta de servicio o OAuth, alcance `spreadsheets.readonly`) y mostrar con Streamlit, Dash o PySide. Para datos en vivo sin esperar la consolidación, la app puede recorrer la pestaña Obras y leer cada "Datos Pagos" directo: la lógica está en `scripts/consolidar.py` (`leer_obra`), reutilizable tal cual cambiando la descarga por la API.
3. **Power BI / Excel:** conectar a la central exportada como .xlsx o vía conector de Google Sheets.

## Reglas para que el tablero no se rompa

- No cambiar nombres de pestañas ni el orden de columnas de "Datos Pagos" (A fecha pedido … H fecha de pago).
- Escribir cada M.O. siempre igual dentro de una obra (las alertas avisan cuando no).
- Toda obra nueva se agrega en la pestaña Obras con su ID de planilla.
