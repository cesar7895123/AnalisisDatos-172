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
    .presentation-card {
        background-color: #ffffff;
        padding: 24px;
        border-radius: 12px;
        margin-bottom: 18px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.06);
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
# Sección: Información del Proyecto (sidebar inputs)
# ---------------------------
PROJECT_INFO_FILE = "project_info.json"

st.sidebar.header("📌 Información del Proyecto")
# Cargar project_info desde archivo si existe
if os.path.exists(PROJECT_INFO_FILE):
    try:
        with open(PROJECT_INFO_FILE, "r", encoding="utf-8") as f:
            file_info = json.load(f)
    except Exception:
        file_info = None
else:
    file_info = None

if "project_info" not in st.session_state:
    # Valores por defecto (si existe archivo, usarlo)
    if file_info:
        st.session_state.project_info = {
            "project_name": file_info.get("project_name", "Dashboard Analítico de Accidentes de Tránsito + IA (Groq)"),
            "team_members": file_info.get("team_members", "Dora Milena Ocampo\nElena Rodriguez\nCesar Bedoya"),
            "project_description": file_info.get("project_description", ""),
            "problem_statement": file_info.get("problem_statement", ""),
            "technologies": file_info.get("technologies", ["Python", "Streamlit", "Pandas", "Plotly"]) 
        }
    else:
        st.session_state.project_info = {
            "project_name": "Dashboard Analítico de Accidentes de Tránsito + IA (Groq)",
            "team_members": "Dora Milena Ocampo\nElena Rodriguez\nCesar Bedoya",
            "project_description": "",
            "problem_statement": "",
            "technologies": ["Python", "Streamlit", "Pandas", "Plotly"]
        }

# Note: Project info input fields have been intentionally removed to hide the options requested.

# Sidebar: Carga de archivo y Configuración de IA
st.sidebar.header("📁 Carga de Datos")
uploaded_file = st.sidebar.file_uploader("Carga tu archivo CSV aquí", type=["csv"])

st.sidebar.header("🤖 Configuración de IA (Groq)")
groq_api_key_input = st.sidebar.text_input("Groq API Key", type="password", help="Obtén tu API Key en https://console.groq.com/")
groq_api_key = groq_api_key_input or os.environ.get("GROQ_API_KEY", "")

num_insights = st.sidebar.slider("Número de Insights a generar:", min_value=1, max_value=10, value=3)

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

# Funciones IA (sin cambios importantes)
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


def chat_con_datos(groq_api_key, pregunta_usuario, datos_resumen):
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

# Crear pestañas principales para presentación y funcionalidades
tabs = st.tabs(["Presentación", "Visualizaciones", "IA - Insights", "Chat", "Tabla de Datos"]) 

# Pestaña: Presentación (tipo slide/presentación)
with tabs[0]:
    st.markdown(f"""
    <div class="presentation-card">
      <h1>📌 {st.session_state.project_info.get('project_name')}</h1>
      <h4>👥 Integrantes</h4>
      <p>{st.session_state.project_info.get('team_members', 'No especificado').replace('\n','<br>')}</p>
      <hr>
      <h4>📝 Descripción general</h4>
      <p>{st.session_state.project_info.get('project_description', 'No especificado')}</p>
      <hr>
      <h4>🎯 Problema que resuelve</h4>
      <p>{st.session_state.project_info.get('problem_statement', 'No especificado')}</p>
      <hr>
      <h4>🛠️ Tecnologías utilizadas</h4>
      <p>{', '.join(st.session_state.project_info.get('technologies', []))}</p>
    </div>
    
    <p>Usa las demás pestañas para ver y analizar los datos, generar informes con IA y chatear con el asistente.</p>
    """, unsafe_allow_html=True)

# Si no hay archivo cargado, mostramos aviso en las pestañas que dependan de datos
if uploaded_file is None:
    with tabs[1]:
        st.info("📁 Por favor, carga tu archivo CSV desde la barra lateral para activar las visualizaciones.")
    with tabs[2]:
        st.info("📁 El generador de Insights requiere un archivo CSV cargado.")
    with tabs[3]:
        st.info("💬 El chat sobre datos funcionará una vez cargues el CSV y apliques filtros.")
    with tabs[4]:
        st.info("🔍 La tabla de datos estará disponible tras cargar un CSV.")
else:
    # Cargar y preparar datos
    df = load_data(uploaded_file)
    st.sidebar.success("¡Archivo cargado con éxito!")

    # Filtros laterales dinámicos
    st.sidebar.subheader("🎯 Filtros Dinámicos")
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
        if isinstance(date_range, tuple) and len(date_range) == 2:
            start_date, end_date = date_range
            df_filtered = df_filtered[
                (df_filtered["FECHA_ACCIDENTE"].dt.date >= start_date) & 
                (df_filtered["FECHA_ACCIDENTE"].dt.date <= end_date)
            ]

    deptos = ["Todos"] + list(df_filtered["DEPARTAMENTO_ACCIDENTE"].dropna().unique())
    selected_depto = st.sidebar.selectbox("Departamento:", deptos)
    if selected_depto != "Todos":
        df_filtered = df_filtered[df_filtered["DEPARTAMENTO_ACCIDENTE"] == selected_depto]

    gravedades = ["Todas"] + list(df_filtered["GRAVEDAD_ACCIDENTE"].dropna().unique())
    selected_gravedad = st.sidebar.selectbox("Gravedad del Accidente:", gravedades)
    if selected_gravedad != "Todas":
        df_filtered = df_filtered[df_filtered["GRAVEDAD_ACCIDENTE"] == selected_gravedad]

    # Preparar algunas variables comunes
    promedio_edad = round(df_filtered["EDAD_VEHICULO"].mean(), 1) if ("EDAD_VEHICULO" in df_filtered.columns and not df_filtered["EDAD_VEHICULO"].isna().all()) else 0
    df_double_dim = df_filtered.groupby(["MARCA_VEHICULO", "TIPO_VEHICULO"]).size().reset_index(name="CANTIDAD") if all(col in df_filtered.columns for col in ["MARCA_VEHICULO","TIPO_VEHICULO"]) else pd.DataFrame()
    if not df_double_dim.empty:
        df_double_dim["MARCA_TIPO"] = df_double_dim["MARCA_VEHICULO"] + " - " + df_double_dim["TIPO_VEHICULO"]
        top10_dim = df_double_dim.sort_values(by="CANTIDAD", ascending=False).head(10)
    else:
        top10_dim = pd.DataFrame()

    df_tipo = df_filtered["TIPO_VEHICULO"].value_counts().reset_index() if "TIPO_VEHICULO" in df_filtered.columns else pd.DataFrame()
    if not df_tipo.empty:
        df_tipo.columns = ["TIPO_VEHICULO", "CANTIDAD"]

    df_gravedad = df_filtered["GRAVEDAD_ACCIDENTE"].value_counts().reset_index() if "GRAVEDAD_ACCIDENTE" in df_filtered.columns else pd.DataFrame()
    if not df_gravedad.empty:
        df_gravedad.columns = ["GRAVEDAD", "CANTIDAD"]

    # Pestaña: Visualizaciones
    with tabs[1]:
        st.subheader("KPIs")
        col_kpi1, col_kpi2, col_kpi3, col_kpi4 = st.columns(4)
        with col_kpi1:
            st.metric("Total Registro Accidentes", len(df_filtered))
        with col_kpi2:
            st.metric("Marcas Distintas", int(df_filtered["MARCA_VEHICULO"].nunique()) if "MARCA_VEHICULO" in df_filtered.columns else 0)
        with col_kpi3:
            st.metric("Tipos de Vehículo", int(df_filtered["TIPO_VEHICULO"].nunique()) if "TIPO_VEHICULO" in df_filtered.columns else 0)
        with col_kpi4:
            st.metric("Edad Promedio Vehículos", f"{promedio_edad} años")

        st.markdown("---")
        st.subheader("Visualizaciones")
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("1. Top 10 Marca + Tipo de Vehículo")
            if not top10_dim.empty:
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
            else:
                st.info("No hay datos suficientes para mostrar esta gráfica.")

        with col2:
            st.subheader("2. Tipos de Vehículos Más Involucrados")
            if not df_tipo.empty:
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
            else:
                st.info("No hay datos para Tipos de Vehículo.")

        col3, col4 = st.columns(2)
        with col3:
            st.subheader("3. Gravedad de los Accidentes")
            if not df_gravedad.empty:
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
            else:
                st.info("No hay datos de gravedad para mostrar.")

        with col4:
            st.subheader("4. Distribución de la Edad de los Vehículos")
            if "EDAD_VEHICULO" in df_filtered.columns and not df_filtered["EDAD_VEHICULO"].dropna().empty:
                fig4 = px.histogram(
                    df_filtered.dropna(subset=["EDAD_VEHICULO"]),
                    x="EDAD_VEHICULO",
                    nbins=20,
                    color_discrete_sequence=["#2b5c8f"],
                    labels={"EDAD_VEHICULO": "Edad del Vehículo (Años)", "count": "Frecuencia"}
                )
                fig4.update_layout(bargap=0.1, margin=dict(l=0, r=0, t=30, b=0))
                st.plotly_chart(fig4, use_container_width=True)
            else:
                st.info("No hay datos de edad del vehículo.")

    # Pestaña: IA - Insights
    with tabs[2]:
        st.header("🧠 Generación de Informe con IA (Groq)")
        if st.button("🚀 Generar Informe de Insights con Groq"):
            if not groq_api_key:
                st.error("Por favor, ingresa tu clave API de Groq en la barra lateral o asegura la variable GROQ_API_KEY.")
            else:
                with st.spinner("Procesando datos con el modelo openai/gpt-oss-120b a través de Groq..."):
                    try:
                        top_marcas_tipos = top10_dim.to_dict(orient="records") if not top10_dim.empty else []
                        dist_tipos = df_tipo.head(5).to_dict(orient="records") if not df_tipo.empty else []
                        dist_gravedad = df_gravedad.to_dict(orient="records") if not df_gravedad.empty else []
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

    # Pestaña: Chat
    with tabs[3]:
        st.header("💬 Chat Interactivo - Interpreta tus Datos")
        st.markdown("Haz preguntas sobre los datos filtrados y obtén respuestas basadas en IA.")

        # Inicializar historial de chat en session state
        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []

        rango_fechas_str = f"{start_date} a {end_date}" if 'start_date' in locals() else "Sin filtro"
        top_marcas_tipos = top10_dim.to_dict(orient="records") if not top10_dim.empty else []
        dist_tipos = df_tipo.head(5).to_dict(orient="records") if not df_tipo.empty else []
        dist_gravedad = df_gravedad.to_dict(orient="records") if not df_gravedad.empty else []

        datos_contexto = {
            "rango_fechas_filtro": rango_fechas_str,
            "departamento_filtro": selected_depto,
            "gravedad_filtro": selected_gravedad,
            "total_accidentes": len(df_filtered),
            "edad_promedio_vehiculo": promedio_edad,
            "marcas_distintas": int(df_filtered["MARCA_VEHICULO"].nunique()) if "MARCA_VEHICULO" in df_filtered.columns else 0,
            "tipos_vehiculo_distintos": int(df_filtered["TIPO_VEHICULO"].nunique()) if "TIPO_VEHICULO" in df_filtered.columns else 0,
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

        if send_button and user_question.strip():
            if not groq_api_key:
                st.error("Por favor, ingresa tu clave API de Groq en la barra lateral para usar el chat.")
            else:
                st.session_state.chat_history.append({"role": "user", "content": user_question})
                with st.spinner("🤔 Analizando tu pregunta..."):
                    try:
                        respuesta_ia = chat_con_datos(groq_api_key, user_question, datos_contexto)
                        st.session_state.chat_history.append({"role": "assistant", "content": respuesta_ia})
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error al procesar tu pregunta: {str(e)}")

        if st.session_state.chat_history:
            if st.button("🗑️ Limpiar Historial de Chat"):
                st.session_state.chat_history = []
                st.rerun()

    # Pestaña: Tabla de Datos
    with tabs[4]:
        st.header("🔍 Datos Filtrados")
        with st.expander("Ver datos filtrados en tabla"):
            st.dataframe(df_filtered, use_container_width=True)

# Footer / nota cuando no hay archivo (la pestaña Presentación queda disponible siempre)
if uploaded_file is None:
    st.sidebar.info("👋 Sube un CSV para activar las demás pestañas.")
