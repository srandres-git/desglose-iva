import altair as alt
import pandas as pd
import numpy as np
import streamlit as st
from determinacion_iva import generar_reporte

# Show the page title and description.
st.set_page_config(page_title="Desglose de IVA",)
st.title("Desglose de IVA")
st.write(
    """
    Desglose de IVA de facturas cobradas. 
    Cruce de reportes de cobros, facturas emitidas y facturas registradas.
    """
)
# create an excel file upload widget
upload_file = st.file_uploader("Cargar reporte", type=["xlsx"])

# check if the file is uploaded
if upload_file is not None:
    # read the excel file
    try:
        facturas_x_concepto = pd.read_excel(upload_file, sheet_name="FacturasConceptos")
        facturas = pd.read_excel(upload_file, sheet_name="Facturas")
        consecutivo_facturacion = pd.read_excel(upload_file, sheet_name="ConsecutivoFacturacion")
        cobros = pd.read_excel(upload_file, sheet_name="Cobros")
    except Exception as e:
        st.write("Asegúrate de que el archivo contenga las hojas: Facturas, FacturasConceptos, ConsecutivoFacturacion y Cobros")
        st.write(f"Error: {e}")

    # Load the data from a CSV. We're caching this so it doesn't reload every time the app
    # reruns (e.g. if the user interacts with the widgets).
    @st.cache
    def load_data():
        return generar_reporte(facturas_x_concepto, facturas, consecutivo_facturacion, cobros)

    cobros, resumen = load_data()

    # # Show a multiselect widget with the genres using `st.multiselect`.
    # genres = st.multiselect(
    #     "Genres",
    #     df.genre.unique(),
    #     ["Action", "Adventure", "Biography", "Comedy", "Drama", "Horror"],
    # )

    # # Show a slider widget with the years using `st.slider`.
    # years = st.slider("Years", 1986, 2006, (2000, 2016))

    # # Filter the dataframe based on the widget input and reshape it.
    # df_filtered = df[(df["genre"].isin(genres)) & (df["year"].between(years[0], years[1]))]
    # df_reshaped = df_filtered.pivot_table(
    #     index="year", columns="genre", values="gross", aggfunc="sum", fill_value=0
    # )
    # df_reshaped = df_reshaped.sort_values(by="year", ascending=False)


    # Display the data as a table using `st.dataframe`.
    st.dataframe(
        resumen,
        use_container_width=True,
        # column_config={"year": st.column_config.TextColumn("Year")},
    )

    # # Display the data as an Altair chart using `st.altair_chart`.
    # df_chart = pd.melt(
    #     df_reshaped.reset_index(), id_vars="year", var_name="genre", value_name="gross"
    # )
    # chart = (
    #     alt.Chart(df_chart)
    #     .mark_line()
    #     .encode(
    #         x=alt.X("year:N", title="Year"),
    #         y=alt.Y("gross:Q", title="Gross earnings ($)"),
    #         color="genre:N",
    #     )
    #     .properties(height=320)
    # )
    # st.altair_chart(chart, use_container_width=True)
