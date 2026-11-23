# ZH Construcciones — Workspace de Notion (resumen técnico para Claude Code)

Estado al 23/11/2026. Todo fue creado con el conector MCP de Notion. El espacio es privado (página borrador del usuario).

## Contexto
- Usuario: arquitecto, ZH Construcciones (Córdoba, Argentina). Responder en español rioplatense.
- Fuente actual de pagos de mano de obra: Google Sheet **"Control de Obras - Pagos Mano de Obra"**
  - ID: `1Z4InsHdZ0IJ41CWlNJe3d09XFNmIAkw5a2MsnhKJmfQ`
  - Pestañas: `Resumen`, `Pagos`, `Saldos M.O.`, `Alertas`, `Obras`
  - `Obras` tiene código, nombre, estado, ID de la planilla de cada obra, carpetas e inicio.
  - `Saldos M.O.` tiene, por obra y contratista: presupuesto original, mes de inicio del ajuste, pagado, ajustes ICC, saldo, presupuesto actualizado y % ejecutado.
- La planilla sigue siendo la fuente principal de los pagos semanales. Notion es el tablero de gestión.

## Página raíz
- **ZH Construcciones | Workspace** — página `421e5621-96e1-8101-b64e-f627775e9c38`
- Contiene las bases originales (no borrarlas) y un panel con vistas enlazadas, en este orden:
  1. 🏗️ Obras en curso (galería de Obras, filtro Estado = "En obra", portada = propiedad "Portada")
  2. ✅ Tareas pendientes (lista de Tareas, Estado ≠ Hecha, orden por Fecha)
  3. ⏳ Pagos pendientes (tabla de Finanzas, Pagado = false)
  4. 📅 Mi semana (tabla de Tareas, Estado ≠ Hecha y Fecha ≤ dentro de una semana)
  5. 🦺 Próximas visitas de obra (lista de Visitas, Fecha ≥ hoy)
  6. 💰 Resumen financiero (gráfico de columnas: suma de Monto por Fecha, apilado por Tipo)

## Bases de datos (database ID → data source ID)

### Obras (central)
- DB `421e562196e18143bf4eed9ef403138d` → DS `collection://421e5621-96e1-8177-95d8-000b66f8aed6`
- Propiedades:
  - Obra (title)
  - Cliente (relación ↔ Clientes.Obras)
  - Estado (status): Presupuestando, Proyecto, En obra, Pausada, Terminada, Cancelada
  - Tipo (select): Vivienda, Duplex, Quincho, Garaje, Oficinas, Galpón, Remodelación, Otro
  - Etapa (select): Anteproyecto, Proyecto ejecutivo, Trámites municipales, Fundaciones, Estructura, Mampostería, Instalaciones, Terminaciones, Entrega
  - Dirección (texto), Inicio (fecha), Fin estimado (fecha), Superficie m2 (número)
  - Presupuesto (número, peso argentino), Portada (archivos), Notas, Responsable (personas)
  - Relaciones: Tareas, Documentos, Movimientos (→ Finanzas), Visitas
  - Rollups: Tareas hechas = suma de Tareas.Hecha; Tareas total = conteo de Tareas; Cobrado = suma de Movimientos."Ingreso $"; Gastado = suma de Movimientos."Egreso $"
  - Fórmulas:
    - Avance = `if(prop("Tareas total") > 0, round(prop("Tareas hechas") / prop("Tareas total") * 100) / 100, 0)`
    - Saldo a cobrar = `prop("Presupuesto") - prop("Cobrado")`
    - Resultado = `prop("Cobrado") - prop("Gastado")`
    - % cobrado = `if(prop("Presupuesto") > 0, round(prop("Cobrado") / prop("Presupuesto") * 100) / 100, 0)`
    - % gastado = lo mismo, con Gastado
- Diseño de página:
  - Arriba: portada, título con Estado, Etapa, Avance, Cliente y Responsable fijados.
  - Debajo: vistas de las relaciones Tareas, Visitas, Movimientos y Documentos.
  - Barra lateral con secciones: Datos de la obra / Finanzas / Otros.
- Vistas: Por estado (tablero), Cronograma (línea de tiempo Inicio → Fin estimado), Finanzas por obra (tabla).
- Cada una de las 7 obras tiene en su contenido un checklist "📋 Documentación y trámites".

Páginas de obra (estado En obra; inicio):

| Obra | Page ID | Inicio |
|---|---|---|
| Duplex Scorza | `421e5621-96e1-816e-8c65-c1c7a38b6fb6` | 2026-10-01 |
| Quincho Cervelli | `421e5621-96e1-81ca-89b1-ec826ba1fadf` | 2026-05-01 |
| Garaje Martino | `421e5621-96e1-8178-8b89-d3aecaef06e5` | 2026-05-01 |
| Oficinas Martino | `421e5621-96e1-81ae-b67a-dd4abd0c6fff` | 2026-04-01 |
| Galpón Yanussi | `421e5621-96e1-8182-9027-eb4c69e00c57` | 2026-09-01 |
| Vivienda Pilla | `421e5621-96e1-81b9-ac56-ff285b72809e` | 2025-05-01 |
| Vivienda Fraresso-Gallo | `421e5621-96e1-811d-a521-f488016e9454` | 2026-06-01 |

### Clientes
- DB `421e562196e1814e9797f41492256abc` → DS `collection://421e5621-96e1-8163-9637-000bba98e018`
- Propiedades: Nombre, Teléfono, Email, CUIT/DNI, Dirección, Tipo (Particular/Empresa/Desarrollador), Estado (Prospecto/Activo/Finalizado), Notas, Obras (relación)
- Registros:

| Cliente | Page ID |
|---|---|
| Scorza | `421e5621-96e1-8180-9662-eb429d1b78a7` |
| Cervelli | `421e5621-96e1-8104-baee-cc47e3c0af96` |
| Martino | `421e5621-96e1-8114-ac55-fc1029ec74e2` |
| Yanussi | `421e5621-96e1-81a5-b063-cc82fbf016e6` |
| Pilla | `421e5621-96e1-8167-9326-e43aafde5a60` |
| Fraresso-Gallo | `421e5621-96e1-817b-9fe8-e305f2d05346` |

### Proveedores y Contratistas
- DB `421e562196e181948becdee34d71915e` → DS `collection://421e5621-96e1-810d-a334-000b253866cf`
- Propiedades:
  - Nombre
  - Rubro (multi-select): Albañilería, Electricidad, Sanitarios, Gas, Pintura, Herrería, Carpintería, Corralón/Materiales, Durlock, Otro
  - Tipo (Mano de obra / Proveedor de materiales / Profesional)
  - Contacto, Teléfono, Email, CUIT, Calificación (1 a 5 ⭐), Notas
  - Relaciones: Tareas, Movimientos, Visitas
- Registros:

| Nombre | Page ID |
|---|---|
| Alessandrini | `421e5621-96e1-81eb-8648-ff62fe640a0f` |
| Villalon | `421e5621-96e1-81b5-a34c-db5fe223817a` |
| Panelo | `421e5621-96e1-8180-b4a7-f1c7b173ea37` |
| Troilo | `421e5621-96e1-8128-ad18-cf3666ea3dd6` |
| Díaz | `421e5621-96e1-8194-a1e0-e18e698cfb0d` |
| Gonella | `421e5621-96e1-81bc-8a15-d31fdeaf1322` |
| Quiroga | `421e5621-96e1-8140-b81c-c2378254a5d5` |
| Papilla Rosas | `421e5621-96e1-8120-889e-eb59067c90ce` |
| Cejas Fernando (steel) | `421e5621-96e1-8163-9072-ef2d18066abe` |
| Boyero (montaje) | `421e5621-96e1-8138-ba05-c8f889d3185c` |
| Taborda (micropilotes) | `421e5621-96e1-81c8-a8e4-f8185e429c5c` |
| Trucco (nivelación) | `421e5621-96e1-81fb-9817-ebf4c8529510` |
| Prodesarrollo | `421e5621-96e1-81a5-a4e0-ed78b84c1456` |

### Tareas
- DB `421e562196e181f5b691dc1698dbf2e7` → DS `collection://421e5621-96e1-813f-9028-000b31c2998d`
- Propiedades:
  - Tarea, Obra (relación), Estado (status: Pendiente, En curso, Esperando, Hecha)
  - Prioridad (Alta/Media/Baja)
  - Tipo (Visita de obra, Compra, Trámite, Reunión cliente, Dibujo/Proyecto, Pago, Otro)
  - Fecha, Responsable, Contratista (relación), Notas
  - Hecha (fórmula) = `if(prop("Estado") == "Hecha", 1, 0)`
- Vistas: Tablero (agrupado por grupo de Estado), Calendario (por Fecha).
- Todavía no hay tareas cargadas.

### Documentos y Planos
- DB `421e562196e1811980ace521b3a56787` → DS `collection://421e5621-96e1-818c-8151-000b7cbc1a4d`
- Propiedades:
  - Documento, Obra (relación)
  - Tipo (Plano, Presupuesto, Contrato, Permiso municipal, Cómputo, Foto de obra, Factura, Otro)
  - Versión, Fecha, Archivo (archivos), Link (URL)
  - Estado (Borrador, En revisión, Aprobado, Reemplazado)
- Vacía.

### Finanzas (movimientos)
- DB `421e562196e18175a1e4d677b22030f1` → DS `collection://421e5621-96e1-81a8-af82-000b51897c27`
- Propiedades:
  - Concepto, Obra (relación ↔ Obras.Movimientos), Proveedor (relación ↔ Proveedores.Movimientos)
  - Tipo (Ingreso/Egreso)
  - Categoría (Cobro cliente, Honorarios, Mano de obra, Materiales, Servicios, Trámites, Otros)
  - Monto (peso argentino), Fecha, Medio de pago (Efectivo/Transferencia/Cheque)
  - Pagado (checkbox), Comprobante (archivos), Notas
  - Ingreso $ = `if(prop("Tipo") == "Ingreso", prop("Monto"), 0)`
  - Egreso $ = `if(prop("Tipo") == "Egreso", prop("Monto"), 0)`
- Vistas: Pendientes de pago, Por categoría, Compras (tablero: Categoría = Materiales, agrupado por Pagado), Balance mensual (gráfico).
- Las compras se registran acá con Categoría = Materiales, para que sumen al Gastado sin duplicar datos.
- Propiedad **ID planilla** (texto) = `"<Obra>#<Fila en Datos Pagos>"`, con el nombre de obra tal cual figura en la planilla (ej. `Galpon Yanussi#14`). Es la clave para no duplicar.
- Datos cargados (23/11/2026): **315 egresos, uno por cada pago** de la pestaña `Pagos`, del 30/05/2025 al 20/11/2026. Total $203.500.312.
  - Concepto = `"<M.O.> · <Tarea>"`; si la tarea es "Otros" o está vacía, se usa la primera línea de Observaciones.
  - Notas = Observaciones + "Forma de pago: …". Medio de pago se deduce de la forma de pago.
  - Categoría: contratistas → Mano de obra; Baño Químico y Obrador → Servicios; Prodesarrollo → Materiales. Los "Otros" se reparten por palabras clave (`categoria_otros` en el script): permisos, amojonamiento, planos y cálculo de estructura → Trámites; volquetes, fletes, obrador, limpieza/picado → Servicios; tierra, ladrillos, chapa, canaletas, placas, cables, nafta, pintura asfáltica → Materiales.
  - Los 38 acumulados al 19/11 que había antes se mandaron a la papelera de Notion (se pueden restaurar).
- Sincronización semanal: leer `Pagos!A2:K` y pasarlo por `scripts/pagos_a_notion.py` junto con los "ID planilla" ya cargados. El script devuelve solo las filas nuevas, listas para crear en Finanzas.

### Visitas de Obra
- DB `421e562196e18177a670cfd76a6c299b` → DS `collection://421e5621-96e1-811b-8e6b-000baba6ac11`
- Propiedades:
  - Visita, Obra (relación), Fecha
  - Motivo (Control de avance, Replanteo, Certificación, Reunión con cliente, Problema / Imprevisto, Entrega)
  - Contratistas presentes (relación), Observaciones, Pendientes, Fotos, Responsable
- Vista: Calendario de visitas.

## Pendientes y próximos pasos sugeridos para Code
1. ~~Sincronizar Sheets → Notion~~ Hecho el 23/11/2026 (ver Finanzas). Ese mismo día se unificaron los nombres en las planillas de obra ("Albañil Alessandrini", "Baño Químico", "Nivelación - Trucco", también en Presupuestos M.O. y Recibos M.O.), se separaron las celdas combinadas de Pilla fila 58 y se corrigió la ortografía de Datos Pagos, la planilla central y Notion. `Saldos M.O.` y Notion suman lo mismo: $203.500.312.
2. **Portadas / renders.** Subir imágenes a la propiedad "Portada" de cada obra con la API de File Upload de Notion. En Drive hay renders, por ejemplo "Garaje para Render *" (posiblemente Garaje Martino) y varios "rendair-image-to-render-*". Confirmar con el usuario a qué obra corresponde cada uno.
3. **Presupuestos y cobros de clientes.** No están en la planilla. Pedirlos al usuario y cargar Presupuesto en cada obra y los cobros como Ingreso.
4. **Gráficos.** "Balance mensual" y el gráfico del panel quedaron agrupados por día. Cambiar a mes, o pedirle al usuario que lo haga desde la interfaz.
5. **Lo que no se pudo vía MCP** (hacer a mano en Notion o verificar si la API lo permite):
   - Botones de carga rápida (+ Obra, + Tarea, + Visita, + Comprobante)
   - Panel en 2 columnas
   - Plantilla predeterminada de Obras con el checklist de documentación
6. Conceptos genéricos sin contratista asignado: Electricista, Plomero, Obrador, Baño químico, Otros, Carpintero.

## Reglas
- No borrar las bases originales: el panel usa vistas enlazadas a ellas.
- Montos en pesos argentinos.
- Antes de cambios masivos o destructivos, confirmar con el usuario.
