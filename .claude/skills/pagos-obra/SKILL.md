---
name: "pagos-obra"
description: Gestión semanal de pagos de mano de obra de TODAS las obras en Google Sheets y Drive, con una planilla central "Control de Obras". Sirve para pasar a la planilla de cada obra los pagos que el usuario dicta o escribe de forma informal, generar la planilla semanal de pagos de cada obra (bloque en la hoja y PDF "boleta" en la carpeta "Pagos" de la obra), generar los recibos que firma cada mano de obra (carpeta "Pagos Semanales"), actualizar el ICC de Córdoba, mantener el análisis de saldo por pagar ajustado por ICC y actualizar la planilla central que junta todas las obras (base del tablero). Usala siempre que el usuario hable de pagos de obra, contratistas o M.O., planillas o boletas semanales, recibos para firmar, presupuestos de mano de obra, saldo o avance de un contratista, ICC, el control o tablero de obras, o mencione Duplex Scorza, Quincho Cervelli, Garaje Martino, Oficinas Martino, Galpón Yanussi, Vivienda Pilla, Vivienda Fraresso-Gallo u otra obra, aunque no nombre la skill.
---

# Pagos de obra (todas las obras)

Cada obra tiene su planilla de Google Sheets "Pagos Manos de Obra - <Obra>. Claude" con el mismo formato estándar. Cada viernes se paga; por cada semana y obra se arma una planilla semanal (bloque en la hoja + PDF en `00-Datos/Pagos <obra>`) y un recibo por mano de obra (PDF en `00-Datos/Pagos Semanales`). La planilla central "Control de Obras" junta todas las obras.

Referencias (leelas antes de la primera escritura):
- `references/estructura-planilla.md`: formato estándar de cada pestaña y particularidades de cada obra.
- `references/tablero.md`: modelo de datos de la planilla central, para el tablero o una app de escritorio.

Antes de editar planillas, cargá también la skill `google-workspace` si está disponible.

## 0. Registro de obras

La fuente de verdad es la pestaña **Obras** de la planilla central `Control de Obras - Pagos Mano de Obra` (`1Z4InsHdZ0IJ41CWlNJe3d09XFNmIAkw5a2MsnhKJmfQ`). Leé `Obras!A1:M30`: código, obra, estado, link, ID de planilla, carpetas (en los HYPERLINK), Excel original, pestaña de planillas semanales, prefijo del título de bloque, formato de fecha del título, formato del nombre del PDF semanal e inicio de obra. `config/obras.json` es una copia con los IDs de carpetas en limpio; si difieren, manda la pestaña Obras y avisá.

Procesá solo las obras con estado "En curso". Si el usuario nombra una obra, trabajá solo esa.

**Obra nueva:** buscá en su carpeta `05-Computos` el Excel "Pagos Manos de Obra - <Obra>" y en `00-Datos` las carpetas "Pagos <obra>" y "Pagos Semanales". Convertí el Excel a Sheets (`create_file` con el .xlsx sin `disableConversionToGoogleType`, título "… . Claude", misma carpeta), estandarizá "Datos Pagos" (ver referencias: columna B "Mes"), copiá de Duplex las pestañas "Recibos M.O.", "ICC Córdoba" y "Presupuesto vs Pagado" (`copy_sheet_to_another_spreadsheet`: primero ICC, renombrala, después el análisis; cambiá A1 y C11:C38 = mes de inicio), completá Recibos M.O. con los datos de recibos anteriores y agregá la fila en Obras y en `config/obras.json`. El Excel original no se toca.

La planilla está en locale es_ES: fórmulas con `;` y nombres en inglés. Todo lo que se genera va en fuente **Montserrat** (`assets/fonts/`).

## 1. Cargar pagos dictados o informales

El usuario suele escribir algo como "Yanussi: el viernes 1.2M a Panelo por zanjas en efectivo; Pilla: 200 lucas a Alessandrini". Puede mezclar obras en un mensaje: separalas.

1. Leé `'Datos Pagos'!A3:I` de esa obra: última fila con datos y los nombres de M.O., tareas y formas de pago ya usados. Reusá los textos exactos ("Albañil Panelo", no "Panelo"); el análisis y los recibos cruzan por nombre.
2. Cada fila: A fecha pedido (hoy si no dice otra), B `=IF(ISNUMBER(A<n>);TEXT(A<n>;"mmmm-yyy");"")`, C M.O., D tarea, E observaciones, F forma de pago ("Transferencia\n<alias>" con el alias que ya figura para ese M.O.), G monto (número), H fecha de pago (el viernes).
3. "1.4M" o "1,4 palos" = 1400000; "20 lucas" = 20000.
4. **Mostrá la tabla por obra y pedí confirmación** antes de escribir, salvo que te digan que cargues directo. Señalá lo supuesto (M.O. nuevo, fecha, alias, obra).
5. Escribí en las filas libres (`update_formulas`), copiá el formato de la fila anterior (`copyPaste` PASTE_FORMAT) y verificá con `get_values`.
6. Controles: si el alias no coincide con el del M.O. (p. ej. "Baño Quimico" con el alias del obrador), preguntá. Si el M.O. no está en "Presupuestos M.O." ni en "Recibos M.O.", avisá.

## 2. Planilla semanal ("boleta") + PDF, por obra

1. **Semanas pendientes.** Agrupá "Datos Pagos" con monto en G por fecha de pago (H). En la pestaña de planillas de la obra (columna "Pestaña planillas semanales"), buscá el último título "<prefijo> - Pagos semana <fecha>" (la fecha puede venir dd/mm/aa o dd/mm/aaaa). Las fechas de pago posteriores son semanas nuevas; las anteriores ya están hechas, no las rehagas.
2. **Bloque en la hoja.** Después del último total, una fila vacía y: título `'<prefijo> - Pagos semana <fecha en el formato de esa obra>`, una fila por pago `[M.O., Tarea, Observaciones, Forma de pago, Monto]` y el total `=+SUM(E<primera>:E<última>)` en E. Formato: `copyPaste` PASTE_FORMAT desde el bloque anterior + `mergeCells` del título A:E. Verificá el total.
3. **PDF (formato ZH Construcciones, desde el 25/11/2026).** JSON `{"obra", "fecha": "DD/MM/AAAA", "proyecto": <B3 de Recibos M.O.>, "con_recibo": <cuántos M.O. de la semana llevan recibo>, "formato_nombre": <"Nombre del PDF semanal" de la obra>, "filas": [[M.O., Tarea, Observaciones, Forma de pago, monto], ...]}` y:
   ```bash
   python3 -I <skill>/scripts/generar_planilla_zh.py datos.json salida.pdf
   ```
   Hoja A4 con encabezado azul "ZH CONSTRUCCIONES" (ZH en naranja), datos de la obra, tabla de pagos, total de la semana y firmas de dirección de obra y administración. Imprime el nombre según la convención de la carpeta de esa obra. Mirá una imagen (`pdftoppm -r 70 -png`). `generar_planilla_pdf.py` es el formato anterior: usalo solo si el usuario lo pide.
4. **Subir.** Buscá si ya existe ese nombre en la carpeta "Pagos <obra>" (`parentId = ...`) para no duplicar; `create_file` con `contentMimeType: "application/pdf"`, `disableConversionToGoogleType: true`, `base64Content` = `sha256:<hex>:<ruta>`.

## 3. Recibos para firmar, por obra

1. Leé `'Recibos M.O.'!A3:F40`: B3 proyecto, B4 ubicación (puede estar vacía), B5 obra (nombre de archivo), B6 carpeta de recibos; desde la fila 9: M.O. (igual que en Datos Pagos), apellido y nombre, concepto, rubro para el archivo, hace recibo (Sí/No), lleva "Mes a pagar" (Sí/No).
2. Agrupá los pagos de la semana por M.O. y sumá. Recibo solo si tiene apellido y nombre y "Hace recibo" = Sí. Sin datos: no inventes, avisá.
3. Si "Lleva Mes a pagar" = Sí (alquileres: baño químico), sacá los meses de Observaciones ("Alquiler mes de Septiembre y Octubre" → "SEPTIEMBRE – OCTUBRE").
4. **Recibo (formato ZH Construcciones, desde el 25/11/2026).** `recibo.json` = `{"obra", "proyecto", "ubicacion", "nombre", "concepto", "rubro_archivo", "fecha_pago": "DD/MM/AAAA", "monto", "mes_a_pagar"?, "forma_pago", "observaciones", "numero"}`:
   - `forma_pago`: columna F de Datos Pagos sin el salto de línea ("Transferencia marcelo.239", "Efectivo").
   - `observaciones`: columna E de Datos Pagos. Si el M.O. cobró varias filas en la semana, unílas con " · ".
   - `numero`: `<prefijo_recibo de la obra>-<AAAAMMDD de la fecha de pago>-<NN>`, NN = orden del recibo dentro de esa obra y semana (01, 02...). Prefijos en `config/obras.json` (DUP, CER, GAR, OFI, YAN, PIL, FRA).
   ```bash
   python3 -I <skill>/scripts/generar_recibo_zh.py recibo.json recibo.pdf
   ```
   Una A4 con dos copias completas e iguales (arriba "Copia para el obrero", abajo "Copia para ZH Construcciones") y línea de corte; cada copia lleva fecha, proyecto, apellido y nombre, concepto, ubicación / mes a pagar / forma de pago, el bloque OBSERVACIONES, el monto en letras y números, y firma + aclaración y DNI. Nombre: `PAGO VIERNES 20.11.2026 (1.200.000) ALBAÑIL - Galpon Yanussi.pdf`. `generar_recibo_pdf.py` (encabezado Zuppa Hermanos, texto rojo) es el formato anterior: usalo solo si el usuario lo pide.
5. Mirá la imagen y subilo a la carpeta de recibos de la obra, sin duplicar nombres.

## 4. ICC Córdoba

```bash
python3 -I <skill>/scripts/icc_cordoba.py --desde <último mes cargado, 1/M/AAAA>
```
Agregá las filas nuevas debajo de la última de `'ICC Córdoba'!A:B` **en cada planilla de obra** (no en C: es ARRAYFORMULA). Lista vacía = no hay dato nuevo. No inventes índices.

## 5. Presupuesto vs pagado (por obra)

Método del usuario: `saldo al cierre de M = (saldo de M-1 − pagos de M) × (1 + variación ICC de M-1)`, desde el "Mes de inicio del ajuste" (amarillo) de cada contratista; variación redondeada a un decimal salvo que B5 diga No. La hoja recalcula sola: leé `'Presupuesto vs Pagado'!A1:Z73` y respondé con esos números. Vigilar: pagos a contratistas sin presupuesto, más de 28 contratistas o 24 meses, nombres repetidos o escritos distinto.

## 6. Actualizar la planilla central "Control de Obras"

Después de procesar las obras (o cuando pidan el control/tablero):
1. Exportá cada planilla de obra en curso: `download_file_content` con `exportMimeType` xlsx; copiá cada una a `exp/<codigo>.xlsx`.
2. ```bash
   python3 -I <skill>/scripts/consolidar.py --obras <skill>/config/obras.json --exportados exp --salida control.xlsx --json control.json
   ```
3. En la central: `batch_clear_values` de `Pagos!A2:K`, `'Saldos M.O.'!A2:I` y `Alertas!A2:C`, y `update_values` con `pagos`, `saldos` y `alertas` del JSON (en tandas de ~150 filas). Actualizá `Resumen!A2` (`actualizado`), `Resumen!B3` (`semana`) y `Resumen!D3` (`mes`). Resumen y Obras son fórmulas: no las reescribas.
4. Verificá `Resumen!A5:L15`: el "Pagado semana" de cada obra tiene que coincidir con el total de su planilla semanal.

## 6b. PDF único de la semana (para el contador)

Cada semana, además de las boletas individuales (que **se quedan** en la carpeta "Pagos <obra>" de cada obra), se arma un PDF que junta las boletas de todas las obras con pagos esa semana. El usuario se lo manda por WhatsApp al contador, Gustavo Martino ("Tato"), que prepara los pagos del viernes.

1. Cuando estén las boletas de la semana de todas las obras en curso (paso 2), bajalas de cada carpeta "Pagos <obra>" (`download_file_content`) en el orden del registro de obras. Las obras sin pagos esa semana no van.
2. Unilas en un solo PDF, una boleta por página (`pypdf`: `PdfWriter().append(...)`). Nombre: `Pagos semana DD-MM-AA - Total $X.pdf` (total de todas las obras, con puntos de miles; p. ej. `Pagos semana 27-11-26 - Total $8.000.000.pdf`).
3. Subilo a la carpeta **ZH → ZH00 -ARQUITECTURA → Pagos de Obras** (`carpeta_pdf_unico` en `config/obras.json`), sin duplicar nombres.
4. Si después cambia un pago de esa semana: regenerá la boleta individual (paso 7), rearmá el PDF único con el total nuevo, subilo y mandá el anterior a la papelera.
5. Respondé con el link y recordale cómo mandarlo desde el celular: app de Drive → ⋮ → Enviar una copia → WhatsApp → Tato, con el mensaje "Hola Tato, ahi van los pagos de esta semana". No hay conector de WhatsApp: el envío lo hace el usuario.

## 7. Forma de trabajo: a pedido, sin fecha fija

El usuario paga los miércoles a la tarde. Entre el lunes y el jueves pasa los pagos (dictados o cargados por él en Datos Pagos) cuando los tiene. Cada vez que lo hace, en el momento: cargá lo dictado (paso 1), generá o completá la planilla semanal y su PDF (paso 2) y los recibos (paso 3) de esa semana, actualizá la central (paso 6) y armá o rearmá el PDF único de la semana (paso 6b). No hay tarea programada.

Si llegan pagos nuevos de una semana que ya tiene bloque y PDF: agregá las filas al bloque, corregí el total, regenerá el PDF y, como el nombre cambia por el monto, mandá el PDF viejo a la papelera (no borrar definitivo) y subí el nuevo. Los recibos de un M.O. cuyo monto cambió se regeneran igual. Si el usuario corrige un pago ya procesado (p. ej. cambia el M.O.), corregilo en Datos Pagos, en el bloque semanal y en la central, regenerá el PDF y mandá a la papelera los recibos que ya no correspondan.

## Qué no hacer

- No modifiques datos que cargó el usuario en Datos Pagos ni Presupuestos M.O., salvo pedido (cargar pagos nuevos sí).
- No borres PDF de las carpetas salvo para reemplazar uno que se regenera (y solo a la papelera); no corrijas nombres viejos con errores ("60-11-26", "30-10-29").
- No toques los Excel originales, ni las pestañas "Reporte", "Tareas", "%M.O.", "%Electicista", "Limpieza de terreno".
- "Recibos M.O." la completa el usuario; podés agregar M.O. nuevos con los datos que él te dé.

## Resumen al terminar

Por obra, pocas líneas: semana y total, links a la planilla semanal y a los recibos; después el total de todas las obras con el link al PDF único de la semana, meses de ICC agregados y alertas de la pestaña Alertas que sean nuevas (pagos sin fecha de pago, fechas mal cargadas, nombres que no coinciden, contratistas > 90% o con saldo negativo, recibos sin datos).
