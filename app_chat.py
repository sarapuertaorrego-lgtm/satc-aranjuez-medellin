import streamlit as st
from ultralytics import YOLO
import folium
from streamlit_folium import st_folium
from PIL import Image
import pandas as pd

# Configuración de página
st.set_page_config(page_title="SAT-C Aranjuez & Medellín", layout="wide")

st.title("🚨 Red de Monitoreo Comunitario y Gestión del Riesgo - SAT-C")
st.write("Plataforma WebGIS comunitaria de alerta temprana (Gratuita y Colaborativa)")

# Cargar modelo YOLO
@st.cache_resource
def cargar_modelo():
    return YOLO("yolov8n.pt")

model = cargar_modelo()

# Base de datos local de puntos clave (Puedes sincronizar esto con Google Sheets fácilmente)
puntos_referencia = {
    "Selecciona o busca una ubicación...": [6.2730, -75.5580],
    "Carrera 54 # 96A-27 (Sector Aranjuez - Comuna 4)": [6.289917, -75.562519],
    "Calle 82 # 50A-27 (Campo Valdés)": [6.278540, -75.559200],
    "Parque de Aranjuez": [6.272100, -75.557400],
    "Sector La Quiebra / Quebrada La Rosa": [6.288500, -75.561000],
    "Cra 51 con Cl 94 (Zona Alta Aranjuez)": [6.285200, -75.559800]
}

if "reportes" not in st.session_state:
    st.session_state.reportes = []

if "map_key" not in st.session_state:
    st.session_state.map_key = 0

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("🔎 1. Selección de Ubicación en Medellín")
    
    # Selector desplegable infalible para direcciones comunitarias
    direccion_seleccionada = st.selectbox(
        "Elige la dirección o sector del reporte:",
        options=list(puntos_referencia.keys())
    )
    
    # Obtener coordenadas automáticas de la opción elegida
    coordenadas_actuales = puntos_referencia[direccion_seleccionada]
    
    st.info(f"📍 **Ubicación activa:** {direccion_seleccionada}")

    st.markdown("---")
    st.subheader("📸 2. Reportar Riesgo con Fotografía")
    
    archivo = st.file_uploader("Sube una foto del punto crítico:", type=["jpg", "jpeg", "png"])
    
    if archivo is not None:
        imagen = Image.open(archivo)
        imagen.save("temp.jpg")
        st.image(imagen, caption="Fotografía cargada por la comunidad", use_container_width=True)
        
        if st.button("🔍 Analizar Fotografía con IA y Guardar Alerta"):
            with st.spinner("Escaneando terreno con YOLOv8..."):
                resultados = model("temp.jpg", conf=0.05)
                
                resultados[0].save("temp_resultado.jpg")
                st.image("temp_resultado.jpg", caption="Resultado del Escaneo IA", use_container_width=True)
                
                estado = "ALERTA DE RIESGO / OBSTRUCCIÓN"
                color = "red"
                
                st.error(f"⚠️ **Punto registrado con éxito en:** {direccion_seleccionada}")
                
                # Guardar en la lista de reportes de la sesión
                st.session_state.reportes.append({
                    "direccion": direccion_seleccionada,
                    "lat": coordenadas_actuales[0],
                    "lon": coordenadas_actuales[1],
                    "estado": estado,
                    "color": color
                })
                st.session_state.map_key += 1

with col2:
    st.subheader("🗺️ Mapa WebGIS Interactivo")
    
    # Crear el mapa centrado en la ubicación seleccionada
    mapa = folium.Map(
        location=coordenadas_actuales,
        zoom_start=17,
        tiles="OpenStreetMap"
    )
    
    # Marcador de la ubicación seleccionada actualmente
    folium.Marker(
        location=coordenadas_actuales,
        popup=f"<b>Seleccionado:</b><br>{direccion_seleccionada}",
        tooltip="Ubicación del Reporte",
        icon=folium.Icon(color="blue", icon="info-sign")
    ).add_to(mapa)
    
    # Dibujar todos los reportes acumulados de la comunidad
    for r in st.session_state.reportes:
        folium.Marker(
            location=[r["lat"], r["lon"]],
            popup=f"<b>Lugar:</b> {r['direccion']}<br><b>Estado:</b> {r['estado']}",
            tooltip=r['direccion'],
            icon=folium.Icon(color=r["color"], icon="warning-sign")
        ).add_to(mapa)
        
    st_folium(mapa, width=550, height=560, key=f"mapa_{st.session_state.map_key}")