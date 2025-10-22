import geopandas as gpd
import pandas as pd
import folium
from branca import colormap as cm
from pathlib import Path

def crear_mapa_lotes(geojson_path):
    """
    Crear mapa de lotes a partir de un archivo GeoJSON exportado desde QGIS.
    Muestra todos los productos aplicados, ignorando valores NaN, 'nan', vacíos, 0, NULL, etc.
    """

    geojson_path = Path(geojson_path)
    if not geojson_path.exists():
        raise FileNotFoundError(f"No se encontró el archivo GeoJSON: {geojson_path}")

    gdf = gpd.read_file(str(geojson_path))

    # Asegurar que 'HAS' sea numérico y sin NaN
    gdf["HAS"] = pd.to_numeric(gdf["HAS"], errors="coerce")
    gdf = gdf.dropna(subset=["HAS"])
    if gdf.empty:
        raise ValueError("❌ La capa no tiene valores válidos en la columna 'HAS'.")

    # 🔹 Limpieza más eficiente: convertir todo a string y reemplazar valores vacíos,
    # excepto 'HAS' que debe seguir numérico
    vacios = ["nan", "none", "null", "", "-", "--", "sin dato", "no aplica"]
    for col in gdf.columns:
        if col not in ["geometry", "HAS"]:
            gdf[col] = gdf[col].astype(str).str.strip().str.lower().replace(vacios, pd.NA)  

    # Calcular centro del mapa
    gdf_proj = gdf.to_crs(epsg=3857)
    centroids = gdf_proj.geometry.centroid
    mean_x, mean_y = centroids.x.mean(), centroids.y.mean()
    centroids_geo = gpd.GeoSeries(
        gpd.points_from_xy([mean_x], [mean_y]), crs=3857
    ).to_crs(epsg=4326)
    center_lat, center_lon = centroids_geo.y.iloc[0], centroids_geo.x.iloc[0]

    # Crear mapa base
    m = folium.Map(location=[center_lat, center_lon], zoom_start=15, control_scale=True)

    # Escala de color por hectáreas
    min_val, max_val = gdf["HAS"].min(), gdf["HAS"].max()
    cmap = cm.LinearColormap(['#ffffcc', '#006837'], vmin=min_val, vmax=max_val)

    columnas_basicas = {"geometry", "Lotes", "HAS", "CULTIVO"}

    # Crear polígonos y popups
    for _, row in gdf.iterrows():
        color = cmap(row["HAS"])

        tooltip = folium.Tooltip(
            f"Lote: {row.get('Lotes', 'N/A')}<br>"
            f"Has: {row.get('HAS', 'N/A')}<br>"
            f"Cultivo: {row.get('CULTIVO', 'N/A')}",
            sticky=True
        )

        popup_html = f"<b>Lote:</b> {row.get('Lotes', 'N/A')}<br>"
        popup_html += f"<b>Has:</b> {row.get('HAS', 'N/A')}<br>"
        popup_html += f"<b>Cultivo:</b> {row.get('CULTIVO', 'N/A')}<br><hr>"
        popup_html += "<b>🧪 Productos aplicados:</b><br>"

        productos_html = ""
        for col in gdf.columns:
            if col not in columnas_basicas:
                valor = row.get(col)
                if pd.notna(valor):
                    productos_html += f"{col}: {valor}<br>"

        if productos_html == "":
            productos_html = "<i>Sin productos registrados</i>"

        popup_html += productos_html

        folium.GeoJson(
            row.geometry,
            tooltip=tooltip,
            popup=folium.Popup(popup_html, max_width=300),
            style_function=lambda x, color=color: {
                "fillColor": color,
                "color": "black",
                "weight": 1,
                "fillOpacity": 0.6,
            }
        ).add_to(m)

    cmap.caption = "Hectáreas (HAS)"
    cmap.add_to(m)

    return m
