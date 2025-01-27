COLS_NUMERICAS_X_CONCEP = ['Cantidad','Precio','Descuento','Importe','TC','TCUsuario','Base IVA 16% Traslado','IVA 16% Traslado','Base IVA 0% Traslado','IVA 0% Traslado']
COLS_NUMERICAS_FACTURAS = ['SubTotal','Base IVA 16', 'Base IVA 8', 'Base IVA 0','IVA','Total','Tipo Cambio']
COLS = {
    'facturas_x_concepto':['UUID']+COLS_NUMERICAS_X_CONCEP,
    'facturas':['UUID', 'Estatus','Moneda']+COLS_NUMERICAS_FACTURAS,
    'consecutivo_facturacion':['Factura','ID de factura oficial','Estado','Nombre Adicional II','Moneda transaccional para valor neto','Tipo de cambio','Imp. Aereo','Valor neto (moneda transaccional)','Total calculado'],
    'cobros':['Documento','Cliente', 'Fecha Cobro','TC','Moneda','Cobros','Cobros MXN'],
}