import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import timedelta

def mostrar_gantt():
    # Lista de tareas
    tareas = [
        {"tarea": "1+9", "inicio": "2024-11-14", "fin": "2025-05-02", "cultivo": "SOJA", "has": 230},
        {"tarea": "1+9", "inicio": "2023-11-10", "fin": "2024-04-09", "cultivo": "SOJA", "has": 230},
        {"tarea": "2",   "inicio": "2023-08-20", "fin": "2024-02-02", "cultivo": "MANI", "has": 34},
        {"tarea": "2",   "inicio": "2024-11-10", "fin": "2025-05-02", "cultivo": "MAIZ", "has": 34},
        {"tarea": "3L",  "inicio": "2023-11-14", "fin": "2024-04-20", "cultivo": "MAIZ", "has": 23},
        {"tarea": "3L",  "inicio": "2024-04-22", "fin": "2024-11-10", "cultivo": "ALFALFA", "has": 23},
        {"tarea": "3L",  "inicio": "2024-11-14", "fin": "2025-05-02", "cultivo": "SOJA", "has": 23},
        {"tarea": "3B",  "inicio": "2023-08-20", "fin": "2024-04-10", "cultivo": "ALFALFA", "has": 33},
        {"tarea": "3B",  "inicio": "2024-04-15", "fin": "2025-11-02", "cultivo": "ALFALFA", "has": 33},
        {"tarea": "4L",  "inicio": "2023-11-14", "fin": "2024-05-02", "cultivo": "MAIZ", "has": 12},
        {"tarea": "4L",  "inicio": "2024-05-14", "fin": "2024-11-13", "cultivo": "ALFALFA", "has": 12},
        {"tarea": "4L",  "inicio": "2024-11-14", "fin": "2025-05-02", "cultivo": "SOJA", "has": 12},
        {"tarea": "4B",  "inicio": "2023-04-15", "fin": "2024-04-25", "cultivo": "ALFALFA", "has": 24},
        {"tarea": "4B",  "inicio": "2024-05-02", "fin": "2024-12-02", "cultivo": "ALFALFA", "has": 24},
        {"tarea": "4B",  "inicio": "2024-11-14", "fin": "2025-04-20", "cultivo": "MAIZ", "has": 24},
        {"tarea": "5N",  "inicio": "2023-11-10", "fin": "2024-03-22", "cultivo": "MAIZ", "has": 26},
        {"tarea": "5N",  "inicio": "2024-11-25", "fin": "2025-04-11", "cultivo": "MAIZ", "has": 26},
        {"tarea": "5N",  "inicio": "2025-04-12", "fin": "2026-04-02", "cultivo": "ALFALFA", "has": 26},
        {"tarea": "5S",  "inicio": "2023-11-10", "fin": "2024-03-22", "cultivo": "MAIZ", "has": 26},
        {"tarea": "5S",  "inicio": "2024-03-25", "fin": "2025-05-02", "cultivo": "ALFALFA", "has": 26},
        {"tarea": "6",   "inicio": "2023-11-14", "fin": "2024-05-02", "cultivo": "MAIZ", "has": 30},
        {"tarea": "6",   "inicio": "2024-11-14", "fin": "2025-05-02", "cultivo": "SOJA", "has": 30},
        {"tarea": "7",   "inicio": "2023-08-15", "fin": "2024-02-02", "cultivo": "MANI", "has": 52},
        {"tarea": "7",   "inicio": "2024-11-10", "fin": "2025-04-26", "cultivo": "MAIZ", "has": 52},
        {"tarea": "8",   "inicio": "2023-11-14", "fin": "2024-04-02", "cultivo": "MAIZ", "has": 52},
        {"tarea": "8",   "inicio": "2024-11-14", "fin": "2025-05-02", "cultivo": "SOJA", "has": 52},
        {"tarea": "10",  "inicio": "2023-11-14", "fin": "2024-04-02", "cultivo": "MAIZ", "has": 7},
        {"tarea": "10",  "inicio": "2024-11-14", "fin": "2025-05-02", "cultivo": "SOJA", "has": 7}
    ]
    
    df = pd.DataFrame(tareas)
    df["inicio"] = pd.to_datetime(df["inicio"])
    df["fin"] = pd.to_datetime(df["fin"])

    colores_cultivo = {
        "SOJA": "#a1d99b",
        "MAIZ": "#fdd835",
        "ALFALFA": "#b5f644",
        "MANI": "#4c7407",
    }

    # --- Detectar solapamientos ---
    df = df.sort_values(by=["tarea", "inicio"])
    df["solapado"] = False
    for lote in df["tarea"].unique():
        df_lote = df[df["tarea"] == lote]
        for i in range(len(df_lote) - 1):
            if df_lote.iloc[i]["fin"] >= df_lote.iloc[i + 1]["inicio"]:
                df.loc[df_lote.index[i + 1], "solapado"] = True

    # --- Crear gráfico ---
    fig = go.Figure()
    cultivos_mostrados = set()  # Para la leyenda

    for _, fila in df.iterrows():
        color = colores_cultivo.get(fila["cultivo"], "#cccccc")
        opacity = 0.4 if fila["solapado"] else 1.0
        mostrar_leyenda = False
        if fila["cultivo"] not in cultivos_mostrados:
            mostrar_leyenda = True
            cultivos_mostrados.add(fila["cultivo"])

        fig.add_trace(go.Scatter(
            x=[fila["inicio"], fila["fin"]],
            y=[fila["tarea"], fila["tarea"]],
            mode="lines",
            line=dict(color=color, width=20),
            opacity=opacity,
            hoverinfo="text",
            hovertext=f"{fila['tarea']} - {fila['cultivo']}<br>{fila['inicio'].date()} → {fila['fin'].date()}",
            name=fila["cultivo"] if mostrar_leyenda else None,  # <-- Nombre de la leyenda solo una vez
            showlegend=mostrar_leyenda
        ))

    fig.update_layout(
        xaxis_title="Fecha",
        yaxis_title="Lote",
        xaxis=dict(type="date"),
        height=400 + 30 * len(df["tarea"].unique()),
        margin=dict(l=40, r=40, t=60, b=30)
    )

    fig.update_yaxes(autorange="reversed")

    st.plotly_chart(fig, use_container_width=True, key="gantt_visible")


if __name__ == "__main__":
    st.title("Gantt por Lote y Cultivo (barras visibles)")
    mostrar_gantt()