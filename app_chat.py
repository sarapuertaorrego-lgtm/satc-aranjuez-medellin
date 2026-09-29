import streamlit as st
from ultralytics import YOLO
import folium
from streamlit_folium import st_folium
from PIL import Image
import pandas as pd
import base64
import io
import os

# Configuración de página
st.set_page_config(page_title="SAT-C Aranjuez & Medellín - Gestión del Riesgo", layout="wide")

st.title("🚨 Red de Monitoreo Comunitario y Gestión del Riesgo - SAT-C")
st.markdown("### Plataforma WebGIS: Reportes Ciudadanos con Base de Datos Dinámica - Comuna 4")

# Cargar modelo YOLO
@st.cache_resource
def cargar_modelo():
    return YOLO("yolov8n.pt")

model = cargar_modelo()

# Archivo de base de datos CSV
CSV_FILE = "barrios_comuna4.csv"

# Cargar la base de datos de la Comuna 4
def cargar_datos_comuna():
    if os.path.exists(CSV_FILE):
        df = pd.read_csv(CSV_FILE)
        # Asegurar que la columna imagen_base64 exista
        if "imagen_base64" not in df.columns:
            df["imagen_base64"] = ""
        return df
    else:
        # DataFrame por defecto si no existe el archivo
        data = {
            "barrio": ["Aranjuez - Parque Principal", "Campo Valdés"],
            "direccion": ["Parque Principal", "Calle 82"],
            "lat": [6.272100, 6.278540],
            "lon": [-75.557400, -75.559200],
            "categoria": ["🗑️ Acumulación de Basuras", "🗑️ Acumulación de Basuras"],
            "color": ["orange", "orange"],
            "icono": ["trash", "trash"],
            "imagen_base64": ["", ""]
        }
        df = pd.DataFrame(data)
        df.to_csv(CSV_FILE, index=False)
        return df

df_comuna = cargar_datos_comuna()

opciones_dict = {"Selecciona un barrio o sector de la Comuna 4...": {
    "lat": 6.2730, "lon": -75.5580, "categoria": "General", "color": "blue", "icono": "info-sign", "direccion": ""
}}

for index, row in df_comuna.iterrows():
    # Evitar duplicar etiquetas si ya tienen reporte
    label = f"{row['barrio']} ({row['categoria']})"
    opciones_dict[label] = {
        "lat": row["lat"],
        "lon": row["lon"],
        "categoria": row["categoria"],
        "color": row["color"],
        "icono": row["icono"],
        "direccion": row["barrio"]
    }

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
        st.warning(f"📍 **Sector Seleccionado:** {zona_seleccionada}")
    else:
        st.info("Selecciona un barrio de la lista para enfocar el mapa WebGIS.")

    st.markdown("---")
    st.subheader("📸 2. Reporte Comunitario con Evidencia")
    
    archivo = st.file_uploader("Sube la fotografía de la emergencia:", type=["jpg", "jpeg", "png"])
    
    if archivo is not None:
        imagen = Image.open(archivo)
        st.image(imagen, caption="Fotografía cargada por el usuario", use_container_width=True)
        
        if st.button("🔍 Analizar con IA y Guardar en Base de Datos"):
            with st.spinner("Procesando imagen con modelo YOLOv8 y actualizando base de datos..."):
                resultados = model(imagen, conf=0.05)
                
                # Procesar imagen con detecciones de IA
                res_plotted = resultados[0].plot()
                res_img = Image.fromarray(res_plotted[..., ::-1])
                
                # Codificar imagen en Base64
                buffered_res = io.BytesIO()
                res_img.save(buffered_res, format="JPEG")
                res_img_str = base64.b64encode(buffered_res.getvalue()).decode()
                
                st.image(res_img, caption="Análisis de IA completado", use_container_width=True)
                
                # Crear nuevo registro para agregar al CSV
                nuevo_reporte = pd.DataFrame([{
                    "barrio": zona_seleccionada,
                    "direccion": f"Reporte Ciudadano en {zona_seleccionada}",
                    "lat": coordenadas_actuales[0],
                    "lon": coordenadas_actuales[1],
                    "categoria": info_zona["categoria"],
                    "color": "red",
                    "icono": "camera",
                    "imagen_base64": res_img_str
                }])
                
                # Adjuntar al DataFrame existente y guardar en el CSV
                df_actualizado = pd.concat([df_comuna, nuevo_reporte], ignore_index=True)
                df_actualizado.to_csv(CSV_FILE, index=False)
                
                st.success("✅ ¡Alerta registrada, foto guardada en la base de datos y mapa actualizado!")
                
                # Actualizar variable local y refrescar mapa
                df_comuna = df_actualizado
                st.session_state.map_key += 1
                st.rerun()

with col2:
    st.subheader("🗺️ Mapa WebGIS Interactivo con Evidencias Guardadas")
    
    mapa = folium.Map(
        location=coordenadas_actuales,
        zoom_start=15,
        tiles="OpenStreetMap"
    )
    
    # Recorrer todos los registros de la base de datos (CSV)
    for index, row in df_comuna.iterrows():
        # Verificar si el registro tiene una imagen guardada en Base64
        img_b64 = str(row.get("imagen_base64", ""))
        
        if img_b64 and img_b64 != "nan" and len(img_b64) > 10:
            # Si tiene foto guardada, crear un popup interactivo con la imagen
            html_popup = f"""
            <div style="width:210px; font-family: sans-serif;">
                <b style="color: #d9534f;">🚨 Reporte Ciudadano con Foto</b><br>
                <b>Sector:</b> {row['barrio']}<br>
                <b>Categoría:</b> {row['categoria']}<br><br>
                <b>Evidencia Fotográfica (IA):</b><br>
                <img src="data:image/jpeg;base64,{img_b64}" width="190px" style="border-radius:6px; margin-top:4px;"/>
            </div>
            """
            popup = folium.Popup(html_popup, max_width=250)
            
            folium.Marker(
                location=[row["lat"], row["lon"]],
                popup=popup,
                tooltip=f"Reporte con Foto 📸 - {row['barrio']}",
                icon=folium.Icon(color="red", icon="camera", prefix="fa")
            ).add_to(mapa)
        else:
            # Marcador estándar del barrio o sector predefinido
            folium.Marker(
                location=[row["lat"], row["lon"]],
                popup=f"<b>Sector:</b> {row['barrio']}<br><b>Categoría:</b> {row['categoria']}",
                tooltip=row['barrio'],
                icon=folium.Icon(color=row["color"], icon=row["icono"])
            ).add_to(mapa)
        
    st_folium(mapa, width=550, height=560, key=f"mapa_{st.session_state.map_key}")