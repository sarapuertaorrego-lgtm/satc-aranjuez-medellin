import streamlit as st
from ultralytics import YOLO
import folium
from streamlit_folium import st_folium
from PIL import Image
import pandas as pd

# Configuración de página
st.set_page_config(page_title="SAT-C Aranjuez & Medellín - Gestión del Riesgo", layout="wide")

st.title("🚨 Red de Monitoreo Comunitario y Gestión del Riesgo - SAT-C")
st.markdown("### Plataforma WebGIS: Monitoreo Comunitario - Comuna 4 (Aranjuez)")

# Cargar modelo YOLO
@st.cache_resource
def cargar_modelo():
    return YOLO("yolov8n.pt")

model = cargar_modelo()

# Cargar la base de datos de la Comuna 4 desde el CSV
@st.cache_data
def cargar_datos_comuna():
    df = pd.read_csv("barrios_comuna4.csv")
    return df

df_comuna = cargar_datos_comuna()

# Crear un diccionario desplegable a partir del DataFrame
opciones_dict = {"Selecciona un barrio o sector de la Comuna 4...": {
    "lat": 6.2730, "lon": -75.5580, "categoria": "General", "color": "blue", "icono": "info-sign", "direccion": ""
}}

for index, row in df_comuna.iterrows():
    label = f"{row['barrio']} - {row['categoria']}"
    opciones_dict[label] = {
        "lat": row["lat"],
        "lon": row["lon"],
        "categoria": row["categoria"],
        "color": row["color"],
        "icono": row["icono"],
        "direccion": row["direccion"]
    }

if "reportes" not in st.session_state:
    st.session_state.reportes = []

if "map_key" not in st.session_state:
    st.session_state.map_key = 0

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("🔎 1. Selección de Sector en la Comuna 4")
    
    zona_seleccionada = st.selectbox(
        "Elige el barrio o punto crítico:",
        options=list(opciones_dict.keys())
    )
    
    info_zona = opciones_dict[zona_seleccionada]
    coordenadas_actuales = [info_zona["lat"], info_zona["lon"]]
    
    if zona_seleccionada != "Selecciona un barrio o sector de la Comuna 4...":
        st.warning(f"📍 **Sector:** {zona_seleccionada}\n\n**Problemática:** {info_zona['direccion']}")
    else:
        st.info("Selecciona un barrio de la lista para enfocar el mapa WebGIS.")

    st.markdown("---")
    st.subheader("📸 2. Reporte Comunitario con Evidencia")
    
    archivo = st.file_uploader("Sube la fotografía de la emergencia:", type=["jpg", "jpeg", "png"])
    
    if archivo is not None:
        imagen = Image.open(archivo)
        imagen.save("temp.jpg")
        st.image(imagen, caption="Fotografía cargada por el usuario", use_container_width=True)
        
        if st.button("🔍 Analizar con IA y Publicar Alerta"):
            with st.spinner("Procesando imagen con modelo YOLOv8..."):
                resultados = model("temp.jpg", conf=0.05)
                
                resultados[0].save("temp_resultado.jpg")
                st.image("temp_resultado.jpg", caption="Resultados del análisis de IA", use_container_width=True)
                
                st.success("✅ ¡Alerta registrada e integrada exitosamente en el mapa!")
                
                st.session_state.reportes.append({
                    "direccion": zona_seleccionada,
                    "lat": coordenadas_actuales[0],
                    "lon": coordenadas_actuales[1],
                    "categoria": info_zona["categoria"],
                    "color": info_zona["color"]
                })
                st.session_state.map_key += 1

with col2:
    st.subheader("🗺️ Mapa WebGIS Interactivo (Comuna 4)")
    
    mapa = folium.Map(
        location=coordenadas_actuales,
        zoom_start=15,
        tiles="OpenStreetMap"
    )
    
    # Marcador de la zona seleccionada en el menú
    if zona_seleccionada != "Selecciona un barrio o sector de la Comuna 4...":
        folium.Marker(
            location=coordenadas_actuales,
            popup=f"<b>Sector:</b> {zona_seleccionada}<br><b>Detalle:</b> {info_zona['direccion']}",
            tooltip="Punto Seleccionado",
            icon=folium.Icon(color=info_zona["color"], icon=info_zona["icono"])
        ).add_to(mapa)
        
    # Opcional: Mostrar todos los puntos predefinidos del CSV en el mapa con su respectivo color
    for index, row in df_comuna.iterrows():
        folium.Marker(
            location=[row["lat"], row["lon"]],
            popup=f"<b>Barrio:</b> {row['barrio']}<br><b>Tipo:</b> {row['categoria']}<br><b>Detalle:</b> {row['direccion']}",
            tooltip=row['barrio'],
            icon=folium.Icon(color=row["color"], icon=row["icono"])
        ).add_to(mapa)
    
    # Renderizar reportes dinámicos hechos por usuarios
    for r in st.session_state.reportes:
        folium.Marker(
            location=[r["lat"], r["lon"]],
            popup=f"<b>Reporte Ciudadano:</b> {r['direccion']}",
            tooltip="Alerta Ciudadana",
            icon=folium.Icon(color=r["color"], icon="warning-sign")
        ).add_to(mapa)
        
    st_folium(mapa, width=550, height=560, key=f"mapa_{st.session_state.map_key}")