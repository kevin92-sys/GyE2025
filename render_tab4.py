import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

def hacienda(BASE_DIR):

    st.subheader("🐄 Ventas de Hacienda 2025")

    archivo_hacienda = BASE_DIR / "HACIENDA 2025.xlsx"

    # =====================================================
    # ================= TABLA 1: RESUMEN ==================
    try:
        df_hacienda = pd.read_excel(
            archivo_hacienda,
            header=2,
            usecols="A:I",
            nrows=7  # filas 3 a 9 en Excel
        )
    except Exception as e:
        st.error(f"⚠️ Error al leer Excel de Hacienda:\n{e}")
        st.stop()

    df_hacienda.columns = df_hacienda.columns.str.strip().str.upper()

    columnas_numericas = [
        "CANTIDAD",
        "KG VIVOS",
        "PROM ANIMAL",
        "KG FRIG",
        "PROM FRIG",
        "RINDE",
        "MONTO VTA EST",
        "LIQUIDACION"
    ]

    for col in columnas_numericas:
        if col in df_hacienda.columns:
            df_hacienda[col] = pd.to_numeric(
                df_hacienda[col].astype(str)
                .str.replace("[^0-9.,-]", "", regex=True)
                .str.replace(",", "."),
                errors="coerce"
            )

    # ================= MÉTRICAS =================
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("🐄 Cantidad Total", f"{df_hacienda['CANTIDAD'].sum():,.0f} cabezas")
    col2.metric("💰 Total Recaudado", f"${df_hacienda['MONTO VTA EST'].sum():,.0f}")
    col3.metric("📦 Kg Vivos Totales", f"{df_hacienda['KG VIVOS'].sum():,.0f} kg")
    col4.metric("📦 Kg Frigoríficos Totales", f"{df_hacienda['KG FRIG'].sum():,.0f} kg")

    # ================= TABLA FORMATEADA =================
    st.markdown("### 📋 Detalle de Ventas por Flete")
    st.dataframe(
        df_hacienda.style.format({
            "CANTIDAD": lambda x: f"{int(x):,}".replace(",", ".") if pd.notnull(x) else "",
            "KG VIVOS": lambda x: f"{int(x):,}".replace(",", ".") if pd.notnull(x) else "",
            "PROM ANIMAL": lambda x: f"{x:.2f}".replace(".", ",") if pd.notnull(x) else "",
            "KG FRIG": lambda x: f"{int(x):,}".replace(",", ".") if pd.notnull(x) else "",
            "PROM FRIG": lambda x: f"{x:.2f}".replace(".", ",") if pd.notnull(x) else "",
            "RINDE": lambda x: f"{x:.2f}".replace(".", ",") + "%" if pd.notnull(x) else "",
            "MONTO VTA EST": lambda x: "$ " + f"{int(x):,}".replace(",", ".") if pd.notnull(x) else "",
            "LIQUIDACION": lambda x: f"{int(x):,}".replace(",", ".") if pd.notnull(x) else "",
        })
    )

    # =====================================================
    # ============ GRÁFICO COMBINADO ======================
    fig_combined = go.Figure()

    # Línea Monto
    fig_combined.add_trace(
        go.Scatter(
            x=df_hacienda.index,
            y=df_hacienda["MONTO VTA EST"],
            mode="lines+markers",
            name="Monto Vta Est ($)",
            line=dict(color="cyan"),
            yaxis="y1"
        )
    )

    # Barras Rinde
    fig_combined.add_trace(
        go.Bar(
            x=df_hacienda.index,
            y=df_hacienda["RINDE"],
            name="Rinde (%)",
            marker_color="lime",
            opacity=0.3,
            yaxis="y2"
        )
    )

    fig_combined.update_layout(
        title="💰 Monto vendido y Rinde por Flete",
        xaxis_title="Flete",
        yaxis=dict(title="Monto Vta Est ($)", side="left", showgrid=False, tickformat="$,"),
        yaxis2=dict(title="Rinde (%)", overlaying="y", side="right", showgrid=False, tickformat=".2f"),
        legend=dict(x=0.01, y=0.99)
    )

    st.plotly_chart(fig_combined, use_container_width=True, key="fig_combined_hacienda")

    # =====================================================
    # ============ TABLA ANIMALES ========================
    try:
        df_animales = pd.read_excel(
            archivo_hacienda,
            header=12,
            usecols="A:I",
            nrows=490
        )
    except Exception as e:
        st.error(f"⚠️ Error al leer tabla de animales:\n{e}")
        st.stop()

    df_animales.columns = df_animales.columns.str.strip().str.upper()

    if "KG MEDIA RES" in df_animales.columns:
        df_animales["KG MEDIA RES"] = pd.to_numeric(
            df_animales["KG MEDIA RES"].astype(str)
            .str.replace("[^0-9.,-]", "", regex=True)
            .str.replace(",", "."),
            errors="coerce"
        )

    df_animales = df_animales.reset_index(drop=True)
    df_animales["ANIMAL_ID"] = df_animales.index + 1

    # ================= SCATTER =================
    fig_scatter = px.scatter(
        df_animales,
        x="ANIMAL_ID",
        y="KG MEDIA RES",
        hover_data=["N° FLETE", "FECHA", "CANTIDAD", "TIPIFICACION", "PRECIO", "MONTO VENTA", "DESTINO", "EXPORTACION"],
        title="🐂 Peso de Media Res por Animal",
        labels={"KG MEDIA RES": "Peso (kg)", "ANIMAL_ID": "Animal"}
    )

    st.plotly_chart(fig_scatter, use_container_width=True, key="fig_scatter_animales")