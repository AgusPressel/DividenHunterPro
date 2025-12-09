"""
================================================================================
MÓDULO 1: INGENIERÍA DE DATOS FINANCIEROS (Backend Logic)
================================================================================

CONCEPTO TEÓRICO:
-----------------
En finanzas, los dividendos son pagos periódicos que las empresas realizan a sus
accionistas. La frecuencia de pago es CRÍTICA para estrategias de inversión:

- Mensual: Ideal para flujo de caja constante (ej: REITs, algunos ETFs)
- Trimestral: Más común en acciones tradicionales (ej: Apple, Microsoft)

PROBLEMA REAL:
--------------
yfinance NO proporciona directamente la frecuencia de dividendos. Debemos
INFERIRLA analizando el historial de pagos del último año.

ESTRATEGIA:
-----------
1. Obtener todos los dividendos del último año (12 meses)
2. Contar cuántos pagos únicos hubo
3. Si hay 10-12 pagos → Mensual
4. Si hay 3-4 pagos → Trimestral
5. Si hay 0-2 pagos → Irregular o sin dividendos

Este es el "momento de aprendizaje" donde construimos lógica de negocio
que las APIs no resuelven por defecto.
"""

import yfinance as yf
from datetime import datetime, timedelta
from typing import Dict, Optional
import pandas as pd


class DividendAnalyzer:
    """
    Clase que encapsula la lógica de análisis de dividendos.
    
    PRINCIPIO DE DISEÑO: Separación de responsabilidades
    - Esta clase solo se encarga de obtener y analizar datos financieros
    - No maneja persistencia ni UI (eso viene en otros módulos)
    """
    
    def __init__(self):
        """Inicializa el analizador sin dependencias externas."""
        self.lookback_months = 12  # Ventana de análisis: 12 meses
    
    def get_ticker_data(self, symbol: str) -> Optional[yf.Ticker]:
        """
        Obtiene el objeto Ticker de yfinance.
        
        Args:
            symbol: Símbolo del activo (ej: 'AAPL', 'MSFT', 'O')
        
        Returns:
            Objeto Ticker o None si hay error
        """
        try:
            ticker = yf.Ticker(symbol.upper())
            # Hacemos una verificación rápida: intentamos obtener info básica
            info = ticker.info
            if not info or 'symbol' not in info:
                return None
            return ticker
        except Exception as e:
            print(f"Error obteniendo ticker {symbol}: {e}")
            return None
    
    def analyze_dividend_frequency(self, ticker: yf.Ticker) -> str:
        """
        DESAFÍO CLAVE: Determina la frecuencia de pago de dividendos.
        
        Esta es la función más importante del módulo. Analiza el historial
        de dividendos y clasifica la frecuencia.
        
        Args:
            ticker: Objeto Ticker de yfinance
        
        Returns:
            'mensual', 'trimestral', 'irregular', o 'sin_dividendos'
        """
        try:
            # Obtener historial de dividendos (Series de pandas con fechas como índice)
            dividends = ticker.dividends
            
            if dividends.empty:
                return 'sin_dividendos'
            
            # Calcular fecha de corte: hace 12 meses desde hoy
            # Usamos pd.Timestamp para compatibilidad con índices de pandas con timezone
            cutoff_date = pd.Timestamp.now() - pd.Timedelta(days=365)
            
            # Filtrar dividendos del último año
            # Dividends es una Series con índice DateTimeIndex (puede tener timezone)
            # Solución: Convertir el índice a timezone-naive si tiene timezone
            # para evitar errores de comparación con datetime sin timezone
            if dividends.index.tz is not None:
                # Convertir índice de timezone-aware a timezone-naive
                # Primero convertimos a UTC, luego removemos el timezone
                dividends = dividends.copy()
                dividends.index = dividends.index.tz_convert('UTC').tz_localize(None)
                # Asegurar que cutoff_date también sea timezone-naive
                cutoff_date = cutoff_date.tz_localize(None) if cutoff_date.tz is not None else cutoff_date
            
            recent_dividends = dividends[dividends.index >= cutoff_date]
            
            if recent_dividends.empty:
                return 'sin_dividendos'
            
            # Contar pagos únicos (puede haber múltiples pagos el mismo día)
            # Agrupamos por fecha para contar días únicos con pagos
            unique_payment_dates = recent_dividends.index.normalize().unique()
            payment_count = len(unique_payment_dates)
            
            # LÓGICA DE CLASIFICACIÓN (Regla de negocio financiera)
            if payment_count >= 10:
                # 10-12 pagos en 12 meses = patrón mensual
                return 'mensual'
            elif payment_count >= 3:
                # 3-4 pagos en 12 meses = patrón trimestral
                return 'trimestral'
            else:
                # 1-2 pagos = irregular o especial
                return 'irregular'
                
        except Exception as e:
            print(f"Error analizando frecuencia de dividendos: {e}")
            return 'irregular'
    
    def get_asset_metrics(self, symbol: str) -> Optional[Dict]:
        """
        Obtiene todas las métricas financieras relevantes de un activo.
        
        Esta función orquesta la obtención de datos y el análisis.
        Es el "punto de entrada" principal de este módulo.
        
        Args:
            symbol: Símbolo del activo
        
        Returns:
            Diccionario con métricas o None si hay error
        """
        ticker = self.get_ticker_data(symbol)
        
        if not ticker:
            return None
        
        try:
            # Obtener información básica del activo
            info = ticker.info
            
            # Obtener precio actual (último precio de cierre)
            hist = ticker.history(period="1d")
            if hist.empty:
                # Intentar obtener precio de info si no hay historial
                current_price = info.get('currentPrice') or info.get('regularMarketPrice')
                if current_price:
                    current_price = float(current_price)
                else:
                    print(f"⚠️ No se pudo obtener precio para {symbol}")
                    return None
            else:
                current_price = float(hist['Close'].iloc[-1])
            
            # Análisis de dividendos (LA FUNCIÓN CLAVE)
            dividend_frequency = self.analyze_dividend_frequency(ticker)
            
            # Calcular dividend yield anual
            dividends = ticker.dividends
            if not dividends.empty:
                # Sumar dividendos del último año
                # Usamos pd.Timestamp para compatibilidad con índices de pandas con timezone
                cutoff_date = pd.Timestamp.now() - pd.Timedelta(days=365)
                
                # Manejar timezone del índice (convertir a timezone-naive si es necesario)
                if dividends.index.tz is not None:
                    dividends = dividends.copy()
                    dividends.index = dividends.index.tz_convert('UTC').tz_localize(None)
                    cutoff_date = cutoff_date.tz_localize(None) if cutoff_date.tz is not None else cutoff_date
                
                recent_dividends = dividends[dividends.index >= cutoff_date]
                annual_dividend = float(recent_dividends.sum())
                
                # Obtener fechas de pago del último año (meses en que se pagaron dividendos)
                # Extraer los meses únicos de las fechas de pago
                payment_months = []
                if not recent_dividends.empty:
                    # Obtener meses únicos de las fechas de pago
                    payment_dates = recent_dividends.index
                    payment_months = sorted(list(set([date.month for date in payment_dates])))
                
                # Dividend Yield = (Dividendos Anuales / Precio) * 100
                dividend_yield = (annual_dividend / current_price * 100) if current_price else 0.0
            else:
                annual_dividend = 0.0
                dividend_yield = 0.0
                payment_months = []
            
            # Construir diccionario de métricas
            metrics = {
                'symbol': symbol.upper(),
                'name': info.get('longName', symbol),
                'sector': info.get('sector', 'N/A'),
                'industry': info.get('industry', 'N/A'),
                'current_price': current_price,
                'annual_dividend': round(annual_dividend, 2),
                'dividend_yield': round(dividend_yield, 2),
                'dividend_frequency': dividend_frequency,
                'dividend_payment_months': payment_months,  # Lista de meses (1-12) en que se pagan dividendos
                'market_cap': info.get('marketCap', 0),
                'last_updated': datetime.now().isoformat()
            }
            
            return metrics
            
        except Exception as e:
            print(f"Error obteniendo métricas para {symbol}: {e}")
            return None


# ============================================================================
# EJEMPLO DE USO (Para testing durante el desarrollo)
# ============================================================================

if __name__ == "__main__":
    """
    Este bloque permite ejecutar el módulo directamente para pruebas.
    En producción, esta lógica se integrará con otros módulos.
    """
    analyzer = DividendAnalyzer()
    
    # Test con diferentes tipos de activos
    test_symbols = ['O', 'AAPL', 'MSFT', 'T']
    
    print("=" * 70)
    print("PRUEBA DEL MÓDULO 1: Análisis de Dividendos")
    print("=" * 70)
    
    for symbol in test_symbols:
        print(f"\n📊 Analizando {symbol}...")
        metrics = analyzer.get_asset_metrics(symbol)
        
        if metrics:
            print(f"  Nombre: {metrics['name']}")
            print(f"  Precio: ${metrics['current_price']:.2f}")
            print(f"  Dividend Yield: {metrics['dividend_yield']:.2f}%")
            print(f"  Frecuencia: {metrics['dividend_frequency'].upper()}")
            print(f"  Dividendo Anual: ${metrics['annual_dividend']:.2f}")
        else:
            print(f"  ❌ No se pudieron obtener datos para {symbol}")
    
    print("\n" + "=" * 70)
    print("✅ Módulo 1 funcionando correctamente")
    print("=" * 70)

