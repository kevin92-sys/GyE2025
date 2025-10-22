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
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🗺️ Mapa de Lotes",
    "📈 Dashboard Económico",
    "🌾 Margen Bruto por Cultivo",
    "🐄 Ganadería",
    "💰 Finanzas y Créditos"
])

# ------------------ RUTAS ------------------
# Carpeta base del proyecto (donde está dashboard.py)
BASE_DIR = Path(__file__).resolve().parent

# Archivo Excel en la misma carpeta que dashboard.py
archivo_excel = BASE_DIR / "4-MOVBANCARIOS2025.xlsx"



# Carpeta de GeoJSON
geojson_dir = BASE_DIR / "datos"

# ========================== TAB 1 ==========================
with tab1:
    st.markdown("## 🗺️ Mapa de Lotes con Información Agronómica")

    # Selector de campaña
    campaña = st.selectbox("Seleccionar campaña", ["2024-2025", "2025-2026"])

    # Detectar archivo GeoJSON según campaña
    if campaña == "2024-2025":
        geojson_path = geojson_dir / "campaña2024-2025.geojson"
    else:
        geojson_path = geojson_dir / "campaña2026.geojson"

    # Validar existencia
    if not geojson_path.exists():
        st.error(f"❌ No se encontró el archivo GeoJSON: `{geojson_path}`")
        st.info("Subí la carpeta `datos/` con los archivos GeoJSON al repo de GitHub.")
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


# ========================== TAB 3 ==========================
with tab3:
    st.subheader("🌾 Margen Bruto Agricultura 2025")

    # ================= Clasificación =================
    ingresos_detalles = [
        "VENTA",
        "COMPENSACIONES",
        "SUBSIDIOS",
        "SOJA PRESTADA ANTERIOR",
        "IVA RG 2300/2007",
        "ALQUILER",
        "BPAS"
    ]

    egresos_detalles = [
        "DESYUYADOR", "APLICACIONES", "SEGUROS", "SIEMBRA", "EXTRACCION",
        "COSECHA", "FLETES", "INSUMOS","INSUMOS 2025", "INSUMOS 2024", "HONORARIOS", "ACARREO",
        "FLETES FERTILIZANTE", "CONTRATO ALQUILER", "ROLLOS", "ANALISIS SUELO", "PICADO", "SEMILLAS"
    ]

    # ================= Preparar dataframe =================
    df_agricultura = df_final[df_final["ACTIVIDAD"].str.upper() == "AGRICULTURA"].copy()
    df_agricultura["DETALLES"] = df_agricultura["DETALLES"].astype(str).str.strip().str.upper()

    df_agricultura["Ingreso ARS"] = pd.to_numeric(
        df_agricultura["Ingreso ARS"].astype(str).str.replace("[^0-9.,-]", "", regex=True)
            .str.replace(",", "."), errors="coerce"
    ).fillna(0)

    df_agricultura["Egreso ARS"] = pd.to_numeric(
        df_agricultura["Egreso ARS"].astype(str).str.replace("[^0-9.,-]", "", regex=True)
            .str.replace(",", "."), errors="coerce"
    ).fillna(0)

    # ================= Agrupar por DETALLES =================
    detalles_unicos = df_agricultura["DETALLES"].unique()
    resumen_detalles = []

    for det in detalles_unicos:
        df_det = df_agricultura[df_agricultura["DETALLES"] == det]
        ingresos = df_det[df_det["DETALLES"].isin(ingresos_detalles)]["Ingreso ARS"].sum()
        egresos = df_det[df_det["DETALLES"].isin(egresos_detalles)]["Egreso ARS"].sum()

        if ingresos != 0 or egresos != 0:
            resumen_detalles.append({
                "DETALLES": det,
                "Ingreso ARS": ingresos,
                "Egreso ARS": egresos,
                "Margen Bruto": ingresos - egresos
            })

    df_resumen_detalles = pd.DataFrame(resumen_detalles).sort_values("Margen Bruto", ascending=False)

    # ================= Métricas resumen =================
    if not df_resumen_detalles.empty:
        total_ingresos = df_resumen_detalles["Ingreso ARS"].sum()
        total_egresos = df_resumen_detalles["Egreso ARS"].sum()
        total_margen = df_resumen_detalles["Margen Bruto"].sum()

        col1, col2, col3 = st.columns(3)
        col1.metric("💰 Total Ingresos", f"${total_ingresos:,.0f}")
        col2.metric("💸 Total Egresos", f"${total_egresos:,.0f}")
        col3.metric("📈 Margen Bruto Total", f"${total_margen:,.0f}")

    # ================= Mostrar tabla =================
    if df_resumen_detalles.empty:
        st.info("ℹ️ No hay datos para mostrar con los filtros aplicados.")
    else:
        st.dataframe(df_resumen_detalles.style.format({
            "Ingreso ARS": "${:,.0f}",
            "Egreso ARS": "${:,.0f}",
            "Margen Bruto": "${:,.0f}"
        }))

        # Gráfico de barras
        fig_detalles = px.bar(
            df_resumen_detalles,
            x="DETALLES",
            y="Margen Bruto",
            color="DETALLES",
            title="🌱 Margen Bruto Agricultura",
            text_auto=True
        )
        st.plotly_chart(fig_detalles, use_container_width=True)



# ========================== TAB 4 ==========================
with tab4:
    st.subheader("🐄 Ventas de Hacienda 2025")

    archivo_hacienda = BASE_DIR / "HACIENDA 2025.xlsx"

    # ================= Tabla 1: resumen por flete =================
    try:
        df_hacienda = pd.read_excel(archivo_hacienda, header=2, usecols="A:I", nrows=6)
    except Exception as e:
        st.error(f"⚠️ Error al leer Excel de Hacienda:\n{e}")
        st.stop()

    df_hacienda.columns = df_hacienda.columns.str.strip().str.upper()

    # Convertir columnas numéricas
    columnas_numericas = ["CANTIDAD", "KG VIVOS", "PROM ANIMAL", "KG FRIG", "PROM FRIG", "RINDE", "MONTO VTA EST", "LIQUIDACION"]
    for col in columnas_numericas:
        if col in df_hacienda.columns:
            df_hacienda[col] = pd.to_numeric(
                df_hacienda[col].astype(str)
                              .str.replace("[^0-9.,-]", "", regex=True)
                              .str.replace(",", "."), 
                errors="coerce"
            )

    # ================= Métricas =================
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("🐄 Cantidad Total", f"{df_hacienda['CANTIDAD'].sum():,.0f} cabezas")
    col2.metric("💰 Total Recaudado", f"${df_hacienda['MONTO VTA EST'].sum():,.0f}")
    col3.metric("📦 Kg Vivos Totales", f"{df_hacienda['KG VIVOS'].sum():,.0f} kg")
    col4.metric("📦 Kg Frigoríficos Totales", f"{df_hacienda['KG FRIG'].sum():,.0f} kg")

    # ================= Tabla =================
    st.markdown("### 📋 Detalle de Ventas por Flete")
    st.dataframe(df_hacienda.style.format({
        "CANTIDAD": "{:,.0f}",
        "KG VIVOS": "{:,.0f}",
        "PROM ANIMAL": "{:,.2f}",
        "KG FRIG": "{:,.0f}",
        "PROM FRIG": "{:,.2f}",
        "RINDE": "{:.2f}%",
        "MONTO VTA EST": "${:,.0f}",
        "LIQUIDACION": "{:,.0f}"  # entero
    }))

    # ================= Gráfico combinado: Monto vs Rinde =================
    import plotly.graph_objects as go

    fig_combined = go.Figure()

    # Monto Vta Est como línea
    fig_combined.add_trace(go.Scatter(
        x=df_hacienda.index,
        y=df_hacienda["MONTO VTA EST"],
        mode="lines+markers",
        name="Monto Vta Est ($)",
        line=dict(color="cyan"),
        yaxis="y1"
    ))

    # Rinde como barras
    fig_combined.add_trace(go.Bar(
        x=df_hacienda.index,
        y=df_hacienda["RINDE"],
        name="Rinde (%)",
        marker_color="lime",
        yaxis="y2",
        opacity=0.2
    ))

    fig_combined.update_layout(
        title="💰 Monto vendido y Rinde por Flete",
        xaxis_title="Flete",
        yaxis=dict(
            title="Monto Vta Est ($)",
            side="left",
            showgrid=False,
            tickformat="$,"
        ),
        yaxis2=dict(
            title="Rinde (%)",
            overlaying="y",
            side="right",
            showgrid=False,
            tickformat=".2f"
        ),
        legend=dict(x=0.01, y=0.99)
    )

    st.plotly_chart(fig_combined, use_container_width=True)

    # ================= Tabla 2: detalle por animal =================
    try:
        df_animales = pd.read_excel(archivo_hacienda, header=12, usecols="A:I", nrows=490)  # fila 13 a 502
    except Exception as e:
        st.error(f"⚠️ Error al leer tabla de animales:\n{e}")
        st.stop()

    df_animales.columns = df_animales.columns.str.strip().str.upper()

    # Convertir KG MEDIA RES a numérico
    df_animales["KG MEDIA RES"] = pd.to_numeric(
        df_animales["KG MEDIA RES"].astype(str)
                        .str.replace("[^0-9.,-]", "", regex=True)
                        .str.replace(",", "."), 
        errors="coerce"
    )

    # Asignar número de animal
    df_animales = df_animales.reset_index(drop=True)
    df_animales["ANIMAL_ID"] = df_animales.index + 1

    # ================= Scatter plot =================
    fig_scatter = px.scatter(
        df_animales,
        x="ANIMAL_ID",
        y="KG MEDIA RES",
        hover_data=["N° FLETE", "FECHA", "CANTIDAD", "TIPIFICACION", "PRECIO", "MONTO VENTA", "DESTINO", "EXPORTACION"],
        title="🐂 Peso de Media Res por Animal",
        labels={"KG MEDIA RES": "Peso (kg)", "ANIMAL_ID": "Animal"}
    )
    st.plotly_chart(fig_scatter, use_container_width=True)






# ========================== TAB 5 ==========================
with tab5:
    st.subheader("💰 Créditos")

    # Archivo de Excel
    archivo_compromisos = BASE_DIR / "5-COMPROMISOS 2025.xlsx"
    
    # Leer Excel, títulos en fila 11 (index=10), solo columnas A-N
    try:
        df_creditos = pd.read_excel(archivo_compromisos, header=10, usecols="A:N")
    except Exception as e:
        st.error(f"⚠️ Error al leer Excel de compromisos:\n{e}")
        st.stop()

    # Limpiar columnas
    df_creditos.columns = df_creditos.columns.str.strip().str.upper()

    # Convertir montos a numéricos
    for col in ["MONTO INICIAL", "A DEVOLVER", "MONTO INICIAL EN USD", "MONTO A DEVOLVER EN USD",
                "TASA INTERES", "COMISION"]:
        if col in df_creditos.columns:
            df_creditos[col] = pd.to_numeric(
                df_creditos[col].astype(str)
                            .str.replace("[^0-9.,-]", "", regex=True)
                            .str.replace(",", "."), 
                errors="coerce"
            )

    # Convertir fechas
    for col in ["FECHA INICIAL", "FECHA FINAL"]:
        if col in df_creditos.columns:
            df_creditos[col] = pd.to_datetime(df_creditos[col], errors="coerce", dayfirst=True)

    # Filtrar solo créditos válidos (descartar subtotales y filas vacías)
    df_creditos = df_creditos[
        df_creditos["MONTO INICIAL"].notna() & 
        (df_creditos["MONTO INICIAL"] > 0) & 
        df_creditos["ESTADO"].notna() &
        df_creditos["DESCRIPCIÓN DEL HITO"].str.upper().str.contains("CREDITO")
    ]

    if df_creditos.empty:
        st.info("ℹ️ No hay créditos válidos para mostrar.")
    else:
        # ================= Métricas =================
        st.markdown("### 📌 Resumen de Créditos")
        total_inicial = df_creditos["MONTO INICIAL"].sum()
        total_a_devolver = df_creditos["A DEVOLVER"].sum()
        pendientes = df_creditos[df_creditos["ESTADO"].str.upper() == "PENDIENTE"].shape[0]

        col1, col2, col3 = st.columns(3)
        col1.metric("💵 Total Capital Inicial (ARS)", f"${total_inicial:,.0f}")
        col2.metric("💵 Total a Devolver (ARS)", f"${total_a_devolver:,.0f}")
        col3.metric("⏳ Créditos Pendientes", f"{pendientes}")

        # ================= Gráfico: Capital Inicial vs A Devolver =================
        import plotly.express as px

        fig_bar = px.bar(
            df_creditos,
            x="DESCRIPCIÓN DEL HITO",
            y=["MONTO INICIAL", "A DEVOLVER"],
            barmode="group",
            text_auto=True,
            title="Capital Inicial vs A Devolver por Crédito (ARS)"
        )

        # Agregar Tasa de Interés como anotación encima de cada barra A Devolver
        for i, row in df_creditos.iterrows():
            fig_bar.add_annotation(
                x=row["DESCRIPCIÓN DEL HITO"],
                y=row["A DEVOLVER"],
                text=f"{row['TASA INTERES']:.2f}%",
                showarrow=True,
                arrowhead=1,
                yshift=10
            )

        st.plotly_chart(fig_bar, use_container_width=True)

        # ================= Tabla =================
        st.markdown("### 📋 Detalle de Créditos")
        st.dataframe(df_creditos[[
            "DESCRIPCIÓN DEL HITO", "MONTO INICIAL", "A DEVOLVER", "TASA INTERES", "FECHA INICIAL", "FECHA FINAL", "ESTADO"
        ]].style.format({
            "MONTO INICIAL": "${:,.0f}",
            "A DEVOLVER": "${:,.0f}",
            "TASA INTERES": "{:.2f}%"
        }))











