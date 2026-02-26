import streamlit as st
import pandas as pd
import plotly.express as px

def render_dashboard_interanual(archivo_2025, archivo_2026, cargar_excel):

    st.markdown("## 📈 Dashboard Económico Interanual")

    campaña = st.selectbox(
        "Seleccionar campaña",
        ["2024-2025", "2025-2026", "Comparar ambas"],
        key="campaña_tab2"
    )

    archivos_campaña = {
        "2024-2025": archivo_2025,
        "2025-2026": archivo_2026
    }

    # ===================== CARGA =====================
    if campaña == "Comparar ambas":
        df_2025 = cargar_excel(archivo_2025, 2025)
        df_2026 = cargar_excel(archivo_2026, 2026)
        df = pd.concat([df_2025, df_2026], ignore_index=True)
    else:
        anio = 2025 if campaña == "2024-2025" else 2026
        df = cargar_excel(archivos_campaña[campaña], anio)
    
    # ===================== VALIDACIÓN =====================
    columnas_requeridas = [
        "Fecha", "Rubro", "DETALLES",
        "Ingreso ARS", "Egreso ARS",
        "Ingreso USD", "Egreso USD",
        "ACTIVIDAD", "AÑO"
    ]
    
    faltantes = [col for col in columnas_requeridas if col not in df.columns]

    if faltantes:
        st.error(f"❌ Faltan columnas necesarias: {', '.join(faltantes)}")
        st.stop()

    # ===================== FORMATEO =====================
    df["Fecha"] = pd.to_datetime(df["Fecha"], errors="coerce")
    df["Mes_Orden"] = df["Fecha"].dt.to_period("M")

    meses_es = {
        1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
        5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
        9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
    }

    df["Mes"] = (
        df["Fecha"].dt.month.map(meses_es)
        + " "
        + df["Fecha"].dt.year.astype(str)
    )

    for col in ["Ingreso ARS", "Egreso ARS", "Ingreso USD", "Egreso USD"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    # ===================== FILTROS =====================
    st.sidebar.header("🔍 Filtro de Actividades")
    actividades_unicas = sorted(df["ACTIVIDAD"].dropna().unique())
    actividad_sel = st.sidebar.multiselect(
        "Seleccioná una o más actividades",
        actividades_unicas,
        default=actividades_unicas
    )
    df = df[df["ACTIVIDAD"].isin(actividad_sel)]

    st.sidebar.header("📂 Filtro de Rubros")
    rubros_validos = sorted(df["Rubro"].dropna().unique())
    rubro_sel = st.sidebar.multiselect(
        "Seleccioná uno o más rubros",
        rubros_validos,
        default=rubros_validos
    )
    df = df[df["Rubro"].isin(rubro_sel)]

    st.sidebar.header("🗓️ Filtro de Meses")
    meses_validos = (
        df.sort_values("Mes_Orden")["Mes"]
        .dropna()
        .unique()
    )
    meses_sel = st.sidebar.multiselect(
        "Seleccioná uno o más meses",
        meses_validos,
        default=meses_validos
    )
    df_final = df[df["Mes"].isin(meses_sel)].copy()

    # ===================== COMPARACIÓN INTERANUAL =====================
    # ===================== COMPARACIÓN INTERANUAL =====================
    if campaña == "Comparar ambas":

        st.markdown("## 📊 Comparación Interanual 2025 vs 2026")

        # ===== Tabla por actividad y mes =====
        for anio in [2025, 2026]:

            st.markdown(f"### 📅 Año {anio}")

            # Filtrar solo egresos del año
            df_anio = df_final[(df_final["AÑO"] == anio) & (df_final["Egreso ARS"] > 0)]

            if df_anio.empty:
                st.info(f"No hay datos para {anio}.")
                continue

            # Agrupar por actividad y Mes_Orden
            tabla = (
                df_anio
                .groupby(["ACTIVIDAD", "Mes_Orden"])["Egreso ARS"]
                .sum()
                .reset_index()
                .pivot(index="ACTIVIDAD", columns="Mes_Orden", values="Egreso ARS")
                .fillna(0)
                .sort_index(axis=1)
            )

            # Nombres de columnas amigables
            tabla.columns = [mes.strftime("%B %Y") if not pd.isnull(mes) else "" for mes in tabla.columns]

            # Agregar fila Total
            tabla.loc["Total"] = tabla.sum()

            st.dataframe(tabla.style.format("${:,.0f}"))

            # Detalles de actividad específica
            actividades_disponibles = df_anio["ACTIVIDAD"].unique()
            if len(actividades_disponibles) > 0:
                actividad_seleccionada = st.selectbox(f"Selecciona actividad {anio}", actividades_disponibles)

                if actividad_seleccionada:
                    detalles = df_anio[df_anio["ACTIVIDAD"] == actividad_seleccionada]
                    st.dataframe(
                        detalles[["Fecha", "DETALLES", "Egreso ARS"]]
                        .sort_values("Fecha")
                        .style.format({"Egreso ARS": "${:,.0f}"})
                    )

        # ===== Gráfico de barras por PERIODO interanual =====
        # ===== Gráfico de barras por PERIODO interanual =====
        # ===== Gráfico de barras por PERIODO interanual usando Fecha =====
        st.markdown("### 📊 Comparación de Egresos por Mes 2025 vs 2026")

        # Filtrar egresos positivos
        df_periodo = df_final[df_final["Egreso ARS"] > 0].copy()

        if not df_periodo.empty:
            # Crear columna Mes_Año en español para mostrar en el gráfico
            df_periodo["Mes"] = df_periodo["Fecha"].dt.month.map(meses_es)
            df_periodo["PERIODO"] = df_periodo["Mes"] + " " + df_periodo["Fecha"].dt.year.astype(str)
            
            # Agrupar por PERIODO y AÑO usando Fecha para orden cronológico
            df_periodo_agrup = (
                df_periodo.groupby(["PERIODO", "AÑO"])["Egreso ARS"]
                .sum()
                .reset_index()
            )

            # Crear columna de orden numérico para ordenar cronológicamente
            df_periodo_agrup["Fecha_orden"] = pd.to_datetime(df_periodo_agrup["PERIODO"], format="%B %Y", errors='coerce')

            # Ordenar por Fecha_orden y convertir PERIODO a categoría
            df_periodo_agrup = df_periodo_agrup.sort_values("Fecha_orden")
            df_periodo_agrup["PERIODO"] = pd.Categorical(
                df_periodo_agrup["PERIODO"],
                categories=df_periodo_agrup["PERIODO"].unique(),
                ordered=True
            )

            # Crear gráfico de barras
            fig_periodo = px.bar(
                df_periodo_agrup,
                x="PERIODO",
                y="Egreso ARS",
                color="AÑO",
                barmode="group",
                title="Egresos por Mes 2025 vs 2026"
            )
            fig_periodo.update_xaxes(tickangle=45)
            st.plotly_chart(fig_periodo, use_container_width=True)
        else:
            st.info("ℹ️ No hay egresos para mostrar por periodo.")

    # ===================== CAMPAÑA INDIVIDUAL =====================
    elif campaña in ["2024-2025", "2025-2026"]:

        st.markdown("## 📌 Métricas Generales")

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("💸 Egresos (ARS)", f"${df_final['Egreso ARS'].sum():,.0f}")
        col2.metric("🟢 Ingresos (ARS)", f"${df_final['Ingreso ARS'].sum():,.0f}")
        col3.metric("💸 Egresos (USD)", f"USD {df_final['Egreso USD'].sum():,.2f}")
        col4.metric("🟢 Ingresos (USD)", f"USD {df_final['Ingreso USD'].sum():,.2f}")

        st.markdown("## 📈 Gráficos")

        # Evolución mensual
        st.subheader("📊 Evolución Mensual (ARS)")
        df_mensual = (
            df_final
            .groupby(["Mes_Orden", "Mes"])
            .sum(numeric_only=True)
            .reset_index()
            .sort_values("Mes_Orden")
        )

        fig_line = px.line(
            df_mensual,
            x="Mes",
            y=["Ingreso ARS", "Egreso ARS"],
            markers=True
        )
        st.plotly_chart(fig_line, use_container_width=True)

        # Barras por rubro
        st.subheader("🏷️ Ingresos y Egresos por Rubro (ARS)")
        df_rubro = df_final.groupby("Rubro").sum(numeric_only=True).reset_index()

        fig_bar = px.bar(
            df_rubro,
            x="Rubro",
            y=["Ingreso ARS", "Egreso ARS"],
            barmode="group"
        )
        st.plotly_chart(fig_bar, use_container_width=True)

        # Pie chart
        st.subheader("🥧 Distribución por Rubro")
        variable_pie = st.selectbox(
            "Seleccioná el tipo de dato a analizar",
            ["Ingreso ARS", "Egreso ARS", "Ingreso USD", "Egreso USD"]
        )

        df_pie = (
            df_final
            .groupby("Rubro")[[variable_pie]]
            .sum()
            .reset_index()
        )

        df_pie = df_pie[df_pie[variable_pie] > 0]

        if not df_pie.empty:
            fig_pie = px.pie(
                df_pie,
                names="Rubro",
                values=variable_pie,
                hole=0.4
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("ℹ️ No hay datos positivos para graficar.")

    

            # ===== Comparación por CONCEPTO (líneas) =====
            
    else:
        st.info("Seleccioná una campaña válida.")

    return df_final