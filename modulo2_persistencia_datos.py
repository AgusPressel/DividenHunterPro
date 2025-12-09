"""
================================================================================
MÓDULO 2: PERSISTENCIA DE DATOS (SQL & Python)
================================================================================

CONCEPTO TEÓRICO:
-----------------
En aplicaciones financieras, necesitamos persistir datos para:
1. Evitar llamadas repetidas a APIs (costosas y lentas)
2. Mantener historial de análisis
3. Permitir análisis comparativos offline

SQLite es perfecto para este proyecto porque:
- No requiere servidor (archivo local)
- Es ligero y rápido
- Soporta SQL estándar
- Ideal para prototipos y aplicaciones pequeñas/medianas

PATRÓN UPSERT:
--------------
Upsert = UPDATE + INSERT
- Si el registro existe → Actualizar
- Si no existe → Insertar

En finanzas, esto es crítico porque los precios cambian constantemente,
pero queremos mantener un solo registro por activo.
"""

import sqlite3
from datetime import datetime
from typing import Dict, Optional, List
import json
import logging

logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Clase que encapsula toda la lógica de persistencia.
    
    PRINCIPIO DE DISEÑO: Encapsulación
    - Toda la interacción con la BD está en esta clase
    - El resto de la aplicación no necesita conocer SQL
    """
    
    def __init__(self, db_path: str = "dividend_hunter.db"):
        """
        Inicializa la conexión a la base de datos.
        
        Args:
            db_path: Ruta al archivo de base de datos SQLite
        """
        self.db_path = db_path
        self.conn = None
        self._initialize_database()
    
    def _ensure_connection(self):
        """
        Asegura que la conexión a la BD esté abierta.
        
        En Streamlit, las conexiones pueden cerrarse entre ejecuciones,
        por lo que necesitamos verificar y restaurar la conexión si es necesario.
        """
        try:
            if self.conn is None:
                self._initialize_database()
            else:
                # Verificar si la conexión sigue activa haciendo una consulta simple
                cursor = self.conn.cursor()
                cursor.execute("SELECT 1")
                cursor.fetchone()
        except (sqlite3.Error, AttributeError, sqlite3.ProgrammingError):
            # La conexión se cerró o hay un error, reinicializar
            try:
                if self.conn:
                    self.conn.close()
            except:
                pass
            self._initialize_database()
    
    def _initialize_database(self):
        """
        Crea la conexión y la tabla si no existe.
        
        Este método es privado (prefijo _) porque solo se usa internamente.
        """
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row  # Permite acceso por nombre de columna
            
            # Crear tabla si no existe
            cursor = self.conn.cursor()
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS assets (
                    symbol TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    sector TEXT,
                    industry TEXT,
                    current_price REAL,
                    annual_dividend REAL,
                    dividend_yield REAL,
                    dividend_frequency TEXT,
                    dividend_payment_months TEXT,
                    market_cap INTEGER,
                    platforms TEXT,
                    last_updated TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Agregar columnas si no existen (para bases de datos existentes)
            try:
                cursor.execute("ALTER TABLE assets ADD COLUMN platforms TEXT")
            except sqlite3.OperationalError:
                pass
            
            try:
                cursor.execute("ALTER TABLE assets ADD COLUMN dividend_payment_months TEXT")
            except sqlite3.OperationalError:
                pass
            
            # Crear tabla de portfolios
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS portfolios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    description TEXT,
                    selected_symbols TEXT NOT NULL,
                    shares_data TEXT NOT NULL,
                    tax_rates_data TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Crear índices para búsquedas rápidas
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_dividend_frequency 
                ON assets(dividend_frequency)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_dividend_yield 
                ON assets(dividend_yield)
            """)
            
            self.conn.commit()
            logger.info(f"✅ Base de datos inicializada: {self.db_path}")
            print(f"✅ Base de datos inicializada: {self.db_path}")
            
        except sqlite3.Error as e:
            logger.error(f"❌ Error inicializando base de datos: {e}")
            print(f"❌ Error inicializando base de datos: {e}")
            raise
    
    def upsert_asset(self, asset_data: Dict) -> bool:
        """
        FUNCIÓN CLAVE: Upsert (Insertar o Actualizar).
        
        Esta es la función más importante del módulo. Implementa el patrón
        Upsert que es fundamental en aplicaciones financieras.
        
        Args:
            asset_data: Diccionario con los datos del activo
        
        Returns:
            True si la operación fue exitosa, False en caso contrario
        """
        try:
            # Validar que tenemos los datos necesarios
            if not asset_data or 'symbol' not in asset_data:
                logger.error("❌ Datos de activo inválidos: falta 'symbol'")
                return False
            
            symbol = asset_data['symbol']
            logger.info(f"Intentando guardar activo: {symbol}")
            
            self._ensure_connection()
            cursor = self.conn.cursor()
            
            # Verificar si el activo ya existe
            cursor.execute("SELECT symbol FROM assets WHERE symbol = ?", (symbol,))
            exists = cursor.fetchone() is not None
            logger.debug(f"Activo {symbol} existe: {exists}")
            
            if exists:
                # UPDATE: Actualizar registro existente
                cursor.execute("""
                    UPDATE assets 
                    SET name = ?,
                        sector = ?,
                        industry = ?,
                        current_price = ?,
                        annual_dividend = ?,
                        dividend_yield = ?,
                        dividend_frequency = ?,
                        dividend_payment_months = ?,
                        market_cap = ?,
                        platforms = COALESCE(?, platforms),
                        last_updated = ?
                    WHERE symbol = ?
                """, (
                    asset_data.get('name'),
                    asset_data.get('sector'),
                    asset_data.get('industry'),
                    asset_data.get('current_price'),
                    asset_data.get('annual_dividend'),
                    asset_data.get('dividend_yield'),
                    asset_data.get('dividend_frequency'),
                    self._format_payment_months(asset_data.get('dividend_payment_months')),
                    asset_data.get('market_cap'),
                    asset_data.get('platforms'),
                    asset_data.get('last_updated'),
                    asset_data['symbol']
                ))
                operation = "Actualizado"
            else:
                # INSERT: Crear nuevo registro
                cursor.execute("""
                    INSERT INTO assets 
                    (symbol, name, sector, industry, current_price, 
                     annual_dividend, dividend_yield, dividend_frequency, 
                     dividend_payment_months, market_cap, platforms, last_updated)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    asset_data.get('symbol'),
                    asset_data.get('name'),
                    asset_data.get('sector'),
                    asset_data.get('industry'),
                    asset_data.get('current_price'),
                    asset_data.get('annual_dividend'),
                    asset_data.get('dividend_yield'),
                    asset_data.get('dividend_frequency'),
                    self._format_payment_months(asset_data.get('dividend_payment_months')),
                    asset_data.get('market_cap'),
                    asset_data.get('platforms'),
                    asset_data.get('last_updated')
                ))
                operation = "Insertado"
            
            self.conn.commit()
            
            # Verificar que realmente se guardó
            cursor.execute("SELECT symbol FROM assets WHERE symbol = ?", (symbol,))
            verified = cursor.fetchone() is not None
            
            if verified:
                logger.info(f"✅ {operation} activo: {symbol} (verificado en BD)")
                print(f"✅ {operation} activo: {symbol}")
                return True
            else:
                logger.error(f"❌ Error: No se pudo verificar el guardado de {symbol}")
                print(f"❌ Error: No se pudo verificar el guardado de {symbol}")
                return False
            
        except sqlite3.Error as e:
            error_msg = f"❌ Error en upsert para {asset_data.get('symbol', 'N/A')}: {e}"
            logger.error(error_msg, exc_info=True)
            print(error_msg)
            try:
                self.conn.rollback()
            except:
                pass
            return False
        except Exception as e:
            error_msg = f"❌ Error inesperado en upsert para {asset_data.get('symbol', 'N/A')}: {e}"
            logger.error(error_msg, exc_info=True)
            print(error_msg)
            try:
                self.conn.rollback()
            except:
                pass
            return False
    
    def get_asset(self, symbol: str) -> Optional[Dict]:
        """
        Obtiene un activo por su símbolo.
        
        Args:
            symbol: Símbolo del activo
        
        Returns:
            Diccionario con los datos o None si no existe
        """
        try:
            self._ensure_connection()
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM assets WHERE symbol = ?", (symbol,))
            row = cursor.fetchone()
            
            if row:
                # Convertir Row a diccionario
                asset = dict(row)
                # Parsear meses de pago
                if 'dividend_payment_months' in asset:
                    asset['dividend_payment_months'] = self._parse_payment_months(
                        asset.get('dividend_payment_months', '')
                    )
                return asset
            return None
            
        except sqlite3.Error as e:
            print(f"❌ Error obteniendo activo: {e}")
            return None
    
    def get_all_assets(self, filter_frequency: Optional[str] = None) -> List[Dict]:
        """
        Obtiene todos los activos, opcionalmente filtrados por frecuencia.
        
        Args:
            filter_frequency: Filtrar por 'mensual', 'trimestral', etc.
        
        Returns:
            Lista de diccionarios con los activos
        """
        try:
            self._ensure_connection()
            cursor = self.conn.cursor()
            
            if filter_frequency:
                cursor.execute("""
                    SELECT * FROM assets 
                    WHERE dividend_frequency = ?
                    ORDER BY dividend_yield DESC
                """, (filter_frequency,))
            else:
                cursor.execute("""
                    SELECT * FROM assets 
                    ORDER BY dividend_yield DESC
                """)
            
            rows = cursor.fetchall()
            assets = [dict(row) for row in rows]
            
            # Parsear meses de pago para cada activo
            for asset in assets:
                if 'dividend_payment_months' in asset:
                    asset['dividend_payment_months'] = self._parse_payment_months(
                        asset.get('dividend_payment_months', '')
                    )
            
            return assets
            
        except sqlite3.Error as e:
            print(f"❌ Error obteniendo activos: {e}")
            return []
    
    def get_all_symbols(self) -> List[str]:
        """
        Obtiene todos los símbolos de activos almacenados en la BD.
        
        Returns:
            Lista de símbolos (strings)
        """
        try:
            self._ensure_connection()
            cursor = self.conn.cursor()
            cursor.execute("SELECT symbol FROM assets ORDER BY symbol")
            rows = cursor.fetchall()
            return [row['symbol'] for row in rows]
        except sqlite3.Error as e:
            logger.error(f"❌ Error obteniendo símbolos: {e}")
            return []
    
    def delete_asset(self, symbol: str) -> bool:
        """
        Elimina un activo de la base de datos.
        
        Args:
            symbol: Símbolo del activo a eliminar
        
        Returns:
            True si se eliminó correctamente
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM assets WHERE symbol = ?", (symbol,))
            self.conn.commit()
            return cursor.rowcount > 0
            
        except sqlite3.Error as e:
            print(f"❌ Error eliminando activo: {e}")
            return False
    
    def get_stats(self) -> Dict:
        """
        Obtiene estadísticas agregadas de la base de datos.
        
        Returns:
            Diccionario con estadísticas
        """
        try:
            self._ensure_connection()
            cursor = self.conn.cursor()
            
            # Total de activos
            cursor.execute("SELECT COUNT(*) as total FROM assets")
            total = cursor.fetchone()['total']
            
            # Por frecuencia
            cursor.execute("""
                SELECT dividend_frequency, COUNT(*) as count
                FROM assets
                GROUP BY dividend_frequency
            """)
            frequency_dist = {row['dividend_frequency']: row['count'] 
                            for row in cursor.fetchall()}
            
            # Promedio de yield
            cursor.execute("""
                SELECT AVG(dividend_yield) as avg_yield
                FROM assets
                WHERE dividend_yield > 0
            """)
            avg_yield = cursor.fetchone()['avg_yield'] or 0.0
            
            return {
                'total_assets': total,
                'frequency_distribution': frequency_dist,
                'average_yield': round(avg_yield, 2)
            }
            
        except sqlite3.Error as e:
            print(f"❌ Error obteniendo estadísticas: {e}")
            return {}
    
    def update_platforms(self, symbol: str, platforms: List[str]) -> bool:
        """
        Actualiza las plataformas donde se puede comprar un activo.
        
        Args:
            symbol: Símbolo del activo
            platforms: Lista de plataformas (ej: ['PREX', 'REVOLUT', 'IBKR'])
        
        Returns:
            True si se actualizó correctamente
        """
        try:
            self._ensure_connection()
            cursor = self.conn.cursor()
            
            # Convertir lista a string separado por comas
            platforms_str = ', '.join([p.strip().upper() for p in platforms if p.strip()])
            
            cursor.execute("""
                UPDATE assets 
                SET platforms = ?
                WHERE symbol = ?
            """, (platforms_str, symbol))
            
            self.conn.commit()
            
            if cursor.rowcount > 0:
                logger.info(f"✅ Plataformas actualizadas para {symbol}: {platforms_str}")
                return True
            else:
                logger.warning(f"⚠️ No se encontró el activo {symbol} para actualizar plataformas")
                return False
                
        except sqlite3.Error as e:
            logger.error(f"❌ Error actualizando plataformas para {symbol}: {e}")
            return False
    
    def get_platforms(self, symbol: str) -> List[str]:
        """
        Obtiene las plataformas donde se puede comprar un activo.
        
        Args:
            symbol: Símbolo del activo
        
        Returns:
            Lista de plataformas
        """
        try:
            self._ensure_connection()
            cursor = self.conn.cursor()
            cursor.execute("SELECT platforms FROM assets WHERE symbol = ?", (symbol,))
            row = cursor.fetchone()
            
            if row and row['platforms']:
                # Convertir string separado por comas a lista
                return [p.strip() for p in row['platforms'].split(',') if p.strip()]
            return []
            
        except sqlite3.Error as e:
            logger.error(f"❌ Error obteniendo plataformas para {symbol}: {e}")
            return []
    
    def get_all_platforms(self) -> List[str]:
        """
        Obtiene todas las plataformas únicas en la base de datos.
        
        Returns:
            Lista de plataformas únicas
        """
        try:
            self._ensure_connection()
            cursor = self.conn.cursor()
            cursor.execute("SELECT platforms FROM assets WHERE platforms IS NOT NULL AND platforms != ''")
            rows = cursor.fetchall()
            
            all_platforms = set()
            for row in rows:
                if row['platforms']:
                    platforms = [p.strip() for p in row['platforms'].split(',') if p.strip()]
                    all_platforms.update(platforms)
            
            return sorted(list(all_platforms))
            
        except sqlite3.Error as e:
            logger.error(f"❌ Error obteniendo todas las plataformas: {e}")
            return []
    
    def _format_payment_months(self, months: List[int]) -> str:
        """
        Formatea una lista de meses a string para almacenar en BD.
        
        Args:
            months: Lista de meses (1-12)
        
        Returns:
            String con meses separados por comas (ej: "1,2,3")
        """
        if not months:
            return ""
        return ",".join([str(m) for m in sorted(months)])
    
    def _parse_payment_months(self, months_str: str) -> List[int]:
        """
        Parsea un string de meses a lista.
        
        Args:
            months_str: String con meses separados por comas (ej: "1,2,3" o "1, 2, 3")
        
        Returns:
            Lista de meses (1-12) válidos
        """
        if not months_str or str(months_str) == 'nan' or str(months_str).strip() == '':
            return []
        try:
            # Convertir a string y limpiar
            months_str = str(months_str).strip()
            # Dividir por comas y limpiar cada elemento
            months = []
            for m in months_str.split(','):
                m_clean = m.strip()
                if m_clean.isdigit():
                    month_num = int(m_clean)
                    # Validar que sea un mes válido (1-12)
                    if 1 <= month_num <= 12:
                        months.append(month_num)
            return sorted(list(set(months)))  # Eliminar duplicados y ordenar
        except Exception as e:
            logger.warning(f"Error parseando meses '{months_str}': {e}")
            return []
    
    def get_assets_by_payment_month(self, month: int) -> List[Dict]:
        """
        Obtiene todos los activos que pagan dividendos en un mes específico.
        
        Args:
            month: Mes (1-12)
        
        Returns:
            Lista de activos
        """
        try:
            self._ensure_connection()
            cursor = self.conn.cursor()
            # Obtener todos los activos que tienen meses de pago definidos
            # No usamos LIKE porque puede dar falsos positivos (ej: mes 1 coincide con 10, 11, 12)
            cursor.execute("""
                SELECT * FROM assets 
                WHERE dividend_payment_months IS NOT NULL 
                AND dividend_payment_months != ''
                ORDER BY dividend_yield DESC
            """)
            
            rows = cursor.fetchall()
            assets = [dict(row) for row in rows]
            
            # Parsear meses y filtrar correctamente
            # Esto evita falsos positivos al parsear correctamente la lista de meses
            result = []
            for asset in assets:
                months_str = asset.get('dividend_payment_months', '')
                if not months_str or str(months_str) == 'nan':
                    continue
                
                # Parsear meses correctamente
                months = self._parse_payment_months(months_str)
                
                # Verificar que el mes buscado esté en la lista parseada
                if month in months:
                    asset['dividend_payment_months'] = months  # Guardar meses parseados
                    result.append(asset)
            
            return result
            
        except sqlite3.Error as e:
            logger.error(f"❌ Error obteniendo activos por mes de pago: {e}")
            return []
        except Exception as e:
            logger.error(f"❌ Error inesperado obteniendo activos por mes de pago: {e}")
            return []
    
    def get_assets_by_platform(self, platform: str) -> List[Dict]:
        """
        Obtiene todos los activos disponibles en una plataforma específica.
        
        Args:
            platform: Nombre de la plataforma
        
        Returns:
            Lista de activos
        """
        try:
            self._ensure_connection()
            cursor = self.conn.cursor()
            # Buscar plataformas que contengan el texto (case insensitive)
            cursor.execute("""
                SELECT * FROM assets 
                WHERE platforms IS NOT NULL 
                AND UPPER(platforms) LIKE ?
                ORDER BY dividend_yield DESC
            """, (f'%{platform.upper()}%',))
            
            rows = cursor.fetchall()
            assets = [dict(row) for row in rows]
            
            # Parsear meses de pago para cada activo
            for asset in assets:
                if 'dividend_payment_months' in asset:
                    asset['dividend_payment_months'] = self._parse_payment_months(
                        asset.get('dividend_payment_months', '')
                    )
            
            return assets
            
        except sqlite3.Error as e:
            logger.error(f"❌ Error obteniendo activos por plataforma: {e}")
            return []
    
    def save_portfolio(self, name: str, description: str, selected_symbols: List[str], 
                      shares_data: Dict[str, int], tax_rates_data: Dict[str, float]) -> bool:
        """
        Guarda un portfolio en la base de datos.
        
        Args:
            name: Nombre del portfolio
            description: Descripción opcional
            selected_symbols: Lista de símbolos seleccionados
            shares_data: Diccionario {symbol: cantidad}
            tax_rates_data: Diccionario {symbol: porcentaje_impuesto}
        
        Returns:
            True si se guardó correctamente, False si hubo error
        """
        try:
            self._ensure_connection()
            cursor = self.conn.cursor()
            
            # Convertir datos a JSON strings
            symbols_str = json.dumps(selected_symbols)
            shares_str = json.dumps(shares_data)
            tax_rates_str = json.dumps(tax_rates_data)
            
            # Verificar si ya existe un portfolio con ese nombre
            cursor.execute("SELECT id FROM portfolios WHERE name = ?", (name,))
            existing = cursor.fetchone()
            
            if existing:
                # Actualizar portfolio existente
                cursor.execute("""
                    UPDATE portfolios 
                    SET description = ?,
                        selected_symbols = ?,
                        shares_data = ?,
                        tax_rates_data = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE name = ?
                """, (description, symbols_str, shares_str, tax_rates_str, name))
                logger.info(f"Portfolio '{name}' actualizado")
            else:
                # Insertar nuevo portfolio
                cursor.execute("""
                    INSERT INTO portfolios (name, description, selected_symbols, shares_data, tax_rates_data)
                    VALUES (?, ?, ?, ?, ?)
                """, (name, description, symbols_str, shares_str, tax_rates_str))
                logger.info(f"Portfolio '{name}' guardado")
            
            self.conn.commit()
            return True
            
        except sqlite3.Error as e:
            logger.error(f"❌ Error guardando portfolio: {e}")
            self.conn.rollback()
            return False
        except Exception as e:
            logger.error(f"❌ Error inesperado guardando portfolio: {e}")
            return False
    
    def get_all_portfolios(self) -> List[Dict]:
        """
        Obtiene todos los portfolios guardados.
        
        Returns:
            Lista de portfolios
        """
        try:
            self._ensure_connection()
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT id, name, description, selected_symbols, shares_data, 
                       tax_rates_data, created_at, updated_at
                FROM portfolios
                ORDER BY updated_at DESC
            """)
            
            rows = cursor.fetchall()
            portfolios = []
            
            for row in rows:
                portfolio = dict(row)
                # Parsear JSON strings
                portfolio['selected_symbols'] = json.loads(portfolio['selected_symbols'])
                portfolio['shares_data'] = json.loads(portfolio['shares_data'])
                portfolio['tax_rates_data'] = json.loads(portfolio['tax_rates_data'])
                portfolios.append(portfolio)
            
            return portfolios
            
        except sqlite3.Error as e:
            logger.error(f"❌ Error obteniendo portfolios: {e}")
            return []
        except Exception as e:
            logger.error(f"❌ Error inesperado obteniendo portfolios: {e}")
            return []
    
    def get_portfolio(self, name: str) -> Optional[Dict]:
        """
        Obtiene un portfolio por su nombre.
        
        Args:
            name: Nombre del portfolio
        
        Returns:
            Diccionario con los datos del portfolio o None si no existe
        """
        try:
            self._ensure_connection()
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT id, name, description, selected_symbols, shares_data, 
                       tax_rates_data, created_at, updated_at
                FROM portfolios
                WHERE name = ?
            """, (name,))
            
            row = cursor.fetchone()
            if row:
                portfolio = dict(row)
                portfolio['selected_symbols'] = json.loads(portfolio['selected_symbols'])
                portfolio['shares_data'] = json.loads(portfolio['shares_data'])
                portfolio['tax_rates_data'] = json.loads(portfolio['tax_rates_data'])
                return portfolio
            return None
            
        except sqlite3.Error as e:
            logger.error(f"❌ Error obteniendo portfolio: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Error inesperado obteniendo portfolio: {e}")
            return None
    
    def delete_portfolio(self, name: str) -> bool:
        """
        Elimina un portfolio de la base de datos.
        
        Args:
            name: Nombre del portfolio a eliminar
        
        Returns:
            True si se eliminó correctamente, False si hubo error
        """
        try:
            self._ensure_connection()
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM portfolios WHERE name = ?", (name,))
            self.conn.commit()
            
            if cursor.rowcount > 0:
                logger.info(f"Portfolio '{name}' eliminado")
                return True
            return False
            
        except sqlite3.Error as e:
            logger.error(f"❌ Error eliminando portfolio: {e}")
            self.conn.rollback()
            return False
        except Exception as e:
            logger.error(f"❌ Error inesperado eliminando portfolio: {e}")
            return False
    
    def get_debug_info(self) -> Dict:
        """
        Obtiene información de depuración sobre el estado de la BD.
        
        Returns:
            Diccionario con información de depuración
        """
        try:
            self._ensure_connection()
            cursor = self.conn.cursor()
            
            # Contar total de registros
            cursor.execute("SELECT COUNT(*) as total FROM assets")
            total = cursor.fetchone()['total']
            
            # Obtener algunos ejemplos
            cursor.execute("SELECT symbol, name, dividend_frequency FROM assets LIMIT 5")
            examples = [dict(row) for row in cursor.fetchall()]
            
            return {
                'db_path': self.db_path,
                'connection_active': self.conn is not None,
                'total_records': total,
                'examples': examples
            }
        except Exception as e:
            return {
                'db_path': self.db_path,
                'connection_active': False,
                'error': str(e),
                'total_records': 0,
                'examples': []
            }
    
    def close(self):
        """Cierra la conexión a la base de datos."""
        if self.conn:
            self.conn.close()
            print("✅ Conexión cerrada")


# ============================================================================
# EJEMPLO DE USO (Para testing durante el desarrollo)
# ============================================================================

if __name__ == "__main__":
    """
    Este bloque permite probar el módulo de persistencia.
    """
    db = DatabaseManager("test_dividend_hunter.db")
    
    # Datos de ejemplo
    test_asset = {
        'symbol': 'O',
        'name': 'Realty Income Corporation',
        'sector': 'Real Estate',
        'industry': 'REIT - Retail',
        'current_price': 60.50,
        'annual_dividend': 3.00,
        'dividend_yield': 4.96,
        'dividend_frequency': 'mensual',
        'market_cap': 40000000000,
        'last_updated': datetime.now().isoformat()
    }
    
    print("=" * 70)
    print("PRUEBA DEL MÓDULO 2: Persistencia de Datos")
    print("=" * 70)
    
    # Test Upsert (Insert)
    print("\n1. Insertando activo...")
    db.upsert_asset(test_asset)
    
    # Test Get
    print("\n2. Obteniendo activo...")
    retrieved = db.get_asset('O')
    if retrieved:
        print(f"   ✅ Encontrado: {retrieved['name']}")
        print(f"   Yield: {retrieved['dividend_yield']}%")
    
    # Test Upsert (Update)
    print("\n3. Actualizando precio...")
    test_asset['current_price'] = 61.00
    test_asset['last_updated'] = datetime.now().isoformat()
    db.upsert_asset(test_asset)
    
    # Test Get All
    print("\n4. Obteniendo todos los activos...")
    all_assets = db.get_all_assets()
    print(f"   Total: {len(all_assets)} activos")
    
    # Test Stats
    print("\n5. Estadísticas:")
    stats = db.get_stats()
    print(f"   Total activos: {stats.get('total_assets', 0)}")
    print(f"   Yield promedio: {stats.get('average_yield', 0)}%")
    
    db.close()
    
    print("\n" + "=" * 70)
    print("✅ Módulo 2 funcionando correctamente")
    print("=" * 70)

