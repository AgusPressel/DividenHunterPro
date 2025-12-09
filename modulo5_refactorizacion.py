"""
================================================================================
MÓDULO 5: REFACTORIZACIÓN Y PRODUCCIÓN
================================================================================

CONCEPTO TEÓRICO:
-----------------
La refactorización es el proceso de mejorar el código SIN cambiar su
funcionalidad. En producción, esto es crítico para:

1. MANTENIBILIDAD: Código fácil de entender y modificar
2. ESCALABILIDAD: Preparado para crecer
3. ROBUSTEZ: Manejo de errores que previene crashes
4. TESTEABILIDAD: Código estructurado es más fácil de testear

PRINCIPIOS APLICADOS:
---------------------
1. DRY (Don't Repeat Yourself): Eliminar duplicación
2. Single Responsibility: Cada función/clase hace una cosa
3. Error Handling: Try/Except robusto en puntos críticos
4. Logging: Registrar eventos importantes
5. Configuración: Separar configuración del código

MANEJO DE ERRORES:
------------------
En aplicaciones financieras, el manejo de errores es CRÍTICO porque:
- Las APIs externas pueden fallar
- Los datos pueden estar incompletos
- Los usuarios pueden ingresar datos inválidos
- La red puede tener problemas

Estrategia:
- Try/Except en funciones que llaman APIs
- Validación de datos de entrada
- Mensajes de error claros para el usuario
- Logging para debugging
"""

import logging
from typing import Optional, Dict, List
import sys
import os

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('dividend_hunter.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


class ErrorHandler:
    """
    Clase utilitaria para manejo centralizado de errores.
    
    PRINCIPIO: Centralización del manejo de errores
    """
    
    @staticmethod
    def handle_api_error(func):
        """
        Decorador para manejar errores de APIs.
        
        Args:
            func: Función a decorar
        
        Returns:
            Función decorada con manejo de errores
        """
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Error en {func.__name__}: {e}", exc_info=True)
                return None
        return wrapper
    
    @staticmethod
    def validate_ticker_symbol(symbol: str) -> bool:
        """
        Valida que un símbolo de ticker sea válido.
        
        Args:
            symbol: Símbolo a validar
        
        Returns:
            True si es válido, False en caso contrario
        """
        if not symbol or not isinstance(symbol, str):
            return False
        
        symbol = symbol.strip().upper()
        
        # Validaciones básicas
        if len(symbol) < 1 or len(symbol) > 5:
            return False
        
        if not symbol.isalnum():
            return False
        
        return True
    
    @staticmethod
    def safe_float_conversion(value, default: float = 0.0) -> float:
        """
        Convierte un valor a float de forma segura.
        
        Args:
            value: Valor a convertir
            default: Valor por defecto si falla
        
        Returns:
            Float o valor por defecto
        """
        try:
            return float(value)
        except (ValueError, TypeError):
            logger.warning(f"No se pudo convertir {value} a float, usando {default}")
            return default


class Config:
    """
    Clase de configuración centralizada.
    
    PRINCIPIO: Separación de configuración y código
    """
    
    # Base de datos
    DB_PATH = os.getenv("DB_PATH", "dividend_hunter.db")
    
    # yfinance
    YFINANCE_TIMEOUT = int(os.getenv("YFINANCE_TIMEOUT", "10"))
    
    # Análisis
    LOOKBACK_MONTHS = int(os.getenv("LOOKBACK_MONTHS", "12"))
    MIN_PAYMENTS_MONTHLY = int(os.getenv("MIN_PAYMENTS_MONTHLY", "10"))
    MIN_PAYMENTS_QUARTERLY = int(os.getenv("MIN_PAYMENTS_QUARTERLY", "3"))
    
    # Streamlit
    PAGE_TITLE = "Dividend Hunter Pro"
    PAGE_ICON = "💰"
    
    # Visualización
    DEFAULT_TOP_N = int(os.getenv("DEFAULT_TOP_N", "10"))
    CHART_HEIGHT = int(os.getenv("CHART_HEIGHT", "600"))


class DataValidator:
    """
    Clase para validar datos financieros.
    
    PRINCIPIO: Validación centralizada
    """
    
    @staticmethod
    def validate_asset_metrics(metrics: Dict) -> bool:
        """
        Valida que las métricas de un activo sean válidas.
        
        Args:
            metrics: Diccionario con métricas
        
        Returns:
            True si es válido, False en caso contrario
        """
        if not metrics:
            logger.warning("Métricas vacías o None")
            return False
        
        required_fields = ['symbol', 'current_price', 'dividend_yield']
        
        for field in required_fields:
            if field not in metrics:
                logger.warning(f"Campo requerido faltante: {field}. Métricas: {list(metrics.keys())}")
                return False
        
        # Validar tipos y rangos
        if not isinstance(metrics['symbol'], str) or not metrics['symbol']:
            logger.warning(f"Símbolo inválido: {metrics.get('symbol')}")
            return False
        
        # Validar precio (puede ser None, pero si existe debe ser > 0)
        price = metrics.get('current_price')
        if price is None:
            logger.warning(f"Precio es None para {metrics.get('symbol')}")
            return False
        
        price = ErrorHandler.safe_float_conversion(price, default=-1.0)
        if price <= 0:
            logger.warning(f"Precio inválido: {price} para {metrics.get('symbol')}")
            return False
        
        # Validar yield (puede ser 0, pero debe estar en rango válido)
        yield_val = metrics.get('dividend_yield')
        if yield_val is None:
            logger.warning(f"Yield es None para {metrics.get('symbol')}")
            return False
        
        yield_val = ErrorHandler.safe_float_conversion(yield_val, default=-1.0)
        if yield_val < 0 or yield_val > 100:  # Yield razonable entre 0-100%
            logger.warning(f"Yield fuera de rango: {yield_val} para {metrics.get('symbol')}")
            return False
        
        logger.debug(f"✅ Métricas validadas correctamente para {metrics.get('symbol')}")
        return True


class PerformanceMonitor:
    """
    Clase para monitorear el rendimiento de operaciones.
    
    PRINCIPIO: Observabilidad en producción
    """
    
    @staticmethod
    def time_operation(func):
        """
        Decorador para medir el tiempo de ejecución.
        
        Args:
            func: Función a medir
        
        Returns:
            Función decorada con medición de tiempo
        """
        import time
        
        def wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            elapsed_time = time.time() - start_time
            logger.info(f"{func.__name__} ejecutado en {elapsed_time:.2f}s")
            return result
        return wrapper


# ============================================================================
# FUNCIONES DE UTILIDAD REFACTORIZADAS
# ============================================================================

def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """
    División segura que evita división por cero.
    
    Args:
        numerator: Numerador
        denominator: Denominador
        default: Valor por defecto si denominator es 0
    
    Returns:
        Resultado de la división o valor por defecto
    """
    try:
        if denominator == 0:
            logger.warning(f"División por cero evitada: {numerator} / {denominator}")
            return default
        return numerator / denominator
    except Exception as e:
        logger.error(f"Error en división: {e}")
        return default


def format_currency(value: float, decimals: int = 2) -> str:
    """
    Formatea un valor como moneda.
    
    Args:
        value: Valor a formatear
        decimals: Número de decimales
    
    Returns:
        String formateado (ej: "$123.45")
    """
    try:
        return f"${value:,.{decimals}f}"
    except Exception as e:
        logger.error(f"Error formateando moneda: {e}")
        return "$0.00"


def format_percentage(value: float, decimals: int = 2) -> str:
    """
    Formatea un valor como porcentaje.
    
    Args:
        value: Valor a formatear
        decimals: Número de decimales
    
    Returns:
        String formateado (ej: "12.34%")
    """
    try:
        return f"{value:.{decimals}f}%"
    except Exception as e:
        logger.error(f"Error formateando porcentaje: {e}")
        return "0.00%"


# ============================================================================
# EJEMPLO DE USO
# ============================================================================

if __name__ == "__main__":
    """
    Este módulo demuestra las utilidades de refactorización.
    """
    print("=" * 70)
    print("PRUEBA DEL MÓDULO 5: Refactorización y Producción")
    print("=" * 70)
    
    # Test de validación
    print("\n1. Validando símbolos de ticker...")
    test_symbols = ["AAPL", "MSFT", "123", "", "TOOLONG", "A1B2"]
    for symbol in test_symbols:
        is_valid = ErrorHandler.validate_ticker_symbol(symbol)
        status = "✅" if is_valid else "❌"
        print(f"   {status} {symbol}: {is_valid}")
    
    # Test de conversión segura
    print("\n2. Conversión segura de valores...")
    test_values = ["123.45", "abc", None, 456.78, "0"]
    for value in test_values:
        result = ErrorHandler.safe_float_conversion(value, -1.0)
        print(f"   {value} → {result}")
    
    # Test de formato
    print("\n3. Formateo de valores...")
    print(f"   Moneda: {format_currency(1234.567)}")
    print(f"   Porcentaje: {format_percentage(12.3456)}")
    
    # Test de validación de métricas
    print("\n4. Validando métricas de activo...")
    valid_metrics = {
        'symbol': 'AAPL',
        'current_price': 150.0,
        'dividend_yield': 0.5
    }
    invalid_metrics = {
        'symbol': 'AAPL',
        'current_price': -10.0,  # Precio negativo
        'dividend_yield': 0.5
    }
    
    print(f"   Métricas válidas: {DataValidator.validate_asset_metrics(valid_metrics)}")
    print(f"   Métricas inválidas: {DataValidator.validate_asset_metrics(invalid_metrics)}")
    
    # Mostrar configuración
    print("\n5. Configuración actual:")
    print(f"   DB Path: {Config.DB_PATH}")
    print(f"   Lookback Months: {Config.LOOKBACK_MONTHS}")
    print(f"   Default Top N: {Config.DEFAULT_TOP_N}")
    
    print("\n" + "=" * 70)
    print("✅ Módulo 5 funcionando correctamente")
    print("=" * 70)
    print("\n💡 Este módulo proporciona utilidades para producción:")
    print("   - Manejo robusto de errores")
    print("   - Validación de datos")
    print("   - Configuración centralizada")
    print("   - Logging y monitoreo")

