import pandas as pd
import numpy as np
from config import COLS_NUMERICAS_X_CONCEP, COLS_NUMERICAS_FACTURAS, COLS

def generar_reporte(
        facturas: pd.DataFrame,
        facturas_x_concepto: pd.DataFrame,
        consecutivo_facturacion: pd.DataFrame,
        cobros: pd.DataFrame,
        ) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Genera un reporte de desglose de IVA de facturas cobradas,
    así como un resumen mensual de IVA cobrado.
    """
    facturas_x_concepto[COLS_NUMERICAS_X_CONCEP] = facturas_x_concepto[COLS_NUMERICAS_X_CONCEP].apply(pd.to_numeric, errors='coerce')
    facturas_x_concepto[COLS_NUMERICAS_X_CONCEP] = facturas_x_concepto[COLS_NUMERICAS_X_CONCEP].fillna(0)
    facturas[COLS_NUMERICAS_FACTURAS] = facturas[COLS_NUMERICAS_FACTURAS].apply(pd.to_numeric, errors='coerce')
    facturas[COLS_NUMERICAS_FACTURAS] = facturas[COLS_NUMERICAS_FACTURAS].fillna(0)

    # UUID a mayusculas
    facturas_x_concepto['UUID'] = facturas_x_concepto['UUID'].str.upper()
    facturas['UUID'] = facturas['UUID'].str.upper()
    consecutivo_facturacion['ID de factura oficial'] = consecutivo_facturacion['ID de factura oficial'].str.upper()

    # %% [markdown]
    # ## Extracción de los cobros

    # %%
    facturas_x_concepto = facturas_x_concepto[COLS['facturas_x_concepto']]
    facturas = facturas[COLS['facturas']]
    consecutivo_facturacion = consecutivo_facturacion[COLS['consecutivo_facturacion']]
    cobros = cobros[COLS['cobros']]

    # %%
    # Cruzamos los cobros con el consecutivo de facturación (Documento x Factura)
    cobros = cobros.merge(consecutivo_facturacion, how='left', left_on='Documento', right_on='Factura')
    # quitamos los de estado 'Cancelado'
    cobros = cobros[cobros['Estado'] != 'Cancelado']
    # calculamos la porción de cobro respecto al total de la factura en moneda original
    cobros['% Cobro'] = (-1)*cobros['Cobros'] / cobros['Total calculado']
    # renombramos columnas
    cobros.rename(columns={
        'ID de factura oficial':'UUID',
        'TC':'TC Cobro',
        'Tipo de cambio':'TC Fact',
        'Total calculado':'Total',
        'Moneda transaccional para valor neto':'Moneda Fact',
        'Moneda':'Moneda Cobro',
        'Estado':'Estado Fact',
        'Valor neto (moneda transaccional)': 'Valor neto total',
    }, inplace=True)
    # tipos de cambio en "Peso mexicano" a 1
    cobros['TC Fact'] = cobros[['TC Fact','Moneda Fact']].apply(lambda x: 1 if x['Moneda Fact'] == 'Peso mexicano' else x['TC Fact'], axis=1)
    cobros['TC Cobro'] = cobros[['TC Cobro','Moneda Cobro']].apply(lambda x: 1 if x['Moneda Cobro'] == 'Peso mexicano' else x['TC Cobro'], axis=1)
    facturas['Tipo Cambio'] = facturas[['Tipo Cambio','Moneda']].apply(lambda x: 1 if x['Moneda'] == 'MXN' else x['Tipo Cambio'], axis=1)

    # calculamos el valor neto cobrado en moneda original y con los tipos de cambio
    cobros['Valor neto cobrado'] = cobros['% Cobro'] * cobros['Valor neto total']
    cobros['Valor neto cobrado (TC Fact)'] = cobros['Valor neto cobrado'] * cobros['TC Fact']
    cobros['Valor neto cobrado (TC Cobro)'] = cobros['Valor neto cobrado'] * cobros['TC Cobro']

    # %%
    # validaciones
    print('No.  de factura duplicados en consecutivo de facturación:',len(consecutivo_facturacion)-len(consecutivo_facturacion.drop_duplicates(subset='Factura')))
    print('Cobros sin factura:',cobros['Factura'].isna().sum())
    print('Cobros donde el cliente no coincide con el de la factura:',cobros[cobros['Cliente'] != cobros['Nombre Adicional II']].shape[0])
    print('Cobros sin TC:',cobros['TC Cobro'].isna().sum())
    print('Cobros sin Cobro:',cobros['Cobros'].isna().sum())
    print('Cobros negativos:',cobros[cobros['% Cobro'] < 0].shape[0])

    # %% [markdown]
    # ## Procesamiento de facturas del SAT

    # %%
    # Obtenemos el importe total que cuenta con IVA 16% en cada factura
    suma_con_base16iva = facturas_x_concepto[facturas_x_concepto['Base IVA 16% Traslado']>0].groupby('UUID')[['Importe']].sum().reset_index()
    # aquellos con base 16% cero o null, se les asigna cero
    suma_con_base16iva = pd.concat([suma_con_base16iva,facturas_x_concepto[~facturas_x_concepto['UUID'].isin(suma_con_base16iva['UUID'])].drop_duplicates(subset='UUID')[['UUID']].assign(Importe=0)])
    suma_con_base16iva.rename(columns={'Importe':'Suma conceptos con IVA (total moneda original)'}, inplace=True)

    # %% [markdown]
    # ## Cruce con facturas del SAT

    # %% [markdown]
    # ### Bases

    # %%
    # en cobros, Suma conceptos con IVA (TC cobro) es la suma anterior, multiplicada por el tipo de cambio del cobro y el porcentaje de cobro
    cobros = cobros.merge(suma_con_base16iva, how='left', on='UUID')
    # si no se encontró la factura, se agrega observación
    cobros['Observación'] = cobros['Suma conceptos con IVA (total moneda original)'].apply(lambda x: 'No se encontró la factura en reporte por conceptos.' if np.isnan(x) else '')
    # rellenamos con ceros
    cobros['Suma conceptos con IVA (total moneda original)'] = cobros['Suma conceptos con IVA (total moneda original)'].fillna(0)
    cobros['Suma conceptos con IVA (TC cobro)'] = cobros['Suma conceptos con IVA (total moneda original)'] * cobros['TC Cobro'] * cobros['% Cobro']
    # extraemos el tipo de cambio origen de la factura
    cobros = cobros.merge(facturas[['UUID','Tipo Cambio',]], how='left', on='UUID')
    cobros.rename(columns={'Tipo Cambio':f'TC Origen'}, inplace=True)
    # si no se encontró la factura, se agrega observación
    cobros['Observación'] = cobros['Observación'] + cobros['TC Origen'].apply(lambda x: f'No se encontró la factura en reporte de facturas.' if np.isnan(x) else '')
    print('Cobros sin TC Origen:',cobros['TC Origen'].isna().sum())
    # Rellenamos con 1
    cobros['TC Origen'] = cobros['TC Origen'].fillna(1)
    # extraemos todas las bases de IVA, pero ajustando el tipo de cambio y el porcentaje de cobro
    for tasa in [16,8,0]:
        cobros = cobros.merge(facturas[['UUID',f'Base IVA {tasa}',]], how='left', on='UUID')
        cobros.rename(columns={f'Base IVA {tasa}':f'Base IVA {tasa} (MXN, TC Cobro)'}, inplace=True)
        # calculamos la base en TC cobro proporcional al cobro
        cobros[f'Base IVA {tasa} (MXN, TC Cobro)'] = cobros[f'Base IVA {tasa} (MXN, TC Cobro)'].fillna(0)
        cobros[f'Base IVA {tasa} (MXN, TC Cobro)'] = cobros[f'Base IVA {tasa} (MXN, TC Cobro)'] * cobros['TC Cobro'] * cobros['% Cobro']/cobros['TC Origen']
    # validaciones
    print('No encontradas en reporte de conceptos:',cobros[cobros['Observación'].str.contains('No se encontró la factura en reporte por conceptos.')].shape[0])
    print('No encontradas en reporte de facturas:',cobros[cobros['Observación'].str.contains('No se encontró la factura en reporte de facturas.')].shape[0])
    print('Cobros sin Base IVA 16 (MXN, TC Cobro):',cobros['Base IVA 16 (MXN, TC Cobro)'].isna().sum())
    print('Cobros sin Base IVA 8 (MXN, TC Cobro):',cobros['Base IVA 8 (MXN, TC Cobro)'].isna().sum())
    print('Cobros sin Base IVA 0 (MXN, TC Cobro):',cobros['Base IVA 0 (MXN, TC Cobro)'].isna().sum())   

    # %% [markdown]
    # ### Impuesto aéreo

    # %%
    cobros['% Base IVA 16'] = cobros.apply(lambda x: x['Base IVA 16 (MXN, TC Cobro)']/x['Suma conceptos con IVA (TC cobro)'] if x['Suma conceptos con IVA (TC cobro)'] != 0 else 0, axis=1)
    # validar que solo aparezcan los valores 0, 1 o 0.25
    print('Valores distintos de 0, 1 o 0.25 en % Base IVA 16?:',cobros['% Base IVA 16'].unique())

    # calculamos la base para el impuesto aéreo
    # es la base 16 cuando Imp AE no es cero, y cero en otro caso
    cobros['Base IVA ImpAE (MXN, TC Cobro)'] = cobros.apply(lambda x: x['Base IVA 16 (MXN, TC Cobro)'] if x['Imp. Aereo'] != 0 else 0, axis=1)
    # validamos que la base IVA ImpAE sea no nula cuando % Base IVA 16 sea 0.25
    print('Valores iguales a 0 en Base IVA ImpAE cuando % Base IVA 16 es 0.25?:',cobros[(cobros['% Base IVA 16'] == 0.25) & (cobros['Base IVA ImpAE (MXN, TC Cobro)'] == 0)].shape[0])
    cobros['Base IVA 16 (menos Base Imp AE) (MXN,TC Cobro)'] = cobros['Base IVA 16 (MXN, TC Cobro)'] - cobros['Base IVA ImpAE (MXN, TC Cobro)']

    # %%
    # aregamos el total de las bases (iva 16 menos aereo, aereo, iva 8, iva 0)
    cobros['Total Bases (MXN, TC Cobro)'] = cobros['Base IVA 16 (menos Base Imp AE) (MXN,TC Cobro)'] + cobros['Base IVA ImpAE (MXN, TC Cobro)'] + cobros['Base IVA 8 (MXN, TC Cobro)'] + cobros['Base IVA 0 (MXN, TC Cobro)']
    # comparamos el total de bases con el valor neto cobrado (TC cobro y TC fact)
    cobros['Diferencia bases vs valor neto cobrado (TC Cobro)'] = cobros['Total Bases (MXN, TC Cobro)'] - cobros['Valor neto cobrado (TC Cobro)']
    cobros['Diferencia bases vs valor neto cobrado (TC Fact)'] = cobros['Total Bases (MXN, TC Cobro)'] - cobros['Valor neto cobrado (TC Fact)']

    # %% [markdown]
    # ### Traslados

    # %%
    # calculamos todos los traslados
    for tasa in [16,8,0]:
        cobros[f'IVA {tasa} (MXN, TC Cobro)'] = cobros[f'Base IVA {tasa} (MXN, TC Cobro)'] * tasa/100
    cobros['IVA ImpAE (MXN, TC Cobro)'] = cobros['Base IVA ImpAE (MXN, TC Cobro)'] * 16/100
    cobros['IVA 16 (menos Imp AE) (MXN, TC Cobro)'] = cobros['Base IVA 16 (menos Base Imp AE) (MXN,TC Cobro)'] * 16/100

    # %% [markdown]
    # ## Resumen

    # %%
    cols_resumen = ['Cobros MXN','Suma conceptos con IVA (TC cobro)','Base IVA 16 (MXN, TC Cobro)','Base IVA 8 (MXN, TC Cobro)',
                    'Base IVA 0 (MXN, TC Cobro)','Base IVA ImpAE (MXN, TC Cobro)','Base IVA 16 (menos Base Imp AE) (MXN,TC Cobro)',
                    'IVA 16 (MXN, TC Cobro)','IVA 8 (MXN, TC Cobro)','IVA 0 (MXN, TC Cobro)','IVA ImpAE (MXN, TC Cobro)',
                    'IVA 16 (menos Imp AE) (MXN, TC Cobro)', 'Total Bases (MXN, TC Cobro)','Valor neto cobrado (TC Cobro)', 'Valor neto cobrado (TC Fact)',
                    'Diferencia bases vs valor neto cobrado (TC Cobro)', 'Diferencia bases vs valor neto cobrado (TC Fact)']
    # Generamos el resumen por fecha de cobro, agrupando por mes
    cobros['Mes'] = cobros['Fecha Cobro'].dt.to_period('M')
    resumen = cobros.groupby('Mes')[cols_resumen].sum().transpose()

    return cobros, resumen
