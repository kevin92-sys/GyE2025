from pathlib import Path
import geopandas as gpd
import folium
import branca.colormap as cm
import pandas as pd

def crear_mapa_lotes(geojson_path=None):
    if geojson_path is None:
        base_dir = Path("C:/Users/Kevin/Dropbox/Administracion/2025/FINANZAS 2025") / "datos"
        geojson_path = base_dir / "Nlotes.geojson"

    gdf = gpd.read_file(str(geojson_path))

    # Asegurar que 'HAS' sea numérico y sin NaN
    gdf["HAS"] = pd.to_numeric(gdf["HAS"], errors="coerce")
    gdf = gdf.dropna(subset=["HAS"])
    
    if gdf.empty:
        raise ValueError("❌ La capa no tiene valores válidos en la columna 'HAS'.")

    # Convertir a CRS proyectado para calcular centro del mapa
    gdf_proj = gdf.to_crs(epsg=3857)
    centroids = gdf_proj.geometry.centroid
    mean_x = centroids.x.mean()
    mean_y = centroids.y.mean()

    # Volver a EPSG:4326 para usar en folium
    centroids_geo = gpd.GeoSeries(gpd.points_from_xy([mean_x], [mean_y]), crs=3857).to_crs(epsg=4326)
    center_lat = centroids_geo.y.iloc[0]
    center_lon = centroids_geo.x.iloc[0]

    m = folium.Map(location=[center_lat, center_lon], zoom_start=15, control_scale=True)

    min_val = gdf["HAS"].min()
    max_val = gdf["HAS"].max()
    cmap = cm.LinearColormap(['#ffffcc', '#006837'], vmin=min_val, vmax=max_val)

    for _, row in gdf.iterrows():
        color = cmap(row["HAS"])

        tooltip = folium.Tooltip(
            f"Lote: {row.get('Lotes', 'N/A')}<br>"
            f"Has: {row.get('HAS', 'N/A')}<br>"
            f"Cultivo: {row.get('CULTIVO', 'N/A')}",
            sticky=True
        )

        popup_html = f"""
        <b>Lote:</b> {row.get('Lotes', 'N/A')}<br>
        <b>Has:</b> {row.get('HAS', 'N/A')}<br>
        <b>Cultivo:</b> {row.get('CULTIVO', 'N/A')}<br>
        <b>ROUND:</b> {row.get('ROUND', 'N/A')}<br>
        <b>FULLTEC:</b> {row.get('FULLTEC', 'N/A')}<br>
        <b>2,4D ADVA:</b> {row.get('2,4D ADVA', 'N/A')}<br>
        <b>A35T GOLD:</b> {row.get('A35T GOLD', 'N/A')}<br>
        <b>ACEITE ROC:</b> {row.get('ACEITE ROC', 'N/A')}<br>
        <b>ACURON:</b> {row.get('ACURON', 'N/A')}<br>
        <b>ADENGO:</b> {row.get('ADENGO', 'N/A')}<br>
        <b>BIFENTRIN:</b> {row.get('BIFENTRIN', 'N/A')}<br>
        """

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
