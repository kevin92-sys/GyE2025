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
from render_tab2 import render_dashboard_interanual
from render_tab4 import hacienda
import locale
locale.setlocale(locale.LC_TIME, "Spanish_Argentina")

##run cmd C:\Users\Kevin\Dropbox\Administracion\2025\FINANZAS 2025>

# Configuración general
st.set_page_config(page_title="Dashboard Modular", layout="wide")
st.title("📊 Est. Don Pedro")

# Tabs principales
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🗺️ Mapa de Lotes",
    "📈 Dashboard Económico",
    "🌾 Margen Bruto por Cultivo",
    "🐄 Ganadería",
    "💰 Finanzas y Créditos"
])

# Ruta base del proyecto
BASE_DIR = Path("C:/Users/Kevin/Dropbox/Administracion/2025/FINANZAS 2025")

archivo_2025 = BASE_DIR / "4-MOVBANCARIOS2025.xlsx"
archivo_2026 = BASE_DIR / "4-MOVBANCARIOS2026.xlsx"


# ========================== TAB 1 ==========================
base_dir = BASE_DIR / "datos"

with tab1:
    st.markdown("## 🗺️ Mapa de Lotes con Información Agronómica")
    
    campaña = st.selectbox(
        "Seleccionar campaña",
        ["2024-2025", "2025-2026"],
        key="campaña_tab1"
    )

    if campaña == "2024-2025":
        geojson_path = base_dir / "campaña2024-2025.geojson"
    else:
        geojson_path = base_dir / "campaña2026.geojson"

    m = crear_mapa_lotes(geojson_path)
    st_folium(m, width=900, height=600)

    st.markdown("---")
    st.markdown("## 📅 Plan de Siembra por Lote")
    mostrar_gantt()


# ========================== FUNCIÓN DE CARGA ==========================
def cargar_excel(path, anio):

    if not path.exists():
        st.error(f"❌ No se encontró el archivo: {path}")
        st.stop()

    hojas = pd.ExcelFile(path).sheet_names

    if "MOV" not in hojas:
        st.error(f"⚠️ La hoja 'MOV' no existe. Hojas disponibles: {hojas}")
        st.stop()

    # 📌 Header según el año
    if anio == 2025:
        header_row = 7   # fila 8 en Excel
    elif anio == 2026:
        header_row = 2   # fila 3 en Excel
    else:
        header_row = 0

    df = pd.read_excel(path, sheet_name="MOV", header=header_row)

    # Normalizar columnas
    df.columns = df.columns.str.strip().str.upper()

    # Renombrar columnas
    df = df.rename(columns={
        "FECHA": "Fecha",
        "RUBRO": "Rubro",
        "INGRESOS": "Ingreso ARS",
        "EGRESOS": "Egreso ARS",
        "INGRES USD": "Ingreso USD",
        "EGRES USD": "Egreso USD",
        "ACTIVIDAD": "ACTIVIDAD"
    })

    df["AÑO"] = anio

    return df

# ========================== TAB 2 ==========================
with tab2:

    df_final = render_dashboard_interanual(
        archivo_2025,
        archivo_2026,
        cargar_excel
    )

    df_agricultura = df_final[
        df_final["ACTIVIDAD"].str.upper() == "AGRICULTURA"
    ].copy()



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
    hacienda(BASE_DIR)



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
