"""
Módulo de análisis de utilidad y proyección de seguros
Calcula margen de ganancia, prima y utilidad potencial basado en perfiles de riesgo
"""

import pandas as pd
import numpy as np
import json
from groq import Groq

def calcular_tasa_accidentalidad(df, columna_agrupacion="TIPO_VEHICULO"):
    """
    Calcula la tasa de accidentalidad por grupo (tipo de vehículo, marca, etc.)
    
    Args:
        df: DataFrame con datos filtrados
        columna_agrupacion: Columna por la que agrupar
        
    Returns:
        DataFrame con tasa de accidentalidad y clasificación de riesgo
    """
    if columna_agrupacion not in df.columns or df.empty:
        return pd.DataFrame()
    
    total_records = len(df)
    
    # Contar accidentes por grupo
    grupos = df[columna_agrupacion].value_counts().reset_index()
    grupos.columns = [columna_agrupacion, "cantidad_accidentes"]
    
    # Calcular tasa de accidentalidad (%)
    grupos["tasa_accidentalidad"] = (grupos["cantidad_accidentes"] / total_records * 100).round(2)
    
    # Clasificar por nivel de riesgo
    def clasificar_riesgo(tasa):
        if tasa >= 15:
            return "ALTO"
        elif tasa >= 8:
            return "MEDIO"
        else:
            return "BAJO"
    
    grupos["nivel_riesgo"] = grupos["tasa_accidentalidad"].apply(clasificar_riesgo)
    
    return grupos.sort_values("tasa_accidentalidad", ascending=False)

def calcular_prima_base(tasa_accidentalidad, prima_base=200000):
    """
    Calcula la prima base de seguros según la tasa de accidentalidad
    Fórmula: prima_base * (1 + factor_riesgo)
    
    Args:
        tasa_accidentalidad: Tasa de accidentalidad en porcentaje
        prima_base: Prima base anual en unidades monetarias
        
    Returns:
        Prima calculada en unidades monetarias
    """
    factor_riesgo = tasa_accidentalidad / 100
    prima = prima_base * (1 + factor_riesgo * 2.5)  # Factor multiplicador
    return round(prima, 2)

def calcular_margen_ganancia(prima, tasa_accidentalidad, margen_base=35):
    """
    Calcula el margen de ganancia (utilidad) como porcentaje
    
    Args:
        prima: Prima de seguro
        tasa_accidentalidad: Tasa de accidentalidad
        margen_base: Margen base de ganancia (%)
        
    Returns:
        Margen de ganancia ajustado en porcentaje
    """
    # Reducir margen según riesgo (a mayor riesgo, menor margen de ganancia)
    margen_ajustado = margen_base - (tasa_accidentalidad * 1.5)
    margen_ajustado = max(margen_ajustado, 10)  # Margen mínimo del 10%
    margen_ajustado = min(margen_ajustado, 45)  # Margen máximo del 45%
    
    return round(margen_ajustado, 2)

def generar_proyeccion_utilidad(df, columna_agrupacion="TIPO_VEHICULO"):
    """
    Genera una proyección completa de utilidad para seguros
    
    Args:
        df: DataFrame con datos filtrados
        columna_agrupacion: Columna por la que agrupar
        
    Returns:
        DataFrame con proyección de utilidad y rentabilidad
    """
    if df.empty:
        return pd.DataFrame()
    
    # Obtener tasa de accidentalidad
    analisis_riesgo = calcular_tasa_accidentalidad(df, columna_agrupacion)
    
    if analisis_riesgo.empty:
        return pd.DataFrame()
    
    # Calcular prima y margen para cada grupo
    analisis_riesgo["prima_anual"] = analisis_riesgo["tasa_accidentalidad"].apply(
        lambda x: calcular_prima_base(x)
    )
    
    analisis_riesgo["margen_ganancia_pct"] = analisis_riesgo["tasa_accidentalidad"].apply(
        lambda x: calcular_margen_ganancia(calcular_prima_base(x), x)
    )
    
    # Calcular utilidad potencial
    analisis_riesgo["utilidad_por_poliza"] = (
        analisis_riesgo["prima_anual"] * analisis_riesgo["margen_ganancia_pct"] / 100
    ).round(2)
    
    analisis_riesgo["utilidad_total_estimada"] = (
        analisis_riesgo["utilidad_por_poliza"] * analisis_riesgo["cantidad_accidentes"]
    ).round(2)
    
    analisis_riesgo["utilidad_mensual"] = (
        analisis_riesgo["utilidad_total_estimada"] / 12
    ).round(2)
    
    return analisis_riesgo

def calcular_resumen_cartera(analisis_riesgo):
    """
    Calcula resumen de cartera de seguros
    
    Args:
        analisis_riesgo: DataFrame con proyección de utilidad
        
    Returns:
        Diccionario con métricas de resumen
    """
    if analisis_riesgo.empty:
        return {}
    
    total_vehiculos = int(analisis_riesgo["cantidad_accidentes"].sum())
    prima_promedio = analisis_riesgo["prima_anual"].mean()
    utilidad_total = analisis_riesgo["utilidad_total_estimada"].sum()
    margen_promedio = analisis_riesgo["margen_ganancia_pct"].mean()
    
    return {
        "total_vehiculos_analizados": total_vehiculos,
        "prima_promedio_anual": round(prima_promedio, 2),
        "utilidad_potencial_total": round(utilidad_total, 2),
        "margen_promedio_cartera": round(margen_promedio, 2),
        "utilidad_mensual_cartera": round(utilidad_total / 12, 2),
        "utilidad_anual_cartera": round(utilidad_total, 2),
        "num_perfiles_riesgo": len(analisis_riesgo)
    }

def generar_recomendaciones_groq(groq_api_key, analisis_riesgo, resumen_cartera, idioma="es"):
    """
    Genera recomendaciones estratégicas usando Groq API
    
    Args:
        groq_api_key: Clave API de Groq
        analisis_riesgo: DataFrame con proyección
        resumen_cartera: Diccionario con resumen
        idioma: Idioma para respuesta (es/en)
        
    Returns:
        String con recomendaciones
    """
    if not groq_api_key:
        return None
    
    try:
        client = Groq(api_key=groq_api_key)
        
        if idioma == "en":
            system_prompt = (
                "You are an expert insurance actuarial analyst specializing in vehicle risk assessment. "
                "Analyze the provided insurance portfolio data and provide strategic recommendations for "
                "maximizing profit margins while managing risk exposure. Respond in English only."
            )
            
            user_prompt = f"""
            Analyze this insurance portfolio data and provide strategic recommendations:
            
            PORTFOLIO SUMMARY:
            - Total Vehicles Analyzed: {resumen_cartera.get('total_vehiculos_analizados', 0)}
            - Average Annual Premium: ${resumen_cartera.get('prima_promedio_anual', 0):.2f}
            - Total Potential Profit: ${resumen_cartera.get('utilidad_potencial_total', 0):.2f}
            - Average Portfolio Margin: {resumen_cartera.get('margen_promedio_cartera', 0):.2f}%
            
            RISK PROFILES:
            {analisis_riesgo[['TIPO_VEHICULO', 'tasa_accidentalidad', 'nivel_riesgo', 'prima_anual', 'margen_ganancia_pct']].to_json()}
            
            Provide 3-4 key strategic recommendations for improving profitability and managing risk.
            """
        else:
            system_prompt = (
                "Eres un experto analista actuarial de seguros especializado en evaluación de riesgo vehicular. "
                "Analiza los datos de cartera de seguros proporcionados y ofrece recomendaciones estratégicas para "
                "maximizar márgenes de ganancia mientras se gestiona la exposición al riesgo. Responde solo en español."
            )
            
            user_prompt = f"""
            Analiza estos datos de cartera de seguros y proporciona recomendaciones estratégicas:
            
            RESUMEN DE CARTERA:
            - Total de Vehículos Analizados: {resumen_cartera.get('total_vehiculos_analizados', 0)}
            - Prima Promedio Anual: ${resumen_cartera.get('prima_promedio_anual', 0):.2f}
            - Utilidad Potencial Total: ${resumen_cartera.get('utilidad_potencial_total', 0):.2f}
            - Margen Promedio de Cartera: {resumen_cartera.get('margen_promedio_cartera', 0):.2f}%
            
            PERFILES DE RIESGO:
            {analisis_riesgo[['TIPO_VEHICULO', 'tasa_accidentalidad', 'nivel_riesgo', 'prima_anual', 'margen_ganancia_pct']].to_json()}
            
            Proporciona 3-4 recomendaciones estratégicas clave para mejorar la rentabilidad y gestionar el riesgo.
            """
        
        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,
            max_tokens=1200
        )
        
        return response.choices[0].message.content
    
    except Exception as e:
        print(f"Error generating Groq recommendations: {str(e)}")
        return None
