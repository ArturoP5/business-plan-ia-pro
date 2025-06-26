# models/modelo_financiero.py

from datetime import datetime
from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from valoracion_profesional import ValoracionProfesional
from utils.valoracion_bancainversion import realizar_valoracion_profesional
from utils.api_data_collector import APIDataCollector

class ModeloFinanciero:
    """
    Modelo financiero completo para PYMEs
    Genera P&L, Balance y Cash Flow proyectados
    """
    def __init__(self, empresa_info: dict, escenario_macro: dict, params_operativos: dict):
        """
        Inicializa el modelo financiero con estructura completa
        """
        # Inicializar el recopilador de datos de APIs
        self.api_collector = APIDataCollector()
        
        # Obtener datos actualizados si está disponible
        try:
            datos_actualizados = self.api_collector.get_datos_macroeconomicos()
            # Actualizar valores macro con datos reales si están disponibles
            escenario_macro['pib'] = datos_actualizados.get('pib', escenario_macro.get('pib', 1.9))
            escenario_macro['inflacion'] = datos_actualizados.get('inflacion', escenario_macro.get('inflacion', 2.5))
            escenario_macro['euribor'] = datos_actualizados.get('euribor', escenario_macro.get('euribor', 2.7))
            escenario_macro['desempleo'] = datos_actualizados.get('desempleo', escenario_macro.get('desempleo', 11.7))
            print(f"✓ Datos macroeconómicos actualizados: {datos_actualizados['fecha_actualizacion']}")
        except Exception as e:
            print(f"⚠️ Usando valores por defecto para datos macro: {e}")
            
        # Información básica de la empresa
        self.nombre = empresa_info.get('nombre', 'Empresa')
        self.sector = empresa_info.get('sector', 'servicios')
        self.empresa_familiar = empresa_info.get('empresa_familiar', 'No')
        self.empresa_auditada = empresa_info.get('empresa_auditada', 'Sí')
        self.año_fundacion = empresa_info.get('año_fundacion', datetime.now().year)
        self.empleados = empresa_info.get('empleados', 10)
        
        # Escenario macroeconómico
        self.pib_crecimiento = escenario_macro.get('pib', 1.9)
        self.inflacion = escenario_macro.get('inflacion', 2.5)
        self.euribor = escenario_macro.get('euribor', 2.7)
        self.tasa_desempleo = escenario_macro.get('desempleo', 11.7)
        
        # Parámetros operativos
        self.ingresos_iniciales = params_operativos.get('ingresos_iniciales', 10_000_000)
        self.crecimiento_ventas = params_operativos.get('crecimiento_ventas', 5.0)
        self.margen_ebitda_inicial = params_operativos.get('margen_ebitda', 12.0)
        self.ebitda_real = params_operativos.get('ebitda_real', None)
        self.margen_ebitda_real = params_operativos.get('margen_ebitda_real', None)
        self.capex_porcentaje = params_operativos.get('capex_ventas', 3.0)
        self.dias_cobro = params_operativos.get('dias_cobro', 60)
        self.dias_pago = params_operativos.get('dias_pago', 45)
        self.dias_inventario = params_operativos.get('dias_inventario', 30)

        # Estructura de costos
        self.costos_variables_pct = params_operativos.get('costos_variables_pct', 0.6)
        self.gastos_personal = params_operativos.get('gastos_personal', 0)
        self.gastos_generales = params_operativos.get('gastos_generales', 0)
        self.gastos_marketing = params_operativos.get('gastos_marketing', 0)
        self.otros_gastos = params_operativos.get('otros_gastos', 0)
                
        # NUEVA ESTRUCTURA FINANCIERA COMPLETA
        # Balance inicial
        self.activo_fijo_inicial = params_operativos.get('activo_fijo', 5_000_000)
        self.inventario_inicial = params_operativos.get('inventario', 1_000_000)
        self.clientes_inicial = params_operativos.get('clientes', 2_000_000)
        self.proveedores_inicial = params_operativos.get('proveedores', 1_500_000)
        self.pasivo_laboral = params_operativos.get('pasivo_laboral', 0)
        self.provisiones_laborales = params_operativos.get('provisiones_laborales', 0)
        self.inversiones_cp_inicial = params_operativos.get('inversiones_cp', 0)
        self.gastos_anticipados_inicial = params_operativos.get('gastos_anticipados', 0)
        self.otros_activos_corrientes_inicial = params_operativos.get('otros_activos_corrientes', 0)
        
        # Activos no corrientes
        self.activo_fijo_bruto_inicial = params_operativos.get('activo_fijo_bruto', 5_000_000)
        self.depreciacion_acumulada_inicial = params_operativos.get('depreciacion_acumulada', 1_000_000)
        # Recalcular activo fijo neto con los valores correctos
        self.activo_fijo_inicial = self.activo_fijo_bruto_inicial - self.depreciacion_acumulada_inicial
        self.activos_intangibles_inicial = params_operativos.get('activos_intangibles', 0)
        self.inversiones_lp_inicial = params_operativos.get('inversiones_lp', 0)
        self.otros_activos_nc_inicial = params_operativos.get('otros_activos_nc', 0)
        
        # Patrimonio
        self.resultados_acumulados = params_operativos.get('resultados_acumulados', 0)
        self.tesoreria_inicial = params_operativos.get('tesoreria', 500_000)
        
        # Estructura de capital
        self.capital_social = params_operativos.get('capital_social', 3_000_000)
        self.reservas = params_operativos.get('reservas', 1_000_000)
        
        # Financiación bancaria detallada
        self.prestamos_lp = params_operativos.get('prestamos_lp', [])
        self.hipotecas = params_operativos.get('hipotecas', [])
        self.leasings = params_operativos.get('leasings', [])
        self.polizas_credito = params_operativos.get('polizas_credito', [])
        # DEBUG: Ver qué datos llegan
        print(f"DEBUG - Hipotecas: {self.hipotecas}")
        print(f"DEBUG - Leasings: {self.leasings}")
        print(f"DEBUG - Pólizas: {self.polizas_credito}")
        self.factoring = params_operativos.get('factoring', {})
        self.confirming = params_operativos.get('confirming', {})
        
        # Plan de inversiones CAPEX
        self.plan_capex = params_operativos.get('plan_capex', [])
        
        # Otros parámetros financieros
        self.tasa_impuestos = params_operativos.get('tasa_impuestos', 25.0)
        self.dividendos_payout = params_operativos.get('dividendos_payout', 30.0)
        self.rating_crediticio = params_operativos.get('rating', 'BB')
        
        # Sistema de valoración profesional
        self.valorador = ValoracionProfesional()
        
        # DataFrames para almacenar proyecciones
        self.pyl = None
        self.balance = None
        self.cash_flow = None
        self.ratios = None

        # Actualizar con datos sectoriales si están disponibles
        self.actualizar_datos_sectoriales()

    def actualizar_datos_sectoriales(self):
        """
        Actualiza los parámetros del modelo con datos sectoriales de APIs
        """
        try:
            # Obtener datos del sector
            datos_sector = self.api_collector.get_datos_sectoriales(self.sector)
            
            # Obtener múltiplos de valoración
            multiples = self.api_collector.get_datos_cnmv(self.sector)
            
            # Actualizar parámetros si hay datos disponibles
            if datos_sector:
                # Ajustar crecimiento según sector
                crecimiento_sector = datos_sector.get('crecimiento_sectorial', 5.0)
                self.crecimiento_ventas = (self.crecimiento_ventas + crecimiento_sector) / 2
                
                
                # Ajustar margen EBITDA según sector
                margen_sector = datos_sector.get('margen_ebitda_medio', 15.0)
                self.margen_ebitda_inicial = (self.margen_ebitda_inicial + margen_sector) / 2
                
                print(f"✓ Datos sectoriales actualizados para {self.sector}")
                print(f"  - Crecimiento ajustado: {self.crecimiento_ventas:.1f}%")
                print(f"  - Margen EBITDA ajustado: {self.margen_ebitda_inicial:.1f}%")
                
            # Guardar múltiplos para valoración
            self.multiples_sector = multiples
            
        except Exception as e:
            print(f"⚠️ No se pudieron actualizar datos sectoriales: {e}")

    def calcular_deuda_total(self, año_actual: int = 1, incluir_pasivo_laboral: bool = True) -> float:
        """
        Calcula la deuda total pendiente actual de todas las fuentes
        
        Args:
            año_actual: Año para el cálculo
            incluir_pasivo_laboral: Si incluir el pasivo laboral en la deuda total
        """
        deuda = 0
        
        # Incluir pasivo laboral si corresponde
        if incluir_pasivo_laboral:
            deuda += self.pasivo_laboral
        
        # Préstamos largo plazo - calcular saldo pendiente
        for prestamo in self.prestamos_lp:
            principal = prestamo.get('principal', 0)
            plazo = prestamo.get('plazo_años', 5)
            año_inicio = prestamo.get('año_inicio', 1)
            años_transcurridos = max(0, año_actual - año_inicio)
            
            if años_transcurridos < plazo:
                if prestamo.get('metodo_amortizacion', 'frances') == 'frances':
                    tipo = prestamo.get('tipo_interes', 5.0)
                    saldo = self._saldo_prestamo_frances(principal, tipo, plazo, años_transcurridos)
                else:  # Lineal
                    saldo = principal - (principal / plazo * años_transcurridos)
                deuda += max(0, saldo)
        
        # Hipotecas - calcular saldo pendiente
        for hipoteca in self.hipotecas:
            principal = hipoteca.get('principal', 0)
            plazo = hipoteca.get('plazo_años', 15)
            año_inicio = hipoteca.get('año_inicio', 1)
            años_transcurridos = max(0, año_actual - año_inicio)
            
            if años_transcurridos < plazo:
                tipo = hipoteca.get('tipo_interes', 3.0)
                saldo = self._saldo_prestamo_frances(principal, tipo, plazo, años_transcurridos)
                deuda += max(0, saldo)
        
        # Leasings - calcular saldo pendiente
        for leasing in self.leasings:
            cuota_mensual = leasing.get('cuota_mensual', 0)
            meses_restantes_inicial = leasing.get('meses_restantes', leasing.get('plazo_meses', 48))
            
            # Calcular meses que han pasado desde el inicio de la proyección
            meses_transcurridos_proyeccion = max(0, (año_actual - 1) * 12)
            
            # Meses restantes actuales
            meses_restantes_actual = max(0, meses_restantes_inicial - meses_transcurridos_proyeccion)
            
            if meses_restantes_actual > 0:
                # Calcular saldo pendiente basado en cuotas restantes
                saldo = cuota_mensual * meses_restantes_actual * 0.9  # Factor de valor presente aproximado
                deuda += max(0, saldo)
        
        # Pólizas de crédito (solo dispuesto actual)
        for poliza in self.polizas_credito:
            deuda += poliza.get('dispuesto', 0)
        
        return deuda

    def calcular_gastos_financieros_anuales(self, año: int) -> float:
        """Calcula los gastos financieros totales para un año"""
        gastos = 0
        
        # Préstamos L/P con diferentes tipos de amortización
        for prestamo in self.prestamos_lp:
            principal = prestamo.get('principal', 0)
            tipo = prestamo.get('tipo_interes', 5.0)
            metodo = prestamo.get('metodo_amortizacion', 'frances')
            plazo = prestamo.get('plazo_años', 5)
            año_inicio = prestamo.get('año_inicio', 1)
            
            if año >= año_inicio and año < año_inicio + plazo:
                if metodo == 'frances':
                    # Cuota constante
                    cuota = self._calcular_cuota_francesa(principal, tipo, plazo)
                    # Calcular intereses del año
                    saldo_inicial = self._saldo_prestamo_frances(principal, tipo, plazo, año - año_inicio)
                    gastos += saldo_inicial * tipo / 100
                elif metodo == 'lineal':
                    # Amortización lineal
                    saldo = principal - (principal / plazo * (año - año_inicio))
                    gastos += saldo * tipo / 100
                elif metodo == 'bullet':
                    # Solo intereses hasta el final
                    gastos += principal * tipo / 100
        
        # Hipotecas (generalmente método francés)
        for hipoteca in self.hipotecas:
            principal = hipoteca.get('principal', 0)
            tipo = hipoteca.get('tipo_interes', self.euribor + 1.0)
            plazo = hipoteca.get('plazo_años', 15)
            año_inicio = hipoteca.get('año_inicio', 1)
            
            if año >= año_inicio and año < año_inicio + plazo:
                saldo_inicial = self._saldo_prestamo_frances(principal, tipo, plazo, año - año_inicio)
                gastos += saldo_inicial * tipo / 100
        
        # Leasings
        for leasing in self.leasings:
            cuota_mensual = leasing.get('cuota_mensual', 0)
            meses_restantes = leasing.get('meses_restantes', leasing.get('plazo_meses', 48))
            # Calcular meses en este año
            meses_año = min(12, max(0, meses_restantes - (año - 1) * 12))
            gastos += cuota_mensual * meses_año * 0.3  # Aproximadamente 30% es interés
        
        # Pólizas de crédito
        for poliza in self.polizas_credito:
            dispuesto = poliza.get('dispuesto', 0)
            tipo = poliza.get('tipo_interes', self.euribor + 2.5)
            gastos += dispuesto * tipo / 100  # Convertir porcentaje a decimal
        
        # Factoring
        if self.factoring:
            limite = self.factoring.get('limite', 0)
            coste = self.factoring.get('coste', 0.015)  # Ya viene como decimal de app.py
            # Asumimos uso del 80% del límite
            volumen_estimado = limite * 0.8
            gastos += volumen_estimado * coste
        
        return gastos

    def _calcular_cuota_francesa(self, principal: float, tipo: float, plazo: int) -> float:
        """Calcula la cuota del método francés"""
        if tipo == 0:
            return principal / plazo
        r = tipo / 100
        return principal * (r * (1 + r)**plazo) / ((1 + r)**plazo - 1)

    def _saldo_prestamo_frances(self, principal: float, tipo: float, plazo: int, años_transcurridos: int) -> float:
        """Calcula el saldo pendiente de un préstamo francés"""
        if años_transcurridos >= plazo:
            return 0
        if tipo == 0:
            return principal * (1 - años_transcurridos / plazo)
        
        r = tipo / 100
        cuota = self._calcular_cuota_francesa(principal, tipo, plazo)
        
        # Saldo = Principal * (1+r)^n - Cuota * ((1+r)^n - 1) / r
        factor = (1 + r) ** años_transcurridos
        saldo = principal * factor - cuota * (factor - 1) / r
        
        return max(0, saldo)  
      
    def generar_proyecciones(self, años: int = 5) -> dict:
        """
        Genera todas las proyecciones financieras
        """
        # Generar P&L
        self.generar_pyl(años)
        
        # Generar Balance
        self.generar_balance(años)
        
        # Generar Cash Flow
        self.generar_cash_flow(años)
        
        # Calcular ratios
        self.calcular_ratios()
        
        # Realizar valoración
        valoracion = self.realizar_valoracion_bancainversion()
        
        return {
            'pyl': self.pyl,
            'balance': self.balance,
            'cash_flow': self.cash_flow,
            'ratios': self.ratios,
            'valoracion': valoracion
        }
    
    def _get_crecimiento_sector(self) -> float:
        """Obtiene crecimiento esperado del sector"""
        crecimientos = {
            'Tecnología': 0.15,
            'Hostelería': 0.06,
            'Automoción': 0.04,
            'Ecommerce': 0.09,
            'Consultoría': 0.08,
            'Retail': 0.035,
            'Servicios': 0.05,
            'Industrial': 0.04,
            'Otro': 0.03
        }
        return crecimientos.get(self.sector, 0.03)

    def generar_pyl(self, años: int = 5):
        """Genera la cuenta de resultados proyectada"""
        pyl = []
        
        for año in range(1, años + 1):
            print(f"\n=== PROCESANDO AÑO {año} ===")
            # Ingresos
            if año == 1:
                # Aplicar crecimiento también en el año 1
                factor_macro = 1 + (self.pib_crecimiento - 2) / 100 * 0.3
                crecimiento_ajustado = self.crecimiento_ventas * factor_macro
                ingresos = self.ingresos_iniciales * (1 + crecimiento_ajustado / 100)
            else:
                # Crecimiento ajustado por inflación y contexto macro
                factor_macro = 1 + (self.pib_crecimiento - 2) / 100 * 0.3  # 30% correlación con PIB
                crecimiento_ajustado = self.crecimiento_ventas * factor_macro
                ingresos = pyl[-1]['ingresos'] * (1 + crecimiento_ajustado / 100)
            
            # Costes operativos
            inflacion_acum = (1 + self.inflacion / 100) ** (año - 1)

            # Coste de ventas como % de ingresos (viene de datos_empresa)
            coste_ventas = ingresos * self.costos_variables_pct

            # Gastos fijos ajustados por inflación
            gastos_personal = self.gastos_personal * inflacion_acum
            gastos_generales = self.gastos_generales * inflacion_acum
            gastos_marketing = self.gastos_marketing * inflacion_acum
            otros_gastos_calc = self.otros_gastos * inflacion_acum if hasattr(self, 'otros_gastos') else 0

            # Total otros gastos
            otros_gastos = gastos_generales + gastos_marketing + otros_gastos_calc
            # Debug de gastos
            print(f"\n=== DEBUG GASTOS AÑO {año} ===")
            print(f"Gastos personal inicial: {self.gastos_personal:,.0f}")
            print(f"Gastos personal ajustado: {gastos_personal:,.0f}")
            print(f"Gastos generales: {gastos_generales:,.0f}")
            print(f"Gastos marketing: {gastos_marketing:,.0f}")
            print(f"Otros gastos calc: {otros_gastos_calc:,.0f}")
            print(f"Total otros gastos: {otros_gastos:,.0f}")
            # Calcular EBITDA correctamente para todos los años
            # Calcular EBITDA = Ventas - Costos - Gastos
            ebitda = ingresos - coste_ventas - gastos_personal - otros_gastos
            margen_ebitda = (ebitda / ingresos * 100) if ingresos > 0 else 0

            
            # Amortizaciones (activo fijo + CAPEX acumulado)
            amortizacion = (self.activo_fijo_inicial + sum([c['importe'] for c in self.plan_capex if c['año'] < año])) / 10
            
            # EBIT
            ebit = ebitda - amortizacion
            
            # Gastos financieros
            gastos_financieros = self.calcular_gastos_financieros_anuales(año)
            
            # BAI y Beneficio Neto
            bai = ebit - gastos_financieros
            impuestos = max(0, bai * self.tasa_impuestos / 100)
            beneficio_neto = bai - impuestos
            
            pyl.append({
                'año': año,
                'ingresos': ingresos,
                'coste_ventas': coste_ventas,
                'margen_bruto': ingresos - coste_ventas,
                'gastos_personal': gastos_personal,
                'otros_gastos': otros_gastos,
                'ebitda': ebitda,
                'margen_ebitda_%': margen_ebitda,
                'amortizacion': amortizacion,
                'ebit': ebit,
                'gastos_financieros': gastos_financieros,
                'bai': bai,
                'impuestos': impuestos,
                'beneficio_neto': beneficio_neto
            })
        # Debug final antes de crear DataFrame
        print("\n=== DEBUG PYL FINAL ===")
        for i, año_data in enumerate(pyl):
        
            self.pyl = pd.DataFrame(pyl)

    def generar_balance(self, años: int = 5):
        """Genera el balance proyectado"""
        balances = []
        
        for año in range(1, años + 1):
            # ACTIVO
            # Activo No Corriente
            activo_fijo_bruto = self.activo_fijo_bruto_inicial
            for capex in self.plan_capex:
                if capex['año'] <= año:
                    activo_fijo_bruto += capex['importe']
            
            amort_acumulada = sum(self.pyl[self.pyl['año'] <= año]['amortizacion'])
            activo_fijo_neto = activo_fijo_bruto - amort_acumulada
            activo_fijo_neto = activo_fijo_bruto - amort_acumulada
            
            # Otros activos no corrientes
            activos_intangibles = self.activos_intangibles_inicial
            inversiones_lp = self.inversiones_lp_inicial
            otros_activos_nc = self.otros_activos_nc_inicial
            
            # Activo Corriente
            if año == 1:
                ingresos = self.ingresos_iniciales
            else:
                ingresos = self.pyl[self.pyl['año'] == año]['ingresos'].values[0]
            
            clientes = ingresos * self.dias_cobro / 365
            inventario = ingresos * 0.6 * self.dias_inventario / 365  # Sobre coste ventas
            
            # Nuevos activos corrientes (mantener valores iniciales por simplicidad)
            inversiones_cp = self.inversiones_cp_inicial
            gastos_anticipados = self.gastos_anticipados_inicial
            otros_activos_corrientes = self.otros_activos_corrientes_inicial
            
            # Tesorería (se calcula al final para cuadrar)
            otros_activos = ingresos * 0.02  # 2% ventas
            
            # PASIVO
            # Patrimonio Neto
            capital = self.capital_social
            reservas = self.reservas
            
            # Acumular beneficios no distribuidos
            for i in range(1, año + 1):
                bn = self.pyl[self.pyl['año'] == i]['beneficio_neto'].values[0]
                dividendos = bn * self.dividendos_payout / 100 if bn > 0 else 0
                reservas += bn - dividendos
            
            patrimonio_neto = capital + reservas + self.resultados_acumulados
            
            # Pasivo No Corriente (deuda L/P pendiente)
            deuda_lp = 0
            for prestamo in self.prestamos_lp:
                saldo = self._calcular_saldo_deuda_año(prestamo, año)
                if saldo > 0:
                    # Parte L/P (más de 1 año)
                    deuda_lp += saldo * 0.8  # 80% es L/P
            
            # Pasivo Corriente
            proveedores = ingresos * 0.6 * self.dias_pago / 365
            # DEBUG: Verificar deuda total
            deuda_total_debug = self.calcular_deuda_total(año)
            deuda_cp = self.calcular_deuda_total(año) * 0.2  # 20% es C/P
            otros_pasivos = ingresos * 0.03
            
            # Calcular tesorería necesaria para cuadrar
            total_activo_sin_tesoreria = (activo_fijo_neto + activos_intangibles + inversiones_lp + 
                                          otros_activos_nc + clientes + inventario + inversiones_cp + 
                                          gastos_anticipados + otros_activos_corrientes + otros_activos)
            total_pasivo_pn = patrimonio_neto + deuda_lp + deuda_cp + proveedores + otros_pasivos
            tesoreria = max(total_pasivo_pn - total_activo_sin_tesoreria, ingresos * 0.02)  # Mínimo 2% ventas
            
            # Ajustar si necesario
            total_activo = total_activo_sin_tesoreria + tesoreria
            
            balances.append({
                'año': año,
                # Activo No Corriente
                'activo_fijo_bruto': activo_fijo_bruto,
                'amortizacion_acumulada': amort_acumulada,
                'activo_fijo_neto': activo_fijo_neto,
                'activos_intangibles': activos_intangibles,
                'inversiones_lp': inversiones_lp,
                'otros_activos_nc': otros_activos_nc,
                # Activo Corriente
                'clientes': clientes,
                'inventario': inventario,
                'inversiones_cp': inversiones_cp,
                'gastos_anticipados': gastos_anticipados,
                'otros_activos_corrientes': otros_activos_corrientes,
                'tesoreria': tesoreria,
                'otros_activos': otros_activos,
                'total_activo': total_activo,
                # Pasivo y PN
                'capital': capital,
                'reservas': reservas,
                'resultados_acumulados': self.resultados_acumulados,
                'patrimonio_neto': patrimonio_neto,
                'deuda_lp': deuda_lp,
                'deuda_cp': deuda_cp,
                'proveedores': proveedores,
                'otros_pasivos': otros_pasivos,
                'total_pasivo_pn': total_pasivo_pn
            })
        
        self.balance = pd.DataFrame(balances)   

    def _calcular_saldo_deuda_año(self, prestamo: dict, año: int) -> float:
        """Calcula el saldo pendiente de un préstamo en un año dado"""
        principal = prestamo.get('principal', 0)
        tipo = prestamo.get('tipo_interes', 5.0)
        plazo = prestamo.get('plazo_años', 5)
        año_inicio = prestamo.get('año_inicio', 1)
        metodo = prestamo.get('metodo_amortizacion', 'frances')
        
        años_transcurridos = año - año_inicio
        
        if años_transcurridos < 0:
            return principal
        if años_transcurridos >= plazo:
            return 0
        
        if metodo == 'frances':
            return self._saldo_prestamo_frances(principal, tipo, plazo, años_transcurridos)
        elif metodo == 'lineal':
            return principal - (principal / plazo * años_transcurridos)
        elif metodo == 'bullet':
            return principal if años_transcurridos < plazo else 0
        
        return 0  

    def generar_cash_flow(self, años: int = 5):
        """Genera el estado de flujos de caja"""
        cash_flows = []
        
        for año in range(1, años + 1):
            # Flujo operativo
            ebitda = self.pyl[self.pyl['año'] == año]['ebitda'].values[0]
            impuestos_pagados = self.pyl[self.pyl['año'] == año]['impuestos'].values[0]
            
            # Variación capital circulante
            if año == 1:
                var_clientes = self.balance[self.balance['año'] == año]['clientes'].values[0] - self.clientes_inicial
                var_inventario = self.balance[self.balance['año'] == año]['inventario'].values[0] - self.inventario_inicial
                var_proveedores = self.balance[self.balance['año'] == año]['proveedores'].values[0] - self.proveedores_inicial
            else:
                var_clientes = (self.balance[self.balance['año'] == año]['clientes'].values[0] - 
                            self.balance[self.balance['año'] == año-1]['clientes'].values[0])
                var_inventario = (self.balance[self.balance['año'] == año]['inventario'].values[0] - 
                                self.balance[self.balance['año'] == año-1]['inventario'].values[0])
                var_proveedores = (self.balance[self.balance['año'] == año]['proveedores'].values[0] - 
                                self.balance[self.balance['año'] == año-1]['proveedores'].values[0])

            # DEBUG - Capital de trabajo
            if año == 1:
                print(f"\n=== DEBUG CAPITAL TRABAJO AÑO 1 ===")
                print(f"Clientes año 1: €{self.balance[self.balance['año'] == año]['clientes'].values[0]:,.0f}")
                print(f"Clientes inicial: €{self.clientes_inicial:,.0f}")
                print(f"Var clientes: €{var_clientes:,.0f}")
                print(f"Inventario año 1: €{self.balance[self.balance['año'] == año]['inventario'].values[0]:,.0f}")
                print(f"Inventario inicial: €{self.inventario_inicial:,.0f}")
                print(f"Var inventario: €{var_inventario:,.0f}")
                print(f"Proveedores año 1: €{self.balance[self.balance['año'] == año]['proveedores'].values[0]:,.0f}")
                print(f"Var proveedores: €{var_proveedores:,.0f}")

            var_nok = - (var_clientes + var_inventario - var_proveedores)   
            
            flujo_operativo = ebitda - impuestos_pagados + var_nok

            # Flujo de inversión
            # CAPEX: usar plan del usuario o porcentaje por sector
            capex_planificado = sum([c['importe'] for c in self.plan_capex if c['año'] == año])
            if capex_planificado > 0:
                capex_año = capex_planificado
            else:
                # Porcentajes de CAPEX por sector
                CAPEX_POR_SECTOR = {
                    'hostelería': 0.06,
                    'tecnología': 0.03,
                    'ecommerce': 0.025,
                    'consultoría': 0.02,
                    'retail': 0.05,
                    'servicios': 0.035,
                    'automoción': 0.08,
                    'industrial': 0.10,
                    'otro': 0.04
                }
                porcentaje = CAPEX_POR_SECTOR.get(self.sector.lower(), 0.04)
                ventas_año = self.pyl[self.pyl['año'] == año]['ingresos'].values[0]
                capex_año = ventas_año * porcentaje
            flujo_inversion = -capex_año
            
            # Flujo financiero
            gastos_financieros = self.pyl[self.pyl['año'] == año]['gastos_financieros'].values[0]
            
            # Amortizaciones de principal
            amort_principal = 0
            for prestamo in self.prestamos_lp:
                if prestamo['metodo_amortizacion'] == 'lineal':
                    amort_principal += prestamo['principal'] / prestamo['plazo_años']
                elif prestamo['metodo_amortizacion'] == 'frances':
                    cuota = self._calcular_cuota_francesa(
                        prestamo['principal'], 
                        prestamo['tipo_interes'], 
                        prestamo['plazo_años']
                    )
                    amort_principal += cuota - gastos_financieros * (prestamo['principal'] / max(self.calcular_deuda_total(año), 1))
            
            # Dividendos
            if año > 1:
                bn_anterior = self.pyl[self.pyl['año'] == año-1]['beneficio_neto'].values[0]
                dividendos = bn_anterior * self.dividendos_payout / 100 if bn_anterior > 0 else 0
            else:
                dividendos = 0
            
            flujo_financiero = -gastos_financieros - amort_principal - dividendos
            
            # Flujo de caja libre (para valoración)
            fcf = flujo_operativo + flujo_inversion
            
            # Flujo total
            flujo_total = flujo_operativo + flujo_inversion + flujo_financiero
            
            cash_flows.append({
                'año': año,
                'flujo_operativo': flujo_operativo,
                'flujo_inversion': flujo_inversion,
                'flujo_financiero': flujo_financiero,
                'flujo_total': flujo_total,
                'free_cash_flow': fcf
            })
        
        self.cash_flow = pd.DataFrame(cash_flows)

    def calcular_ratios(self):
        """Calcula ratios financieros clave"""
        ratios = []
        
        for año in range(1, len(self.pyl) + 1):
            # Datos del año
            ingresos = self.pyl[self.pyl['año'] == año]['ingresos'].values[0]
            ebitda = self.pyl[self.pyl['año'] == año]['ebitda'].values[0]
            beneficio_neto = self.pyl[self.pyl['año'] == año]['beneficio_neto'].values[0]
            
            total_activo = self.balance[self.balance['año'] == año]['total_activo'].values[0]
            patrimonio_neto = self.balance[self.balance['año'] == año]['patrimonio_neto'].values[0]
            deuda_total = (self.balance[self.balance['año'] == año]['deuda_lp'].values[0] + 
                        self.balance[self.balance['año'] == año]['deuda_cp'].values[0])
            
            # Ratios de rentabilidad
            margen_ebitda = ebitda / ingresos * 100
            margen_neto = beneficio_neto / ingresos * 100
            roe = beneficio_neto / patrimonio_neto * 100 if patrimonio_neto > 0 else 0
            roa = beneficio_neto / total_activo * 100
            
            # Ratios de solvencia
            ratio_endeudamiento = deuda_total / patrimonio_neto if patrimonio_neto > 0 else 999
            ratio_cobertura_intereses = ebitda / self.pyl[self.pyl['año'] == año]['gastos_financieros'].values[0] if self.pyl[self.pyl['año'] == año]['gastos_financieros'].values[0] > 0 else 999
            deuda_neta_ebitda = (deuda_total - self.balance[self.balance['año'] == año]['tesoreria'].values[0]) / ebitda if ebitda > 0 else 999
            
            # Ratios de liquidez
            activo_corriente = (self.balance[self.balance['año'] == año]['clientes'].values[0] +
                            self.balance[self.balance['año'] == año]['inventario'].values[0] +
                            self.balance[self.balance['año'] == año]['tesoreria'].values[0])
            pasivo_corriente = (self.balance[self.balance['año'] == año]['deuda_cp'].values[0] +
                            self.balance[self.balance['año'] == año]['proveedores'].values[0])
            
            ratio_liquidez = activo_corriente / pasivo_corriente if pasivo_corriente > 0 else 999
            
            ratios.append({
                'año': año,
                'margen_ebitda_%': margen_ebitda,
                'margen_neto_%': margen_neto,
                'roe_%': roe,
                'roa_%': roa,
                'ratio_endeudamiento': ratio_endeudamiento,
                'cobertura_intereses': ratio_cobertura_intereses,
                'deuda_neta_ebitda': deuda_neta_ebitda,
                'ratio_liquidez': ratio_liquidez
            })
        
        self.ratios = pd.DataFrame(ratios)

    def realizar_valoracion(self) -> dict:
        """Realiza la valoración completa de la empresa con metodología mejorada"""
        
        # Importar la nueva clase
        from valoracion_profesional_v2 import ValoracionProfesionalMejorada
        
        # Crear instancia del valorador mejorado
        valorador_mejorado = ValoracionProfesionalMejorada()
        
        # Preparar datos para valoración
        empresa_info = {
            'sector': self.sector,
            'año_fundacion': self.año_fundacion,
            'cliente_principal_pct': 20,  # Asumimos 20% por defecto
            'equipo_directivo_años_exp': 10  # Asumimos 10 años por defecto
        }
        
        # Parámetros financieros
        params_financieros = {
            'ingresos_ultimo_año': self.pyl['ingresos'].iloc[-1] if self.pyl is not None else self.ingresos_iniciales,
            'margen_ebitda': self.pyl['margen_ebitda_%'].iloc[-1] if self.pyl is not None else self.margen_ebitda_inicial,
            'rating': self.rating_crediticio,
            'deuda_total': self.calcular_deuda_total(self.pyl['año'].max() if self.pyl is not None else 5),
            'equity_total': self.balance['patrimonio_neto'].iloc[-1] if self.balance is not None else self.capital_social,
            'tasa_impuestos': self.tasa_impuestos
        }
        
        # 1. Calcular WACC mejorado
        wacc, detalles_wacc = valorador_mejorado.calcular_wacc_completo(empresa_info, params_financieros)
        
        # 2. Calcular tasa de crecimiento terminal
        g = valorador_mejorado.calcular_tasa_crecimiento_terminal(self.sector)
        
        # 3. Obtener flujos de caja
        flujos_caja = self.cash_flow['free_cash_flow'].tolist() if self.cash_flow is not None else []
        
        # 4. Calcular deuda neta
        deuda_total = self.calcular_deuda_total(1)  # Año inicial para valoración
        tesoreria = self.balance['tesoreria'].iloc[-1] if self.balance is not None else self.tesoreria_inicial
        deuda_neta = deuda_total - tesoreria
        
        # 5. Realizar valoración DCF
        valoracion_dcf = valorador_mejorado.realizar_valoracion_dcf(
            flujos_caja, wacc, g, deuda_neta
        )
        
        # 6. Análisis de sensibilidad
        caso_base = {'wacc': wacc, 'g': g}
        tabla_sensibilidad = valorador_mejorado.analisis_sensibilidad_bidimensional(
            caso_base, flujos_caja, deuda_neta
        )
        
        # 7. Valoración por múltiplos (mantener compatibilidad)
        ebitda_ultimo = self.pyl['ebitda'].iloc[-1] if self.pyl is not None else 0
        multiplo_sector = {
            'Tecnología': 15.0, 'Hostelería': 8.0, 'Ecommerce': 12.0,
            'Consultoría': 10.0, 'Retail': 7.0, 'Servicios': 9.0,
            'Industrial': 8.0, 'Automoción': 7.0, 'Otro': 9.0
        }.get(self.sector, 9.0)
        
        valoracion_multiplos = {
            'valor_empresa': ebitda_ultimo * multiplo_sector,
            'valor_equity': ebitda_ultimo * multiplo_sector - deuda_neta,
            'multiplo_aplicado': multiplo_sector,
            'ebitda_base': ebitda_ultimo
        }
        
        # 8. Preparar resultado completo
        resultado = {
            # WACC y componentes
            'wacc_detalle': detalles_wacc,
            
            # Valoración DCF
            'valoracion_dcf': valoracion_dcf,
            
            # Valoración por múltiplos
            'valoracion_multiplos': valoracion_multiplos,
            
            # TIR esperada (simplificada)
            'tir_esperada': ((valoracion_dcf['equity_value'] / params_financieros['equity_total']) ** (1/5) - 1) * 100 if params_financieros['equity_total'] > 0 else 0,
            
            # Análisis de sensibilidad
            'analisis_sensibilidad': {
                'wacc_-2%': tabla_sensibilidad.iloc[0, 2] if len(tabla_sensibilidad) > 0 else 0,
                'wacc_-1%': tabla_sensibilidad.iloc[1, 2] if len(tabla_sensibilidad) > 1 else 0,
                'wacc_base': valoracion_dcf['equity_value'],
                'wacc_+1%': tabla_sensibilidad.iloc[3, 2] if len(tabla_sensibilidad) > 3 else 0,
                'wacc_+2%': tabla_sensibilidad.iloc[4, 2] if len(tabla_sensibilidad) > 4 else 0,
            },
            
            # Rating implícito
            'rating_implicito': self.rating_crediticio,
            
            # Métricas adicionales para transparencia
            'tasa_crecimiento_g': g * 100,
            'wacc': wacc * 100,
            'prima_tamaño': detalles_wacc['prima_tamaño'],
            'prima_especifica': detalles_wacc['prima_especifica']
        }
        
        return resultado   

    def calcular_metricas_clave(self, pyl_df: pd.DataFrame) -> Dict:
        """
        Calcula métricas financieras clave del negocio
        """
        metricas = {
            'crecimiento_ventas_promedio': 0,
            'margen_ebitda_promedio': 0,
            'roi_proyectado': 0,
            'punto_equilibrio_año': 0,
            'valor_empresa_estimado': 0
        }
        
        # Crecimiento promedio de ventas
        ventas = pyl_df['Ventas'].values
        crecimientos = [(ventas[i] - ventas[i-1]) / ventas[i-1] * 100 
                       for i in range(1, len(ventas))]
        metricas['crecimiento_ventas_promedio'] = round(sum(crecimientos) / len(crecimientos), 1)
        
        # Margen EBITDA promedio
        metricas['margen_ebitda_promedio'] = round(pyl_df['EBITDA %'].mean(), 1)
        
        # ROI simple (beneficio año 5 / inversión inicial estimada)
        beneficio_año_5 = pyl_df['Beneficio Neto'].iloc[-1]
        inversion_estimada = ventas[0] * 0.2  # 20% de ventas año 1
        metricas['roi_proyectado'] = round(beneficio_año_5 / inversion_estimada * 100, 1)
        
        # Punto de equilibrio (primer año con beneficio positivo)
        for idx, beneficio in enumerate(pyl_df['Beneficio Neto']):
            if beneficio > 0:
                metricas['punto_equilibrio_año'] = idx + 1
                break
        
        # Valor empresa (múltiplo de EBITDA)
        ebitda_promedio_ultimos_3 = pyl_df['EBITDA'].iloc[-3:].mean()
        multiplo_sector = 5  # Simplificado, debería venir por sector
        metricas['valor_empresa_estimado'] = round(ebitda_promedio_ultimos_3 * multiplo_sector, 0)
        
        return metricas
    
    def generar_resumen_ejecutivo(self) -> str:
        """
        Genera un resumen ejecutivo del plan financiero
        """
        pyl = self.generar_pyl()
        metricas = self.calcular_metricas_clave(pyl)
        
        resumen = f"""
        RESUMEN EJECUTIVO - {self.nombre_empresa}
        {'=' * 50}
        
        Sector: {self.sector}
        Período de proyección: {self.año_actual} - {self.año_actual + self.años_proyeccion - 1}
        
        PROYECCIONES CLAVE:
        - Ventas año 1: €{pyl['Ventas'].iloc[0]:,.0f}
        - Ventas año 5: €{pyl['Ventas'].iloc[-1]:,.0f}
        - Crecimiento promedio: {metricas['crecimiento_ventas_promedio']}%
        
        RENTABILIDAD:
        - EBITDA año 1: €{pyl['EBITDA'].iloc[0]:,.0f} ({pyl['EBITDA %'].iloc[0]}%)
        - EBITDA año 5: €{pyl['EBITDA'].iloc[-1]:,.0f} ({pyl['EBITDA %'].iloc[-1]}%)
        - Margen EBITDA promedio: {metricas['margen_ebitda_promedio']}%
        
        VALORACIÓN:
        - ROI proyectado: {metricas['roi_proyectado']}%
        - Valor estimado empresa: €{metricas['valor_empresa_estimado']:,.0f}
        - Punto de equilibrio: Año {metricas['punto_equilibrio_año']}
        """
        
        return resumen
    def calcular_working_capital(self, pyl_df: pd.DataFrame) -> pd.DataFrame:
        """
        Calcula las necesidades de Capital de Trabajo (Working Capital)
        """
        wc_data = {
            'Año': pyl_df['Año'],
            'Ventas': pyl_df['Ventas'],
            'Cuentas por Cobrar': [],
            'Inventario': [],
            'Cuentas por Pagar': [],
            'Capital de Trabajo': [],
            'Variación WC': []
        }
        
        for i, ventas in enumerate(pyl_df['Ventas']):
            # Cuentas por cobrar (días de cobro)
            cuentas_cobrar = ventas * (self.dias_cobro / 365)
            wc_data['Cuentas por Cobrar'].append(round(cuentas_cobrar, 0))
            
            # Inventario (15% de costos para simplificar)
            inventario = ventas * self.costos_variables_pct * 0.15
            wc_data['Inventario'].append(round(inventario, 0))
            
            # Cuentas por pagar (días de pago)
            cuentas_pagar = ventas * self.costos_variables_pct * (self.dias_pago / 365)
            wc_data['Cuentas por Pagar'].append(round(cuentas_pagar, 0))
            
            # Capital de trabajo neto
            wc = cuentas_cobrar + inventario - cuentas_pagar
            wc_data['Capital de Trabajo'].append(round(wc, 0))
            
            # Variación (necesidad de financiación)
            if i == 0:
                variacion = wc  # Primer año es el total
            else:
                variacion = wc - wc_data['Capital de Trabajo'][i-1]
            wc_data['Variación WC'].append(round(variacion, 0))
        
        return pd.DataFrame(wc_data)
    
    def calcular_financiacion_circulante(self, wc_df: pd.DataFrame, pyl_df: pd.DataFrame) -> pd.DataFrame:
        """
        Calcula las necesidades de financiación del circulante y pólizas de crédito
        """
        financiacion_data = {
            'Año': wc_df['Año'],
            'Necesidad WC': wc_df['Capital de Trabajo'],
            'Límite Póliza': [],
            'Uso Póliza': [],
            'Disponible': [],
            'Coste Póliza': [],
            'Exceso/(Déficit)': []
        }
        
        for i in range(len(wc_df)):
            # Límite de póliza basado en ventas
            ventas = pyl_df['Ventas'].iloc[i]
            limite = self.polizas_credito['limite']
            financiacion_data['Límite Póliza'].append(round(limite, 0))
            
            # Uso de la póliza (máximo entre necesidad WC y 0)
            necesidad = wc_df['Capital de Trabajo'].iloc[i]
            uso_poliza = min(max(0, necesidad), limite)
            financiacion_data['Uso Póliza'].append(round(uso_poliza, 0))
            
            # Disponible
            disponible = limite - uso_poliza
            financiacion_data['Disponible'].append(round(disponible, 0))
            
            # Coste financiero de la póliza
            coste = uso_poliza * self.polizas_credito['tipo_interes']
            financiacion_data['Coste Póliza'].append(round(coste, 0))
            
            # Exceso o déficit de financiación
            exceso_deficit = limite - necesidad
            financiacion_data['Exceso/(Déficit)'].append(round(exceso_deficit, 0))
        
        return pd.DataFrame(financiacion_data)
    
    def calcular_free_cash_flow(self, pyl_df: pd.DataFrame, wc_df: pd.DataFrame) -> pd.DataFrame:
        """
        Calcula el Free Cash Flow (Flujo de Caja Libre)
        Usa el plan CAPEX del usuario o porcentajes por sector si no hay plan
        """
        
        # Porcentajes de CAPEX por sector (como % de ventas)
        CAPEX_POR_SECTOR = {
            'hostelería': 6.0,      # Renovaciones, equipamiento cocina
            'tecnología': 3.0,      # Principalmente equipos informáticos
            'ecommerce': 2.5,       # Tecnología y logística ligera
            'consultoría': 2.0,     # Mínimo, principalmente ordenadores
            'retail': 5.0,          # Renovación tiendas, sistemas POS
            'servicios': 3.5,       # Variable, promedio general
            'automoción': 8.0,      # Equipamiento taller, herramientas
            'industrial': 10.0,     # Maquinaria pesada
            'otro': 4.0            # Promedio conservador
        }
        
        fcf_data = {
            'Año': pyl_df['Año'],
            'EBITDA': pyl_df['EBITDA'],
            'Impuestos sobre EBIT': [],
            'CAPEX': [],
            'Variación Working Capital': wc_df['Variación WC'],
            'Free Cash Flow': []
        }
        
        for i in range(len(pyl_df)):
            # Impuestos sobre EBIT
            impuestos_ebit = pyl_df['EBIT'].iloc[i] * self.tasa_impuesto if pyl_df['EBIT'].iloc[i] > 0 else 0
            fcf_data['Impuestos sobre EBIT'].append(round(impuestos_ebit, 0))
            
            # CAPEX: Usar plan del usuario o porcentaje por sector
            año_actual = pyl_df['Año'].iloc[i]

            
            # Buscar si hay CAPEX planificado para este año
            capex_planificado = sum([c.get('importe', 0) for c in self.plan_capex if c.get('año') == año_actual])
            
            
            if capex_planificado > 0:
                # Usar el CAPEX introducido por el usuario
                capex = capex_planificado
            else:
                # Usar porcentaje según el sector
                porcentaje_capex = CAPEX_POR_SECTOR.get(self.sector, CAPEX_POR_SECTOR['Otro'])
                capex = pyl_df['Ventas'].iloc[i] * (porcentaje_capex / 100)
                print(f"DEBUG FCF - Porcentaje CAPEX: {porcentaje_capex}")
                print(f"DEBUG FCF - CAPEX calculado: {capex}")
            
            fcf_data['CAPEX'].append(round(capex, 0))
            
            # Free Cash Flow
            fcf = (pyl_df['EBITDA'].iloc[i] - 
                   impuestos_ebit - 
                   capex - 
                   wc_df['Variación WC'].iloc[i])
            fcf_data['Free Cash Flow'].append(round(fcf, 0))
        
        return pd.DataFrame(fcf_data)
    
    def calcular_valoracion_dcf(self, fcf_df: pd.DataFrame, wacc: float = None) -> Dict:
        """
        Calcula la valoración por DCF como los bancos de inversión
        Incluye análisis de sensibilidad y múltiples métodos
        """
        # WACC por sector (basado en Damodaran)
        wacc_por_sector = {
            'Tecnología': 0.12,
            'Hostelería': 0.09,
            'Ecommerce': 0.11,
            'Consultoría': 0.10,
            'Retail': 0.08,
            'Servicios': 0.09,
            'Industrial': 0.08,
            'Automoción': 0.09,
            'Otro': 0.10
        }
        
        # Usar WACC específico del sector si no se proporciona
        if wacc is None:
            wacc = wacc_por_sector.get(self.sector, 0.10)
        
        # 1. MÉTODO DCF CLÁSICO
        # Calcular valor presente de los flujos (años 1-5)
        valores_presentes = []
        for i in range(len(fcf_df)):
            vp = fcf_df['Free Cash Flow'].iloc[i] / ((1 + wacc) ** (i + 1))
            valores_presentes.append(vp)
        
        # Valor terminal - Método de crecimiento perpetuo (Gordon Growth)
        fcf_ultimo = fcf_df['Free Cash Flow'].iloc[-1]
        g = 0.025  # 2.5% crecimiento perpetuo (conservador)
        
        # Normalizar FCF del último año si es necesario
        fcf_normalizado = fcf_ultimo
        if fcf_ultimo < fcf_df['EBITDA'].iloc[-1] * 0.3:  # Si FCF < 30% EBITDA
            # Usar promedio de los últimos 3 años
            fcf_normalizado = fcf_df['Free Cash Flow'].iloc[-3:].mean()
        
        valor_terminal_gg = fcf_normalizado * (1 + g) / (wacc - g)
        
        # Valor terminal - Método de múltiplo de salida
        ebitda_ultimo = fcf_df['EBITDA'].iloc[-1]
        multiplos_salida = {
            'Tecnología': 15.0,
            'Hostelería': 8.0,
            'Ecommerce': 12.0,
            'Consultoría': 10.0,
            'Retail': 7.0,
            'Servicios': 9.0,
            'Industrial': 8.0,
            'Automoción': 7.0,
            'Otro': 9.0
        }
        multiplo_exit = multiplos_salida.get(self.sector, 9.0)
        valor_terminal_multiplo = ebitda_ultimo * multiplo_exit
        
        # Promedio ponderado de ambos métodos (60% Gordon, 40% Múltiplo)
        valor_terminal = valor_terminal_gg * 0.6 + valor_terminal_multiplo * 0.4
        
        # Valor presente del valor terminal
        vp_valor_terminal = valor_terminal / ((1 + wacc) ** len(fcf_df))
        
        # Enterprise Value
        enterprise_value = sum(valores_presentes) + vp_valor_terminal
        
        # 2. AJUSTES AL ENTERPRISE VALUE
        # Agregar: Caja y equivalentes (estimado como 10% de ventas último año)
        caja_estimada = fcf_df['Free Cash Flow'].iloc[:2].mean() * 0.5  # Conservador
        
        # Bridge to Equity Value
        # Calcular deuda total actual
        deuda_total = (self.prestamos_lp['principal'] + 
                        self.hipotecas['principal'] + 
                        self.polizas_credito['dispuesto'])

        equity_value = enterprise_value + caja_estimada - deuda_total
        
        # 3. ANÁLISIS DE MÚLTIPLOS COMPARABLES
        # Múltiplos actuales de mercado por sector
        ev_ventas_multiples = {
            'Tecnología': 4.5,
            'Hostelería': 1.2,
            'Ecommerce': 2.0,
            'Consultoría': 2.5,
            'Retail': 0.8,
            'Servicios': 1.5,
            'Industrial': 1.0,
            'Automoción': 0.7,
            'Otro': 1.5
        }
        
        # Estimación más conservadora de ventas del año 5
        crecimiento_anual = self._calcular_crecimiento_historico()
        if crecimiento_anual > 1:
            crecimiento_anual = crecimiento_anual / 100
        # Aplicar crecimiento compuesto más realista
        ventas_ultimo = self.ventas_historicas[-1] * ((1 + crecimiento_anual) ** 5)
        ev_por_multiplo_ventas = ventas_ultimo * ev_ventas_multiples.get(self.sector, 1.5)
        
        # 4. VALORACIÓN FINAL (Promedio ponderado)
        # 70% DCF, 30% Múltiplos (estándar en banca de inversión)
        valoracion_final = enterprise_value * 0.7 + ev_por_multiplo_ventas * 0.3
        
        # 5. ANÁLISIS DE SENSIBILIDAD
        # Escenarios de WACC
        wacc_bear = wacc + 0.02  # +2%
        wacc_bull = wacc - 0.01  # -1%
        
        # Recalcular para escenarios
        ev_bear = sum([fcf_df['Free Cash Flow'].iloc[i] / ((1 + wacc_bear) ** (i + 1)) 
                      for i in range(len(fcf_df))])
        ev_bear += (valor_terminal / ((1 + wacc_bear) ** len(fcf_df)))
        
        ev_bull = sum([fcf_df['Free Cash Flow'].iloc[i] / ((1 + wacc_bull) ** (i + 1)) 
                      for i in range(len(fcf_df))])
        ev_bull += (valor_terminal / ((1 + wacc_bull) ** len(fcf_df)))
        
        # Retornar diccionario completo estilo pitch deck
        return {
            # Valoración principal
            'valor_empresa': round(valoracion_final, 0),
            'valor_equity': round(equity_value, 0),
            
            # Componentes de valor
            'valor_presente_fcf': round(sum(valores_presentes), 0),
            'valor_terminal': round(valor_terminal, 0),
            'valor_terminal_pct': round((vp_valor_terminal / enterprise_value) * 100, 1),
            
            # Múltiplos implícitos
            'ev_ebitda_actual': round(enterprise_value / fcf_df['EBITDA'].iloc[0], 1),
            'ev_ebitda_salida': round(enterprise_value / ebitda_ultimo, 1),
            'ev_ventas': round(enterprise_value / ventas_ultimo, 1),
            
            # Parámetros clave
            'wacc_utilizado': round(wacc * 100, 1),
            'tasa_crecimiento_terminal': g * 100,
            'multiplo_salida_usado': multiplo_exit,
            
            # Análisis de sensibilidad
            'valoracion_escenario_bajo': round(ev_bear, 0),
            'valoracion_escenario_alto': round(ev_bull, 0),
            'rango_valoracion': f"€{ev_bear:,.0f} - €{ev_bull:,.0f}",
            
            # Métricas de retorno
            'tir_esperada': round(((max(0.01, equity_value) / max(1, self.ventas_historicas[-1] * 0.2)) ** (1/5) - 1) * 100, 1) if equity_value > 0 else 0,
            'money_multiple': round(equity_value / (self.ventas_historicas[-1] * 0.2), 1)
        }
    
    def generar_analisis_ia(self, pyl_df: pd.DataFrame, valoracion: Dict, financiacion_df: pd.DataFrame) -> Dict:
        """
        Genera un análisis inteligente con recomendaciones tipo consultoría
        """
        # Métricas clave para el análisis
        crecimiento_ventas = ((pyl_df['Ventas'].iloc[-1] / pyl_df['Ventas'].iloc[0]) ** (1/5) - 1) * 100
        margen_ebitda_inicial = pyl_df['EBITDA %'].iloc[0]
        margen_ebitda_final = pyl_df['EBITDA %'].iloc[-1]
        roi = valoracion.get('tir_esperada', 0)
        multiplo_ebitda = valoracion.get('ev_ebitda_salida', 0)
        deficit_max = financiacion_df['Exceso/(Déficit)'].min() if len(financiacion_df) > 0 else 0
        
        # AGREGAR AQUÍ - Datos macroeconómicos para el análisis
        contexto_macro = {
            'pib_medio': 1.95,  # Media 2024-2026
            'inflacion_media': 2.53,  # Media 2024-2026
            'euribor_medio': 2.67,  # Media 2024-2026
            'desempleo_medio': 11.7,  # Media 2024-2026
        }
        
        # Crecimiento esperado por sector (basado en informes oficiales)
        crecimiento_sectorial = {
            'Tecnología': 15.0,
            'Hostelería': 6.0,
            'Automoción': 4.0,
            'Ecommerce': 9.0,
            'Consultoría': 8.0,
            'Retail': 3.5,
            'Servicios': 5.0,
            'Industrial': 4.0,
            'Otro': 3.0
        }
        
        crecimiento_esperado_sector = crecimiento_sectorial.get(self.sector, 3.0)
        
        # Análisis por componentes
        analisis = {
            'resumen_ejecutivo': '',
            'fortalezas': [],
            'riesgos': [],
            'recomendaciones': [],
            'rating': '',
            'viabilidad': ''
        }
        
        # Evaluación de crecimiento con contexto sectorial
        diferencia_sector = crecimiento_ventas - crecimiento_esperado_sector
        
        if diferencia_sector > 5:
            analisis['fortalezas'].append(f"Crecimiento del {crecimiento_ventas:.1f}% anual, superando ampliamente la media del sector ({crecimiento_esperado_sector:.1f}%)")
        elif diferencia_sector > 0:
            analisis['fortalezas'].append(f"Crecimiento del {crecimiento_ventas:.1f}% anual, por encima de la media sectorial")
        else:
            analisis['riesgos'].append(f"Crecimiento del {crecimiento_ventas:.1f}% anual, por debajo del sector ({crecimiento_esperado_sector:.1f}%)")
        
        # Análisis del contexto macroeconómico
        if crecimiento_ventas > contexto_macro['pib_medio'] * 2:
            analisis['fortalezas'].append(f"Crecimiento muy superior al PIB esperado ({contexto_macro['pib_medio']:.1f}%)")
        
        # Evaluación del impacto de tipos de interés
        if contexto_macro['euribor_medio'] > 3 and margen_ebitda_final < 15:
            analisis['riesgos'].append(f"Márgenes ajustados en entorno de tipos altos (Euribor medio {contexto_macro['euribor_medio']:.1f}%)")
        # Evaluación de márgenes
        mejora_margen = margen_ebitda_final - margen_ebitda_inicial
        if mejora_margen > 5:
            analisis['fortalezas'].append(f"Excelente mejora de márgenes (+{mejora_margen:.1f}pp)")
        elif mejora_margen > 0:
            analisis['fortalezas'].append(f"Mejora progresiva de márgenes (+{mejora_margen:.1f}pp)")
        else:
            analisis['riesgos'].append("Márgenes estancados o decrecientes")
        
        # Evaluación financiera
        if deficit_max < 0:
            analisis['riesgos'].append(f"Déficit de financiación de €{abs(deficit_max):,.0f}")
            analisis['recomendaciones'].append("Negociar ampliación de líneas de crédito antes del inicio del proyecto")
        
        if roi > 25:
            analisis['fortalezas'].append(f"ROI excepcional del {roi:.1f}%")
        elif roi > 15:
            analisis['fortalezas'].append(f"ROI atractivo del {roi:.1f}%")
        else:
            analisis['riesgos'].append(f"ROI moderado del {roi:.1f}%")
        
        # Recomendaciones por sector
        recomendaciones_sector = {
            'Tecnología': [
                "Invertir en I+D para mantener ventaja competitiva",
                "Considerar modelo SaaS para ingresos recurrentes",
                "Explorar mercados internacionales"
            ],
            'Hostelería': [
                "Implementar sistema de gestión de inventarios para reducir mermas",
                "Desarrollar programa de fidelización",
                "Optimizar horarios según análisis de demanda"
            ],
            'Automoción': [
                "Diversificar proveedores para reducir riesgo",
                "Negociar plazos de pago más largos",
                "Considerar factoring para mejorar liquidez"
            ],
            'Ecommerce': [
                "Invertir en marketing digital y SEO",
                "Optimizar logística de última milla",
                "Desarrollar marketplace o dropshipping"
            ]
        }
        
        # Agregar recomendaciones sectoriales
        if self.sector in recomendaciones_sector:
            analisis['recomendaciones'].extend(recomendaciones_sector[self.sector])
        
        # Recomendaciones financieras generales
        if margen_ebitda_final < 15:
            analisis['recomendaciones'].append("Revisar estructura de costos para mejorar márgenes")
        
        if self.dias_cobro > 60:
            analisis['recomendaciones'].append("Implementar políticas de cobro más agresivas")

        # Recomendaciones basadas en contexto macroeconómico
        if contexto_macro['inflacion_media'] > 2.5:
            analisis['recomendaciones'].append("Implementar cláusulas de revisión de precios en contratos para protegerse de la inflación")
        
        if contexto_macro['euribor_medio'] > 2.5 and deficit_max < 0:
            analisis['recomendaciones'].append("Considerar financiación alternativa (crowdlending, factoring) ante tipos elevados")
        
        if contexto_macro['desempleo_medio'] > 10 and self.sector in ['Retail', 'Hostelería']:
            analisis['recomendaciones'].append("Aprovechar disponibilidad de talento y posibles ayudas a la contratación")
        
        # Recomendaciones específicas por comparación sectorial
        if diferencia_sector < -2:
            analisis['recomendaciones'].append(f"Analizar estrategias de los líderes del sector para acelerar crecimiento")
            analisis['recomendaciones'].append("Considerar alianzas estratégicas o adquisiciones para ganar cuota de mercado")
        
        # Determinar rating
        puntuacion = 0
        puntuacion += 2 if crecimiento_ventas > 15 else 1 if crecimiento_ventas > 5 else 0
        puntuacion += 2 if mejora_margen > 5 else 1 if mejora_margen > 0 else 0
        puntuacion += 2 if roi > 20 else 1 if roi > 10 else 0
        puntuacion += 1 if deficit_max >= 0 else 0
        
        if puntuacion >= 6:
            analisis['rating'] = '⭐⭐⭐⭐⭐ Excelente'
            analisis['viabilidad'] = 'ALTA'
        elif puntuacion >= 4:
            analisis['rating'] = '⭐⭐⭐⭐ Bueno'
            analisis['viabilidad'] = 'MEDIA-ALTA'
        elif puntuacion >= 2:
            analisis['rating'] = '⭐⭐⭐ Regular'
            analisis['viabilidad'] = 'MEDIA'
        else:
            analisis['rating'] = '⭐⭐ Mejorable'
            analisis['viabilidad'] = 'BAJA'
        
        # Generar resumen ejecutivo con contexto macro
        comparacion_sector = "por encima" if diferencia_sector > 0 else "por debajo"
        puntos_diferencia = abs(diferencia_sector)
        
        analisis['resumen_ejecutivo'] = f"""
        La empresa {self.nombre_empresa} del sector {self.sector} presenta un plan de negocio con 
        crecimiento proyectado del {crecimiento_ventas:.1f}% anual ({puntos_diferencia:.1f}pp {comparacion_sector} 
        de la media sectorial del {crecimiento_esperado_sector:.1f}%), alcanzando ventas de €{pyl_df['Ventas'].iloc[-1]:,.0f} 
        en el año 5. 
        
        En un contexto macroeconómico de crecimiento moderado (PIB {contexto_macro['pib_medio']:.1f}%), 
        inflación controlada ({contexto_macro['inflacion_media']:.1f}%) y tipos de interés en descenso 
        (Euribor medio {contexto_macro['euribor_medio']:.1f}%), la empresa muestra una evolución del EBITDA 
        desde {margen_ebitda_inicial:.1f}% hasta {margen_ebitda_final:.1f}%.
        
        La valoración estimada es de €{valoracion['valor_empresa']:,.0f} (múltiplo {multiplo_ebitda:.1f}x EBITDA), 
        con un ROI esperado del {roi:.1f}%. La viabilidad del proyecto se considera {analisis['viabilidad']}.
        """
        return analisis
     
    def generar_resumen_ejecutivo(self):
        """
        Genera un resumen ejecutivo en texto para el business plan
        """
        # Calcular métricas si no existen
        # Usar el P&L ya generado si existe, sino generar uno nuevo
        if self.pyl is not None:
            pyl = self.pyl
        else:
            self.generar_pyl(5)  # Generar con 5 años
            pyl = self.pyl
        metricas = self.calcular_metricas_clave(pyl)
        
        resumen = f"""
RESUMEN EJECUTIVO - {self.nombre_empresa}
{'=' * 60}

INFORMACIÓN GENERAL
------------------
Empresa: {self.nombre_empresa}
Sector: {self.sector}
Fecha de análisis: {datetime.now().strftime('%d/%m/%Y')}

SITUACIÓN ACTUAL
----------------
Ventas actuales: €{self.ventas_historicas[-1]:,.0f}
Crecimiento histórico: {self._calcular_crecimiento_historico():.1f}% anual
Estructura de costos:
  - Costos variables: {self.costos_variables_pct*100:.0f}% de ventas
  - Gastos de personal: €{self.gastos_personal:,.0f}
  - Gastos generales: €{self.gastos_generales:,.0f}
  - Gastos de marketing: €{self.gastos_marketing:,.0f}

PROYECCIONES A 5 AÑOS
---------------------
Ventas año 5: €{pyl['Ventas'].iloc[-1]:,.0f}
Crecimiento promedio anual: {metricas['crecimiento_ventas_promedio']:.1f}%

EBITDA año 5: €{pyl['EBITDA'].iloc[-1]:,.0f}
Margen EBITDA año 5: {pyl['EBITDA %'].iloc[-1]:.1f}%

Beneficio neto año 5: €{pyl['Beneficio Neto'].iloc[-1]:,.0f}
Margen neto año 5: {pyl['Beneficio Neto %'].iloc[-1]:.1f}%

INDICADORES CLAVE
-----------------
ROI proyectado: {metricas['roi_proyectado']:.1f}%
Periodo de recuperación: {metricas.get('payback_period', 'N/A')}
TIR del proyecto: {metricas.get('tir_proyecto', 'Por calcular')}

CONCLUSIONES
------------
El proyecto muestra una evolución {self._evaluar_evolucion(metricas)} con:
- Crecimiento sostenido de ventas
- Mejora progresiva de márgenes
- Generación positiva de caja
- Retorno atractivo sobre la inversión

RECOMENDACIONES
---------------
1. Mantener control estricto de costos variables
2. Optimizar gastos de personal mediante productividad
3. Incrementar inversión en marketing para acelerar crecimiento
4. Considerar financiación para capital de trabajo inicial
5. Monitorear métricas mensualmente vs. proyecciones

{'=' * 60}
Documento generado por Business Plan IA
"""
        return resumen

    def _calcular_crecimiento_historico(self):
        """Calcula el crecimiento histórico promedio"""
        ventas = self.ventas_historicas
        if len(ventas) < 2:
            return 0
        
        crecimiento_total = (ventas[-1] / ventas[0]) ** (1 / (len(ventas) - 1)) - 1
        return crecimiento_total * 100

    def _evaluar_evolucion(self, metricas):
        """Evalúa si la evolución es positiva, moderada o necesita mejoras"""
        roi = metricas['roi_proyectado']
        if roi > 25:
            return "muy positiva"
        elif roi > 15:
            return "positiva"
        elif roi > 10:
            return "moderada"
        else:
            return "que requiere optimización"   
        
    def realizar_valoracion_bancainversion(self) -> Dict:
        """
        Realiza valoración profesional con metodología de banca de inversión
        
        Returns:
            Dict con valoración completa incluyendo DCF, múltiplos y transacciones
        """
        try:
            # Asegurarse de que hay proyecciones generadas
            if self.pyl is None or self.cash_flow is None:
                raise ValueError("Debe generar proyecciones antes de valorar")
            
            # Realizar valoración completa
            valoracion = realizar_valoracion_profesional(self)
            
            # Añadir información adicional
            valoracion['empresa'] = self.nombre
            valoracion['sector'] = self.sector
            valoracion['fecha_valoracion'] = datetime.now().strftime('%Y-%m-%d')
            
            return valoracion
            
        except Exception as e:
            print(f"Error en valoración profesional: {e}")
            return {
                'error': str(e),
                'valoracion_disponible': False
            }
    
# Función de prueba
if __name__ == "__main__":
    
    # Datos de ejemplo para testing
    datos_prueba = {
        'nombre': 'PYME Test SL',
        'sector': 'Tecnología',
        'ventas_historicas': [500000, 650000, 780000],
        'costos_variables_pct': 0.6,
        'gastos_personal': 150000,
        'gastos_generales': 50000,
        'gastos_marketing': 30000,
        'otros_gastos': 20000
    }
    
    # Crear modelo y generar P&L
    modelo = ModeloFinanciero(datos_prueba)
    pyl = modelo.generar_pyl()
    
    print("\nP&L PROYECTADO:")
    print(pyl.to_string(index=False))
    
    print("\n" + modelo.generar_resumen_ejecutivo())