import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

def hacienda(BASE_DIR):

    st.subheader("🐄 Ventas de Hacienda 2025")

    archivo_hacienda = BASE_DIR / "HACIENDA 2025.xlsx"

    # ===================== TABLA RESUMEN HACIENDA 2025 =====================
    try:
        df_hacienda = pd.read_excel(
            archivo_hacienda,
            header=2,
            usecols="A:I",
            nrows=7
        )
    except Exception as e:
        st.error(f"⚠️ Error al leer Excel de Hacienda:\n{e}")
        st.stop()

    df_hacienda.columns = df_hacienda.columns.str.strip().str.upper()
    columnas_numericas = ["CANTIDAD","KG VIVOS","PROM ANIMAL","KG FRIG","PROM FRIG","RINDE","MONTO VTA EST","LIQUIDACION"]

    for col in columnas_numericas:
        if col in df_hacienda.columns:
            df_hacienda[col] = pd.to_numeric(
                df_hacienda[col].astype(str).str.replace("[^0-9.,-]", "", regex=True).str.replace(",", "."),
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
    st.dataframe(df_hacienda.style.format({
        "CANTIDAD": lambda x: f"{int(x):,}".replace(",", ".") if pd.notnull(x) else "",
        "KG VIVOS": lambda x: f"{int(x):,}".replace(",", ".") if pd.notnull(x) else "",
        "PROM ANIMAL": lambda x: f"{x:.2f}".replace(".", ",") if pd.notnull(x) else "",
        "KG FRIG": lambda x: f"{int(x):,}".replace(",", ".") if pd.notnull(x) else "",
        "PROM FRIG": lambda x: f"{x:.2f}".replace(".", ",") if pd.notnull(x) else "",
        "RINDE": lambda x: f"{x:.2f}".replace(".", ",") + "%" if pd.notnull(x) else "",
        "MONTO VTA EST": lambda x: "$ " + f"{int(x):,}".replace(",", ".") if pd.notnull(x) else "",
        "LIQUIDACION": lambda x: f"{int(x):,}".replace(",", ".") if pd.notnull(x) else "",
    }))

    # ================= GRÁFICO COMBINADO =================
    fig_combined = go.Figure()
    fig_combined.add_trace(go.Scatter(x=df_hacienda.index, y=df_hacienda["MONTO VTA EST"], mode="lines+markers",
                                      name="Monto Vta Est ($)", line=dict(color="cyan"), yaxis="y1"))
    fig_combined.add_trace(go.Bar(x=df_hacienda.index, y=df_hacienda["RINDE"], name="Rinde (%)",
                                  marker_color="lime", opacity=0.3, yaxis="y2"))
    fig_combined.update_layout(
        title="💰 Monto vendido y Rinde por Flete",
        xaxis_title="Flete",
        yaxis=dict(title="Monto Vta Est ($)", side="left", showgrid=False, tickformat="$,"),
        yaxis2=dict(title="Rinde (%)", overlaying="y", side="right", showgrid=False, tickformat=".2f"),
        legend=dict(x=0.01, y=0.99)
    )
    st.plotly_chart(fig_combined, use_container_width=True, key="fig_combined_hacienda")

    # ================= TABLA ANIMALES =================
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
            df_animales["KG MEDIA RES"].astype(str).str.replace("[^0-9.,-]", "", regex=True).str.replace(",", "."),
            errors="coerce"
        )
    df_animales = df_animales.reset_index(drop=True)
    df_animales["ANIMAL_ID"] = df_animales.index + 1

    fig_scatter = px.scatter(df_animales, x="ANIMAL_ID", y="KG MEDIA RES",
                             hover_data=["N° FLETE", "FECHA", "CANTIDAD", "TIPIFICACION",
                                         "PRECIO", "MONTO VENTA", "DESTINO", "EXPORTACION"],
                             title="🐂 Peso de Media Res por Animal",
                             labels={"KG MEDIA RES": "Peso (kg)", "ANIMAL_ID": "Animal"})
    st.plotly_chart(fig_scatter, use_container_width=True, key="fig_scatter_animales")
<<<<<<< HEAD

    # ================= MOVIMIENTO HACIENDA 2025 =================
    st.subheader("📊 Movimiento de Hacienda (2024-2026) - Comparativa Compra/Venta")

    archivo_movimiento = BASE_DIR / "2.1- MOVIMIENTO HACIENDA 2025.xlsx"
    hojas = ["2024", "2025", "2026"]
    dfs_movimiento = {}

    for hoja in hojas:
        try:
            df = pd.read_excel(archivo_movimiento, sheet_name=hoja, header=1)
            df.columns = df.columns.str.strip()
            dfs_movimiento[hoja] = df
        except Exception as e:
            st.error(f"⚠️ Error al leer hoja {hoja}: {e}")

    # Mostrar en pestañas
    tab1, tab2, tab3 = st.tabs(hojas)
    for tab, hoja in zip([tab1, tab2, tab3], hojas):
        with tab:
            if hoja in dfs_movimiento:
                df = dfs_movimiento[hoja]
                st.dataframe(df)

                cols_upper = [c.upper() for c in df.columns]

                if "PRECIO POR KG" in cols_upper and "CONCEPTO" in cols_upper:
                    precio_col = df.columns[cols_upper.index("PRECIO POR KG")]
                    concepto_col = df.columns[cols_upper.index("CONCEPTO")]

                    # Convertir PRECIO POR KG a numérico
                    df[precio_col] = pd.to_numeric(
                        df[precio_col].astype(str)
                        .str.replace("[^0-9.,-]", "", regex=True)
                        .str.replace(",", "."),
                        errors="coerce"
                    )

                    # Filtrar filas por concepto
                    df_venta = df[df[concepto_col].str.upper().str.contains("VENTA")]
                    df_compra = df[df[concepto_col].str.upper().str.contains("COMPRA")]

                    # Calcular total por concepto (PRECIO POR KG * CANTIDAD si existe)
                    if "CANTIDAD" in cols_upper:
                        cant_col = df.columns[cols_upper.index("CANTIDAD")]
                        df_venta["MONTO_CALC"] = df_venta[precio_col] * pd.to_numeric(df_venta[cant_col], errors="coerce")
                        df_compra["MONTO_CALC"] = df_compra[precio_col] * pd.to_numeric(df_compra[cant_col], errors="coerce")
                    else:
                        df_venta["MONTO_CALC"] = df_venta[precio_col]
                        df_compra["MONTO_CALC"] = df_compra[precio_col]

                    # Agrupar por concepto y sumar
                    venta_agrup = df_venta.groupby(concepto_col)["MONTO_CALC"].sum().reset_index()
                    compra_agrup = df_compra.groupby(concepto_col)["MONTO_CALC"].sum().reset_index()

                    # Unir para comparar lado a lado
                    df_comparativa = pd.merge(venta_agrup, compra_agrup, on=concepto_col, how="outer", suffixes=("_VENTA", "_COMPRA")).fillna(0)

                    # Gráfico comparativo
                    fig = px.bar(df_comparativa, x=concepto_col, y=["MONTO_CALC_VENTA", "MONTO_CALC_COMPRA"],
                                title=f"Comparativa Compra vs Venta {hoja}",
                                labels={"value": "Importe ($)", "variable": "Tipo"})
                    st.plotly_chart(fig, use_container_width=True)

                    # Mostrar ratio promedio si hay compra
                    if not df_compra.empty:
                        ratio_promedio = df_venta[precio_col].mean() / df_compra[precio_col].mean()
                        st.metric(f"Ratio Precio Venta/Compra {hoja}", f"{ratio_promedio:.2f}")
                    else:
                        st.info("⚠️ No hay datos de compra para calcular ratio")
                else:
                    st.info("⚠️ No hay columnas PRECIO POR KG o CONCEPTO en esta hoja")

                    

=======

    # ================= MOVIMIENTO HACIENDA 2025 =================
    st.subheader("📊 Movimiento de Hacienda (2024-2026) - Comparativa Compra/Venta")

    archivo_movimiento = BASE_DIR / "2.1- MOVIMIENTO HACIENDA 2025.xlsx"
    hojas = ["2024", "2025", "2026"]
    dfs_movimiento = {}

    for hoja in hojas:
        try:
            df = pd.read_excel(archivo_movimiento, sheet_name=hoja, header=1)
            df.columns = df.columns.str.strip()
            dfs_movimiento[hoja] = df
        except Exception as e:
            st.error(f"⚠️ Error al leer hoja {hoja}: {e}")

    # Mostrar en pestañas
    tab1, tab2, tab3 = st.tabs(hojas)
    for tab, hoja in zip([tab1, tab2, tab3], hojas):
        with tab:
            if hoja in dfs_movimiento:
                df = dfs_movimiento[hoja]
                st.dataframe(df)

                cols_upper = [c.upper() for c in df.columns]

                if "PRECIO POR KG" in cols_upper and "CONCEPTO" in cols_upper:
                    precio_col = df.columns[cols_upper.index("PRECIO POR KG")]
                    concepto_col = df.columns[cols_upper.index("CONCEPTO")]

                    # Convertir PRECIO POR KG a numérico
                    df[precio_col] = pd.to_numeric(
                        df[precio_col].astype(str)
                        .str.replace("[^0-9.,-]", "", regex=True)
                        .str.replace(",", "."),
                        errors="coerce"
                    )

                    # Filtrar filas por concepto
                    df_venta = df[df[concepto_col].str.upper().str.contains("VENTA")]
                    df_compra = df[df[concepto_col].str.upper().str.contains("COMPRA")]

                    # Calcular total por concepto (PRECIO POR KG * CANTIDAD si existe)
                    if "CANTIDAD" in cols_upper:
                        cant_col = df.columns[cols_upper.index("CANTIDAD")]
                        df_venta["MONTO_CALC"] = df_venta[precio_col] * pd.to_numeric(df_venta[cant_col], errors="coerce")
                        df_compra["MONTO_CALC"] = df_compra[precio_col] * pd.to_numeric(df_compra[cant_col], errors="coerce")
                    else:
                        df_venta["MONTO_CALC"] = df_venta[precio_col]
                        df_compra["MONTO_CALC"] = df_compra[precio_col]

                    # Agrupar por concepto y sumar
                    venta_agrup = df_venta.groupby(concepto_col)["MONTO_CALC"].sum().reset_index()
                    compra_agrup = df_compra.groupby(concepto_col)["MONTO_CALC"].sum().reset_index()

                    # Unir para comparar lado a lado
                    df_comparativa = pd.merge(venta_agrup, compra_agrup, on=concepto_col, how="outer", suffixes=("_VENTA", "_COMPRA")).fillna(0)

                    # Gráfico comparativo
                    fig = px.bar(df_comparativa, x=concepto_col, y=["MONTO_CALC_VENTA", "MONTO_CALC_COMPRA"],
                                title=f"Comparativa Compra vs Venta {hoja}",
                                labels={"value": "Importe ($)", "variable": "Tipo"})
                    st.plotly_chart(fig, use_container_width=True)

                    # Mostrar ratio promedio si hay compra
                    if not df_compra.empty:
                        ratio_promedio = df_venta[precio_col].mean() / df_compra[precio_col].mean()
                        st.metric(f"Ratio Precio Venta/Compra {hoja}", f"{ratio_promedio:.2f}")
                    else:
                        st.info("⚠️ No hay datos de compra para calcular ratio")
                else:
                    st.info("⚠️ No hay columnas PRECIO POR KG o CONCEPTO en esta hoja")
>>>>>>> 5324675 (hacienda)
