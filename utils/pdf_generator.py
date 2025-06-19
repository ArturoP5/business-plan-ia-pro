from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.graphics.shapes import Drawing, Rect, Line
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.linecharts import HorizontalLineChart
from reportlab.graphics.charts.piecharts import Pie
from reportlab.pdfgen import canvas
from datetime import datetime
import pandas as pd
from typing import Dict
from io import BytesIO

def generar_pdf_ejecutivo(datos_empresa: Dict, pyl_df: pd.DataFrame, 
                         valoracion: Dict, analisis_ia: Dict, 
                         financiacion_df: pd.DataFrame, fcf_df: pd.DataFrame = None) -> bytes:
    """
    Genera un PDF ejecutivo profesional estilo McKinsey/Goldman Sachs
    """
      # DEBUGGING - AGREGAR ESTAS LÍNEAS
    print("=== DEBUG PDF GENERATOR ===")
    print(f"datos_empresa keys: {datos_empresa.keys() if datos_empresa else 'None'}")
    print(f"pyl_df shape: {pyl_df.shape if pyl_df is not None else 'None'}")
    print(f"valoracion keys: {valoracion.keys() if valoracion else 'None'}")
    print(f"analisis_ia keys: {analisis_ia.keys() if analisis_ia else 'None'}")
    print(f"financiacion_df shape: {financiacion_df.shape if financiacion_df is not None else 'None'}")
    print(f"fcf_df shape: {fcf_df.shape if fcf_df is not None else 'None'}")
    print("========================")
    
    buffer = BytesIO()
    
    # Configuración del documento
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm,
        title=f"Business Plan - {datos_empresa['nombre']}",
        author="Business Plan IA"
    )
    
    # Contenido del PDF
    story = []
    
    # Estilos profesionales
    styles = getSampleStyleSheet()
    
    # Estilo para título principal
    titulo_principal = ParagraphStyle(
        'TituloPrincipal',
        parent=styles['Title'],
        fontSize=32,
        textColor=colors.HexColor('#0F172A'),
        alignment=TA_CENTER,
        spaceAfter=12,
        fontName='Helvetica-Bold'
    )
    
    # Estilo para subtítulos
    subtitulo = ParagraphStyle(
        'Subtitulo',
        parent=styles['Heading1'],
        fontSize=20,
        textColor=colors.HexColor('#334155'),
        spaceAfter=20,
        fontName='Helvetica-Bold',
        borderWidth=2,
        borderColor=colors.HexColor('#3B82F6'),
        borderPadding=(0, 0, 5, 0)
    )
    
    # Estilo para texto ejecutivo
    texto_ejecutivo = ParagraphStyle(
        'TextoEjecutivo',
        parent=styles['Normal'],
        fontSize=11,
        textColor=colors.HexColor('#475569'),
        alignment=TA_JUSTIFY,
        spaceAfter=12,
        leading=16
    )
    
    # Estilo para highlights
    highlight_style = ParagraphStyle(
        'Highlight',
        parent=styles['Normal'],
        fontSize=14,
        textColor=colors.HexColor('#1E40AF'),
        alignment=TA_CENTER,
        fontName='Helvetica-Bold',
        spaceAfter=20
    )
    
    # PORTADA EJECUTIVA
    story.append(Spacer(1, 3*cm))
    
    # Logo/Marca (simulado con texto)
    story.append(Paragraph("BUSINESS PLAN", ParagraphStyle(
        'Logo',
        fontSize=16,
        textColor=colors.HexColor('#64748B'),
        alignment=TA_CENTER,
        fontName='Helvetica',
        spaceAfter=20
    )))
    
    # Título de la empresa
    story.append(Paragraph(datos_empresa['nombre'].upper(), titulo_principal))
    
    # Línea decorativa
    d = Drawing(450, 3)
    d.add(Line(0, 0, 450, 0, strokeColor=colors.HexColor('#3B82F6'), strokeWidth=3))
    story.append(d)
    story.append(Spacer(1, 0.5*cm))
    
    # Sector y fecha
    story.append(Paragraph(f"Sector {datos_empresa['sector']}", ParagraphStyle(
        'Sector',
        fontSize=16,
        textColor=colors.HexColor('#64748B'),
        alignment=TA_CENTER,
        spaceAfter=8
    )))
    
    story.append(Paragraph(datetime.now().strftime("%B %Y").upper(), ParagraphStyle(
        'Fecha',
        fontSize=14,
        textColor=colors.HexColor('#94A3B8'),
        alignment=TA_CENTER
    )))
    
    story.append(Spacer(1, 4*cm))
    
    # Rating y valoración en la portada
    valoracion_text = f"Valoración: €{valoracion['valor_empresa']:,.0f}"
    story.append(Paragraph(valoracion_text, highlight_style))
    
    rating_text = f"Rating: {analisis_ia['rating']}"
    story.append(Paragraph(rating_text, ParagraphStyle(
        'Rating',
        fontSize=18,
        textColor=colors.HexColor('#059669') if 'Excelente' in analisis_ia['rating'] else colors.HexColor('#DC2626'),
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )))
    
    story.append(PageBreak())
    
    # EXECUTIVE SUMMARY
    story.append(Paragraph("EXECUTIVE SUMMARY", subtitulo))
    story.append(Paragraph(analisis_ia['resumen_ejecutivo'].strip(), texto_ejecutivo))
    story.append(Spacer(1, 1*cm))
    
    # KEY INVESTMENT HIGHLIGHTS
    story.append(Paragraph("KEY INVESTMENT HIGHLIGHTS", subtitulo))
    
    # Crear tabla de highlights
    highlights_data = []
    
    # Crecimiento
    crecimiento = ((pyl_df['Ventas'].iloc[-1] / pyl_df['Ventas'].iloc[0]) ** (1/5) - 1) * 100
    highlights_data.append([
        "CRECIMIENTO ANUAL (CAGR)",
        f"{crecimiento:.1f}%",
        "📈"
    ])
    
    # EBITDA
    highlights_data.append([
        "MARGEN EBITDA AÑO 5",
        f"{pyl_df['EBITDA %'].iloc[-1]:.1f}%",
        "💰"
    ])
    
    # Valoración
    highlights_data.append([
        "MÚLTIPLO EV/EBITDA",
        f"{valoracion['ev_ebitda_salida']:.1f}x",
        "📊"
    ])
    
    # TIR
    highlights_data.append([
        "TIR ESPERADA",
        f"{valoracion['tir_esperada']:.1f}%",
        "🎯"
    ])
    
    highlights_table = Table(highlights_data, colWidths=[7*cm, 4*cm, 1*cm])
    highlights_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F8FAFC')),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#1E293B')),
        ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#1E40AF')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('FONTSIZE', (1, 0), (1, -1), 16),
        ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white, colors.HexColor('#F1F5F9')]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ('RIGHTPADDING', (0, 0), (-1, -1), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
    ]))
    
    story.append(highlights_table)
    story.append(PageBreak())

    # PERSPECTIVAS ECONÓMICAS Y SECTORIALES
    story.append(Paragraph("PERSPECTIVAS ECONÓMICAS Y SECTORIALES", subtitulo))
    story.append(Spacer(1, 0.5*cm))
    
    # Contexto Macroeconómico
    story.append(Paragraph("Contexto Macroeconómico España 2024-2029", ParagraphStyle(
        'Subsection',
        fontSize=14,
        textColor=colors.HexColor('#1E40AF'),
        fontName='Helvetica-Bold',
        spaceAfter=12
    )))
    
   # Tabla de indicadores macro
    macro_data = [
        ['Indicador', '2024E', '2025E', '2026E', 'Tendencia'],
        ['Crecimiento PIB (%)', '2.3%', '1.9%', '1.7%', 'Estable'],
        ['Inflación (IPC)', '3.3%', '2.4%', '1.9%', 'Bajada'],
        ['Euribor 12M', '3.6%', '2.9%', '2.5%', 'Bajada'],
        ['Tasa de Desempleo', '12.1%', '11.7%', '11.3%', 'Mejora'],
        ['Consumo Privado', '1.6%', '1.8%', '2.0%', 'Subida']
    ]
    
    tabla_macro = Table(macro_data, colWidths=[5*cm, 2.5*cm, 2.5*cm, 2.5*cm, 2.5*cm])
    tabla_macro.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3B82F6')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8FAFC')]),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    
    story.append(tabla_macro)
    story.append(Spacer(1, 0.5*cm))
    
    # Análisis sectorial específico
    sector_analysis = {
        'Hostelería': 'El sector hostelero español muestra una recuperación sólida post-COVID, con crecimientos del 5-7% anual. Factores clave: turismo internacional récord, digitalización acelerada y nuevos modelos de negocio híbridos.',
        'Tecnología': 'Sector en expansión con crecimientos del 15-20% anual. España se posiciona como hub tecnológico del sur de Europa. Oportunidades en IA, ciberseguridad y transformación digital empresarial.',
        'Automoción': 'Transformación hacia la electromovilidad con inversiones récord. España mantiene su posición como 2º productor europeo. Retos: adaptación cadena suministro y competencia asiática.',
        'Ecommerce': 'Crecimiento sostenido del 8-10% anual. Penetración online alcanzará el 20% del retail total en 2026. Tendencias: quick commerce, sostenibilidad y experiencia omnicanal.',
        'Consultoría': 'Mercado en expansión del 7-9% anual. Alta demanda en transformación digital, ESG y gestión del cambio. Consolidación del sector y entrada de nuevos players tecnológicos.',
        'Retail': 'Recuperación gradual con crecimientos del 3-4%. Transformación hacia modelos híbridos físico-digital. Presión en márgenes por inflación y cambios en patrones de consumo.',
        'Servicios': 'Sector heterogéneo con crecimientos del 4-6%. Digitalización de procesos y profesionalización. Oportunidades en servicios de valor añadido y especialización.',
        'Industrial': 'Modernización y reindustrialización con fondos Next Generation. Crecimiento del 3-5% con foco en sostenibilidad, Industria 4.0 y reshoring de producción.'
    }
    
    story.append(Paragraph(f"Análisis Sectorial - {datos_empresa['sector']}", ParagraphStyle(
        'Subsection',
        fontSize=14,
        textColor=colors.HexColor('#1E40AF'),
        fontName='Helvetica-Bold',
        spaceAfter=12
    )))
    
    sector_text = sector_analysis.get(datos_empresa['sector'], 
                                     'Sector con perspectivas moderadas de crecimiento. Importante monitorizar evolución competitiva y adaptación tecnológica.')
    
    story.append(Paragraph(sector_text, texto_ejecutivo))
    story.append(Spacer(1, 0.5*cm))
    
    # Factores de riesgo macroeconómico
    story.append(Paragraph("Factores de Riesgo a Monitorizar", ParagraphStyle(
        'Warning',
        fontSize=12,
        textColor=colors.HexColor('#DC2626'),
        fontName='Helvetica-Bold',
        spaceAfter=8
    )))
    
    riesgos = [
        "• Política monetaria BCE y evolución tipos de interés",
        "• Tensiones geopolíticas y cadenas de suministro",
        "• Evolución inflación y costes energéticos",
        "• Cambios regulatorios y fiscales",
        "• Impacto tecnológico y digitalización acelerada"
    ]
    
    for riesgo in riesgos:
        story.append(Paragraph(riesgo, ParagraphStyle(
            'RiskItem',
            fontSize=10,
            textColor=colors.HexColor('#64748B'),
            leftIndent=20,
            spaceAfter=4
        )))
    
    # Fuentes de información
    story.append(Spacer(1, 0.5*cm))
    story.append(Paragraph("Fuentes", ParagraphStyle(
        'SourcesTitle',
        fontSize=10,
        textColor=colors.HexColor('#64748B'),
        fontName='Helvetica-Oblique',
        spaceAfter=4
    )))
    
    fuentes_text = """Datos macroeconómicos: Banco de España, INE, Comisión Europea (DG ECFIN), FMI World Economic Outlook. 
    Análisis sectorial: CNMV, Informes sectoriales del Ministerio de Industria, Comercio y Turismo, 
    Observatorio Nacional de Tecnología y Sociedad (ONTSI), ANFAC (Automoción), Mesa del Turismo."""
    
    story.append(Paragraph(fuentes_text, ParagraphStyle(
        'Sources',
        fontSize=8,
        textColor=colors.HexColor('#94A3B8'),
        fontName='Helvetica',
        alignment=TA_JUSTIFY,
        leftIndent=20,
        rightIndent=20,
        spaceAfter=12
    )))
    
    story.append(PageBreak())
    
    # PROYECCIONES FINANCIERAS
    story.append(Paragraph("PROYECCIONES FINANCIERAS", subtitulo))
    story.append(Spacer(1, 0.5*cm))
    
    # Tabla de métricas principales
    metricas_principales = [
        ['', 'Año 1', 'Año 3', 'Año 5', 'CAGR'],
        ['Ventas (€k)', 
         f"{pyl_df['Ventas'].iloc[0]/1000:.0f}",
         f"{pyl_df['Ventas'].iloc[2]/1000:.0f}",
         f"{pyl_df['Ventas'].iloc[-1]/1000:.0f}",
         f"{crecimiento:.1f}%"],
        ['EBITDA (€k)', 
         f"{pyl_df['EBITDA'].iloc[0]/1000:.0f}",
         f"{pyl_df['EBITDA'].iloc[2]/1000:.0f}",
         f"{pyl_df['EBITDA'].iloc[-1]/1000:.0f}",
         f"{((pyl_df['EBITDA'].iloc[-1]/pyl_df['EBITDA'].iloc[0])**(1/5)-1)*100:.1f}%"],
        ['Margen EBITDA (%)', 
         f"{pyl_df['EBITDA %'].iloc[0]:.1f}",
         f"{pyl_df['EBITDA %'].iloc[2]:.1f}",
         f"{pyl_df['EBITDA %'].iloc[-1]:.1f}",
         "-"],
        ['FCF (€k)', 
         f"{fcf_df['Free Cash Flow'].iloc[0]/1000:.0f}",
         f"{fcf_df['Free Cash Flow'].iloc[2]/1000:.0f}",
         f"{fcf_df['Free Cash Flow'].iloc[-1]/1000:.0f}",
         "-"]
    ]
    
    tabla_metricas = Table(metricas_principales, colWidths=[4*cm, 3*cm, 3*cm, 3*cm, 2.5*cm])
    tabla_metricas.setStyle(TableStyle([
        # Encabezado
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E293B')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        
        # Primera columna
        ('BACKGROUND', (0, 1), (0, -1), colors.HexColor('#F8FAFC')),
        ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
        
        # Datos
        ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
        ('FONTNAME', (1, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        
        # Grid
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    
    story.append(tabla_metricas)
    story.append(Spacer(1, 1*cm))
    
    # ANÁLISIS ESTRATÉGICO Y RECOMENDACIONES
    story.append(Paragraph("ANÁLISIS ESTRATÉGICO Y RECOMENDACIONES", subtitulo))
    story.append(Spacer(1, 0.5*cm))
    
    # Fortalezas
    story.append(Paragraph("Fortalezas Identificadas", ParagraphStyle(
        'Subsection',
        fontSize=14,
        textColor=colors.HexColor('#059669'),
        fontName='Helvetica-Bold',
        spaceAfter=12
    )))
    
    for fortaleza in analisis_ia.get('fortalezas', []):
        story.append(Paragraph(f"• {fortaleza}", ParagraphStyle(
            'Item',
            fontSize=11,
            textColor=colors.HexColor('#475569'),
            leftIndent=20,
            spaceAfter=6
        )))
    
    story.append(Spacer(1, 0.5*cm))
    
    # Riesgos
    story.append(Paragraph("Riesgos a Mitigar", ParagraphStyle(
        'Subsection',
        fontSize=14,
        textColor=colors.HexColor('#DC2626'),
        fontName='Helvetica-Bold',
        spaceAfter=12
    )))
    
    for riesgo in analisis_ia.get('riesgos', []):
        story.append(Paragraph(f"• {riesgo}", ParagraphStyle(
            'Item',
            fontSize=11,
            textColor=colors.HexColor('#475569'),
            leftIndent=20,
            spaceAfter=6
        )))
    
    story.append(Spacer(1, 0.5*cm))
    
    # Recomendaciones
    story.append(Paragraph("Recomendaciones Estratégicas", ParagraphStyle(
        'Subsection',
        fontSize=14,
        textColor=colors.HexColor('#1E40AF'),
        fontName='Helvetica-Bold',
        spaceAfter=12
    )))
    
    for recomendacion in analisis_ia.get('recomendaciones', []):
        story.append(Paragraph(f"→ {recomendacion}", ParagraphStyle(
            'Recommendation',
            fontSize=11,
            textColor=colors.HexColor('#1E293B'),
            leftIndent=20,
            spaceAfter=8,
            fontName='Helvetica'
        )))
    
    # VALORACIÓN
    story.append(Paragraph("VALORACIÓN DE LA EMPRESA", subtitulo))
    story.append(Spacer(1, 0.5*cm))
    
    # Tabla de valoración
    val_data = [
        ['Metodología', 'Valor', 'Múltiplo'],
        ['DCF (Caso Base)', f"€{valoracion['valor_empresa']:,.0f}", f"{valoracion['ev_ebitda_salida']:.1f}x EBITDA"],
        ['Escenario Conservador', f"€{valoracion['valoracion_escenario_bajo']:,.0f}", "WACC +2%"],
        ['Escenario Optimista', f"€{valoracion['valoracion_escenario_alto']:,.0f}", "WACC -1%"]
    ]
    
    tabla_val = Table(val_data, colWidths=[6*cm, 5*cm, 5*cm])
    tabla_val.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E293B')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8FAFC')]),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
    ]))
    
    story.append(tabla_val)
    story.append(Spacer(1, 1*cm))
       
    # Conclusión
    conclusion = f"""
    Basado en nuestro análisis, {datos_empresa['nombre']} presenta una oportunidad de inversión 
    {analisis_ia['viabilidad'].lower()} con un potencial de retorno del {valoracion['tir_esperada']:.1f}% 
    y una valoración estimada de €{valoracion['valor_empresa']:,.0f}.
    """
    
    story.append(Paragraph("CONCLUSIÓN", ParagraphStyle(
        'Conclusion',
        fontSize=14,
        textColor=colors.HexColor('#1E293B'),
        fontName='Helvetica-Bold',
        spaceAfter=12
    )))
    story.append(Paragraph(conclusion, texto_ejecutivo))
    
    # Disclaimer
    story.append(Spacer(1, 2*cm))
    disclaimer = """
    Este documento contiene proyecciones financieras basadas en supuestos y análisis de mercado. 
    Los resultados reales pueden diferir materialmente. Se recomienda revisión por asesores profesionales.
    """
    story.append(Paragraph(disclaimer, ParagraphStyle(
        'Disclaimer',
        fontSize=8,
        textColor=colors.HexColor('#94A3B8'),
        alignment=TA_CENTER,
        fontName='Helvetica-Oblique'
    )))
    
    # Generar PDF
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()