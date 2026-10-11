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
st.markdown("### Plataforma WebGIS Colaborativa y Alertas Comunitarias - Comuna 4 (Aranjuez)")

# Cargar modelo YOLO
@st.cache_resource
def cargar_modelo():
    return YOLO("yolov8n.pt")

model = cargar_modelo()

CSV_FILE = "barrios_comuna4.csv"

# Cargar base de datos
def cargar_datos_comuna():
    if os.path.exists(CSV_FILE):
        df = pd.read_csv(CSV_FILE)
        if "imagen_base64" not in df.columns:
            df["imagen_base64"] = ""
        if "comentario" not in df.columns:
            df["comentario"] = ""
        return df
    else:
        data = {
            "barrio": ["Aranjuez - Parque Principal", "Campo Valdés"],
            "direccion": ["Parque Principal", "Calle 82"],
            "lat": [6.272100, 6.278540],
            "lon": [-75.557400, -75.559200],
            "categoria": ["🗑️ Acumulación de Basuras", "🗑️ Acumulación de Basuras"],
            "color": ["orange", "orange"],
            "icono": ["trash", "trash"],
            "imagen_base64": ["", ""],
            "comentario": ["Punto crítico histórico", "Contenedores colapsados"]
        }
        df = pd.DataFrame(data)
        df.to_csv(CSV_FILE, index=False)
        return df

df_comuna = cargar_datos_comuna()

opciones_dict = {"Selecciona un barrio o sector de la Comuna 4...": {
    "lat": 6.2730, "lon": -75.5580, "categoria": "General", "color": "blue", "icono": "info-sign"
}}

for index, row in df_comuna.iterrows():
    label = f"{row['barrio']} ({row['categoria']})"
    opciones_dict[label] = {
        "lat": row["lat"],
        "lon": row["lon"],
        "categoria": row["categoria"],
        "color": row["color"],
        "icono": row["icono"]
    }

if "map_key" not in st.session_state:
    st.session_state.map_key = 0

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("🔎 1. Ubicación y Reporte Comunitario")
    
    zona_seleccionada = st.selectbox(
        "Elige el barrio o sector de afectación:",
        options=list(opciones_dict.keys())
    )
    
    info_zona = opciones_dict[zona_seleccionada]
    coordenadas_actuales = [info_zona["lat"], info_zona["lon"]]
    
    if zona_seleccionada != "Selecciona un barrio o sector de la Comuna 4...":
        st.warning(f"📍 **Sector Seleccionado:** {zona_seleccionada}")
    else:
        st.info("Selecciona un sector de la lista para enfocar el mapa WebGIS.")

    st.markdown("---")
    st.subheader("📸 2. Evidencia y Comentarios Ciudadanos")
    
    comentario_usuario = st.text_area("Comentario o descripción detallada del problema:", placeholder="Ej: Hay acumulación de escombros que bloquean el paso peatonal...")
    archivo = st.file_uploader("Sube la fotografía del riesgo:", type=["jpg", "jpeg", "png"])
    
    if archivo is not None:
        imagen = Image.open(archivo)
        st.image(imagen, caption="Fotografía cargada por el usuario", use_container_width=True)
        
        if st.button("🔍 Analizar con IA y Publicar Alerta Global"):
            with st.spinner("Procesando imagen con modelo YOLOv8 y sincronizando base de datos..."):
                resultados = model(imagen, conf=0.05)
                
                res_plotted = resultados[0].plot()
                res_img = Image.fromarray(res_plotted[..., ::-1])
                
                buffered_res = io.BytesIO()
                res_img.save(buffered_res, format="JPEG")
                res_img_str = base64.b64encode(buffered_res.getvalue()).decode()
                
                st.image(res_img, caption="Análisis de IA completado", use_container_width=True)
                
                nuevo_reporte = pd.DataFrame([{
                    "barrio": zona_seleccionada,
                    "direccion": f"Alerta Comunitaria: {zona_seleccionada}",
                    "lat": coordenadas_actuales[0],
                    "lon": coordenadas_actuales[1],
                    "categoria": info_zona["categoria"],
                    "color": "red",
                    "icono": "camera",
                    "imagen_base64": res_img_str,
                    "comentario": comentario_usuario if comentario_usuario else "Sin comentario adicional."
                }])
                
                df_actualizado = pd.concat([df_comuna, nuevo_reporte], ignore_index=True)
                df_actualizado.to_csv(CSV_FILE, index=False)
                
                st.success("✅ ¡Alerta publicada con éxito para toda la comunidad!")
                
                df_comuna = df_actualizado
                st.session_state.map_key += 1
                st.rerun()

    st.markdown("---")
    st.subheader("📞 Directorio de Emergencias Oficiales")
    st.markdown("""
    Si la emergencia requiere atención inmediata de las autoridades, comunícate a las líneas oficiales:
    * **🔥 Bomberos:** `119`[cite: 10]
    * **👮‍♂️ Policía Nacional:** `112`[cite: 10]
    * **🚑 Ambulancias / Urgencias Médicas:** `125`[cite: 10]
    * ** cruz Roja Colombiana:** `132`[cite: 10]
    * **⛑️ Defensa Civil Colombiana:** `144`[cite: 10]
    * **⚠️ Atención de Desastres Nacional (UNGRD):** `111`[cite: 10]
    """)

with col2:
    st.subheader("🗺️ Mapa WebGIS en Tiempo Real (Comuna 4)")
    
    mapa = folium.Map(
        location=coordenadas_actuales,
        zoom_start=15,
        tiles="OpenStreetMap"
    )
    
    for index, row in df_comuna.iterrows():
        img_b64 = str(row.get("imagen_base64", ""))
        comentario_txt = str(row.get("comentario", "Sin comentarios"))
        
        if img_b64 and img_b64 != "nan" and len(img_b64) > 10:
            html_popup = f"""
            <div style="width:220px; font-family: sans-serif;">
                <b style="color: #d9534f;">🚨 Alerta Comunitaria</b><br>
                <b>Sector:</b> {row['barrio']}<br>
                <b>Categoría:</b> {row['categoria']}<br>
                <b>Comentario:</b> {comentario_txt}<br><br>
                <b>Evidencia Fotográfica:</b><br>
                <img src="data:image/jpeg;base64,{img_b64}" width="200px" style="border-radius:6px; margin-top:4px;"/>
            </div>
            """
            popup = folium.Popup(html_popup, max_width=250)
            
            folium.Marker(
                location=[row["lat"], row["lon"]],
                popup=popup,
                tooltip=f"Reporte Ciudadano 📸 - {row['barrio']}",
                icon=folium.Icon(color="red", icon="camera", prefix="fa")
            ).add_to(mapa)
        else:
            folium.Marker(
                location=[row["lat"], row["lon"]],
                popup=f"<b>Sector:</b> {row['barrio']}<br><b>Categoría:</b> {row['categoria']}<br><b>Info:</b> {comentario_txt}",
                tooltip=row['barrio'],
                icon=folium.Icon(color=row["color"], icon=row["icono"])
            ).add_to(mapa)
        
    st_folium(mapa, width=550, height=620, key=f"mapa_{st.session_state.map_key}")