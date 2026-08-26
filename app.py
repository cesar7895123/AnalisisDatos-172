import os
import json
import streamlit as st
import pandas as pd
import plotly.express as px
from groq import Groq

# Configuración de la página
st.set_page_config(
    page_title="Dashboard de Accidentes & IA Groq",
    page_icon="🚗",
    layout="wide"
)

# Estilo personalizado CSS
st.markdown("""
    <style>
    .main {
        background-color: #f8f9fa;
    }
    .stMetric {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .report-card {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #00a86b;
        margin-bottom: 15px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .chat-message {
        padding: 12px;
        border-radius: 8px;
        margin-bottom: 10px;
        display: flex;
        gap: 10px;
    }
    .chat-message.user {
        background-color: #e3f2fd;
        justify-content: flex-end;
    }
    .chat-message.assistant {
        background-color: #f5f5f5;
        justify-content: flex-start;
    }
    .chat-message-content {
        max-width: 80%;
        padding: 10px 15px;
        border-radius: 6px;
    }
    .chat-message.user .chat-message-content {
        background-color: #2196F3;
        color: white;
    }
    .chat-message.assistant .chat-message-content {
        background-color: #e0e0e0;
        color: black;
    }
    </style>
""", unsafe_allow_html=True)

# ---------------------------
# Sección: Información del Proyecto
# ---------------------------
st.sidebar.header("📌 Información del Proyecto")
project_name = st.sidebar.text_input("🏷️ Nombre del proyecto", value="Dashboard Analítico de Accidentes de Tránsito + IA (Groq)")
team_members = st.sidebar.text_area("👥 Integrantes del equipo", placeholder="Ej: Juan Pérez - Analista\nMaría Ruiz - Ingeniera de Datos")
project_description = st.sidebar.text_area("📝 Descripción general", placeholder="Breve descripción del proyecto")
problem_statement = st.sidebar.text_area("🎯 Problema que resuelve", placeholder="Qué problema aborda el proyecto")
technologies_default = ["Python", "Streamlit", "Pandas", "Plotly", "Groq", "OpenAI", "Docker", "Git"]
technologies_selected = st.sidebar.multiselect("🛠️ Tecnologías utilizadas", options=technologies_default, default=["Python", "Streamlit", "Pandas", "Plotly"])
technologies_custom = st.sidebar.text_input("Añadir tecnologías (separadas por comas)")
technologies = technologies_selected + [t.strip() for t in technologies_custom.split(",") if t.strip()]

# Mostrar resumen del proyecto en la cabecera principal
st.title(f"🚗 {project_name if project_name else 'Dashboard Analítico de Accidentes de Tránsito'}")
st.markdown(project_description if project_description else "Visualización interactiva e informe generado por IA (`openai/gpt-oss-120b`).")

st.markdown(f"""
<div class="report-card">
  <h3>📌 {project_name}</h3>
  <p><strong>👥 Integrantes:</strong><br>{team_members.replace('\n','<br>') if team_members else 'No especificado'}</p>
  <p><strong>📝 Descripción general:</strong> {project_description if project_description else 'No especificado'}</p>
  <p><strong>🎯 Problema que resuelve:</strong> {problem_statement if problem_statement else 'No especificado'}</p>
  <p><strong>🛠️ Tecnologías utilizadas:</strong> {', '.join(technologies) if technologies else 'No especificado'}</p>
</div>
""", unsafe_allow_html=True)

# Carga de datos con caché
@st.cache_data
def load_data(file):
    df = pd.read_csv(file)
    
    # Conversión de EDAD_VEHICULO
    if "EDAD_VEHICULO" in df.columns:
        df["EDAD_VEHICULO"] = pd.to_numeric(df["EDAD_VEHICULO"], errors='coerce')
        
    # Conversión de FECHA_ACCIDENTE a datetime
    if "FECHA_ACCIDENTE" in df.columns:
        df["FECHA_ACCIDENTE"] = pd.to_datetime(df["FECHA_ACCIDENTE"], errors='coerce')
        
    return df

# Función para generar informe con Groq
def generar_informe_groq(groq_api_key, datos_resumen, num_insights):
    client = Groq(api_key=groq_api_key)
    
    system_prompt = (
        "Eres un experto en seguridad vial y análisis analítico de datos de accidentes de tránsito. "
        "Tu tarea es analizar los datos agregados proporcionados y generar un informe ejecutivo claro, profesional y accionable. "
        "Debes responder ÚNICAMENTE en formato JSON."
    )
    
    user_prompt = f"""
    Analiza el siguiente resumen de datos de accidentes de tránsito:
    
    --- RESUMEN DE DATOS ---
    {json.dumps(datos_resumen, ensure_ascii=False, indent=2)}
    --- FIN DE DATOS ---
    
    Instrucciones:
    1. Genera un resumen ejecutivo general de la situación analizada.
    2. Genera EXACTAMENTE {num_insights} insights clave fundamentados en los datos.
    3. Para cada insight, incluye un título, la descripción detallada del hallazgo y una recomendación o medida preventiva específica.
    
    Responde strictly en formato JSON con la siguiente estructura:
    {{
      "resumen_ejecutivo": "Texto descriptivo del resumen...",
      "insights": [
        {{
          "id": 1,
          "titulo": "Título del insight",
          "hallazgo": "Explicación del hallazgo",
          "recomendacion": "Medida o acción recomendada"
        }}
      ]
    }}
    """

    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.2,
        response_format={"type": "json_object"}
    )
    
    return json.loads(response.choices[0].message.content)

# Función para chat interactivo sobre datos
def chat_con_datos(groq_api_key, pregunta_usuario, datos_resumen):
    """
    Realiza una consulta al modelo Groq sobre los datos filtrados.
    """
    client = Groq(api_key=groq_api_key)
    
    system_prompt = (
        "Eres un experto analista de datos de accidentes de tránsito. "
        "Tienes acceso a un resumen de datos sobre accidentes filtrados. "
        "Responde de manera clara, concisa y fundamentada en los datos proporcionados. "
        "Si la pregunta no está relacionada con los datos, indícalo amablemente."
    )
    
    context_prompt = f"""
    Contexto - Datos disponibles para análisis:
    {json.dumps(datos_resumen, ensure_ascii=False, indent=2)}
    
    Pregunta del usuario: {pregunta_usuario}
    
    Analiza la pregunta en relación con los datos disponibles y proporciona una respuesta clara y fundamentada.
    """

    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": context_prompt}
        ],
        temperature=0.7,
        max_tokens=1000
    )
    
    return response.choices[0].message.content

# Sidebar: Carga de archivo y Configuración de IA
st.sidebar.header("📁 Carga de Datos")
uploaded_file = st.sidebar.file_uploader("Carga tu archivo CSV aquí", type=["csv"])

st.sidebar.header("🤖 Configuración de IA (Groq)")
groq_api_key_input = st.sidebar.text_input("Groq API Key", type="password", help="Obtén tu API Key en https://console.groq.com/")
groq_api_key = groq_api_key_input or os.environ.get("GROQ_API_KEY", "")

num_insights = st.sidebar.slider("Número de Insights a generar:", min_value=1, max_value=10, value=3)

if uploaded_file is not None:
    df = load_data(uploaded_file)
    st.sidebar.success("¡Archivo cargado con éxito!")
    
    # Filtros laterales dinámicos
    st.sidebar.subheader("🎯 Filtros Dinámicos")
    
    # --- FILTRO 1: INTERVALO DE FECHAS ---
    df_filtered = df.copy()
    
    if "FECHA_ACCIDENTE" in df.columns and not df["FECHA_ACCIDENTE"].dropna().empty:
        min_date = df["FECHA_ACCIDENTE"].min().date()
        max_date = df["FECHA_ACCIDENTE"].max().date()
        
        date_range = st.sidebar.date_input(
            "Rango de Fechas:",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date
        )
        
        # Validación para asegurar que el usuario haya seleccionado ambos extremos (inicio y fin)
        if isinstance(date_range, tuple) and len(date_range) == 2:
            start_date, end_date = date_range
            df_filtered = df_filtered[
                (df_filtered["FECHA_ACCIDENTE"].dt.date >= start_date) & 
                (df_filtered["FECHA_ACCIDENTE"].dt.date <= end_date)
            ]
    
    # --- FILTRO 2: DEPARTAMENTO ---
    deptos = ["Todos"] + list(df_filtered["DEPARTAMENTO_ACCIDENTE"].dropna().unique())
    selected_depto = st.sidebar.selectbox("Departamento:", deptos)
    
    if selected_depto != "Todos":
        df_filtered = df_filtered[df_filtered["DEPARTAMENTO_ACCIDENTE"] == selected_depto]

    # --- FILTRO 3: GRAVEDAD ---
    gravedades = ["Todas"] + list(df_filtered["GRAVEDAD_ACCIDENTE"].dropna().unique())
    selected_gravedad = st.sidebar.selectbox("Gravedad del Accidente:", gravedades)
    
    if selected_gravedad != "Todas":
        df_filtered = df_filtered[df_filtered["GRAVEDAD_ACCIDENTE"] == selected_gravedad]

    # Métricas principales (KPIs)
    col_kpi1, col_kpi2, col_kpi3, col_kpi4 = st.columns(4)
    with col_kpi1:
        st.metric("Total Registro Accidentes", len(df_filtered))
    with col_kpi2:
        st.metric("Marcas Distintas", df_filtered["MARCA_VEHICULO"].nunique())
    with col_kpi3:
        st.metric("Tipos de Vehículo", df_filtered["TIPO_VEHICULO"].nunique())
    with col_kpi4:
        promedio_edad = round(df_filtered["EDAD_VEHICULO"].mean(), 1) if not df_filtered["EDAD_VEHICULO"].isna().all() else 0
        st.metric("Edad Promedio Vehículos", f"{promedio_edad} años")

    st.markdown("---")

    # Layout en cuadrícula de 2 columnas para los gráficos
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("1. Top 10 Marca + Tipo de Vehículo")
        df_double_dim = df_filtered.groupby(["MARCA_VEHICULO", "TIPO_VEHICULO"]).size().reset_index(name="CANTIDAD")
        df_double_dim["MARCA_TIPO"] = df_double_dim["MARCA_VEHICULO"] + " - " + df_double_dim["TIPO_VEHICULO"]
        top10_dim = df_double_dim.sort_values(by="CANTIDAD", ascending=False).head(10)
        
        fig1 = px.bar(
            top10_dim,
            x="CANTIDAD",
            y="MARCA_TIPO",
            orientation="h",
            color="CANTIDAD",
            color_continuous_scale="Viridis",
            labels={"MARCA_TIPO": "Marca - Tipo", "CANTIDAD": "N° Accidentes"},
            text="CANTIDAD"
        )
        fig1.update_layout(yaxis={'categoryorder':'total ascending'}, showlegend=False, margin=dict(l=0, r=0, t=30, b=0))
        st.plotly_chart(fig1, use_container_width=True)

    with col2:
        st.subheader("2. Tipos de Vehículos Más Involucrados")
        df_tipo = df_filtered["TIPO_VEHICULO"].value_counts().reset_index()
        df_tipo.columns = ["TIPO_VEHICULO", "CANTIDAD"]
        
        fig2 = px.bar(
            df_tipo,
            x="TIPO_VEHICULO",
            y="CANTIDAD",
            color="TIPO_VEHICULO",
            labels={"TIPO_VEHICULO": "Tipo de Vehículo", "CANTIDAD": "N° Accidentes"},
            text="CANTIDAD"
        )
        fig2.update_layout(showlegend=False, margin=dict(l=0, r=0, t=30, b=0))
        st.plotly_chart(fig2, use_container_width=True)

    col3, col4 = st.columns(2)

    with col3:
        st.subheader("3. Gravedad de los Accidentes")
        df_gravedad = df_filtered["GRAVEDAD_ACCIDENTE"].value_counts().reset_index()
        df_gravedad.columns = ["GRAVEDAD", "CANTIDAD"]
        
        fig3 = px.pie(
            df_gravedad,
            names="GRAVEDAD",
            values="CANTIDAD",
            hole=0.4,
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        fig3.update_traces(textinfo='percent+label')
        fig3.update_layout(margin=dict(l=0, r=0, t=30, b=0))
        st.plotly_chart(fig3, use_container_width=True)

    with col4:
        st.subheader("4. Distribución de la Edad de los Vehículos")
        fig4 = px.histogram(
            df_filtered.dropna(subset=["EDAD_VEHICULO"]),
            x="EDAD_VEHICULO",
            nbins=20,
            color_discrete_sequence=["#2b5c8f"],
            labels={"EDAD_VEHICULO": "Edad del Vehículo (Años)", "count": "Frecuencia"}
        )
        fig4.update_layout(bargap=0.1, margin=dict(l=0, r=0, t=30, b=0))
        st.plotly_chart(fig4, use_container_width=True)

    st.markdown("---")

    # Sección para el informe generado por IA
    st.header("🧠 Generación de Informe con IA (Groq)")

    if st.button("🚀 Generar Informe de Insights con Groq"):
        if not groq_api_key:
            st.error("Por favor, ingresa tu clave API de Groq en la barra lateral o asegura la variable GROQ_API_KEY.")
        else:
            with st.spinner("Procesando datos con el modelo openai/gpt-oss-120b a través de Groq..."):
                try:
                    top_marcas_tipos = top10_dim.to_dict(orient="records")
                    dist_tipos = df_tipo.head(5).to_dict(orient="records")
                    dist_gravedad = df_gravedad.to_dict(orient="records")
                    
                    # Incluimos el rango de fechas actual en la carga útil enviada a la IA
                    rango_fechas_str = f"{start_date} a {end_date}" if 'start_date' in locals() else "Sin filtro"

                    resumen_payload = {
                        "rango_fechas_filtro": rango_fechas_str,
                        "departamento_filtro": selected_depto,
                        "gravedad_filtro": selected_gravedad,
                        "total_accidentes": len(df_filtered),
                        "edad_promedio_vehiculo": promedio_edad,
                        "top_marca_tipo_accidentes": top_marcas_tipos,
                        "tipos_vehiculo_frecuentes": dist_tipos,
                        "distribucion_gravedad": dist_gravedad
                    }
                    
                    informe = generar_informe_groq(groq_api_key, resumen_payload, num_insights)
                    
                    st.success("¡Informe generado exitosamente!")
                    
                    st.subheader("📌 Resumen Ejecutivo")
                    st.info(informe.get("resumen_ejecutivo", "No disponible"))
                    
                    st.subheader(f"💡 {len(informe.get('insights', []))} Insights Generados")
                    for item in informe.get("insights", []):
                        st.markdown(f"""
                        <div class="report-card">
                            <h4>#{item.get('id', '')} - {item.get('titulo', '')}</h4>
                            <p><strong>Hallazgo:</strong> {item.get('hallazgo', '')}</p>
                            <p><strong>Recomendación:</strong> {item.get('recomendacion', '')}</p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                except Exception as e:
                    st.error(f"Error al conectar con la API de Groq: {str(e)}")

    st.markdown("---")

    # ============================================
    # NUEVA SECCIÓN: CHATBOX INTERACTIVO
    # ============================================
    st.header("💬 Chat Interactivo - Interpreta tus Datos")
    st.markdown("Haz preguntas sobre los datos filtrados y obtén respuestas basadas en IA.")

    # Inicializar historial de chat en session state
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # Preparar datos de contexto para el chat
    rango_fechas_str = f"{start_date} a {end_date}" if 'start_date' in locals() else "Sin filtro"
    
    top_marcas_tipos = top10_dim.to_dict(orient="records")
    dist_tipos = df_tipo.head(5).to_dict(orient="records")
    dist_gravedad = df_gravedad.to_dict(orient="records")
    
    datos_contexto = {
        "rango_fechas_filtro": rango_fechas_str,
        "departamento_filtro": selected_depto,
        "gravedad_filtro": selected_gravedad,
        "total_accidentes": len(df_filtered),
        "edad_promedio_vehiculo": promedio_edad,
        "marcas_distintas": df_filtered["MARCA_VEHICULO"].nunique(),
        "tipos_vehiculo_distintos": df_filtered["TIPO_VEHICULO"].nunique(),
        "top_marca_tipo_accidentes": top_marcas_tipos,
        "tipos_vehiculo_frecuentes": dist_tipos,
        "distribucion_gravedad": dist_gravedad
    }

    # Mostrar historial de chat
    chat_container = st.container()
    
    with chat_container:
        for message in st.session_state.chat_history:
            if message["role"] == "user":
                st.markdown(f"""
                <div class="chat-message user">
                    <div class="chat-message-content">
                        <strong>Tú:</strong> {message["content"]}
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="chat-message assistant">
                    <div class="chat-message-content">
                        <strong>IA:</strong> {message["content"]}
                    </div>
                </div>
                """, unsafe_allow_html=True)

    # Input del usuario
    col_input, col_button = st.columns([5, 1])
    
    with col_input:
        user_question = st.text_input(
            "Escribe tu pregunta aquí:",
            placeholder="Ej: ¿Cuál es la marca de vehículo con más accidentes?",
            key="user_input"
        )
    
    with col_button:
        send_button = st.button("📤 Enviar", use_container_width=True)

    # Procesamiento de la pregunta
    if send_button and user_question.strip():
        if not groq_api_key:
            st.error("Por favor, ingresa tu clave API de Groq en la barra lateral para usar el chat.")
        else:
            # Agregar pregunta del usuario al historial
            st.session_state.chat_history.append({
                "role": "user",
                "content": user_question
            })
            
            # Generar respuesta con IA
            with st.spinner("🤔 Analizando tu pregunta..."):
                try:
                    respuesta_ia = chat_con_datos(groq_api_key, user_question, datos_contexto)
                    
                    # Agregar respuesta al historial
                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": respuesta_ia
                    })
                    
                    # Recargar la página para mostrar el nuevo mensaje
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"Error al procesar tu pregunta: {str(e)}")
    
    # Botón para limpiar chat
    if st.session_state.chat_history:
        if st.button("🗑️ Limpiar Historial de Chat"):
            st.session_state.chat_history = []
            st.rerun()

    st.markdown("---")

    with st.expander("🔍 Ver datos filtrados en tabla"):
        st.dataframe(df_filtered, use_container_width=True)

else:
    st.info("👋 Por favor, carga tu archivo CSV en la barra lateral izquierda para activar el dashboard.")
