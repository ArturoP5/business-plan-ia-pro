import streamlit as st

def load_css():
    """Carga estilos CSS personalizados para la aplicación"""
    st.markdown("""
    <style>
        /* Variables de color */
        :root {
            --primary-color: #1E3A8A;
            --secondary-color: #3B82F6;
            --success-color: #10B981;
            --warning-color: #F59E0B;
            --error-color: #EF4444;
            --background: #F9FAFB;
            --card-bg: #FFFFFF;
            --text-primary: #111827;
            --text-secondary: #6B7280;
        }
        
        /* Fondo general */
        .stApp {
            background-color: var(--background);
        }
        
        /* Headers con gradiente */
        .main-header {
            background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%);
            padding: 2.5rem;
            border-radius: 20px;
            color: white;
            text-align: center;
            box-shadow: 0 10px 30px rgba(30, 58, 138, 0.2);
            margin-bottom: 2rem;
            animation: slideDown 0.6s ease-out;
        }
        
        /* Animación de entrada */
        @keyframes slideDown {
            from {
                opacity: 0;
                transform: translateY(-20px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        /* Cards de métricas */
        .metric-card {
            background: var(--card-bg);
            padding: 1.5rem;
            border-radius: 16px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            border: 1px solid rgba(0, 0, 0, 0.05);
            height: 100%;
        }
        
        .metric-card:hover {
            transform: translateY(-4px);
            box-shadow: 0 12px 24px rgba(0, 0, 0, 0.1);
            border-color: var(--primary-color);
        }
        
        .metric-value {
            font-size: 2.5rem;
            font-weight: 700;
            color: var(--primary-color);
            margin: 0.5rem 0;
        }
        
        .metric-label {
            font-size: 0.875rem;
            color: var(--text-secondary);
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        
        .metric-delta {
            font-size: 0.875rem;
            font-weight: 600;
            display: inline-flex;
            align-items: center;
            gap: 0.25rem;
            padding: 0.25rem 0.75rem;
            border-radius: 9999px;
            margin-top: 0.5rem;
        }
        
        .metric-delta.positive {
            color: var(--success-color);
            background-color: rgba(16, 185, 129, 0.1);
        }
        
        .metric-delta.negative {
            color: var(--error-color);
            background-color: rgba(239, 68, 68, 0.1);
        }
        
        /* Botones mejorados */
        .stButton > button {
            background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%);
            color: white;
            border: none;
            padding: 0.75rem 2rem;
            font-weight: 600;
            border-radius: 12px;
            transition: all 0.3s ease;
            box-shadow: 0 4px 6px rgba(30, 58, 138, 0.2);
            text-transform: none;
            font-size: 1rem;
        }
        
        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 12px rgba(30, 58, 138, 0.3);
        }
        
        /* Tabs personalizadas */
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
            background-color: rgba(255, 255, 255, 0.5);
            padding: 0.5rem;
            border-radius: 16px;
            backdrop-filter: blur(10px);
        }
        
        .stTabs [data-baseweb="tab"] {
            height: 45px;
            padding: 0 20px;
            background-color: transparent;
            border-radius: 12px;
            color: var(--text-secondary);
            font-weight: 500;
            transition: all 0.3s ease;
        }
        
        .stTabs [data-baseweb="tab"]:hover {
            background-color: rgba(30, 58, 138, 0.05);
            color: var(--primary-color);
        }
        
        .stTabs [aria-selected="true"] {
            background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%);
            color: white !important;
            font-weight: 600;
            box-shadow: 0 4px 12px rgba(30, 58, 138, 0.2);
        }
        
        /* Inputs mejorados */
        .stTextInput > div > div > input,
        .stNumberInput > div > div > input,
        .stSelectbox > div > div > select {
            border-radius: 10px;
            border: 2px solid #E5E7EB;
            padding: 0.75rem 1rem;
            transition: all 0.3s ease;
            background-color: var(--card-bg);
        }
        
        .stTextInput > div > div > input:focus,
        .stNumberInput > div > div > input:focus,
        .stSelectbox > div > div > select:focus {
            border-color: var(--primary-color);
            box-shadow: 0 0 0 3px rgba(30, 58, 138, 0.1);
        }
        
        /* Expanders mejorados */
        .streamlit-expanderHeader {
            background-color: rgba(30, 58, 138, 0.05);
            border-radius: 12px;
            font-weight: 600;
            transition: all 0.3s ease;
        }
        
        .streamlit-expanderHeader:hover {
            background-color: rgba(30, 58, 138, 0.1);
        }
        
        /* Tablas mejoradas */
        .dataframe {
            border: none !important;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
        }
        
        .dataframe thead th {
            background-color: var(--primary-color) !important;
            color: white !important;
            font-weight: 600;
            text-transform: uppercase;
            font-size: 0.75rem;
            letter-spacing: 0.05em;
        }
        
        .dataframe tbody tr:hover {
            background-color: rgba(30, 58, 138, 0.03);
        }
        
        /* Success/Error/Warning/Info boxes mejorados */
        .stAlert {
            border-radius: 12px;
            border: none;
            padding: 1rem 1.5rem;
            font-weight: 500;
        }
        
        .stSuccess {
            background-color: rgba(16, 185, 129, 0.1);
            color: #047857;
            border-left: 4px solid var(--success-color);
        }
        
        .stError {
            background-color: rgba(239, 68, 68, 0.1);
            color: #B91C1C;
            border-left: 4px solid var(--error-color);
        }
        
        .stWarning {
            background-color: rgba(245, 158, 11, 0.1);
            color: #B45309;
            border-left: 4px solid var(--warning-color);
        }
        
        .stInfo {
            background-color: rgba(59, 130, 246, 0.1);
            color: #1E40AF;
            border-left: 4px solid var(--secondary-color);
        }
        
        /* Sidebar mejorado */
        .css-1d391kg {
            background-color: var(--card-bg);
            border-right: 1px solid #E5E7EB;
        }
        
        /* Progress bar personalizada */
        .stProgress > div > div > div > div {
            background: linear-gradient(90deg, var(--primary-color) 0%, var(--secondary-color) 100%);
            border-radius: 10px;
        }
        
        /* Animación de carga */
        @keyframes pulse {
            0% {
                opacity: 1;
            }
            50% {
                opacity: 0.5;
            }
            100% {
                opacity: 1;
            }
        }
        
        .loading {
            animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
        }
        
        /* Títulos con estilo */
        h1 {
            color: var(--primary-color);
            font-weight: 700;
            margin-bottom: 1.5rem;
        }
        
        h2 {
            color: var(--text-primary);
            font-weight: 600;
            margin-bottom: 1rem;
        }
        
        h3 {
            color: var(--text-primary);
            font-weight: 600;
            margin-bottom: 0.75rem;
        }
        
        /* Divider personalizado */
        hr {
            margin: 2rem 0;
            border: none;
            border-top: 2px solid #E5E7EB;
        }
        
        /* Footer */
        .footer {
            text-align: center;
            padding: 2rem;
            margin-top: 4rem;
            border-top: 1px solid #E5E7EB;
            color: var(--text-secondary);
            font-size: 0.875rem;
        }
    </style>
    """, unsafe_allow_html=True)

def create_metric_card(label, value, delta=None, delta_color="normal"):
    """Crea una tarjeta de métrica personalizada"""
    delta_html = ""
    if delta:
        delta_class = "positive" if delta_color == "normal" and delta > 0 else "negative"
        delta_symbol = "↑" if delta > 0 else "↓"
        delta_html = f'<div class="metric-delta {delta_class}">{delta_symbol} {abs(delta):.1f}%</div>'
    
    return f"""
    <div class="metric-card">
        <div class="metric-label">{label}</div>
        <div class="metric-value">{value}</div>
        {delta_html}
    </div>
    """

def create_header(title, subtitle=None):
    """Crea un header con estilo"""
    subtitle_html = f"<p style='font-size: 1.2rem; margin-top: 0.5rem; opacity: 0.9;'>{subtitle}</p>" if subtitle else ""
    return f"""
    <div class="main-header">
        <h1 style='color: white; margin: 0; font-size: 2.5rem;'>{title}</h1>
        {subtitle_html}
    </div>
    """