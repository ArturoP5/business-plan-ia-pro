import numpy as np
import pandas as pd
from typing import Dict, Tuple, Optional
from datetime import datetime

class ValoracionProfesionalMejorada:
    """
    Sistema de valoración DCF profesional para PYMEs españolas
    Incluye ajustes por tamaño, sector y riesgo específico
    """
    
    def __init__(self):
        # Datos de mercado España (actualizables)
        self.tasa_libre_riesgo = 3.5  # Bono español 10 años
        self.prima_riesgo_mercado = 6.5  # Prima histórica España
        self.inflacion_esperada = 2.0  # BCE objetivo
        self.pib_potencial = 2.0  # España largo plazo
        
        # Betas sectoriales ajustados (Damodaran + ajuste España)
        self.betas_sector = {
            'Tecnología': 1.35,
            'Hostelería': 1.15,
            'Ecommerce': 1.25,
            'Consultoría': 1.10,
            'Retail': 0.95,
            'Servicios': 1.00,
            'Automoción': 1.20,
            'Industrial': 1.10,
            'Otro': 1.00
        }
        
        # Spreads de crédito por rating (puntos básicos)
        self.spreads_rating = {
            'AAA': 50, 'AA': 75, 'A': 100,
            'BBB': 150, 'BB': 300, 'B': 500,
            'CCC': 800, 'D': 1000
        }
    
    def calcular_wacc_completo(self, empresa_info: Dict, params_financieros: Dict) -> Tuple[float, Dict]:
        """
        Calcula WACC con metodología completa para PYMEs
        """
        # 1. Tasa libre de riesgo
        rf = self.tasa_libre_riesgo / 100
        
        # 2. Beta ajustado (método Blume)
        beta_sector = self.betas_sector.get(empresa_info.get('sector', 'Otro'), 1.0)
        beta_ajustado = 0.67 * beta_sector + 0.33 * 1.0
        
        # 3. Prima de riesgo de mercado
        prm = self.prima_riesgo_mercado / 100
        
        # 4. Prima por tamaño (Size Premium)
        ventas_anuales = params_financieros.get('ingresos_ultimo_año', 1000000)
        prima_tamaño = self._calcular_prima_tamaño(ventas_anuales) / 100
        
        # 5. Prima específica empresa
        prima_especifica = self._calcular_prima_especifica(empresa_info, params_financieros) / 100
        
        # 6. Coste del equity (CAPM modificado)
        ke = rf + beta_ajustado * prm + prima_tamaño + prima_especifica
        
        # 7. Coste de la deuda
        rating = params_financieros.get('rating', 'BB')
        spread = self.spreads_rating.get(rating, 300) / 10000  # Convertir a decimal
        kd_antes_imp = rf + spread
        tasa_impuestos = params_financieros.get('tasa_impuestos', 25) / 100
        kd = kd_antes_imp * (1 - tasa_impuestos)
        
        # 8. Estructura de capital
        deuda_total = params_financieros.get('deuda_total', 0)
        equity_total = params_financieros.get('equity_total', 1000000)
        
        # Si no hay equity positivo, usar valor mínimo
        if equity_total <= 0:
            equity_total = max(ventas_anuales * 0.2, 100000)
        
        valor_empresa = deuda_total + equity_total
        
        # Pesos
        wd = deuda_total / valor_empresa if valor_empresa > 0 else 0
        we = equity_total / valor_empresa if valor_empresa > 0 else 1
        
        # 9. WACC final
        wacc = we * ke + wd * kd
        
        # Retornar detalles para transparencia
        detalles = {
            'tasa_libre_riesgo': rf * 100,
            'beta_sector': beta_sector,
            'beta_ajustado': beta_ajustado,
            'prima_mercado': prm * 100,
            'prima_tamaño': prima_tamaño * 100,
            'prima_especifica': prima_especifica * 100,
            'coste_equity': ke * 100,
            'coste_deuda_antes_imp': kd_antes_imp * 100,
            'coste_deuda': kd * 100,
            'peso_equity': we,
            'peso_deuda': wd,
            'wacc': wacc * 100,
            'rating_implicito': rating
        }
        
        return wacc, detalles
    
    def _calcular_prima_tamaño(self, ventas_anuales: float) -> float:
        """
        Prima adicional por tamaño según estudios empíricos
        Basado en Ibbotson/Morningstar y ajustado para España
        """
        if ventas_anuales < 500_000:  # Micro empresa
            return 6.0
        elif ventas_anuales < 2_000_000:  # Muy pequeña
            return 4.5
        elif ventas_anuales < 10_000_000:  # Pequeña
            return 3.0
        elif ventas_anuales < 50_000_000:  # Mediana
            return 1.5
        elif ventas_anuales < 200_000_000:  # Mediana-grande
            return 0.5
        else:  # Grande
            return 0.0
    
    def _calcular_prima_especifica(self, empresa_info: Dict, params_financieros: Dict) -> float:
        """
        Prima por riesgos específicos de la empresa
        """
        prima = 0.0
        
        # 1. Concentración de clientes
        if empresa_info.get('cliente_principal_pct', 0) > 30:
            prima += 2.0  # Alta dependencia
        
        # 2. Antigüedad del negocio
        años_operando = datetime.now().year - empresa_info.get('año_fundacion', datetime.now().year)
        if años_operando < 3:
            prima += 3.0  # Startup
        elif años_operando < 7:
            prima += 1.5  # Joven
        
        # 3. Posición competitiva
        margen_ebitda = params_financieros.get('margen_ebitda', 10)
        margen_sector = self._obtener_margen_medio_sector(empresa_info.get('sector', 'Otro'))
        
        if margen_ebitda < margen_sector * 0.7:
            prima += 2.0  # Márgenes bajos
        elif margen_ebitda > margen_sector * 1.3:
            prima -= 1.0  # Márgenes superiores (reduce riesgo)
        
        # 4. Calidad del management (simplificado)
        if empresa_info.get('equipo_directivo_años_exp', 0) < 5:
            prima += 1.0
        
        # Límites
        return max(0, min(prima, 8.0))  # Entre 0% y 8%
    
    def calcular_tasa_crecimiento_terminal(self, sector: str, datos_macro: Optional[Dict] = None) -> float:
        """
        Calcula g perpetua considerando sector y macroeconomía
        """
        if datos_macro:
            inflacion = datos_macro.get('inflacion_esperada', self.inflacion_esperada)
            pib = datos_macro.get('pib_potencial', self.pib_potencial)
        else:
            inflacion = self.inflacion_esperada
            pib = self.pib_potencial
        
        # Factores de ajuste sectorial
        factores_sector = {
            'Tecnología': 1.3,    # Crece más que PIB
            'Hostelería': 0.9,    # Cerca del PIB
            'Ecommerce': 1.2,     # Superior al PIB
            'Consultoría': 1.0,   # Como el PIB
            'Retail': 0.8,        # Inferior al PIB
            'Servicios': 1.0,     # Como el PIB
            'Automoción': 0.9,    # Maduro
            'Industrial': 0.9,    # Maduro
            'Otro': 1.0
        }
        
        factor = factores_sector.get(sector, 1.0)
        
        # Crecimiento = Inflación + Crecimiento real ajustado
        crecimiento_real = (pib - inflacion) * factor
        g = inflacion + crecimiento_real
        
        # Límites razonables
        return max(inflacion, min(g, pib + 1.0)) / 100
    
    def _obtener_margen_medio_sector(self, sector: str) -> float:
        """Márgenes EBITDA medios por sector en España"""
        margenes = {
            'Tecnología': 20.0,
            'Hostelería': 12.0,
            'Ecommerce': 8.0,
            'Consultoría': 25.0,
            'Retail': 8.0,
            'Servicios': 15.0,
            'Automoción': 10.0,
            'Industrial': 12.0,
            'Otro': 12.0
        }
        return margenes.get(sector, 12.0)
    
    def realizar_valoracion_dcf(self, flujos_caja: list, wacc: float, g: float, 
                               deuda_neta: float = 0) -> Dict:
        """
        Valoración DCF con método de dos etapas
        """
        # Valor presente de flujos explícitos
        vp_flujos = sum([fc / (1 + wacc) ** (i + 1) for i, fc in enumerate(flujos_caja)])
        
        # Valor terminal
        ultimo_flujo = flujos_caja[-1]
        valor_terminal = ultimo_flujo * (1 + g) / (wacc - g)
        vp_valor_terminal = valor_terminal / (1 + wacc) ** len(flujos_caja)
        
        # Enterprise Value
        enterprise_value = vp_flujos + vp_valor_terminal
        
        # Equity Value
        equity_value = enterprise_value - deuda_neta
        
        return {
            'enterprise_value': enterprise_value,
            'equity_value': max(0, equity_value),  # No puede ser negativo
            'vp_flujos_explicitos': vp_flujos,
            'vp_valor_terminal': vp_valor_terminal,
            'valor_terminal': valor_terminal,
            'peso_valor_terminal': vp_valor_terminal / enterprise_value * 100 if enterprise_value > 0 else 0
        }
    
    def analisis_sensibilidad_bidimensional(self, caso_base: Dict, flujos: list, 
                                          deuda_neta: float) -> pd.DataFrame:
        """
        Análisis de sensibilidad WACC vs g (tabla bidimensional)
        """
        wacc_base = caso_base['wacc']
        g_base = caso_base['g']
        
        # Rangos de sensibilidad
        wacc_rango = np.arange(wacc_base - 0.02, wacc_base + 0.021, 0.01)
        g_rango = np.arange(g_base - 0.01, g_base + 0.011, 0.005)
        
        # Crear tabla
        tabla = pd.DataFrame(index=[f"{w:.1%}" for w in wacc_rango],
                           columns=[f"{g:.1%}" for g in g_rango])
        
        for i, w in enumerate(wacc_rango):
            for j, g in enumerate(g_rango):
                if w > g:  # WACC debe ser mayor que g
                    val = self.realizar_valoracion_dcf(flujos, w, g, deuda_neta)
                    tabla.iloc[i, j] = val['equity_value']
                else:
                    tabla.iloc[i, j] = np.nan
        
        return tabla