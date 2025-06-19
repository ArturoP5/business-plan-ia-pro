"""
Sistema profesional de valoración de empresas
Incluye cálculo de WACC, prima de riesgo sectorial y DCF
"""

import numpy as np
import numpy_financial as npf
from datetime import datetime
from typing import Dict, List, Tuple, Optional

class ValoracionProfesional:
    """
    Clase principal para realizar valoraciones profesionales de empresas
    utilizando metodología DCF con cálculo de WACC sectorial
    """
    
    def __init__(self):
        # Tasas libres de riesgo actualizadas (Mayo 2025)
        self.tasas_libres_riesgo = {
            'EUR': 3.1,  # Bono España 10Y actual
            'USD': 4.5   # Treasury 10Y
        }
        
        # Betas sectoriales no apalancadas (unlevered)
        self.betas_sectoriales = {
            'tecnologia': 1.5,
            'software': 1.8,
            'automocion': 1.3,
            'retail': 1.0,
            'inmobiliario': 1.2,
            'renovables': 0.9,
            'servicios': 1.1,
            'consumo': 0.8,
            'industrial': 1.2,
            'financiero': 1.4,
            'salud': 0.9,
            'energia': 1.1,
            'telecomunicaciones': 1.0,
            'utilities': 0.7
        }
        
        # Prima de riesgo del mercado español
        self.prima_mercado = 5.5  # Histórica España
        
        # Primas de riesgo por tamaño
        self.primas_tamaño = {
            'micro': 5.0,      # <10M revenue
            'pequeña': 3.0,    # 10-50M
            'mediana': 1.5,    # 50-250M
            'grande': 0.0      # >250M
        }
        
        # Ajustes de riesgo sectorial (específicos España)
        self.ajustes_sectoriales = {
            'tecnologia': 2.0,      # Alta obsolescencia
            'automocion': 1.5,      # Transición eléctrica
            'retail': 1.0,          # Amazon effect
            'inmobiliario': -0.5,   # Activos tangibles
            'renovables': -1.0,     # Contratos largo plazo
            'servicios': 0.5,
            'consumo': 0.3,
            'industrial': 0.8,
            'financiero': 0.0,      # Ya reflejado en beta
            'salud': -0.3,
            'energia': 1.2,
            'telecomunicaciones': 0.5,
            'utilities': -0.8
        }
        
        # Spreads de crédito por rating
        self.spreads_credito = {
            'AAA': 0.5,
            'AA': 0.8,
            'A': 1.2,
            'BBB': 2.0,
            'BB': 3.5,
            'B': 5.0,
            'CCC': 8.0,
            'CC': 12.0,
            'D': 20.0
        }
        
        # Múltiplos EV/EBITDA por sector (medianas mercado español)
        self.multiplos_sector = {
            'tecnologia': 12.0,
            'software': 15.0,
            'automocion': 5.5,
            'retail': 7.0,
            'inmobiliario': 10.0,
            'renovables': 11.0,
            'servicios': 8.0,
            'consumo': 9.0,
            'industrial': 7.5,
            'financiero': 8.0,
            'salud': 11.0,
            'energia': 6.0,
            'telecomunicaciones': 6.5,
            'utilities': 8.5
        }
    
    def determinar_tamaño_empresa(self, ingresos_anuales: float) -> str:
        """
        Determina el tamaño de la empresa basado en ingresos
        """
        if ingresos_anuales < 10_000_000:
            return 'micro'
        elif ingresos_anuales < 50_000_000:
            return 'pequeña'
        elif ingresos_anuales < 250_000_000:
            return 'mediana'
        else:
            return 'grande'
    
    def calcular_beta_apalancada(self, 
                                 sector: str, 
                                 ratio_deuda_equity: float, 
                                 tasa_impuestos: float = 0.25) -> float:
        """
        Calcula la beta apalancada usando la fórmula de Hamada
        Beta_levered = Beta_unlevered * [1 + (1 - Tax) * (D/E)]
        """
        beta_desapalancada = self.betas_sectoriales.get(sector, 1.0)
        beta_apalancada = beta_desapalancada * (1 + (1 - tasa_impuestos) * ratio_deuda_equity)
        return beta_apalancada
    
    def calcular_coste_equity(self,
                             sector: str,
                             tamaño: str,
                             ratio_deuda_equity: float,
                             moneda: str = 'EUR') -> float:
        """
        Calcula el coste del equity usando CAPM ajustado
        Re = Rf + β × (Rm - Rf) + Prima_tamaño + Ajuste_sectorial
        """
        # Tasa libre de riesgo
        rf = self.tasas_libres_riesgo[moneda]
        
        # Beta apalancada
        beta = self.calcular_beta_apalancada(sector, ratio_deuda_equity)
        
        # Prima de mercado
        prima_mercado = self.prima_mercado
        
        # Prima por tamaño
        prima_tamaño = self.primas_tamaño[tamaño]
        
        # Ajuste sectorial
        ajuste_sector = self.ajustes_sectoriales.get(sector, 0)
        
        # Cálculo final
        coste_equity = rf + (beta * prima_mercado) + prima_tamaño + ajuste_sector
        
        return coste_equity
    
    def calcular_coste_deuda(self,
                            rating: str,
                            euribor: float = 2.7) -> float:
        """
        Calcula el coste de la deuda basado en rating crediticio
        Rd = Euribor + Spread
        """
        spread = self.spreads_credito.get(rating, 5.0)  # Default BB
        return euribor + spread
    
    def calcular_wacc(self,
                     sector: str,
                     ingresos: float,
                     deuda_total: float,
                     equity_total: float,
                     rating: str = 'BB',
                     tasa_impuestos: float = 0.25) -> Dict[str, float]:
        """
        Calcula el WACC (Weighted Average Cost of Capital)
        WACC = (E/V × Re) + (D/V × Rd × (1-T))
        """
        # Determinar tamaño
        tamaño = self.determinar_tamaño_empresa(ingresos)
        
        # Valor total de la empresa
        valor_total = deuda_total + equity_total
        
        # Pesos
        peso_equity = equity_total / valor_total
        peso_deuda = deuda_total / valor_total
        
        # Ratio D/E
        ratio_de = deuda_total / equity_total if equity_total > 0 else 0
        
        # Costes
        coste_equity = self.calcular_coste_equity(sector, tamaño, ratio_de)
        coste_deuda = self.calcular_coste_deuda(rating)
        
        # WACC
        wacc = (peso_equity * coste_equity) + (peso_deuda * coste_deuda * (1 - tasa_impuestos))
        
        return {
            'wacc': wacc,
            'coste_equity': coste_equity,
            'coste_deuda': coste_deuda,
            'peso_equity': peso_equity,
            'peso_deuda': peso_deuda,
            'beta_apalancada': self.calcular_beta_apalancada(sector, ratio_de)
        }
    
    def calcular_valor_terminal(self,
                               fcf_ultimo_año: float,
                               tasa_crecimiento_perpetuo: float,
                               wacc: float) -> float:
        """
        Calcula el valor terminal usando el modelo de Gordon
        VT = FCF_n × (1 + g) / (WACC - g)
        """
        if wacc <= tasa_crecimiento_perpetuo:
            raise ValueError("WACC debe ser mayor que la tasa de crecimiento perpetuo")
        
        valor_terminal = fcf_ultimo_año * (1 + tasa_crecimiento_perpetuo) / (wacc - tasa_crecimiento_perpetuo)
        return valor_terminal
    
    def valoracion_dcf(self,
                      flujos_caja_libres: List[float],
                      wacc: float,
                      tasa_crecimiento_perpetuo: float = 0.02,
                      deuda_neta: float = 0) -> Dict[str, float]:
        """
        Realiza una valoración completa por DCF
        """
        # Valor presente de los flujos proyectados
        vp_flujos = sum([fcf / (1 + wacc) ** (i + 1) 
                        for i, fcf in enumerate(flujos_caja_libres)])
        
        # Valor terminal
        fcf_ultimo = flujos_caja_libres[-1]
        valor_terminal = self.calcular_valor_terminal(fcf_ultimo, tasa_crecimiento_perpetuo, wacc)
        
        # Valor presente del valor terminal
        años_proyeccion = len(flujos_caja_libres)
        vp_valor_terminal = valor_terminal / (1 + wacc) ** años_proyeccion
        
        # Valor empresa (Enterprise Value)
        valor_empresa = vp_flujos + vp_valor_terminal
        
        # Valor del equity
        valor_equity = valor_empresa - deuda_neta
        
        return {
            'valor_empresa': valor_empresa,
            'valor_equity': valor_equity,
            'vp_flujos': vp_flujos,
            'vp_valor_terminal': vp_valor_terminal,
            'valor_terminal': valor_terminal
        }
    
    def valoracion_por_multiplos(self,
                                ebitda_actual: float,
                                sector: str,
                                deuda_neta: float = 0,
                                ajuste_tamaño: float = 0.9) -> Dict[str, float]:
        """
        Valoración por múltiplos comparables
        """
        # Múltiplo base del sector
        multiplo_base = self.multiplos_sector.get(sector, 8.0)
        
        # Ajuste por tamaño (empresas pequeñas suelen tener descuento)
        multiplo_ajustado = multiplo_base * ajuste_tamaño
        
        # Valor empresa
        valor_empresa = ebitda_actual * multiplo_ajustado
        
        # Valor equity
        valor_equity = valor_empresa - deuda_neta
        
        return {
            'valor_empresa': valor_empresa,
            'valor_equity': valor_equity,
            'multiplo_aplicado': multiplo_ajustado,
            'ebitda_base': ebitda_actual
        }
    
    def calcular_tir_inversion(self,
                              inversion_inicial: float,
                              flujos_caja: List[float],
                              valor_terminal_equity: float) -> float:
        """
        Calcula la TIR de una inversión
        """
        # Agregar valor terminal al último flujo
        flujos_completos = flujos_caja.copy()
        flujos_completos[-1] += valor_terminal_equity
        
        # Crear array de flujos incluyendo inversión inicial
        flujos_tir = [-inversion_inicial] + flujos_completos
        
        # Calcular TIR usando numpy
        tir = npf.irr(flujos_tir)
        
        return tir
    
    def analisis_sensibilidad_wacc(self,
                                  wacc_base: float,
                                  flujos_caja: List[float],
                                  tasa_crecimiento: float,
                                  deuda_neta: float,
                                  rango_wacc: float = 2.0) -> Dict[str, float]:
        """
        Análisis de sensibilidad sobre el WACC
        """
        resultados = {}
        
        # Rango de WACC a analizar
        waccs = [wacc_base - rango_wacc, 
                wacc_base - rango_wacc/2,
                wacc_base,
                wacc_base + rango_wacc/2,
                wacc_base + rango_wacc]
        
        for wacc in waccs:
            val = self.valoracion_dcf(flujos_caja, wacc/100, tasa_crecimiento, deuda_neta)
            resultados[f'wacc_{wacc:.1f}%'] = val['valor_equity']
        
        return resultados
    
    def generar_resumen_valoracion(self,
                                  empresa_info: Dict,
                                  proyecciones: Dict,
                                  params_financieros: Dict) -> Dict:
        """
        Genera un resumen completo de valoración
        """
        # Extraer información
        sector = empresa_info['sector']
        ingresos = proyecciones['ingresos_año1']
        ebitda_actual = proyecciones['ebitda_año1']
        flujos_caja = proyecciones['flujos_caja_libres']
        
        deuda_total = params_financieros['deuda_total']
        equity_total = params_financieros['equity_total']
        deuda_neta = params_financieros['deuda_neta']
        rating = params_financieros.get('rating', 'BB')
        
        # Calcular WACC
        wacc_info = self.calcular_wacc(
            sector, ingresos, deuda_total, equity_total, rating
        )
        wacc = wacc_info['wacc'] / 100  # Convertir a decimal
        
        # Valoración DCF
        val_dcf = self.valoracion_dcf(
            flujos_caja, wacc, 0.02, deuda_neta
        )
        
        # Valoración por múltiplos
        tamaño = self.determinar_tamaño_empresa(ingresos)
        ajuste = 0.9 if tamaño in ['micro', 'pequeña'] else 1.0
        val_multiplos = self.valoracion_por_multiplos(
            ebitda_actual, sector, deuda_neta, ajuste
        )
        
        # TIR esperada (asumiendo inversión = valor equity)
        tir = self.calcular_tir_inversion(
            val_dcf['valor_equity'],
            flujos_caja,
            val_dcf['valor_terminal']
        )
        
        # Sensibilidad
        sensibilidad = self.analisis_sensibilidad_wacc(
            wacc_info['wacc'], flujos_caja, 0.02, deuda_neta
        )
        
        return {
            'wacc_detalle': wacc_info,
            'valoracion_dcf': val_dcf,
            'valoracion_multiplos': val_multiplos,
            'tir_esperada': tir,
            'analisis_sensibilidad': sensibilidad,
            'rating_implicito': self._calcular_rating_implicito(wacc_info['wacc'])
        }
    
    def _calcular_rating_implicito(self, wacc: float) -> str:
        """
        Determina un rating implícito basado en el WACC
        """
        if wacc < 7:
            return "AA"
        elif wacc < 9:
            return "A"
        elif wacc < 11:
            return "BBB"
        elif wacc < 13:
            return "BB"
        elif wacc < 15:
            return "B"
        else:
            return "CCC"