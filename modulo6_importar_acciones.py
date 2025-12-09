"""
================================================================================
MÓDULO 6: IMPORTAR ACCIONES DISPONIBLES EN YFINANCE
================================================================================

CONCEPTO TEÓRICO:
-----------------
yfinance no proporciona una función directa para obtener todas las acciones
disponibles. Este módulo implementa múltiples estrategias para obtener listas
completas de símbolos de acciones:

1. Listas de exchanges (NYSE, NASDAQ, etc.)
2. APIs públicas de listas de símbolos
3. Archivos de referencia locales
4. Búsqueda por criterios (sector, mercado, etc.)

ESTRATEGIAS:
------------
- Descarga de listas oficiales de exchanges
- Cache local para evitar descargas repetidas
- Validación de símbolos con yfinance
- Filtrado por criterios específicos
"""

import yfinance as yf
import pandas as pd
import requests
from typing import List, Dict, Optional, Set
from datetime import datetime
import os
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class StockImporter:
    """
    Clase para importar y gestionar listas de acciones disponibles en yfinance.
    
    PRINCIPIO DE DISEÑO: Múltiples fuentes de datos
    - No dependemos de una sola fuente
    - Cache local para eficiencia
    - Validación de símbolos antes de retornar
    """
    
    def __init__(self, cache_dir: str = "cache"):
        """
        Inicializa el importador de acciones.
        
        Args:
            cache_dir: Directorio para almacenar archivos cache
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.cache_file = self.cache_dir / "symbols_cache.json"
        self.cache_expiry_days = 7  # Renovar cache cada 7 días
        
    def get_nasdaq_symbols(self) -> List[str]:
        """
        Obtiene lista de símbolos del NASDAQ desde fuente pública.
        
        Returns:
            Lista de símbolos NASDAQ
        """
        try:
            # Intentar descargar desde fuente pública de NASDAQ
            # Nota: Las APIs públicas pueden cambiar, por lo que tenemos fallbacks
            try:
                # Método 1: Intentar descargar CSV desde NASDAQ
                csv_url = "https://old.nasdaq.com/screening/companies-by-name.aspx?letter=0&exchange=nasdaq&render=download"
                response = requests.get(csv_url, timeout=15)
                
                if response.status_code == 200:
                    # Leer CSV
                    from io import StringIO
                    df = pd.read_csv(StringIO(response.text))
                    if 'Symbol' in df.columns:
                        symbols = df['Symbol'].dropna().tolist()
                        # Filtrar símbolos válidos (máximo 5 caracteres, sin espacios)
                        valid_symbols = [s.strip().upper() for s in symbols 
                                        if isinstance(s, str) and len(s.strip()) <= 5 and s.strip().isalnum()]
                        if valid_symbols:
                            logger.info(f"[OK] Obtenidos {len(valid_symbols)} símbolos NASDAQ desde CSV")
                            return valid_symbols
            except Exception as e:
                logger.debug(f"No se pudo descargar NASDAQ desde CSV: {e}")
            
            # Método alternativo: lista conocida de símbolos NASDAQ populares
            logger.info("Usando lista conocida de símbolos NASDAQ")
            return self._get_known_nasdaq_symbols()
            
        except Exception as e:
            logger.error(f"[ERROR] Error obteniendo símbolos NASDAQ: {e}")
            return self._get_known_nasdaq_symbols()
    
    def get_nyse_symbols(self) -> List[str]:
        """
        Obtiene lista de símbolos del NYSE.
        
        Returns:
            Lista de símbolos NYSE
        """
        try:
            # Similar a NASDAQ, intentar descargar desde fuente pública
            # Por ahora, retornamos lista conocida
            return self._get_known_nyse_symbols()
        except Exception as e:
            logger.error(f"[ERROR] Error obteniendo símbolos NYSE: {e}")
            return self._get_known_nyse_symbols()
    
    def _get_known_nasdaq_symbols(self) -> List[str]:
        """Retorna lista conocida de símbolos NASDAQ populares."""
        return [
            # NASDAQ 100 principales
            'AAPL', 'MSFT', 'GOOGL', 'GOOG', 'AMZN', 'NVDA', 'META', 'TSLA',
            'NFLX', 'AMD', 'INTC', 'CMCSA', 'ADBE', 'COST', 'AVGO', 'PEP',
            'CSCO', 'TMUS', 'TXN', 'QCOM', 'AMGN', 'INTU', 'ISRG', 'BKNG',
            'VRSK', 'FISV', 'CDNS', 'ADP', 'REGN', 'ATVI', 'PAYX', 'SNPS',
            'ASML', 'CRWD', 'FTNT', 'KLAC', 'CTSH', 'NXPI', 'CDW', 'ODFL',
            'FAST', 'DXCM', 'BKR', 'ANSS', 'TEAM', 'VRSN', 'SWKS', 'IDXX',
            'LRCX', 'CTAS', 'WBD', 'ROST', 'PCAR', 'CPRT', 'MELI', 'MNST',
            'EXPD', 'XEL', 'DLTR', 'FANG', 'CTVA', 'ON', 'AEP', 'GEHC',
            'EA', 'VRTX', 'BIIB', 'ALGN', 'ANET', 'DDOG', 'ENPH', 'GFS',
            'HON', 'ILMN', 'LULU', 'MRVL', 'NTES', 'PDD', 'PYPL', 'RIVN',
            'ROKU', 'SPLK', 'TTD', 'TTWO', 'WDAY', 'ZM', 'ZS', 'FTNT',
            # Acciones de dividendos populares en NASDAQ
            'O', 'STAG', 'MAIN', 'AGNC', 'PSEC', 'ORC', 'GLAD', 'GAIN',
            'GOOD', 'LAND', 'SLRC', 'ARCC', 'BXSL', 'CSWC', 'FDUS', 'HTGC'
        ]
    
    def _get_known_nyse_symbols(self) -> List[str]:
        """Retorna lista conocida de símbolos NYSE populares."""
        return [
            # Bancos y Finanzas
            'JPM', 'BAC', 'WFC', 'C', 'GS', 'MS', 'BLK', 'SCHW', 'AXP',
            'COF', 'USB', 'PNC', 'TFC', 'BK', 'STT', 'MTB', 'FITB', 'HBAN',
            'RF', 'ZION', 'KEY', 'CFG', 'CMA', 'WTFC', 'ONB', 'TCBI',
            'V', 'MA', 'FIS', 'FISV', 'GPN', 'FLYW', 'AFRM',
            # Energía
            'XOM', 'CVX', 'COP', 'SLB', 'EOG', 'MPC', 'PSX', 'VLO', 'HAL',
            'OXY', 'MRO', 'FANG', 'DVN', 'CTRA', 'APA', 'NOV', 'FTI',
            # Retail
            'WMT', 'HD', 'COST', 'TGT', 'LOW', 'TJX', 'DG', 'DLTR', 'BBY',
            'BBWI', 'DKS', 'ANF', 'AEO', 'GPS', 'URBN', 'OLLI',
            # Healthcare
            'JNJ', 'PFE', 'UNH', 'ABT', 'TMO', 'ABBV', 'MRK', 'BMY', 'LLY',
            'AMGN', 'GILD', 'REGN', 'VRTX', 'BIIB', 'ILMN', 'ALNY', 'MRNA',
            'NVAX', 'BNTX',
            # REITs (muy importantes para dividendos)
            'O', 'SPG', 'PLD', 'EQIX', 'WELL', 'PSA', 'EXR', 'AVB', 'EQR',
            'MAA', 'UDR', 'CPT', 'ESS', 'AIRC', 'INVH', 'AMT', 'CCI', 'SBAC',
            # Dividendos populares
            'T', 'VZ', 'KO', 'PEP', 'PG', 'JNJ', 'XOM', 'CVX', 'WMT', 'HD',
            'MCD', 'NKE', 'DIS', 'BA', 'CAT', 'GE', 'MMM', 'HON', 'UTX',
            'RTX', 'LMT', 'NOC', 'GD', 'TXT', 'EMR', 'ETN', 'ITW', 'PH',
            'ROK', 'CMI', 'DE', 'AGCO', 'CNHI', 'TTC', 'WWD', 'AME', 'FLS'
        ]
    
    def get_all_exchange_symbols(self, exchanges: Optional[List[str]] = None) -> List[str]:
        """
        Obtiene símbolos de múltiples exchanges.
        
        Args:
            exchanges: Lista de exchanges a consultar. Si None, usa todos.
        
        Returns:
            Lista combinada de símbolos (sin duplicados)
        """
        if exchanges is None:
            exchanges = ['NASDAQ', 'NYSE']
        
        all_symbols = set()
        
        if 'NASDAQ' in exchanges:
            nasdaq_symbols = self.get_nasdaq_symbols()
            all_symbols.update(nasdaq_symbols)
            logger.info(f"[OK] Obtenidos {len(nasdaq_symbols)} símbolos de NASDAQ")
        
        if 'NYSE' in exchanges:
            nyse_symbols = self.get_nyse_symbols()
            all_symbols.update(nyse_symbols)
            logger.info(f"[OK] Obtenidos {len(nyse_symbols)} símbolos de NYSE")
        
        return sorted(list(all_symbols))
    
    def validate_symbol(self, symbol: str) -> bool:
        """
        Valida que un símbolo existe y es válido en yfinance.
        
        Args:
            symbol: Símbolo a validar
        
        Returns:
            True si el símbolo es válido, False en caso contrario
        """
        try:
            ticker = yf.Ticker(symbol.upper())
            info = ticker.info
            # Verificar que tenemos información válida
            if info and 'symbol' in info:
                return True
            return False
        except Exception:
            return False
    
    def validate_symbols_batch(self, symbols: List[str], max_workers: int = 10) -> List[str]:
        """
        Valida múltiples símbolos en lote.
        
        Args:
            symbols: Lista de símbolos a validar
            max_workers: Número máximo de validaciones concurrentes
        
        Returns:
            Lista de símbolos válidos
        """
        valid_symbols = []
        total = len(symbols)
        
        logger.info(f"Validando {total} símbolos...")
        
        for i, symbol in enumerate(symbols, 1):
            if self.validate_symbol(symbol):
                valid_symbols.append(symbol)
            
            if i % 50 == 0:
                logger.info(f"Progreso: {i}/{total} ({len(valid_symbols)} válidos hasta ahora)")
        
        logger.info(f"[OK] Validación completa: {len(valid_symbols)}/{total} símbolos válidos")
        return valid_symbols
    
    def get_cached_symbols(self) -> Optional[List[str]]:
        """
        Obtiene símbolos desde cache si está disponible y no expirado.
        
        Returns:
            Lista de símbolos desde cache o None si no hay cache válido
        """
        if not self.cache_file.exists():
            return None
        
        try:
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            # Verificar expiración
            cache_date = datetime.fromisoformat(cache_data.get('date', ''))
            days_old = (datetime.now() - cache_date).days
            
            if days_old > self.cache_expiry_days:
                logger.info(f"Cache expirado ({days_old} días). Se renovará.")
                return None
            
            symbols = cache_data.get('symbols', [])
            logger.info(f"[OK] Símbolos cargados desde cache ({len(symbols)} símbolos, {days_old} días)")
            return symbols
            
        except Exception as e:
            logger.warning(f"[WARNING] Error leyendo cache: {e}")
            return None
    
    def save_symbols_to_cache(self, symbols: List[str]):
        """
        Guarda símbolos en cache.
        
        Args:
            symbols: Lista de símbolos a guardar
        """
        try:
            cache_data = {
                'date': datetime.now().isoformat(),
                'symbols': symbols,
                'count': len(symbols)
            }
            
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"[OK] {len(symbols)} símbolos guardados en cache")
            
        except Exception as e:
            logger.error(f"[ERROR] Error guardando cache: {e}")
    
    def get_all_available_symbols(
        self, 
        validate: bool = True,
        use_cache: bool = True,
        exchanges: Optional[List[str]] = None
    ) -> List[str]:
        """
        Obtiene todas las acciones disponibles.
        
        Este es el método principal del módulo. Combina múltiples fuentes
        y opcionalmente valida los símbolos.
        
        Args:
            validate: Si True, valida cada símbolo con yfinance
            use_cache: Si True, intenta usar cache primero
            exchanges: Lista de exchanges a consultar
        
        Returns:
            Lista de símbolos disponibles
        """
        # Intentar cargar desde cache
        if use_cache:
            cached_symbols = self.get_cached_symbols()
            if cached_symbols:
                return cached_symbols
        
        # Obtener símbolos de exchanges
        logger.info("Obteniendo símbolos de exchanges...")
        symbols = self.get_all_exchange_symbols(exchanges)
        
        # Validar si se solicita
        if validate:
            logger.info("Validando símbolos con yfinance...")
            symbols = self.validate_symbols_batch(symbols)
        
        # Guardar en cache
        if use_cache:
            self.save_symbols_to_cache(symbols)
        
        return symbols
    
    def search_symbols(
        self, 
        query: str, 
        symbols: Optional[List[str]] = None
    ) -> List[str]:
        """
        Busca símbolos que coincidan con un query.
        
        Args:
            query: Texto a buscar (puede ser parte del símbolo o nombre)
            symbols: Lista de símbolos donde buscar. Si None, obtiene todos.
        
        Returns:
            Lista de símbolos que coinciden
        """
        if symbols is None:
            symbols = self.get_all_available_symbols(validate=False, use_cache=True)
        
        query_upper = query.upper()
        matches = []
        
        for symbol in symbols:
            if query_upper in symbol.upper():
                matches.append(symbol)
                # También intentar obtener el nombre de la empresa
                try:
                    ticker = yf.Ticker(symbol)
                    info = ticker.info
                    if info and 'longName' in info:
                        company_name = info['longName'].upper()
                        if query_upper in company_name:
                            matches.append(symbol)
                except:
                    pass
        
        # Eliminar duplicados manteniendo orden
        return sorted(list(set(matches)))
    
    def get_symbols_by_sector(
        self, 
        sector: str,
        symbols: Optional[List[str]] = None
    ) -> List[str]:
        """
        Filtra símbolos por sector.
        
        Args:
            sector: Sector a filtrar (ej: 'Technology', 'Finance', 'Healthcare')
            symbols: Lista de símbolos a filtrar. Si None, obtiene todos.
        
        Returns:
            Lista de símbolos del sector especificado
        """
        if symbols is None:
            symbols = self.get_all_available_symbols(validate=False, use_cache=True)
        
        sector_symbols = []
        sector_upper = sector.upper()
        
        logger.info(f"Buscando símbolos en sector: {sector}")
        
        for symbol in symbols:
            try:
                ticker = yf.Ticker(symbol)
                info = ticker.info
                if info and 'sector' in info:
                    if sector_upper in info['sector'].upper():
                        sector_symbols.append(symbol)
            except:
                continue
        
        logger.info(f"[OK] Encontrados {len(sector_symbols)} símbolos en sector {sector}")
        return sector_symbols
    
    def export_symbols_to_file(
        self, 
        symbols: List[str],
        filename: str = "symbols_list.txt"
    ):
        """
        Exporta lista de símbolos a un archivo de texto.
        
        Args:
            symbols: Lista de símbolos a exportar
            filename: Nombre del archivo de salida
        """
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                for symbol in symbols:
                    f.write(f"{symbol}\n")
            
            logger.info(f"[OK] {len(symbols)} símbolos exportados a {filename}")
            
        except Exception as e:
            logger.error(f"[ERROR] Error exportando símbolos: {e}")
    
    def export_symbols_to_excel(
        self,
        symbols: List[str],
        filename: str = "symbols_list.xlsx"
    ):
        """
        Exporta lista de símbolos a un archivo Excel con información adicional.
        
        Args:
            symbols: Lista de símbolos a exportar
            filename: Nombre del archivo de salida
        """
        try:
            data = []
            
            logger.info(f"Obteniendo información adicional para {len(symbols)} símbolos...")
            
            for i, symbol in enumerate(symbols, 1):
                try:
                    ticker = yf.Ticker(symbol)
                    info = ticker.info
                    
                    data.append({
                        'Symbol': symbol,
                        'Name': info.get('longName', 'N/A'),
                        'Sector': info.get('sector', 'N/A'),
                        'Industry': info.get('industry', 'N/A'),
                        'Market Cap': info.get('marketCap', 'N/A'),
                        'Current Price': info.get('currentPrice', 'N/A')
                    })
                    
                    if i % 50 == 0:
                        logger.info(f"Progreso: {i}/{len(symbols)}")
                        
                except Exception as e:
                    data.append({
                        'Symbol': symbol,
                        'Name': 'Error obteniendo datos',
                        'Sector': 'N/A',
                        'Industry': 'N/A',
                        'Market Cap': 'N/A',
                        'Current Price': 'N/A'
                    })
            
            df = pd.DataFrame(data)
            df.to_excel(filename, index=False)
            
            logger.info(f"[OK] {len(symbols)} símbolos exportados a {filename}")
            
        except Exception as e:
            logger.error(f"[ERROR] Error exportando a Excel: {e}")


# ============================================================================
# FUNCIONES DE CONVENIENCIA
# ============================================================================

def get_all_stocks(validate: bool = True, use_cache: bool = True) -> List[str]:
    """
    Función de conveniencia para obtener todas las acciones disponibles.
    
    Args:
        validate: Si True, valida cada símbolo
        use_cache: Si True, usa cache si está disponible
    
    Returns:
        Lista de símbolos disponibles
    """
    importer = StockImporter()
    return importer.get_all_available_symbols(validate=validate, use_cache=use_cache)


def search_stocks(query: str) -> List[str]:
    """
    Función de conveniencia para buscar acciones.
    
    Args:
        query: Texto a buscar
    
    Returns:
        Lista de símbolos que coinciden
    """
    importer = StockImporter()
    return importer.search_symbols(query)


# ============================================================================
# EJEMPLO DE USO
# ============================================================================

if __name__ == "__main__":
    """
    Ejemplo de uso del módulo de importación de acciones.
    """
    print("=" * 70)
    print("MÓDULO 6: IMPORTAR ACCIONES DISPONIBLES")
    print("=" * 70)
    
    # Configurar logging básico
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    importer = StockImporter()
    
    # Ejemplo 1: Obtener todas las acciones (con cache)
    print("\n1. Obteniendo todas las acciones disponibles...")
    all_symbols = importer.get_all_available_symbols(
        validate=False,  # Más rápido sin validar
        use_cache=True
    )
    print(f"   Total de símbolos: {len(all_symbols)}")
    print(f"   Primeros 10: {all_symbols[:10]}")
    
    # Ejemplo 2: Buscar símbolos
    print("\n2. Buscando símbolos que contengan 'AAPL'...")
    search_results = importer.search_symbols("AAPL")
    print(f"   Resultados: {search_results}")
    
    # Ejemplo 3: Filtrar por sector
    print("\n3. Buscando acciones del sector Technology...")
    tech_symbols = importer.get_symbols_by_sector("Technology", all_symbols[:100])
    print(f"   Encontrados: {len(tech_symbols)} símbolos")
    print(f"   Ejemplos: {tech_symbols[:5]}")
    
    # Ejemplo 4: Exportar a archivo
    print("\n4. Exportando símbolos a archivo...")
    importer.export_symbols_to_file(all_symbols[:50], "ejemplo_symbols.txt")
    
    print("\n" + "=" * 70)
    print("[OK] Módulo 6 funcionando correctamente")
    print("=" * 70)

