---
name: pagos-obra
description: Gestión semanal de pagos de mano de obra de una obra de construcción en Google Sheets y Drive. Sirve para pasar a la planilla los pagos que el usuario dicta o escribe de forma informal, generar la planilla semanal de pagos (bloque en la hoja y PDF en Drive con el nombre "Pagos DD-MM-YY <obra>. Monto $X.pdf"), generar los recibos que firma cada mano de obra ("PAGO VIERNES DD.MM.AAAA (monto) RUBRO - <obra>.pdf"), actualizar el ICC de Córdoba nivel general y mantener el análisis de saldo por pagar ajustado mes a mes por ICC. Usala siempre que el usuario hable de pagos de la obra, contratistas o M.O., la planilla o el reporte semanal de pagos, el PDF de pagos de la semana, recibos o boletas de pago para firmar, presupuestos de mano de obra, saldo o avance de un contratista, ICC o actualizar presupuestos por índice, o mencione Duplex Scorza u otra obra con esta planilla, aunque no nombre la skill.
---

# Pagos de obra

Flujo de pagos de mano de obra de una obra: el usuario carga los pagos en "Datos Pagos", cada viernes se paga, y por cada semana se arma una planilla (bloque en la hoja y PDF en Drive). Además se sigue cuánto se pagó contra el presupuesto de cada contratista, actualizado por el ICC de Córdoba.

La estructura detallada de cada pestaña, con ejemplos y errores conocidos, está en `references/estructura-planilla.md`. Leela antes de la primera escritura en una planilla.

Antes de editar la planilla, cargá también el skill `google-workspace` si está disponible: tiene las reglas del conector de Sheets (rangos 0-based, field masks, verificación).

## 1. Identificar la obra

Cada obra tiene una planilla de Google Sheets y una carpeta de Drive para los PDF. Si el usuario no los da, buscalos con Drive (`title contains 'Pagos'`) y confirmá cuál es. Obra conocida:

| Obra | Planilla | Carpeta planillas PDF | Carpeta recibos | Pestaña planillas |
|---|---|---|---|---|
| Duplex Scorza | `1NCSXuZIceSNyMogyojV40FqGBCUu-p1cZpHOqt2ceFc` | `1O-9azxTTW1LmJz6KbCLPBuq0MNLgWjt7` | `1J3f5axqB7aUy160cwNzpVklmez3modTC` ("Pagos Semanales") | "Pagos Duplex Scorza" (sheetId 1434351530) |

En una obra nueva, leé los nombres de pestañas y la fila de encabezados (`get_spreadsheet` con `fields: ["sheets.properties"]` y `get_values` de las primeras filas) y mapeá las columnas antes de escribir. Si la estructura difiere mucho, decíselo al usuario en lugar de forzarla.

La planilla está en locale es_ES: las fórmulas llevan `;` como separador y los nombres de función en inglés.

## 2. Cargar pagos dictados o informales

El usuario suele escribir algo como "el viernes le pago 1.4M a Alessandrini por armaduras, y 20 lucas en efectivo del flete". Pasalo a filas de "Datos Pagos":

1. Leé `'Datos Pagos'!A3:I` para ver la última fila con datos y los nombres de contratistas, tareas y formas de pago ya usados. Reusá esos textos exactos: el análisis cruza por nombre de contratista, y "Alessandrini" no coincide con "Albañil Alessandrini".
2. Armá cada fila: A fecha pedido (hoy, si no dice otra), B la fórmula `=TEXT(A<n>; "mmmm-yyy")`, C M.O., D tarea, E observaciones, F forma de pago (para una transferencia, "Transferencia \n<alias>" con el alias que ya figura para ese contratista), G monto como número, H fecha de pago (el viernes que corresponda).
3. Interpretá las abreviaturas: "1.4M" o "1,4 palos" = 1400000, "20 lucas" = 20000.
4. **Mostrá la tabla y pedí confirmación antes de escribir**, salvo que el usuario haya dicho que la cargues directo. Señalá lo que tuviste que suponer (contratista nuevo, fecha, alias faltante).
5. Escribí en las filas libres que siguen a la última con datos (`update_formulas`), copiá el formato de la fila anterior (`copyPaste` PASTE_FORMAT) y verificá con `get_values`.

Si el contratista no existe en "Presupuestos M.O.", avisá: sus pagos van a aparecer en el análisis sin presupuesto.

## 3. Planilla semanal + PDF

1. **Detectar semanas pendientes.** Agrupá las filas de "Datos Pagos" con monto en G por fecha de pago (H). Leé `'<pestaña planillas>'!A:E` y tomá la fecha del último título "… - Pagos semana DD/MM/AAAA". Las fechas de pago posteriores son semanas nuevas. Las anteriores ya se procesaron: no las rehagas aunque haya una fecha rara (en Duplex Scorza, 15/5/2026 es un error de tipeo ya incluido en la semana del 09/10).
   - Si el usuario pide una semana puntual, hacé esa aunque ya exista el bloque, pero preguntá antes de duplicar.
2. **Bloque en la hoja.** Después del último total, dejá una fila vacía y escribí: el título `'<Obra> - Pagos semana DD/MM/AAAA` (con apóstrofe, para que quede como texto), una fila por pago `[M.O., Tarea, Observaciones, Forma de pago, Monto]` en el orden de Datos Pagos, y la fila total con E = `=+SUM(E<primera>:E<última>)`. Después un `update_spreadsheet` con `copyPaste` PASTE_FORMAT desde el bloque anterior (título, una fila de pago para cada fila nueva, total) y `mergeCells` del título A:E. Verificá con `get_values` que el total coincida con la suma.
3. **PDF.** Escribí un JSON `{"obra": "...", "fecha": "DD/MM/AAAA", "filas": [[M.O., Tarea, Observaciones, Forma de pago, monto], ...]}` y corré:
   ```bash
   python3 -I <skill>/scripts/generar_planilla_pdf.py datos.json salida.pdf
   ```
   El script imprime el nombre de archivo según la convención de la carpeta (`Pagos 13-11-26 Duplex Scorza. Monto $1.400.000.pdf`). Para controlar el resultado, mirá una imagen (`pdftoppm -r 70 -png salida.pdf pag`).
4. **Subirlo a Drive.** Primero buscá en la carpeta si ya hay un archivo con ese nombre (`parentId = '<carpeta>'`) para no duplicar. Después `create_file` con `title` = nombre impreso, `parentId` = carpeta, `contentMimeType: "application/pdf"`, `disableConversionToGoogleType: true` y `base64Content` como referencia al archivo (`sha256:<hex>:<ruta absoluta>`).
5. Respondé con el total de la semana y el link al PDF.

Los nombres viejos de la carpeta tienen errores de año ("30-10-29"). No los corrijas sin que te lo pidan; los nuevos van con el año correcto.

## 3b. Recibos para firmar

Por cada semana, cada mano de obra firma un recibo: una hoja A4 con dos copias iguales, el encabezado "RECIBO" de la empresa, proyecto, ubicación, apellido y nombre, concepto y el monto en letras y en números. La fecha queda en blanco para completarla a mano al firmar.

1. Leé `'Recibos M.O.'!A3:E40`: B3 proyecto, B4 ubicación, B5 obra (para el nombre del archivo), B6 carpeta de recibos; desde la fila 9, por cada M.O. (escrito igual que en Datos Pagos): apellido y nombre, concepto, rubro para el nombre del archivo y si hace recibo.
2. Agrupá los pagos de la semana por M.O. y sumá. Hacé recibo solo para los que tienen apellido y nombre y "Hace recibo" = Sí. Si alguien cobró y no tiene datos, no inventes el nombre: avisá para que lo completen en esa pestaña.
3. Por cada uno, escribí `recibo.json` y corré:
   ```bash
   python3 -I <skill>/scripts/generar_recibo_pdf.py recibo.json recibo.pdf
   ```
   con `{"obra", "proyecto", "ubicacion", "nombre", "concepto", "rubro_archivo", "fecha_pago": "DD/MM/AAAA", "monto"}`. El script pone el monto en letras como en los originales ("UN MILLON CUATROCIENTOS MIL PESOS") e imprime el nombre: `PAGO VIERNES 13.11.2026 (1.400.000) ALBAÑIL - Duplex Scorza.pdf`. El encabezado sale de `assets/encabezado_recibo.jpg`. Si no tenés la skill instalada (por ejemplo, en una tarea programada), extraelo de un recibo existente: `pdfimages -j -f 1 -l 1 recibo_existente.pdf hdr` y pasá `--encabezado hdr-000.jpg`.
4. Mirá la imagen del PDF y subilo a la carpeta de recibos como en el paso 3.4, sin duplicar nombres.

## 4. Actualizar el ICC Córdoba

El ICC lo publica la Dirección General de Estadística y Censos de Córdoba, alrededor de mediados de cada mes, con el dato del mes anterior. La página pública es una app que lee de un servicio de datos; el script consulta ese servicio directamente:

```bash
python3 -I <skill>/scripts/icc_cordoba.py --desde <último mes cargado, 1/M/AAAA>
```

Imprime las filas nuevas `[["1/10/2026", nivel general], ...]`, del mes más viejo al más nuevo (con `--capitulos` agrega mano de obra, materiales y varios, que hoy no se usan). Agregalas debajo de la última fila de `'ICC Córdoba'!A:B` con `update_values`. No escribas en C: la variación mensual es una ARRAYFORMULA que se extiende sola. Si la lista viene vacía, todavía no se publicó nada nuevo.

Si el servicio no responde, probá la página https://estadistica.cba.gov.ar/portal/apps/sites/#/estadistica/pages/indice-del-costo-de-la-construccion. No inventes ni estimes un índice: si no hay dato, el análisis usa el último publicado y lo marca como "No, se usa el último".

## 5. Análisis presupuesto vs pagado

### Método (lo definió el usuario)
Solo importa la **variación mensual del ICC nivel general**, y se aplica sobre lo que queda **por pagar**, siempre con el mes vencido:

    saldo al cierre del mes M = (saldo al cierre de M-1 − pagos de M) × (1 + variación del ICC de M-1)

Ejemplo: presupuesto $100, en octubre se pagan $10 → saldo $90. Al cerrar octubre se aplica la variación de septiembre (supongamos 10%) → $99. En noviembre se aplica la de octubre, y así.
- El primer mes del ajuste de cada contratista es el "Mes de inicio del ajuste" (input amarillo); antes de eso el saldo es el presupuesto.
- Un mes se ajusta cuando terminó y ya está publicada la variación del mes anterior. El mes en curso muestra el saldo con los pagos hechos, sin ajuste todavía.
- La variación se redondea a un decimal, como la publica Estadística (1,2% en septiembre 2026). Hay un selector para usar la exacta.
- Cada pago cae en el mes de su fecha de pago (si no tiene, en el de la fecha de pedido).

### Si la planilla ya tiene "Presupuesto vs Pagado"
Se recalcula solo. Leé `'Presupuesto vs Pagado'!A1:Z73` y respondé con esos números, sin recalcular por tu cuenta lo que la hoja ya calcula:
- Filas 10 a 39: por contratista, presupuesto original, mes de inicio, pagado, ajustes por ICC acumulados, saldo por pagar actual, presupuesto actualizado (pagado + saldo) y % ejecutado.
- Filas 42 a 73: matriz de saldos al cierre de cada mes (24 meses, columnas C:Z), con la variación aplicada y si el mes ya se ajustó.
- Columnas AB:AE: detalle de pagos traído de Datos Pagos.
Para vigilar: contratistas con pagos y presupuesto 0 (sus pagos no entran al ajuste), más de 28 contratistas o una obra que pase los 24 meses (hay que extender la tabla o la matriz), y mes de inicio todavía en el valor por defecto.

### Si hay que crearlo (obra nueva)
1. Mes de inicio de obra (fila 2 de Datos Pagos) como mes de inicio del ajuste por defecto.
2. `python3 -I <skill>/scripts/icc_cordoba.py --desde 1/<mes>/<año-1> > icc.json` (con un año de serie alcanza; toda la serie arranca en 1991).
3. `python3 -I <skill>/scripts/armar_analisis.py --icc icc.json --mes-inicio 1/M/AAAA --obra "<Obra>" --fecha-consulta DD/MM/AAAA > pasos.json` (opciones `--id-analisis`, `--id-icc` si esos sheetId están ocupados; `--pagos`, `--presupuestos` si las pestañas se llaman distinto).
4. En orden: `update_spreadsheet` con `crear_pestanas`; `update_formulas` con `icc`, `analisis_arriba` y `matriz` (cada uno trae `range` y `formulas`); `update_spreadsheet` con `copiar_y_formato`, que completa los meses copiando hacia la derecha y los contratistas hacia abajo.
5. Verificá con `get_values` y explicá las celdas amarillas.

## 6. Rutina semanal

Si el usuario quiere que esto corra solo, se crea una tarea programada que cada semana hace los pasos 3, 3b, 4 y 5 (verificación) y manda un resumen con alertas. La tarea necesita los conectores de Google Drive y Google Sheets: si no se pueden asociar al crearla, decile que los agregue desde la pantalla de rutinas de claude.ai. Como las sesiones programadas no tienen esta skill instalada salvo que el repo esté adjunto, el pedido de la tarea tiene que incluir los scripts de PDF completos y cómo sacar el encabezado del recibo de un recibo existente en Drive.

## Qué no hacer

- No modifiques los datos que cargó el usuario en Datos Pagos ni en Presupuestos M.O., salvo que te lo pida (cargar pagos nuevos sí está permitido, siguiendo la sección 2).
- No borres ni renombres PDF de la carpeta.
- No toques las pestañas "Reporte" ni "Tareas". "Recibos M.O." la completa el usuario.

## Resumen al terminar

Cerrá con pocas líneas: qué se creó (semana, total, links de planilla y recibos), meses de ICC agregados, saldo por pagar de cada contratista con presupuesto y alertas:
- pagos con monto pero sin fecha de pago;
- fecha de pago anterior a la fecha de pedido;
- contratistas con % ejecutado > 90% o saldo actualizado negativo;
- pagos a contratistas sin presupuesto cargado;
- mano de obra que cobró y no tiene datos para el recibo.
