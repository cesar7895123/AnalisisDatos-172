import os
import json
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from groq import Groq
from utils.profit_analyzer import (
    generar_proyeccion_utilidad,
    calcular_resumen_cartera,
    generar_recomendaciones_groq
)

# ====================================
# Configuración y Carga de Traducciones
# ====================================

# Cargar traducciones desde archivo JSON
def cargar_traducciones():
    try:
        with open("i18n/translations.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"es": {}, "en": {}}

TRADUCCIONES = cargar_traducciones()

# Inicializar idioma en session state
if "idioma" not in st.session_state:
    st.session_state.idioma = "es"

# Función para obtener traducción
def t(clave, default=""):
    """Obtiene una traducción con soporte a claves anidadas"""
    keys = clave.split(".")
    result = TRADUCCIONES.get(st.session_state.idioma, {})
    for key in keys:
        result = result.get(key, {})
    return result if result else default

# Selector de idioma en la barra lateral
col_lang1, col_lang2 = st.sidebar.columns(2)
with col_lang1:
    if st.button("🇪🇸 Español", use_container_width=True, key="lang_es"):
        st.session_state.idioma = "es"
        st.rerun()
with col_lang2:
    if st.button("🇬🇧 English", use_container_width=True, key="lang_en"):
        st.session_state.idioma = "en"
        st.rerun()

# ====================================
# Configuración de la página
# ====================================
page_title = t("page_title", "Dashboard de Accidentes & IA Groq")
st.set_page_config(
    page_title=page_title,
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
    .profit-card {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #1f77b4;
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
# Sección: Información del Proyecto
# ---------------------------
PROJECT_INFO_FILE = "project_info.json"

st.sidebar.header(t("sidebar.project_info", "📌 Información del Proyecto"))

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
    if file_info:
        st.session_state.project_info = {
            "project_name": file_info.get("project_name", "Dashboard Analítico de Accidentes de Tránsito + IA (Groq)"),
            "team_members": file_info.get("team_members", "Dora Milena Ocampo\nElena Rodriguez\nCesar Bedoya"),
            "project_description": file_info.get("project_description", "Análisis inteligente de datos de accidentes vehiculares con IA"),
            "problem_statement": file_info.get("problem_statement", "Mejorar el análisis y la interpretación de datos de siniestralidad vial"),
            "technologies": file_info.get("technologies", ["Python", "Streamlit", "Pandas", "Plotly", "Groq", "GitHub"]) 
        }
    else:
        st.session_state.project_info = {
            "project_name": "Dashboard Analítico de Accidentes de Tránsito + IA (Groq)",
            "team_members": "Dora Milena Ocampo\nElena Rodriguez\nCesar Bedoya",
            "project_description": "Análisis inteligente de datos de accidentes vehiculares con IA",
            "problem_statement": "Mejorar el análisis y la interpretación de datos de siniestralidad vial",
            "technologies": ["Python", "Streamlit", "Pandas", "Plotly", "Groq", "GitHub"]
        }

# Sidebar: Carga de archivo y Configuración de IA
st.sidebar.header(t("sidebar.data_upload", "📁 Carga de Datos"))
uploaded_file = st.sidebar.file_uploader(t("sidebar.upload_csv", "Carga tu archivo CSV aquí"), type=["csv"])

st.sidebar.header(t("sidebar.ai_config", "🤖 Configuración de IA (Groq)"))
groq_api_key_input = st.sidebar.text_input(
    t("sidebar.groq_api_key", "Groq API Key"), 
    type="password", 
    help=t("sidebar.api_key_help", "Obtén tu API Key en https://console.groq.com/")
)
groq_api_key = groq_api_key_input or os.environ.get("GROQ_API_KEY", "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")

num_insights = st.sidebar.slider(
    t("sidebar.num_insights", "Número de Insights a generar:"), 
    min_value=1, 
    max_value=10, 
    value=3
)

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

# Funciones IA
def generar_informe_groq(groq_api_key, datos_resumen, num_insights, idioma="es"):
    client = Groq(api_key=groq_api_key)
    
    if idioma == "en":
        system_prompt = (
            "You are an expert in road safety and analytical analysis of traffic accident data. "
            "Your task is to analyze the provided aggregated data and generate a clear, professional and actionable executive report. "
            "You must respond ONLY in JSON format."
        )
        
        user_prompt = f"""
        Analyze the following summary of traffic accident data:
        
        --- DATA SUMMARY ---
        {json.dumps(datos_resumen, ensure_ascii=False, indent=2)}
        --- END OF DATA ---
        
        Instructions:
        1. Generate a general executive summary of the analyzed situation.
        2. Generate EXACTLY {num_insights} key insights based on the data.
        3. For each insight, include a title, detailed description of the finding and a specific preventive measure or recommendation.
        
        Respond strictly in JSON format with the following structure:
        {{
          "executive_summary": "Descriptive text of the summary...",
          "insights": [
            {{
              "id": 1,
              "title": "Insight title",
              "finding": "Explanation of the finding",
              "recommendation": "Recommended action or measure"
            }}
          ]
        }}
        """
    else:
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


def chat_con_datos(groq_api_key, pregunta_usuario, datos_resumen, idioma="es"):
    client = Groq(api_key=groq_api_key)
    
    if idioma == "en":
        system_prompt = (
            "You are an expert analyst of traffic accident data. "
            "You have access to a summary of filtered accident data. "
            "Respond clearly, concisely and based on the provided data. "
            "If the question is not related to the data, indicate it politely."
        )
        
        context_prompt = f"""
        Context - Data available for analysis:
        {json.dumps(datos_resumen, ensure_ascii=False, indent=2)}
        
        User question: {pregunta_usuario}
        
        Analyze the question in relation to the available data and provide a clear and well-founded response.
        """
    else:
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

# Crear pestañas principales
tab_names = [
    t("tabs.presentation", "Presentación"),
    t("tabs.visualizations", "Visualizaciones"),
    t("tabs.insights", "IA - Insights"),
    t("tabs.chat", "Chat"),
    t("tabs.data_table", "Tabla de Datos"),
    t("tabs.profit_analysis", "Análisis de Utilidad")
]

tabs = st.tabs(tab_names)

# Pestaña: Presentación
with tabs[0]:
    st.markdown(f"""
    <div class="presentation-card">
      <h1>📌 {st.session_state.project_info.get('project_name')}</h1>
      <h4>{t("presentation.members", "👥 Integrantes")}</h4>
      <p>{st.session_state.project_info.get('team_members', 'No especificado').replace(chr(10),'<br>')}</p>
      <hr>
      <h4>{t("presentation.description", "📝 Descripción general")}</h4>
      <p>{st.session_state.project_info.get('project_description', 'No especificado')}</p>
      <hr>
      <h4>{t("presentation.problem", "🎯 Problema que resuelve")}</h4>
      <p>{st.session_state.project_info.get('problem_statement', 'No especificado').replace(chr(10),'<br>')}</p>
      <hr>
      <h4>{t("presentation.technologies", "🛠️ Tecnologías utilizadas")}</h4>
      <p>{', '.join(st.session_state.project_info.get('technologies', []))}</p>
    </div>
    
    <p>{t("presentation.instructions", "Usa las demás pestañas para ver y analizar los datos, generar informes con IA y chatear con el asistente.")}</p>
    """, unsafe_allow_html=True)

# Si no hay archivo cargado
if uploaded_file is None:
    with tabs[1]:
        st.info(t("visualizations.insufficient_data", "📁 Por favor, carga tu archivo CSV desde la barra lateral para activar las visualizaciones."))
    with tabs[2]:
        st.info(t("insights.error_api_key", "📁 El generador de Insights requiere un archivo CSV cargado."))
    with tabs[3]:
        st.info(t("chat.title", "💬 El chat sobre datos funcionará una vez cargues el CSV y apliques filtros."))
    with tabs[4]:
        st.info(t("data_table.title", "🔍 La tabla de datos estará disponible tras cargar un CSV."))
    with tabs[5]:
        st.info(t("profit_analysis.error_no_data", "Por favor, carga un archivo CSV para activar el análisis de utilidad."))
else:
    # Cargar y preparar datos
    df = load_data(uploaded_file)
    st.sidebar.success(t("sidebar.file_loaded_success", "¡Archivo cargado con éxito!"))

    # Filtros laterales dinámicos
    st.sidebar.subheader(t("sidebar.dynamic_filters", "🎯 Filtros Dinámicos"))
    df_filtered = df.copy()

    if "FECHA_ACCIDENTE" in df.columns and not df["FECHA_ACCIDENTE"].dropna().empty:
        min_date = df["FECHA_ACCIDENTE"].min().date()
        max_date = df["FECHA_ACCIDENTE"].max().date()
        
        date_range = st.sidebar.date_input(
            t("sidebar.date_range", "Rango de Fechas:"),
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
    selected_depto = st.sidebar.selectbox(t("sidebar.department", "Departamento:"), deptos)
    if selected_depto != "Todos":
        df_filtered = df_filtered[df_filtered["DEPARTAMENTO_ACCIDENTE"] == selected_depto]

    gravedades = ["Todas"] + list(df_filtered["GRAVEDAD_ACCIDENTE"].dropna().unique())
    selected_gravedad = st.sidebar.selectbox(t("sidebar.accident_severity", "Gravedad del Accidente:"), gravedades)
    if selected_gravedad != "Todas":
        df_filtered = df_filtered[df_filtered["GRAVEDAD_ACCIDENTE"] == selected_gravedad]

    # Preparar variables comunes
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
        st.subheader(t("visualizations.kpis", "KPIs"))
        col_kpi1, col_kpi2, col_kpi3, col_kpi4 = st.columns(4)
        with col_kpi1:
            st.metric(t("visualizations.total_accidents", "Total Registro Accidentes"), len(df_filtered))
        with col_kpi2:
            st.metric(t("visualizations.distinct_brands", "Marcas Distintas"), int(df_filtered["MARCA_VEHICULO"].nunique()) if "MARCA_VEHICULO" in df_filtered.columns else 0)
        with col_kpi3:
            st.metric(t("visualizations.vehicle_types", "Tipos de Vehículo"), int(df_filtered["TIPO_VEHICULO"].nunique()) if "TIPO_VEHICULO" in df_filtered.columns else 0)
        with col_kpi4:
            st.metric(t("visualizations.avg_vehicle_age", "Edad Promedio Vehículos"), f"{promedio_edad} años")

        st.markdown("---")
        st.subheader(t("visualizations.title", "Visualizaciones"))
        col1, col2 = st.columns(2)
        with col1:
            st.subheader(t("visualizations.top_brand_type", "1. Top 10 Marca + Tipo de Vehículo"))
            if not top10_dim.empty:
                fig1 = px.bar(
                    top10_dim,
                    x="CANTIDAD",
                    y="MARCA_TIPO",
                    orientation="h",
                    color="CANTIDAD",
                    color_continuous_scale="Viridis",
                    labels={"MARCA_TIPO": t("visualizations.brand_type_label", "Marca - Tipo"), "CANTIDAD": t("visualizations.accidents_label", "N° Accidentes")},
                    text="CANTIDAD"
                )
                fig1.update_layout(yaxis={'categoryorder':'total ascending'}, showlegend=False, margin=dict(l=0, r=0, t=30, b=0))
                st.plotly_chart(fig1, use_container_width=True)
            else:
                st.info(t("visualizations.insufficient_data", "No hay datos suficientes para mostrar esta gráfica."))

        with col2:
            st.subheader(t("visualizations.vehicle_types_involved", "2. Tipos de Vehículos Más Involucrados"))
            if not df_tipo.empty:
                fig2 = px.bar(
                    df_tipo,
                    x="TIPO_VEHICULO",
                    y="CANTIDAD",
                    color="TIPO_VEHICULO",
                    labels={"TIPO_VEHICULO": t("visualizations.vehicle_type_label", "Tipo de Vehículo"), "CANTIDAD": t("visualizations.accidents_label", "N° Accidentes")},
                    text="CANTIDAD"
                )
                fig2.update_layout(showlegend=False, margin=dict(l=0, r=0, t=30, b=0))
                st.plotly_chart(fig2, use_container_width=True)
            else:
                st.info(t("visualizations.no_data_type", "No hay datos para Tipos de Vehículo."))

        col3, col4 = st.columns(2)
        with col3:
            st.subheader(t("visualizations.accident_severity", "3. Gravedad de los Accidentes"))
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
                st.info(t("visualizations.no_data_severity", "No hay datos de gravedad para mostrar."))

        with col4:
            st.subheader(t("visualizations.vehicle_age_dist", "4. Distribución de la Edad de los Vehículos"))
            if "EDAD_VEHICULO" in df_filtered.columns and not df_filtered["EDAD_VEHICULO"].dropna().empty:
                fig4 = px.histogram(
                    df_filtered.dropna(subset=["EDAD_VEHICULO"]),
                    x="EDAD_VEHICULO",
                    nbins=20,
                    color_discrete_sequence=["#2b5c8f"],
                    labels={"EDAD_VEHICULO": t("visualizations.vehicle_age_label", "Edad del Vehículo (Años)"), "count": t("visualizations.frequency_label", "Frecuencia")}
                )
                fig4.update_layout(bargap=0.1, margin=dict(l=0, r=0, t=30, b=0))
                st.plotly_chart(fig4, use_container_width=True)
            else:
                st.info(t("visualizations.no_data_age", "No hay datos de edad del vehículo."))

    # Pestaña: IA - Insights
    with tabs[2]:
        st.header(t("insights.title", "🧠 Generación de Informe con IA (Groq)"))
        if st.button(t("insights.generate_btn", "🚀 Generar Informe de Insights con Groq")):
            if not groq_api_key:
                st.error(t("insights.error_api_key", "Por favor, ingresa tu clave API de Groq en la barra lateral o asegura la variable GROQ_API_KEY."))
            else:
                with st.spinner(t("insights.processing", "Procesando datos con el modelo openai/gpt-oss-120b a través de Groq...")):
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

                        informe = generar_informe_groq(groq_api_key, resumen_payload, num_insights, st.session_state.idioma)

                        st.success(t("insights.success", "¡Informe generado exitosamente!"))
                        st.subheader(t("insights.executive_summary", "📌 Resumen Ejecutivo"))
                        
                        # Adaptarse a claves en español o inglés
                        resumen_key = "resumen_ejecutivo" if st.session_state.idioma == "es" else "executive_summary"
                        insights_key = "insights"
                        titulo_key = "titulo" if st.session_state.idioma == "es" else "title"
                        hallazgo_key = "hallazgo" if st.session_state.idioma == "es" else "finding"
                        recomendacion_key = "recomendacion" if st.session_state.idioma == "es" else "recommendation"
                        
                        st.info(informe.get(resumen_key, "No disponible"))

                        st.subheader(f"💡 {len(informe.get(insights_key, []))} {t('insights.insights_generated', 'Insights Generados')}")
                        for item in informe.get(insights_key, []):
                            st.markdown(f"""
                            <div class="report-card">
                                <h4>#{item.get('id', '')} - {item.get(titulo_key, '')}</h4>
                                <p><strong>{t('insights.finding', 'Hallazgo:')}:</strong> {item.get(hallazgo_key, '')}</p>
                                <p><strong>{t('insights.recommendation', 'Recomendación:')}:</strong> {item.get(recomendacion_key, '')}</p>
                            </div>
                            """, unsafe_allow_html=True)

                    except Exception as e:
                        st.error(f"{t('insights.api_error', 'Error al conectar con la API de Groq:')} {str(e)}")

    # Pestaña: Chat
    with tabs[3]:
        st.header(t("chat.title", "💬 Chat Interactivo - Interpreta tus Datos"))
        st.markdown(t("chat.description", "Haz preguntas sobre los datos filtrados y obtén respuestas basadas en IA."))

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

        chat_container = st.container()
        with chat_container:
            for message in st.session_state.chat_history:
                if message["role"] == "user":
                    st.markdown(f"""
                    <div class="chat-message user">
                        <div class="chat-message-content">
                            <strong>{t("chat.user_label", "Tú:")}:</strong> {message["content"]}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class="chat-message assistant">
                        <div class="chat-message-content">
                            <strong>{t("chat.ai_label", "IA:")}:</strong> {message["content"]}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

        col_input, col_button = st.columns([5, 1])
        with col_input:
            user_question = st.text_input(
                t("chat.placeholder", "Escribe tu pregunta aquí:"),
                placeholder=t("chat.placeholder", "Ej: ¿Cuál es la marca de vehículo con más accidentes?"),
                key="user_input"
            )
        with col_button:
            send_button = st.button(t("chat.send_btn", "📤 Enviar"), use_container_width=True)

        if send_button and user_question.strip():
            if not groq_api_key:
                st.error(t("chat.error_api_key", "Por favor, ingresa tu clave API de Groq en la barra lateral para usar el chat."))
            else:
                st.session_state.chat_history.append({"role": "user", "content": user_question})
                with st.spinner(t("chat.analyzing", "🤔 Analizando tu pregunta...")):
                    try:
                        respuesta_ia = chat_con_datos(groq_api_key, user_question, datos_contexto, st.session_state.idioma)
                        st.session_state.chat_history.append({"role": "assistant", "content": respuesta_ia})
                        st.rerun()
                    except Exception as e:
                        st.error(f"{t('chat.error_process', 'Error al procesar tu pregunta:')} {str(e)}")

        if st.session_state.chat_history:
            if st.button(t("chat.clear_history", "🗑️ Limpiar Historial de Chat")):
                st.session_state.chat_history = []
                st.rerun()

    # Pestaña: Tabla de Datos
    with tabs[4]:
        st.header(t("data_table.title", "🔍 Datos Filtrados"))
        with st.expander(t("data_table.view_filtered", "Ver datos filtrados en tabla")):
            st.dataframe(df_filtered, use_container_width=True)

    # Pestaña: Análisis de Utilidad (NUEVA)
    with tabs[5]:
        st.header(t("profit_analysis.title", "📊 Análisis de Utilidad y Proyección de Seguros"))
        st.markdown(t("profit_analysis.description", "Proyección de ganancia y margen de utilidad basado en perfiles de riesgo vehicular"))
        
        if st.button(t("profit_analysis.generate_projection", "🚀 Generar Proyección de Utilidad")):
            with st.spinner(t("profit_analysis.generating_recommendations", "Generando proyección de utilidad...")):
                try:
                    # Generar análisis de utilidad
                    analisis_riesgo = generar_proyeccion_utilidad(df_filtered, "TIPO_VEHICULO")
                    resumen_cartera = calcular_resumen_cartera(analisis_riesgo)
                    
                    if analisis_riesgo.empty or resumen_cartera is None:
                        st.warning(t("profit_analysis.error_no_data", "No hay datos suficientes para generar proyección"))
                    else:
                        # Resumen de Cartera
                        st.subheader(t("profit_analysis.summary_title", "📈 Resumen de Proyección de Seguros"))
                        col1, col2, col3, col4 = st.columns(4)
                        
                        with col1:
                            st.metric(
                                t("profit_analysis.total_vehicles", "Total de Vehículos"),
                                resumen_cartera.get("total_vehiculos_analizados", 0)
                            )
                        with col2:
                            st.metric(
                                t("profit_analysis.avg_premium", "Prima Promedio Anual"),
                                f"${resumen_cartera.get('prima_promedio_anual', 0):,.0f}"
                            )
                        with col3:
                            st.metric(
                                t("profit_analysis.total_potential_profit", "Utilidad Total Potencial"),
                                f"${resumen_cartera.get('utilidad_potencial_total', 0):,.0f}"
                            )
                        with col4:
                            st.metric(
                                t("profit_analysis.annual_profit", "Utilidad Anual Cartera"),
                                f"${resumen_cartera.get('utilidad_anual_cartera', 0):,.0f}"
                            )
                        
                        st.markdown("---")
                        
                        # Tabla detallada de perfiles de riesgo
                        st.subheader(t("profit_analysis.profile_risk", "Perfiles de Riesgo por Tipo de Vehículo"))
                        
                        # Preparar datos para mostrar
                        display_cols = ["TIPO_VEHICULO", "cantidad_accidentes", "tasa_accidentalidad", "nivel_riesgo", "prima_anual", "margen_ganancia_pct", "utilidad_por_poliza", "utilidad_total_estimada"]
                        
                        if st.session_state.idioma == "en":
                            display_cols_renamed = {
                                "TIPO_VEHICULO": "Vehicle Type",
                                "cantidad_accidentes": "Accident Count",
                                "tasa_accidentalidad": "Accident Rate (%)",
                                "nivel_riesgo": "Risk Level",
                                "prima_anual": "Annual Premium",
                                "margen_ganancia_pct": "Profit Margin (%)",
                                "utilidad_por_poliza": "Profit per Policy",
                                "utilidad_total_estimada": "Total Estimated Profit"
                            }
                        else:
                            display_cols_renamed = {
                                "TIPO_VEHICULO": "Tipo Vehículo",
                                "cantidad_accidentes": "Cantidad Accidentes",
                                "tasa_accidentalidad": "Tasa Accidentalidad (%)",
                                "nivel_riesgo": "Nivel Riesgo",
                                "prima_anual": "Prima Anual",
                                "margen_ganancia_pct": "Margen Ganancia (%)",
                                "utilidad_por_poliza": "Utilidad por Póliza",
                                "utilidad_total_estimada": "Utilidad Total Estimada"
                            }
                        
                        df_display = analisis_riesgo[display_cols].copy()
                        df_display.columns = [display_cols_renamed.get(col, col) for col in display_cols]
                        
                        st.dataframe(df_display, use_container_width=True)
                        
                        # Gráfico de utilidad proyectada
                        st.subheader(t("profit_analysis.profit_projection_title", "Utilidad Proyectada por Perfil de Riesgo"))
                        
                        fig_profit = px.bar(
                            analisis_riesgo,
                            x="TIPO_VEHICULO",
                            y="utilidad_total_estimada",
                            color="nivel_riesgo",
                            labels={
                                "TIPO_VEHICULO": t("profit_analysis.vehicle_type", "Tipo Vehículo"),
                                "utilidad_total_estimada": t("profit_analysis.total_profit_estimated", "Utilidad Total Estimada"),
                                "nivel_riesgo": t("profit_analysis.risk_level", "Nivel de Riesgo")
                            },
                            text="utilidad_total_estimada",
                            color_discrete_map={
                                "ALTO": "#ff7f0e",
                                "MEDIO": "#ffbb78",
                                "BAJO": "#2ca02c"
                            }
                        )
                        fig_profit.update_traces(textposition='outside')
                        st.plotly_chart(fig_profit, use_container_width=True)
                        
                        # Gráfico de prima vs margen
                        st.subheader(t("profit_analysis.premium_rate", "Prima Anual vs Margen de Ganancia"))
                        
                        fig_scatter = px.scatter(
                            analisis_riesgo,
                            x="prima_anual",
                            y="margen_ganancia_pct",
                            size="cantidad_accidentes",
                            color="nivel_riesgo",
                            hover_name="TIPO_VEHICULO",
                            labels={
                                "prima_anual": "Prima Anual",
                                "margen_ganancia_pct": "Margen de Ganancia (%)",
                                "nivel_riesgo": "Nivel de Riesgo"
                            },
                            color_discrete_map={
                                "ALTO": "#ff7f0e",
                                "MEDIO": "#ffbb78",
                                "BAJO": "#2ca02c"
                            }
                        )
                        st.plotly_chart(fig_scatter, use_container_width=True)
                        
                        # Recomendaciones AI (si existe API Key)
                        if groq_api_key and groq_api_key != "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":
                            st.subheader(t("profit_analysis.insurance_recommendation", "💡 Recomendaciones Estratégicas de Seguros"))
                            
                            with st.spinner(t("profit_analysis.generating_recommendations", "Generando recomendaciones...")):
                                recomendaciones = generar_recomendaciones_groq(
                                    groq_api_key,
                                    analisis_riesgo,
                                    resumen_cartera,
                                    st.session_state.idioma
                                )
                                
                                if recomendaciones:
                                    st.markdown(f"""
                                    <div class="profit-card">
                                        {recomendaciones}
                                    </div>
                                    """, unsafe_allow_html=True)
                        else:
                            st.info(t("profit_analysis.no_groq_key", "Se requiere API Key de Groq válida para generar recomendaciones automáticas."))
                        
                except Exception as e:
                    st.error(f"Error al generar proyección: {str(e)}")

if uploaded_file is None:
    st.sidebar.info(t("sidebar.upload_hint", "👋 Sube un CSV para activar las demás pestañas."))
