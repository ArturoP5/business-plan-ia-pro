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
from utils.pdf_generator_pro import generar_pdf_profesional
from utils.api_data_collector import APIDataCollector
from utils.excel_handler import crear_plantilla_excel, leer_excel_datos

# AUTENTICACIÓN BÁSICA - Friends & Family Beta
def check_password():
    """Returns `True` if the user had the correct password."""
    
    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if st.session_state.get("password", "") == st.secrets.get("APP_PASSWORD", "V@luPr0!A#2024"):
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown("## 🔐 Bienvenido a ValuProIA")
            st.markdown("*Versión Beta - Acceso Friends & Family*")
            st.text_input(
                "Contraseña", 
                type="password", 
                on_change=password_entered, 
                key="password",
                help="Mínimo 10 caracteres con mayúsculas, minúsculas, números y símbolos"
            )
            
            # Sistema de recuperación
            with st.expander("¿Olvidaste la contraseña?"):
                st.info("""
                📧 **Opciones de recuperación:**
                
                1. Contacta directamente:
                   - Email: arturo.pineiro@mac.com
                
                2. Pista: La contraseña incluye:
                   - El nombre de la app con símbolos
                   - El año actual
                   - Símbolos especiales (@, !, #)
                """)
        return False
    
    elif not st.session_state["password_correct"]:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown("## 🔐 Bienvenido a ValuProIA")
            st.text_input(
                "Contraseña", 
                type="password", 
                on_change=password_entered, 
                key="password"
            )
            st.error("😕 Contraseña incorrecta. Verifica mayúsculas y símbolos.")
            
            if st.button("¿Necesitas ayuda?"):
                st.info("💡 Contacta a arturo.pineiro@mac.com para obtener acceso")
        return False
    
    else:
        return True

# Verificar contraseña antes de mostrar la app
if not check_password():
    st.stop()

st.set_page_config(
    page_title="ValuProIA",
    page_icon="assets/icon_favicon_32.ico",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== FUNCIONES HELPER ====================
def formato_numero(label, value=0, key=None, decimales=0, help_text=None, min_value=None, max_value=None):
    """Helper para inputs numéricos con formato consistente"""
    if decimales > 0:
        formato = f"%.{decimales}f"
        step = 10**(-decimales)
        value = float(value)
        min_value = float(min_value) if min_value is not None else None
        max_value = float(max_value) if max_value is not None else None
    else:
        formato = "%d"
        step = 1000 if value >= 10000 else 100
        value = int(value)
        min_value = int(min_value) if min_value is not None else None
        max_value = int(max_value) if max_value is not None else None
    
    return st.number_input(
        label,
        value=value,
        step=step,
        format=formato,
        key=key,
        help=help_text,
        min_value=min_value,
        max_value=max_value
    )
def formato_display(valor):
    """Formatea un número con separadores de miles para display"""
    if valor >= 1000:
        return f"{valor:,.0f}".replace(",", ".")
    return f"{valor:.0f}"

def formato_porcentaje(label, value=0, key=None, help_text=None, min_value=0, max_value=100):
    """Helper para inputs de porcentaje"""
    return formato_numero(
        label + " (%)",
        value=value,
        key=key,
        decimales=2,
        help_text=help_text,
        min_value=min_value,
        max_value=max_value
    )

def get_simbolo_moneda():
    """Obtiene el símbolo de moneda actual"""
    return st.session_state.get('simbolo_moneda', '€')

# ========================================================

def mostrar_resumen_ejecutivo_profesional(num_empleados_actual=None, año_fundacion_actual=None):
    """Muestra el resumen ejecutivo profesional mejorado"""
    
    if 'datos_guardados' not in st.session_state:
        st.error("No hay datos disponibles. Genera primero las proyecciones.")
        return
    
    datos = st.session_state.datos_guardados
    
    # Extraer datos necesarios
    empresa = datos['nombre_empresa']
    sector = datos['sector']
    valoracion_prof = datos.get('valoracion_profesional', {})
    metricas = datos.get('metricas', {})
    pyl = datos.get('pyl', datos.get('proyecciones', {}).get('pyl'))
    ratios = datos.get('ratios', datos.get('proyecciones', {}).get('ratios'))
    balance = datos.get('balance', datos.get('proyecciones', {}).get('balance'))

    # Obtener valoración real
    valor_empresa = valoracion_prof.get('valoracion_final', 0)
    tir_real = valoracion_prof.get('dcf_detalle', {}).get('tir', metricas.get('tir_proyecto', 0))
    
    # SNAPSHOT EJECUTIVO
    st.markdown("## 🎯 **SNAPSHOT EJECUTIVO**")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "Valoración Empresa",
            f"{get_simbolo_moneda()}{valor_empresa:,.0f}",
            delta=f"Múltiplo {valoracion_prof.get('multiples_detalle', {}).get('ev_ebitda_final', 15):.1f}x"
        )
    
    with col2:
        rating = "⭐⭐⭐⭐" if tir_real > 20 else "⭐⭐⭐" if tir_real > 15 else "⭐⭐"
        st.metric("Rating Inversión", rating)
    
    with col3:
        viabilidad = "🟢 ALTA" if tir_real > 20 else "🟡 MEDIA" if tir_real > 10 else "🔴 BAJA"
        st.metric("Viabilidad", viabilidad)
    
    # Segunda fila de métricas
    col4, col5, col6 = st.columns(3)
    
    with col4:
        st.metric("TIR Proyecto", f"{tir_real:.1f}%")
    
    with col5:
        # Calcular payback period real
        cash_flow = datos.get('cash_flow', {})
        if 'Free Cash Flow' in cash_flow:
            fcf_values = cash_flow['Free Cash Flow'].values
            inversion_inicial = fcf_values[0] if fcf_values[0] < 0 else -1000000  # Si no hay inversión inicial negativa, asumir 1M
            
            # Calcular flujos acumulados
            acumulado = 0
            payback = None
            for i, flujo in enumerate(fcf_values[1:], 1):  # Empezar desde año 1
                acumulado += flujo
                if acumulado + inversion_inicial >= 0:
                    # Interpolación para obtener el momento exacto
                    flujo_faltante = -(inversion_inicial + acumulado - flujo)
                    fraccion_año = flujo_faltante / flujo if flujo > 0 else 0
                    payback = i - 1 + fraccion_año
                    break
            
            if payback is None:
                payback = ">5"  # No se recupera en 5 años
            else:
                payback = f"{payback:.1f}"
        else:
            payback = "N/D"
        if isinstance(payback, (int, float)):
            st.metric("Payback Period", f"{payback:.1f} años")
        else:
            st.metric("Payback Period", f"{payback} años")
            
    with col6:
        roi = metricas.get('roi_proyectado', 0)
        st.metric("ROI Esperado", f"{roi:.1f}%")
         
    # RESUMEN DE NEGOCIO
    st.markdown("---")
    st.markdown("### 📈 **RESUMEN DE NEGOCIO**")   
    
    col_neg1, col_neg2 = st.columns(2)
    
    with col_neg1:
        st.markdown(f"""
        **{empresa}**  
        📍 Sector: {sector}  
        👥 Empleados: {st.session_state.get('num_empleados_sidebar', 10)}  
        📅 Fundada: {st.session_state.get('año_fundacion_sidebar', 2020)}
        """)
    
    # Calcular métricas históricas reales
    datos_empresa = datos.get('datos_empresa', {})
    if datos_empresa and 'ventas_historicas' in datos_empresa:
        ventas_historicas = datos_empresa['ventas_historicas'][-1] if isinstance(datos_empresa['ventas_historicas'], list) else datos_empresa['ventas_historicas']
        costos_pct = datos_empresa.get('costos_variables_pct', 0)
        gastos_personal = datos_empresa.get('gastos_personal', 0)
        gastos_generales = datos_empresa.get('gastos_generales', 0)
        gastos_marketing = datos_empresa.get('gastos_marketing', 0)
        
        margen_bruto = ventas_historicas * (1 - costos_pct)
        ebitda_actual = margen_bruto - gastos_personal - gastos_generales - gastos_marketing
        margen_ebitda_actual = (ebitda_actual / ventas_historicas * 100) if ventas_historicas > 0 else 0
        ebitda_historico = margen_bruto - gastos_personal - gastos_generales - gastos_marketing
        margen_ebitda_historico = (ebitda_historico / ventas_historicas * 100) if ventas_historicas > 0 else 0
        
    else:
        # Obtener valores históricos del sidebar - 100% dinámico
        ventas_historicas = st.session_state.get('ventas_1', pyl['Ventas'].iloc[0])
        
        # Obtener todos los valores del sidebar usando las keys
        costos_pct = st.session_state.get('costos_variables_slider', 40) / 100
        gastos_personal = st.session_state.get('gastos_personal_key', 0)
        gastos_generales = st.session_state.get('gastos_generales_key', 0)
        gastos_marketing = st.session_state.get('gastos_marketing_key', 0)
        
        # Calcular EBITDA histórico con valores reales del sidebar
        margen_bruto = ventas_historicas * (1 - costos_pct)
        ebitda_historico = margen_bruto - gastos_personal - gastos_generales - gastos_marketing
        margen_ebitda_historico = (ebitda_historico / ventas_historicas * 100) if ventas_historicas > 0 else 0

    with col_neg2:
        st.markdown(f"""
        **Posición Financiera:**  
        💰 Ventas actuales: {get_simbolo_moneda()}{ventas_historicas:,.0f}  
        📊 EBITDA actual: {get_simbolo_moneda()}{ebitda_historico:,.0f}  
        💵 Margen EBITDA: {margen_ebitda_historico:.1f}%
        """)
    
    # MÉTRICAS FINANCIERAS CLAVE
    st.markdown("---")
    st.markdown("### 💰 **MÉTRICAS FINANCIERAS CLAVE**")
    
    # Crear tabla de evolución
    metricas_tabla = pd.DataFrame({
        'Métrica': ['Ventas (€k)', 'EBITDA (€k)', 'Margen EBITDA (%)', 'Cash Flow (€k)'],
        'Actual': [
            f"{ventas_historicas/1000:,.0f}",
            f"{ebitda_historico/1000:,.0f}",
            f"{margen_ebitda_historico:.1f}%",
            "N/A"  # No hay cash flow histórico
        ],
        'Año 1': [
            f"{pyl['Ventas'].iloc[0]/1000:,.0f}",
            f"{pyl['EBITDA'].iloc[0]/1000:,.0f}",
            f"{pyl['EBITDA %'].iloc[0]:.1f}%",
            f"{cash_flow['Free Cash Flow'].iloc[0]/1000:,.0f}"
        ],
        'Año 2': [
            f"{pyl['Ventas'].iloc[1]/1000:,.0f}",
            f"{pyl['EBITDA'].iloc[1]/1000:,.0f}",
            f"{pyl['EBITDA %'].iloc[1]:.1f}%",
            f"{cash_flow['Free Cash Flow'].iloc[1]/1000:,.0f}"
        ],
        'Año 3': [
            f"{pyl['Ventas'].iloc[2]/1000:,.0f}",
            f"{pyl['EBITDA'].iloc[2]/1000:,.0f}",
            f"{pyl['EBITDA %'].iloc[2]:.1f}%",
            f"{cash_flow['Free Cash Flow'].iloc[2]/1000:,.0f}"
        ],
        'Año 4': [
            f"{pyl['Ventas'].iloc[3]/1000:,.0f}",
            f"{pyl['EBITDA'].iloc[3]/1000:,.0f}",
            f"{pyl['EBITDA %'].iloc[3]:.1f}%",
            f"{cash_flow['Free Cash Flow'].iloc[3]/1000:,.0f}"
        ],
        'Año 5': [
            f"{pyl['Ventas'].iloc[4]/1000:,.0f}",
            f"{pyl['EBITDA'].iloc[4]/1000:,.0f}",
            f"{pyl['EBITDA %'].iloc[4]:.1f}%",
            f"{cash_flow['Free Cash Flow'].iloc[4]/1000:,.0f}"
        ]
    })
    
    st.dataframe(metricas_tabla, hide_index=True, use_container_width=True)

   # INDICADORES FINANCIEROS CLAVE
    st.markdown("---")
    st.markdown("### 📊 **INDICADORES FINANCIEROS CLAVE**")
    
    # 1. INDICADORES DE RENTABILIDAD
    st.markdown("#### 1️⃣ **Rentabilidad** *(¿Qué tan bien gana dinero la empresa?)*")
    with st.expander("💡 **¿Qué significan estos indicadores de Rentabilidad?**"):
        st.markdown("""
        ### 📊 Indicadores de Rentabilidad - Guía para No Financieros
        
        **🎯 ROE (Return on Equity - Rentabilidad sobre Capital)**
        - **¿Qué mide?**: Cuánto gana la empresa por cada € que invirtieron los socios
        - **Ejemplo**: ROE del 15% = Por cada 100€ invertidos, genera 15€ de beneficio al año
        - **Benchmark sector**: 10-15% es saludable, >20% es excelente
        - **🚨 Alerta**: <5% indica baja rentabilidad para los accionistas
                    
        **🏭 ROCE (Return on Capital Employed - Rentabilidad sobre Capital Empleado)**
        - **¿Qué mide?**: Cuánto gana la empresa con el capital que usa para operar
        - **Ejemplo**: ROCE del 23% = Por cada 100€ de capital operativo, genera 23€ de beneficio
        - **Benchmark sector**: 15-20% es bueno, >25% es excelente
        - **🚨 Alerta**: <10% indica uso ineficiente del capital
        - **💡 Diferencia con ROE**: ROCE mide eficiencia operativa, ROE mide retorno a accionistas           
        
        **📈 Margen EBITDA**
        - **¿Qué mide?**: De cada 100€ vendidos, cuántos quedan como beneficio operativo
        - **Ejemplo**: Margen 25% = De 100€ de ventas, 25€ son beneficio operativo
        - **Benchmark sector**: 
          - Servicios: 15-25%
          - Tecnología: 20-35%
          - Retail: 8-15%
        - **🚨 Alerta**: <10% puede indicar problemas de eficiencia
        
        **💰 Margen Neto**
        - **¿Qué mide?**: Beneficio final después de TODOS los gastos e impuestos
        - **Ejemplo**: Margen 10% = De 100€ vendidos, 10€ son beneficio limpio
        - **Benchmark**: 5-10% es saludable según el sector
        - **🚨 Alerta**: Negativo significa pérdidas
        
        **📊 ¿Cómo interpretarlos juntos?**
        - **Todos altos**: Empresa muy rentable y eficiente ✅
        - **EBITDA alto, Neto bajo**: Posibles problemas de deuda o impuestos ⚠️
        - **ROE bajo con márgenes altos**: Demasiado capital sin usar eficientemente 💡
        """)
    col_rent1, col_rent2, col_rent3, col_rent4, col_rent5 = st.columns(5)
    
    with col_rent1:
        if 'Costos' in pyl.columns:
            margen_bruto = ((pyl['Ventas'].iloc[-1] - pyl['Costos'].iloc[-1]) / pyl['Ventas'].iloc[-1] * 100)
        else:
            margen_bruto = pyl.get('Margen Bruto %', pd.Series([9.0])).iloc[-1]
        st.metric("Margen Bruto", f"{margen_bruto:.1f}%", help="(Ventas - Coste Ventas) / Ventas")
    
    with col_rent2:
        st.metric("Margen EBITDA", f"{pyl['EBITDA %'].iloc[-1]:.1f}%", help="EBITDA / Ventas")
    
    with col_rent3:
        margen_neto = (pyl['Beneficio Neto'].iloc[-1] / pyl['Ventas'].iloc[-1] * 100)
        st.metric("Margen Neto", f"{margen_neto:.1f}%", help="Beneficio Neto / Ventas")
    
    with col_rent4:
        patrimonio_neto = datos.get('balance', {}).get('patrimonio_neto', pd.Series([100000])).iloc[-1]
        # En app.py línea ~223, antes del if patrimonio_neto > 0:
        
        if patrimonio_neto > 0:
            roe = (pyl['Beneficio Neto'].iloc[-1] / patrimonio_neto) * 100
        else:
            roe = 0
        st.metric("ROE", f"{roe:.1f}%", help="Beneficio Neto / Patrimonio Neto")

    with col_rent5:
        # Obtener ROCE del DataFrame de ratios
        roce = ratios.iloc[-1].get('roce_%', 0) if ratios is not None and not ratios.empty else 0
        st.metric("ROCE", f"{roce:.1f}%", help="EBIT / Capital Empleado")
    
    # 2. INDICADORES DE LIQUIDEZ
    st.markdown("#### 2️⃣ **Liquidez** *(¿Puede pagar sus deudas a corto plazo?)*")
    with st.expander("💡 **¿Qué significan estos indicadores de Liquidez?**"):
        st.markdown("""
        ### 💧 Indicadores de Liquidez - Guía para No Financieros
        
        **🔵 Ratio Corriente (Current Ratio)**
        - **¿Qué mide?**: Si puede pagar todas sus deudas del próximo año
        - **Cálculo simple**: Activo Corriente ÷ Pasivo Corriente
        - **Ejemplo**: Ratio 1.5 = Tiene 1.50€ disponibles por cada 1€ que debe
        - **Benchmark óptimo**: 
          - 1.5 - 2.0 → Situación saludable ✅
          - < 1.0 → Problemas de liquidez 🚨
          - > 3.0 → Exceso de recursos sin usar 💡
        
        **⚡ Prueba Ácida (Quick Ratio)**
        - **¿Qué mide?**: Capacidad de pago inmediata (sin vender inventario)
        - **Por qué importa**: El inventario puede tardar meses en convertirse en dinero
        - **Benchmark**: 
          - > 1.0 → Excelente liquidez inmediata ✅
          - 0.8 - 1.0 → Aceptable
          - < 0.8 → Dependencia del inventario ⚠️
        
        **💰 Capital de Trabajo**
        - **¿Qué es?**: Dinero disponible para las operaciones diarias
        - **Cálculo**: Activo Corriente - Pasivo Corriente
        - **Ejemplo positivo**: +500K€ = Colchón financiero para 2-3 meses
        - **Si es negativo**: La empresa financia operaciones con deuda 🚨
        
        **📊 Días de Caja**
        - **¿Qué mide?**: Cuántos días puede operar con el efectivo actual
        - **Cálculo**: Efectivo ÷ Gastos diarios
        - **Benchmark**: 
          - > 90 días → Muy seguro ✅
          - 30-90 días → Normal
          - < 30 días → Riesgo de quedarse sin efectivo ⚠️
        
        **💡 Señales de Alerta**:
        - Ratio corriente cayendo trimestre a trimestre
        - Capital de trabajo negativo creciente
        - Días de caja < 30
        - Prueba ácida < 0.5
        """)
    col_liq1, col_liq2, col_liq3, col_liq4 = st.columns(4)
    
    with col_liq1:
        st.metric("Ratio Liquidez", f"{ratios.iloc[-1]['ratio_liquidez']:.2f}x", help="Activo Corriente / Pasivo Corriente")
    
    with col_liq2:
        # Calcular prueba ácida (sin inventarios)
        balance = datos.get('balance', {})

        activo_liquido = balance.get('tesoreria', pd.Series([0])).iloc[-1] + balance.get('clientes', pd.Series([0])).iloc[-1]
        pasivo_corriente = (balance.get('deuda_cp', pd.Series([0])) + balance.get('proveedores', pd.Series([0]))).iloc[-1]
        prueba_acida = activo_liquido / pasivo_corriente if pasivo_corriente > 0 else 0
        st.metric("Prueba Ácida", f"{prueba_acida:.2f}x", help="(Activo Corriente - Inventario) / Pasivo Corriente")
    
    with col_liq3:
        fondo_maniobra = (balance.get('tesoreria', pd.Series([0])) + balance.get('clientes', pd.Series([0])) + balance.get('inventario', pd.Series([0]))).iloc[-1] - balance.get('Pasivo Corriente', pd.Series([0])).iloc[-1]
        st.metric("Fondo Maniobra", f"{get_simbolo_moneda()}{fondo_maniobra:,.0f}", help="Activo Corriente - Pasivo Corriente")
    
    with col_liq4:
        tesoreria = balance['tesoreria'].iloc[-1] if 'tesoreria' in balance else 0
        gastos_diarios = (pyl['Gastos Personal'].iloc[-1] + pyl['Otros Gastos'].iloc[-1]) / 365
        dias_caja = int(tesoreria / gastos_diarios) if gastos_diarios > 0 and tesoreria > 0 else 0
        st.metric("Días de Caja", f"{dias_caja:.0f}", help="Días que puede operar con la caja actual")
    
    # 3. INDICADORES DE SOLVENCIA Y ENDEUDAMIENTO
    st.markdown("#### 3️⃣ **Solvencia y Endeudamiento** *(¿Cómo se financia?)*")
    with st.expander("💡 **¿Qué significan estos indicadores de Solvencia y Endeudamiento?**"):
        st.markdown("""
        ### 🏦 Indicadores de Solvencia y Endeudamiento - Guía para No Financieros
        
        **📊 Ratio de Endeudamiento (Deuda/EBITDA)**
        - **¿Qué mide?**: Años necesarios para pagar toda la deuda con los beneficios actuales
        - **Ejemplo**: Ratio 3x = Tardaría 3 años en pagar toda la deuda
        - **Benchmark por situación**:
          - < 2x → Endeudamiento bajo, capacidad de inversión ✅
          - 2x - 3x → Endeudamiento moderado, normal
          - 3x - 4x → Endeudamiento alto, precaución ⚠️
          - > 4x → Sobreendeudamiento, riesgo alto 🚨
        
        **💼 Ratio Deuda/Patrimonio (D/E)**
        - **¿Qué mide?**: Cuánto debe la empresa vs. cuánto vale para los socios
        - **Ejemplo**: D/E = 0.5 = Por cada 1€ de los socios, debe 0.50€
        - **Benchmark sector**:
          - < 0.5 → Conservador, mucho margen ✅
          - 0.5 - 1.0 → Equilibrado
          - 1.0 - 2.0 → Apalancado (común en inmobiliarias)
          - > 2.0 → Muy apalancado, mayor riesgo 🚨
        
        **🛡️ Cobertura de Intereses (EBITDA/Intereses)**
        - **¿Qué mide?**: Cuántas veces puede pagar los intereses con sus beneficios
        - **Ejemplo**: Cobertura 5x = Genera 5€ por cada 1€ de intereses
        - **Interpretación**:
          - > 3x → Cómoda capacidad de pago ✅
          - 2x - 3x → Margen ajustado pero suficiente
          - 1.5x - 2x → Situación límite ⚠️
          - < 1.5x → Dificultad para pagar intereses 🚨
        
        **🏗️ Ratio de Autonomía Financiera**
        - **¿Qué mide?**: % del negocio financiado con recursos propios
        - **Cálculo**: Patrimonio Neto ÷ Total Activo × 100
        - **Interpretación**:
          - > 50% → Alta autonomía, bajo riesgo ✅
          - 30% - 50% → Equilibrio normal
          - < 30% → Alta dependencia de financiación externa ⚠️
        
        **⚠️ Señales de Alerta en Conjunto**:
        - Deuda/EBITDA > 4x + Cobertura < 2x = Problema grave
        - D/E creciendo + Márgenes cayendo = Espiral peligrosa
        - Autonomía < 20% = Vulnerable a crisis de crédito
        
        **💡 Consejo**: No es malo tener deuda si genera más rentabilidad que su coste
        """)
    col_solv1, col_solv2, col_solv3, col_solv4 = st.columns(4)
    
    with col_solv1:
        st.metric("Ratio Endeudamiento", f"{ratios.iloc[-1]['ratio_endeudamiento']:.2f}x", help="Deuda Total / EBITDA")
    
    with col_solv2:
        cobertura = ratios.iloc[-1]['cobertura_intereses']
        if cobertura >= 999:
            cobertura_texto = "Sin deuda"
        else:
            cobertura_texto = f"{cobertura:.1f}x"
        st.metric("Cobertura Intereses", cobertura_texto, help="EBITDA / Gastos Financieros")
    
    with col_solv3:
        deuda_patrimonio = ratios.iloc[-1].get('deuda_patrimonio', 0)
        st.metric("Deuda/Patrimonio", f"{deuda_patrimonio:.2f}x", help="Deuda Total / Patrimonio Neto")
    
    with col_solv4:
        autonomia_financiera = (balance.get('patrimonio neto', pd.Series([1])).iloc[-1] / balance.get('total activo', pd.Series([1])).iloc[-1] * 100)
        st.metric("Autonomía Financiera", f"{autonomia_financiera:.1f}%", help="Patrimonio Neto / Total Activo")
    
    # 4. INDICADORES DE EFICIENCIA
    st.markdown("#### 4️⃣ **Eficiencia Operativa** *(¿Qué tan bien usa sus recursos?)*")
    with st.expander("💡 **¿Qué significan estos indicadores de Eficiencia Operativa?**"):
        st.markdown("""
        ### ⚙️ Indicadores de Eficiencia Operativa - Guía para No Financieros
        
        **📦 Rotación de Inventario**
        - **¿Qué mide?**: Cuántas veces al año vende todo su inventario
        - **Ejemplo**: Rotación 12x = Vende todo el stock cada mes
        - **Por qué importa**: Inventario parado = dinero muerto
        - **Benchmark por sector**:
          - Alimentación: 12-24x (productos frescos) ✅
          - Tecnología: 6-12x (obsolescencia rápida)
          - Moda: 4-6x (por temporadas)
          - Industrial: 2-4x (productos duraderos)
        - **🚨 Alerta**: Rotación cayendo = acumulación de stock obsoleto
        
        **💳 Días de Cobro (DSO - Days Sales Outstanding)**
        - **¿Qué mide?**: Días que tarda en cobrar a sus clientes
        - **Ejemplo**: 45 días = Los clientes pagan mes y medio después
        - **Impacto**: Más días = más dinero "prestado" a clientes
        - **Benchmark**:
          - < 30 días → Excelente gestión de cobros ✅
          - 30-60 días → Normal en B2B
          - 60-90 días → Revisar política de crédito ⚠️
          - > 90 días → Riesgo de impagos alto 🚨
        
        **📅 Días de Pago (DPO - Days Payables Outstanding)**
        - **¿Qué mide?**: Días que tarda en pagar a proveedores
        - **Estrategia**: Equilibrio entre liquidez y relación con proveedores
        - **Benchmark**:
          - 30-45 días → Estándar mercado
          - > 60 días → Puede indicar problemas de caja ⚠️
          - < 30 días → Quizás pierde descuentos por pronto pago
        
        **🔄 Ciclo de Conversión de Efectivo**
        - **Fórmula**: Días Inventario + Días Cobro - Días Pago
        - **¿Qué significa?**: Días que el dinero está "atrapado" en operaciones
        - **Ejemplo**: 30 + 45 - 60 = 15 días
        - **Objetivo**: Cuanto menor, mejor
        - **Ideal**: Negativo (cobras antes de pagar) 🎯
        
        **📈 Productividad por Empleado**
        - **¿Qué mide?**: Ventas ÷ Número de empleados
        - **Benchmark variable por sector**:
          - Tecnología: >200K€/empleado
          - Servicios: 80-150K€/empleado
          - Retail: 150-300K€/empleado
        
        **💡 Mejoras Rápidas de Eficiencia**:
        - Reducir días de cobro → Descuentos por pronto pago
        - Optimizar inventario → Sistema Just-in-Time
        - Negociar plazos pago → Sin dañar relación proveedores
        - Automatizar procesos → Aumentar productividad
        
        **⚠️ Señal de Excelencia**: 
        Ciclo de efectivo negativo = El negocio se autofinancia con proveedores
        """)
    col_ef1, col_ef2, col_ef3, col_ef4 = st.columns(4)
    
    with col_ef1:
        dias_cobro = datos.get('datos_empresa', {}).get('dias_cobro', 60)
        st.metric("Días de Cobro", f"{dias_cobro}", help="Días promedio para cobrar a clientes")
    
    with col_ef2:
        dias_pago = datos.get('datos_empresa', {}).get('dias_pago', 30)
        st.metric("Días de Pago", f"{dias_pago}", help="Días promedio para pagar a proveedores")
    
    with col_ef3:
        ciclo_caja = dias_cobro - dias_pago
        st.metric("Ciclo de Caja", f"{ciclo_caja} días", help="Días cobro - Días pago")
    
    with col_ef4:
        total_activo = balance['total_activo'].iloc[-1] if 'total_activo' in balance else 1
        rotacion_activos = pyl['Ventas'].iloc[-1] / total_activo if total_activo > 0 else 0
        st.metric("Rotación Activos", f"{rotacion_activos:.2f}x", help="Ventas / Total Activos")
    # FORTALEZAS COMPETITIVAS
    st.markdown("---")
    st.markdown("### 💪 **FORTALEZAS COMPETITIVAS**")
    
    fortalezas_mejoradas = [
        f"**Rentabilidad sólida**: Margen EBITDA del {pyl['EBITDA %'].iloc[-1]:.1f}% (año 5)",
        f"**Bajo endeudamiento**: Ratio deuda/EBITDA de {ratios.iloc[-1]['ratio_endeudamiento']:.2f}x",
        f"**Eficiencia operativa**: ROE del {ratios.iloc[-1].get('roe_%', 0):.0f}% y ROCE del {ratios.iloc[-1].get('roce_%', 0):.0f}%",
        f"**Posición de caja**: {get_simbolo_moneda()}{balance['tesoreria'].iloc[-1]:,.0f} proyectada año 5",
        f"**Crecimiento sostenible**: CAGR {metricas.get('cagr_ventas', 0):.1f}% con generación positiva de caja"
    ]
    
    for fortaleza in fortalezas_mejoradas:
        st.success(f"✓ {fortaleza}")
    
    # RIESGOS Y ALERTAS
    st.markdown("---")
    st.markdown("### ⚠️ **RIESGOS Y ALERTAS**")
    
    # Analizar riesgos basados en métricas reales
    riesgos_identificados = []
    
    # Riesgos basados en métricas
    if metricas.get('cagr_ventas', 0) < 5:
        riesgos_identificados.append(f"**Crecimiento limitado**: {metricas.get('cagr_ventas', 0):.1f}% CAGR vs 15-20% del sector")
    
    if ratios.iloc[-1]['ratio_liquidez'] < 1.5:
        riesgos_identificados.append(f"**Liquidez ajustada**: Ratio de liquidez {ratios.iloc[-1]['ratio_liquidez']:.2f}x")
    
    # Riesgos basados en tamaño/estructura
    num_empleados = datos.get('datos_empresa', {}).get('num_empleados', datos.get('datos_empresa', {}).get('empleados', 12))
    if num_empleados < 10:
        riesgos_identificados.append(f"**Equipo muy reducido**: Solo {num_empleados} empleados, riesgo operativo alto")
    elif num_empleados > 50:
        riesgos_identificados.append(f"**Estructura pesada**: {num_empleados} empleados, riesgo de ineficiencia")
    
    # Riesgos por sector
    sector = datos.get('sector', '').lower()
    if 'ecommerce' in sector or 'online' in sector:
        riesgos_identificados.append("**Márgenes ajustados**: Presión competitiva en precios online")
    elif 'tecnolog' in sector:
        riesgos_identificados.append("**Obsolescencia tecnológica**: Necesidad constante de innovación")
    elif 'industrial' in sector:
        riesgos_identificados.append("**Intensivo en capital**: Requiere inversiones continuas en activos")
    
    # Riesgos por endeudamiento
    ratio_deuda = ratios.iloc[-1].get('ratio_endeudamiento', 0)
    if ratio_deuda > 3:
        riesgos_identificados.append(f"**Alto endeudamiento**: Ratio deuda/EBITDA de {ratio_deuda:.1f}x")
    
    # Si no hay riesgos específicos, añadir uno genérico
    if len(riesgos_identificados) == 0:
        riesgos_identificados.append("**Entorno competitivo**: Mantener vigilancia del mercado")
    
    for riesgo in riesgos_identificados:
        st.warning(f"! {riesgo}")

    # RECOMENDACIONES ESTRATÉGICAS
    st.markdown("---")
    st.markdown("### 🎯 **RECOMENDACIONES ESTRATÉGICAS**")
    
    col_rec1, col_rec2, col_rec3 = st.columns(3)
    
    with col_rec1:
        st.markdown("**Corto Plazo (0-12 meses)**")
        recom_corto = []
        
        # Recomendaciones basadas en métricas
        if ratios.iloc[-1].get('ratio_endeudamiento', 0) < 0.5:
            recom_corto.append("✅ Considerar leverage moderado para acelerar crecimiento")
        else:
            recom_corto.append("✅ Reducir endeudamiento actual")
            
        if datos.get('datos_empresa', {}).get('num_empleados', 0) < 20:
            recom_corto.append("✅ Fortalecer equipo en áreas clave")
        
        if 'ecommerce' in datos.get('sector', '').lower():
            recom_corto.append("✅ Optimizar conversión y AOV online")
        elif 'tecnolog' in datos.get('sector', '').lower():
            recom_corto.append("✅ Acelerar desarrollo de producto")
        
        st.info("\n".join(recom_corto[:3]))  # Máximo 3 recomendaciones
    
    with col_rec2:
        st.markdown("**Medio Plazo (1-3 años)**")
        recom_medio = []
        
        if metricas.get('cagr_ventas', 0) > 15:
            recom_medio.append("📊 Consolidar crecimiento actual")
        else:
            recom_medio.append("📊 Acelerar crecimiento orgánico")
            
        if valor_empresa > 5000000:
            recom_medio.append("🚀 Expansión internacional")
        else:
            recom_medio.append("🚀 Expansión nacional primero")
            
        recom_medio.append("💡 Digitalización de procesos")
        
        st.info("\n".join(recom_medio[:3]))
    
    with col_rec3:
        st.markdown("**Largo Plazo (3-5 años)**")
        recom_largo = []
        
        if datos.get('empresa_familiar') == 'Sí':
            recom_largo.append("🏭 Profesionalización del gobierno corporativo")
        else:
            recom_largo.append("🏭 Consolidación sectorial vía M&A")
            
        if valor_empresa > 10000000:
            recom_largo.append("📈 Preparación para salida a bolsa")
        else:
            recom_largo.append("📈 Preparación para ronda Serie A/B")
            
        recom_largo.append("🌍 Liderazgo en sostenibilidad")
        
        st.info("\n".join(recom_largo[:3]))
    
    # INVESTMENT THESIS (si existe)
    if datos.get('analisis_ia', {}).get('resumen_ejecutivo'):
        st.markdown("---")
        st.markdown("### 📊 **INVESTMENT THESIS - ANÁLISIS CFO**")
        st.info(datos['analisis_ia']['resumen_ejecutivo'])

    # CONCLUSIÓN
    st.markdown("---")
    st.markdown("### 🏁 **CONCLUSIÓN Y PRÓXIMOS PASOS**")
    
    conclusion_text = f"""
    La empresa **{empresa}** presenta fundamentos sólidos con una valoración atractiva de **{get_simbolo_moneda()}{valor_empresa:,.0f}**.
    
    **Aspectos destacados:**
    - TIR del proyecto: **{tir_real:.1f}%**
    - Margen EBITDA sostenible: **{metricas.get('margen_ebitda_promedio', 0):.1f}%**
    - Generación de caja positiva en todos los años
    
    **Recomendación:** {'✅ INVERTIR' if tir_real > 15 else '⚠️ ANALIZAR CON DETALLE' if tir_real > 10 else '❌ REPLANTEAR PROYECTO'}
    
    **Próximos pasos sugeridos:**
    1. Due diligence detallada
    2. Negociación de términos de inversión
    3. Plan de 100 días post-inversión
    """
    
    st.info(conclusion_text)
    
    # Fecha de generación
    st.caption(f"*Análisis generado el {datetime.now().strftime('%d/%m/%Y')} | Datos sujetos a verificación*")

# Diccionarios de configuración por país
TIPOS_IMPOSITIVOS = {
    "España": 25.0,
    "Francia": 26.5,
    "Alemania": 30.0,
    "Reino Unido": 19.0,
    "Estados Unidos": 21.0,
    "Portugal": 21.0,
    "Italia": 24.0,
    "Países Bajos": 25.8,
    "Irlanda": 12.5,
    "Bélgica": 25.0
}

MONEDAS = {
    "EUR": "€",
    "USD": "$",
    "GBP": "£",
    "CHF": "CHF"
}

# Inicializar session state
if 'datos_guardados' not in st.session_state:
    st.session_state.datos_guardados = None
if 'proyeccion_generada' not in st.session_state:
    st.session_state.proyeccion_generada = False

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
# Logo centrado con mejor distribución
st.markdown("<div style='height: 50px;'></div>", unsafe_allow_html=True)  # Espaciado superior
col1, col2, col3 = st.columns([2, 3, 2])  # Cambiar proporciones
with col2:
    st.image("assets/ValUProIA.png", use_container_width=True)
    st.markdown("<h3 style='text-align: center; color: #666; margin-top: 10px;'>Valoración empresarial con metodología M&A e IA</h3>", unsafe_allow_html=True)
st.markdown("<div style='height: 30px;'></div>", unsafe_allow_html=True)  # Espaciado inferior
# Mostrar ejemplo
with st.expander("📚 Ver ejemplo de uso"):
    st.markdown("""
    ### Cómo usar Valoración empresarial con metodología M&A e IA:
    
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

# Header principal


# Sidebar para entrada de datos
with st.sidebar:
    st.header("📋 Datos de tu Empresa")
    # Modo Demo
    st.markdown("---")
    st.markdown("### 🎮 Modo Demo")
    empresa_demo = st.selectbox(
        "Cargar empresa de ejemplo:",
        ["Ninguna", "🍕 Restaurante La Terraza", "💻 TechStart SaaS", "🛍️ ModaOnline Shop", "🏭 MetalPro Industrial"]
    )
    
    # Sección de importación de Excel
    st.markdown("---")
    st.markdown("### 📥 Importar datos desde Excel")
    
    # Selector de sector para la plantilla
    sector_plantilla = st.selectbox(
        "Selecciona el sector para la plantilla:",
        ["General", "Hostelería", "Tecnología", "Ecommerce", "Industrial"],
        help="La plantilla incluirá valores típicos del sector"
    )

    col1, col2 = st.columns(2)
    with col1:
        if st.button("📄 Descargar Plantilla", type="secondary", use_container_width=True):
            excel_template = crear_plantilla_excel(sector_plantilla)
            st.download_button(
                label="💾 Guardar Plantilla",
                data=excel_template,
                file_name=f"Plantilla_BusinessPlan_{datetime.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    
    with col2:
        uploaded_file = st.file_uploader(
            "Cargar Excel",
            type=['xlsx', 'xls'],
            help="Sube el archivo Excel con los datos completados"
        )
    
    # Inicializar datos_excel
    datos_excel = None
    
    if uploaded_file is not None:
        datos_excel = leer_excel_datos(uploaded_file)
        if datos_excel:
            st.success("✅ Datos cargados correctamente")
            # Cargar líneas de financiación si existen
            if 'lineas_financiacion' in datos_excel and datos_excel['lineas_financiacion']:
                st.session_state.lineas_financiacion = datos_excel['lineas_financiacion']
                st.info(f"📊 Cargadas {len(datos_excel['lineas_financiacion'])} líneas de financiación")
            # AÑADIR AQUÍ LAS LÍNEAS DE DEBUG
            with st.expander("📊 Ver datos importados"):
                st.write("**Info General:**", datos_excel.get('info_general', {}))
                st.write("**PYL Histórico:**", datos_excel.get('pyl_historico', {}))
                st.write("**Datos Laborales:**", datos_excel.get('datos_laborales', {}))
            # Los datos se usarán para rellenar los campos automáticamente
    st.markdown("---")
    # MODO DEMO - Cargar datos de ejemplo
    if empresa_demo == "🍕 Restaurante La Terraza":
        datos_excel = {
            'info_general': {
                'nombre_empresa': 'Restaurante La Terraza SL',
                'sector': 'Hostelería',
                'pais': 'España',
                'año_fundacion': 2015,
                'empresa_familiar': 'Sí',
                'empresa_auditada': 'Sí',
                'moneda': 'EUR'
            },
            'pyl_historico': {
                'ventas': [850000, 920000, 1050000],
                'costos_variables_pct': 43,
                'gastos_personal': 210000,
                'gastos_generales': 48000,
                'gastos_marketing': 22000
            },
            'datos_laborales': {
                'num_empleados': 18,
                'coste_medio_empleado': 28000,
                'antiguedad_media': 6.5,
                'rotacion_anual': 12.0
            },
            'balance_activo': {
                'tesoreria_inicial': 480000,
                'inversiones_cp': 50000,
                'clientes_inicial': 180000,
                'inventario_inicial': 120000,
                'activo_fijo_bruto': 450000,
                'depreciacion_acumulada': 120000,
                'activos_intangibles': 80000,
                'amortizacion_intangibles': 25000,
                'otros_deudores': 15000,
                'admin_publica_deudora': 25000,
                'gastos_anticipados': 8000,
                'activos_impuesto_diferido_cp': 5000,
                'inversiones_lp': 0,
                'creditos_lp': 0,
                'fianzas_depositos': 15000,
                'activos_impuesto_diferido_lp': 0
            },
            'balance_pasivo': {
                'proveedores_inicial': 120000,
                'prestamo_principal': 200000,
                'acreedores_servicios': 25000,
                'anticipos_clientes': 10000,
                'remuneraciones_pendientes': 18000,
                'admin_publica_acreedora': 35000,
                'provisiones_cp': 5000,
                'hipoteca_importe_original': 300000,
                'hipoteca_meses_transcurridos': 60,
                'leasing_total': 80000,
                'otros_prestamos_lp': 0,
                'provisiones_riesgos': 10000,
                'leasing_cuota_mensual': 2000,
                'leasing_meses_restantes': 40,
                'otros_pasivos_cp': 0,
                'otras_provisiones_lp': 0,
                'pasivos_impuesto_diferido': 0
            },
            'balance_patrimonio': {
                'capital_social': 50000,
                'prima_emision': 0,
                'reserva_legal': 10000,
                'reservas': 85000,
                'resultados_acumulados': 125000,
                'resultado_ejercicio': 45000,
                'ajustes_valor': 0,
                'subvenciones': 15000
            },
            'proyecciones': {
                'capex_año1': 50000,
                'capex_año2': 75000,
                'capex_año3': 60000,
                'capex_año4': 40000,
                'capex_año5': 30000
            }
        }
        st.success("✅ Cargado: Restaurante La Terraza (Hostelería)")

    elif empresa_demo == "💻 TechStart SaaS":
        datos_excel = {
            'info_general': {
                'nombre_empresa': 'TechStart SaaS',
                'sector': 'Tecnología',
                'pais': 'España',
                'año_fundacion': 2018,
                'empresa_familiar': 'No',
                'empresa_auditada': 'Sí',
                'moneda': 'EUR'
            },
            'pyl_historico': {
                'ventas': [2500000, 3800000, 5200000],
                'costos_variables_pct': 25,
                'gastos_personal': 1800000,
                'gastos_generales': 320000,
                'gastos_marketing': 450000
            },
            'datos_laborales': {
                'num_empleados': 32,
                'coste_medio_empleado': 56000,
                'antiguedad_media': 2.5,
                'rotacion_anual': 18.0
            },
            'balance_activo': {
                'tesoreria_inicial': 1870000,
                'inversiones_cp': 300000,
                'clientes_inicial': 850000,
                'inventario_inicial': 0,
                'activo_fijo_bruto': 280000,
                'depreciacion_acumulada': 95000,
                'activos_intangibles': 450000,
                'amortizacion_intangibles': 90000,
                'otros_deudores': 45000,
                'admin_publica_deudora': 120000,
                'gastos_anticipados': 85000,
                'activos_impuesto_diferido_cp': 25000,
                'inversiones_lp': 0,
                'creditos_lp': 0,
                'fianzas_depositos': 35000,
                'activos_impuesto_diferido_lp': 0
            },
            'balance_pasivo': {
                'proveedores_inicial': 180000,
                'prestamo_principal': 500000,
                'acreedores_servicios': 95000,
                'anticipos_clientes': 320000,
                'remuneraciones_pendientes': 150000,
                'admin_publica_acreedora': 280000,
                'provisiones_cp': 0,
                'hipoteca_importe_original': 0,
                'hipoteca_meses_transcurridos': 0,
                'leasing_total': 120000,
                'otros_prestamos_lp': 0,
                'provisiones_riesgos': 50000,
                'leasing_cuota_mensual': 3500,
                'leasing_meses_restantes': 36,
                'otros_pasivos_cp': 0,
                'otras_provisiones_lp': 0,
                'pasivos_impuesto_diferido': 0
            },
            'balance_patrimonio': {
                'capital_social': 100000,
                'prima_emision': 900000,
                'reserva_legal': 20000,
                'reservas': 350000,
                'resultados_acumulados': 55000,
                'resultado_ejercicio': 420000,
                'ajustes_valor': 0,
                'subvenciones': 85000
            },
            'proyecciones': {
                'capex_año1': 150000,
                'capex_año2': 200000,
                'capex_año3': 250000,
                'capex_año4': 180000,
                'capex_año5': 150000
            }
        }
        st.success("✅ Cargado: TechStart SaaS (Tecnología)")

    elif empresa_demo == "🛍️ ModaOnline Shop":
        datos_excel = {
            'info_general': {
                'nombre_empresa': 'ModaOnline Shop SL',
                'sector': 'Ecommerce',
                'pais': 'España',
                'año_fundacion': 2019,
                'empresa_familiar': 'Sí',
                'empresa_auditada': 'No',
                'moneda': 'EUR'
            },
            'pyl_historico': {
                'ventas': [1800000, 2600000, 3500000],
                'costos_variables_pct': 65,
                'gastos_personal': 280000,
                'gastos_generales': 120000,
                'gastos_marketing': 350000
            },
            'datos_laborales': {
                'num_empleados': 12,
                'coste_medio_empleado': 32000,
                'antiguedad_media': 2.0,
                'rotacion_anual': 25.0
            },
            'balance_activo': {
                'tesoreria_inicial': 734000,
                'inversiones_cp': 0,
                'clientes_inicial': 180000,
                'inventario_inicial': 680000,
                'activo_fijo_bruto': 120000,
                'depreciacion_acumulada': 35000,
                'activos_intangibles': 95000,
                'amortizacion_intangibles': 20000,
                'otros_deudores': 25000,
                'admin_publica_deudora': 85000,
                'gastos_anticipados': 15000,
                'activos_impuesto_diferido_cp': 0,
                'inversiones_lp': 0,
                'creditos_lp': 0,
                'fianzas_depositos': 18000,
                'activos_impuesto_diferido_lp': 0
            },
            'balance_pasivo': {
                'proveedores_inicial': 420000,
                'prestamo_principal': 150000,
                'acreedores_servicios': 65000,
                'anticipos_clientes': 95000,
                'remuneraciones_pendientes': 35000,
                'admin_publica_acreedora': 125000,
                'provisiones_cp': 15000,
                'hipoteca_importe_original': 0,
                'hipoteca_meses_transcurridos': 0,
                'leasing_total': 0,
                'otros_prestamos_lp': 50000,
                'provisiones_riesgos': 0,
                'leasing_cuota_mensual': 0,
                'leasing_meses_restantes': 0,
                'otros_pasivos_cp': 25000,
                'otras_provisiones_lp': 0,
                'pasivos_impuesto_diferido': 0
            },
            'balance_patrimonio': {
                'capital_social': 50000,
                'prima_emision': 0,
                'reserva_legal': 10000,
                'reservas': 120000,
                'resultados_acumulados': 392000,
                'resultado_ejercicio': 95000,
                'ajustes_valor': 0,
                'subvenciones': 0
            },
            'proyecciones': {
                'capex_año1': 80000,
                'capex_año2': 120000,
                'capex_año3': 150000,
                'capex_año4': 100000,
                'capex_año5': 80000
            }
        }
        st.success("✅ Cargado: ModaOnline Shop (Ecommerce)")

    elif empresa_demo == "🏭 MetalPro Industrial":
        datos_excel = {
            'info_general': {
                'nombre_empresa': 'MetalPro Industrial SA',
                'sector': 'Industrial',
                'pais': 'España',
                'año_fundacion': 2008,
                'empresa_familiar': 'No',
                'empresa_auditada': 'Sí',
                'moneda': 'EUR'
            },
            'pyl_historico': {
                'ventas': [8500000, 9200000, 10500000],
                'costos_variables_pct': 62,
                'gastos_personal': 1850000,
                'gastos_generales': 480000,
                'gastos_marketing': 95000
            },
            'datos_laborales': {
                'num_empleados': 68,
                'coste_medio_empleado': 38000,
                'antiguedad_media': 8.5,
                'rotacion_anual': 8.0
            },
            'balance_activo': {
                'tesoreria_inicial': 4820000,
                'inversiones_cp': 150000,
                'clientes_inicial': 1850000,
                'inventario_inicial': 2200000,
                'activo_fijo_bruto': 5800000,
                'depreciacion_acumulada': 2100000,
                'activos_intangibles': 180000,
                'amortizacion_intangibles': 60000,
                'otros_deudores': 120000,
                'admin_publica_deudora': 180000,
                'gastos_anticipados': 45000,
                'activos_impuesto_diferido_cp': 0,
                'inversiones_lp': 250000,
                'creditos_lp': 0,
                'fianzas_depositos': 85000,
                'activos_impuesto_diferido_lp': 35000
            },
            'balance_pasivo': {
                'proveedores_inicial': 1650000,
                'prestamo_principal': 2200000,
                'acreedores_servicios': 280000,
                'anticipos_clientes': 450000,
                'remuneraciones_pendientes': 195000,
                'admin_publica_acreedora': 420000,
                'provisiones_cp': 85000,
                'hipoteca_importe_original': 3000000,
                'hipoteca_meses_transcurridos': 84,
                'leasing_total': 680000,
                'otros_prestamos_lp': 0,
                'provisiones_riesgos': 120000,
                'leasing_cuota_mensual': 15000,
                'leasing_meses_restantes': 48,
                'otros_pasivos_cp': 65000,
                'otras_provisiones_lp': 180000,
                'pasivos_impuesto_diferido': 95000
            },
            'balance_patrimonio': {
                'capital_social': 500000,
                'prima_emision': 0,
                'reserva_legal': 100000,
                'reservas': 850000,
                'resultados_acumulados': 3335000,
                'resultado_ejercicio': 380000,
                'ajustes_valor': 0,
                'subvenciones': 120000
            },
            'proyecciones': {
                'capex_año1': 450000,
                'capex_año2': 650000,
                'capex_año3': 800000,
                'capex_año4': 550000,
                'capex_año5': 400000
            }
        }
        st.success("✅ Cargado: MetalPro Industrial (Industrial)")

    # Preparar valores por defecto desde Excel o valores estándar
    if 'datos_excel' in locals() and datos_excel:
        # Valores desde Excel
        default_nombre = datos_excel['info_general']['nombre_empresa']
        default_sector = datos_excel['info_general']['sector']
        default_pais = datos_excel['info_general']['pais']
        default_año = datos_excel['info_general']['año_fundacion']
        default_familiar = datos_excel['info_general']['empresa_familiar']
        default_auditada = datos_excel['info_general']['empresa_auditada']
        default_moneda = datos_excel['info_general']['moneda']
        
        # Datos PYL
        default_ventas = datos_excel['pyl_historico']['ventas']
        default_costos_var = datos_excel['pyl_historico']['costos_variables_pct']
        default_gastos_personal = datos_excel['pyl_historico']['gastos_personal']
        default_gastos_generales = datos_excel['pyl_historico']['gastos_generales']
        default_gastos_marketing = datos_excel['pyl_historico']['gastos_marketing']
        
        # Datos laborales
        default_empleados = datos_excel['datos_laborales']['num_empleados']
        default_coste_empleado = datos_excel['datos_laborales']['coste_medio_empleado']
        default_antiguedad = datos_excel['datos_laborales']['antiguedad_media']
        default_rotacion = datos_excel['datos_laborales']['rotacion_anual']
        # Valores del balance - pasivo
        default_proveedores = int(datos_excel['balance_pasivo']['proveedores_inicial'])
        default_prestamo_principal = int(datos_excel['balance_pasivo']['prestamo_principal'])
        # Más valores del pasivo
        default_acreedores = int(datos_excel['balance_pasivo'].get('acreedores_servicios', 0))
        default_anticipos = int(datos_excel['balance_pasivo'].get('anticipos_clientes', 0))
        default_remuneraciones = int(datos_excel['balance_pasivo'].get('remuneraciones_pendientes', 0))
        default_admin_acreedora = int(datos_excel['balance_pasivo'].get('admin_publica_acreedora', 0))
        default_provisiones_cp = int(datos_excel['balance_pasivo'].get('provisiones_cp', 0))
        default_hipoteca_original = int(datos_excel['balance_pasivo'].get('hipoteca_importe_original', 0))
        default_hipoteca_meses = int(datos_excel['balance_pasivo'].get('hipoteca_meses_transcurridos', 0))
        default_leasing = int(datos_excel['balance_pasivo'].get('leasing_total', 0))
        default_otros_prestamos = int(datos_excel['balance_pasivo'].get('otros_prestamos_lp', 0))
        default_provisiones_riesgos = int(datos_excel['balance_pasivo'].get('provisiones_riesgos', 0))
        default_leasing_cuota = int(datos_excel['balance_pasivo'].get('leasing_cuota_mensual', 0))
        default_leasing_meses = int(datos_excel['balance_pasivo'].get('leasing_meses_restantes', 0))
        default_otros_pasivos_cp = int(datos_excel['balance_pasivo'].get('otros_pasivos_cp', 0))
        default_otras_provisiones_lp = int(datos_excel['balance_pasivo'].get('otras_provisiones_lp', 0))
        default_pasivos_impuesto_dif = int(datos_excel['balance_pasivo'].get('pasivos_impuesto_diferido', 0))
        # Valores del patrimonio neto
        default_capital_social = int(datos_excel['balance_patrimonio'].get('capital_social', 100000))
        default_prima_emision = int(datos_excel['balance_patrimonio'].get('prima_emision', 0))
        default_reserva_legal = int(datos_excel['balance_patrimonio'].get('reserva_legal', 20000))
        default_otras_reservas = int(datos_excel['balance_patrimonio'].get('reservas', 0))
        default_resultados_acum = int(datos_excel['balance_patrimonio'].get('resultados_acumulados', 0))
        default_resultado_ejercicio = int(datos_excel['balance_patrimonio'].get('resultado_ejercicio', 0))
        default_ajustes_valor = int(datos_excel['balance_patrimonio'].get('ajustes_valor', 0))
        default_subvenciones = int(datos_excel['balance_patrimonio'].get('subvenciones', 0))
        # Valores de proyecciones (CAPEX)
        default_capex_año1 = datos_excel['proyecciones']['capex_año1']
        default_capex_año2 = datos_excel['proyecciones']['capex_año2']
        default_capex_año3 = datos_excel['proyecciones']['capex_año3']
        default_capex_año4 = datos_excel['proyecciones']['capex_año4']
        default_capex_año5 = datos_excel['proyecciones']['capex_año5']
        # Valores del balance - activo
        default_tesoreria = int(datos_excel['balance_activo']['tesoreria_inicial'])
        default_clientes = int(datos_excel['balance_activo']['clientes_inicial'])
        default_inventario = int(datos_excel['balance_activo']['inventario_inicial'])
        # Más valores del activo
        default_inversiones_cp = int(datos_excel['balance_activo']['inversiones_cp'])
        default_otros_deudores = int(datos_excel['balance_activo']['otros_deudores'])
        default_admin_publica_deudora = int(datos_excel['balance_activo']['admin_publica_deudora'])
        default_gastos_anticipados = int(datos_excel['balance_activo']['gastos_anticipados'])
        default_activos_impuesto_cp = int(datos_excel['balance_activo']['activos_impuesto_diferido_cp'])
        default_activo_fijo = int(datos_excel['balance_activo']['activo_fijo_bruto'])
        default_depreciacion = int(datos_excel['balance_activo']['depreciacion_acumulada'])
        default_intangibles = int(datos_excel['balance_activo']['activos_intangibles'])
        default_amort_intangibles = int(datos_excel['balance_activo']['amortizacion_intangibles'])
        default_fianzas = int(datos_excel['balance_activo']['fianzas_depositos'])
        default_inversiones_lp = int(datos_excel['balance_activo']['inversiones_lp'])
        default_creditos_lp = int(datos_excel['balance_activo']['creditos_lp'])
        default_activos_impuesto_lp = int(datos_excel['balance_activo']['activos_impuesto_diferido_lp'])
        # Valores de proyecciones
        default_capex_año1 = datos_excel['proyecciones']['capex_año1']
        print(f"\n=== VALORES PASIVO DEL EXCEL ===")
        print(f"Proveedores: €{default_proveedores:,.0f}")
        print(f"Préstamo principal: €{default_prestamo_principal:,.0f}")
        print(f"Datos completos pasivo: {datos_excel.get('balance_pasivo', {})}")
        print("=================================\n")
    else:
        # Valores por defecto estándar
        default_nombre = "Mi Empresa SL"
        default_sector = "Hostelería"
        default_pais = "España"
        default_año = datetime.now().year - 10
        default_familiar = "No"
        default_auditada = "Sí"
        default_moneda = "EUR"
        
        # Valores PYL por defecto
        default_ventas = [13500000, 14200000, 15000000]
        default_costos_var = 40
        default_gastos_personal = 120000
        default_gastos_generales = 36000
        default_gastos_marketing = 12000
        
        # Valores laborales por defecto
        default_empleados = 10
        default_coste_empleado = 35000
        default_antiguedad = 5.0
        default_rotacion = 10.0
    
    # Información básica
    st.subheader("Información General")
    nombre_empresa = st.text_input("Nombre de la empresa", value=default_nombre)
    
    año_fundacion = st.number_input(
        "Año de Fundación",
        min_value=1900,
        max_value=datetime.now().year,
        value=default_año if 'default_año' in locals() else datetime.now().year - 10,
        step=1,
        help="Año en que se constituyó la empresa",
        key="año_fundacion_sidebar",
    )

    # Características de la empresa
    col1, col2 = st.columns(2)
    with col1:
        empresa_familiar = st.selectbox(
        "¿Empresa familiar?",
        ["No", "Sí"],
        index=1 if default_familiar == "Sí" else 0,
        help="Las empresas familiares pueden tener valoraciones diferentes"
    )
    with col2:
        empresa_auditada = st.selectbox(
            "¿Cuentas auditadas?",
            ["Sí", "No"],
            help="Las cuentas auditadas dan más confianza a inversores"
        )
    
    sectores_lista = ["Hostelería", "Tecnología", "Ecommerce", "Consultoría",
                      "Retail", "Servicios", "Automoción", "Industrial", "Otro"]
    sector = st.selectbox(
        "Sector",
        sectores_lista,
        index=sectores_lista.index(default_sector) if default_sector in sectores_lista else 0
    )

    # País y configuración fiscal
    col1, col2 = st.columns(2)
    with col1:
        paises_lista = list(TIPOS_IMPOSITIVOS.keys())
        pais = st.selectbox(
            "País",
            paises_lista,
            index=paises_lista.index(default_pais) if default_pais in paises_lista else 0,
            help="País donde opera la empresa"
        )
    with col2:
        tipo_impositivo = TIPOS_IMPOSITIVOS[pais]
        st.metric("Tipo impositivo", f"{tipo_impositivo}%")
    
    # Moneda
    moneda = st.selectbox(
        "Moneda",
        list(MONEDAS.keys()),
        index=0,  # EUR por defecto
        help="Moneda para los cálculos"
    )
    simbolo_moneda = MONEDAS[moneda]
    # Guardar en session_state para uso global
    st.session_state['simbolo_moneda'] = simbolo_moneda

    # Datos históricos
    st.subheader("💰 Datos de Ventas")

    # Pregunta simple y directa
    periodo_datos = st.radio(
        "¿Para qué período vas a introducir datos?",
        options=[
            "Últimos 3 años completos",
            "Año actual + 2 anteriores", 
            "Personalizar años"
        ],
        index=0,  # Por defecto: últimos 3 años completos
        horizontal=True
    )

    # Calcular años automáticamente según la selección
    año_actual = datetime.now().year

    if periodo_datos == "Últimos 3 años completos":
        # Si estamos en 2025, muestra 2022, 2023, 2024
        año_3 = año_actual - 3
        año_2 = año_actual - 2
        año_1 = año_actual - 1
        primer_año_proyeccion = año_actual
        
    elif periodo_datos == "Año actual + 2 anteriores":
        # Si estamos en 2025, muestra 2023, 2024, 2025
        año_3 = año_actual - 2
        año_2 = año_actual - 1
        año_1 = año_actual
        primer_año_proyeccion = año_actual + 1
        
    else:  # Personalizar
        # Solo si elige personalizar, mostrar selector
        año_final = st.selectbox(
            "Selecciona el último año con datos:",
            options=list(range(año_actual - 5, año_actual + 1)),
            index=5  # Por defecto el año actual
        )
        año_3 = año_final - 2
        año_2 = año_final - 1
        año_1 = año_final
        primer_año_proyeccion = año_final + 1

    # Mostrar claramente qué se está introduciendo
    st.info(f"📊 **Introduciendo datos reales**: {año_3}, {año_2}, {año_1}")
    st.success(f"📈 **Se proyectará**: {primer_año_proyeccion} → {primer_año_proyeccion + 4}")

    # Los campos de entrada con años claros
    col1, col2, col3 = st.columns(3)

    with col1:
        ventas_año_3 = formato_numero(
            f"Ventas {año_3}",
            value=default_ventas[0] if 'default_ventas' in locals() else 13500000,
            key="ventas_3",
            help_text="Ventas reales"
        )

    with col2:
        ventas_año_2 = formato_numero(
            f"Ventas {año_2}",
            value=default_ventas[1] if 'default_ventas' in locals() else 14200000,
            key="ventas_2",
            help_text="Ventas reales"
        )

    with col3:
        ventas_año_1 = formato_numero(
            f"Ventas {año_1}",
            value=default_ventas[2] if 'default_ventas' in locals() else 15000000,
            key="ventas_1",
            help_text="Ventas reales"
        )

    # Guardar el año base para usar después
    st.session_state['primer_año_proyeccion'] = primer_año_proyeccion

    # Estructura de costos
    st.subheader("Estructura de Costos")

    costos_variables_pct = st.slider(
        "Costos Variables (% de ventas)",
        min_value=10,
        max_value=98,
        value=default_costos_var if 'default_costos_var' in locals() else 40,
        help="Incluye: materias primas, mercancías, comisiones de venta",
        key="costos_variables_slider"
    ) / 100

    gastos_personal = st.number_input(
        f"Gastos de Personal Anuales ({get_simbolo_moneda()})",
        min_value=0,
        value=default_gastos_personal if 'default_gastos_personal' in locals() else 120000,
        step=5000,
        help="Incluye: salarios, seguridad social, beneficios",
        key="gastos_personal_key"
    )    

    gastos_generales = st.number_input(
        f"Gastos Generales Anuales ({get_simbolo_moneda()})",
        min_value=0,
        value=default_gastos_generales if 'default_gastos_generales' in locals() else 36000,
        step=1000,
        help="Incluye: alquiler, suministros, seguros",
        key="gastos_generales_key"
    )

    gastos_marketing = st.number_input(
        f"Gastos de Marketing Anuales ({get_simbolo_moneda()})",
        min_value=0,
        value=default_gastos_marketing if 'default_gastos_marketing' in locals() else 12000,
        step=1000,
        help="Incluye: publicidad, web, redes sociales",
        key="gastos_marketing_key"
    )

    # Cálculo de EBITDA en tiempo real
    st.markdown("---")
    st.subheader("📊 EBITDA Calculado")
    
    # Calcular valores
    coste_ventas = ventas_año_1 * costos_variables_pct
    total_gastos = gastos_personal + gastos_generales + gastos_marketing
    ebitda_calculado = ventas_año_1 - coste_ventas - total_gastos
    margen_ebitda_calc = (ebitda_calculado / ventas_año_1 * 100) if ventas_año_1 > 0 else 0
    
    # Mostrar desglose
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown(f"""
        **Desglose del cálculo:**
        - Ventas: **{simbolo_moneda}{ventas_año_1:,.0f}**
        - Costos variables ({costos_variables_pct*100:.0f}%): **-{simbolo_moneda}{coste_ventas:,.0f}**
        - Gastos de personal: **-{simbolo_moneda}{gastos_personal:,.0f}**
        - Gastos generales: **-{simbolo_moneda}{gastos_generales:,.0f}**
        - Gastos de marketing: **-{simbolo_moneda}{gastos_marketing:,.0f}**
        """)
    with col2:
        st.metric("EBITDA", f"{simbolo_moneda}{ebitda_calculado:,.0f}")
        st.metric("Margen EBITDA", f"{margen_ebitda_calc:.1f}%")
    
    # Indicador de salud
    if margen_ebitda_calc < 5:
        st.error("⚠️ Margen EBITDA muy bajo - Revisar estructura de costos")
    elif margen_ebitda_calc < 10:
        st.warning("📊 Margen EBITDA mejorable")
    else:
        st.success("✅ Margen EBITDA saludable")
    
    st.markdown("---")

    # Datos Laborales
    st.subheader("Datos Laborales")
    
    col1, col2 = st.columns(2)
    
    with col1:
        num_empleados = st.number_input(
            "Número de empleados",
            min_value=1,
            value=default_empleados if 'default_empleados' in locals() else 10,
            step=1,
            help="Total de empleados en plantilla",
            key="num_empleados_sidebar",
        )
        
        coste_medio_empleado = st.number_input(
            f"Coste medio por empleado ({get_simbolo_moneda()}/año)",
            min_value=0,
            value=35000,
            step=1000,
            help="Incluye salario bruto + SS empresa + beneficios"
        )
    
    with col2:
        antiguedad_media = st.number_input(
            "Antigüedad media plantilla (años)",
            min_value=0.0,
            max_value=40.0,
            value=5.0,
            step=0.5,
            help="Años promedio de antigüedad de los empleados"
        )
        
        rotacion_anual = st.number_input(
            "Rotación anual esperada (%)",
            min_value=0.0,
            max_value=100.0,
            value=10.0,
            step=1.0,
            help="% de empleados que dejan la empresa al año"
        )
    
    # NUEVO: Campos para reestructuración
    st.markdown("---")
    st.markdown("#### 🔄 Reestructuración de Plantilla")
    
    # [Aquí va todo el código de reestructuración que ya tienes]

    # NUEVO: Campos para reestructuración
    st.markdown("---")
    st.markdown("#### 🔄 Reestructuración de Plantilla")
        
    reestructuracion_prevista = st.checkbox(
        "¿Se prevé una reestructuración a corto plazo?",
        value=False,
        help="Marcar si se planea reducir plantilla en los próximos 12-24 meses"
    )
        
    if reestructuracion_prevista:
        # Sin columnas porque estamos en el sidebar
        porcentaje_afectados = st.number_input(
            "% de plantilla afectada",
            min_value=0.0,
            max_value=100.0,
            value=10.0,
            step=1.0,
            help="Porcentaje de empleados que serán despedidos"
        )
            
        empleados_afectados = int(num_empleados * porcentaje_afectados / 100)
        st.caption(f"👥 Empleados afectados: {empleados_afectados}")
        
        tipo_indemnizacion = st.selectbox(
            "Días de indemnización por año",
            options=["20 días", "33 días", "45 días", "Otro"],
            help="Según normativa o acuerdo colectivo"
        )
            
        if tipo_indemnizacion == "Otro":
            dias_indemnizacion = st.number_input(
                "Especificar días por año",
                min_value=0,
                max_value=90,
                value=30,
                step=1
            )
        else:
            dias_indemnizacion = int(tipo_indemnizacion.split()[0])
        
            # Cálculo de la provisión por reestructuración
            salario_anual_medio = coste_medio_empleado / 1.35  # Salario bruto aproximado
            
            # Calcular indemnización con tope de 12 mensualidades
            dias_totales = dias_indemnizacion * antiguedad_media
            años_salario = dias_totales / 365
            años_salario_con_tope = min(años_salario, 1.0)  # Tope de 12 meses = 1 año
            
            indemnizacion_por_persona = salario_anual_medio * años_salario_con_tope
            provision_reestructuracion = empleados_afectados * indemnizacion_por_persona
            
            # Añadir costes adicionales (10% para asesores, outplacement, etc.)
            provision_total_reestructuracion = provision_reestructuracion * 1.1
            
            st.warning(f"""
            ⚠️ **Provisión por Reestructuración**:
            - Empleados afectados: {empleados_afectados}
            - Indemnización por persona: {get_simbolo_moneda()}{indemnizacion_por_persona:,.0f}
            - Provisión base: {get_simbolo_moneda()}{provision_reestructuracion:,.0f}
            - **Provisión total recomendada**: {get_simbolo_moneda()}{provision_total_reestructuracion:,.0f}
            
            *Incluye 10% adicional para costes asociados (asesores, outplacement, litigios)*
            """)
            
            # Guardar en session_state para usar en el balance
            st.session_state['provision_reestructuracion'] = provision_total_reestructuracion
    else:
        provision_total_reestructuracion = 0
        st.session_state['provision_reestructuracion'] = 0

    # Valores por defecto para mantener compatibilidad
    provisiones_laborales = 0  # Ya no se usa, se maneja con reestructuración
    meses_indemnizacion = 0  # Ya no se usa, se define en reestructuración
    
    # Asegurar que provision_total_reestructuracion siempre exista
    if 'provision_total_reestructuracion' not in locals():
        provision_total_reestructuracion = 0
        
    pasivo_laboral_total = provision_total_reestructuracion  # Solo la provisión de reestructuración

    # Solo mostrar info si hay provisión por reestructuración
    if 'provision_total_reestructuracion' in locals() and provision_total_reestructuracion > 0:
        st.info(f"""
        📊 **Provisión por Reestructuración**: {get_simbolo_moneda()}{provision_total_reestructuracion:,.0f}
        
        *Esta provisión se cargará automáticamente en el Pasivo Corriente del Balance*
        """)

    # EQUITY BRIDGE PROFESIONAL
    st.markdown("---")
    st.markdown("#### 💰 Análisis Profesional M&A")
    
    mostrar_equity_bridge = st.checkbox(
        "Mostrar Equity Bridge",
        value=False,
        help="Análisis profesional para valoración M&A - Del Enterprise Value al Equity Value"
    )
    
    if mostrar_equity_bridge:
        st.info("""
        📊 **¿Qué es el Equity Bridge?**
        
        Es el 'puente' que muestra cómo se pasa del valor de la empresa (EV) 
        al valor para los accionistas (Equity), descontando deudas y provisiones.
        
        Se mostrará en la pestaña de Valoración.
        """)
        
        # Guardar preferencia
        st.session_state['mostrar_equity_bridge'] = True
    else:
        st.session_state['mostrar_equity_bridge'] = False
    
    # Otras provisiones
    st.markdown("##### 📋 Provisiones adicionales")
    
    tiene_litigios = st.checkbox("¿Litigios pendientes?", value=False)
    if tiene_litigios:
        provision_litigios = st.number_input(
            
            f"Estimación provisión litigios ({get_simbolo_moneda()})",
            min_value=0,
            value=0,
            step=10000,
            help="Estimación de costes por litigios en curso"
        )
        st.session_state['provision_litigios'] = provision_litigios
    else:
        st.session_state['provision_litigios'] = 0
    
    tiene_contingencias = st.checkbox("¿Contingencias fiscales?", value=False)
    if tiene_contingencias:
        provision_fiscal = st.number_input(
            f"Provisión contingencias fiscales ({get_simbolo_moneda()})",
            min_value=0,
            value=0,
            step=10000,
            help="Posibles ajustes de inspecciones fiscales"
        )
        st.session_state['provision_fiscal'] = provision_fiscal
    else:
        st.session_state['provision_fiscal'] = 0

    # Parámetros financieros
    st.subheader("Parámetros Financieros")
    
    # Crear tabs para organizar mejor la información
    # Botón de generación
    st.markdown("---")
    generar_proyeccion = st.button("📈 Generar Proyección Financiera", type="primary", use_container_width=True)
    tab_activos, tab_pasivos, tab_patrimonio, tab_proyecciones, tab_parametros = st.tabs(["📊 ACTIVOS", "💳 PASIVOS", "🏛️ PATRIMONIO NETO", "📈 PROYECCIONES", "⚙️ PARÁMETROS"])
    with tab_activos:
        st.markdown("### 📊 BALANCE - ACTIVO")
        
        # ACTIVO CORRIENTE
        with st.expander("💰 ACTIVO CORRIENTE", expanded=True):
            
            # Tesorería y Equivalentes
            st.markdown("#### Tesorería y Equivalentes")
            col1, col2 = st.columns(2)
            with col1:
                tesoreria_inicial = st.number_input(
                    f"Caja y bancos ({get_simbolo_moneda()})",
                    min_value=0,
                    value=default_tesoreria if 'default_tesoreria' in locals() else 0,
                    step=50000,
                    help="Efectivo + cuentas bancarias a la vista"
                )
                inversiones_cp = st.number_input(
                    f"Inversiones financieras temporales ({get_simbolo_moneda()})",
                    min_value=0,
                    value=default_inversiones_cp if 'default_inversiones_cp' in locals() else 0,
                    step=10000,
                    help="Depósitos, fondos mercado monetario < 1 año"
                )
            with col2:
                total_tesoreria = tesoreria_inicial + inversiones_cp
                st.metric("Total Tesorería", f"{get_simbolo_moneda()}{total_tesoreria:,.0f}")
                
            # Cuentas por Cobrar
            st.markdown("#### Cuentas por Cobrar")
            col1, col2 = st.columns(2)
            with col1:
                clientes_inicial = st.number_input(
                    f"Clientes comerciales ({get_simbolo_moneda()})",
                    min_value=0,
                    value=default_clientes if 'default_clientes' in locals() else 0,
                    step=100000,
                    help="Facturas pendientes de cobro"
                )
                otros_deudores = st.number_input(
                    f"Otros deudores ({get_simbolo_moneda()})",
                    min_value=0,
                    value=default_otros_deudores if 'default_otros_deudores' in locals() else 0,
                    step=10000,
                    help="Deudores no comerciales, anticipos, etc."
                )
            with col2:
                admin_publica_deudora = st.number_input(
                    f"Administraciones públicas deudoras ({get_simbolo_moneda()})",
                    min_value=0,
                    value=default_admin_publica_deudora if 'default_admin_publica_deudora' in locals() else 0,
                    step=10000,
                    help="IVA a compensar, devoluciones pendientes, etc."
                )
                total_cuentas_cobrar = clientes_inicial + otros_deudores + admin_publica_deudora
                st.metric("Total Cuentas por Cobrar", f"{get_simbolo_moneda()}{total_cuentas_cobrar:,.0f}")
                
            # Existencias
            st.markdown("#### Existencias")
            col1, col2 = st.columns(2)
            with col1:
                inventario_inicial = st.number_input(
                    f"Inventarios ({get_simbolo_moneda()})",
                    min_value=0,
                    value=default_inventario if 'default_inventario' in locals() else 0,
                    step=100000,
                    help="Materias primas + productos en curso + terminados"
                )
            with col2:
                st.info(f"📦 Rotación: {dias_stock if 'dias_stock' in locals() else 30} días")
                
            # Otros Activos Corrientes
            st.markdown("#### Otros Activos Corrientes")
            col1, col2 = st.columns(2)
            with col1:
                gastos_anticipados = st.number_input(
                    f"Gastos anticipados ({get_simbolo_moneda()})",
                    min_value=0,
                    value=default_gastos_anticipados if 'default_gastos_anticipados' in locals() else 0,
                    step=10000,
                    help="Seguros, alquileres pagados por anticipado"
                )
            with col2:
                activos_impuesto_diferido_cp = st.number_input(
                    f"Activos por impuesto diferido CP ({get_simbolo_moneda()})",
                    min_value=0,
                    value=default_activos_impuesto_cp if 'default_activos_impuesto_cp' in locals() else 0,
                    step=10000,
                    help="Créditos fiscales a compensar < 1 año"
                )
                otros_activos_corrientes = 0  # Eliminamos este campo genérico
                
            # Total Activo Corriente
            total_activo_corriente = (total_tesoreria + total_cuentas_cobrar + 
                                     inventario_inicial + gastos_anticipados + 
                                     activos_impuesto_diferido_cp)
            st.success(f"**TOTAL ACTIVO CORRIENTE: {get_simbolo_moneda()}{total_activo_corriente:,.0f}**")
        
        # ACTIVO NO CORRIENTE
        with st.expander("🏭 ACTIVO NO CORRIENTE", expanded=True):
            
            # Inmovilizado Material
            st.markdown("#### Inmovilizado Material")
            col1, col2 = st.columns(2)
            with col1:
                activo_fijo_bruto = st.number_input(
                    f"Inmovilizado material bruto ({get_simbolo_moneda()})",
                    min_value=0,
                    value=default_activo_fijo if 'default_activo_fijo' in locals() else 0,
                    step=100000,
                    help="Coste histórico: terrenos, edificios, maquinaria"
                )
                depreciacion_acumulada = st.number_input(
                    f"Amortización acumulada material ({get_simbolo_moneda()})",
                    min_value=0,
                    max_value=activo_fijo_bruto,
                    value=default_depreciacion if 'default_depreciacion' in locals() else 0,
                    step=100000,
                    help="Depreciación acumulada del inmovilizado material"
                )
            with col2:
                activo_fijo_neto = activo_fijo_bruto - depreciacion_acumulada
                st.metric("Inmovilizado Material Neto", f"{get_simbolo_moneda()}{activo_fijo_neto:,.0f}")
                if activo_fijo_bruto > 0:
                    st.info(f"📊 Depreciación: {(depreciacion_acumulada/activo_fijo_bruto*100):.1f}%")
                    
            # Inmovilizado Inmaterial
            st.markdown("#### Inmovilizado Inmaterial")
            col1, col2 = st.columns(2)
            with col1:
                activos_intangibles = st.number_input(
                    f"Activos intangibles brutos ({get_simbolo_moneda()})",
                    min_value=0,
                    value=default_intangibles if 'default_intangibles' in locals() else 0,
                    step=50000,
                    help="Software, patentes, marcas, fondo de comercio"
                )
                amortizacion_intangibles = st.number_input(
                    f"Amortización acumulada intangibles ({get_simbolo_moneda()})",
                    min_value=0,
                    max_value=activos_intangibles,
                    value=default_amort_intangibles if 'default_amort_intangibles' in locals() else 0,
                    step=10000,
                    help="Amortización acumulada de intangibles"
                )
            with col2:
                intangibles_netos = activos_intangibles - amortizacion_intangibles
                st.metric("Intangibles Netos", f"{get_simbolo_moneda()}{intangibles_netos:,.0f}")

                
            # Inversiones Financieras LP
            st.markdown("#### Inversiones Financieras a Largo Plazo")
            col1, col2 = st.columns(2)
            with col1:
                inversiones_lp = st.number_input(
                    f"Participaciones en empresas ({get_simbolo_moneda()})",
                    min_value=0,
                    value=default_inversiones_lp if 'default_inversiones_lp' in locals() else 0,
                    step=50000,
                    help="Inversiones en otras empresas"
                )
                creditos_lp = st.number_input(
                    f"Créditos a largo plazo ({get_simbolo_moneda()})",
                    min_value=0,
                    value=default_creditos_lp if 'default_creditos_lp' in locals() else 0,
                    step=10000,
                    help="Préstamos concedidos a terceros > 1 año"
                )
            with col2:
                fianzas_depositos = st.number_input(
                    f"Fianzas y depósitos ({get_simbolo_moneda()})",
                    min_value=0,
                    value=default_fianzas if 'default_fianzas' in locals() else 0,
                    step=10000,
                    help="Fianzas de alquileres, suministros, etc."
                )
                total_inversiones_lp = inversiones_lp + creditos_lp + fianzas_depositos
                st.metric("Total Inversiones LP", f"{get_simbolo_moneda()}{total_inversiones_lp:,.0f}")

                
            # Activos por Impuesto Diferido LP
            st.markdown("#### Otros Activos No Corrientes")
            activos_impuesto_diferido_lp = st.number_input(
                f"Activos por impuesto diferido LP ({get_simbolo_moneda()})",
                min_value=0,
                value=default_activos_impuesto_lp if 'default_activos_impuesto_lp' in locals() else 0,
                step=10000,
                help="Créditos fiscales a compensar > 1 año"
            )
            otros_activos_nc = 0  # Eliminamos este campo genérico
            
            # Total Activo No Corriente
            total_activo_no_corriente = (activo_fijo_neto + intangibles_netos + 
                                        total_inversiones_lp + activos_impuesto_diferido_lp)
            st.success(f"**TOTAL ACTIVO NO CORRIENTE: {get_simbolo_moneda()}{total_activo_no_corriente:,.0f}**")
        
        # TOTAL ACTIVOS
        total_activos = total_activo_corriente + total_activo_no_corriente
        st.markdown("---")
        st.markdown(f"### 💼 **TOTAL ACTIVOS: {get_simbolo_moneda()}{total_activos:,.0f}**")


        # Guardar en session_state para otros tabs
        st.session_state['total_activo_corriente'] = total_activo_corriente
        st.session_state['total_activo_no_corriente'] = total_activo_no_corriente
        st.session_state['total_activos'] = total_activos

    with tab_pasivos:
        st.markdown("### 💳 BALANCE - PASIVO")
        
        # PASIVO CORRIENTE
        with st.expander("📌 PASIVO CORRIENTE", expanded=True):
            
            # Deuda Financiera CP
            st.markdown("#### 💳 Líneas de Financiación Circulante")

            # Sistema dinámico de líneas de financiación
            if 'lineas_financiacion' not in st.session_state:
                st.session_state.lineas_financiacion = [{
                    'tipo': 'Póliza crédito',
                    'banco': 'Banco principal',
                    'limite': 500000,
                    'dispuesto': 250000,
                    'tipo_interes': 4.5
                }]

            # Botones para gestionar líneas
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                st.info(f"📊 Tienes {len(st.session_state.lineas_financiacion)} líneas de financiación configuradas")
            with col2:
                if st.button("➕ Añadir línea", key="add_linea"):
                    st.session_state.lineas_financiacion.append({
                        'tipo': 'Póliza crédito',
                        'banco': f'Banco {len(st.session_state.lineas_financiacion) + 1}',
                        'limite': 0,
                        'dispuesto': 0,
                        'tipo_interes': 4.5
                    })
                    st.rerun()
            with col3:
                if len(st.session_state.lineas_financiacion) > 1:
                    if st.button("➖ Eliminar última", key="del_linea"):
                        st.session_state.lineas_financiacion.pop()
                        st.rerun()

            # Crear las líneas de financiación
            total_limite = 0
            total_dispuesto = 0
            polizas_credito = []  # Para mantener compatibilidad con modelo_financiero

            for idx, linea in enumerate(st.session_state.lineas_financiacion):
                # Usar container en lugar de expander
                st.markdown(f"##### 📄 Línea {idx + 1}: {linea['tipo']} - {linea['banco']}")
                with st.container():
                    st.markdown("---")
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # Tipo de financiación
                        tipo = st.selectbox(
                            "Tipo de financiación",
                            [
                                "Póliza crédito",
                                "Póliza crédito stock", 
                                "Descuento comercial",
                                "Anticipo facturas",
                                "Factoring con recurso",
                                "Factoring sin recurso",
                                "Confirming proveedores",
                                "Pagarés empresa",
                                "Crédito importación"
                            ],
                            index=["Póliza crédito", "Póliza crédito stock", "Descuento comercial", 
                                "Anticipo facturas", "Factoring con recurso", "Factoring sin recurso",
                                "Confirming proveedores", "Pagarés empresa", "Crédito importación"].index(linea['tipo']),
                            key=f"tipo_{idx}",
                            help="Cada tipo tiene condiciones y costes diferentes"
                        )
                        st.session_state.lineas_financiacion[idx]['tipo'] = tipo
                        
                        # Entidad financiera
                        banco = st.text_input(
                            "Entidad financiera",
                            value=linea['banco'],
                            key=f"banco_{idx}",
                            placeholder="Nombre del banco o entidad"
                        )
                        st.session_state.lineas_financiacion[idx]['banco'] = banco
                        
                    with col2:
                        # Límite
                        limite = st.number_input(
                            f"Límite concedido ({get_simbolo_moneda()})",
                            min_value=0,
                            value=int(linea['limite']),
                            step=50000,
                            key=f"limite_{idx}",
                            help="Importe máximo disponible"
                        )
                        st.session_state.lineas_financiacion[idx]['limite'] = limite
                        total_limite += limite
                        
                        # Dispuesto
                        dispuesto = st.number_input(
                            f"Importe dispuesto ({get_simbolo_moneda()})",
                            min_value=0,
                            max_value=limite,
                            value=int(min(linea['dispuesto'], limite)),
                            step=10000,
                            key=f"dispuesto_{idx}",
                            help="Importe actualmente utilizado"
                        )
                        st.session_state.lineas_financiacion[idx]['dispuesto'] = dispuesto
                        total_dispuesto += dispuesto
                    
                    # Condiciones financieras
                    col3, col4, col5 = st.columns(3)
                    
                    with col3:
                        tipo_interes = st.number_input(
                            "Tipo interés (%)",
                            min_value=0.0,
                            max_value=15.0,
                            value=linea.get('tipo_interes', 4.5),
                            step=0.1,
                            key=f"tipo_interes_{idx}",
                            help="Tipo de interés anual"
                        )
                        st.session_state.lineas_financiacion[idx]['tipo_interes'] = tipo_interes
                        
                    with col4:
                        # Comisiones según tipo
                        if tipo in ["Póliza crédito", "Póliza crédito stock"]:
                            comision = st.number_input(
                                "Comisión apertura (%)",
                                min_value=0.0,
                                max_value=3.0,
                                value=0.5,
                                step=0.1,
                                key=f"comision_{idx}"
                            )
                        elif tipo == "Factoring con recurso" or tipo == "Factoring sin recurso":
                            comision = st.number_input(
                                "Comisión factoring (%)",
                                min_value=0.0,
                                max_value=5.0,
                                value=1.5,
                                step=0.1,
                                key=f"comision_{idx}"
                            )
                        else:
                            comision = 0.25
                        st.session_state.lineas_financiacion[idx]['comision'] = comision
                        
                    with col5:
                        # Información adicional
                        if limite > 0:
                            utilizacion = (dispuesto / limite) * 100
                            if utilizacion > 80:
                                st.error(f"⚠️ Utilización: {utilizacion:.0f}%")
                            elif utilizacion > 60:
                                st.warning(f"📊 Utilización: {utilizacion:.0f}%")
                            else:
                                st.success(f"✅ Utilización: {utilizacion:.0f}%")
                    
                    # Preparar para modelo (mantener compatibilidad)
                    polizas_credito.append({
                        'tipo_poliza': tipo,
                        'banco': banco,
                        'limite': limite,
                        'dispuesto': dispuesto,
                        'tipo_interes': tipo_interes,
                        'comision_apertura': comision / 100,
                        'comision_no_dispuesto': 0.002 if "Póliza" in tipo else 0
                    })

            # Resumen de financiación
            st.markdown("---")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Límite total", f"{get_simbolo_moneda()}{total_limite:,.0f}")
            with col2:
                st.metric("Total dispuesto", f"{get_simbolo_moneda()}{total_dispuesto:,.0f}")
            with col3:
                st.metric("Disponible", f"{get_simbolo_moneda()}{total_limite - total_dispuesto:,.0f}")
            with col4:
                utilizacion_total = (total_dispuesto / total_limite * 100) if total_limite > 0 else 0
                st.metric("Utilización media", f"{utilizacion_total:.1f}%")

            # Variables para mantener compatibilidad con el resto del código
            poliza_limite = sum([l['limite'] for l in st.session_state.lineas_financiacion if 'Póliza crédito' in l['tipo']])
            poliza_dispuesto = sum([l['dispuesto'] for l in st.session_state.lineas_financiacion if 'Póliza crédito' in l['tipo']])
            descuento_limite = sum([l['limite'] for l in st.session_state.lineas_financiacion if 'Descuento' in l['tipo']])
            descuento_dispuesto = sum([l['dispuesto'] for l in st.session_state.lineas_financiacion if 'Descuento' in l['tipo']])
            factoring_importe = sum([l['dispuesto'] for l in st.session_state.lineas_financiacion if 'Factoring' in l['tipo']])
            confirming_limite = sum([l['limite'] for l in st.session_state.lineas_financiacion if 'Confirming' in l['tipo']])
            # Variables adicionales de compatibilidad (tipos de interés)
            poliza_tipo = st.session_state.lineas_financiacion[0].get('tipo_interes', 4.5) if st.session_state.lineas_financiacion else 4.5
            descuento_tipo = next((l['tipo_interes'] for l in st.session_state.lineas_financiacion if 'Descuento' in l['tipo']), 5.0)
            factoring_tipo = next((l['tipo_interes'] for l in st.session_state.lineas_financiacion if 'Factoring' in l['tipo']), 5.0)
            factoring_recurso = "Con recurso" if any('con recurso' in l['tipo'].lower() for l in st.session_state.lineas_financiacion if 'Factoring' in l['tipo']) else "Sin recurso"
            confirming_coste = next((l.get('tipo_interes', 0.5)/100 for l in st.session_state.lineas_financiacion if 'Confirming' in l['tipo']), 0.02)

            # Total Deuda Financiera CP (para el balance)
            total_deuda_financiera_cp = total_dispuesto
            st.info(f"💰 Total Deuda Financiera CP: {get_simbolo_moneda()}{total_deuda_financiera_cp:,.0f}")
            
            # Pasivo Comercial
            st.markdown("#### Pasivo Comercial")
            col1, col2 = st.columns(2)
            with col1:
                proveedores_inicial = st.number_input(
                    f"Proveedores comerciales ({get_simbolo_moneda()})",
                    min_value=0,
                    value=default_proveedores if 'default_proveedores' in locals() else 0,
                    step=100000,
                    help="Facturas pendientes de pago a proveedores"
                )
            with col2:
                acreedores_servicios = st.number_input(
                    f"Acreedores por servicios ({get_simbolo_moneda()})",
                    min_value=0,
                    value=default_acreedores if 'default_acreedores' in locals() else 0,
                    step=50000,
                    help="Servicios profesionales, suministros, etc."
                )
            total_pasivo_comercial = proveedores_inicial + acreedores_servicios

            # Anticipos de clientes
            anticipos_clientes = st.number_input(
                f"Anticipos de clientes ({get_simbolo_moneda()})",
                min_value=0,
                value=default_anticipos if 'default_anticipos' in locals() else 0,
                step=50000,
                help="Cobros anticipados por ventas futuras"
            )
            
            # Otras Obligaciones CP
            st.markdown("#### Otras Obligaciones a Corto Plazo")
            col1, col2 = st.columns(2)
            with col1:
                remuneraciones_pendientes = st.number_input(
                    f"Remuneraciones pendientes ({get_simbolo_moneda()})",
                    min_value=0,
                    value=default_remuneraciones if 'default_remuneraciones' in locals() else 0,
                    step=10000,
                    help="Salarios, pagas extra, bonus pendientes"
                )
                admin_publica_acreedora = st.number_input(
                    f"Administraciones públicas ({get_simbolo_moneda()})",
                    min_value=0,
                    value=default_admin_acreedora if 'default_admin_acreedora' in locals() else 0,
                    step=50000,
                    help="IRPF, IVA, Seg. Social pendientes"
                )
            with col2:
                # Calcular valor por defecto de provisiones
                # Calcular todas las provisiones
                provision_reestructuracion = st.session_state.get('provision_reestructuracion', 0)
                provision_litigios = st.session_state.get('provision_litigios', 0)
                provision_fiscal = st.session_state.get('provision_fiscal', 0)
                provision_defecto = provision_reestructuracion + provision_litigios + provision_fiscal
                
                provisiones_cp = st.number_input(
                    f"Provisiones a corto plazo ({get_simbolo_moneda()})",
                    min_value=0,
                    value=round(provision_defecto) if provision_defecto > 0 else (default_provisiones_cp if 'default_provisiones_cp' in locals() else 0),
                    step=10000,
                    help=f"Total provisiones: Reestructuración ({get_simbolo_moneda()}{provision_reestructuracion:,.0f}) + Litigios ({get_simbolo_moneda()}{provision_litigios:,.0f}) + Fiscal ({get_simbolo_moneda()}{provision_fiscal:,.0f})"
                )
                
                # Mostrar desglose si hay provisiones
                if provision_defecto > 0:
                    desglose_provisiones = []
                    if provision_reestructuracion > 0:
                        desglose_provisiones.append(f"Reestructuración: {get_simbolo_moneda()}{provision_reestructuracion:,.0f}")
                    if provision_litigios > 0:
                        desglose_provisiones.append(f"Litigios: {get_simbolo_moneda()}{provision_litigios:,.0f}")
                    if provision_fiscal > 0:
                        desglose_provisiones.append(f"Fiscal: {get_simbolo_moneda()}{provision_fiscal:,.0f}")
                    
                    st.caption(f"📌 Desglose: {' | '.join(desglose_provisiones)}")

                otros_pasivos_cp = st.number_input(
                    f"Otros pasivos corrientes ({get_simbolo_moneda()})",
                    min_value=0,
                    value=default_otros_pasivos_cp if 'default_otros_pasivos_cp' in locals() else 0,
                    step=10000,
                    help="Otros pasivos no clasificados"
                )
                
            # Total Pasivo Corriente
            total_pasivo_corriente = (total_deuda_financiera_cp + total_pasivo_comercial +
                                     anticipos_clientes + remuneraciones_pendientes + 
                                     admin_publica_acreedora + provisiones_cp + otros_pasivos_cp)
            st.success(f"**TOTAL PASIVO CORRIENTE: {get_simbolo_moneda()}{total_pasivo_corriente:,.0f}**")
        
        # PASIVO NO CORRIENTE
        with st.expander("📊 PASIVO NO CORRIENTE", expanded=True):
            
            # Deuda Financiera LP
            st.markdown("#### Deuda Financiera a Largo Plazo")
            
            # Préstamos
            with st.container():
                st.markdown("**Préstamos bancarios**")
                col1, col2, col3 = st.columns(3)
                with col1:
                    prestamo_principal = st.number_input(
                        f"Principal pendiente ({get_simbolo_moneda()})",
                        min_value=0,
                        value=default_prestamo_principal if 'default_prestamo_principal' in locals() else 0,
                        step=100000,
                        help="Importe pendiente de amortizar"
                    )
                with col2:
                    prestamo_interes = formato_porcentaje(
                        "Tipo interés",
                        value=3.5,
                        key="prestamo_interes",
                        max_value=15.0,
                    )
                with col3:
                    prestamo_años = st.number_input(
                        "Años restantes",
                        min_value=0,
                        max_value=20,
                        value=5,
                        step=1
                    )
                    
            # Hipotecas
            with st.container():
                st.markdown("**Hipotecas**")
                col1, col2 = st.columns(2)
                with col1:
                    hipoteca_importe_original = st.number_input(
                        f"Importe original hipoteca ({get_simbolo_moneda()})",
                        min_value=0,
                        value=default_hipoteca_original if 'default_hipoteca_original' in locals() else 0,
                        step=100000,
                        help="Importe inicial del préstamo hipotecario"
                    )
                    hipoteca_interes = formato_porcentaje(
                        "Tipo interés hipoteca",
                        value=3.25,
                        key="hipoteca_interes",
                        max_value=10.0,
                    )
                with col2:
                    hipoteca_plazo_total = st.number_input(
                        "Plazo total (años)",
                        min_value=0,
                        max_value=30,
                        value=15,
                        step=1
                    )
                    hipoteca_meses_transcurridos = st.number_input(
                        "Meses transcurridos",
                        min_value=0,
                        max_value=hipoteca_plazo_total * 12,
                        value=default_hipoteca_meses if 'default_hipoteca_meses' in locals() else 60,
                        step=12
                    )
                    
            # Calcular hipoteca pendiente
            if hipoteca_importe_original > 0 and hipoteca_plazo_total > 0:
                meses_totales = hipoteca_plazo_total * 12
                meses_restantes = meses_totales - hipoteca_meses_transcurridos
                if meses_restantes > 0:
                    # Cálculo simplificado del principal pendiente
                    hipoteca_principal = hipoteca_importe_original * (meses_restantes / meses_totales)
                else:
                    hipoteca_principal = 0
            else:
                hipoteca_principal = 0
                
            # Leasing
            with st.container():
                st.markdown("**Leasing**")
                col1, col2 = st.columns(2)
                with col1:
                    leasing_total = st.number_input(
                        f"Valor pendiente leasing ({get_simbolo_moneda()})",
                        min_value=0,
                        value=default_leasing if 'default_leasing' in locals() else 0,
                        step=50000,
                        help="Cuotas pendientes de pago"
                    )
                    leasing_tipo = st.selectbox(
                        "Tipo de leasing",
                        ["Financiero", "Operativo"],
                        help="Financiero: aparece en balance. Operativo: off-balance"
                    )
                with col2:
                    leasing_cuota = st.number_input(
                        f"Cuota mensual ({get_simbolo_moneda()})",
                        min_value=0,
                        value=default_leasing_cuota if 'default_leasing_cuota' in locals() else 0,
                        step=1000
                    )
                    leasing_meses = st.number_input(
                        "Meses restantes",
                        min_value=0,
                        max_value=120,
                        value=default_leasing_meses if 'default_leasing_meses' in locals() else 0,
                        step=1
                    )
                    
            # Otros préstamos LP
            otros_prestamos_lp = st.number_input(
                f"Otros préstamos LP ({get_simbolo_moneda()})",
                min_value=0,
                value=default_otros_prestamos if 'default_otros_prestamos' in locals() else 0,
                step=50000,
                help="Préstamos de socios, entidades de crédito no bancarias, etc."
            )
            
            # Total Deuda Financiera LP
            total_deuda_financiera_lp = (prestamo_principal + hipoteca_principal + 
                                        leasing_total + otros_prestamos_lp)
            st.info(f"💰 Total Deuda Financiera LP: {get_simbolo_moneda()}{total_deuda_financiera_lp:,.0f}")
            
            # Provisiones LP
            st.markdown("#### Provisiones a Largo Plazo")
            col1, col2 = st.columns(2)
            with col1:
                provisiones_riesgos = st.number_input(
                    f"Provisiones para riesgos ({get_simbolo_moneda()})",
                    min_value=0,
                    value=default_provisiones_riesgos if 'default_provisiones_riesgos' in locals() else 0,
                    step=50000,
                    help="Litigios, garantías, responsabilidades"
                )
                # provisiones_laborales ya existe desde el pasivo laboral
            with col2:
                otras_provisiones_lp = st.number_input(
                    f"Otras provisiones LP ({get_simbolo_moneda()})",
                    min_value=0,
                    value=default_otras_provisiones_lp if 'default_otras_provisiones_lp' in locals() else 0,
                    step=10000,
                    help="Otras provisiones a largo plazo"
                )
            total_provisiones_lp = provisiones_riesgos + otras_provisiones_lp
            
            # Pasivos por Impuesto Diferido
            pasivos_impuesto_diferido = st.number_input(
                f"Pasivos por impuesto diferido ({get_simbolo_moneda()})",
                min_value=0,
                value=default_pasivos_impuesto_dif if 'default_pasivos_impuesto_dif' in locals() else 0,
                step=10000,
                help="Diferencias temporarias imponibles"
            )
            
            # Total Pasivo No Corriente
            total_pasivo_no_corriente = (total_deuda_financiera_lp + total_provisiones_lp + 
                                        pasivos_impuesto_diferido)
            st.success(f"**TOTAL PASIVO NO CORRIENTE: {get_simbolo_moneda()}{total_pasivo_no_corriente:,.0f}**")
        
        # TOTAL PASIVOS
        total_pasivos = total_pasivo_corriente + total_pasivo_no_corriente
        st.markdown("---")
        st.markdown(f"### 💳 **TOTAL PASIVOS: {get_simbolo_moneda()}{total_pasivos:,.0f}**")

        # Guardar en session_state para otros tabs
        st.session_state['total_pasivo_corriente'] = total_pasivo_corriente
        st.session_state['total_pasivo_no_corriente'] = total_pasivo_no_corriente
        st.session_state['total_pasivos'] = total_pasivos

    with tab_patrimonio:
        st.markdown("### 🏛️ BALANCE - PATRIMONIO NETO")
        
        # Capital y Reservas
        with st.expander("💎 CAPITAL Y RESERVAS", expanded=True):
            
            # Capital
            st.markdown("#### Capital")
            col1, col2 = st.columns(2)
            with col1:
                capital_social = st.number_input(
                    f"Capital social ({get_simbolo_moneda()})",
                    min_value=3000,  # Mínimo legal SA
                    value=default_capital_social if 'default_capital_social' in locals() else 3000,
                    step=10000,
                    help="Capital escriturado y desembolsado"
                )
            with col2:
                prima_emision = st.number_input(
                    f"Prima de emisión ({get_simbolo_moneda()})",
                    min_value=0,
                    value=default_prima_emision if 'default_prima_emision' in locals() else 0,
                    step=10000,
                    help="Sobreprecio en emisión de acciones"
                )
                
            # Reservas
            st.markdown("#### Reservas")
            col1, col2 = st.columns(2)
            with col1:
                reserva_legal = st.number_input(
                    f"Reserva legal ({get_simbolo_moneda()})",
                    min_value=0,
                    max_value=int(capital_social * 0.2),  # Límite 20% capital
                    value=default_reserva_legal if 'default_reserva_legal' in locals() else min(20000, int(capital_social * 0.2)),
                    step=1000,
                    help="Obligatoria: 10% beneficio hasta 20% capital"
                )
                reservas = st.number_input(
                    f"Otras reservas ({get_simbolo_moneda()})",
                    min_value=0,
                    value=default_otras_reservas if 'default_otras_reservas' in locals() else 0,
                    step=50000,
                    help="Reservas voluntarias, estatutarias, etc."
                )
            with col2:
                total_reservas = reserva_legal + reservas
                st.metric("Total Reservas", f"{get_simbolo_moneda()}{total_reservas:,.0f}")
                
        # Resultados
        with st.expander("📈 RESULTADOS", expanded=True):
            col1, col2 = st.columns(2)
            with col1:
                resultados_acumulados = st.number_input(
                    f"Resultados ejercicios anteriores ({get_simbolo_moneda()})",
                    value=default_resultados_acum if 'default_resultados_acum' in locals() else 0,
                    step=50000,
                    help="Beneficios/pérdidas acumuladas no distribuidas"
                )
            with col2: 
                # Ajustar resultado por provisiones nuevas
                provision_litigios_nueva = st.session_state.get('provision_litigios', 0)
                provision_fiscal_nueva = st.session_state.get('provision_fiscal', 0)
                provision_reestructuracion_nueva = st.session_state.get('provision_reestructuracion', 0)
                ajuste_provisiones = provision_litigios_nueva + provision_fiscal_nueva + provision_reestructuracion_nueva
                
                # Calcular resultado ajustado
                resultado_base = round(default_resultado_ejercicio) if 'default_resultado_ejercicio' in locals() else 0
                resultado_ajustado = round(resultado_base - ajuste_provisiones)

                resultado_ejercicio = st.number_input(
                    f"Resultado del ejercicio ({get_simbolo_moneda()})",
                    value=resultado_ajustado,
                    step=10000,
                    help=f"Beneficio/pérdida del año actual. Ajustado por provisiones: -{get_simbolo_moneda()}{ajuste_provisiones:,.0f}" if ajuste_provisiones > 0 else "Beneficio/pérdida del año actual"
                )
                # Mostrar desglose si hay ajustes por provisiones
                if ajuste_provisiones > 0:
                    desglose_ajustes = []
                    if provision_reestructuracion_nueva > 0:
                        desglose_ajustes.append(f"Reestructuración: {get_simbolo_moneda()}{provision_reestructuracion_nueva:,.0f}")
                    if provision_litigios_nueva > 0:
                        desglose_ajustes.append(f"Litigios: {get_simbolo_moneda()}{provision_litigios_nueva:,.0f}")
                    if provision_fiscal_nueva > 0:
                        desglose_ajustes.append(f"Fiscal: {get_simbolo_moneda()}{provision_fiscal_nueva:,.0f}")
                    
                    st.caption(f"📌 Ajuste por provisiones: {' | '.join(desglose_ajustes)}")
                    
        # Otros componentes
        with st.expander("🔧 OTROS COMPONENTES", expanded=False):
            col1, col2 = st.columns(2)
            with col1:
                ajustes_valor = st.number_input(
                    f"Ajustes por cambio de valor ({get_simbolo_moneda()})",
                    value=default_ajustes_valor if 'default_ajustes_valor' in locals() else 0,
                    step=10000,
                    help="Ajustes por valoración de instrumentos financieros"
                )

            with col2:
                subvenciones = st.number_input(
                    f"Subvenciones de capital ({get_simbolo_moneda()})",
                    min_value=0,
                    value=default_subvenciones if 'default_subvenciones' in locals() else 0,
                    step=10000,
                    help="Subvenciones no reintegrables pendientes de imputar"
                )
                
        # TOTAL PATRIMONIO NETO
        total_patrimonio_neto = (capital_social + prima_emision + total_reservas + 
                                resultados_acumulados + resultado_ejercicio + 
                                ajustes_valor + subvenciones)

        # Recalcular totales para la comprobación
        total_activos = total_activo_corriente + total_activo_no_corriente
        total_pasivos = total_pasivo_corriente + total_pasivo_no_corriente
        st.markdown("---")
        st.markdown(f"### 🏛️ **TOTAL PATRIMONIO NETO: {get_simbolo_moneda()}{total_patrimonio_neto:,.0f}**")
        
        # Verificación del Balance
        st.markdown("---")
        st.markdown("### ✅ COMPROBACIÓN DEL BALANCE")
        
        # Recuperar totales de session_state
        total_activos = st.session_state.get('total_activos', 0)
        total_pasivos = st.session_state.get('total_pasivos', 0)
        
        col1, col2, col3 = st.columns(3)
        with col1:
             st.metric("Total Activos", f"{get_simbolo_moneda()}{total_activos:,.0f}")
        with col2:
            total_pasivo_patrimonio = total_pasivos + total_patrimonio_neto
            st.metric("Pasivos + PN", f"{get_simbolo_moneda()}{total_pasivo_patrimonio:,.0f}")
        with col3:
            diferencia = total_activos - total_pasivo_patrimonio
            if abs(diferencia) < 1:
                st.success("✅ Balance cuadrado")
            else:
                st.error(f"❌ Diferencia: {get_simbolo_moneda()}{diferencia:,.0f}") 

    with tab_proyecciones:
        st.markdown("### 📈 PROYECCIONES")
        st.markdown("---")
        st.markdown("#### Plan de Inversiones (CAPEX)")
        
        col1, col2 = st.columns(2)
        with col1:
            capex_año1 = st.number_input(
                f"Inversión Año 1 ({get_simbolo_moneda()})", 
                min_value=0,
                value=int(default_capex_año1) if 'default_capex_año1' in locals() else 0,
                step=50000,
                help="Sin límite máximo - introduce la inversión necesaria"
            )
            capex_año2 = st.number_input(
                f"Inversión Año 2 ({get_simbolo_moneda()})", 
                min_value=0,
                value=int(default_capex_año2) if 'default_capex_año2' in locals() else 0,
                step=50000
            )
            capex_año3 = st.number_input(
                f"Inversión Año 3 ({get_simbolo_moneda()})", 
                min_value=0,
                value=int(default_capex_año3) if 'default_capex_año3' in locals() else 0,
                step=50000
            )
        with col2:
            capex_año4 = st.number_input(
                f"Inversión Año 4 ({get_simbolo_moneda()})", 
                min_value=0,
                value=int(default_capex_año4) if 'default_capex_año4' in locals() else 0,
                step=50000
            )
            capex_año5 = st.number_input(
                f"Inversión Año 5 ({get_simbolo_moneda()})", 
                min_value=0,
                value=int(default_capex_año5) if 'default_capex_año5' in locals() else 0,
                step=50000
            )
            vida_util = st.slider("Vida útil media (años)", 3, 20, 10)

        st.markdown("---")
        st.markdown("#### Expectativas de Crecimiento")
        col1, col2 = st.columns(2)
        with col1:
          crecimiento_extraordinario = st.number_input(
                "Eventos extraordinarios - Impacto en crecimiento (%)", 
                min_value=-50.0, 
                max_value=100.0, 
                value=0.0, 
                step=5.0,
                help="Ajuste por eventos especiales: contratos grandes (+), pérdida de clientes (-), adquisiciones (+), etc. El modelo ajustará la proyección base con este factor."
            )
        with col2:
            # Mostrar el crecimiento histórico para referencia
            if ventas_año_2 > 0 and ventas_año_1 > 0:
                crecimiento_historico = ((ventas_año_1 - ventas_año_2) / ventas_año_2) * 100
                st.info(f"📊 Crecimiento histórico: {crecimiento_historico:.1f}%")
            else:
                st.info("📊 Crecimiento histórico: N/A")
    
    with tab_parametros:
        st.markdown("### ⚙️ PARÁMETROS OPERATIVOS")
        st.markdown("---")
        
        st.markdown("#### Ciclo de Conversión de Efectivo")
        col1, col2, col3 = st.columns(3)
        with col1:
            dias_cobro = st.number_input("Días de cobro", 0, 120, 60, help="Días promedio de cobro a clientes")
        with col2:
            dias_pago = st.number_input("Días de pago", 0, 90, 30, help="Días promedio de pago a proveedores")
        with col3:
            dias_stock = st.number_input("Días de stock", 0, 90, 45, help="Días de inventario promedio")
    
    # Verificar estado de las APIs

    # Verificar estado de las APIs
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("### 🔄 Estado de Conexión a Datos")
    with col2:
        # Verificar conexión a APIs
        try:
            api_test = APIDataCollector()
            api_test.get_datos_macroeconomicos()
            st.success("✅ APIs Activas")
        except:
            st.warning("⚠️ Modo Offline")
    
# Área principal
if generar_proyeccion:
    
    # Guardar que se generó una proyección
    st.session_state.proyeccion_generada = True

    # Preparar datos para el modelo
    datos_empresa = {
        'nombre': nombre_empresa,
        'sector': sector,
        'empresa_familiar': empresa_familiar == "Sí",
        'empresa_auditada': empresa_auditada,
        'ventas_historicas': [ventas_año_3, ventas_año_2, ventas_año_1],
        'costos_variables_pct': costos_variables_pct,
        'gastos_personal': gastos_personal,
        'gastos_generales': gastos_generales,
        'gastos_marketing': gastos_marketing,
        'otros_gastos': gastos_generales + gastos_marketing,
        'num_empleados': num_empleados,
        'año_fundacion': año_fundacion,
        
        # NUEVA ESTRUCTURA DE FINANCIACIÓN
        'prestamos_lp': {
            'principal': prestamo_principal,
            'tipo_interes': prestamo_interes,
            'años_restantes': prestamo_años,
            'sistema_amortizacion': 'frances'
        },
        'hipotecas': {
            'principal': hipoteca_principal,
            'tipo_interes': hipoteca_interes,
            'años_restantes': round((hipoteca_plazo_total * 12 - hipoteca_meses_transcurridos) / 12, 1) if hipoteca_importe_original > 0 else 0
        },
        'leasings': {
            'valor_total': leasing_total,
            'cuota_mensual': leasing_cuota,
            'meses_restantes': leasing_meses,
            'tipo': leasing_tipo.lower() if leasing_total > 0 else 'operativo'
        },
        'polizas_credito': [
            pol for pol in [
                {
                    'limite': poliza_limite,
                    'dispuesto': poliza_dispuesto,
                    'tipo_interes': poliza_tipo,
                    'comision_apertura': 0.005,
                    'comision_no_dispuesto': 0.002,
                    'tipo_poliza': 'credito'
                } if poliza_limite > 0 else None,
                {
                    'limite': descuento_limite,
                    'dispuesto': descuento_dispuesto,
                    'tipo_interes': descuento_tipo,
                    'comision_apertura': 0.003,
                    'comision_no_dispuesto': 0.001,
                    'tipo_poliza': 'descuento_comercial'
                } if descuento_limite > 0 else None
            ] if pol is not None
        ],
        'factoring': {
            'limite': factoring_importe,
            'porcentaje_anticipable': 0.80,
            'coste': factoring_tipo,
            'con_recurso': factoring_recurso
        },
        'confirming': {
            'limite': confirming_limite,
            'plazo_pago': 90,
            'coste_proveedor': confirming_coste if confirming_limite > 0 else 0.02,
            'coste_empresa': 0.01
        },
        
        # PLAN DE INVERSIONES
        'plan_inversiones': {
            'año_1': capex_año1,
            'año_2': capex_año2,
            'año_3': capex_año3,
            'año_4': capex_año4,
            'año_5': capex_año5,
            'vida_util_media': vida_util
        },
        
        # PARÁMETROS OPERATIVOS
        'dias_cobro': dias_cobro,
        'dias_pago': dias_pago,
        'dias_stock': dias_stock,
        
        # Mantener compatibilidad temporal
        'deuda_actual': prestamo_principal + hipoteca_principal + leasing_total + otros_prestamos_lp + total_dispuesto,
        'tipo_interes': prestamo_interes if prestamo_principal > 0 else 0.05,
        
        # Agregar datos del balance inicial
        'balance_activo': {
            'clientes_inicial': clientes_inicial,
            'inventario_inicial': inventario_inicial
        },
        'balance_pasivo': {
            'proveedores_inicial': proveedores_inicial
        }
    }

    # Guardar datos_empresa en session_state para uso posterior
    st.session_state['datos_empresa'] = datos_empresa

    # Preparar datos para el nuevo modelo
    empresa_info = {
        'nombre': nombre_empresa,
        'sector': sector,
        'empresa_familiar': empresa_familiar,
        'empresa_auditada': empresa_auditada,
        'año_fundacion': año_fundacion,
        'empleados': num_empleados,  # Cambiado para usar el campo nuevo
        'coste_medio_empleado': coste_medio_empleado,
        'provisiones_laborales': provisiones_laborales,
        'meses_indemnizacion': meses_indemnizacion,
        'antiguedad_media': antiguedad_media,
        'rotacion_anual': rotacion_anual,
        'pasivo_laboral_total': pasivo_laboral_total,
        # Agregar datos del balance inicial
        'balance_activo': {
            'clientes_inicial': clientes_inicial,
            'inventario_inicial': inventario_inicial
        },
        'balance_pasivo': {
            'proveedores_inicial': proveedores_inicial
        }
    }
    # Margen EBITDA esperado basado en el sector
    margenes_por_sector = {
        "Hostelería": 0.15,
        "Tecnología": 0.25,
        "Ecommerce": 0.10,
        "Consultoría": 0.30,
        "Retail": 0.12,
        "Servicios": 0.20,
        "Automoción": 0.15,
        "Industrial": 0.18,
        "Otro": 0.15
    }
    margen_ebitda_esperado = margenes_por_sector.get(sector, 0.15)

    # Calcular EBITDA real basado en datos introducidos
    coste_ventas_total = ventas_año_1 * costos_variables_pct
    gastos_totales = gastos_personal + gastos_generales + gastos_marketing
    ebitda_real = ventas_año_1 - coste_ventas_total - gastos_totales
    margen_ebitda_real = (ebitda_real / ventas_año_1 * 100) if ventas_año_1 > 0 else 0
    
    # Mostrar comparación con sector
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(
            "EBITDA Real Calculado",
            f"{get_simbolo_moneda()}{ebitda_real:,.0f}",
            f"{margen_ebitda_real:.1f}% margen"
        )
    with col2:
        st.metric(
            "Margen Sector",
            f"{margen_ebitda_esperado*100:.1f}%",
            f"{sector}"
        )
    with col3:
        diferencia_margen = margen_ebitda_real - (margen_ebitda_esperado * 100)
        st.metric(
            "Diferencia vs Sector",
            f"{diferencia_margen:+.1f}pp",
            "Mejor" if diferencia_margen > 0 else "Peor"
        )

    # Escenario macro con valores por defecto
    escenario_macro = {
        'pib': 1.9,  # Dato actual España
        'inflacion': 2.5,
        'euribor': 2.7,
        'desempleo': 11.7
    }
    
    # Mostrar información sobre datos actualizados
    with st.expander("ℹ️ Fuente de datos macroeconómicos", expanded=False):
        st.info("""
        Los datos macroeconómicos se actualizan automáticamente de fuentes oficiales:
        - **PIB**: Instituto Nacional de Estadística (INE)
        - **Inflación**: INE - IPC
        - **Euribor**: Banco Central Europeo
        - **Desempleo**: INE - EPA
        
        Si las APIs no están disponibles, se usan valores por defecto.
        """)

    # Mostrar datos actuales si se están usando APIs
    if st.session_state.get('mostrar_datos_api', True):
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("PIB", f"{escenario_macro['pib']}%", help="Crecimiento PIB España")
        with col2:
            st.metric("Inflación", f"{escenario_macro['inflacion']}%", help="IPC anual")
        with col3:
            st.metric("Euribor", f"{escenario_macro['euribor']}%", help="Euribor 12 meses")
        with col4:
            st.metric("Desempleo", f"{escenario_macro['desempleo']}%", help="Tasa de paro EPA")

    # Calcular variables necesarias
    # Calcular crecimiento base inteligente
    if ventas_año_2 > 0:
        crecimiento_historico = ((ventas_año_1 - ventas_año_2) / ventas_año_2) * 100
    else:
        crecimiento_historico = 0.05  # 5% por defecto
    
    # Añadir factor extraordinario al crecimiento histórico
    tasa_crecimiento = crecimiento_historico + crecimiento_extraordinario  # Ya está en porcentaje
    
    # Variables de deuda faltantes
    prestamo_plazo = prestamo_años if prestamo_principal > 0 else 5
    hipoteca_plazo = round((hipoteca_plazo_total * 12 - hipoteca_meses_transcurridos) / 12, 1) if hipoteca_principal > 0 else 15
    sistema_amortizacion = 'frances'  # Por defecto
    leasing_importe = leasing_total  # Usar el valor de leasing_total

    params_operativos = {
        'ingresos_iniciales': ventas_año_1,
        'crecimiento_ventas': tasa_crecimiento,
        'margen_ebitda': margen_ebitda_esperado,
        'margen_ebitda': margen_ebitda_esperado,
        'ebitda_real': ebitda_real,
        'margen_ebitda_real': margen_ebitda_real / 100,  # Convertir a decimal
        'gastos_personal': gastos_personal,
        'gastos_generales': gastos_generales,
        'gastos_marketing': gastos_marketing,
        'tesoreria': tesoreria_inicial,
        'clientes': clientes_inicial,
        'inventario': inventario_inicial,
        'proveedores': proveedores_inicial,
        'pasivo_laboral': pasivo_laboral_total,
        'provisiones_laborales': provisiones_laborales,
        'inversiones_cp': inversiones_cp,
        'gastos_anticipados': gastos_anticipados,
        'otros_activos_corrientes': otros_activos_corrientes,
        'otros_deudores': otros_deudores,
        'admin_publica_deudora': admin_publica_deudora,
        'activos_impuesto_diferido_cp': activos_impuesto_diferido_cp,
        'amortizacion_intangibles': amortizacion_intangibles,
        'creditos_lp': creditos_lp,
        'fianzas_depositos': fianzas_depositos,
        'activos_impuesto_diferido_lp': activos_impuesto_diferido_lp,
        'acreedores_servicios': acreedores_servicios,
        'remuneraciones_pendientes': remuneraciones_pendientes,
        'admin_publica_acreedora': admin_publica_acreedora,
        'provisiones_cp': provisiones_cp,
        'otros_pasivos_cp': otros_pasivos_cp,
        'anticipos_clientes': anticipos_clientes,
        'otros_prestamos_lp': otros_prestamos_lp,
        'provisiones_riesgos': provisiones_riesgos,
        'otras_provisiones_lp': otras_provisiones_lp,
        'pasivos_impuesto_diferido': pasivos_impuesto_diferido,
        'prima_emision': prima_emision,
        'reserva_legal': reserva_legal,
        'resultado_ejercicio': resultado_ejercicio,
        'ajustes_valor': ajustes_valor,
        'subvenciones': subvenciones,
        'capex_ventas': 3.0,
        'dias_cobro': dias_cobro,
        'dias_pago': dias_pago,
        'dias_inventario': dias_stock,
        'activo_fijo': activo_fijo_neto,
        'activo_fijo_bruto': activo_fijo_bruto,
        'depreciacion_acumulada': depreciacion_acumulada,
        'activos_intangibles': activos_intangibles,
        'inversiones_lp': inversiones_lp,
        'otros_activos_nc': otros_activos_nc,
        'capital_social': capital_social,
        'reservas': reservas,
        'resultados_acumulados': resultados_acumulados,
        'tasa_impuestos': tipo_impositivo,
        'rating': 'BB', 
        'rating': 'BB',
        'costos_variables_pct': costos_variables_pct,
        'gastos_personal': gastos_personal,
        'gastos_generales': gastos_generales,
        'gastos_marketing': gastos_marketing,
        'otros_gastos': datos_empresa.get('otros_gastos', 0),        
        'prestamos_lp': [
            {
                'principal': prestamo_principal,
                'tipo_interes': prestamo_interes,
                'plazo_años': prestamo_plazo,
                'año_inicio': 1,
                'metodo_amortizacion': sistema_amortizacion
            }
        ] if prestamo_principal > 0 else [],
        'hipotecas': [
            {
                'principal': hipoteca_principal,
                'tipo_interes': hipoteca_interes,
                'plazo_años': hipoteca_plazo,
                'año_inicio': 1
            }
        ] if hipoteca_principal > 0 else [],
        'leasings': [
            {
                'principal': leasing_total,
                'cuota_mensual': leasing_cuota,
                'meses_restantes': leasing_meses,
                'tipo': leasing_tipo,
                'año_inicio': 1
            }
        ] if leasing_total > 0 else [],
        'plan_capex': [
            {'año': 1, 'importe': capex_año1, 'tipo': 'expansion'},
            {'año': 2, 'importe': capex_año2, 'tipo': 'expansion'},
            {'año': 3, 'importe': capex_año3, 'tipo': 'expansion'},
            {'año': 4, 'importe': capex_año4, 'tipo': 'expansion'},
            {'año': 5, 'importe': capex_año5, 'tipo': 'expansion'}
        ],
        'polizas_credito': [
            pol for pol in [
                {
                    'limite': poliza_limite,
                    'dispuesto': poliza_dispuesto,
                    'tipo_interes': poliza_tipo,
                    'tipo_poliza': 'credito'
                } if poliza_limite > 0 else None,
                {
                    'limite': descuento_limite,
                    'dispuesto': descuento_dispuesto,
                    'tipo_interes': descuento_tipo,
                    'tipo_poliza': 'descuento_comercial'
                } if descuento_limite > 0 else None
            ] if pol is not None
        ]
    }
    
    # Crear modelo y generar proyecciones
    with st.spinner('Generando proyecciones financieras...'):
        modelo = ModeloFinanciero(empresa_info, escenario_macro, params_operativos)
        
    
        # Generar todas las proyecciones
        proyecciones = modelo.generar_proyecciones(5)
        
        # Extraer los DataFrames
        pyl = proyecciones['pyl']
        balance = proyecciones['balance']
        cash_flow = proyecciones['cash_flow']
        ratios = proyecciones['ratios']
        valoracion = proyecciones['valoracion']

        # Adaptar estructura de valoración al formato esperado por app.py
        valoracion_adaptada = {
            'valor_empresa': valoracion.get('valoracion_dcf', {}).get('valor_empresa', 0),
            'valor_equity': valoracion.get('valoracion_dcf', {}).get('valor_equity', 0),
            'wacc_utilizado': valoracion.get('wacc_detalle', {}).get('wacc', 10.0),
            'ev_ebitda_salida': valoracion.get('valoracion_multiplos', {}).get('multiplo_aplicado', 5.0),
            'tir_esperada': valoracion.get('tir_esperada', 0),
            'money_multiple': abs(valoracion.get('tir_esperada', 0) / 10) if valoracion.get('tir_esperada', 0) != 0 else 1.5,
            'valor_terminal_pct': (valoracion.get('valoracion_dcf', {}).get('vp_valor_terminal', 0) / 
                                valoracion.get('valoracion_dcf', {}).get('valor_empresa', 1) * 100) if valoracion.get('valoracion_dcf', {}).get('valor_empresa', 0) > 0 else 50,
            'valoracion_escenario_bajo': valoracion.get('analisis_sensibilidad', {}).get('wacc_15.6%', 0),
            'valoracion_escenario_alto': valoracion.get('analisis_sensibilidad', {}).get('wacc_11.6%', 0),
            'rango_valoracion': f"{get_simbolo_moneda()}{valoracion.get('analisis_sensibilidad', {}).get('wacc_15.6%', 0):,.0f} - {get_simbolo_moneda()}{valoracion.get('analisis_sensibilidad', {}).get('wacc_11.6%', 0):,.0f}"
        }

        # Usar la valoración adaptada en lugar de la original
        valoracion = valoracion_adaptada

        # Compatibilidad con código antiguo
        wc_df = None  # Se calculará si es necesario
        financiacion_df = None  # Se calculará si es necesario
        fcf_df = cash_flow  # Usar el cash_flow del nuevo modelo

        # Transformar columnas del nuevo modelo a nombres esperados por app.py
        pyl = pyl.rename(columns={
            'año': 'Año',
            'ingresos': 'Ventas',
            'coste_ventas': 'Costos',
            'margen_bruto': 'Margen Bruto',
            'gastos_personal': 'Gastos Personal',
            'otros_gastos': 'Otros Gastos',
            'ebitda': 'EBITDA',
            'margen_ebitda_%': 'EBITDA %',
            'amortizacion': 'Amortización',
            'ebit': 'EBIT',
            'gastos_financieros': 'Gastos Financieros',
            'bai': 'BAI',
            'impuestos': 'Impuestos',
            'beneficio_neto': 'Beneficio Neto'
        })

        # Agregar columnas calculadas que espera app.py
        pyl['Margen Bruto %'] = (pyl['Margen Bruto'] / pyl['Ventas'] * 100).round(1)
        pyl['Beneficio Neto %'] = (pyl['Beneficio Neto'] / pyl['Ventas'] * 100).round(1)
        
        # AGREGAR AQUÍ - Transformar columnas de cash_flow
        cash_flow = cash_flow.rename(columns={
            'año': 'Año',
            'flujo_operativo': 'Flujo Operativo',
            'flujo_inversion': 'Flujo Inversión',
            'flujo_financiero': 'Flujo Financiero',
            'flujo_total': 'Flujo Total',
            'free_cash_flow': 'Free Cash Flow'
        })

        # Para mantener compatibilidad con el código existente
        metricas = {
            'cagr_ventas': ((pyl['Ventas'].iloc[-1] / pyl['Ventas'].iloc[0]) ** (1/5) - 1) * 100,
            'margen_ebitda_promedio': pyl['EBITDA %'].mean(),
            'tir_proyecto': 15.0,  # Valor temporal
            'payback_simple': 5,
            'crecimiento_ventas_promedio': ((pyl['Ventas'].iloc[-1] / pyl['Ventas'].iloc[0]) ** (1/5) - 1) * 100,
            'roi_proyectado': 25.0  # Valor temporal
        }

        # Generar resumen ejecutivo
        # resumen = modelo.generar_resumen_ejecutivo()  # El modelo espera columnas originales
        # Crear resumen simple con los datos transformados
        resumen = f"""
        RESUMEN EJECUTIVO - {nombre_empresa}
        {'=' * 50}

        Sector: {sector}
        Proyección a 5 años

        RESULTADOS CLAVE:
        - Ventas año 5: {get_simbolo_moneda()}{pyl['Ventas'].iloc[-1]:,.0f}
        - EBITDA año 5: {get_simbolo_moneda()}{pyl['EBITDA'].iloc[-1]:,.0f} ({pyl['EBITDA %'].iloc[-1]:.1f}%)
        - Beneficio año 5: {get_simbolo_moneda()}{pyl['Beneficio Neto'].iloc[-1]:,.0f}

        CRECIMIENTO:
        - CAGR Ventas: {metricas['cagr_ventas']:.1f}%
        - Margen EBITDA promedio: {metricas['margen_ebitda_promedio']:.1f}%

        VALORACIÓN:
        - Valor empresa: {get_simbolo_moneda()}{valoracion.get('valor_empresa', 0):,.0f}
        - TIR proyecto: {metricas['tir_proyecto']:.1f}%
        """
    
   # Crear analisis_ia con la nueva información

        # Obtener datos históricos para el análisis
        datos_empresa = st.session_state.get('datos_empresa', {})
        if datos_empresa and 'ventas_historicas' in datos_empresa:
            ventas_historicas = datos_empresa['ventas_historicas'][-1] if isinstance(datos_empresa['ventas_historicas'], list) else datos_empresa['ventas_historicas']
            costos_pct = datos_empresa.get('costos_variables_pct', 0)
            gastos_personal = datos_empresa.get('gastos_personal', 0)
            gastos_generales = datos_empresa.get('gastos_generales', 0)
            gastos_marketing = datos_empresa.get('gastos_marketing', 0)
            margen_bruto = ventas_historicas * (1 - costos_pct)
        else:
            # Fallback a valores del primer año proyectado
            ventas_historicas = pyl['Ventas'].iloc[0]
            margen_bruto = pyl['Margen Bruto'].iloc[0]
            gastos_personal = pyl['Gastos Personal'].iloc[0]
            gastos_generales = 0
            gastos_marketing = 0

        # Análisis profesional estilo CFO/M&A
        # Calcular métricas adicionales para el análisis
        # Asegurar que las variables están definidas
        if 'ebitda_actual' not in locals():
            ebitda_actual = pyl['EBITDA'].iloc[0]
        if 'ventas_historicas' not in locals():
            ventas_historicas = pyl['Ventas'].iloc[0]
        if 'margen_ebitda_actual' not in locals():
            margen_ebitda_actual = (ebitda_actual / ventas_historicas * 100) if ventas_historicas > 0 else 0

        # Obtener valoración profesional
        valoracion_prof = modelo.realizar_valoracion_bancainversion() if hasattr(modelo, 'realizar_valoracion_bancainversion') else {}
        valor_empresa_calc = valoracion_prof.get('valoracion_final', 0)    
        # Obtener TIR real
        tir_real = valoracion_prof.get('dcf_detalle', {}).get('tir', metricas.get('tir_proyecto', 0))
        multiplo_ventas = valor_empresa_calc / ventas_historicas if ventas_historicas > 0 else 0
        multiplo_ebitda = valor_empresa_calc / ebitda_actual if ebitda_actual > 0 else 0

        # Obtener EBITDA histórico real
        ventas_hist = st.session_state.get('ventas_1', ventas_historicas)
        costos_pct = st.session_state.get('costos_variables_slider', 40) / 100
        gastos_personal = st.session_state.get('gastos_personal_key', 0)
        gastos_generales = st.session_state.get('gastos_generales_key', 0)
        gastos_marketing = st.session_state.get('gastos_marketing_key', 0)

        margen_bruto = ventas_hist * (1 - costos_pct)
        ebitda_historico = margen_bruto - gastos_personal - gastos_generales - gastos_marketing

        # Calcular múltiplos profesionales LTM/NTM
        multiplo_ebitda_ltm = valor_empresa_calc / ebitda_historico if ebitda_historico > 0 else 0
        multiplo_ebitda_ntm = valor_empresa_calc / pyl['EBITDA'].iloc[0] if pyl['EBITDA'].iloc[0] > 0 else 0
        multiplo_ventas_ltm = valor_empresa_calc / ventas_historicas if ventas_historicas > 0 else 0

        analisis_ia = {
            'resumen': f"Deal atractivo con TIR {metricas['tir_proyecto']:.1f}% y múltiplo EV/EBITDA {multiplo_ebitda:.1f}x",
            'multiplo_ebitda_ltm': multiplo_ebitda_ltm,
            'multiplo_ebitda_ntm': multiplo_ebitda_ntm,
            'multiplo_ventas_ltm': multiplo_ventas_ltm,
            'resumen_ejecutivo': f"""
            
            **INVESTMENT THESIS**
            
            {nombre_empresa} presenta una oportunidad de inversión {'excepcional' if metricas['tir_proyecto'] > 30 else 'atractiva'} 
            en el sector {sector} con las siguientes características:
            
            **Valoración**: Enterprise Value de {get_simbolo_moneda()}{valor_empresa_calc:,.0f} 
            ({multiplo_ebitda_ltm:.1f}x EBITDA LTM / {multiplo_ebitda_ntm:.1f}x EBITDA NTM, {multiplo_ventas_ltm:.1f}x ventas LTM)
            
            **Crecimiento**: CAGR del {metricas['cagr_ventas']:.1f}% en ventas,
            alcanzando {get_simbolo_moneda()}{pyl['Ventas'].iloc[-1]/1e6:.1f}M en año 5
            
            **Rentabilidad**: Mejora de margen EBITDA desde {margen_ebitda_actual:.1f}% actual hasta 
            {pyl['EBITDA %'].iloc[-1]:.1f}% en año 5 (+{pyl['EBITDA %'].iloc[-1] - margen_ebitda_actual:.0f}pp)
                  
            **Retorno**: TIR del proyecto {tir_real:.1f}% con payback
            
            **Estructura de capital**: Ratio D/E actual {ratios.iloc[0]['ratio_endeudamiento']:.1f}x con capacidad de 
            apalancamiento adicional hasta 3.0x para acelerar crecimiento
            
            **Exit Strategy**: Múltiples salidas viables en 3-5 años vía trade sale (competidores estratégicos), 
            secondary buyout (fondos de PE) o {'IPO' if valoracion.get('valor_empresa', 0) > 50e6 else 'venta estratégica'}
            """,
            'viabilidad': 'ALTA' if metricas['tir_proyecto'] > 20 else 'MEDIA' if metricas['tir_proyecto'] > 10 else 'BAJA',
            'rating': '⭐⭐⭐⭐⭐' if metricas['tir_proyecto'] > 30 else '⭐⭐⭐⭐' if metricas['tir_proyecto'] > 20 else '⭐⭐⭐',
            'fortalezas': [
                f"Valoración atractiva: {multiplo_ebitda_ltm:.1f}x EBITDA LTM / {multiplo_ebitda_ntm:.1f}x EBITDA NTM (vs {multiplo_ebitda * 1.5:.1f}x peers)",
                f"Margen EBITDA escalable: {margen_ebitda_actual:.1f}% → {pyl['EBITDA %'].iloc[-1]:.1f}%",
                f"FCF yield del {(cash_flow['Free Cash Flow'].iloc[-1] / valoracion.get('valor_empresa', 1)) * 100:.1f}% en año 5"
            ],
            'riesgos': [
                f"Working capital intensivo: {((balance['clientes'].iloc[-1] + balance['inventario'].iloc[-1]) / pyl['Ventas'].iloc[-1] * 365):.0f} días",
                f"Concentración {'sectorial' if 'ecommerce' in sector.lower() else 'geográfica'}: mercado {'online competitivo' if 'ecommerce' in sector.lower() else 'local'}"
            ],
            'recomendaciones': [
                f"Entry múltiple target: {multiplo_ebitda * 0.8:.1f}x EBITDA (20% descuento)",
                f"Estructura deal: 70% equity, 30% earn-out basado en EBITDA año 2",
                f"Value creation: Focus en {'conversión online' if 'ecommerce' in sector.lower() else 'eficiencia operativa'} (+300bps margen)"
            ]
        }
    
    # AQUÍ - Crear DataFrames de compatibilidad
    # Crear DataFrame de capital de trabajo
    wc_data = []
    for i in range(len(balance)):
        clientes = balance.iloc[i]['clientes']
        inventario = balance.iloc[i]['inventario']
        proveedores = balance.iloc[i]['proveedores']
        capital_trabajo = clientes + inventario - proveedores
        
        variacion = 0 if i == 0 else capital_trabajo - wc_data[i-1]['Capital de Trabajo']
        
        wc_data.append({
            'Año': i + 1,
            'Capital de Trabajo': capital_trabajo,
            'Variación': variacion
        })
    
    wc_df = pd.DataFrame(wc_data)
    
    # Crear DataFrame de financiación
    financiacion_data = []
    for i in range(len(pyl)):
        ventas = pyl['Ventas'].iloc[i]
        limite = ventas * 0.25
        necesidad = wc_df['Capital de Trabajo'].iloc[i]
        uso = min(necesidad, limite)
        
        financiacion_data.append({
            'Año': i + 1,
            'Límite Póliza': limite,
            'Uso Póliza': uso,
            'Disponible': limite - uso,
            'Coste Póliza': uso * 0.06,
            'Exceso/(Déficit)': limite - necesidad
        })
    
    financiacion_df = pd.DataFrame(financiacion_data)
    fcf_df = cash_flow

    # Guardar todos los datos en session state
    st.session_state.datos_guardados = {
        'nombre_empresa': nombre_empresa,
        'sector': sector,
        'proyecciones': proyecciones,
        'pyl': pyl,
        'balance': balance,
        'cash_flow': cash_flow,
        'ratios': ratios,
        'valoracion': valoracion,
        'valoracion_profesional': modelo.realizar_valoracion_bancainversion() if hasattr(modelo, 'realizar_valoracion_bancainversion') else None,
        'metricas': metricas,
        'analisis_ia': analisis_ia,
        'resumen': resumen,
        # Mantener compatibilidad con código antiguo
        'datos_empresa': datos_empresa,
        'wc_df': None,
        'financiacion_df': None,
        'fcf_df': cash_flow,
        # Datos para recrear el modelo
        'modelo_params': {
            'ingresos_iniciales': params_operativos.get('ingresos_iniciales', 0),
            'margen_ebitda_inicial': params_operativos.get('margen_ebitda', 10),
            'crecimiento_ventas': params_operativos.get('crecimiento_ventas', 5),
            'empleados': datos_empresa.get('num_empleados', 10),
            'año_fundacion': datos_empresa.get('año_fundacion', datetime.now().year - 5),
            'tesoreria_inicial': params_operativos.get('tesoreria', 500000),
            'capital_social': params_operativos.get('capital_social', 3000000),
            'prestamos_lp': params_operativos.get('prestamos_lp', []),
            'hipotecas': params_operativos.get('hipotecas', []),
            'leasings': params_operativos.get('leasings', []),
            'polizas_credito': params_operativos.get('polizas_credito', [])
        }
  
    }
    
    # Actualizar análisis_ia con valoración real si existe
    if st.session_state.datos_guardados.get('valoracion_profesional'):
        val_prof = st.session_state.datos_guardados['valoracion_profesional']
        if val_prof and val_prof.get('valoracion_final'):
            valor_real = val_prof.get('valoracion_final', 0)
            tir_real = val_prof.get('dcf_detalle', {}).get('tir', st.session_state.datos_guardados['metricas'].get('tir_proyecto', 0))
            
            # Actualizar resumen ejecutivo con la valoración real
            #st.session_state.datos_guardados['analisis_ia']['resumen_ejecutivo'] = f"""
            #La empresa {st.session_state.datos_guardados['nombre_empresa']} del sector {st.session_state.datos_guardados['sector']} presenta un plan de negocio con 
            #crecimiento proyectado del {st.session_state.datos_guardados['metricas']['cagr_ventas']:.1f}% anual, alcanzando ventas de {get_simbolo_moneda()}{st.session_state.datos_guardados['pyl']['Ventas'].iloc[-1]:,.0f}
            #en el año 5. El margen EBITDA promedio es del {st.session_state.datos_guardados['metricas']['margen_ebitda_promedio']:.1f}%.
            
            #La valoración estimada es de {get_simbolo_moneda()}{valor_real:,.0f} con un ROI esperado del {tir_real:.1f}%.
            #La viabilidad del proyecto se considera {st.session_state.datos_guardados['analisis_ia']['viabilidad']}.
            #""" 
            # Actualizar también las fortalezas con la valoración real
            st.session_state.datos_guardados['analisis_ia']['fortalezas'][2] = f"Valoración: {get_simbolo_moneda()}{valor_real:,.0f}"
    # Mostrar resultados
    st.success("✅ Proyección generada exitosamente!")

    # Tabs para organizar la información
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs(
        ["💼 Dashboard", "📊 P&L Detallado", "🗂️ Balance Proyectado", "📈 Analytics", "📑 Resumen Ejecutivo", "💎 Valoración", "📄 Documentos", "📚 Glosario"])

    with tab1:
        st.header("Dashboard de Métricas Clave")

        # Métricas principales en cards
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
            label="Ventas Año 5",
            value=f"{get_simbolo_moneda()}{st.session_state.datos_guardados["pyl"]['Ventas'].iloc[-1]:,.0f}",
            delta=f"{st.session_state.datos_guardados["metricas"]['crecimiento_ventas_promedio']:.1f}% crecimiento anual"
        )

        with col2:
            st.metric(
            label="EBITDA Año 5",
            value=f"{get_simbolo_moneda()}{st.session_state.datos_guardados["pyl"]['EBITDA'].iloc[-1]:,.0f}",
            delta=f"{st.session_state.datos_guardados["pyl"]['EBITDA %'].iloc[-1]}% margen"
        )

        with col3:
            st.metric(
            label="Beneficio Año 5",
            value=f"{get_simbolo_moneda()}{st.session_state.datos_guardados["pyl"]['Beneficio Neto'].iloc[-1]:,.0f}",
            delta=f"{st.session_state.datos_guardados["pyl"]['Beneficio Neto %'].iloc[-1]}% margen"
        )

        with col4:
            st.metric(
            label="ROI Proyectado",
            value=f"{st.session_state.datos_guardados["metricas"]['roi_proyectado']}%"
        )

    with tab5:
        mostrar_resumen_ejecutivo_profesional(
            st.session_state.datos_guardados['datos_empresa'].get('num_empleados', 10),
            st.session_state.datos_guardados['datos_empresa'].get('año_fundacion', 2020)
        )

    with tab6:
        st.header("💎 Valoración Profesional - Metodología M&A")

        # AÑADIR ESTE EXPANDER
        with st.expander("📚 ¿Cómo se calcula la valoración de tu empresa?", expanded=False):
            st.markdown("""
            ### 🎯 Metodología de Valoración Profesional
            
            Utilizamos un **enfoque múltiple** similar al usado por bancos de inversión, combinando 4 métodos:
            
            #### 1️⃣ **DCF (Descuento de Flujos de Caja) - 40% peso**
            - Proyectamos los flujos de caja libres (FCF) a 5 años
            - Calculamos el valor terminal usando crecimiento perpetuo (g = inflación + 0.5%)
            - Descontamos todo al presente usando el WACC (coste medio ponderado del capital)
            - **Ventaja**: Refleja la capacidad real de generar caja de tu negocio
            
            #### 2️⃣ **Múltiplos de Mercado - 20% peso**
            - **EV/EBITDA**: Valor Empresa / EBITDA (múltiplo más usado en M&A)
            - **EV/Ventas**: Para empresas en crecimiento o con márgenes variables
            - **Ventaja**: Refleja lo que inversores pagan por empresas similares
            
            #### 3️⃣ **Transacciones Comparables - 20% peso**
            - Analizamos ventas recientes de empresas del mismo sector
            - Ajustamos por tamaño, crecimiento y márgenes
            - **Ventaja**: Precios reales pagados en el mercado
            
            #### 4️⃣ **Valoración Sectorial - 20% peso**
            - Múltiplos específicos de tu sector
            - Consideramos tendencias y perspectivas del sector
            - **Ventaja**: Captura las particularidades de tu industria
            
            ### 📊 Ajustes Automáticos Aplicados
            
            **✅ Premios por:**
            - Márgenes EBITDA superiores al sector (+10-25%)
            - Alto crecimiento vs. competidores (+10-20%)
            - Bajo endeudamiento (Deuda/EBITDA < 2x) (+10%)
            - Posición de liderazgo en nicho (+5-15%)
            
            **❌ Descuentos por:**
            - Tamaño pequeño (<€10M ventas) (-25%)
            - **Empresa familiar** (-30% por iliquidez)
            - Alta concentración de clientes (-10-20%)
            - Dependencia del fundador (-10-15%)
            
            ### 💡 Interpretación de tu Valoración
            
            - **Valoración Central**: Precio justo en condiciones normales
            - **Rango Mínimo**: Venta rápida o momento difícil (-20%)
            - **Rango Máximo**: Comprador estratégico con sinergias (+20%)
            
            ⚠️ **Nota**: Esta es una valoración indicativa. Una valoración formal requiere 
            due diligence completa, análisis de contratos, y evaluación de activos intangibles.
            """)
        
        # EQUITY BRIDGE - Solo si el usuario lo activó
        if st.session_state.get('mostrar_equity_bridge', False):
            st.markdown("---")
            
            # Obtener valores necesarios
            valor_empresa = valoracion_prof.get('valoracion_final', 0) if 'valoracion_prof' in locals() else 0
            deuda_neta = valoracion_prof.get('deuda_neta', 0) if 'valoracion_prof' in locals() else 0
            provision_reest = st.session_state.get('provision_reestructuracion', 0)
            provision_litigios = st.session_state.get('provision_litigios', 0)
            provision_fiscal = st.session_state.get('provision_fiscal', 0)
            
            with st.expander("💰 **Equity Value Bridge** - Análisis Profesional M&A", expanded=True):
                col_bridge1, col_bridge2 = st.columns([3, 1])
                
                with col_bridge1:
                    # Cálculos del bridge
                    equity_value = valor_empresa - deuda_neta
                    total_provisiones = provision_reest + provision_litigios + provision_fiscal
                    equity_ajustado = equity_value - total_provisiones
                    
                    st.markdown(f"""```
Enterprise Value (Valor del Negocio):     {get_simbolo_moneda()}{valor_empresa:>15,.0f}
(-) Deuda Financiera Neta:                {get_simbolo_moneda()}{deuda_neta:>15,.0f}
{"─" * 65}
= Equity Value:                           {get_simbolo_moneda()}{equity_value:>15,.0f}

Ajustes debt-like items:
(-) Provisión Reestructuración:           {get_simbolo_moneda()}{provision_reest:>15,.0f}
(-) Provisión Litigios:                   {get_simbolo_moneda()}{provision_litigios:>15,.0f}
(-) Provisión Contingencias Fiscales:     {get_simbolo_moneda()}{provision_fiscal:>15,.0f}
{"─" * 65}
= Equity Value Ajustado:                  {get_simbolo_moneda()}{equity_ajustado:>15,.0f}
```""")
                    
                    # Explicación adicional
                    if total_provisiones > 0:
                        impacto_porcentual = (total_provisiones / valor_empresa * 100) if valor_empresa > 0 else 0
                        st.info(f"""
                        📊 **Impacto de las provisiones**: {impacto_porcentual:.1f}% del Enterprise Value
                        
                        En un proceso de M&A real, estas provisiones se negocian como ajustes al precio.
                        """)
                
                with col_bridge2:
                    # Gráfico de impacto
                    if valor_empresa > 0:
                        fig_bridge = go.Figure()
                        
                        valores = [valor_empresa, -deuda_neta, -total_provisiones, equity_ajustado]
                        textos = ['EV', 'Deuda Neta', 'Provisiones', 'Equity Final']
                        colores = ['blue', 'red', 'orange', 'green']
                        
                        fig_bridge.add_trace(go.Waterfall(
                            x=textos,
                            y=valores,
                            text=[f"{get_simbolo_moneda()}{abs(v):,.0f}" for v in valores],
                            textposition="outside",
                            connector={"line": {"color": "rgb(63, 63, 63)"}},
                            decreasing={"marker": {"color": "red"}},
                            increasing={"marker": {"color": "green"}},
                            totals={"marker": {"color": "blue"}}
                        ))
                        
                        fig_bridge.update_layout(
                            title="Bridge to Equity",
                            height=400,
                            showlegend=False
                        )
                        
                        st.plotly_chart(fig_bridge, use_container_width=True)

        # Realizar valoración
        with st.spinner("Calculando valoración con metodología de banca de inversión..."):
            try:
                # Verificar si tenemos modelo o datos guardados
                if 'modelo' in locals() and hasattr(modelo, 'realizar_valoracion_bancainversion'):
                    valoracion = modelo.realizar_valoracion_bancainversion()
                elif 'datos_guardados' in st.session_state and st.session_state.datos_guardados:
                    if st.session_state.datos_guardados.get('valoracion_profesional'):
                        valoracion = st.session_state.datos_guardados['valoracion_profesional']
                    else:
                        # Crear valoración simple desde datos guardados
                        valoracion = {
                            'valoracion_final': 0,
                            'rango_valoracion': {'minimo': 0, 'central': 0, 'maximo': 0},
                            'descuento_iliquidez': 20,
                            'error': 'Valoración no disponible. Genere una nueva proyección.'
                        }
                else:
                    valoracion = {
                        'valoracion_final': 0,
                        'rango_valoracion': {'minimo': 0, 'central': 0, 'maximo': 0},
                        'descuento_iliquidez': 20,
                        'error': 'No hay datos disponibles. Genere una proyección primero.'
                    }
                
                # ESTOS PRINTS DEBEN ESTAR AL MISMO NIVEL QUE EL IF-ELIF-ELSE
                print(f"\n=== ESTRUCTURA VALORACIÓN ===")
                print(f"Claves principales: {list(valoracion.keys())}")
                print(f"Valoración final: {valoracion.get('valoracion_final', 'NO EXISTE')}")
                
                if 'error' not in valoracion:
                    # Métricas principales
                    col1, col2, col3, col4 = st.columns(4)
                    
                    valor_final = valoracion['valoracion_final']
                    rango = valoracion['rango_valoracion']
                    
                    with col1:
                        st.metric(
                            "Valoración Central",
                            f"{get_simbolo_moneda()}{valor_final/1_000_000:.1f}M",
                            help="Valoración ponderada post-descuento iliquidez"
                        )
                    with col2:
                        st.metric(
                            "Rango Mínimo",
                            f"{get_simbolo_moneda()}{rango['minimo']/1_000_000:.1f}M"
                        )
                    with col3:
                        st.metric(
                            "Rango Máximo", 
                            f"{get_simbolo_moneda()}{rango['maximo']/1_000_000:.1f}M"
                        )
                    with col4:
                        st.metric(
                            "Descuento Iliquidez",
                            f"{valoracion['descuento_iliquidez']:.0f}%"
                        )
                    
                    # Tabs para diferentes análisis
                    val_tab1, val_tab2, val_tab3, val_tab4 = st.tabs(
                        ["📊 Football Field", "🔬 DCF Detalle", "📈 Múltiplos", "🎯 Sensibilidad"]
                    )
                    
                    with val_tab1:
                        st.subheader("Gráfico Football Field")
                        # Crear gráfico de rangos de valoración
                        ff_data = valoracion['football_field']
                        
                        fig_ff = go.Figure()
                        
                        # Añadir rangos
                        for i, metodo in enumerate(ff_data['metodos']):
                            fig_ff.add_trace(go.Scatter(
                                x=[ff_data['valores_min'][i], ff_data['valores_max'][i]],
                                y=[metodo, metodo],
                                mode='lines',
                                line=dict(color='lightblue', width=20),
                                showlegend=False
                            ))
                            
                            # Valor central
                            fig_ff.add_trace(go.Scatter(
                                x=[ff_data['valores_central'][i]],
                                y=[metodo],
                                mode='markers',
                                marker=dict(size=15, color='darkblue'),
                                showlegend=False
                            ))
                        
                        # ESTA LÍNEA ESTABA MAL INDENTADA - DEBE ESTAR DENTRO DE val_tab1
                        # Línea de valor final
                        fig_ff.add_hline(
                            y=0.5, 
                            line_dash="dash", 
                            line_color="red",
                            annotation_text=f"Valor Final: {get_simbolo_moneda()}{ff_data['valor_final']/1_000_000:.1f}M"
                        )
                        
                        fig_ff.update_layout(
                            title="Rangos de Valoración por Metodología",
                            xaxis_title=f"Valor ({get_simbolo_moneda()}M)",
                            height=400
                        )
                        
                        st.plotly_chart(fig_ff, use_container_width=True)
                    
                    with val_tab2:
                        st.subheader("Análisis DCF Detallado")
                        with st.expander("💡 **¿Qué es el análisis DCF y cómo interpretarlo?**"):
                            st.markdown("""
                            ### 📈 Análisis DCF (Discounted Cash Flow) - Guía para No Financieros
                            
                            **🎯 ¿Qué es el DCF?**
                            El DCF es como calcular cuánto vale un árbol frutal:
                            - No por la fruta de hoy, sino por TODA la fruta futura
                            - Considerando que fruta en 5 años vale menos que fruta hoy
                            - Es el método más usado por inversores profesionales
                            
                            **📊 Los 3 Componentes Clave:**
                            
                            **1️⃣ Flujos de Caja Libres (FCF)**
                            - El dinero real que genera el negocio cada año
                            - Después de pagar todo: empleados, proveedores, impuestos, inversiones
                            - Es lo que queda para repartir o reinvertir
                            
                            **2️⃣ Tasa de Descuento (WACC)**
                            - Representa el "coste de oportunidad" + riesgo
                            - Típicamente 8-12% para empresas estables
                            - Mayor riesgo = Mayor WACC = Menor valoración
                            - Piénsalo como: "¿Qué rentabilidad mínima exijo por mi dinero?"
                            
                            **3️⃣ Valor Terminal**
                            - El valor de la empresa del año 6 en adelante
                            - Asume crecimiento estable a perpetuidad
                            - Suele representar 60-80% del valor total
                            
                            **🔍 Cómo Interpretar los Resultados:**
                            
                            **Valor Presente de FCF (5 años)**: 
                            - Si es 40% del total → Empresa madura, predecible ✅
                            - Si es 20% del total → Empresa en crecimiento, más arriesgada ⚠️
                            
                            **Enterprise Value (EV)**:
                            - Valor total del negocio operativo
                            - Sin considerar deuda o efectivo
                            
                            **Equity Value**:
                            - EV - Deuda Neta = Lo que vale para los accionistas
                            - Es el precio justo si compras el 100%
                            
                            **💡 Señales a Observar:**
                            - WACC > 15% → Negocio muy arriesgado
                            - Valor Terminal > 80% → Demasiada incertidumbre futura
                            - FCF negativos primeros años → Normal en startups
                            
                            **📌 Ejemplo Práctico:**
                            Si el DCF dice que tu empresa vale €10M:
                            - Con deuda de €2M → Equity vale €8M
                            - Si tienes 40% → Tu parte vale €3.2M
                            """)
                        dcf = valoracion['dcf_detalle']
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.markdown("**Componentes del WACC:**")
                            wacc_comp = dcf['componentes_wacc']
                            
                            st.write(f"- Ke (Costo del Equity): {wacc_comp['ke']:.1f}%")
                            st.write(f"- Kd (Costo de la Deuda): {wacc_comp['kd_neto']:.1f}%")
                            st.write(f"- Beta Ajustado: {wacc_comp['beta_ajustado']:.2f}")
                            st.write(f"- Prima por Tamaño: {wacc_comp['prima_tamaño']:.1f}%")
                            st.write(f"- Estructura (D/E): {wacc_comp['wd']:.0f}%/{wacc_comp['we']:.0f}%")
                        
                        with col2:
                            st.markdown("**Componentes del Valor:**")
                            st.write(f"- VP Flujos Explícitos: {get_simbolo_moneda()}{dcf['vp_flujos_explicitos']/1_000_000:.1f}M")
                            st.write(f"- VP Valor Terminal: {get_simbolo_moneda()}{dcf['vp_valor_terminal']/1_000_000:.1f}M")
                            st.write(f"- Valor Terminal %: {dcf['peso_valor_terminal']:.0f}%")
                            st.write(f"- Tasa Crecimiento Terminal: {dcf['g_terminal']:.1f}%")
                    
                    with val_tab3:
                        st.subheader("Valoración por Múltiplos")
                        with st.expander("💡 **¿Qué son los múltiplos de valoración y cómo usarlos?**"):
                            st.markdown("""
                            ### 🔢 Valoración por Múltiplos - Guía para No Financieros
                            
                            **🎯 ¿Qué son los Múltiplos?**
                            Es como tasar una casa comparándola con las del barrio:
                            - Si las casas similares se venden a 3,000€/m²
                            - Y tu casa tiene 100m² → Vale ~300,000€
                            - En empresas usamos ventas o EBITDA en vez de m²
                            
                            **📊 Los Múltiplos Más Importantes:**
                            
                            **1️⃣ EV/EBITDA (El más usado en M&A)**
                            - Valor Empresa ÷ EBITDA
                            - Ejemplo: EV/EBITDA = 8x significa que la empresa vale 8 veces su beneficio operativo anual
                            - **Interpretación por rangos**:
                              - 4-6x → Empresas maduras, bajo crecimiento
                              - 6-10x → Crecimiento moderado, estable
                              - 10-15x → Alto crecimiento o sector premium
                              - >15x → Startups o sectores muy valorados
                            
                            **2️⃣ EV/Ventas (Para empresas en crecimiento)**
                            - Útil cuando no hay beneficios aún
                            - Típico en tecnología o empresas nuevas
                            - **Benchmark por sector**:
                              - Software: 3-10x
                              - Servicios: 0.5-2x
                              - Retail: 0.3-1x
                              - Industrial: 0.5-1.5x
                            
                            **3️⃣ P/E (Price/Earnings)**
                            - Precio ÷ Beneficio por acción
                            - Más usado en bolsa que en M&A privado
                            - 15-20x es típico en empresas estables
                            
                            **🔍 Cómo Interpretar los Resultados:**
                            
                            **Si tu múltiplo > Media del sector**:
                            - Posibles razones positivas:
                              ✅ Mejor margen que competidores
                              ✅ Mayor crecimiento
                              ✅ Mejor posición competitiva
                            - O podría estar sobrevalorada ⚠️
                            
                            **Si tu múltiplo < Media del sector**:
                            - Posibles razones:
                              ⚠️ Menores márgenes
                              ⚠️ Más riesgo percibido
                              ⚠️ Menor crecimiento
                            - O podría ser una oportunidad 💡
                            
                            **💡 Ajustes Típicos a los Múltiplos:**
                            - **Descuento por tamaño**: -20-30% si <€10M ventas
                            - **Descuento por iliquidez**: -20-30% empresa privada
                            - **Premio por control**: +20-30% si compras mayoría
                            
                            **📌 Ejemplo Práctico:**
                            - Tu empresa: EBITDA €1M
                            - Múltiplo sector: 7x
                            - Valor base: €7M
                            - Descuento tamaño -20%: €5.6M
                            - Este es tu Enterprise Value estimado
                            
                            **⚠️ Limitaciones:**
                            - Los múltiplos son una foto, no una película
                            - No capturan el potencial futuro como el DCF
                            - Muy sensibles a la calidad de los comparables
                            """)
                        # Mostrar múltiplos
                        multiples = valoracion['multiples_detalle']
                        
                        mult_df = pd.DataFrame({
                            'Método': list(multiples.keys()),
                            'Múltiplo': [m['multiplo'] for m in multiples.values()],
                            f'Valor Empresa ({get_simbolo_moneda()}M)': [m['valor_empresa']/1_000_000 for m in multiples.values()],
                            f'Valor Equity ({get_simbolo_moneda()}M)': [m['valor_equity']/1_000_000 for m in multiples.values()]
                        })
                        
                        st.dataframe(mult_df.round(1), hide_index=True)
                        
                        # Gráfico de comparación
                        fig_mult = go.Figure(data=[
                            go.Bar(
                                x=mult_df['Método'],
                                y=mult_df[f'Valor Equity ({get_simbolo_moneda()}M)'],
                                text=mult_df[f'Valor Equity ({get_simbolo_moneda()}M)'].round(1),
                                textposition='auto',
                            )
                        ])
                        
                        fig_mult.update_layout(
                            title="Valoración por Diferentes Múltiplos",
                            yaxis_title=f"Valor Equity ({get_simbolo_moneda()}M)",
                            showlegend=False
                        )
                        
                        st.plotly_chart(fig_mult, use_container_width=True)
                    
                    with val_tab4:
                        st.subheader("Análisis de Sensibilidad")
                        with st.expander("💡 **¿Qué es el análisis de sensibilidad y por qué es crucial?**"):
                            st.markdown("""
                            ### 🎯 Análisis de Sensibilidad - Guía para No Financieros
                            
                            **🎲 ¿Qué es el Análisis de Sensibilidad?**
                            Es como un "¿Y si...?" para tu valoración:
                            - ¿Y si las ventas crecen 5% menos?
                            - ¿Y si los tipos de interés suben?
                            - ¿Y si los márgenes bajan 2 puntos?
                            - Muestra cómo cambia el valor con diferentes escenarios
                            
                            **📊 Las Variables Clave que se Analizan:**
                            
                            **1️⃣ WACC (Tasa de Descuento)**
                            - **Qué representa**: El coste del dinero + riesgo
                            - **Si sube**: La valoración BAJA (futuro vale menos)
                            - **Si baja**: La valoración SUBE
                            - **Rango típico**: 8% (muy seguro) a 15% (arriesgado)
                            
                            **2️⃣ Tasa de Crecimiento Terminal (g)**
                            - **Qué es**: A qué ritmo crecerá la empresa "para siempre"
                            - **Rango prudente**: 2-3% (inflación)
                            - **Impacto**: Pequeños cambios = grandes diferencias en valor
                            
                            **3️⃣ Márgenes EBITDA**
                            - **Qué mide**: Rentabilidad operativa
                            - **Variación típica**: ±2-5 puntos porcentuales
                            - **Impacto directo** en flujos de caja
                            
                            **🔍 Cómo Leer la Tabla de Sensibilidad:**
                            
                            La tabla muestra una matriz donde:
                            - **Filas**: Diferentes valores de WACC
                            - **Columnas**: Diferentes tasas de crecimiento (g)
                            - **Celdas**: Valor resultante de tu empresa
                            
                            **Ejemplo de interpretación**:
                            ```
                            WACC↓ / g→   2%     2.5%    3%
                            9%           8.5M    9.2M    10.1M
                            10%          7.8M    8.4M    9.1M  ← Caso base
                            11%          7.2M    7.7M    8.3M
                            ```
                            
                            **💡 Qué Buscar:**
                            
                            **Valoración Robusta** ✅:
                            - Poca variación entre escenarios
                            - La mayoría de casos dan valores similares
                            - Tu caso base está en el centro
                            
                            **Valoración Frágil** ⚠️:
                            - Enormes diferencias entre escenarios
                            - Valor se duplica o divide por 2 fácilmente
                            - Muy sensible a pequeños cambios
                            
                            **📌 Reglas Prácticas:**
                            
                            1. **Si el rango es estrecho** (ej: €8-10M):
                               - Valoración confiable
                               - Menor riesgo para inversores
                            
                            2. **Si el rango es amplio** (ej: €5-15M):
                               - Mayor incertidumbre
                               - Necesitas más análisis
                               - Considera el escenario conservador
                            
                            3. **Zona de confort**:
                               - WACC entre 9-12%
                               - g entre 2-3%
                               - Si necesitas valores extremos para justificar el precio, cuidado 🚨
                            
                            **⚡ Consejo Pro:**
                            Los inversores profesionales siempre miran el caso pesimista.
                            Si tu empresa sigue siendo atractiva en el peor escenario, 
                            es una inversión sólida.
                            """)
                        # Mostrar tabla de sensibilidad
                        if 'sensibilidad' in dcf:
                            st.markdown(f"**Sensibilidad del Valor del Equity ({get_simbolo_moneda()}M) a WACC y g:**")
                            
                            # Convertir a DataFrame si no lo es
                            sens_df = dcf['sensibilidad']
                            if isinstance(sens_df, pd.DataFrame):
                                st.dataframe(sens_df.style.highlight_max(axis=None))
                            else:
                                st.write("Datos de sensibilidad no disponibles")
                    
                    # Conclusiones
                    st.markdown("---")
                    st.subheader("📋 Conclusiones Ejecutivas")
                    
                    for conclusion in valoracion['conclusiones']:
                        st.write(f"• {conclusion}")
                    
                else:
                    st.error(f"Error en la valoración: {valoracion.get('error', 'Error desconocido')}")
                    
            except Exception as e:
                st.error(f"Error al calcular la valoración: {str(e)}")
                st.info("Asegúrese de haber generado las proyecciones financieras primero")
    with tab7:
        st.header("📄 Documentos Ejecutivos")
        
        if 'datos_guardados' in st.session_state:
            col1, col2, col3 = st.columns([1, 3, 1])
            
            with col2:
                st.markdown("### 📑 Business Plan Ejecutivo")
                st.markdown("""
                Genera un documento profesional PDF con toda la información de tu proyecto:
                - Executive Summary
                - Análisis Financiero Completo
                - Proyecciones a 5 años
                - Análisis DAFO
                - Valoración y Recomendaciones
                """)
                
                if 'pdf_generado' not in st.session_state:
                    st.session_state.pdf_generado = False
                
                if st.button("📥 Generar PDF Ejecutivo", type="primary", use_container_width=True):
                    st.session_state.pdf_generado = True
                
                if st.session_state.pdf_generado:
                    try:
                        with st.spinner('Preparando documentación ejecutiva...'):
                            datos_guardados = st.session_state.datos_guardados
                            
                            # Asegurar que valoracion_pdf existe
                            if 'valoracion_profesional' in datos_guardados and datos_guardados['valoracion_profesional']:
                                val_prof = datos_guardados['valoracion_profesional']
                                valoracion_pdf = {
                                    'valor_empresa': val_prof.get('valoracion_final', 0),
                                    'valor_equity': val_prof.get('valoracion_final', 0) - val_prof.get('deuda_neta', 0),
                                    'ev_ebitda_salida': val_prof.get('multiples_detalle', {}).get('ev_ebitda_final', {}).get('multiplo', 7.0),
                                    'ev_ebitda_ltm': datos_guardados.get('analisis_ia', {}).get('multiplo_ebitda_ltm', 10.3),
                                    'ev_ebitda_ntm': datos_guardados.get('analisis_ia', {}).get('multiplo_ebitda_ntm', 8.3),
                                    'tir_esperada': val_prof.get('dcf_detalle', {}).get('tir', 15.0),
                                    'wacc_utilizado': val_prof.get('dcf_detalle', {}).get('wacc', 10.0),
                                    'deuda_neta': val_prof.get('deuda_neta', 0)
                                }  
                            else:
                                # Si no hay valoracion profesional, usar valoracion estándar
                                valoracion_pdf = datos_guardados.get('valoracion', {})
                 
                            # Generar PDF
                            pdf_bytes = generar_pdf_profesional(
                                datos_empresa=datos_guardados['datos_empresa'],
                                pyl_df=datos_guardados['pyl'],
                                valoracion=valoracion_pdf,
                                analisis_ia=datos_guardados.get('analisis_ia', {}),
                            )
                            
                            # Botón de descarga
                            st.download_button(
                                label="📄 Descargar Business Plan (PDF)",
                                data=pdf_bytes,
                                file_name=f"BusinessPlan_{datos_guardados['datos_empresa']['nombre'].replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.pdf",
                                mime="application/pdf",
                                type="secondary",
                                use_container_width=True,
                                key="download_pdf_button"
                            )
                            
                            st.success("✅ PDF generado exitosamente!")
                            
                            # Reset para permitir generar otro
                            if st.button("🔄 Generar nuevo PDF", type="secondary"):
                                st.session_state.pdf_generado = False
                                st.rerun()
                            
                    except Exception as e:
                        st.error(f"Error al generar PDF: {str(e)}")
                        st.info("Por favor, verifica que has generado las proyecciones primero.")
                        st.session_state.pdf_generado = False
        else:
            st.info("👆 Genera primero las proyecciones financieras para poder crear el documento PDF")

   # Tab 7: Glosario
    with tab8:
        st.header("📚 Glosario de Términos Financieros")
        
        # Diccionario de términos completo
        glosario = {
            "Métricas Financieras": {
                "EBITDA": "Earnings Before Interest, Taxes, Depreciation and Amortization. Beneficio antes de intereses, impuestos, depreciación y amortización. Fórmula: EBITDA = Ingresos - Costos - Gastos Operativos",
                "P&L": "Profit & Loss. Cuenta de pérdidas y ganancias. Estado financiero que muestra ingresos, gastos y beneficios.",
                "FCF": "Free Cash Flow. Flujo de caja libre. Efectivo disponible después de inversiones. Fórmula: FCF = EBITDA - Impuestos - CapEx - Δ Capital Trabajo",
                "CapEx": "Capital Expenditure. Inversiones en activos fijos como maquinaria, equipos o instalaciones.",
                "EBIT": "Earnings Before Interest and Taxes. Beneficio antes de intereses e impuestos.",
                "Gross Margin": "Margen bruto. Rentabilidad después de costos directos. Fórmula: (Ventas - Costos) / Ventas × 100",
                "OPEX": "Operating Expenses. Gastos operativos del negocio excluyendo costos de producción.",
                "COGS": "Cost of Goods Sold. Costo de los bienes vendidos. Incluye materiales y mano de obra directa.",
                "SG&A": "Selling, General & Administrative. Gastos de ventas, generales y administrativos.",
                "D&A": "Depreciation & Amortization. Depreciación de activos tangibles y amortización de intangibles.",
                "Net Income": "Beneficio Neto. Ganancia final después de todos los gastos e impuestos.",
                "Gross Profit": "Beneficio Bruto. Ventas menos costo de ventas."
            },
            "Balance": {
                "Working Capital": "Capital de trabajo. Recursos necesarios para la operación diaria. Fórmula: Activo Corriente - Pasivo Corriente",
                "Current Assets": "Activo Corriente. Activos líquidos o convertibles en efectivo en menos de un año.",
                "Current Liabilities": "Pasivo Corriente. Obligaciones a pagar en menos de un año.",
                "Equity": "Patrimonio Neto. Valor de la empresa para los accionistas.",
                "PP&E": "Property, Plant & Equipment. Propiedad, planta y equipo. Activos fijos tangibles.",
                "A/R": "Accounts Receivable. Cuentas por cobrar. Dinero que deben los clientes.",
                "A/P": "Accounts Payable. Cuentas por pagar. Dinero que se debe a proveedores.",
                "WIP": "Work in Progress. Trabajo en proceso. Inventario parcialmente completado.",
                "Goodwill": "Fondo de Comercio. Valor intangible de marca, reputación y relaciones con clientes.",
                "Inventory": "Inventario. Existencias de productos terminados, materias primas y productos en proceso."
            },
            "Valoración": {
                "DCF": "Discounted Cash Flow. Flujo de caja descontado. Método de valoración basado en proyecciones futuras.",
                "WACC": "Weighted Average Cost of Capital. Costo promedio ponderado del capital. Tasa de descuento para valoración.",
                "EV": "Enterprise Value. Valor de la empresa. Precio total de adquisición. Fórmula: Market Cap + Deuda - Efectivo",
                "Terminal Value": "Valor Terminal. Valor de la empresa al final del período de proyección.",
                "NPV": "Net Present Value. Valor Actual Neto. Valor presente de flujos futuros menos inversión inicial.",
                "IRR": "Internal Rate of Return. Tasa Interna de Retorno. Tasa que hace el VAN igual a cero.",
                "Payback": "Período de Recuperación. Tiempo necesario para recuperar la inversión inicial.",
                "Multiple": "Múltiplo de Valoración. Ratio para comparar empresas (ej: EV/EBITDA, P/E).",
                "Beta": "Coeficiente Beta. Medida del riesgo sistemático de una acción respecto al mercado.",
                "LTM": "Last Twelve Months. Últimos doce meses. Período de referencia para métricas históricas. Se usa en múltiplos de valoración como EV/EBITDA LTM.",
                "NTM": "Next Twelve Months. Próximos doce meses. Período de referencia para métricas proyectadas. Se usa en múltiplos forward como EV/EBITDA NTM.",
                "TTM": "Trailing Twelve Months. Sinónimo de LTM. Últimos 12 meses de datos históricos.",
            },
            "Ratios": {
                "ROE": "Return on Equity. Rentabilidad sobre el patrimonio. Fórmula: Beneficio Neto / Patrimonio × 100",
                "ROCE": "Return on Capital Employed. Rentabilidad sobre capital empleado. Mide la eficiencia en el uso del capital operativo. Fórmula: EBIT / (Activos Totales - Pasivo Corriente) × 100",
                "ROA": "Return on Assets. Rentabilidad sobre activos. Fórmula: Beneficio Neto / Activos × 100",
                "Liquidity Ratio": "Ratio de liquidez. Capacidad de pagar obligaciones a corto plazo. Fórmula: Activo Corriente / Pasivo Corriente",
                "Debt-to-Equity": "Ratio deuda/patrimonio. Nivel de apalancamiento. Fórmula: Deuda Total / Patrimonio Neto",
                "Quick Ratio": "Prueba Ácida. Liquidez excluyendo inventarios. Fórmula: (Activo Corriente - Inventario) / Pasivo Corriente",
                "Current Ratio": "Ratio Corriente. Similar al ratio de liquidez. Activo Corriente / Pasivo Corriente",
                "DSO": "Days Sales Outstanding. Días de cobro. Tiempo promedio para cobrar ventas.",
                "DPO": "Days Payable Outstanding. Días de pago. Tiempo promedio para pagar a proveedores.",
                "Asset Turnover": "Rotación de Activos. Eficiencia en el uso de activos. Fórmula: Ventas / Activos Totales",
                "Interest Coverage": "Cobertura de Intereses. Capacidad de pagar intereses. Fórmula: EBIT / Gastos por Intereses"
            }
        }
            
        # Mostrar por categorías con expanders
        for categoria, terminos in glosario.items():
            terminos_filtrados = terminos
            
            with st.expander(f"📂 {categoria} ({len(terminos_filtrados)} términos)", expanded=True):
                # Crear dos columnas para los términos
                cols = st.columns(2)
                for idx, (termino, definicion) in enumerate(terminos_filtrados.items()):
                    with cols[idx % 2]:
                        st.markdown(f"**{termino}**")
                        st.caption(definicion)
                        st.markdown("")
        
        # Estadísticas y nota al pie
        total_terminos = sum(len(terminos) for terminos in glosario.values())
        
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total de términos", total_terminos)
        with col2:
            st.metric("Categorías", len(glosario))
        with col3:
            st.metric("Más usado", "EBITDA")
            
        st.info("""
        💡 **Tips de uso:**
        - Usa la barra de búsqueda para encontrar términos rápidamente
        - Los términos están agrupados por categorías
        - Consulta este glosario cuando encuentres una abreviación desconocida
        - Las fórmulas muestran cómo se calculan las métricas
        """)

    with tab2:
        st.header("📊 Cuenta de Resultados Proyectada (P&L)")
        
        if pyl is not None and not pyl.empty:
            # Métricas resumen
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                crecimiento_ventas = ((pyl['Ventas'].iloc[-1] / pyl['Ventas'].iloc[0]) ** (1/5) - 1) * 100
                st.metric("CAGR Ventas", f"{crecimiento_ventas:.1f}%")
            
            with col2:
                margen_ebitda_promedio = pyl['EBITDA %'].mean()
                st.metric("Margen EBITDA Promedio", f"{margen_ebitda_promedio:.1f}%")
            
            with col3:
                margen_neto_promedio = pyl['Beneficio Neto %'].mean()
                st.metric("Margen Neto Promedio", f"{margen_neto_promedio:.1f}%")
            
            with col4:
                beneficio_acumulado = pyl['Beneficio Neto'].sum()
                st.metric("Beneficio Acumulado", f"{get_simbolo_moneda()}{beneficio_acumulado:,.0f}")
            
            # Mostrar tabla
            st.markdown("---")
            pyl_display = pyl.copy()
            for col in pyl_display.columns:
                if col != 'Año' and '%' not in col:
                    pyl_display[col] = pyl_display[col].apply(lambda x: f"{get_simbolo_moneda()}{x:,.0f}".replace(",", "."))
                elif '%' in col:
                    pyl_display[col] = pyl_display[col].apply(lambda x: f"{x:.1f}%")
    
            
            st.dataframe(pyl_display, use_container_width=True, hide_index=True)
            
            # Botón de descarga
            csv = pyl.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Descargar P&L en CSV",
                data=csv,
                file_name=f"pyl_{nombre_empresa}_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
        else:
            st.error("No hay datos de P&L disponibles")

    with tab3:
        st.header("🗂️ Balance Proyectado")
    
        if balance is not None and not balance.empty:
            # Métricas principales en la parte superior
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                patrimonio_inicial = balance['patrimonio_neto'].iloc[0]
                patrimonio_final = balance['patrimonio_neto'].iloc[-1]
                crecimiento = ((patrimonio_final / patrimonio_inicial) - 1) * 100
                st.metric("Patrimonio Final", f"€{patrimonio_final/1000:.0f}k", f"+{crecimiento:.1f}%")
            
            with col2:
                deuda_total_final = balance['deuda_cp'].iloc[-1] + balance['deuda_lp'].iloc[-1]
                st.metric("Deuda Total Final", f"€{deuda_total_final/1000:.0f}k")
            
            with col3:
                ratio_deuda_pat = deuda_total_final / patrimonio_final if patrimonio_final > 0 else 0
                st.metric("Deuda/Patrimonio", f"{ratio_deuda_pat:.2f}x")
            
            with col4:
                total_activos_final = balance['total_activo'].iloc[-1]
                st.metric("Total Activos", f"€{total_activos_final/1000:.0f}k")
            
            # Tabla principal
            st.subheader("📊 Evolución del Balance")

            # Preparar datos con formato
            balance_tabla = pd.DataFrame({
                'Año': balance['año'],
                'Tesorería': balance['tesoreria'].apply(lambda x: f"€{x:,.0f}"),
                'Clientes': balance['clientes'].apply(lambda x: f"€{x:,.0f}"),
                'Inventario': balance['inventario'].apply(lambda x: f"€{x:,.0f}"),
                'Activo Fijo': balance['activo_fijo_neto'].apply(lambda x: f"€{x:,.0f}"),
                'TOTAL ACTIVO': balance['total_activo'].apply(lambda x: f"€{x:,.0f}"),
                'Proveedores': balance['proveedores'].apply(lambda x: f"€{x:,.0f}"),
                'Deuda CP': balance['deuda_cp'].apply(lambda x: f"€{x:,.0f}"),
                'Deuda LP': balance['deuda_lp'].apply(lambda x: f"€{x:,.0f}"),
                'Patrimonio': balance['patrimonio_neto'].apply(lambda x: f"€{x:,.0f}")
            })
            
            st.dataframe(balance_tabla, use_container_width=True, hide_index=True)
            
            # Gráfico de evolución
            with st.expander("📈 Ver Gráfico de Evolución"):
                fig_data = pd.DataFrame({
                    'Año': balance['año'],
                    'Total Activos': balance['total_activo']/1000,
                    'Patrimonio Neto': balance['patrimonio_neto']/1000,
                    'Deuda Total': (balance['deuda_cp'] + balance['deuda_lp'])/1000
                })
                st.line_chart(fig_data.set_index('Año'))
        else:
            st.warning("No hay datos de balance proyectado disponibles")
    
    with tab4:
        st.header("📈 Analytics")
        
        if pyl is not None and not pyl.empty:
            # Gráfico de Ventas y EBITDA
            st.subheader("📊 Evolución de Ventas y EBITDA")
            
            fig1 = go.Figure()
            fig1.add_trace(go.Bar(
                x=pyl['Año'],
                y=pyl['Ventas'],
                name='Ventas',
                marker_color='lightblue'
            ))
            fig1.add_trace(go.Bar(
                x=pyl['Año'],
                y=pyl['EBITDA'],
                name='EBITDA',
                marker_color='darkblue'
            ))
            fig1.update_layout(
                barmode='group',
                title='Evolución de Ventas y EBITDA',
                xaxis_title='Año',
                yaxis_title='Importe (€)',
                hovermode='x unified',
                height=400
            )
            st.plotly_chart(fig1, use_container_width=True)
            
            # Gráfico de Márgenes
            st.subheader("📈 Evolución de Márgenes")
            
            fig2 = go.Figure()
            fig2.add_trace(go.Scatter(
                x=pyl['Año'],
                y=pyl['Margen Bruto %'],
                mode='lines+markers',
                name='Margen Bruto %',
                line=dict(color='green')
            ))
            fig2.add_trace(go.Scatter(
                x=pyl['Año'],
                y=pyl['EBITDA %'],
                mode='lines+markers',
                name='Margen EBITDA %',
                line=dict(color='blue')
            ))
            fig2.add_trace(go.Scatter(
                x=pyl['Año'],
                y=pyl['Beneficio Neto %'],
                mode='lines+markers',
                name='Margen Neto %',
                line=dict(color='red')
            ))
            fig2.update_layout(
                title='Evolución de Márgenes',
                xaxis_title='Año',
                yaxis_title='Porcentaje (%)',
                hovermode='x unified',
                height=400
            )
            st.plotly_chart(fig2, use_container_width=True)
            
            # Free Cash Flow si existe
            if cash_flow is not None and not cash_flow.empty:
                st.markdown("---")
                # AÑADIR EN LA SECCIÓN DE ANALYTICS, ANTES DE MOSTRAR LA TABLA DE FREE CASH FLOW:ç

                with st.expander("💰 ¿Qué es el Free Cash Flow y por qué es crucial para su empresa?"):
                    st.markdown("""
                    ### Free Cash Flow: La Métrica Clave de Generación de Valor
                    
                    El **Free Cash Flow (FCF)** representa el efectivo real que genera su empresa después de cubrir todas las 
                    necesidades operativas y de inversión. Es el dinero disponible para remunerar a accionistas, reducir deuda 
                    o reinvertir en crecimiento.
                    
                    #### 📊 Metodología de Cálculo
                    
                    **Punto de partida: EBITDA**
                    - Beneficio operativo antes de intereses, impuestos, depreciación y amortización
                    - Refleja la capacidad operativa pura del negocio
                    
                    **Ajustes para llegar al efectivo real:**
                    
                    **1. (-) Impuestos sobre el beneficio operativo**
                    - Impacto fiscal sobre las operaciones (sin considerar el escudo fiscal de la deuda)
                    
                    **2. (-) CAPEX (Inversiones en activos)**
                    - **Con plan de inversiones definido**: Utilizamos sus proyecciones específicas
                    - **Sin plan definido**: Aplicamos benchmarks sectoriales basados en mejores prácticas:
                    
                    | Sector | CAPEX/Ventas | Justificación |
                    |--------|--------------|---------------|
                    | Industrial | 10% | Maquinaria pesada, instalaciones |
                    | Automoción | 8% | Equipamiento especializado |
                    | Hostelería | 6% | Renovaciones, equipamiento |
                    | Retail | 5% | Modernización puntos de venta |
                    | Servicios | 3.5% | Inversión moderada |
                    | Tecnología | 3% | Principalmente equipos IT |
                    | Ecommerce | 2.5% | Infraestructura digital |
                    | Consultoría | 2% | Inversión mínima |
                    
                    **3. (-) Variación del Capital de Trabajo**
                    - Inversión en el crecimiento: inventarios, crédito a clientes, financiación de proveedores
                    - Un crecimiento rápido requiere más capital de trabajo
                    
                    #### 💡 Interpretación para la Toma de Decisiones
                    
                    **FCF Positivo y Creciente**
                    - ✅ Negocio autosuficiente financieramente
                    - ✅ Capacidad para distribuir dividendos
                    - ✅ Posibilidad de reducir deuda
                    - ✅ Recursos para adquisiciones estratégicas
                    
                    **FCF Negativo**
                    - ⚠️ Requiere financiación externa
                    - ⚠️ Común en fases de alto crecimiento
                    - ⚠️ Debe ser temporal y planificado
                    
                    #### 🎯 Por Qué los Inversores se Fijan en el FCF
                    
                    1. **Valoración DCF**: El valor de su empresa es el valor presente de los FCF futuros
                    2. **Calidad de beneficios**: Distingue entre beneficios contables y generación real de caja
                    3. **Sostenibilidad**: Indica si el crecimiento es financieramente viable
                    4. **Flexibilidad estratégica**: Mayor FCF = más opciones estratégicas
                    
                    #### 📈 Benchmarks de Referencia
                    
                    - **FCF Yield** (FCF/Valor Empresa): >5% se considera atractivo
                    - **Conversión de EBITDA a FCF**: >40% indica eficiencia operativa
                    - **Crecimiento del FCF**: Debe superar el crecimiento del PIB + inflación
                    
                    *Esta metodología está alineada con los estándares utilizados por fondos de inversión y banca de inversión 
                    para evaluar la generación de valor empresarial.*
                    """)
                st.subheader("💰 Free Cash Flow Proyectado")
                
                fcf_display = cash_flow.copy()
                for col in fcf_display.columns:
                    if col != 'Año':
                        fcf_display[col] = fcf_display[col].apply(lambda x: f"{get_simbolo_moneda()}{x:,.0f}".replace(",", "."))
                
                st.dataframe(fcf_display, use_container_width=True, hide_index=True)
                
                # Métricas de FCF
                col1, col2, col3 = st.columns(3)
                with col1:
                    fcf_total = cash_flow['Free Cash Flow'].sum()
                    st.metric("FCF Acumulado", f"{get_simbolo_moneda()}{fcf_total:,.0f}")
                with col2:
                    fcf_promedio = cash_flow['Free Cash Flow'].mean()
                    st.metric("FCF Promedio", f"{get_simbolo_moneda()}{fcf_promedio:,.0f}")
                with col3:
                    fcf_año5 = cash_flow['Free Cash Flow'].iloc[-1]
                    st.metric("FCF Año 5", f"{get_simbolo_moneda()}{fcf_año5:,.0f}")
            
            # Financiación del Capital de Trabajo si existe
            if 'financiacion_df' in st.session_state.datos_guardados:
                financiacion_df = st.session_state.datos_guardados['financiacion_df']
                if financiacion_df is not None and not financiacion_df.empty:
                    st.markdown("---")
                    st.subheader("💳 Financiación del Capital de Trabajo")
                    
                    # Métricas
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        limite_total = financiacion_df['Límite Póliza'].iloc[-1]
                        st.metric("Límite de Crédito Año 5", f"{get_simbolo_moneda()}{limite_total:,.0f}")
                    with col2:
                        uso_promedio = financiacion_df['Uso Póliza'].mean()
                        st.metric("Uso Promedio", f"{get_simbolo_moneda()}{uso_promedio:,.0f}")
                    with col3:
                        coste_total = financiacion_df['Coste Póliza'].sum()
                        st.metric("Coste Total", f"{get_simbolo_moneda()}{coste_total:,.0f}")
                    
                    # Tabla
                    financiacion_display = financiacion_df.copy()
                    for col in financiacion_display.columns:
                        if col != 'Año':
                            financiacion_display[col] = financiacion_display[col].apply(
                                lambda x: f"{get_simbolo_moneda()}{x:,.0f}")
                    
                    st.dataframe(financiacion_display, use_container_width=True)
        else:
            st.error("No hay datos disponibles para análisis")

# Si hay datos guardados pero no se está generando nueva proyección, mostrarlos
if not generar_proyeccion and st.session_state.proyeccion_generada and st.session_state.datos_guardados:
    # Recuperar datos guardados
    datos = st.session_state.datos_guardados
    
    # Compatibilidad con la nueva estructura
    pyl = datos.get('pyl', datos.get('proyecciones', {}).get('pyl'))
    balance = datos.get('balance', datos.get('proyecciones', {}).get('balance'))
    cash_flow = datos.get('cash_flow', datos.get('proyecciones', {}).get('cash_flow'))
    ratios = datos.get('ratios', datos.get('proyecciones', {}).get('ratios'))
    valoracion = datos.get('valoracion', datos.get('proyecciones', {}).get('valoracion'))
    metricas = datos.get('metricas', {})
    analisis_ia = st.session_state.datos_guardados.get('analisis_ia', {})
    resumen = datos.get('resumen', {})
    nombre_empresa = datos.get('nombre_empresa', 'Empresa')
    
    # Para mantener compatibilidad con código antiguo
    if 'wc_df' in datos:
        wc_df = datos['wc_df']
        financiacion_df = datos['financiacion_df']
        fcf_df = datos['fcf_df']
    else:
        # Usar los nuevos DataFrames
        wc_df = None
        financiacion_df = None
        fcf_df = cash_flow

    # Mostrar los mismos resultados

    # Mostrar los mismos resultados
    st.success("✅ Mostrando proyección guardada")

    # Botón PDF simple al final de la generación
    st.markdown("---")
    # Botón PDF mejorado
    st.markdown("---")
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        # Usar un contenedor para evitar recargas
        pdf_container = st.container()
        with pdf_container:
            if st.button("📄 Generar PDF del Business Plan", type="primary", use_container_width=True, key="pdf_button"):
                with st.spinner("Generando PDF..."):
                    try:
                        # Preparar valoración para PDF
                        if 'valoracion_profesional' in st.session_state.datos_guardados and st.session_state.datos_guardados['valoracion_profesional']:
                            val_prof = st.session_state.datos_guardados['valoracion_profesional']
                            valoracion_pdf = {
                                'valor_empresa': val_prof.get('valoracion_final', 0),
                                'valor_equity': val_prof.get('valoracion_final', 0) - val_prof.get('deuda_neta', 0),
                                'ev_ebitda_salida': val_prof.get('multiples_detalle', {}).get('ev_ebitda_final', {}).get('multiplo', 7.0),
                                'ev_ebitda_ltm': st.session_state.datos_guardados.get('analisis_ia', {}).get('multiplo_ebitda_ltm', 10.3),
                                'ev_ebitda_ntm': st.session_state.datos_guardados.get('analisis_ia', {}).get('multiplo_ebitda_ntm', 8.3),
                                'tir_esperada': val_prof.get('dcf_detalle', {}).get('tir', 15.0),
                                'wacc_utilizado': val_prof.get('dcf_detalle', {}).get('wacc', 10.0),
                                'deuda_neta': val_prof.get('deuda_neta', 0)
                            }
                        else:
                            valoracion_pdf = st.session_state.datos_guardados.get('valoracion', {})
                            
                        # Añadir CAPEX desde el DataFrame de cash flow
                        if 'cash_flow' in st.session_state.datos_guardados:
                            cf_df = st.session_state.datos_guardados['cash_flow']
                            if 'Flujo Inversión' in cf_df.columns:
                                for i in range(min(5, len(cf_df))):
                                    capex = abs(cf_df['Flujo Inversión'].iloc[i])
                                    valoracion_pdf[f'capex_año{i+1}'] = capex
                        if 'plan_capex' in st.session_state.datos_guardados:
                            for i, capex_data in enumerate(st.session_state.datos_guardados['plan_capex']):
                                if i < 5:
                                    valoracion_pdf[f'capex_año{i+1}'] = capex_data.get('importe', 0)

                        pdf_bytes = generar_pdf_profesional(
                            datos_empresa=st.session_state.datos_guardados['datos_empresa'],
                            pyl_df=st.session_state.datos_guardados['pyl'],
                            balance_df=st.session_state.datos_guardados.get('balance'),
                            valoracion=valoracion_pdf,
                            analisis_ia=st.session_state.datos_guardados.get('analisis_ia', {})
                        )
                        
                        # Crear un nombre único para el archivo
                        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                        filename = f"BusinessPlan_{timestamp}.pdf"
                        
                        # Mostrar enlace de descarga directamente
                        st.success("✅ PDF generado exitosamente!")
                        st.download_button(
                            label="📥 Descargar PDF",
                            data=pdf_bytes,
                            file_name=filename,
                            mime="application/pdf",
                            key=f"download_{timestamp}"
                        )
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
else:
    # Pantalla de bienvenida cuando no hay proyección
    st.info("👈 Introduce los datos de tu empresa en la barra lateral y pulsa **Generar Proyección**")

# Footer
st.markdown("---")
st.markdown(
    """
    <div style="text-align: center; color: #64748B;">
    </div>
    """,
    unsafe_allow_html=True
)
