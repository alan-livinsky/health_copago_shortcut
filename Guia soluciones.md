# Guia soluciones

## Caso de uso 1: abrir desde un turno un atajo ya existente de otro modulo

### Necesidad

Desde `gnuhealth.appointment` se necesitaba ejecutar rapido el acceso a
`Health Services` del paciente asociado al turno, sin obligar al usuario a:

- abrir la ficha del paciente
- usar el relacionado "Services"
- volver a buscar el documento correcto

### Solucion / patron

Patron: `Wizard + StateAction + pyson_domain`

Se creo un wizard de accion sobre `gnuhealth.appointment` que:

1. toma el `active_id` del turno
2. valida que haya exactamente un turno seleccionado
3. valida que el turno tenga paciente
4. devuelve una `act_window` del modelo `gnuhealth.health_service`
5. aplica un `pyson_domain` filtrando por el paciente del turno

### Cuando usar este patron

Usar este patron cuando:

- ya existe una pantalla funcional en otro modulo
- no hace falta crear datos nuevos
- solo se necesita abrir esa pantalla ya filtrada por el contexto actual

### Ventaja

Evita duplicar logica de negocio. El nuevo modulo solo navega mas rapido hacia
una funcion existente.


## Caso de uso 2: generar un documento intermedio y luego abrir el comprobante final

### Necesidad

Desde un turno se queria crear un copago en menos pasos. El flujo manual era:

1. abrir servicios del paciente
2. crear un servicio
3. completar encabezado
4. completar linea de servicio
5. generar factura
6. abrir la factura resultante

### Solucion / patron

Patron: `Wizard + creacion programatica + apertura del resultado`

Se implemento un wizard que:

1. toma el turno activo
2. obtiene el paciente
3. busca el producto de copago relacionado con `md-1`
4. crea un `gnuhealth.health_service`
5. crea una sola linea de servicio invoiceable
6. genera la factura a partir de ese servicio
7. marca el servicio como `invoiced`
8. abre la factura creada

### Datos que se cargan automaticamente

- paciente: paciente del turno
- fecha del servicio: fecha actual
- descripcion: `copago`
- institucion: institucion por defecto
- company: company por defecto del contexto
- factura a: party del paciente
- linea de servicio:
  - producto: el que coincide con `md-1`
  - cantidad: `1`
  - desde: fecha actual
  - hasta: fecha actual
  - invoice: verdadero

### Cuando usar este patron

Usar este patron cuando:

- el usuario repite siempre la misma carga administrativa
- los datos salen de reglas claras del contexto
- el resultado esperado es abrir un registro final ya generado

### Ventaja

Reduce pasos manuales y baja la probabilidad de errores de carga.


## Caso de uso 3: generar un documento y disparar directamente la descarga o impresion

### Necesidad

Se queria una version todavia mas rapida que no solo cree el copago y la
factura, sino que ademas dispare directamente la impresion / descarga del
comprobante.

### Solucion / patron

Patron: `Wizard + StateReport`

Se reutilizo la misma logica de generacion del copago y luego se devolvio un
`StateReport` en vez de una ventana.

Punto importante: en Tryton el `StateReport` no usa el XML id del action
report, sino el `report_name`.

En este caso:

- esto fallo: `StateReport('account_invoice.report_invoice')`
- esto funciono: `StateReport('account.invoice')`

### Regla practica

Si un reporte no aparece con `StateReport`, revisar en el modulo origen:

- registro `ir.action.report`
- valor de `<field name="report_name">`

Ese valor de `report_name` es el que normalmente se debe usar en
`StateReport(...)`.

### Cuando usar este patron

Usar este patron cuando:

- el paso final real del usuario es imprimir o descargar
- abrir primero el formulario solo agrega friccion
- ya existe un reporte funcional en otro modulo

### Ventaja

Convierte un flujo administrativo largo en una sola accion orientada al
resultado final.


## Caso de uso 4: resolver dudas entre XML id y report_name en Tryton

### Necesidad

Aparecio un error:

`AssertionError: account_invoice.report_invoice not found`

Esto podia confundir porque el modulo de invoice si tenia un registro
`ir.action.report` con id `report_invoice`.

### Solucion / patron

Patron: distinguir entre:

- XML id del action: por ejemplo `account_invoice.report_invoice`
- report name tecnico: por ejemplo `account.invoice`

Para `StateAction` o referencias XML se usa normalmente el action / XML id.
Para `StateReport` se debe usar el `report_name`.

### Regla rapida

- si voy a abrir una ventana: pensar en `StateAction`
- si voy a disparar un reporte: pensar en `StateReport`
- si uso `StateReport`, buscar `report_name`


## Caso de uso 5: agregar funciones rapidas sin tocar en exceso la vista original

### Necesidad

La idea inicial era agregar botones en la lista de turnos, pero podia no ser
viable o conveniente segun la vista cliente.

### Solucion / patron

Patron: `form_action` en barra superior

Se agregaron acciones sobre `gnuhealth.appointment` usando `ir.action.keyword`
con keyword `form_action`. Esto permite:

- mantener bajo el impacto visual
- no depender de que la tree view soporte bien los botones deseados
- ofrecer acciones rapidas reutilizables desde el contexto del registro

### Cuando usar este patron

Usar este patron cuando:

- el cliente ya resuelve bien acciones en la barra superior
- no vale la pena modificar mucho la tree view
- el flujo necesita contexto del registro activo

### Ventaja

Es una extension de bajo riesgo y facil de mantener.


## Resumen de patrones reutilizables

### Abrir un atajo ya existente

`Wizard + StateAction + pyson_domain`

### Crear un documento automaticamente y abrirlo

`Wizard + logica de negocio + act_window final`

### Crear un documento y descargar/imprimir directo

`Wizard + logica de negocio + StateReport`

### Elegir correctamente el identificador del reporte

Para `StateReport`, usar `report_name`, no el XML id.

