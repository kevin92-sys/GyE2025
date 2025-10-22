import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_folium import st_folium
from pathlib import Path
import os
import time
import folium
import shutil
from importdash import crear_mapa_lotes
import geopandas as gpd
from gantt_lotes import mostrar_gantt

# Configuración general
st.set_page_config(page_title="Dashboard Modular", layout="wide")
st.title("📊 Dashboard Modular de Ingresos y Egresos")


# Tabs principales
tab1, tab2 = st.tabs(["🗺️ Mapa de Lotes", "📈 Dashboard Económico"])
# Ruta base del proyecto
# ------------------ RUTAS ------------------
# Archivo Excel en la misma carpeta que dashboard.py
archivo_excel = Path("4-MOVBANCARIOS2025.xlsx")

# Carpeta de GeoJSON relativa al repo
geojson_dir = Path("datos")

# ========================== TAB 1 ==========================
with tab1:
    st.markdown("## 🗺️ Mapa de Lotes con Información Agronómica")
    
    # Selector de campaña
    campaña = st.selectbox(
        "Seleccionar campaña",
        ["2024-2025", "2025-2026"]
    )

    # Asignar archivo según campaña
    if campaña == "2024-2025":
        geojson_path = geojson_dir / "campaña2024-2025.geojson"
    else:
        geojson_path = geojson_dir / "campaña2025-2026.geojson"

    # Validar existencia
    if not geojson_path.exists():
        st.error(f"❌ No se encontró el archivo GeoJSON: `{geojson_path}`")
        st.stop()

    # Crear y mostrar el mapa
    m = crear_mapa_lotes(geojson_path)
    st_folium(m, width=900, height=600)

    st.markdown("---")
    st.markdown("## 📅 Plan de Siembra por Lote")
    mostrar_gantt()


# ========================== TAB 2 ==========================
with tab2:
    st.markdown("## 📊 Dashboard Económico")

    # Validación y carga de Excel
    if not archivo_excel.exists():
        st.error(f"❌ No se encontró el archivo Excel: `{archivo_excel}`")
        st.stop()
    try:
        df = pd.read_excel(archivo_excel, sheet_name="MOV", skiprows=2)
    except Exception as e:
        st.error(f"⚠️ Ocurrió un error al leer el archivo Excel:\n\n`{e}`")
        st.stop()

    # Procesamiento de columnas
    df.columns = df.columns.str.strip().str.upper()
    df = df.rename(columns={
        "FECHA": "Fecha",
        "RUBRO": "Rubro",
        "INGRESOS": "Ingreso ARS",
        "EGRESOS": "Egreso ARS",
        "INGRES USD": "Ingreso USD",
        "EGRES USD": "Egreso USD"
    })

    # Validación de columnas
    columnas_requeridas = ["Fecha", "Rubro", "Ingreso ARS", "Egreso ARS", "Ingreso USD", "Egreso USD", "ACTIVIDAD"]
    if not all(col in df.columns for col in columnas_requeridas):
        st.error("❌ Faltan columnas necesarias: " + ", ".join(columnas_requeridas))
        st.stop()

    # Formateo general
    df["Fecha"] = pd.to_datetime(df["Fecha"], errors="coerce")
    df["Mes"] = df["Fecha"].dt.to_period("M").astype(str)

    for col in ["Ingreso ARS", "Egreso ARS", "Ingreso USD", "Egreso USD"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    # ========= MÓDULO 1: Filtro por Actividad =========
    st.sidebar.header("🔍 Filtro de Actividades")
    actividades_unicas = sorted(df["ACTIVIDAD"].dropna().unique())
    actividad_sel = st.sidebar.multiselect("Seleccioná una o más actividades", actividades_unicas, default=actividades_unicas)

    df_filtrado_1 = df[df["ACTIVIDAD"].isin(actividad_sel)]

    # ========= MÓDULO 2: Filtro por Rubro (según actividad) =========
    st.sidebar.header("📂 Filtro de Rubros")
    rubros_validos = sorted(df_filtrado_1["Rubro"].dropna().unique())
    rubro_sel = st.sidebar.multiselect("Seleccioná uno o más rubros", rubros_validos, default=rubros_validos)

    df_filtrado_2 = df_filtrado_1[df_filtrado_1["Rubro"].isin(rubro_sel)]

    # ========= MÓDULO 3: Filtro por Mes =========
    st.sidebar.header("🗓️ Filtro de Meses")
    meses_validos = sorted(df_filtrado_2["Mes"].dropna().unique())
    meses_sel = st.sidebar.multiselect("Seleccioná uno o más meses", meses_validos, default=meses_validos)

    df_final = df_filtrado_2[df_filtrado_2["Mes"].isin(meses_sel)]

    # ========= MÓDULO 4: Métricas =========
    st.markdown("## 📌 Métricas Generales")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("💸 Egresos (ARS)", f"${df_final['Egreso ARS'].sum():,.0f}")
    col2.metric("🟢 Ingresos (ARS)", f"${df_final['Ingreso ARS'].sum():,.0f}")
    col3.metric("💸 Egresos (USD)", f"USD {df_final['Egreso USD'].sum():,.2f}")
    col4.metric("🟢 Ingresos (USD)", f"USD {df_final['Ingreso USD'].sum():,.2f}")

    # ========= MÓDULO 5: Gráficos =========
    st.markdown("## 📈 Gráficos")

    # Evolución mensual
    st.subheader("📊 Evolución Mensual de Ingresos y Egresos (ARS)")
    df_mensual = df_final.groupby("Mes").sum(numeric_only=True).reset_index()
    fig_line = px.line(
        df_mensual,
        x="Mes",
        y=["Ingreso ARS", "Egreso ARS"],
        markers=True,
        color_discrete_map={"Ingreso ARS": "green", "Egreso ARS": "red"}
    )
    st.plotly_chart(fig_line, use_container_width=True)

    # Barras por rubro
    st.subheader("🏷️ Ingresos y Egresos por Rubro (ARS)")
    df_rubro = df_final.groupby("Rubro").sum(numeric_only=True).reset_index()
    fig_bar_ars = px.bar(df_rubro, x="Rubro", y=["Ingreso ARS", "Egreso ARS"], barmode="group", height=400)
    st.plotly_chart(fig_bar_ars, use_container_width=True)

    st.subheader("💵 Ingresos y Egresos por Rubro (USD)")
    fig_bar_usd = px.bar(df_rubro, x="Rubro", y=["Ingreso USD", "Egreso USD"], barmode="group", height=400)
    st.plotly_chart(fig_bar_usd, use_container_width=True)

    # 🎯 Pie Chart por Rubro
    # ========= MÓDULO 5 (continuación): Pie Chart por Rubro con detalles =========
    st.subheader("🥧 Distribución por Rubro (Pie Chart)")

    # Selector de variable a mostrar
    opciones_pie = {
        "Ingreso ARS": "green",
        "Egreso ARS": "red",
        "Ingreso USD": "green",
        "Egreso USD": "red"
    }
    variable_pie = st.selectbox("Seleccioná el tipo de dato a analizar", list(opciones_pie.keys()))

    # Pie general por Rubro
    df_pie_rubro = df_final.groupby("Rubro")[[variable_pie]].sum().reset_index()
    df_pie_rubro = df_pie_rubro[df_pie_rubro[variable_pie] > 0].sort_values(by=variable_pie, ascending=False)

    fig_pie = px.pie(
        df_pie_rubro,
        names="Rubro",
        values=variable_pie,
        title=f"Distribución de {variable_pie} por Rubro",
        color_discrete_sequence=[opciones_pie[variable_pie]],
        hole=0.4
    )
    st.plotly_chart(fig_pie, use_container_width=True)

    # Selector de Rubro para ver detalles
    rubro_detalle = st.selectbox("🔎 Ver detalles para el rubro:", df_pie_rubro["Rubro"].unique())

    # Pie por Detalles dentro del rubro seleccionado
    df_detalles = df_final[df_final["Rubro"] == rubro_detalle]
    if "CONCEPTO" in df_detalles.columns:
        df_pie_detalles = df_detalles.groupby("CONCEPTO")[[variable_pie]].sum().reset_index()
        df_pie_detalles = df_pie_detalles[df_pie_detalles[variable_pie] > 0]
    
        if not df_pie_detalles.empty:
            fig_pie_detalle = px.pie(
                df_pie_detalles,
                names="CONCEPTO",
                values=variable_pie,
                title=f"Desglose de {variable_pie} dentro de {rubro_detalle}",
                hole=0.4,
                color_discrete_sequence=px.colors.sequential.RdBu
            )
            st.plotly_chart(fig_pie_detalle, use_container_width=True)
        else:
            st.info(f"ℹ️ No hay valores positivos para {variable_pie} en los conceptos de '{rubro_detalle}'.")
    else:
        st.warning("⚠️ La columna 'CONCEPTO' no existe en los datos.")




    # ========= MÓDULO: MARGEN BRUTO POR CULTIVO (adaptado a CULT. PRINCIPAL) =========
    st.subheader("🌾 Margen Bruto por Cultivo")

    ingresos_detalles = ["VENTA", "COMPENSACIONES", "SUBSIDIOS","IVA RG 2300/2007"]  # los que suman ingresos
    egresos_detalles = [
        "DESYUYADOR", "APLICACIONES", "SEGUROS", "SIEMBRA", "EXTRACCION",
        "COSECHA", "FLETES", "INSUMOS", "HONORARIOS", "ACARREO", "ALQUILER"
    ]  # gastos

    def calcular_margen_bruto(df):
        # Normalizar textos
        df["DETALLES"] = df["DETALLES"].astype(str).str.strip().str.upper()
        df["CONCEPTO"] = df["CONCEPTO"].astype(str).str.strip().str.upper()

        ingresos_detalles = ["VENTA", "COMPENSACIONES", "SUBSIDIOS", "SOJA PRESTADA ANTERIOR"]
        egresos_detalles = [
            "DESYUYADOR", "APLICACIONES", "SEGUROS", "SIEMBRA", "EXTRACCION",
            "COSECHA", "FLETES", "INSUMOS", "HONORARIOS", "ACARREO", "ALQUILER","FLETES FERTILIZANTE","BPAS"
        ]
        ingresos_detalles_upper = [x.upper() for x in ingresos_detalles]
        egresos_detalles_upper = [x.upper() for x in egresos_detalles]

        # Asegurar que los valores sean numéricos
        df["Ingreso ARS"] = pd.to_numeric(
            df["Ingreso ARS"].astype(str).str.replace("[^0-9.,-]", "", regex=True).str.replace(",", "."), errors="coerce"
        ).fillna(0)
        df["Egreso ARS"] = pd.to_numeric(
            df["Egreso ARS"].astype(str).str.replace("[^0-9.,-]", "", regex=True).str.replace(",", "."), errors="coerce"
        ).fillna(0)

        # Obtener todos los cultivos únicos del campo CONCEPTO
        cultivos = df["CONCEPTO"].unique()

        margen_cultivos = []

        for cultivo in cultivos:
            df_cultivo = df[df["CONCEPTO"] == cultivo]

            ingresos = df_cultivo[df_cultivo["DETALLES"].isin(ingresos_detalles_upper)]["Ingreso ARS"].sum()
            egresos = df_cultivo[df_cultivo["DETALLES"].isin(egresos_detalles_upper)]["Egreso ARS"].sum()

            if ingresos > 0 or egresos > 0:
                margen_cultivos.append({
                    "Cultivo": cultivo,
                    "Ingreso ARS": ingresos,
                    "Egreso ARS": egresos,
                    "Margen Bruto": ingresos - egresos
                })

        df_margen = pd.DataFrame(margen_cultivos)
        return df_margen.sort_values("Margen Bruto", ascending=False)


    df_margen_bruto = calcular_margen_bruto(df_final)

    if df_margen_bruto.empty:
        st.info("ℹ️ No hay datos para mostrar Margen Bruto con los filtros aplicados.")
    else:
        # Mostrar tabla con formato
        st.dataframe(df_margen_bruto.style.format({
            "Ingreso ARS": "${:,.0f}",
            "Egreso ARS": "${:,.0f}",
            "Margen Bruto": "${:,.0f}"
        }))

        # Mostrar gráfico
        fig_margen = px.bar(
            df_margen_bruto,
            x="Cultivo",
            y="Margen Bruto",
            color="Cultivo",
            title="🌱 Margen Bruto por Cultivo",
            text_auto=True
        )
        st.plotly_chart(fig_margen, use_container_width=True)


    # ========= MÓDULO 6: Tabla Detallada =========
    st.markdown("## 📋 Tabla Detallada")
    st.dataframe(df_final[["Fecha", "Rubro", "ACTIVIDAD", "Ingreso ARS", "Egreso ARS", "Ingreso USD", "Egreso USD"]].style.format({
        "Ingreso ARS": "${:,.0f}",
        "Egreso ARS": "${:,.0f}",
        "Ingreso USD": "USD {:,.2f}",
        "Egreso USD": "USD {:,.2f}"
    }))




