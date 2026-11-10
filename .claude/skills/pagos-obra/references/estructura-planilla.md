# Estructura de la planilla de pagos de obra

Modelo: "Pagos Manos de Obra - Duplex Scorza" (Google Sheets, locale es_ES).
Otra obra puede tener otro nombre de pestaña o columnas corridas: leé los encabezados antes de escribir y adaptá.

## Contenido

- [Datos Pagos](#datos-pagos-reporte-de-pagos)
- [Pagos <obra> (planillas semanales)](#pagos-obra-planillas-semanales)
- [Presupuestos M.O.](#presupuestos-mo)
- [Recibos M.O.](#recibos-mo)
- [Carpeta de recibos](#carpeta-de-recibos)
- [Presupuesto vs Pagado](#presupuesto-vs-pagado-análisis)
- [ICC Córdoba](#icc-córdoba)
- [Particularidades del locale](#particularidades-del-locale)

## Datos Pagos (reporte de pagos)

Filas 1 y 2: nombre de la obra y fecha de inicio ("Inicio Lunes 5/10/26"). Fila 3: encabezados. Datos desde la fila 4.

| Col | Encabezado | Contenido |
|---|---|---|
| A | Fecha pedido | fecha (número de serie, se ve D/M/AAAA) |
| B | (sin título) | fórmula `=TEXT(A4; "mmmm-yyy")` → "octubre-2026". Copiarla en filas nuevas. |
| C | M.O. | contratista; tiene que coincidir con el nombre en Presupuestos M.O. |
| D | Tarea | rubro (Replanteo y nivelación, Armaduras, Otros...) |
| E | Observaciones | descripción de la tarea |
| F | Forma de pago | "Transferencia \n<alias>" o "Efectivo" (el salto de línea es parte del texto) |
| G | A Pagar | monto, número con formato moneda |
| H | Fecha de pago | viernes en que se paga; agrupa la semana |
| I | (notas) | texto libre, por ejemplo "pago zh construcciones" |

Más abajo (filas ~49 en adelante) hay notas sueltas y un bloque viejo en J:K ("Pagos Comienzo oficinas"). No son pagos de la obra: G está vacía, así que los filtros por G numérico los excluyen. No los toques.

Errores conocidos en Duplex Scorza: el pago de Hugo Luján (fila 5) tiene fecha de pago 15/5/2026 en lugar de 15/10/2026.

## Pagos <obra> (planillas semanales)

Ejemplo de bloque (filas 19 a 21):

```
19 | Duplex Scorza - Pagos semana 06/11/2026            (A:E combinadas)
20 | Albañil Alessandrini | Armaduras | Corte de hierros... | Transferencia \nruben.alessa | 1400000
21 |                      |           |                    |                              | =+SUM(E20)
22 | (vacía)
```

- Título: fondo amarillo (#FFE598), negrita, centrado, borde grueso; A:E combinadas. Escribilo con apóstrofe adelante para que no se convierta en fecha.
- Filas de pago: A en gris (#D8D8D8) y negrita; C y D con ajuste de texto; E en formato moneda `_-"$"\ * #,##0.00_-`.
- Total: solo E, negrita, `=+SUM(E<primera>:E<última>)`.
- Una fila vacía entre bloques. Anchos de columna A:E: 116, 151, 179, 96, 105 px.
- La forma más segura de dar formato a un bloque nuevo es `copyPaste` con `PASTE_FORMAT` desde el bloque anterior (título → título, fila de pago → cada fila, total → total) y después `mergeCells` del título.
- Abajo de todo (fila ~70 en adelante) hay cálculos sueltos del usuario: no los muevas. Si un bloque nuevo los fuera a pisar, avisá antes.

## Presupuestos M.O.

Fila 2: encabezados (B "M.O", C "Presupuesto", D "Pagado", E "Saldo restante"). Contratistas desde B3. Solo algunos tienen presupuesto en C. G y H tienen cálculos auxiliares del usuario sin título. No es una pestaña para editar desde la skill.

## Recibos M.O.

Datos para los recibos (la completa el usuario; celdas amarillas). B3 proyecto ("D.G.D DESARROLLO / DUPLEX – SCORZA ANDRES"), B4 ubicación ("LOTEO SAN SEVERINO"), B5 obra para el nombre de archivo ("Duplex Scorza"), B6 id de la carpeta de recibos. Fila 8: encabezados. Desde la fila 9: A M.O. (igual que en Datos Pagos), B apellido y nombre, C concepto, D rubro para el nombre de archivo, E hace recibo (Sí/No).

Cargados al crearla: Albañil Alessandrini → ALESSANDRINI RUBEN / ALBAÑILERÍA / ALBAÑIL; Electricista → QUIROGA DAMIÁN / ELECTRICISTA / ELECTRICISTA; Otros → No. El resto de los contratistas quedó sin datos.

## Carpeta de recibos

"Pagos Semanales" (`1J3f5axqB7aUy160cwNzpVklmez3modTC`). Un PDF por mano de obra y por semana: `PAGO VIERNES 06.11.2026 (1.400.000) ALBAÑIL - Duplex Scorza.pdf`. Hoja A4 con dos copias del recibo: banner "RECIBO" + logo de la empresa (imagen de 567×89 pt), "FECHA: ____ DE 2026" en blanco, PROYECTO, UBICACIÓN, APELLIDO Y NOMBRE, CONCEPTO, "Recibí conforme la suma de pesos: <EN LETRAS> PESOS. Son: $ <monto>." y línea de "Firma y Aclaración". Texto en rojo puro, Montserrat 10 (etiquetas en negrita). Recibo de referencia: `1vyFBs0BliipPhacoy-su3XnjZGPE78aK`.

El 06/11/2026 hay un recibo del electricista por $180.000 que no está cargado en Datos Pagos.

## Presupuesto vs Pagado (análisis)

La crea `scripts/armar_analisis.py`. Todo son fórmulas salvo las celdas amarillas.

- B5: redondear la variación a un decimal (Sí/No). B6: último ICC publicado. B7: mes en curso (TODAY). B8: último mes ya ajustado.
- Filas 10 a 39, A:H: una fila por contratista (lee `Presupuestos M.O.`!B3:C30): presupuesto original, C mes de inicio del ajuste (input), pagado, ajustes por ICC acumulados (= saldo actual − (presupuesto − pagado)), saldo por pagar actual, presupuesto actualizado (pagado + saldo), % ejecutado.
- Filas 42 a 44, C:Z: meses (24 desde el inicio), variación aplicada (la del mes anterior, de 'ICC Córdoba'!C) y si el mes ya cerró y se ajustó.
- Filas 46 a 73, C:Z: saldo al cierre de cada mes por contratista: `(saldo anterior − pagos del mes) × (1 + variación si el mes se ajustó)`. Los meses futuros quedan vacíos.
- AB:AE desde la fila 11: detalle de pagos con FILTER sobre Datos Pagos (fecha de pago, o de pedido si falta; mes; M.O.; monto).

Valores al 10/11/2026 (Albañil Alessandrini, presupuesto $187.200.000, inicio oct-2026): octubre pagó $4.600.000 y cerró en (187.200.000 − 4.600.000) × 1,012 = $184.791.200; noviembre lleva $1.400.000 pagados, saldo $183.391.200 sin ajustar todavía.

## ICC Córdoba

Fila 4: encabezados. Desde la fila 5: A mes (1/M/AAAA), B índice nivel general. C (variación mensual) es una ARRAYFORMULA que arranca en C6: al agregar meses, escribí solo A:B.

## Particularidades del locale

- es_ES: los argumentos se separan con `;` y los decimales con `,`. Los nombres de función van en inglés (SUMIFS, XLOOKUP...). Los conectores devuelven y aceptan las fórmulas así.
- Las fechas escritas como texto "1/10/2026" se leen como día/mes/año.
- `get_values` devuelve lo que se ve: montos como " $  1.400.000,00 ". Para los números crudos, leé la grilla con `userEnteredValue`.
- La zona horaria de la planilla está en America/Los_Angeles; no importa para fechas sin hora.
