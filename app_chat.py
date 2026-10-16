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
st.markdown("### Plataforma WebGIS Interactiva - Comuna 4 (Aranjuez)")

# Cargar modelo YOLO
@st.cache_resource
def cargar_modelo():
    return YOLO("yolov8n.pt")

model = cargar_modelo()

CSV_FILE = "barrios_comuna4.csv"

# Cargar base de datos con persistencia en CSV
def cargar_datos_comuna():
    if os.path.exists(CSV_FILE):
        df = pd.read_csv(CSV_FILE)
        if "imagen_base64" not in df.columns:
            df["imagen_base64"] = ""
        if "comentario" not in df.columns:
            df["comentario"] = ""
        return df
    else:
        # Fallback de emergencia si no encuentra el archivo
        data = {
            "barrio": ["Aranjuez"],
            "direccion": ["Parque Principal"],
            "lat": [6.272100],
            "lon": [-75.557400],
            "categoria": ["🗑️ Acumulación de Basuras"],
            "color": ["orange"],
            "icono": ["trash"],
            "imagen_base64": [""],
            "comentario": ["Punto crítico inicial"]
        }
        df = pd.DataFrame(data)
        df.to_csv(CSV_FILE, index=False)
        return df

df_comuna = cargar_datos_comuna()

if "map_key" not in st.session_state:
    st.session_state.map_key = 0

# --- DASHBOARD DE MÉTRICAS SUPERIOR (Calculado directo del CSV) ---
total_puntos = len(df_comuna)
total_basura = len(df_comuna[df_comuna['categoria'].str.contains("Basuras", na=False)])
total_inundacion = len(df_comuna[df_comuna['categoria'].str.contains("Inundación", na=False)])
total_deslizamiento = len(df_comuna[df_comuna['categoria'].str.contains("Deslizamiento", na=False)])

st.markdown("---")
m1, m2, m3, m4 = st.columns(4)
m1.metric("📊 Total Puntos en Comuna 4", total_puntos)
m2.metric("🗑️ Alertas de Basuras", total_basura)
m3.metric("🌊 Alertas de Inundación", total_inundacion)
m4.metric("⛰️ Alertas de Deslizamiento", total_deslizamiento)
st.markdown("---")

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("🔎 1. Registro de Ubicación y Riesgo")
    
    direccion_usuario = st.text_input("Dirección o sector exacto de la emergencia:", placeholder="Ej: Calle 81 # 50-22, Sector La Quiebra")
    
    categoria_riesgo = st.selectbox(
        "Selecciona el tipo de riesgo identificado:",
        options=[
            "🗑️ Acumulación de Basuras",
            "🌊 Inundación Frecuente / Riesgo Hídrico",
            "⛰️ Deslizamiento de Tierra / Talud"
        ]
    )
    
    if "Basuras" in categoria_riesgo:
        color_r = "orange"
        icono_r = "trash"
    elif "Inundación" in categoria_riesgo:
        color_r = "cadetblue"
        icono_r = "tint"
    else:
        color_r = "red"
        icono_r = "warning-sign"

    st.markdown("---")
    st.subheader("📸 2. Evidencia y Comentarios Ciudadanos")
    
    comentario_usuario = st.text_area("Comentario o detalles adicionales:", placeholder="Describa brevemente la situación observada...")
    archivo = st.file_uploader("Sube la fotografía del riesgo:", type=["jpg", "jpeg", "png"])
    
    if archivo is not None:
        imagen = Image.open(archivo)
        st.image(imagen, caption="Fotografía cargada por el usuario", use_container_width=True)
        
        if st.button("🔍 Analizar con IA y Publicar Reporte"):
            if not direccion_usuario.strip():
                st.warning("⚠️ Por favor ingresa la dirección o ubicación exacta antes de publicar.")
            else:
                with st.spinner("Procesando imagen con IA y guardando en la base de datos..."):
                    resultados = model(imagen, conf=0.05)
                    
                    res_plotted = resultados[0].plot()
                    res_img = Image.fromarray(res_plotted[..., ::-1])
                    
                    buffered_res = io.BytesIO()
                    res_img.save(buffered_res, format="JPEG")
                    res_img_str = base64.b64encode(buffered_res.getvalue()).decode()
                    
                    st.image(res_img, caption="Análisis de IA completado", use_container_width=True)
                    
                    # Coordenadas base en la Comuna 4
                    lat_base = 6.2730
                    lon_base = -75.5580
                    
                    # Crear nuevo registro e insertarlo directamente en el DataFrame y CSV
                    nuevo_reporte = pd.DataFrame([{
                        "barrio": direccion_usuario,
                        "direccion": direccion_usuario,
                        "lat": lat_base,
                        "lon": lon_base,
                        "categoria": categoria_riesgo,
                        "color": color_r,
                        "icono": "camera",
                        "imagen_base64": res_img_str,
                        "comentario": comentario_usuario if comentario_usuario else "Sin comentario adicional."
                    }])
                    
                    df_actualizado = pd.concat([df_comuna, nuevo_reporte], ignore_index=True)
                    df_actualizado.to_csv(CSV_FILE, index=False)
                    
                    st.success("✅ ¡Reporte publicado con éxito y guardado permanentemente en el sistema!")
                    
                    st.session_state.map_key += 1
                    st.rerun()

    st.markdown("---")
    st.subheader("📞 Directorio de Emergencias Oficiales")
    st.markdown("Haz clic sobre cualquier opción para **llamar directamente** desde tu dispositivo:")
    st.markdown("- 🔥 **Bomberos (119):** [Llamar 119](tel:119)")
    st.markdown("- 👮‍♂️ **Policía Nacional (112):** [Llamar 112](tel:112)")
    st.markdown("- 🚑 **Ambulancias / Urgencias (125):** [Llamar 125](tel:125)")
    st.markdown("- 🔴 **Cruz Roja (132):** [Llamar 132](tel:132)")
    st.markdown("- ⛑️ **Defensa Civil (144):** [Llamar 144](tel:144)")
    st.markdown("- ⚠️ **UNGRD (111):** [Llamar 111](tel:111)")

with col2:
    st.subheader("🗺️ Mapa WebGIS Interactivo con Filtros Dinámicos")
    
    # --- FILTROS DINÁMICOS POR CAPAS ---
    st.markdown("**Filtrar capas en el mapa:**")
    f_col1, f_col2, f_col3 = st.columns(3)
    ver_basura = f_col1.checkbox("🗑️ Basuras", value=True)
    ver_inundacion = f_col2.checkbox("🌊 Inundaciones", value=True)
    ver_deslizamiento = f_col3.checkbox("⛰️ Deslizamientos", value=True)
    
    mapa = folium.Map(
        location=[6.2730, -75.5580],
        zoom_start=14,
        tiles="OpenStreetMap"
    )
    
    # Recorrer todos los puntos de la base de datos (tanto barrios oficiales como reportes ciudadanos)
    for index, row in df_comuna.iterrows():
        cat = str(row.get("categoria", ""))
        img_b64 = str(row.get("imagen_base64", ""))
        barrio_txt = str(row.get("barrio", "Ubicación"))
        comentario_txt = str(row.get("comentario", ""))
        
        # Evaluar filtros
        mostrar = False
        if "Basuras" in cat and ver_basura:
            mostrar = True
        elif "Inundación" in cat and ver_inundacion:
            mostrar = True
        elif "Deslizamiento" in cat and ver_deslizamiento:
            mostrar = True
            
        if mostrar:
            # Si tiene foto guardada en base64, mostrar marcador rojo con camarita 📸
            if img_b64 and img_b64 != "nan" and len(img_b64) > 10:
                html_popup = f"""
                <div style="width:220px; font-family: sans-serif;">
                    <b style="color: #d9534f;">🚨 Alerta Comuna 4</b><br>
                    <b>Ubicación:</b> {barrio_txt}<br>
                    <b>Categoría:</b> {cat}<br>
                    <b>Comentario:</b> {comentario_txt}<br><br>
                    <b>Evidencia Fotográfica:</b><br>
                    <img src="data:image/jpeg;base64,{img_b64}" width="200px" style="border-radius:6px; margin-top:4px;"/>
                </div>
                """
                popup = folium.Popup(html_popup, max_width=250)
                
                folium.Marker(
                    location=[row["lat"], row["lon"]],
                    popup=popup,
                    tooltip=f"Reporte Ciudadano 📸 - {barrio_txt}",
                    icon=folium.Icon(color="red", icon="camera", prefix="fa")
                ).add_to(mapa)
            else:
                # Marcador institucional del barrio oficial
                folium.Marker(
                    location=[row["lat"], row["lon"]],
                    popup=f"<b>Barrio / Sector:</b> {barrio_txt}<br><b>Categoría:</b> {cat}<br><b>Diagnóstico:</b> {comentario_txt}",
                    tooltip=barrio_txt,
                    icon=folium.Icon(color=row["color"], icon=row["icono"])
                ).add_to(mapa)
        
    st_folium(mapa, width=550, height=580, key=f"mapa_{st.session_state.map_key}") 