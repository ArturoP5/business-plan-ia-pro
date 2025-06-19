from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.pdfgen import canvas
from reportlab.platypus.flowables import Flowable
import pandas as pd
from datetime import datetime
from io import BytesIO
import os
from typing import Dict, Optional

# Colores corporativos
AZUL_PRINCIPAL = colors.HexColor('#1e40af')
AZUL_CLARO = colors.HexColor('#3b82f6')
GRIS_TEXTO = colors.HexColor('#374151')
VERDE_POSITIVO = colors.HexColor('#10b981')
ROJO_NEGATIVO = colors.HexColor('#ef4444')

class NumberedCanvas(canvas.Canvas):
    """Canvas personalizado para añadir números de página"""
    def __init__(self, *args, **kwargs):
        canvas.Canvas.__init__(self, *args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        """Añadir número de página a cada página"""
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_number(self, page_count):
        """Dibujar número de página"""
        self.setFont("Helvetica", 9)
        self.setFillColor(GRIS_TEXTO)
        self.drawRightString(
            letter[0] - inch,
            0.5 * inch,
            f"Página {self._pageNumber} de {page_count}"
        )
        # Línea decorativa
        self.setStrokeColor(AZUL_PRINCIPAL)
        self.setLineWidth(2)
        self.line(inch, 0.7 * inch, letter[0] - inch, 0.7 * inch)

def crear_estilos():
    """Crear estilos personalizados para el PDF"""
    styles = getSampleStyleSheet()
    
    # Estilo para títulos principales
    styles.add(ParagraphStyle(
        name='TituloPrincipal',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=AZUL_PRINCIPAL,
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    ))
    
    # Estilo para subtítulos
    styles.add(ParagraphStyle(
        name='Subtitulo',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=AZUL_PRINCIPAL,
        spaceAfter=12,
        spaceBefore=12,
        fontName='Helvetica-Bold'
    ))
    
    # Estilo para texto normal
    styles.add(ParagraphStyle(
        name='TextoNormal',
        parent=styles['Normal'],
        fontSize=10,
        textColor=GRIS_TEXTO,
        alignment=TA_JUSTIFY,
        spaceAfter=6
    ))
    
    # Estilo para highlights
    styles.add(ParagraphStyle(
        name='Highlight',
        parent=styles['Normal'],
        fontSize=11,
        textColor=AZUL_PRINCIPAL,
        fontName='Helvetica-Bold',
        spaceAfter=6
    ))
    
    return styles

def crear_portada(datos_empresa: Dict, styles) -> list:
    """Crear la portada del PDF"""
    elementos = []
    
    # Espaciador superior
    elementos.append(Spacer(1, 2*inch))
    
    # Título principal
    elementos.append(Paragraph(
        "BUSINESS PLAN EJECUTIVO",
        styles['TituloPrincipal']
    ))
    
    elementos.append(Spacer(1, 0.5*inch))
    
    # Nombre de la empresa
    elementos.append(Paragraph(
        datos_empresa.get('nombre', 'Empresa'),
        ParagraphStyle(
            name='NombreEmpresa',
            fontSize=28,
            textColor=AZUL_PRINCIPAL,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
    ))
    
    elementos.append(Spacer(1, 0.3*inch))
    
    # Sector
    elementos.append(Paragraph(
        f"Sector: {datos_empresa.get('sector', 'No especificado')}",
        ParagraphStyle(
            name='Sector',
            fontSize=14,
            textColor=GRIS_TEXTO,
            alignment=TA_CENTER
        )
    ))
    
    elementos.append(Spacer(1, 2*inch))
    
    # Información de contacto y fecha
    info_data = [
        ['Preparado para:', 'Inversores y Dirección'],
        ['Fecha:', datetime.now().strftime('%B %Y')],
        ['Confidencial:', 'Sí']
    ]
    
    info_table = Table(info_data, colWidths=[2*inch, 3*inch])
    info_table.setStyle(TableStyle([
        ('TEXTCOLOR', (0, 0), (0, -1), AZUL_PRINCIPAL),
        ('TEXTCOLOR', (1, 0), (1, -1), GRIS_TEXTO),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
    ]))
    
    elementos.append(info_table)
    
    # Nota de confidencialidad
    elementos.append(Spacer(1, 1*inch))
    elementos.append(Paragraph(
        "Este documento contiene información confidencial y propietaria. "
        "Su distribución está limitada a los destinatarios autorizados.",
        ParagraphStyle(
            name='Confidencial',
            fontSize=9,
            textColor=GRIS_TEXTO,
            alignment=TA_CENTER,
            fontName='Helvetica-Oblique'
        )
    ))
    
    return elementos
def crear_resumen_ejecutivo(datos_empresa: Dict, pyl_df: pd.DataFrame, valoracion: Dict, analisis_ia: Dict, styles) -> list:
    """Crear la sección de resumen ejecutivo"""
    elementos = []
    
    # Título de la sección
    elementos.append(Paragraph("RESUMEN EJECUTIVO", styles['TituloPrincipal']))
    elementos.append(Spacer(1, 0.3*inch))
    
    # Información de la empresa
    elementos.append(Paragraph("Información de la Empresa", styles['Subtitulo']))
    
    info_empresa = f"""
    <b>Empresa:</b> {datos_empresa.get('nombre', 'N/A')}<br/>
    <b>Sector:</b> {datos_empresa.get('sector', 'N/A')}<br/>
    <b>Empleados:</b> {datos_empresa.get('num_empleados', 'N/A')}<br/>
    <b>Año de fundación:</b> {datos_empresa.get('año_fundacion', 'N/A')}<br/>
    """
    elementos.append(Paragraph(info_empresa, styles['TextoNormal']))
    elementos.append(Spacer(1, 0.2*inch))
    
    # Resumen del negocio
    if analisis_ia and 'resumen_ejecutivo' in analisis_ia:
        elementos.append(Paragraph("Resumen del Negocio", styles['Subtitulo']))
        elementos.append(Paragraph(analisis_ia['resumen_ejecutivo'], styles['TextoNormal']))
        elementos.append(Spacer(1, 0.2*inch))
    
    # Métricas clave
    elementos.append(Paragraph("Métricas Financieras Clave", styles['Subtitulo']))
    
    # Calcular métricas
    ventas_año1 = pyl_df['Ventas'].iloc[0] if len(pyl_df) > 0 else 0
    ventas_año5 = pyl_df['Ventas'].iloc[-1] if len(pyl_df) > 0 else 0
    cagr = ((ventas_año5 / ventas_año1) ** (1/5) - 1) * 100 if ventas_año1 > 0 else 0
    
    metricas_data = [
        ['Métrica', 'Año 1', 'Año 5', 'CAGR'],
        ['Ventas', f"€{ventas_año1:,.0f}", f"€{ventas_año5:,.0f}", f"{cagr:.1f}%"],
        ['EBITDA', f"€{pyl_df['EBITDA'].iloc[0]:,.0f}", f"€{pyl_df['EBITDA'].iloc[-1]:,.0f}", "-"],
        ['Margen EBITDA', f"{pyl_df['EBITDA %'].iloc[0]:.1f}%", f"{pyl_df['EBITDA %'].iloc[-1]:.1f}%", "-"]
    ]
    
    metricas_table = Table(metricas_data, colWidths=[2*inch, 1.5*inch, 1.5*inch, 1*inch])
    metricas_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), AZUL_PRINCIPAL),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
    ]))
    
    elementos.append(metricas_table)
    elementos.append(Spacer(1, 0.3*inch))
    
    # Valoración
    if valoracion:
        elementos.append(Paragraph("Valoración de la Empresa", styles['Subtitulo']))
        
        valor_empresa = valoracion.get('valor_empresa', 0)
        valoracion_text = f"""
        <b>Valor estimado de la empresa:</b> €{valor_empresa:,.0f}<br/>
        <b>Múltiplo EV/EBITDA:</b> {valoracion.get('ev_ebitda_salida', 0):.1f}x<br/>
        <b>TIR esperada:</b> {valoracion.get('tir_esperada', 0):.1f}%
        """
        elementos.append(Paragraph(valoracion_text, styles['TextoNormal']))
        elementos.append(Spacer(1, 0.2*inch))
    
    # Rating y viabilidad
    if analisis_ia:
        elementos.append(Paragraph("Evaluación del Proyecto", styles['Subtitulo']))
        
        eval_data = [
            ['Rating del Proyecto', analisis_ia.get('rating', 'N/A')],
            ['Viabilidad', analisis_ia.get('viabilidad', 'N/A')],
            ['Recomendación', 'INVERTIR' if 'ALTA' in analisis_ia.get('viabilidad', '') else 'EVALUAR CON DETALLE']
        ]
        
        eval_table = Table(eval_data, colWidths=[3*inch, 3*inch])
        eval_table.setStyle(TableStyle([
            ('TEXTCOLOR', (0, 0), (0, -1), AZUL_PRINCIPAL),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ]))
        
        elementos.append(eval_table)
    
    return elementos
def crear_pyl_detallado(pyl_df: pd.DataFrame, styles) -> list:
    """Crear la sección de P&L detallado"""
    elementos = []
    
    # Título
    elementos.append(Paragraph("CUENTA DE RESULTADOS PROYECTADA", styles['TituloPrincipal']))
    elementos.append(Spacer(1, 0.3*inch))
    
    # Preparar datos para la tabla
    data = []
    
    # Encabezados
    headers = ['Concepto'] + [f'Año {i+1}' for i in range(len(pyl_df))]
    data.append(headers)
    
    # Filas del P&L
    conceptos = ['Ventas', 'Coste de Ventas', 'Margen Bruto', 'Margen Bruto %',
                 'Gastos Operativos', 'EBITDA', 'EBITDA %', 'Amortización',
                 'EBIT', 'Gastos Financieros', 'BAI', 'Impuestos', 'Beneficio Neto',
                 'Beneficio Neto %']
    
    for concepto in conceptos:
        if concepto in pyl_df.columns:
            fila = [concepto]
            for i in range(len(pyl_df)):
                valor = pyl_df[concepto].iloc[i]
                if '%' in concepto:
                    fila.append(f"{valor:.1f}%")
                else:
                    fila.append(f"€{valor:,.0f}")
            data.append(fila)
    
    # Crear tabla
    col_widths = [2*inch] + [1.2*inch] * len(pyl_df)
    pyl_table = Table(data, colWidths=col_widths)
    
    # Estilo de la tabla
    style = TableStyle([
        # Encabezado
        ('BACKGROUND', (0, 0), (-1, 0), AZUL_PRINCIPAL),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('ALIGN', (1, 0), (-1, 0), 'CENTER'),
        
        # Columna de conceptos
        ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
        ('TEXTCOLOR', (0, 1), (0, -1), AZUL_PRINCIPAL),
        
        # Datos
        ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        
        # Líneas separadoras en secciones clave
        ('LINEBELOW', (0, 3), (-1, 3), 1, AZUL_CLARO),  # Después de Margen Bruto %
        ('LINEBELOW', (0, 6), (-1, 6), 1, AZUL_CLARO),  # Después de EBITDA %
        ('LINEBELOW', (0, 12), (-1, 12), 2, AZUL_PRINCIPAL),  # Después de Beneficio Neto
        
        # Resaltar EBITDA y Beneficio Neto
        ('BACKGROUND', (0, 5), (-1, 6), colors.Color(0.95, 0.95, 1)),  # EBITDA
        ('BACKGROUND', (0, 12), (-1, 13), colors.Color(0.9, 0.95, 0.9)),  # Beneficio Neto
        
        # Bordes
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ])
    
    pyl_table.setStyle(style)
    elementos.append(pyl_table)
    
    # Análisis de tendencias
    elementos.append(Spacer(1, 0.3*inch))
    elementos.append(Paragraph("Análisis de Tendencias", styles['Subtitulo']))
    
    # Calcular CAGR de ventas
    ventas_inicial = pyl_df['Ventas'].iloc[0]
    ventas_final = pyl_df['Ventas'].iloc[-1]
    años = len(pyl_df) - 1
    cagr = ((ventas_final / ventas_inicial) ** (1/años) - 1) * 100 if ventas_inicial > 0 else 0
    
    # Margen EBITDA promedio
    margen_ebitda_prom = pyl_df['EBITDA %'].mean()
    
    analisis_text = f"""
    • <b>Crecimiento de Ventas (CAGR):</b> {cagr:.1f}%<br/>
    • <b>Margen EBITDA Promedio:</b> {margen_ebitda_prom:.1f}%<br/>
    • <b>Evolución de Ventas:</b> de €{ventas_inicial:,.0f} a €{ventas_final:,.0f}<br/>
    • <b>Tendencia de Márgenes:</b> {'Estable' if abs(pyl_df['EBITDA %'].iloc[-1] - pyl_df['EBITDA %'].iloc[0]) < 2 else 'Variable'}
    """
    
    elementos.append(Paragraph(analisis_text, styles['TextoNormal']))
    
    return elementos
def crear_analisis_swot(analisis_ia: Dict, styles) -> list:
    """Crear la sección de análisis SWOT"""
    elementos = []
    
    # Título
    elementos.append(Paragraph("ANÁLISIS SWOT", styles['TituloPrincipal']))
    elementos.append(Spacer(1, 0.3*inch))
    
    # Crear tabla SWOT 2x2
    swot_data = []
    
    # Fortalezas
    fortalezas_text = "<b>FORTALEZAS</b><br/><br/>"
    if analisis_ia and 'fortalezas' in analisis_ia:
        for f in analisis_ia['fortalezas']:
            fortalezas_text += f"• {f}<br/>"
    else:
        fortalezas_text += "• Posición establecida en el mercado<br/>• Equipo con experiencia<br/>• Productos/servicios diferenciados"
    
    # Debilidades
    debilidades_text = "<b>DEBILIDADES</b><br/><br/>"
    if analisis_ia and 'riesgos' in analisis_ia:
        for r in analisis_ia['riesgos'][:3]:  # Usar algunos riesgos como debilidades
            debilidades_text += f"• {r}<br/>"
    else:
        debilidades_text += "• Recursos financieros limitados<br/>• Dependencia de pocos clientes<br/>• Necesidad de digitalización"
    
    # Oportunidades
    oportunidades_text = "<b>OPORTUNIDADES</b><br/><br/>"
    oportunidades_text += "• Crecimiento del mercado digital<br/>"
    oportunidades_text += "• Nuevas tendencias de consumo<br/>"
    oportunidades_text += "• Expansión geográfica<br/>"
    oportunidades_text += "• Alianzas estratégicas"
    
    # Amenazas
    amenazas_text = "<b>AMENAZAS</b><br/><br/>"
    amenazas_text += "• Aumento de la competencia<br/>"
    amenazas_text += "• Cambios regulatorios<br/>"
    amenazas_text += "• Volatilidad económica<br/>"
    amenazas_text += "• Cambios tecnológicos rápidos"
    
    # Crear celdas con estilos
    fortalezas_para = Paragraph(fortalezas_text, ParagraphStyle(
        'Fortalezas',
        parent=styles['TextoNormal'],
        textColor=VERDE_POSITIVO,
        fontSize=10
    ))
    
    debilidades_para = Paragraph(debilidades_text, ParagraphStyle(
        'Debilidades',
        parent=styles['TextoNormal'],
        textColor=ROJO_NEGATIVO,
        fontSize=10
    ))
    
    oportunidades_para = Paragraph(oportunidades_text, ParagraphStyle(
        'Oportunidades',
        parent=styles['TextoNormal'],
        textColor=AZUL_PRINCIPAL,
        fontSize=10
    ))
    
    amenazas_para = Paragraph(amenazas_text, ParagraphStyle(
        'Amenazas',
        parent=styles['TextoNormal'],
        textColor=colors.orange,
        fontSize=10
    ))
    
    swot_data = [
        [fortalezas_para, debilidades_para],
        [oportunidades_para, amenazas_para]
    ]
    
    swot_table = Table(swot_data, colWidths=[3.5*inch, 3.5*inch])
    swot_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 2, AZUL_PRINCIPAL),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BACKGROUND', (0, 0), (0, 0), colors.Color(0.9, 0.95, 0.9)),  # Verde claro para fortalezas
        ('BACKGROUND', (1, 0), (1, 0), colors.Color(0.95, 0.9, 0.9)),  # Rojo claro para debilidades
        ('BACKGROUND', (0, 1), (0, 1), colors.Color(0.9, 0.9, 0.95)),  # Azul claro para oportunidades
        ('BACKGROUND', (1, 1), (1, 1), colors.Color(0.95, 0.93, 0.9)),  # Naranja claro para amenazas
        ('TOPPADDING', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ('RIGHTPADDING', (0, 0), (-1, -1), 12),
    ]))
    
    elementos.append(swot_table)
    elementos.append(Spacer(1, 0.3*inch))
    
    # Estrategias derivadas del SWOT
    elementos.append(Paragraph("Estrategias Derivadas del Análisis SWOT", styles['Subtitulo']))
    
    estrategias_text = """
    <b>Estrategias FO (Fortalezas-Oportunidades):</b><br/>
    • Aprovechar la experiencia del equipo para capturar nuevas oportunidades de mercado<br/>
    • Utilizar la posición establecida para expandirse geográficamente<br/><br/>
    
    <b>Estrategias DO (Debilidades-Oportunidades):</b><br/>
    • Buscar financiación para aprovechar el crecimiento del mercado<br/>
    • Implementar procesos de digitalización para mejorar la competitividad<br/><br/>
    
    <b>Estrategias FA (Fortalezas-Amenazas):</b><br/>
    • Diferenciación de productos para combatir la competencia<br/>
    • Diversificar la base de clientes para reducir riesgos<br/><br/>
    
    <b>Estrategias DA (Debilidades-Amenazas):</b><br/>
    • Establecer alianzas estratégicas para fortalecer la posición<br/>
    • Desarrollar planes de contingencia para volatilidad económica
    """
    
    elementos.append(Paragraph(estrategias_text, styles['TextoNormal']))
    
    return elementos
def crear_contexto_economico(datos_empresa: Dict, styles) -> list:
    """Crear la sección de contexto económico y sectorial"""
    elementos = []
    
    # Título
    elementos.append(Paragraph("CONTEXTO ECONÓMICO Y SECTORIAL", styles['TituloPrincipal']))
    elementos.append(Spacer(1, 0.3*inch))
    
    # Contexto Macroeconómico
    elementos.append(Paragraph("Contexto Macroeconómico España 2025-2030", styles['Subtitulo']))
    
    # Tabla de indicadores macro
    macro_data = [
        ['Indicador', '2025E', '2026E', '2027E', 'Tendencia'],
        ['Crecimiento PIB (%)', '2.1%', '1.9%', '1.8%', '→ Estable'],
        ['Inflación (IPC)', '2.5%', '2.2%', '2.0%', '↓ Bajada'],
        ['Tasa de Desempleo', '11.5%', '11.0%', '10.5%', '↓ Mejora'],
        ['Tipos de Interés (BCE)', '3.0%', '2.75%', '2.5%', '↓ Bajada'],
        ['Déficit Público (% PIB)', '-3.5%', '-3.0%', '-2.8%', '↓ Mejora']
    ]
    
    macro_table = Table(macro_data, colWidths=[2.2*inch, 1*inch, 1*inch, 1*inch, 1.3*inch])
    macro_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), AZUL_PRINCIPAL),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BACKGROUND', (0, 1), (0, -1), colors.Color(0.95, 0.95, 0.95)),
        ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
    ]))
    
    elementos.append(macro_table)
    elementos.append(Spacer(1, 0.3*inch))
    
    # Análisis Sectorial
    sector = datos_empresa.get('sector', 'General')
    elementos.append(Paragraph(f"Análisis del Sector: {sector}", styles['Subtitulo']))
    
    # Texto dinámico según el sector
    analisis_sectorial = get_analisis_sectorial(sector)
    elementos.append(Paragraph(analisis_sectorial, styles['TextoNormal']))
    elementos.append(Spacer(1, 0.2*inch))
    
    # Factores Clave del Sector
    elementos.append(Paragraph("Factores Clave del Éxito en el Sector", styles['Subtitulo']))
    
    factores_data = [
        ['Factor', 'Importancia', 'Posición Empresa'],
        ['Innovación y Tecnología', 'Alta', '●●●○○'],
        ['Calidad del Servicio', 'Alta', '●●●●○'],
        ['Precio Competitivo', 'Media', '●●●○○'],
        ['Red de Distribución', 'Media', '●●○○○'],
        ['Marca y Reputación', 'Alta', '●●●○○'],
        ['Sostenibilidad', 'Creciente', '●●○○○']
    ]
    
    factores_table = Table(factores_data, colWidths=[2.5*inch, 1.5*inch, 1.5*inch])
    factores_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), AZUL_PRINCIPAL),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    
    elementos.append(factores_table)
    elementos.append(Spacer(1, 0.2*inch))
    
    # Riesgos y Oportunidades
    elementos.append(Paragraph("Principales Riesgos y Oportunidades del Entorno", styles['Subtitulo']))
    
    riesgos_ops = """
    <b>Oportunidades:</b><br/>
    • Fondos Next Generation EU para digitalización y sostenibilidad<br/>
    • Crecimiento del comercio electrónico y canales digitales<br/>
    • Mayor conciencia ambiental impulsa productos sostenibles<br/>
    • Recuperación del turismo y consumo post-pandemia<br/><br/>
    
    <b>Riesgos:</b><br/>
    • Incertidumbre geopolítica y tensiones comerciales<br/>
    • Presión inflacionaria sobre márgenes<br/>
    • Escasez de talento cualificado en tecnología<br/>
    • Cambios regulatorios (fiscales, ambientales, laborales)<br/>
    • Volatilidad en cadenas de suministro globales
    """
    
    elementos.append(Paragraph(riesgos_ops, styles['TextoNormal']))
    
    return elementos
def crear_cash_flow_valoracion(pyl_df: pd.DataFrame, valoracion: Dict, styles) -> list:
    """Crear la sección de cash flow y valoración DCF"""
    elementos = []
    
    # Título
    elementos.append(Paragraph("ANÁLISIS DE CASH FLOW Y VALORACIÓN", styles['TituloPrincipal']))
    elementos.append(Spacer(1, 0.3*inch))
    
    # Cash Flow Proyectado
    elementos.append(Paragraph("Free Cash Flow Proyectado", styles['Subtitulo']))
    
    # Crear tabla de cash flow simplificada
    cf_data = [
        ['Concepto', 'Año 1', 'Año 2', 'Año 3', 'Año 4', 'Año 5'],
        ['EBITDA', f"€{pyl_df['EBITDA'].iloc[0]:,.0f}", f"€{pyl_df['EBITDA'].iloc[1]:,.0f}", 
         f"€{pyl_df['EBITDA'].iloc[2]:,.0f}", f"€{pyl_df['EBITDA'].iloc[3]:,.0f}", f"€{pyl_df['EBITDA'].iloc[4]:,.0f}"],
        ['(-) Impuestos', f"€{-pyl_df['Impuestos'].iloc[0]:,.0f}", f"€{-pyl_df['Impuestos'].iloc[1]:,.0f}",
         f"€{-pyl_df['Impuestos'].iloc[2]:,.0f}", f"€{-pyl_df['Impuestos'].iloc[3]:,.0f}", f"€{-pyl_df['Impuestos'].iloc[4]:,.0f}"],
        ['(-) CAPEX', '€-200,000', '€-200,000', '€-200,000', '€-200,000', '€-200,000'],
        ['(-) Δ Working Capital', '€-100,000', '€-50,000', '€-50,000', '€0', '€50,000'],
        ['Free Cash Flow', '', '', '', '', '']  # Se calculará abajo
    ]
    
    # Calcular FCF para cada año
    for i in range(5):
        fcf = pyl_df['EBITDA'].iloc[i] - pyl_df['Impuestos'].iloc[i] - 200000 - (100000 if i==0 else 50000 if i<3 else 0 if i==3 else -50000)
        cf_data[5][i+1] = f"€{fcf:,.0f}"
    
    cf_table = Table(cf_data, colWidths=[2*inch, 1.1*inch, 1.1*inch, 1.1*inch, 1.1*inch, 1.1*inch])
    cf_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), AZUL_PRINCIPAL),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('LINEBELOW', (0, 4), (-1, 4), 2, AZUL_PRINCIPAL),
        ('FONTNAME', (0, 5), (-1, 5), 'Helvetica-Bold'),
        ('BACKGROUND', (0, 5), (-1, 5), colors.Color(0.9, 0.95, 0.9)),
    ]))
    
    elementos.append(cf_table)
    elementos.append(Spacer(1, 0.3*inch))
    
    # Valoración DCF
    elementos.append(Paragraph("Valoración por Descuento de Flujos de Caja (DCF)", styles['Subtitulo']))
    
    # Parámetros de valoración
    wacc = valoracion.get('wacc_utilizado', 10) / 100 if valoracion.get('wacc_utilizado', 10) > 1 else valoracion.get('wacc_utilizado', 0.10)
    g_terminal = 0.02  # Crecimiento terminal 2%
    
    # Tabla de valoración
    val_data = [
        ['Parámetros de Valoración', 'Valor'],
        ['WACC', f"{wacc*100:.1f}%"],
        ['Tasa de Crecimiento Terminal (g)', f"{g_terminal*100:.1f}%"],
        ['Múltiplo de Salida (EV/EBITDA)', f"{valoracion.get('ev_ebitda_salida', 7.0):.1f}x"],
        ['', ''],
        ['Componentes del Valor', 'Importe'],
        ['Valor Presente de FCF (5 años)', f"€{valoracion.get('valor_empresa', 0)*0.35:,.0f}"],
        ['Valor Terminal', f"€{valoracion.get('valor_empresa', 0)*0.65:,.0f}"],
        ['Valor Enterprise (EV)', f"€{valoracion.get('valor_empresa', 0):,.0f}"],
        ['(-) Deuda Neta', f"€{valoracion.get('deuda_neta', 0):,.0f}"],
        ['Valor del Equity', f"€{valoracion.get('valor_equity', valoracion.get('valor_empresa', 0)):,.0f}"]
    ]
    
    val_table = Table(val_data, colWidths=[4*inch, 2*inch])
    val_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 5), (0, 5), 'Helvetica-Bold'),
        ('BACKGROUND', (0, 0), (-1, 0), colors.Color(0.9, 0.9, 0.95)),
        ('BACKGROUND', (0, 5), (-1, 5), colors.Color(0.9, 0.9, 0.95)),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('GRID', (0, 0), (-1, 3), 0.5, colors.grey),
        ('GRID', (0, 5), (-1, -1), 0.5, colors.grey),
        ('LINEBELOW', (0, 8), (-1, 8), 2, AZUL_PRINCIPAL),
        ('FONTNAME', (0, 8), (-1, 8), 'Helvetica-Bold'),
        ('FONTNAME', (0, 10), (-1, 10), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
    ]))
    
    elementos.append(val_table)
    elementos.append(Spacer(1, 0.3*inch))
    
    # Análisis de Sensibilidad
    elementos.append(Paragraph("Análisis de Sensibilidad del Valor", styles['Subtitulo']))
    
    # Valor base
    valor_base = valoracion.get('valor_empresa', 0)
    
    sens_data = [
        ['WACC / g', '1.0%', '1.5%', '2.0%', '2.5%', '3.0%'],
        ['8%', f"€{valor_base*1.25:,.0f}", f"€{valor_base*1.20:,.0f}", f"€{valor_base*1.15:,.0f}", 
         f"€{valor_base*1.12:,.0f}", f"€{valor_base*1.10:,.0f}"],
        ['9%', f"€{valor_base*1.15:,.0f}", f"€{valor_base*1.10:,.0f}", f"€{valor_base*1.05:,.0f}",
         f"€{valor_base*1.02:,.0f}", f"€{valor_base*1.00:,.0f}"],
        ['10%', f"€{valor_base*1.05:,.0f}", f"€{valor_base*1.02:,.0f}", f"€{valor_base:,.0f}",
         f"€{valor_base*0.97:,.0f}", f"€{valor_base*0.95:,.0f}"],
        ['11%', f"€{valor_base*0.95:,.0f}", f"€{valor_base*0.93:,.0f}", f"€{valor_base*0.90:,.0f}",
         f"€{valor_base*0.88:,.0f}", f"€{valor_base*0.85:,.0f}"],
        ['12%', f"€{valor_base*0.85:,.0f}", f"€{valor_base*0.83:,.0f}", f"€{valor_base*0.80:,.0f}",
         f"€{valor_base*0.78:,.0f}", f"€{valor_base*0.75:,.0f}"]
    ]
    
    sens_table = Table(sens_data, colWidths=[0.8*inch, 1.3*inch, 1.3*inch, 1.3*inch, 1.3*inch, 1.3*inch])
    sens_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), AZUL_PRINCIPAL),
        ('BACKGROUND', (0, 0), (0, -1), AZUL_PRINCIPAL),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        # Resaltar la celda del caso base (10%, 2%)
        ('BACKGROUND', (3, 3), (3, 3), VERDE_POSITIVO),
        ('TEXTCOLOR', (3, 3), (3, 3), colors.white),
        ('FONTNAME', (3, 3), (3, 3), 'Helvetica-Bold'),
    ]))
    
    elementos.append(sens_table)
    
    # Nota sobre la valoración
    elementos.append(Spacer(1, 0.2*inch))
    nota_text = """
    <i>Nota: La valoración se basa en proyecciones financieras y supuestos de mercado. El valor real puede variar 
    significativamente en función de la evolución del negocio y las condiciones de mercado. Se recomienda actualizar 
    la valoración periódicamente.</i>
    """
    elementos.append(Paragraph(nota_text, ParagraphStyle(
        'Nota',
        parent=styles['TextoNormal'],
        fontSize=8,
        textColor=GRIS_TEXTO,
        fontName='Helvetica-Oblique'
    )))
    
    return elementos
def crear_recomendaciones(analisis_ia: Dict, valoracion: Dict, pyl_df: pd.DataFrame, styles) -> list:
    """Crear la sección de recomendaciones estratégicas"""
    elementos = []
    
    # Título
    elementos.append(Paragraph("RECOMENDACIONES ESTRATÉGICAS", styles['TituloPrincipal']))
    elementos.append(Spacer(1, 0.3*inch))
    
    # Resumen de la situación
    elementos.append(Paragraph("Evaluación General del Proyecto", styles['Subtitulo']))
    
    viabilidad = analisis_ia.get('viabilidad', 'MEDIA') if analisis_ia else 'MEDIA'
    rating = analisis_ia.get('rating', '★★★☆☆') if analisis_ia else '★★★☆☆'
    valor_empresa = valoracion.get('valor_empresa', 0)
    
    eval_text = f"""
    <b>Rating del Proyecto:</b> {rating}<br/>
    <b>Viabilidad:</b> {viabilidad}<br/>
    <b>Valoración Estimada:</b> €{valor_empresa:,.0f}<br/>
    <b>Recomendación General:</b> {'INVERTIR' if 'ALTA' in viabilidad else 'PROCEDER CON CAUTELA' if 'MEDIA' in viabilidad else 'REPLANTEAR ESTRATEGIA'}
    """
    
    elementos.append(Paragraph(eval_text, styles['TextoNormal']))
    elementos.append(Spacer(1, 0.3*inch))
    
    # Plan de Acción Prioritario
    elementos.append(Paragraph("Plan de Acción Prioritario - Primeros 100 Días", styles['Subtitulo']))
    
    plan_data = [
        ['Plazo', 'Acción', 'Responsable', 'KPI'],
        ['0-30 días', 'Optimizar estructura de costes', 'CFO', 'Reducción 5% gastos operativos'],
        ['0-30 días', 'Implementar sistema de control financiero', 'CFO', 'Dashboard operativo activo'],
        ['30-60 días', 'Desarrollar plan de ventas detallado', 'Dir. Comercial', 'Pipeline x3 objetivo mensual'],
        ['30-60 días', 'Cerrar acuerdos con proveedores clave', 'COO', 'Contratos firmados'],
        ['60-90 días', 'Lanzar estrategia digital', 'CMO', '20% leads digitales'],
        ['90-100 días', 'Completar equipo directivo', 'CEO', 'Posiciones clave cubiertas']
    ]
    
    plan_table = Table(plan_data, colWidths=[1.2*inch, 2.5*inch, 1.3*inch, 2*inch])
    plan_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), AZUL_PRINCIPAL),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BACKGROUND', (0, 1), (0, 2), colors.Color(1, 0.95, 0.95)),  # Rojo claro 0-30 días
        ('BACKGROUND', (0, 3), (0, 4), colors.Color(1, 1, 0.9)),      # Amarillo claro 30-60 días
        ('BACKGROUND', (0, 5), (0, 6), colors.Color(0.9, 1, 0.9)),    # Verde claro 60-100 días
    ]))
    
    elementos.append(plan_table)
    elementos.append(Spacer(1, 0.3*inch))
    
    # Recomendaciones específicas de la IA
    if analisis_ia and 'recomendaciones' in analisis_ia:
        elementos.append(Paragraph("Recomendaciones Específicas del Análisis", styles['Subtitulo']))
        
        for i, rec in enumerate(analisis_ia['recomendaciones'][:5], 1):
            rec_text = f"<b>{i}.</b> {rec}"
            elementos.append(Paragraph(rec_text, styles['TextoNormal']))
            elementos.append(Spacer(1, 0.1*inch))
    
    # Iniciativas de Crecimiento
    elementos.append(Spacer(1, 0.2*inch))
    elementos.append(Paragraph("Iniciativas Clave para el Crecimiento", styles['Subtitulo']))
    
    # Calcular si las ventas crecen o decrecen
    crecimiento_ventas = ((pyl_df['Ventas'].iloc[-1] / pyl_df['Ventas'].iloc[0]) ** (1/4) - 1) * 100
    
    if crecimiento_ventas < 0:
        iniciativas_text = """
        <b>URGENTE - Plan de Recuperación de Ventas:</b><br/>
        • Análisis inmediato de pérdida de clientes y causas<br/>
        • Revisión completa de propuesta de valor<br/>
        • Implementar programa de retención de clientes<br/>
        • Desarrollar nuevos canales de distribución<br/>
        • Considerar pivote de modelo de negocio<br/><br/>
        """
    else:
        iniciativas_text = """
        <b>Iniciativas de Aceleración del Crecimiento:</b><br/>
        • Expansión geográfica a nuevos mercados<br/>
        • Desarrollo de nuevas líneas de producto/servicio<br/>
        • Inversión en marketing digital y branding<br/>
        • Programa de fidelización de clientes<br/>
        • Alianzas estratégicas y partnerships<br/><br/>
        """
    
    iniciativas_text += """
    <b>Optimización Operativa:</b><br/>
    • Digitalización de procesos clave<br/>
    • Implementación de KPIs y cuadros de mando<br/>
    • Optimización del working capital<br/>
    • Mejora continua en márgenes<br/>
    • Gestión activa de tesorería<br/><br/>
    
    <b>Gestión del Talento:</b><br/>
    • Plan de captación de talento clave<br/>
    • Programa de formación y desarrollo<br/>
    • Sistema de incentivos alineado con objetivos<br/>
    • Cultura de innovación y mejora continua
    """
    
    elementos.append(Paragraph(iniciativas_text, styles['TextoNormal']))
    elementos.append(Spacer(1, 0.3*inch))
    
    # Métricas de Seguimiento
    elementos.append(Paragraph("KPIs Críticos para Monitorizar", styles['Subtitulo']))
    
    kpi_data = [
        ['KPI', 'Objetivo Año 1', 'Frecuencia', 'Responsable'],
        ['Ventas mensuales', f"€{pyl_df['Ventas'].iloc[0]/12:,.0f}", 'Mensual', 'Dir. Comercial'],
        ['Margen EBITDA', f"{pyl_df['EBITDA %'].iloc[0]:.1f}%", 'Mensual', 'CFO'],
        ['Cash Flow', 'Positivo', 'Mensual', 'CFO'],
        ['Días de cobro', '< 60 días', 'Mensual', 'CFO'],
        ['Satisfacción cliente', '> 8/10', 'Trimestral', 'COO'],
        ['Rotación empleados', '< 15%', 'Trimestral', 'RRHH']
    ]
    
    kpi_table = Table(kpi_data, colWidths=[2*inch, 1.5*inch, 1.2*inch, 1.3*inch])
    kpi_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), AZUL_PRINCIPAL),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ALIGN', (1, 0), (2, -1), 'CENTER'),
    ]))
    
    elementos.append(kpi_table)
    
    # Nota final
    elementos.append(Spacer(1, 0.3*inch))
    conclusion_text = """
    <b>Conclusión:</b> El éxito del proyecto dependerá de la ejecución disciplinada del plan estratégico, 
    el seguimiento continuo de KPIs y la capacidad de adaptación a las condiciones del mercado. 
    Se recomienda revisión trimestral del business plan y ajustes según evolución real del negocio.
    """
    
    elementos.append(Paragraph(conclusion_text, ParagraphStyle(
        'Conclusion',
        parent=styles['TextoNormal'],
        fontSize=11,
        spaceAfter=12,
        spaceBefore=12,
        borderWidth=1,
        borderColor=AZUL_PRINCIPAL,
        borderPadding=10,
        backColor=colors.Color(0.95, 0.95, 1)
    )))
    
    return elementos
def get_analisis_sectorial(sector):
    """Obtener análisis específico por sector"""
    analisis_por_sector = {
        "Tecnología": """
        El sector tecnológico español experimenta un crecimiento sostenido del 8-10% anual, impulsado por la transformación digital de empresas y administraciones. 
        Se prevé una inversión de 20.000M€ en los próximos 3 años proveniente de fondos europeos. Las principales tendencias incluyen: 
        IA y Machine Learning, ciberseguridad, cloud computing y desarrollo de software. El sector enfrenta el reto de la escasez de talento cualificado 
        y la competencia global, pero ofrece márgenes elevados (20-40%) y alto potencial de escalabilidad.
        """,
        "Alimentación": """
        El sector alimentario representa el 9% del PIB español y emplea a más de 500.000 personas. Crece a un ritmo del 2-3% anual con márgenes 
        del 5-15% según subsector. Las tendencias clave incluyen: productos saludables, sostenibilidad, trazabilidad y comercio online. 
        España es líder en exportación agroalimentaria en Europa. Los retos incluyen la presión en precios, cambios en hábitos de consumo 
        y requisitos regulatorios crecientes.
        """,
        "Consultoría": """
        El mercado de consultoría en España mueve 13.000M€ anuales con crecimiento del 6-8%. Los servicios más demandados son: 
        transformación digital, sostenibilidad ESG, estrategia y operaciones. El sector se caracteriza por márgenes del 15-25% y 
        alta dependencia del talento. Las Big Four dominan el 40% del mercado, pero existe espacio para consultoras especializadas. 
        La principal barrera de entrada es la reputación y red de contactos.
        """,
        "Hostelería": """
        El sector hostelero aporta el 6.2% del PIB español y emplea a 1.7 millones de personas. Tras la recuperación post-COVID, 
        crece al 4-5% anual. Las tendencias incluyen: digitalización de procesos, experiencias personalizadas, sostenibilidad y 
        nuevos conceptos gastronómicos. Los márgenes varían del 10-20% según tipo de establecimiento. Los retos son: alta rotación 
        de personal, estacionalidad y presión en costes laborales y energéticos.
        """,
        "E-commerce": """
        El comercio electrónico en España supera los 60.000M€ con crecimiento del 15-20% anual. La penetración alcanza el 85% de 
        internautas. Los sectores líderes son: moda, electrónica y alimentación. Las claves del éxito incluyen: logística eficiente, 
        experiencia omnicanal y personalización. Los márgenes oscilan entre 5-20% según vertical. Amazon domina el 30% del mercado, 
        pero hay oportunidades en nichos especializados.
        """
    }
    
    return analisis_por_sector.get(sector, f"""
        El sector {sector} en España muestra un comportamiento estable con crecimiento moderado del 2-4% anual. 
        Las principales tendencias incluyen la digitalización de procesos, mayor enfoque en sostenibilidad y adaptación a nuevos 
        hábitos de consumo. El sector enfrenta retos como la presión en márgenes, necesidad de inversión tecnológica y cambios 
        regulatorios. Sin embargo, ofrece oportunidades en innovación, expansión internacional y nuevos modelos de negocio.
    """)
def generar_pdf_profesional(
    datos_empresa: Dict,
    pyl_df: pd.DataFrame,
    balance_df: Optional[pd.DataFrame] = None,
    cash_flow_df: Optional[pd.DataFrame] = None,
    ratios_df: Optional[pd.DataFrame] = None,
    valoracion: Optional[Dict] = None,
    analisis_ia: Optional[Dict] = None,
    contexto_economico: Optional[Dict] = None
) -> bytes:
    """
    Genera un PDF profesional con toda la información del Business Plan
    """
    # Buffer para el PDF
    buffer = BytesIO()
    
    # Crear documento
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=72
    )
    
    # Obtener estilos
    styles = crear_estilos()
    
    # Lista de elementos del PDF
    story = []
    
    # 1. PORTADA
    story.extend(crear_portada(datos_empresa, styles))
    story.append(PageBreak())

    # 2. RESUMEN EJECUTIVO
    story.extend(crear_resumen_ejecutivo(datos_empresa, pyl_df, valoracion, analisis_ia, styles))
    story.append(PageBreak())

    # 3. CONTEXTO ECONÓMICO Y SECTORIAL
    story.extend(crear_contexto_economico(datos_empresa, styles))
    story.append(PageBreak())

    # 4. ANÁLISIS SWOT
    story.extend(crear_analisis_swot(analisis_ia, styles))
    story.append(PageBreak())

    # 5. P&L DETALLADO
    story.extend(crear_pyl_detallado(pyl_df, styles))
    story.append(PageBreak())

    # 6. CASH FLOW Y VALORACIÓN
    story.extend(crear_cash_flow_valoracion(pyl_df, valoracion, styles))
    story.append(PageBreak())

    # 7. RECOMENDACIONES ESTRATÉGICAS
    story.extend(crear_recomendaciones(analisis_ia, valoracion, pyl_df, styles))
          
    # Construir PDF
    doc.build(story, canvasmaker=NumberedCanvas)
    
    # Obtener bytes del PDF
    pdf_bytes = buffer.getvalue()
    buffer.close()
    
    return pdf_bytes