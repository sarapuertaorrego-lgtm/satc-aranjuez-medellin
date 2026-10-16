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
st.markdown("### Plataforma WebGIS Colaborativa - Comuna 4 (Aranjuez)")

# Cargar modelo YOLO
@st.cache_resource
def cargar_modelo():
    return YOLO("yolov8n.pt")

model = cargar_modelo()

CSV_FILE = "barrios_comuna4.csv"

# Inicializar estado de sesión para reportes persistentes
if "reportes_activos" not in st.session_state:
    st.session_state.reportes_activos = []

# Cargar base de datos inicial y sincronizar con la sesión
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
            "direccion": ["Parque Principal de Aranjuez", "Calle 82"],
            "lat": [6.272100, 6.278540],
            "lon": [-75.557400, -75.559200],
            "categoria": ["🗑️ Acumulación de Basuras", "🗑️ Acumulación de Basuras"],
            "color": ["orange", "orange"],
            "icono": ["trash", "trash"],
            "imagen_base64": ["", ""],
            "comentario": ["Punto crítico histórico de contenedores", "Acumulación recurrente de residuos"]
        }
        df = pd.DataFrame(data)
        df.to_csv(CSV_FILE, index=False)
        return df

df_comuna = cargar_datos_comuna()

# Sancionar los reportes del CSV a la sesión si existen imágenes guardadas
if len(st.session_state.reportes_activos) == 0:
    for _, row in df_comuna.iterrows():
        img_b64 = str(row.get("imagen_base64", ""))
        if img_b64 and img_b64 != "nan" and len(img_b64) > 10:
            st.session_state.reportes_activos.append({
                "barrio": row["barrio"],
                "lat": row["lat"],
                "lon": row["lon"],
                "categoria": row["categoria"],
                "imagen_base64": img_b64,
                "comentario": row.get("comentario", "Sin comentarios")
            })

if "map_key" not in st.session_state:
    st.session_state.map_key = 0

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
                with st.spinner("Procesando imagen con IA y actualizando registro..."):
                    resultados = model(imagen, conf=0.05)
                    
                    res_plotted = resultados[0].plot()
                    res_img = Image.fromarray(res_plotted[..., ::-1])
                    
                    buffered_res = io.BytesIO()
                    res_img.save(buffered_res, format="JPEG")
                    res_img_str = base64.b64encode(buffered_res.getvalue()).decode()
                    
                    st.image(res_img, caption="Análisis de IA completado", use_container_width=True)
                    
                    # Coordenadas base en Comuna 4 para ubicar el reporte
                    lat_base = 6.2730
                    lon_base = -75.5580
                    
                    # Agregar al estado de sesión persistente
                    nuevo_reporte_dict = {
                        "barrio": direccion_usuario,
                        "lat": lat_base,
                        "lon": lon_base,
                        "categoria": categoria_riesgo,
                        "imagen_base64": res_img_str,
                        "comentario": comentario_usuario if comentario_usuario else "Sin comentario adicional."
                    }
                    st.session_state.reportes_activos.append(nuevo_reporte_dict)
                    
                    # Guardar también en el CSV físico
                    nuevo_reporte_df = pd.DataFrame([{
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
                    
                    df_actualizado = pd.concat([df_comuna, nuevo_reporte_df], ignore_index=True)
                    df_actualizado.to_csv(CSV_FILE, index=False)
                    
                    st.success("✅ ¡Reporte publicado con éxito y guardado en el sistema!")
                    
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
    st.subheader("🗺️ Mapa WebGIS en Tiempo Real (Comuna 4)")
    
    mapa = folium.Map(
        location=[6.2730, -75.5580],
        zoom_start=15,
        tiles="OpenStreetMap"
    )
    
    # 1. Dibujar los puntos predefinidos base del CSV que no tienen foto de reporte ciudadano
    for index, row in df_comuna.iterrows():
        img_b64 = str(row.get("imagen_base64", ""))
        if not img_b64 or img_b64 == "nan" or len(img_b64) <= 10:
            folium.Marker(
                location=[row["lat"], row["lon"]],
                popup=f"<b>Ubicación:</b> {row['barrio']}<br><b>Categoría:</b> {row['categoria']}<br><b>Info:</b> {row.get('comentario', '')}",
                tooltip=row['barrio'],
                icon=folium.Icon(color=row["color"], icon=row["icono"])
            ).add_to(mapa)

    # 2. Dibujar todos los reportes activos almacenados en la sesión (con su respectiva foto y camarita 📸)
    for r in st.session_state.reportes_activos:
        img_b64 = r["imagen_base64"]
        html_popup = f"""
        <div style="width:220px; font-family: sans-serif;">
            <b style="color: #d9534f;">🚨 Alerta Comuna 4</b><br>
            <b>Ubicación:</b> {r['barrio']}<br>
            <b>Categoría:</b> {r['categoria']}<br>
            <b>Comentario:</b> {r['comentario']}<br><br>
            <b>Evidencia Fotográfica:</b><br>
            <img src="data:image/jpeg;base64,{img_b64}" width="200px" style="border-radius:6px; margin-top:4px;"/>
        </div>
        """
        popup = folium.Popup(html_popup, max_width=250)
        
        folium.Marker(
            location=[r["lat"], r["lon"]],
            popup=popup,
            tooltip=f"Reporte Ciudadano 📸 - {r['barrio']}",
            icon=folium.Icon(color="red", icon="camera", prefix="fa")
        ).add_to(mapa)
        
    st_folium(mapa, width=550, height=620, key=f"mapa_{st.session_state.map_key}")