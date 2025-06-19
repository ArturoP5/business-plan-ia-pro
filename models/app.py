"""
Business Plan IA - Interfaz Web
Genera proyecciones financieras profesionales para PYMEs
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
from models.modelo_financiero import ModeloFinanciero
from utils.pdf_generator import generar_pdf_ejecutivo


# Inicializar session state
if 'datos_guardados' not in st.session_state:
    st.session_state.datos_guardados = None
if 'proyeccion_generada' not in st.session_state:
    st.session_state.proyeccion_generada = False

# Configuración de la página
st.set_page_config(
    page_title="Business Plan IA",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado para mejor diseño
st.markdown("""
    <style>
    .main-header {
        font-size: 3rem;
        color: #1E3A8A;
        text-align: center;
        margin-bottom: 2rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #64748B;
        text-align: center;
        margin-bottom: 3rem;
    }
    .metric-card {
        background-color: #F8FAFC;
        padding: 1.5rem;
        border-radius: 0.5rem;
        border: 1px solid #E2E8F0;
    }
    </style>
""", unsafe_allow_html=True)

# Header principal
st.markdown('<h1 class="main-header">🚀 Business Plan IA</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Genera proyecciones financieras profesionales en minutos</p>', unsafe_allow_html=True)

# Sidebar para entrada de datos
with st.sidebar:
    st.header("📝 Datos de tu Empresa")

    # Información básica
    st.subheader("Información General")
    nombre_empresa = st.text_input("Nombre de la empresa", "Mi Empresa SL")
    sector = st.selectbox(
        "Sector",
        ["Hostelería", "Tecnología", "Ecommerce", "Consultoría",
            "Retail", "Servicios", "Industrial", "Otro"]
    )

    # Datos históricos
    st.subheader("Ventas Históricas")
    col1, col2 = st.columns(2)

    año_actual = datetime.now().year
    with col1:
        ventas_año_anterior_2 = st.number_input(
            f"Ventas {año_actual - 2} (€)",
            min_value=0,
            value=300000,
            step=10000,
            help="Introduce las ventas de hace 2 años"
        )
    with col2:
        ventas_año_anterior_1 = st.number_input(
            f"Ventas {año_actual - 1} (€)",
            min_value=0,
            value=350000,
            step=10000,
            help="Introduce las ventas del año pasado"
        )

    ventas_año_actual = st.number_input(
        f"Ventas {año_actual} (estimadas) (€)",
        min_value=0,
        value=400000,
        step=10000,
        help="Estimación de ventas del año actual"
    )

    # Estructura de costos
    st.subheader("Estructura de Costos")

    costos_variables_pct = st.slider(
        "Costos Variables (% de ventas)",
        min_value=10,
        max_value=80,
        value=40,
        help="Incluye: materias primas, mercancías, comisiones de venta"
    ) / 100

    gastos_personal = st.number_input(
        "Gastos de Personal Anuales (€)",
        min_value=0,
        value=120000,
        step=5000,
        help="Incluye: salarios, seguridad social, beneficios"
    )

    gastos_generales = st.number_input(
        "Gastos Generales Anuales (€)",
        min_value=0,
        value=36000,
        step=1000,
        help="Incluye: alquiler, suministros, seguros"
    )

    gastos_marketing = st.number_input(
        "Gastos de Marketing Anuales (€)",
        min_value=0,
        value=12000,
        step=1000,
        help="Incluye: publicidad, web, redes sociales"
    )

    # Parámetros financieros
    st.subheader("Parámetros Financieros")

    deuda_actual = st.number_input(
        "Deuda Actual (€)",
        min_value=0,
        value=0,
        step=5000,
        help="Préstamos bancarios, líneas de crédito, etc."
    )

    if deuda_actual > 0:
        tipo_interes = st.slider(
            "Tipo de Interés (%)",
            min_value=0.0,
            max_value=15.0,
            value=5.0,
            step=0.5
        ) / 100
    else:
        tipo_interes = 0.05

    # Botón de generación
    st.markdown("---")
    generar_proyeccion = st.button("🚀 Generar Proyección", type="primary", use_container_width=True)

# DEBUG - Variables del sidebar
st.write("DEBUG - Valor del botón:", generar_proyeccion if 'generar_proyeccion' in locals() else "NO EXISTE")
st.write("DEBUG - nombre_empresa:", nombre_empresa if 'nombre_empresa' in locals() else "NO EXISTE")

# Área principal
if generar_proyeccion:
    # Guardar que se generó una proyección
    st.session_state.proyeccion_generada = True

    st.write("DEBUG - ENTRÓ AL IF!")
    st.write("DEBUG - Session state actualizado:", st.session_state.proyeccion_generada)

    # Preparar datos para el modelo
    datos_empresa = {
        'nombre': nombre_empresa,
        'sector': sector,
        'ventas_historicas': [ventas_año_anterior_2, ventas_año_anterior_1, ventas_año_actual],
        'costos_variables_pct': costos_variables_pct,
        'gastos_personal': gastos_personal,
        'gastos_generales': gastos_generales,
        'gastos_marketing': gastos_marketing,
        # Estimamos otros gastos como 20% de gastos generales
        'otros_gastos': gastos_generales * 0.2,
        'deuda_actual': deuda_actual,
        'tipo_interes': tipo_interes
    }

    # Crear modelo y generar proyecciones
    with st.spinner('Generando proyecciones financieras...'):
        modelo = ModeloFinanciero(datos_empresa)
        pyl = modelo.generar_pyl()
        metricas = modelo.calcular_metricas_clave(pyl)

        # NUEVOS CÁLCULOS FINANCIEROS
        wc_df = modelo.calcular_working_capital(pyl)
        financiacion_df = modelo.calcular_financiacion_circulante(wc_df, pyl)
        fcf_df = modelo.calcular_free_cash_flow(pyl, wc_df)
        valoracion = modelo.calcular_valoracion_dcf(fcf_df)
        analisis_ia = modelo.generar_analisis_ia(pyl, valoracion, financiacion_df)
        resumen = modelo.generar_resumen_ejecutivo()

    # Guardar todos los datos en session state
    st.session_state.datos_guardados = {
        'datos_empresa': datos_empresa,
        'pyl': pyl,
        'metricas': metricas,
        'wc_df': wc_df,
        'financiacion_df': financiacion_df,
        'fcf_df': fcf_df,
        'valoracion': valoracion,
        'analisis_ia': analisis_ia,
        'nombre_empresa': nombre_empresa,
        'resumen': resumen
    }

    # Mostrar resultados
    st.success("✅ Proyección generada exitosamente!")

    # Tabs para organizar la información
    tab1, tab2, tab3, tab4 = st.tabs(
        ["📊 Dashboard", "📈 P&L Detallado", "📉 Gráficos", "📄 Resumen Ejecutivo"])

    with tab1:
        st.header("Dashboard de Métricas Clave")

        # Métricas principales en cards
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
            label="Ventas Año 5",
            value=f"€{pyl['Ventas'].iloc[-1]:,.0f}",
            delta=f"{metricas['crecimiento_ventas_promedio']}% crecimiento anual"
        )

        with col2:
            st.metric(
            label="EBITDA Año 5",
            value=f"€{pyl['EBITDA'].iloc[-1]:,.0f}",
            delta=f"{pyl['EBITDA %'].iloc[-1]}% margen"
        )

        with col3:
            st.metric(
            label="Beneficio Año 5",
            value=f"€{pyl['Beneficio Neto'].iloc[-1]:,.0f}",
            delta=f"{pyl['Beneficio Neto %'].iloc[-1]}% margen"
        )

        with col4:
            st.metric(
            label="ROI Proyectado",
            value=f"{metricas['roi_proyectado']}%"
        )

    # NUEVA SECCIÓN: Valoración Profesional Estilo Banca de Inversión
    st.markdown("---")
    st.subheader("🏦 Valoración de la Empresa (Metodología DCF)")

    # Primera fila - Valoración principal
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
        label="Valor de la Empresa",
        value=f"€{valoracion['valor_empresa']:,.0f}",
        delta=f"Rango: {valoracion['rango_valoracion']}"
    )

    with col2:
        st.metric(
        label="Múltiplo EV/EBITDA",
        value=f"{valoracion['ev_ebitda_salida']}x",
        delta=f"WACC: {valoracion['wacc_utilizado']}%"
    )

    with col3:
        st.metric(
        label="TIR Esperada",
        value=f"{valoracion['tir_esperada']}%",
        delta=f"{valoracion['money_multiple']}x retorno"
    )

    with col4:
        st.metric(
        label="Free Cash Flow Año 5",
        value=f"€{fcf_df['Free Cash Flow'].iloc[-1]:,.0f}",
        delta=f"{valoracion['valor_terminal_pct']:.0f}% valor terminal"
    )

    # Segunda fila - Capital de trabajo y análisis
    st.markdown("---")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
        label="Capital de Trabajo Inicial",
        value=f"€{wc_df['Capital de Trabajo'].iloc[0]:,.0f}",
        delta="Necesidad de financiación"
    )

    with col2:
        st.metric(
        label="Escenario Conservador",
        value=f"€{valoracion['valoracion_escenario_bajo']:,.0f}",
        delta="WACC +2%"
    )

    with col3:
        st.metric(
        label="Escenario Optimista",
        value=f"€{valoracion['valoracion_escenario_alto']:,.0f}",
        delta="WACC -1%"
    )

    # Tabla de Free Cash Flow
    st.markdown("---")
    st.subheader("💰 Free Cash Flow Proyectado")

    fcf_display = fcf_df.copy()
    for col in fcf_display.columns:
        if col != 'Año':
            fcf_display[col] = fcf_display[col].apply(lambda x: f"€{x:,.0f}")

    st.dataframe(fcf_display, use_container_width=True, height=200)

    # Nueva tabla de Financiación del Circulante
    st.markdown("---")
    st.subheader("💳 Financiación del Capital de Trabajo")

    # Métricas de financiación
    col1, col2, col3 = st.columns(3)

    with col1:
        limite_total = financiacion_df['Límite Póliza'].iloc[-1]
    st.metric(
        label="Límite de Crédito Año 5",
        value=f"€{limite_total:,.0f}",
        delta="25% de ventas"
    )

    with col2:
        uso_promedio = financiacion_df['Uso Póliza'].mean()
    st.metric(
        label="Uso Promedio de Póliza",
        value=f"€{uso_promedio:,.0f}",
        delta=f"{(uso_promedio/limite_total*100):.0f}% del límite" if limite_total > 0 else "N/A"
    )

    with col3:
        coste_total = financiacion_df['Coste Póliza'].sum()
    st.metric(
        label="Coste Financiero Total",
        value=f"€{coste_total:,.0f}",
        delta="6% anual s/dispuesto"
    )

    # Tabla de financiación
    financiacion_display = financiacion_df.copy()
    for col in financiacion_display.columns:
        if col != 'Año':
            financiacion_display[col] = financiacion_display[col].apply(
                lambda x: f"€{x:,.0f}")

    st.dataframe(financiacion_display, use_container_width=True, height=200)

    # Alerta si hay déficit
    if any(financiacion_df['Exceso/(Déficit)'] < 0):
        deficit_max = abs(financiacion_df['Exceso/(Déficit)'].min())
    st.warning(
        f"⚠️ **Alerta**: Necesitarás financiación adicional de €{deficit_max:,.0f} para cubrir el capital de trabajo en algún momento del proyecto.")

    # NUEVA SECCIÓN: Análisis Inteligente y Recomendaciones
    st.markdown("---")
    st.subheader("🤖 Análisis Inteligente y Recomendaciones")

    # Rating y viabilidad
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Rating del Proyecto", analisis_ia['rating'])
    with col2:
        viabilidad_color = "🟢" if "ALTA" in analisis_ia[
        'viabilidad'] else "🟡" if "MEDIA" in analisis_ia['viabilidad'] else "🔴"
    st.metric("Viabilidad", f"{viabilidad_color} {analisis_ia['viabilidad']}")

    # Resumen ejecutivo
    st.markdown("### 📋 Resumen Ejecutivo")
    st.info(analisis_ia['resumen_ejecutivo'])

    # Fortalezas, Riesgos y Recomendaciones en columnas
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("### 💪 Fortalezas")
    for fortaleza in analisis_ia['fortalezas']:
        st.success(f"✓ {fortaleza}")

    with col2:
        st.markdown("### ⚠️ Riesgos")
    for riesgo in analisis_ia['riesgos']:
        st.warning(f"! {riesgo}")

    with col3:
        st.markdown("### 💡 Recomendaciones")
    for recomendacion in analisis_ia['recomendaciones']:
        st.info(f"→ {recomendacion}")

    # Sección de descarga de informes profesionales
    st.markdown("---")
    st.subheader("📑 Documentos Ejecutivos")

    col1, col2, col3 = st.columns([1, 3, 1])

    with col2:
        # Generar PDF automáticamente
        try:
            with st.spinner('Preparando documentación ejecutiva...'):
                pdf_bytes = generar_pdf_ejecutivo(
                    datos_empresa=datos_empresa,
                    pyl_df=pyl,
                    valoracion=valoracion,
                    analisis_ia=analisis_ia,
                    financiacion_df=financiacion_df
                )

            # Mostrar botón de descarga con estilo premium
            st.download_button(
                label="📄 Descargar Business Plan Ejecutivo (PDF)",
                data=pdf_bytes,
                file_name=f"BusinessPlan_{datos_empresa['nombre'].replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.pdf",
                mime="application/pdf",
                type="primary",
                use_container_width=True,
                help="Documento profesional para presentación a inversores y directivos"
            )

            st.success("✅ Documento ejecutivo preparado - Formato profesional McKinsey/Goldman Sachs")

            # Información adicional
            with st.expander("ℹ️ Contenido del documento"):
                st.markdown("""
                **El Business Plan Ejecutivo incluye:**
                - Executive Summary
                - Key Investment Highlights  
                - Proyecciones Financieras (5 años)
                - Análisis Estratégico (DAFO)
                - Valoración DCF con escenarios
                - Conclusiones y recomendaciones
                
                **Diseñado para:** CEOs, CFOs, Inversores, Consejo de Administración
                """)

        except Exception as e:
            st.error(f"Error preparando documentación: {str(e)}")
            st.info("Por favor, verifica que todos los datos estén completos y vuelve a generar la proyección.")

    with tab2:
        st.header("Cuenta de Resultados Proyectada (P&L)")

        # Mostrar tabla con formato
        pyl_display = pyl.copy()

        # Formatear números para mejor visualización
        for col in pyl_display.columns:
            if col != 'Año' and '%' not in col:
                pyl_display[col] = pyl_display[col].apply(lambda x: f"€{x:,.0f}")
            elif '%' in col:
                pyl_display[col] = pyl_display[col].apply(lambda x: f"{x}%")

        st.dataframe(
            pyl_display,
            use_container_width=True,
            height=600
        )

        # Botón de descarga
        csv = pyl.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Descargar P&L en CSV",
            data=csv,
            file_name=f"pyl_{nombre_empresa.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )

    with tab3:
        st.header("Visualizaciones")

    # Gráfico de Ventas y EBITDA
    fig1 = go.Figure()

    # Barras de ventas
    fig1.add_trace(go.Bar(
        x=pyl['Año'],
        y=pyl['Ventas'],
        name='Ventas',
        marker_color='lightblue',
        text=[f"€{v:,.0f}" for v in pyl['Ventas']],
        textposition='outside'
    ))

    # Línea de EBITDA
    fig1.add_trace(go.Scatter(
        x=pyl['Año'],
        y=pyl['EBITDA'],
        name='EBITDA',
        line=dict(color='green', width=3),
        mode='lines+markers',
        yaxis='y2'
    ))

    # Configuración del layout
    fig1.update_layout(
        title='Evolución de Ventas y EBITDA',
        xaxis_title='Año',
        yaxis=dict(title='Ventas (€)', side='left'),
        yaxis2=dict(title='EBITDA (€)', side='right', overlaying='y'),
        hovermode='x unified',
        height=500
    )

    st.plotly_chart(fig1, use_container_width=True)

    # Gráfico de márgenes
    fig2 = go.Figure()

    fig2.add_trace(go.Scatter(
        x=pyl['Año'],
        y=pyl['Margen Bruto %'],
        name='Margen Bruto %',
        line=dict(width=2),
        mode='lines+markers'
    ))

    fig2.add_trace(go.Scatter(
        x=pyl['Año'],
        y=pyl['EBITDA %'],
        name='Margen EBITDA %',
        line=dict(width=2),
        mode='lines+markers'
    ))

    fig2.add_trace(go.Scatter(
        x=pyl['Año'],
        y=pyl['Beneficio Neto %'],
        name='Margen Neto %',
        line=dict(width=2),
        mode='lines+markers'
    ))

    fig2.update_layout(
        title='Evolución de Márgenes',
        xaxis_title='Año',
        yaxis_title='Porcentaje (%)',
        hovermode='x unified',
        height=400
    )

    st.plotly_chart(fig2, use_container_width=True)

    with tab4:
        st.header("Resumen Ejecutivo")

        # Mostrar resumen en un contenedor con estilo
        st.markdown(
            f"""
            <div style="background-color: #F8FAFC; padding: 2rem; border-radius: 0.5rem; border: 1px solid #E2E8F0;">
                <pre style="white-space: pre-wrap; font-family: monospace;">{resumen}</pre>
            </div>
            """,
            unsafe_allow_html=True
        )

        # Botón para descargar resumen
        st.download_button(
            label="📥 Descargar Resumen en TXT",
            data=resumen,
            file_name=f"resumen_ejecutivo_{nombre_empresa.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.txt",
            mime="text/plain"
        )

# Si hay datos guardados pero no se está generando nueva proyección, mostrarlos
elif st.session_state.proyeccion_generada and st.session_state.datos_guardados:
    # Recuperar datos guardados
    datos = st.session_state.datos_guardados
    datos_empresa = datos['datos_empresa']
    pyl = datos['pyl']
    metricas = datos['metricas']
    wc_df = datos['wc_df']
    financiacion_df = datos['financiacion_df']
    fcf_df = datos['fcf_df']
    valoracion = datos['valoracion']
    analisis_ia = datos['analisis_ia']
    nombre_empresa = datos['nombre_empresa']

    # Mostrar los mismos resultados
    st.success("✅ Mostrando proyección guardada")

    # Tabs para organizar la información
    tab1, tab2, tab3, tab4 = st.tabs(
        ["📊 Dashboard", "📈 P&L Detallado", "📉 Gráficos", "📄 Resumen Ejecutivo"])

    with tab1:
        st.header("Dashboard de Métricas Clave")

        # Métricas principales en cards
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                label="Ventas Año 5",
                value=f"€{pyl['Ventas'].iloc[-1]:,.0f}",
                delta=f"{metricas['crecimiento_ventas_promedio']}% crecimiento anual"
            )

        with col2:
            st.metric(
                label="EBITDA Año 5",
                value=f"€{pyl['EBITDA'].iloc[-1]:,.0f}",
                delta=f"{pyl['EBITDA %'].iloc[-1]}% margen"
            )

        with col3:
            st.metric(
                label="Beneficio Año 5",
                value=f"€{pyl['Beneficio Neto'].iloc[-1]:,.0f}",
                delta=f"{pyl['Beneficio Neto %'].iloc[-1]}% margen"
            )

        with col4:
            st.metric(
                label="ROI Proyectado",
                value=f"{metricas['roi_proyectado']}%"
            )

        # NUEVA SECCIÓN: Valoración Profesional Estilo Banca de Inversión
        st.markdown("---")
        st.subheader("🏦 Valoración de la Empresa (Metodología DCF)")

        # Primera fila - Valoración principal
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                label="Valor de la Empresa",
                value=f"€{valoracion['valor_empresa']:,.0f}",
                delta=f"Rango: {valoracion['rango_valoracion']}"
            )

        with col2:
            st.metric(
                label="Múltiplo EV/EBITDA",
                value=f"{valoracion['ev_ebitda_salida']}x",
                delta=f"WACC: {valoracion['wacc_utilizado']}%"
            )

        with col3:
            st.metric(
                label="TIR Esperada",
                value=f"{valoracion['tir_esperada']}%",
                delta=f"{valoracion['money_multiple']}x retorno"
            )

        with col4:
            st.metric(
                label="Free Cash Flow Año 5",
                value=f"€{fcf_df['Free Cash Flow'].iloc[-1]:,.0f}",
                delta=f"{valoracion['valor_terminal_pct']:.0f}% valor terminal"
            )

        # Segunda fila - Capital de trabajo y análisis
        st.markdown("---")
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                label="Capital de Trabajo Inicial",
                value=f"€{wc_df['Capital de Trabajo'].iloc[0]:,.0f}",
                delta="Necesidad de financiación"
            )

        with col2:
            st.metric(
                label="Escenario Conservador",
                value=f"€{valoracion['valoracion_escenario_bajo']:,.0f}",
                delta="WACC +2%"
            )

        with col3:
            st.metric(
                label="Escenario Optimista",
                value=f"€{valoracion['valoracion_escenario_alto']:,.0f}",
                delta="WACC -1%"
            )

        # Tabla de Free Cash Flow
        st.markdown("---")
        st.subheader("💰 Free Cash Flow Proyectado")

        fcf_display = fcf_df.copy()
        for col in fcf_display.columns:
            if col != 'Año':
                fcf_display[col] = fcf_display[col].apply(
                    lambda x: f"€{x:,.0f}")

        st.dataframe(fcf_display, use_container_width=True, height=200)

        # Nueva tabla de Financiación del Circulante
        st.markdown("---")
        st.subheader("💳 Financiación del Capital de Trabajo")

        # Métricas de financiación
        col1, col2, col3 = st.columns(3)

        with col1:
            limite_total = financiacion_df['Límite Póliza'].iloc[-1]
            st.metric(
                label="Límite de Crédito Año 5",
                value=f"€{limite_total:,.0f}",
                delta="25% de ventas"
            )

        with col2:
            uso_promedio = financiacion_df['Uso Póliza'].mean()
            st.metric(
                label="Uso Promedio de Póliza",
                value=f"€{uso_promedio:,.0f}",
                delta=f"{(uso_promedio/limite_total*100):.0f}% del límite" if limite_total > 0 else "N/A"
            )

        with col3:
            coste_total = financiacion_df['Coste Póliza'].sum()
            st.metric(
                label="Coste Financiero Total",
                value=f"€{coste_total:,.0f}",
                delta="6% anual s/dispuesto"
            )

        # Tabla de financiación
        financiacion_display = financiacion_df.copy()
        for col in financiacion_display.columns:
            if col != 'Año':
                financiacion_display[col] = financiacion_display[col].apply(
                    lambda x: f"€{x:,.0f}")

        st.dataframe(financiacion_display,
                     use_container_width=True, height=200)

        # Alerta si hay déficit
        if any(financiacion_df['Exceso/(Déficit)'] < 0):
            deficit_max = abs(financiacion_df['Exceso/(Déficit)'].min())
            st.warning(
                f"⚠️ **Alerta**: Necesitarás financiación adicional de €{deficit_max:,.0f} para cubrir el capital de trabajo en algún momento del proyecto.")

        # NUEVA SECCIÓN: Análisis Inteligente y Recomendaciones
        st.markdown("---")
        st.subheader("🤖 Análisis Inteligente y Recomendaciones")

        # Rating y viabilidad
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Rating del Proyecto", analisis_ia['rating'])
        with col2:
            viabilidad_color = "🟢" if "ALTA" in analisis_ia[
                'viabilidad'] else "🟡" if "MEDIA" in analisis_ia['viabilidad'] else "🔴"
            st.metric("Viabilidad",
                      f"{viabilidad_color} {analisis_ia['viabilidad']}")

        # Resumen ejecutivo
        st.markdown("### 📋 Resumen Ejecutivo")
        st.info(analisis_ia['resumen_ejecutivo'])

        # Fortalezas, Riesgos y Recomendaciones en columnas
        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("### 💪 Fortalezas")
            for fortaleza in analisis_ia['fortalezas']:
                st.success(f"✓ {fortaleza}")

        with col2:
            st.markdown("### ⚠️ Riesgos")
            for riesgo in analisis_ia['riesgos']:
                st.warning(f"! {riesgo}")

        with col3:
            st.markdown("### 💡 Recomendaciones")
            for recomendacion in analisis_ia['recomendaciones']:
                st.info(f"→ {recomendacion}")

        # Sección de descarga de informes profesionales
        st.markdown("---")
        st.subheader("📑 Documentos Ejecutivos")

        col1, col2, col3 = st.columns([1, 3, 1])

        with col2:
            # Generar PDF automáticamente
            try:
                with st.spinner('Preparando documentación ejecutiva...'):
                    pdf_bytes = generar_pdf_ejecutivo(
                        datos_empresa=datos_empresa,
                        pyl_df=pyl,
                        valoracion=valoracion,
                        analisis_ia=analisis_ia,
                        financiacion_df=financiacion_df
                    )

                # Mostrar botón de descarga con estilo premium
                st.download_button(
                    label="📄 Descargar Business Plan Ejecutivo (PDF)",
                    data=pdf_bytes,
                    file_name=f"BusinessPlan_{datos_empresa['nombre'].replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.pdf",
                    mime="application/pdf",
                    type="primary",
                    use_container_width=True,
                    help="Documento profesional para presentación a inversores y directivos"
                )

                st.success(
                "✅ Documento ejecutivo preparado - Formato profesional McKinsey/Goldman Sachs")

                # Información adicional
                with st.expander("ℹ️ Contenido del documento"):
                    st.markdown("""
                    **El Business Plan Ejecutivo incluye:**
                    - Executive Summary
                    - Key Investment Highlights  
                    - Proyecciones Financieras (5 años)
                    - Análisis Estratégico (DAFO)
                    - Valoración DCF con escenarios
                    - Conclusiones y recomendaciones
                    
                    **Diseñado para:** CEOs, CFOs, Inversores, Consejo de Administración
                    """)

            except Exception as e:
                st.error(f"Error preparando documentación: {str(e)}")
                st.info(
                    "Por favor, verifica que todos los datos estén completos y vuelve a generar la proyección.")

    with tab2:
        st.header("Cuenta de Resultados Proyectada (P&L)")

        # Recuperar resumen desde los datos guardados
        resumen = datos.get('resumen', 'Resumen no disponible')

        # Mostrar tabla con formato
        pyl_display = pyl.copy()

        # Formatear números para mejor visualización
        for col in pyl_display.columns:
            if col != 'Año' and '%' not in col:
                pyl_display[col] = pyl_display[col].apply(
                    lambda x: f"€{x:,.0f}")
            elif '%' in col:
                pyl_display[col] = pyl_display[col].apply(lambda x: f"{x}%")

        st.dataframe(
            pyl_display,
            use_container_width=True,
            height=600
        )

        # Botón de descarga
        csv = pyl.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Descargar P&L en CSV",
            data=csv,
            file_name=f"pyl_{nombre_empresa.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )

    with tab3:
        st.header("Visualizaciones")

        # Gráfico de Ventas y EBITDA
        fig1 = go.Figure()

        # Barras de ventas
        fig1.add_trace(go.Bar(
            x=pyl['Año'],
            y=pyl['Ventas'],
            name='Ventas',
            marker_color='lightblue',
            text=[f"€{v:,.0f}" for v in pyl['Ventas']],
            textposition='outside'
        ))

        # Línea de EBITDA
        fig1.add_trace(go.Scatter(
            x=pyl['Año'],
            y=pyl['EBITDA'],
            name='EBITDA',
            line=dict(color='green', width=3),
            mode='lines+markers',
            yaxis='y2'
        ))

        # Configuración del layout
        fig1.update_layout(
            title='Evolución de Ventas y EBITDA',
            xaxis_title='Año',
            yaxis=dict(title='Ventas (€)', side='left'),
            yaxis2=dict(title='EBITDA (€)', side='right', overlaying='y'),
            hovermode='x unified',
            height=500
        )

        st.plotly_chart(fig1, use_container_width=True)

        # Gráfico de márgenes
        fig2 = go.Figure()

        fig2.add_trace(go.Scatter(
            x=pyl['Año'],
            y=pyl['Margen Bruto %'],
            name='Margen Bruto %',
            line=dict(width=2),
            mode='lines+markers'
        ))

        fig2.add_trace(go.Scatter(
            x=pyl['Año'],
            y=pyl['EBITDA %'],
            name='Margen EBITDA %',
            line=dict(width=2),
            mode='lines+markers'
        ))

        fig2.add_trace(go.Scatter(
            x=pyl['Año'],
            y=pyl['Beneficio Neto %'],
            name='Margen Neto %',
            line=dict(width=2),
            mode='lines+markers'
        ))

        fig2.update_layout(
            title='Evolución de Márgenes',
            xaxis_title='Año',
            yaxis_title='Porcentaje (%)',
            hovermode='x unified',
            height=400
        )

        st.plotly_chart(fig2, use_container_width=True)

    with tab4:
        st.header("Resumen Ejecutivo")

        # Generar resumen si no existe
        if 'resumen' not in locals():
            resumen = f"""
            RESUMEN EJECUTIVO - {datos_empresa['nombre']}
            {'=' * 50}
            
            Sector: {datos_empresa['sector']}
            
            PROYECCIONES CLAVE:
            - Ventas año 5: €{pyl['Ventas'].iloc[-1]:,.0f}
            - EBITDA año 5: €{pyl['EBITDA'].iloc[-1]:,.0f} ({pyl['EBITDA %'].iloc[-1]:.1f}%)
            - Valoración: €{valoracion['valor_empresa']:,.0f}
            """

        # Mostrar resumen en un contenedor con estilo
        st.markdown(
            f"""
            <div style="background-color: #F8FAFC; padding: 2rem; border-radius: 0.5rem; border: 1px solid #E2E8F0;">
                <pre style="white-space: pre-wrap; font-family: monospace;">{resumen}</pre>
            </div>
            """,
            unsafe_allow_html=True
        )

        # Botón para descargar resumen
        st.download_button(
            label="📥 Descargar Resumen en TXT",
            data=resumen,
            file_name=f"resumen_ejecutivo_{nombre_empresa.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.txt",
            mime="text/plain"
        )

else:
    # Pantalla de bienvenida cuando no hay proyección
    st.info("👈 Introduce los datos de tu empresa en la barra lateral y pulsa **Generar Proyección**")

    # Mostrar ejemplo
    with st.expander("📚 Ver ejemplo de uso"):
        st.markdown("""
        ### Cómo usar Business Plan IA:
        
        1. **Información General**: Introduce el nombre y sector de tu empresa
        2. **Ventas Históricas**: Añade las ventas de los últimos 2-3 años
        3. **Estructura de Costos**: Define tus costos variables y fijos
        4. **Parámetros Financieros**: Si tienes deuda, indícalo
        5. **Genera la Proyección**: Pulsa el botón y obtén tu Business Plan
        
        ### Sectores predefinidos:
        - **Hostelería**: Restaurantes, bares, hoteles (margen ~65%)
        - **Tecnología**: SaaS, software, apps (margen ~80%)
        - **Ecommerce**: Tiendas online (margen ~35%)
        - **Consultoría**: Servicios profesionales (margen ~90%)
        
        ### ¿Qué obtendrás?
        - P&L proyectado a 5 años
        - Dashboard con métricas clave
        - Gráficos interactivos
        - Resumen ejecutivo descargable
        """)

# Footer
st.markdown("---")
st.markdown(
    """
    <div style="text-align: center; color: #64748B;">
        <p>Creado con ❤️ por Business Plan IA | Powered by Claude & Streamlit</p>
    </div>
    """,
    unsafe_allow_html=True
)
