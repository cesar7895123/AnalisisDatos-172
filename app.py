import streamlit as st
import pandas as pd
import plotly.express as px

# Configuración de la página
st.set_page_config(
    page_title="Dashboard de Accidentes de Tránsito",
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
    </style>
""", unsafe_allow_html=True)

st.title("🚗 Dashboard Analítico de Accidentes de Tránsito")
st.markdown("Analítica interactiva basada en el dataset de vehículos involucrados en accidentes.")

# Carga de datos con caché para optimizar rendimiento
@st.cache_data
def load_data(file):
    df = pd.read_csv(file)
    if "EDAD_VEHICULO" in df.columns:
        df["EDAD_VEHICULO"] = pd.to_numeric(df["EDAD_VEHICULO"], errors='coerce')
    return df

# Sidebar: Carga de archivo y Filtros
st.sidebar.header("📁 Carga de Datos y Filtros")
uploaded_file = st.sidebar.file_uploader("Carga tu archivo CSV aquí", type=["csv"])

if uploaded_file is not None:
    df = load_data(uploaded_file)
    st.sidebar.success("¡Archivo cargado con éxito!")
    
    # Filtros dinámicos
    st.sidebar.subheader("Filtros Dinámicos")
    
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

    # Indicadores Clave (KPIs)
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

    # Gráficos e Indicadores Solicitados
    col1, col2 = st.columns(2)

    # 1. Doble dimensión: MARCA_VEHICULO x TIPO_VEHICULO (Top 10)
    with col1:
        st.subheader("1. Top 10 Combinación (Marca + Tipo)")
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

    # 2. Tipos de vehículos más involucrados
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

    # 3. Gravedad de los Accidentes
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

    # 4. Distribución de la edad del vehículo
    with col4:
        st.subheader("4. Distribución de Edad del Vehículo")
        fig4 = px.histogram(
            df_filtered.dropna(subset=["EDAD_VEHICULO"]),
            x="EDAD_VEHICULO",
            nbins=20,
            color_discrete_sequence=["#2b5c8f"],
            labels={"EDAD_VEHICULO": "Edad del Vehículo (Años)", "count": "Frecuencia"}
        )
        fig4.update_layout(bargap=0.1, margin=dict(l=0, r=0, t=30, b=0))
        st.plotly_chart(fig4, use_container_width=True)

    # Tabla interactiva
    with st.expander("🔍 Explorar Datos Filtrados"):
        st.dataframe(df_filtered, use_container_width=True)

else:
    st.info("👋 Por favor, carga tu archivo CSV en el menú lateral para activar el dashboard.")