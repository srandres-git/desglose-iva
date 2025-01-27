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
# create multiple excel file uploaders
# if all the data is in the same file, the file gets very large
upload_facturas = st.file_uploader("Sube el archivo de facturas", type=["xlsx"])
upload_facturas_x_concepto = st.file_uploader("Sube el archivo de facturas por concepto", type=["xlsx"])
upload_consecutivo_facturacion = st.file_uploader("Sube el archivo de consecutivo de facturación", type=["xlsx"])
upload_cobros = st.file_uploader("Sube el archivo de cobros", type=["xlsx"])

# check if the file is uploaded
if upload_facturas is not None and upload_facturas_x_concepto is not None and upload_consecutivo_facturacion is not None and upload_cobros is not None:
    # read the excel file
    try:
        facturas_x_concepto = pd.read_excel(upload_facturas_x_concepto,)
        facturas = pd.read_excel(upload_facturas)
        consecutivo_facturacion = pd.read_excel(upload_consecutivo_facturacion)
        cobros = pd.read_excel(upload_cobros)
    except Exception as e:
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
