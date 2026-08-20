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
    </style>
""", unsafe_allow_html=True)

st.title("🚗 Dashboard Analítico de Accidentes de Tránsito + IA (Groq)")
st.markdown("Visualización interactiva e informe generado por IA (`openai/gpt-oss-120b`).")

# Carga de datos con caché
@st.cache_data
def load_data(file):
    df = pd.read_csv(file)
    if "EDAD_VEHICULO" in df.columns:
        df["EDAD_VEHICULO"] = pd.to_numeric(df["EDAD_VEHICULO"], errors='coerce')
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
    
    deptos = ["Todos"] + list(df["DEPARTAMENTO_ACCIDENTE"].dropna().unique())
    selected_depto = st.sidebar.selectbox("Departamento:", deptos)
    
    if selected_depto != "Todos":
        df_filtered = df[df["DEPARTAMENTO_ACCIDENTE"] == selected_depto]
    else:
        df_filtered = df.copy()

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
                    
                    resumen_payload = {
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

    with st.expander("🔍 Ver datos filtrados en tabla"):
        st.dataframe(df_filtered, use_container_width=True)

else:
    st.info("👋 Por favor, carga tu archivo CSV en la barra lateral izquierda para activar el dashboard.")
