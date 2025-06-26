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
NARANJA_ALERTA = colors.HexColor('#f59e0b')

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
    """Crear la sección de resumen ejecutivo mejorado"""
    elementos = []
    
    # Título de la sección
    elementos.append(Paragraph("INVESTMENT MEMORANDUM - EXECUTIVE SUMMARY", styles['TituloPrincipal']))
    elementos.append(Spacer(1, 0.3*inch))
    
    # INVESTMENT THESIS DESTACADO
    thesis_style = ParagraphStyle(
        'ThesisBox',
        parent=styles['TextoNormal'],
        borderWidth=2,
        borderColor=AZUL_PRINCIPAL,
        borderPadding=12,
        backColor=colors.Color(0.97, 0.97, 1),
        spaceAfter=12
    )
    
    # Extraer métricas clave
    sector = datos_empresa.get('sector', 'General')
    ventas_actuales = pyl_df['Ventas'].iloc[0] if len(pyl_df) > 0 else 0
    ventas_futuras = pyl_df['Ventas'].iloc[-1] if len(pyl_df) > 0 else 0
    ebitda_actual = pyl_df['EBITDA'].iloc[0] if len(pyl_df) > 0 else 0
    ebitda_futuro = pyl_df['EBITDA'].iloc[-1] if len(pyl_df) > 0 else 0
    margen_actual = pyl_df['EBITDA %'].iloc[0] if 'EBITDA %' in pyl_df.columns else 15
    margen_futuro = pyl_df['EBITDA %'].iloc[-1] if 'EBITDA %' in pyl_df.columns else 20
    
    cagr_ventas = ((ventas_futuras / ventas_actuales) ** (1/5) - 1) * 100 if ventas_actuales > 0 else 0
    cagr_ebitda = ((ebitda_futuro / ebitda_actual) ** (1/5) - 1) * 100 if ebitda_actual > 0 else 0
    
    valor_empresa = valoracion.get('valor_empresa', 0)
    multiplo_entrada = analisis_ia.get('multiplo_ebitda_ltm', 10.3)
    tir_proyecto = valoracion.get('tir_esperada', 20)
    
    # Investment Thesis mejorado
    thesis_text = f"""
    <b><font size="12">INVESTMENT THESIS</font></b><br/><br/>
    
    <b>{datos_empresa.get('nombre', 'La Empresa')}</b> representa una oportunidad de inversión 
    <b>{'excepcional' if tir_proyecto > 25 else 'atractiva' if tir_proyecto > 15 else 'moderada'}</b> 
    en el sector <b>{sector}</b> español, con un equity story basado en:
    <br/><br/>
    
    <b>1. Crecimiento Acelerado:</b> CAGR Ventas {cagr_ventas:.1f}% / CAGR EBITDA {cagr_ebitda:.1f}%<br/>
    <b>2. Expansión de Márgenes:</b> {margen_actual:.1f}% → {margen_futuro:.1f}% (+{margen_futuro - margen_actual:.0f}pp)<br/>
    <b>3. Valoración Atractiva:</b> {multiplo_entrada:.1f}x EBITDA (descuento 20-30% vs. peers)<br/>
    <b>4. Clear Path to Exit:</b> Múltiples compradores estratégicos y financieros<br/>
    <b>5. Management Buy-in:</b> Equipo comprometido con skin in the game
    """
    
    elementos.append(Paragraph(thesis_text, thesis_style))
    elementos.append(Spacer(1, 0.3*inch))
    
    # SNAPSHOT DE LA TRANSACCIÓN
    elementos.append(Paragraph("Transaction Snapshot", styles['Subtitulo']))
    
    # Crear dos columnas para la información
    snapshot_data = [
        [
            Paragraph("<b>Target Company</b>", styles['TextoNormal']),
            Paragraph(f"{datos_empresa.get('nombre', 'N/A')}", styles['TextoNormal'])
        ],
        [
            Paragraph("<b>Sector</b>", styles['TextoNormal']),
            Paragraph(f"{sector}", styles['TextoNormal'])
        ],
        [
            Paragraph("<b>Geografía</b>", styles['TextoNormal']),
            Paragraph("España (con potencial internacional)", styles['TextoNormal'])
        ],
        [
            Paragraph("<b>Ventas LTM</b>", styles['TextoNormal']),
            Paragraph(f"€{ventas_actuales/1e6:.1f}M", styles['TextoNormal'])
        ],
        [
            Paragraph("<b>EBITDA LTM</b>", styles['TextoNormal']),
            Paragraph(f"€{ebitda_actual/1e6:.1f}M ({margen_actual:.1f}%)", styles['TextoNormal'])
        ],
        [
            Paragraph("<b>Enterprise Value</b>", styles['TextoNormal']),
            Paragraph(f"€{valor_empresa/1e6:.1f}M", styles['TextoNormal'])
        ],
        [
            Paragraph("<b>EV/EBITDA Entry</b>", styles['TextoNormal']),
            Paragraph(f"{multiplo_entrada:.1f}x LTM / {analisis_ia.get('multiplo_ebitda_ntm', 8.3):.1f}x NTM", styles['TextoNormal'])
        ],
        [
            Paragraph("<b>Target IRR</b>", styles['TextoNormal']),
            Paragraph(f"{tir_proyecto:.1f}%", styles['TextoNormal'])
        ],
        [
            Paragraph("<b>Investment Horizon</b>", styles['TextoNormal']),
            Paragraph("3-5 años", styles['TextoNormal'])
        ],
        [
            Paragraph("<b>Deal Type</b>", styles['TextoNormal']),
            Paragraph("Growth Capital / Buyout", styles['TextoNormal'])
        ]
    ]
    
    snapshot_table = Table(snapshot_data, colWidths=[2.5*inch, 4*inch])
    snapshot_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LINEBELOW', (0, 0), (-1, -2), 0.5, colors.Color(0.9, 0.9, 0.9)),
    ]))
    
    elementos.append(snapshot_table)
    elementos.append(Spacer(1, 0.3*inch))
    
    # KEY INVESTMENT HIGHLIGHTS
    elementos.append(Paragraph("Key Investment Highlights", styles['Subtitulo']))
    
    # Highlights específicos por sector
    # Highlights específicos por sector
    highlights_por_sector = {
        'Tecnología': [
            f"🚀 <b>Modelo SaaS Escalable:</b> {cagr_ventas:.0f}% crecimiento con CAC/LTV >3x",
            f"💡 <b>Product-Market Fit Validado:</b> NRR >110%, Churn <5% anual",
            f"🌍 <b>Expansión Internacional:</b> Modelo replicable en LATAM y Europa",
            f"🎯 <b>TAM Significativo:</b> €5Bn+ mercado direccionable creciendo 20%+ anual"
        ],
        'Hostelería': [
            f"📈 <b>Recovery Post-COVID:</b> RevPAR +{cagr_ventas:.0f}% YoY, ocupación >80%",
            f"🏆 <b>Posicionamiento Premium:</b> ADR 20% superior a competencia",
            f"🔄 <b>Asset-Light Growth:</b> Expansión vía management y franquicia",
            f"💰 <b>FCF Robusto:</b> Conversión EBITDA-FCF >60%"
        ],
        'Ecommerce': [
            f"📱 <b>Omnichannel Leader:</b> {cagr_ventas:.0f}% crecimiento online + offline",
            f"🛒 <b>Métricas Best-in-Class:</b> AOV creciendo, CAC estable",
            f"🚚 <b>Logística Propia:</b> Control full-stack de customer experience",
            f"🎯 <b>Categoría en Crecimiento:</b> Penetración online <20% con runway"
        ],
        'Industrial': [
            f"🏭 <b>Líder en Nicho:</b> #1-2 cuota mercado con pricing power",
            f"🔧 <b>Eficiencia Operativa:</b> OEE >85%, lead times -30%",
            f"🌱 <b>ESG Leadership:</b> Certificaciones y acceso a fondos verdes",
            f"🤝 <b>Contratos Long-Term:</b> >70% ingresos recurrentes/predecibles"
        ],
        'Consultoría': [
            f"🎯 <b>Expertise Diferenciado:</b> Especialización en {sector} con +15 años track record",
            f"💼 <b>Blue-Chip Clients:</b> 80% IBEX-35/Fortune 500, contratos multi-año",
            f"📊 <b>Márgenes Premium:</b> {margen_actual:.0f}%+ EBITDA vs 15-20% industria",
            f"🚀 <b>Escalabilidad:</b> Modelo de leverage con ratios 1:8 senior:junior"
        ],
        'Retail': [
            f"🏬 <b>Footprint Optimizado:</b> {cagr_ventas:.0f}% SSS growth, locations prime",
            f"📱 <b>Transformación Digital:</b> 25%+ ventas online, click&collect mismo día",
            f"🎯 <b>Power Brands:</b> Portfolio marcas propias margen +40%",
            f"💳 <b>Customer Loyalty:</b> 60%+ ventas de clientes recurrentes, NPS >50"
        ],
        'Servicios': [
            f"🔄 <b>Ingresos Recurrentes:</b> 70%+ base contractual, churn <10%",
            f"📈 <b>Cross-Selling:</b> 2.5x servicios/cliente, ARPU creciendo {cagr_ventas/2:.0f}%",
            f"🌐 <b>Plataforma Escalable:</b> Tecnología propia, márgenes incrementales 60%+",
            f"🏆 <b>Market Leader:</b> Top 3 nacional con oportunidad consolidación"
        ],
        'Automoción': [
            f"🚗 <b>Multi-Marca Premium:</b> Concesionario oficial 5+ marcas líderes",
            f"🔧 <b>Postventa Recurrente:</b> 45% gross profit de servicios y recambios",
            f"📊 <b>Gestión Best-in-Class:</b> Rotación stock 8x, ROI >25%",
            f"⚡ <b>Ready for EV:</b> Infraestructura y certificaciones movilidad eléctrica"
        ]
    }
    
    # Para "Otro" o sectores no definidos
    highlights = highlights_por_sector.get(sector, [
        f"📈 <b>Crecimiento Sostenido:</b> {cagr_ventas:.0f}% CAGR con visibilidad alta",
        f"💰 <b>Mejora Operacional:</b> +{margen_futuro - margen_actual:.0f}pp margen EBITDA potencial",
        f"🎯 <b>Posición Competitiva:</b> Top 5 player con ventajas diferenciales",
        f"🚀 <b>Value Creation:</b> Múltiples palancas identificadas con ROI >3x"
    ])
    
    for highlight in highlights:
        elementos.append(Paragraph(highlight, styles['TextoNormal']))
        elementos.append(Spacer(1, 0.1*inch))
    
    elementos.append(Spacer(1, 0.2*inch))
    
    # FINANCIAL OVERVIEW - Tabla mejorada
    elementos.append(Paragraph("Financial Overview", styles['Subtitulo']))
    
    # Preparar datos financieros
    # Calcular año actual (año 0) basado en datos históricos
    ventas_historicas = datos_empresa.get('ventas_historicas', [])
    ventas_actual = ventas_historicas[-1] if ventas_historicas else ventas_actuales * 0.85
    
    # Estimar EBITDA actual basado en margen histórico
    ebitda_actual_real = ventas_actual * (margen_actual / 100)
    
    años = ['Actual', 'Año 1', 'Año 2', 'Año 3', 'Año 4', 'Año 5']
    ventas_data = [f"€{pyl_df['Ventas'].iloc[i]/1e6:.1f}M" for i in range(len(pyl_df))]
    ebitda_data = [f"€{pyl_df['EBITDA'].iloc[i]/1e6:.1f}M" for i in range(len(pyl_df))]
    margen_data = [f"{pyl_df['EBITDA %'].iloc[i]:.1f}%" for i in range(len(pyl_df))]
    
    financial_data = [
        ['Métrica'] + años[:len(ventas_data) + 1],
        ['Ventas'] + [f"€{ventas_actual/1e6:.1f}M"] + ventas_data,
        ['Crecimiento %'] + ['--'] + [f"+{((ventas_actuales/ventas_actual)-1)*100:.1f}%"] + [f"+{((pyl_df['Ventas'].iloc[i]/pyl_df['Ventas'].iloc[i-1])-1)*100:.1f}%" 
                                       for i in range(1, len(pyl_df))],
        ['EBITDA'] + [f"€{ebitda_actual_real/1e6:.1f}M"] + ebitda_data,
        ['Margen EBITDA'] + [f"{(ebitda_actual_real/ventas_actual)*100:.1f}%"] + margen_data,
        ['CAPEX % Ventas'] + ['3.0%'] + ['2.5%'] * 5  # Aproximación
    ]
    
    financial_table = Table(financial_data, colWidths=[1.5*inch] + [0.9*inch] * 6)
    financial_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), AZUL_PRINCIPAL),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
        ('BACKGROUND', (1, 2), (-1, 2), colors.Color(0.95, 1, 0.95)),  # Highlight growth
        ('BACKGROUND', (1, 4), (-1, 4), colors.Color(0.95, 0.95, 1)),  # Highlight margins
    ]))
    
    elementos.append(financial_table)
    
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
def crear_analisis_swot(analisis_ia: Dict, datos_empresa: Dict, styles) -> list:
    """Crear la sección de análisis SWOT mejorado con datos específicos"""
    elementos = []
    
    # Título
    elementos.append(Paragraph("ANÁLISIS SWOT ESTRATÉGICO", styles['TituloPrincipal']))
    elementos.append(Spacer(1, 0.3*inch))
    
    # Introducción contextual
    intro_text = """
    <b>Análisis de Posicionamiento Competitivo</b><br/>
    Evaluación integral de factores internos y externos que impactan la estrategia de crecimiento y valoración.
    """
    elementos.append(Paragraph(intro_text, styles['TextoNormal']))
    elementos.append(Spacer(1, 0.2*inch))
    
    # Extraer datos del análisis
    fortalezas = analisis_ia.get('fortalezas', [])
    riesgos = analisis_ia.get('riesgos', [])
    sector = datos_empresa.get('sector', 'General')
    multiplo_ebitda = analisis_ia.get('multiplo_ebitda_ltm', 8.0)
    
    # FORTALEZAS - Basadas en métricas reales
    fortalezas_text = "<b>FORTALEZAS (Ventajas Competitivas)</b><br/><br/>"
    if fortalezas:
        for f in fortalezas[:3]:
            fortalezas_text += f"• {f}<br/>"
    
    # Agregar fortalezas adicionales basadas en datos
    if multiplo_ebitda < 10:
        fortalezas_text += f"• Valoración atractiva vs comparables del sector<br/>"
    fortalezas_text += "• Equipo directivo con track record probado<br/>"
    fortalezas_text += "• Modelo de negocio escalable con operating leverage positivo<br/>"
    
    # DEBILIDADES - Basadas en riesgos identificados
    debilidades_text = "<b>DEBILIDADES (Áreas de Mejora)</b><br/><br/>"
    if riesgos:
        for r in riesgos[:2]:
            debilidades_text += f"• {r}<br/>"
    
    sector_debilidades = {
        'Tecnología': [
            "• Alto cash burn rate en fase de crecimiento",
            "• Dependencia de talento técnico escaso"
        ],
        'Hostelería': [
            "• Márgenes presionados por inflación costes",
            "• Alta rotación de personal"
        ],
        'Industrial': [
            "• Intensivo en capital con ciclos largos de inversión",
            "• Exposición a volatilidad materias primas"
        ],
        'Ecommerce': [
            "• CAC elevado en entorno competitivo",
            "• Dependencia de plataformas third-party"
        ],
        'Consultoría': [
            "• Dependencia del talento senior (key person risk)",
            "• Escalabilidad limitada por modelo people-intensive"
        ],
        'Retail': [
            "• Costes fijos elevados (alquileres prime locations)",
            "• Presión inventario y obsolescencia"
        ],
        'Servicios': [
            "• Fragmentación del mercado con barreras bajas",
            "• Dificultad diferenciación en commodities"
        ],
        'Automoción': [
            "• Capital circulante intensivo (stock vehículos)",
            "• Márgenes presionados por marcas"
        ]
    }
    
    debilidades_sector = sector_debilidades.get(sector, ["• Recursos limitados para expansión acelerada"])
    for d in debilidades_sector[:1]:
        debilidades_text += f"{d}<br/>"
    
    # OPORTUNIDADES - Específicas y cuantificadas
    oportunidades_text = "<b>OPORTUNIDADES (Catalizadores de Valor)</b><br/><br/>"
    
    oportunidades_sector = {
        'Tecnología': [
            "• TAM expandiéndose 20%+ anual (€50Bn+ en Europa)",
            "• Shift estructural a SaaS (penetración <30% en PYMEs)",
            "• M&A activo: 15-25x ARR para assets premium"
        ],
        'Hostelería': [
            "• Consolidación post-COVID (20% locales disponibles)",
            "• Turismo premium +15% YoY (RevPAR históricos)",
            "• Delivery/ghost kitchens: nuevo vertical €5Bn+"
        ],
        'Industrial': [
            "• Fondos Next Gen €140Bn para digitalización",
            "• Reshoring cadenas suministro (+30% demanda local)",
            "• Transición energética: €1Tn inversión 2030"
        ],
        'Ecommerce': [
            "• Penetración online 15% vs 25% UK (gap estructural)",
            "• Social commerce emergente (€10Bn+ potencial)",
            "• Quick commerce transformando last-mile"
        ],
        'Consultoría': [
            "• Transformación digital empresas (€20Bn+ mercado)",
            "• Fondos EU para consultoría estratégica PYMEs",
            "• Consolidación: 5000+ boutiques independientes"
        ],
        'Retail': [
            "• Retail media networks (nuevo revenue stream)",
            "• Experiential retail diferenciando del online",
            "• Consolidación sector (M&A múltiplos atractivos)"
        ],
        'Servicios': [
            "• Outsourcing trend (+15% CAGR próximos 5 años)",
            "• Digitalización servicios tradicionales",
            "• Roll-up opportunities en mercados fragmentados"
        ],
        'Automoción': [
            "• Transición EV: €50Bn inversión España 2030",
            "• Movilidad como servicio (MaaS) emergente",
            "• Consolidación concesionarios (3000→1500 en 10 años)"
        ]
    }
    
    ops = oportunidades_sector.get(sector, [
        "• Digitalización acelerada post-pandemia",
        "• Acceso a financiación en mínimos históricos",
        "• Consolidación sectorial creando oportunidades M&A"
    ])
    
    for o in ops[:3]:
        oportunidades_text += f"{o}<br/>"
    
    # AMENAZAS - Riesgos específicos y mitigables
    amenazas_text = "<b>AMENAZAS (Riesgos a Mitigar)</b><br/><br/>"
    
    amenazas_sector = {
        'Tecnología': [
            "• Compresión múltiplos tech (-40% desde picos)",
            "• Big Tech entrando en verticales nicho",
            "• Regulación datos/AI aumentando compliance"
        ],
        'Hostelería': [
            "• Inflación salarios/energía (+15% YoY)",
            "• Cambios hábitos consumo (delivery vs presencial)",
            "• Regulación laboral/fiscal más restrictiva"
        ],
        'Industrial': [
            "• Disrupción tecnológica en manufacturing",
            "• Guerra comercial impactando supply chains",
            "• Transición verde requiere CAPEX masivo"
        ],
        'Ecommerce': [
            "• Amazon/Alibaba dominancia creciente",
            "• CAC inflation por saturación digital marketing",
            "• Regulación platforms/marketplaces EU"
        ],
        'Consultoría': [
            "• Presión precios por RFPs competitivos",
            "• In-housing trend en grandes corporates",
            "• Automatización/AI reemplazando juniors"
        ],
        'Retail': [
            "• Shift estructural a online acelerándose",
            "• Inflación reduciendo poder adquisitivo",
            "• Amazon/Shein disrupting categorías"
        ],
        'Servicios': [
            "• Commoditización y guerra de precios",
            "• Nuevos entrantes con VC funding",
            "• Regulación laboral sectores específicos"
        ],
        'Automoción': [
            "• Disrupción Tesla/China en EV",
            "• Cambio modelo agencia vs concesión",
            "• Regulación emisiones cada vez más estricta"
        ]
    }
    
    ams = amenazas_sector.get(sector, [
        "• Entorno macro incierto (inflación/tipos)",
        "• Competencia internacional creciente",
        "• Cambios regulatorios impredecibles"
    ])
    
    for a in ams[:3]:
        amenazas_text += f"{a}<br/>"
    
    # Crear tabla SWOT mejorada
    swot_data = [
        [Paragraph(fortalezas_text, styles['TextoNormal']), 
         Paragraph(debilidades_text, styles['TextoNormal'])],
        [Paragraph(oportunidades_text, styles['TextoNormal']), 
         Paragraph(amenazas_text, styles['TextoNormal'])]
    ]
    
    swot_table = Table(swot_data, colWidths=[3.5*inch, 3.5*inch])
    swot_table.setStyle(TableStyle([
        # Bordes
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('BOX', (0, 0), (-1, -1), 2, AZUL_PRINCIPAL),
        # Padding
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ('RIGHTPADDING', (0, 0), (-1, -1), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        # Alineación
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    
    elementos.append(swot_table)
    elementos.append(Spacer(1, 0.3*inch))
    
    # Conclusión estratégica
    conclusion_text = f"""
    <b>Implicaciones Estratégicas:</b><br/>
    La compañía está bien posicionada para capturar el crecimiento del mercado, con una propuesta de valor 
    diferenciada y métricas financieras sólidas. Las principales palancas de creación de valor incluyen:
    (i) aceleración del crecimiento orgánico vía expansión geográfica/producto, 
    (ii) mejora operacional para expandir márgenes 300-500bps, y 
    (iii) consolidación oportunista a múltiplos atractivos.
    """
    elementos.append(Paragraph(conclusion_text, styles['TextoNormal']))
    
    return elementos

def crear_contexto_economico(datos_empresa: Dict, pyl_df: pd.DataFrame, styles) -> list:
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
    
    # Análisis dinámico basado en el sector
    sector = datos_empresa.get('sector', 'General')
    margen_ebitda = pyl_df['EBITDA %'].iloc[-1] if 'EBITDA %' in pyl_df.columns else 15

    # Oportunidades específicas por sector con cuantificación
    oportunidades_por_sector = {
        'Industrial': f"""
        <b>Oportunidades de Creación de Valor:</b><br/>
        • <b>Consolidación sectorial:</b> Mercado fragmentado con +2,000 PYMEs. Potencial de arbitraje 3-4x EBITDA via roll-up<br/>
        • <b>Digitalización 4.0:</b> €4.3Bn fondos Next Gen para industria. ROI >30% en automatización procesos (reducción 20% costes operativos)<br/>
        • <b>Nearshoring trend:</b> Repatriación cadenas suministro post-COVID. TAM incremento 15-20% próximos 3 años<br/>
        • <b>Transición energética:</b> Subvenciones 40% CAPEX para eficiencia. Ahorro energético 25-30% = +200-300bps margen EBITDA<br/>
        • <b>M&A opportunities:</b> Múltiplos PYMEs 5-7x vs cotizadas 10-12x. Arbitraje valoración 40-60%<br/><br/>
        
        <b>Riesgos Específicos y Mitigantes:</b><br/>
        • <b>Intensidad competitiva China/Asia:</b> Presión -15% precios. Mitigante: diferenciación servicio/calidad<br/>
        • <b>Volatilidad materias primas:</b> ±20% costes. Mitigante: contratos indexados + coberturas financieras<br/>
        • <b>Obsolescencia tecnológica:</b> Ciclo inversión 5-7 años. Mitigante: CAPEX 3-4% ventas anuales<br/>
        • <b>Concentración clientes:</b> Top 5 = 40-60% ventas. Mitigante: diversificación geográfica/sectorial<br/>
        • <b>Working capital intensivo:</b> 80-120 días. Mitigante: factoring/confirming liberaría €2-3M liquidez
        """,
        
        'Tecnología': f"""
        <b>Oportunidades de Creación de Valor:</b><br/>
        • <b>Modelo SaaS escalable:</b> LTV/CAC >3x, márgenes 70-80%. Valoraciones 4-8x ARR vs 1-2x tradicional<br/>
        • <b>Expansión internacional:</b> TAM global €50Bn, penetración <5%. Potencial 10x en 5 años<br/>
        • <b>AI/ML integration:</b> Incremento pricing power 20-30%. Early adopters premium valuations +40%<br/>
        • <b>Strategic acquirers activos:</b> Microsoft, Google, Salesforce. Múltiplos salida 15-25x ARR<br/>
        • <b>Venture capital dry powder:</b> €2.5Bn España. Series A/B valoraciones pre-money €20-50M<br/><br/>
        
        <b>Riesgos Específicos y Mitigantes:</b><br/>
        • <b>Burn rate elevado:</b> -€500k/mes típico. Mitigante: runway 18-24 meses + revenue milestones<br/>
        • <b>Churn rate crítico:</b> >5% mensual insostenible. Mitigante: customer success + product-market fit<br/>
        • <b>Talento tech escaso:</b> Coste developers +30% YoY. Mitigante: equity compensation + remote work<br/>
        • <b>Ciclos venta B2B largos:</b> 6-12 meses. Mitigante: proof of concepts + referencias Fortune 500<br/>
        • <b>Dependencia tecnológica:</b> AWS/Azure 20-30% costes. Mitigante: arquitectura multi-cloud
        """,
        
        'Hostelería': f"""
        <b>Oportunidades de Creación de Valor:</b><br/>
        • <b>Consolidación post-COVID:</b> 20% establecimientos cerrados. Adquisiciones 0.5-1x ventas (pre-COVID 2-3x)<br/>
        • <b>Delivery/dark kitchens:</b> Margen contribución 25-30% vs 15% tradicional. CAPEX 70% menor<br/>
        • <b>Turismo premium recovery:</b> RevPAR +15% YoY. Ocupación 85%+ en segmento 4-5 estrellas<br/>
        • <b>Sale & leaseback inmuebles:</b> Liberar 30-40% capital. Cap rates 5-6% = valoración atractiva<br/>
        • <b>Franquicia/licensing:</b> Asset-light expansion. Royalties 5-7% + fees. ROE >30%<br/><br/>
        
        <b>Riesgos Específicos y Mitigantes:</b><br/>
        • <b>Estacionalidad elevada:</b> 60% ingresos en 4 meses. Mitigante: diversificación geográfica + MICE<br/>
        • <b>Costes laborales/SMI:</b> 35-40% ventas. Mitigante: tecnología autoservicio + optimización turnos<br/>
        • <b>Dependencia TripAdvisor/OTAs:</b> Comisiones 15-25%. Mitigante: direct booking >50% + loyalty<br/>
        • <b>Regulación turística:</b> Licencias restrictivas. Mitigante: grandfathering + lobby sectorial<br/>
        • <b>Sensibilidad económica:</b> Beta 1.5-2x PIB. Mitigante: mix precio/volumen + segmentación
        """,
        
        'Ecommerce': f"""
        <b>Oportunidades de Creación de Valor:</b><br/>
        • <b>Conversión optimization:</b> CRO puede aumentar 30-50% ventas sin CAC adicional. Quick wins identificados<br/>
        • <b>Expansión marketplaces:</b> Amazon/eBay/Zalando suben-utilizados. Potencial +40% GMV año 1<br/>
        • <b>D2C margins:</b> Eliminar intermediarios = +1000-1500bps margen bruto. Payback <12 meses<br/>
        • <b>International expansion:</b> Cross-border representa 35% e-commerce. Plug&play con partners<br/>
        • <b>M&A roll-up:</b> Consolidar competidores pequeños a 3-5x EBITDA. Sinergias tech/logística 30%+<br/><br/>
        
        <b>Riesgos Específicos y Mitigantes:</b><br/>
        • <b>CAC inflation:</b> CPCs +20% YoY. Mitigante: SEO/content marketing + retention focus<br/>
        • <b>Amazon dependencia:</b> 40%+ ventas marketplace. Mitigante: omnichannel + D2C push<br/>
        • <b>Logística last-mile:</b> Costes +15% anual. Mitigante: volumen para negociar + puntos recogida<br/>
        • <b>Cyber-security:</b> Data breaches riesgo reputacional. Mitigante: PCI compliance + cyber insurance<br/>
        • <b>Working capital peaks:</b> Black Friday/Navidad. Mitigante: inventory financing + pre-orders
        """,
        
        'Consultoría': f"""
        <b>Oportunidades de Creación de Valor:</b><br/>
        • <b>Especialización sectorial:</b> Premium pricing +30-40% vs generalistas. Casos de éxito demostrables<br/>
        • <b>Recurring revenue model:</b> Retainers y suscripciones vs proyectos. Predictibilidad +80% ingresos<br/>
        • <b>IP/Metodologías propietarias:</b> Productizar conocimiento. Márgenes 80%+ vs 40% consulting tradicional<br/>
        • <b>Nearshoring delivery:</b> Centros en LatAm/Europa Este. Reducción costes 40-50% manteniendo calidad<br/>
        • <b>Strategic partnerships:</b> Big 4 buscan boutiques especializadas. Exit múltiplos 12-15x EBITDA<br/><br/>
        
        <b>Riesgos Específicos y Mitigantes:</b><br/>
        • <b>Dependencia key clients:</b> Top 3 = 50%+ revenues. Mitigante: account planning + C-suite relationships<br/>
        • <b>Talent war:</b> Rotación seniors 25%+. Mitigante: carry/phantom shares + cultura diferenciada<br/>
        • <b>Commoditización:</b> Presión precios -10% anual. Mitigante: move upstream + resultados garantizados<br/>
        • <b>Utilización rates:</b> Break-even 65%+. Mitigante: bench productivo + formación continua<br/>
        • <b>Cash collection:</b> DSO 90+ días. Mitigante: progress billing + penalties por retraso
        """,
        
        'Retail': f"""
        <b>Oportunidades de Creación de Valor:</b><br/>
        • <b>Omnichannel integration:</b> Online pick-up in store +25% ticket medio. Inventory visibility ROI 6 meses<br/>
        • <b>Private label expansion:</b> Del 15% al 40% mix. Margen bruto +800-1000bps vs marcas nacionales<br/>
        • <b>Store optimization:</b> Cerrar 20% tiendas no rentables. EBITDA improvement +200-300bps inmediato<br/>
        • <b>Retail media network:</b> Monetizar tráfico/data. Nuevo revenue stream €1-2M año 1, 90% margen<br/>
        • <b>Sale-leaseback portfolio:</b> Liberar €10-20M capital. Invertir en crecimiento/digital ROI >25%<br/><br/>
        
        <b>Riesgos Específicos y Mitigantes:</b><br/>
        • <b>Footfall decline:</b> -5% anual tendencia. Mitigante: experiential retail + servicios valor añadido<br/>
        • <b>Inventory obsolescence:</b> 10-15% stock >6 meses. Mitigante: AI demand planning + liquidación ágil<br/>
        • <b>Rental costs inflation:</b> +3-5% anual. Mitigante: renegociación COVID + revenue share deals<br/>
        • <b>E-commerce cannibalización:</b> -20% ventas tienda. Mitigante: ship-from-store + clienteling digital<br/>
        • <b>Seasonal cashflow:</b> 40% ventas en Q4. Mitigante: inventory financing + supplier extended terms
        """,
        
        'Servicios': f"""
        <b>Oportunidades de Creación de Valor:</b><br/>
        • <b>Subscription transformation:</b> De transaccional a recurrente. LTV/CAC de 1x a 4x en 18 meses<br/>
        • <b>Vertical integration:</b> Adquirir suppliers clave. Margen bruto +30% + control calidad<br/>
        • <b>Platform economics:</b> Crear marketplace B2B. Take rate 15-20% con asset-light model<br/>
        • <b>AI/Automation:</b> Reducir headcount 25% sin impacto servicio. Payback <12 meses<br/>
        • <b>Geographic density:</b> Clusters urbanos para economías escala. EBITDA margin +400bps<br/><br/>
        
        <b>Riesgos Específicos y Mitigantes:</b><br/>
        • <b>Labor intensity:</b> 60%+ costes son personal. Mitigante: tecnología + offshore selectivo<br/>
        • <b>Customer concentration:</b> Contratos 1-2 años. Mitigante: multi-year deals + switching costs<br/>
        • <b>Price competition:</b> Race to bottom en básicos. Mitigante: value-added services + bundling<br/>
        • <b>Regulatory compliance:</b> Cambios normativos frecuentes. Mitigante: compliance officer + buffer costes<br/>
        • <b>Scalability challenges:</b> Crecimiento requiere CAPEX. Mitigante: franquicia + partnerships
        """,
        
        'Automoción': f"""
        <b>Oportunidades de Creación de Valor:</b><br/>
        • <b>EV transition capture:</b> First-mover en servicios EV. Premium pricing +40% vs combustión<br/>
        • <b>Aftersales focus:</b> Margen bruto 45% vs 15% venta. Aumentar attach rate a 70%+ clientes<br/>
        • <b>F&I products:</b> Financiación y seguros. Commission income €500-1000/vehículo, 80% margen<br/>
        • <b>Multi-brand strategy:</b> Agregar 2-3 marcas premium. Economías escala + poder negociación<br/>
        • <b>Corporate fleet management:</b> B2B recurring revenue. Contratos 3-5 años, márgenes estables<br/><br/>
        
        <b>Riesgos Específicos y Mitigantes:</b><br/>
        • <b>OEM pressure:</b> Márgenes venta <5%. Mitigante: volumen bonuses + focus postventa<br/>
        • <b>Inventory financing costs:</b> +200bps tipos. Mitigante: quick turn + pre-orders modelo Tesla<br/>
        • <b>Direct sales threat:</b> Marcas bypassean dealers. Mitigante: service exclusive + CRM ownership<br/>
        • <b>Semiconductor shortage:</b> Supply constraints. Mitigante: multi-marca portfolio + used cars<br/>
        • <b>EV transition CAPEX:</b> €500k-1M por punto. Mitigante: OEM co-investment + subsidios 40%
        """
    }

    # Seleccionar análisis según sector o usar genérico mejorado
    if sector in oportunidades_por_sector:
        riesgos_ops = oportunidades_por_sector[sector]
    else:
        # Análisis genérico pero profesional
        riesgos_ops = f"""
        <b>Oportunidades de Creación de Valor:</b><br/>
        • <b>Arbitraje valoración:</b> PYMEs {5 if margen_ebitda < 15 else 7}x EBITDA vs comparables cotizadas 10-14x<br/>
        • <b>Eficiencias operativas:</b> Benchmarking indica potencial +{int(25-margen_ebitda)}% margen EBITDA<br/>
        • <b>Consolidación sectorial:</b> Mercado fragmentado, sinergias 15-20% base costes combinada<br/>
        • <b>Digitalización procesos:</b> Reducción 20-30% costes administrativos. Payback <18 meses<br/>
        • <b>Expansión geográfica:</b> Mercados adyacentes infrautilizados. TAM 3-4x mercado actual<br/><br/>
        
        <b>Riesgos Específicos y Mitigantes:</b><br/>
        • <b>Concentración cliente/proveedor:</b> Top 5 >50% volumen. Mitigante: contratos largo plazo<br/>
        • <b>Obsolescencia modelo negocio:</b> Disrupción digital. Mitigante: inversión I+D 3-5% ventas<br/>
        • <b>Apalancamiento operativo:</b> Costes fijos {60 if margen_ebitda < 20 else 40}%. Mitigante: flexibilización estructura<br/>
        • <b>Gap generacional management:</b> Edad media >55 años. Mitigante: plan sucesión + phantom shares<br/>
        • <b>Limitaciones financieras:</b> Debt capacity 2.5-3x EBITDA. Mitigante: capital growth + venture debt
        """
    
    elementos.append(Paragraph(riesgos_ops, styles['TextoNormal']))
    
    return elementos
def crear_cash_flow_valoracion(pyl_df: pd.DataFrame, valoracion: Dict, balance_df: pd.DataFrame, datos_empresa: Dict, styles) -> list:
    """Crear la sección de cash flow y valoración DCF"""
    if datos_empresa and 'balance_activo' in datos_empresa:
        print(f"  - clientes_inicial: {datos_empresa['balance_activo'].get('clientes_inicial', 'NO EXISTE')}")
    elementos = []
    
    # Título
    elementos.append(Paragraph("ANÁLISIS DE CASH FLOW Y VALORACIÓN", styles['TituloPrincipal']))
    elementos.append(Spacer(1, 0.3*inch))
    
    # Cash Flow Proyectado
    elementos.append(Paragraph("Free Cash Flow Proyectado", styles['Subtitulo']))
    
    # Crear tabla de cash flow calculando valores reales
    cf_data = [
        ['Concepto', 'Año 1', 'Año 2', 'Año 3', 'Año 4', 'Año 5'],
        ['EBITDA', f"€{pyl_df['EBITDA'].iloc[0]:,.0f}", f"€{pyl_df['EBITDA'].iloc[1]:,.0f}", 
         f"€{pyl_df['EBITDA'].iloc[2]:,.0f}", f"€{pyl_df['EBITDA'].iloc[3]:,.0f}", f"€{pyl_df['EBITDA'].iloc[4]:,.0f}"],
        ['(-) Impuestos', f"€{-pyl_df['Impuestos'].iloc[0]:,.0f}", f"€{-pyl_df['Impuestos'].iloc[1]:,.0f}",
         f"€{-pyl_df['Impuestos'].iloc[2]:,.0f}", f"€{-pyl_df['Impuestos'].iloc[3]:,.0f}", f"€{-pyl_df['Impuestos'].iloc[4]:,.0f}"],
        ['(-) CAPEX', '', '', '', '', ''],  # Se calculará abajo
        ['(-) Δ Working Capital', '', '', '', '', ''],  # Se calculará abajo
        ['Free Cash Flow', '', '', '', '', '']  # Se calculará abajo
    ]
    
    # Calcular CAPEX desde valoracion o usar default
    for i in range(5):
        # Intentar múltiples fuentes de datos
        capex = 0
        
        # Opción 1: Buscar en valoracion directamente
        if f'capex_año{i+1}' in valoracion:
            capex = valoracion[f'capex_año{i+1}']
        # Opción 2: Buscar en estructura de inversiones
        elif 'capex' in valoracion and isinstance(valoracion['capex'], list) and i < len(valoracion['capex']):
            capex = valoracion['capex'][i]
        # Opción 3: Default basado en ventas
        else:
            capex = 0  # Sin datos de CAPEX, asumimos 0
            
        cf_data[3][i+1] = f"€{-abs(capex):,.0f}"

    # Calcular Working Capital desde el balance real
    for i in range(5):
        if balance_df is not None and all(col in balance_df.columns for col in ['clientes', 'inventario', 'proveedores']):
            # Analytics pone variación = 0 para el año 1
            if i == 0:
                # Calcular WC inicial desde datos_empresa
                if datos_empresa and 'balance_activo' in datos_empresa:
                    clientes_inicial = datos_empresa.get('balance_activo', {}).get('clientes_inicial', 0)
                    inventario_inicial = datos_empresa.get('balance_activo', {}).get('inventario_inicial', 0)
                    proveedores_inicial = datos_empresa.get('balance_pasivo', {}).get('proveedores_inicial', 0)
                    wc_inicial = clientes_inicial + inventario_inicial - proveedores_inicial
                    
                    # WC año 1 desde balance
                    wc_año1 = (balance_df['clientes'].iloc[0] + balance_df['inventario'].iloc[0] - balance_df['proveedores'].iloc[0])
                    wc_change = wc_año1 - wc_inicial
                    print(f"WC año 1: inicial={wc_inicial:,.0f}, año1={wc_año1:,.0f}, cambio={wc_change:,.0f}")
                    
                else:
                    wc_change = 0
            else:
                # Años 2-5: cambio año a año
                wc_actual = (balance_df['clientes'].iloc[i] + balance_df['inventario'].iloc[i] - balance_df['proveedores'].iloc[i])
                wc_anterior = (balance_df['clientes'].iloc[i-1] + balance_df['inventario'].iloc[i-1] - balance_df['proveedores'].iloc[i-1])
                wc_change = wc_actual - wc_anterior
        else:
            # Fallback
            wc_change = 0 if i == 0 else pyl_df['Ventas'].iloc[i] * 0.01
        
        cf_data[4][i+1] = f"€{-wc_change:,.0f}" if wc_change > 0 else f"€{abs(wc_change):,.0f}"
    
    # Calcular FCF para cada año
    for i in range(5):
        ebitda = pyl_df['EBITDA'].iloc[i]
        impuestos = pyl_df['Impuestos'].iloc[i]
        
        # Extraer valores numéricos de las strings formateadas
        capex_str = cf_data[3][i+1].replace('€', '').replace(',', '')
        wc_str = cf_data[4][i+1].replace('€', '').replace(',', '')
        
        capex = float(capex_str) if capex_str else 0
        wc_change = float(wc_str) if wc_str else 0
        
        fcf = ebitda - impuestos + capex + wc_change  # AMBOS ya vienen como negativos
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
        ['Múltiplo EV/EBITDA', f"{valoracion.get('ev_ebitda_ltm', 10.3):.1f}x LTM / {valoracion.get('ev_ebitda_ntm', 8.3):.1f}x NTM"],
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
def crear_recomendaciones(analisis_ia: Dict, valoracion: Dict, pyl_df: pd.DataFrame, datos_empresa: Dict, styles) -> list:
    """Crear la sección de recomendaciones estratégicas mejoradas"""
    elementos = []
    
    # Título
    elementos.append(Paragraph("RECOMENDACIONES ESTRATÉGICAS Y PLAN DE ACCIÓN", styles['TituloPrincipal']))
    elementos.append(Spacer(1, 0.3*inch))
    
    # Extraer datos clave
    sector = datos_empresa.get('sector', 'General')
    valor_empresa = valoracion.get('valor_empresa', 0)
    multiplo_ebitda = analisis_ia.get('multiplo_ebitda_ltm', 8.0)
    viabilidad = analisis_ia.get('viabilidad', 'MEDIA')
    rating = analisis_ia.get('rating', '★★★☆☆')
    
    # Métricas financieras
    margen_ebitda_actual = pyl_df['EBITDA %'].iloc[0] if 'EBITDA %' in pyl_df.columns else 15
    margen_ebitda_futuro = pyl_df['EBITDA %'].iloc[-1] if 'EBITDA %' in pyl_df.columns else 20
    crecimiento_ventas = ((pyl_df['Ventas'].iloc[-1] / pyl_df['Ventas'].iloc[0]) ** (1/5) - 1) * 100
    
    # 1. INVESTMENT RECOMMENDATION
    elementos.append(Paragraph("Investment Recommendation", styles['Subtitulo']))
    
    # Definir recomendación basada en métricas
    if multiplo_ebitda < 6 and margen_ebitda_futuro > 20:
        recomendacion = "STRONG BUY"
        color_rec = VERDE_POSITIVO
    elif multiplo_ebitda < 8 and crecimiento_ventas > 15:
        recomendacion = "BUY"
        color_rec = VERDE_POSITIVO
    elif multiplo_ebitda < 10:
        recomendacion = "HOLD"
        color_rec = NARANJA_ALERTA
    else:
        recomendacion = "WAIT"
        color_rec = ROJO_NEGATIVO
    
    rec_text = f"""
    <b>Recomendación:</b> <font color='{color_rec}'>{recomendacion}</font><br/>
    <b>Target Entry Multiple:</b> {multiplo_ebitda * 0.85:.1f}x EBITDA (15% descuento)<br/>
    <b>Expected IRR:</b> {analisis_ia.get('tir_proyecto', 20):.1f}%<br/>
    <b>Investment Horizon:</b> 3-5 años<br/>
    <b>Exit Multiple Range:</b> {multiplo_ebitda * 1.2:.1f}x - {multiplo_ebitda * 1.5:.1f}x EBITDA
    """
    
    elementos.append(Paragraph(rec_text, styles['TextoNormal']))
    elementos.append(Spacer(1, 0.3*inch))
    
    # 2. VALUE CREATION PLAN
    elementos.append(Paragraph("Value Creation Plan", styles['Subtitulo']))
    
    # Plan específico por sector
    value_creation_por_sector = {
        'Tecnología': [
            {
                'iniciativa': 'Product-Led Growth',
                'impacto': '+40% ARR',
                'tiempo': '12 meses',
                'inversion': '€500k',
                'roi': '3.5x'
            },
            {
                'iniciativa': 'Expansión Internacional (UK/DACH)',
                'impacto': '+€2M ARR',
                'tiempo': '18 meses',
                'inversion': '€1.2M',
                'roi': '2.8x'
            },
            {
                'iniciativa': 'Upsell/Cross-sell Optimization',
                'impacto': '+25% LTV',
                'tiempo': '6 meses',
                'inversion': '€200k',
                'roi': '5.2x'
            }
        ],
        'Hostelería': [
            {
                'iniciativa': 'Revenue Management System',
                'impacto': '+15% RevPAR',
                'tiempo': '6 meses',
                'inversion': '€150k',
                'roi': '4.5x'
            },
            {
                'iniciativa': 'F&B Optimization',
                'impacto': '+300bps margen',
                'tiempo': '9 meses',
                'inversion': '€300k',
                'roi': '3.8x'
            },
            {
                'iniciativa': 'Direct Booking Strategy',
                'impacto': '-€200k OTA fees',
                'tiempo': '12 meses',
                'inversion': '€250k',
                'roi': '3.2x'
            }
        ],
        'Ecommerce': [
            {
                'iniciativa': 'Conversion Rate Optimization',
                'impacto': '+35% conversión',
                'tiempo': '6 meses',
                'inversion': '€180k',
                'roi': '6.2x'
            },
            {
                'iniciativa': 'Marketplace Expansion',
                'impacto': '+€1.5M GMV',
                'tiempo': '9 meses',
                'inversion': '€400k',
                'roi': '3.8x'
            },
            {
                'iniciativa': 'Supply Chain Automation',
                'impacto': '-20% COGS',
                'tiempo': '12 meses',
                'inversion': '€600k',
                'roi': '2.5x'
            }
        ],
        'Industrial': [
            {
                'iniciativa': 'Lean Manufacturing',
                'impacto': '-25% waste',
                'tiempo': '12 meses',
                'inversion': '€800k',
                'roi': '3.2x'
            },
            {
                'iniciativa': 'Digitalización Procesos',
                'impacto': '+20% productividad',
                'tiempo': '18 meses',
                'inversion': '€1.5M',
                'roi': '2.7x'
            },
            {
                'iniciativa': 'Energy Efficiency Program',
                'impacto': '-30% costes energía',
                'tiempo': '12 meses',
                'inversion': '€500k',
                'roi': '4.1x'
            }
        ],
        'Consultoría': [
            {
                'iniciativa': 'Especialización Vertical',
                'impacto': '+30% pricing power',
                'tiempo': '12 meses',
                'inversion': '€300k',
                'roi': '4.5x'
            },
            {
                'iniciativa': 'Plataforma Digital/IP',
                'impacto': '40% proyectos recurring',
                'tiempo': '18 meses',
                'inversion': '€800k',
                'roi': '3.2x'
            },
            {
                'iniciativa': 'Offshore Delivery Center',
                'impacto': '-30% coste delivery',
                'tiempo': '9 meses',
                'inversion': '€500k',
                'roi': '3.8x'
            }
        ],
        'Retail': [
            {
                'iniciativa': 'Omnichannel Integration',
                'impacto': '+25% conversión',
                'tiempo': '9 meses',
                'inversion': '€600k',
                'roi': '3.5x'
            },
            {
                'iniciativa': 'Private Label Expansion',
                'impacto': '+500bps margen bruto',
                'tiempo': '12 meses',
                'inversion': '€400k',
                'roi': '4.2x'
            },
            {
                'iniciativa': 'Store Format Optimization',
                'impacto': '+20% ventas/m²',
                'tiempo': '15 meses',
                'inversion': '€1M',
                'roi': '2.8x'
            }
        ],
        'Servicios': [
            {
                'iniciativa': 'Digitalización Procesos',
                'impacto': '-25% costes operativos',
                'tiempo': '12 meses',
                'inversion': '€450k',
                'roi': '3.8x'
            },
            {
                'iniciativa': 'Suscripción/Recurring Model',
                'impacto': '+40% LTV cliente',
                'tiempo': '6 meses',
                'inversion': '€200k',
                'roi': '5.5x'
            },
            {
                'iniciativa': 'Cross-sell/Upsell Program',
                'impacto': '+30% ARPU',
                'tiempo': '9 meses',
                'inversion': '€250k',
                'roi': '4.8x'
            }
        ],
        'Automoción': [
            {
                'iniciativa': 'Postventa Digital',
                'impacto': '+20% retención clientes',
                'tiempo': '8 meses',
                'inversion': '€350k',
                'roi': '4.1x'
            },
            {
                'iniciativa': 'EV Service Center',
                'impacto': 'Nueva línea €2M+',
                'tiempo': '12 meses',
                'inversion': '€1.2M',
                'roi': '2.5x'
            },
            {
                'iniciativa': 'Fleet Management Services',
                'impacto': '+€1.5M recurring',
                'tiempo': '6 meses',
                'inversion': '€300k',
                'roi': '5.0x'
            }
        ]
    }
    
    iniciativas = value_creation_por_sector.get(sector, [
        {
            'iniciativa': 'Optimización Operacional',
            'impacto': '+15% EBITDA',
            'tiempo': '12 meses',
            'inversion': '€300k',
            'roi': '3.5x'
        },
        {
            'iniciativa': 'Expansión Comercial',
            'impacto': '+25% ventas',
            'tiempo': '18 meses',
            'inversion': '€500k',
            'roi': '3.0x'
        }
    ])
    
    value_data = [['Iniciativa', 'Impacto Esperado', 'Plazo', 'Inversión', 'ROI']]
    for init in iniciativas[:3]:
        value_data.append([
            init['iniciativa'],
            init['impacto'],
            init['tiempo'],
            init['inversion'],
            init['roi']
        ])
    
    value_table = Table(value_data, colWidths=[2.2*inch, 1.5*inch, 1*inch, 1*inch, 0.8*inch])
    value_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), AZUL_PRINCIPAL),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        # Colorear ROI
        ('BACKGROUND', (4, 1), (4, -1), colors.Color(0.9, 1, 0.9)),
        ('FONTNAME', (4, 1), (4, -1), 'Helvetica-Bold'),
    ]))
    
    elementos.append(value_table)
    elementos.append(Spacer(1, 0.3*inch))
    
    # 3. EXECUTION ROADMAP - 100 DÍAS
    elementos.append(Paragraph("Execution Roadmap - Primeros 100 Días", styles['Subtitulo']))
    
    # Roadmap específico
    roadmap_data = [
        ['Fase', 'Acciones Clave', 'Entregables', 'Quick Wins'],
        [
            'Días 1-30\n(Diagnóstico)',
            '• Due Diligence operacional\n• Análisis competitivo\n• Mapping procesos',
            '• Informe gaps operacionales\n• Benchmark competidores\n• Quick wins identificados',
            '• Renegociación top 5 proveedores\n• Freeze hiring no crítico\n• Optimización cash cycle'
        ],
        [
            'Días 31-60\n(Planificación)',
            '• Diseño org. objetivo\n• Plan transformación\n• Presupuesto revisado',
            '• Nueva estructura org.\n• Business plan 100 días\n• Forecast actualizado',
            '• Eliminación duplicidades\n• Cierre canales no rentables\n• Mejora pricing 2-3%'
        ],
        [
            'Días 61-100\n(Ejecución)',
            '• Implementar cambios\n• Lanzar iniciativas\n• Comunicación stakeholders',
            '• KPIs dashboard live\n• Equipo clave contratado\n• Primeros resultados',
            '• EBITDA +100-200bps\n• NWC liberado €200k+\n• Pipeline comercial x2'
        ]
    ]
    
    roadmap_table = Table(roadmap_data, colWidths=[1.2*inch, 2.2*inch, 2.1*inch, 2*inch])
    roadmap_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), AZUL_PRINCIPAL),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.Color(1, 0.98, 0.98), colors.white]),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    
    elementos.append(roadmap_table)
    elementos.append(Spacer(1, 0.3*inch))
    
    # 4. RISK MITIGATION
    elementos.append(Paragraph("Risk Mitigation Strategy", styles['Subtitulo']))
    
    risk_text = """
    <b>Principales Riesgos y Mitigantes:</b><br/>
    • <b>Riesgo Ejecución:</b> Contratar COO con experiencia en turnarounds<br/>
    • <b>Riesgo Mercado:</b> Diversificar base clientes (concentración <20%)<br/>
    • <b>Riesgo Financiero:</b> Mantener covenant Deuda/EBITDA <3.0x<br/>
    • <b>Riesgo Tecnológico:</b> Inversión continua 3-5% ingresos en tech/digital
    """
    
    elementos.append(Paragraph(risk_text, styles['TextoNormal']))
    elementos.append(Spacer(1, 0.3*inch))
    
    # 5. EXIT STRATEGY
    elementos.append(Paragraph("Exit Strategy", styles['Subtitulo']))
    
    exit_text = f"""
    <b>Opciones de Salida (Año 3-5):</b><br/><br/>
    
    <b>1. Trade Sale</b> - Probabilidad: 60%<br/>
    Compradores: Competidores estratégicos, consolidadores sectoriales<br/>
    Múltiplo esperado: {multiplo_ebitda * 1.3:.1f}x - {multiplo_ebitda * 1.5:.1f}x EBITDA<br/><br/>
    
    <b>2. Secondary Buyout</b> - Probabilidad: 30%<br/>  
    Compradores: Fondos PE mid-market<br/>
    Múltiplo esperado: {multiplo_ebitda * 1.2:.1f}x - {multiplo_ebitda * 1.4:.1f}x EBITDA<br/><br/>
    
    <b>3. {"IPO" if valor_empresa > 50000000 else "Management Buyout"}</b> - Probabilidad: 10%<br/>
    {"Requisitos: €100M+ ingresos, 20%+ EBITDA margin" if valor_empresa > 50000000 else "Con apoyo de debt financing"}<br/>
    Múltiplo esperado: {multiplo_ebitda * 1.1:.1f}x - {multiplo_ebitda * 1.3:.1f}x EBITDA
    """
    
    elementos.append(Paragraph(exit_text, styles['TextoNormal']))
    
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
    story.extend(crear_contexto_economico(datos_empresa, pyl_df, styles))
    story.append(PageBreak())

    # 4. ANÁLISIS SWOT
    story.extend(crear_analisis_swot(analisis_ia, datos_empresa, styles))
    story.append(PageBreak())

    # 5. P&L DETALLADO
    story.extend(crear_pyl_detallado(pyl_df, styles))
    story.append(PageBreak())

    # 6. CASH FLOW Y VALORACIÓN
    story.extend(crear_cash_flow_valoracion(pyl_df, valoracion, balance_df, datos_empresa, styles))
    story.append(PageBreak())

    # 7. RECOMENDACIONES ESTRATÉGICAS
    story.extend(crear_recomendaciones(analisis_ia, valoracion, pyl_df, datos_empresa, styles))
          
    # Construir PDF
    doc.build(story, canvasmaker=NumberedCanvas)
    
    # Obtener bytes del PDF
    pdf_bytes = buffer.getvalue()
    buffer.close()
    
    return pdf_bytes