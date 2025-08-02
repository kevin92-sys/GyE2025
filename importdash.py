import geopandas as gpd
import folium
import matplotlib.pyplot as plt
from matplotlib import colormaps
from folium.plugins import MiniMap
from branca.element import Element
import numpy as np

def crear_mapa_lotes(geojson_path):
    # Leer GeoJSON
    gdf = gpd.read_file(geojson_path)

    # Asegurar EPSG:4326
    if gdf.crs.to_string() != "EPSG:4326":
        gdf = gdf.to_crs(epsg=4326)

    # Crear mapa base
    m = folium.Map(zoom_start=14, tiles="CartoDB positron")

    # Centrar a los lotes usando bounds
    bounds = gdf.total_bounds
    m.fit_bounds([[bounds[1], bounds[0]], [bounds[3], bounds[2]]])

    # Agregar minimap
    minimap = MiniMap(toggle_display=True, position="bottomright")
    m.add_child(minimap)

    # Configurar colormap
    cmap = colormaps["YlGn"]
    norm = plt.Normalize(gdf["HAS"].min(), gdf["HAS"].max())

    # Crear leyenda dinámica
    legend_colors = []
    steps = 5
    has_min, has_max = gdf["HAS"].min(), gdf["HAS"].max()
    values = np.linspace(has_min, has_max, steps)
    for v in values:
        color = "#{:02x}{:02x}{:02x}".format(*[int(255 * c) for c in cmap(norm(v))[:3]])
        legend_colors.append((round(v, 1), color))

    legend_html = """
    <div style="
        position: fixed; 
        bottom: 50px; 
        left: 50px; 
        width: 200px; 
        background-color: white; 
        border: 2px solid grey; 
        padding: 10px; 
        z-index: 9999; 
        border-radius: 5px; 
        font-size: 14px;
        font-family: Arial, sans-serif;
        color: black;
    ">
    <b>🌱 Hectáreas por lote</b><br><br>
    """
    for v, c in legend_colors:
        legend_html += f"""
        <div style='display: flex; align-items: center; margin-bottom: 5px;'>
            <div style='width: 30px; height: 15px; background-color: {c}; margin-right: 10px; border: 1px solid #555;'></div>
            <span>≥ {v}</span>
        </div>
        """
    legend_html += "</div>"

    m.get_root().html.add_child(Element(legend_html))

    # Agregar polígonos con tooltip y popup
    for _, row in gdf.iterrows():
        color = "#{:02x}{:02x}{:02x}".format(*[int(255 * c) for c in cmap(norm(row["HAS"]))[:3]])
        tooltip = f"Lote: {row['Lotes']} - HAS: {row['HAS']}"
        popup_html = f"""
        <b>Lote:</b> {row['Lotes']}<br>
        <b>Has:</b> {row['HAS']}<br>
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

    return m


