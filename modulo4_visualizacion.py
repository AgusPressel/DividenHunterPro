"""
================================================================================
MÓDULO 4: VISUALIZACIÓN FINANCIERA (Data Viz)
================================================================================

CONCEPTO TEÓRICO:
-----------------
En finanzas, la visualización de datos es crucial para tomar decisiones.
Un buen gráfico puede revelar patrones que los números por sí solos ocultan.

EL SCATTER PLOT: "LA BÚSQUEDA DEL TESORO"
------------------------------------------
Este gráfico es una herramienta poderosa para encontrar "gemas" de inversión:

Eje X (Precio): Costo de entrada
Eje Y (Yield): Retorno esperado
Color (Frecuencia): Patrón de pago

INTERPRETACIÓN:
- Esquina superior izquierda = GEMAS 💎
  (Bajo precio, Alto yield, Ideal para inversores)
- Esquina inferior derecha = EVITAR
  (Alto precio, Bajo yield, No eficiente)

POR QUÉ ESTE GRÁFICO ES PODEROSO:
1. Permite comparar múltiples activos de un vistazo
2. Identifica outliers (gemas y trampas)
3. Facilita la toma de decisiones visual
4. Combina 3 dimensiones (X, Y, Color) en 2D

Plotly es ideal porque:
- Interactivo (hover, zoom, pan)
- Integración nativa con Streamlit
- Exportable a imágenes
"""

import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from typing import List, Dict, Optional
import sys
import os

# Importar módulos anteriores
sys.path.append(os.path.dirname(__file__))
from modulo2_persistencia_datos import DatabaseManager


class FinancialVisualizer:
    """
    Clase que encapsula toda la lógica de visualización financiera.
    
    PRINCIPIO DE DISEÑO: Visualización como servicio
    - Esta clase solo se encarga de crear gráficos
    - No maneja datos ni UI (solo recibe datos y devuelve figuras)
    """
    
    def __init__(self, db_path: str = "dividend_hunter.db"):
        """
        Inicializa el visualizador.
        
        Args:
            db_path: Ruta a la base de datos (debe ser la misma que usa app.py)
        """
        self.db = DatabaseManager(db_path)
    
    def _asset_has_platform(self, asset: Dict, platform: str) -> bool:
        """
        Verifica si un activo tiene una plataforma específica.
        
        Args:
            asset: Diccionario con datos del activo
            platform: Nombre de la plataforma
        
        Returns:
            True si el activo tiene la plataforma
        """
        platforms = asset.get('platforms', '')
        if not platforms or str(platforms) == 'nan':
            return False
        platforms_list = [p.strip().upper() for p in str(platforms).split(',') if p.strip()]
        return platform.upper() in platforms_list
    
    def _asset_has_payment_month(self, asset: Dict, month: int) -> bool:
        """
        Verifica si un activo paga dividendos en un mes específico.
        
        Args:
            asset: Diccionario con datos del activo
            month: Mes (1-12)
        
        Returns:
            True si el activo paga en ese mes
        """
        months_data = asset.get('dividend_payment_months', '')
        if not months_data or str(months_data) == 'nan' or str(months_data).strip() == '':
            return False
        
        # Si ya es una lista parseada, verificar directamente
        if isinstance(months_data, list):
            return month in months_data
        
        # Si es string, parsear correctamente usando el método de la BD
        # Usar el mismo método de parseo que la BD para consistencia
        months_str = str(months_data).strip()
        try:
            months = []
            for m in months_str.split(','):
                m_clean = m.strip()
                if m_clean.isdigit():
                    month_num = int(m_clean)
                    # Validar que sea un mes válido (1-12)
                    if 1 <= month_num <= 12:
                        months.append(month_num)
            return month in months
        except Exception:
            return False
    
    def _format_tooltip_text(self, row: pd.Series, config: Dict) -> str:
        """
        Formatea el texto del tooltip incluyendo información de plataformas.
        
        Args:
            row: Fila del DataFrame con datos del activo
            config: Configuración de frecuencia
        
        Returns:
            Texto formateado para el tooltip
        """
        text = f"<b>{row['symbol']}</b><br>{row['name']}<br>"
        text += f"Precio: ${row['current_price']:.2f}<br>"
        text += f"Yield: {row['dividend_yield']:.2f}%<br>"
        text += f"Frecuencia: {config['description']}"
        
        # Agregar plataformas si existen
        if 'platforms' in row and row['platforms'] and str(row['platforms']) != 'nan':
            platforms = [p.strip() for p in str(row['platforms']).split(',') if p.strip()]
            if platforms:
                text += f"<br>🏪 Plataformas: {', '.join(platforms)}"
        
        # Agregar meses de pago si existen
        if 'dividend_payment_months' in row and row['dividend_payment_months'] and str(row['dividend_payment_months']) != 'nan':
            months_data = row['dividend_payment_months']
            months = []
            
            # Parsear meses correctamente según el tipo de dato
            if isinstance(months_data, list):
                # Si ya es una lista, usar directamente (validar que sean enteros)
                months = [m for m in months_data if isinstance(m, int) and 1 <= m <= 12]
            elif isinstance(months_data, str):
                # Si es string, parsear usando el mismo método que la BD
                months_str = str(months_data).strip()
                if months_str:
                    for m in months_str.split(','):
                        m_clean = m.strip()
                        if m_clean.isdigit():
                            month_num = int(m_clean)
                            if 1 <= month_num <= 12:
                                months.append(month_num)
            else:
                # Intentar convertir a string y parsear
                months_str = str(months_data).strip()
                if months_str:
                    for m in months_str.split(','):
                        m_clean = m.strip()
                        if m_clean.isdigit():
                            month_num = int(m_clean)
                            if 1 <= month_num <= 12:
                                months.append(month_num)
            
            # Mostrar meses en el tooltip
            if months:
                month_names = {1: 'Ene', 2: 'Feb', 3: 'Mar', 4: 'Abr', 5: 'May', 6: 'Jun',
                             7: 'Jul', 8: 'Ago', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dic'}
                month_labels = [month_names.get(m, str(m)) for m in sorted(months)]
                text += f"<br>📅 Paga en: {', '.join(month_labels)}"
        
        return text
    
    def create_treasure_hunt_scatter(self, 
                                    filter_frequency: Optional[str] = None,
                                    min_yield: float = 0.0,
                                    filter_platform: Optional[str] = None,
                                    filter_payment_month: Optional[int] = None) -> go.Figure:
        """
        FUNCIÓN CLAVE: Crea el "Scatter Plot: La Búsqueda del Tesoro".
        
        Este es el gráfico más importante del módulo. Visualiza la relación
        entre Precio, Yield y Frecuencia para identificar oportunidades.
        
        Args:
            filter_frequency: Filtrar por frecuencia (opcional)
            min_yield: Yield mínimo a mostrar (filtro)
        
        Returns:
            Figura de Plotly lista para mostrar
        """
        # Obtener datos con estrategia de filtrado combinado
        # IMPORTANTE: Aplicar todos los filtros en el orden correcto para evitar resultados incorrectos
        
        # Paso 1: Obtener conjunto base de activos
        if filter_platform:
            assets = self.db.get_assets_by_platform(filter_platform)
        else:
            assets = self.db.get_all_assets()
        
        # Paso 2: Aplicar filtro de frecuencia (si existe)
        if filter_frequency:
            assets = [a for a in assets if a.get('dividend_frequency') == filter_frequency]
        
        # Paso 3: Aplicar filtro de mes de pago (si existe) - DEBE ser el último para asegurar precisión
        if filter_payment_month:
            # Filtrar activos que realmente pagan en el mes seleccionado
            # VALIDACIÓN CRÍTICA: Solo incluir activos cuyo mes de pago esté en la lista de meses que paga
            filtered_assets = []
            for asset in assets:
                months_data = asset.get('dividend_payment_months', '')
                
                # Si no hay datos de meses, excluir el activo
                if not months_data or str(months_data) == 'nan' or str(months_data).strip() == '':
                    continue
                
                # Parsear meses - Asegurar que siempre sea una lista de enteros
                months = []
                if isinstance(months_data, str):
                    # Si es string, parsear usando el método de la BD
                    months = self.db._parse_payment_months(months_data)
                elif isinstance(months_data, list):
                    # Si ya es lista, validar y normalizar
                    months = []
                    for m in months_data:
                        if isinstance(m, int) and 1 <= m <= 12:
                            months.append(m)
                        elif isinstance(m, str) and m.strip().isdigit():
                            m_int = int(m.strip())
                            if 1 <= m_int <= 12:
                                months.append(m_int)
                else:
                    # Tipo no reconocido, intentar convertir a string y parsear
                    months = self.db._parse_payment_months(str(months_data))
                
                # Actualizar el asset con los meses parseados
                asset['dividend_payment_months'] = months
                
                # VALIDACIÓN CRÍTICA: Verificar que el mes filtrado esté en la lista de meses que paga
                # Solo incluir si el mes está presente en la lista
                if months and filter_payment_month in months:
                    filtered_assets.append(asset)
            
            assets = filtered_assets
        
        if not assets:
            # Crear figura vacía con mensaje
            fig = go.Figure()
            fig.add_annotation(
                text="No hay datos para visualizar",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False
            )
            return fig
        
        # Convertir a DataFrame
        df = pd.DataFrame(assets)
        
        # Filtrar por yield mínimo
        df = df[df['dividend_yield'] >= min_yield]
        
        if df.empty:
            fig = go.Figure()
            fig.add_annotation(
                text="No hay activos que cumplan los filtros",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False
            )
            return fig
        
        # Mapeo de frecuencia a colores y símbolos con descripciones claras
        frequency_config = {
            'mensual': {
                'color': '#2ecc71', 
                'name': '📅 Pago Mensual (10-12 pagos/año)', 
                'symbol': 'circle',
                'description': 'Ideal para flujo de caja constante'
            },
            'trimestral': {
                'color': '#3498db', 
                'name': '📆 Pago Trimestral (3-4 pagos/año)', 
                'symbol': 'square',
                'description': 'Más común en acciones tradicionales'
            },
            'irregular': {
                'color': '#f39c12', 
                'name': '⚠️ Pago Irregular (1-2 pagos/año)', 
                'symbol': 'diamond',
                'description': 'Pagos esporádicos o especiales'
            },
            'sin_dividendos': {
                'color': '#e74c3c', 
                'name': '❌ Sin Dividendos', 
                'symbol': 'x',
                'description': 'No paga dividendos actualmente'
            }
        }
        
        # Crear figura
        fig = go.Figure()
        
        # Agrupar por frecuencia y crear trazos separados
        for freq in df['dividend_frequency'].unique():
            freq_data = df[df['dividend_frequency'] == freq]
            config = frequency_config.get(freq, {
                'color': '#95a5a6',
                'name': freq.capitalize(),
                'symbol': 'circle'
            })
            
            fig.add_trace(go.Scatter(
                x=freq_data['current_price'],
                y=freq_data['dividend_yield'],
                mode='markers',
                name=config['name'],
                marker=dict(
                    size=14,
                    color=config['color'],
                    symbol=config['symbol'],
                    line=dict(width=2, color='white'),
                    opacity=0.85
                ),
                text=[self._format_tooltip_text(row, config) for _, row in freq_data.iterrows()],
                hovertemplate='%{text}<extra></extra>',
                customdata=freq_data['symbol'].values,
                legendgroup=config['name']
            ))
        
        # Personalizar layout
        fig.update_layout(
            title={
                'text': '💰 La Búsqueda del Tesoro: Precio vs. Yield',
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 22, 'color': '#2c3e50', 'family': 'Arial, sans-serif'}
            },
            xaxis_title={
                'text': 'Precio Actual (USD) ← Más caro',
                'font': {'size': 14, 'color': '#34495e'}
            },
            yaxis_title={
                'text': 'Dividend Yield (%) ← Mayor retorno',
                'font': {'size': 14, 'color': '#34495e'}
            },
            hovermode='closest',
            plot_bgcolor='white',
            paper_bgcolor='#f8f9fa',
            legend=dict(
                title=dict(
                    text='<b>Frecuencia de Pago de Dividendos</b>',
                    font=dict(size=13, color='#2c3e50')
                ),
                orientation="v",
                yanchor="top",
                y=0.98,
                xanchor="left",
                x=1.02,
                bgcolor='rgba(255, 255, 255, 0.8)',
                bordercolor='#bdc3c7',
                borderwidth=1,
                font=dict(size=11),
                itemclick="toggleothers",
                itemdoubleclick="toggle"
            ),
            height=650,
            margin=dict(l=80, r=180, t=80, b=80)
        )
        
        # Agregar anotaciones explicativas mejoradas
        fig.add_annotation(
            text="<b>💎 ZONA DE GEMAS</b><br>Bajo precio + Alto yield<br>Ideal para inversión",
            xref="paper", yref="paper",
            x=0.02, y=0.98,
            showarrow=False,
            bgcolor="rgba(46, 204, 113, 0.25)",
            bordercolor="rgba(46, 204, 113, 0.8)",
            borderwidth=2,
            borderpad=8,
            font=dict(size=12, color='#1e8449', family='Arial, sans-serif'),
            align="left"
        )
        
        fig.add_annotation(
            text="<b>⚠️ ZONA A EVITAR</b><br>Alto precio + Bajo yield<br>No eficiente",
            xref="paper", yref="paper",
            x=0.98, y=0.02,
            showarrow=False,
            bgcolor="rgba(231, 76, 60, 0.25)",
            bordercolor="rgba(231, 76, 60, 0.8)",
            borderwidth=2,
            borderpad=8,
            font=dict(size=12, color='#c0392b', family='Arial, sans-serif'),
            align="right"
        )
        
        # Agregar guía de interpretación en la parte inferior
        fig.add_annotation(
            text="<b>📊 Cómo leer este gráfico:</b><br>" +
                 "• <b>Eje X (Precio):</b> Costo de entrada - Mientras más a la derecha, más caro<br>" +
                 "• <b>Eje Y (Yield):</b> Retorno esperado - Mientras más arriba, mayor retorno<br>" +
                 "• <b>Color/Forma:</b> Frecuencia de pago (ver leyenda a la derecha)<br>" +
                 "• <b>Mejor inversión:</b> Puntos en la esquina superior izquierda",
            xref="paper", yref="paper",
            x=0.5, y=-0.12,
            showarrow=False,
            bgcolor="rgba(236, 240, 241, 0.9)",
            bordercolor="#95a5a6",
            borderwidth=1,
            borderpad=10,
            font=dict(size=10, color='#2c3e50', family='Arial, sans-serif'),
            align="left",
            xanchor="center"
        )
        
        return fig
    
    def create_yield_distribution(self, 
                                 filter_frequency: Optional[str] = None,
                                 filter_platform: Optional[str] = None,
                                 filter_payment_month: Optional[int] = None) -> go.Figure:
        """
        Crea un histograma de distribución de yields.
        
        Útil para entender la distribución de retornos en el portfolio.
        
        Args:
            filter_frequency: Filtrar por frecuencia (opcional)
            filter_platform: Filtrar por plataforma (opcional)
        
        Returns:
            Figura de Plotly
        """
        # Obtener datos con estrategia de filtrado combinado
        # Paso 1: Obtener conjunto base de activos
        if filter_platform:
            assets = self.db.get_assets_by_platform(filter_platform)
        else:
            assets = self.db.get_all_assets()
        
        # Paso 2: Aplicar filtro de frecuencia (si existe)
        if filter_frequency:
            assets = [a for a in assets if a.get('dividend_frequency') == filter_frequency]
        
        # Paso 3: Aplicar filtro de mes de pago (si existe) - DEBE ser el último para asegurar precisión
        if filter_payment_month:
            # VALIDACIÓN CRÍTICA: Solo incluir activos cuyo mes de pago esté en la lista de meses que paga
            filtered_assets = []
            for asset in assets:
                months_data = asset.get('dividend_payment_months', '')
                
                # Si no hay datos de meses, excluir el activo
                if not months_data or str(months_data) == 'nan' or str(months_data).strip() == '':
                    continue
                
                # Parsear meses - Asegurar que siempre sea una lista de enteros
                months = []
                if isinstance(months_data, str):
                    months = self.db._parse_payment_months(months_data)
                elif isinstance(months_data, list):
                    for m in months_data:
                        if isinstance(m, int) and 1 <= m <= 12:
                            months.append(m)
                        elif isinstance(m, str) and m.strip().isdigit():
                            m_int = int(m.strip())
                            if 1 <= m_int <= 12:
                                months.append(m_int)
                else:
                    months = self.db._parse_payment_months(str(months_data))
                
                asset['dividend_payment_months'] = months
                
                # VALIDACIÓN: Verificar que el mes filtrado esté en la lista de meses que paga
                if months and filter_payment_month in months:
                    filtered_assets.append(asset)
            
            assets = filtered_assets
        
        if not assets:
            fig = go.Figure()
            fig.add_annotation(
                text="No hay datos para visualizar",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False
            )
            return fig
        
        df = pd.DataFrame(assets)
        df = df[df['dividend_yield'] > 0]  # Solo activos con dividendos
        
        if df.empty:
            fig = go.Figure()
            fig.add_annotation(
                text="No hay activos con dividendos",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False
            )
            return fig
        
        fig = px.histogram(
            df,
            x='dividend_yield',
            nbins=20,
            title='Distribución de Dividend Yields',
            labels={'dividend_yield': 'Dividend Yield (%)', 'count': 'Cantidad de Activos'},
            color_discrete_sequence=['#3498db']
        )
        
        fig.update_layout(
            plot_bgcolor='white',
            paper_bgcolor='#f8f9fa',
            height=400
        )
        
        return fig
    
    def create_top_performers(self, top_n: int = 10) -> go.Figure:
        """
        Crea un gráfico de barras con los top N activos por yield.
        
        Args:
            top_n: Número de activos a mostrar
        
        Returns:
            Figura de Plotly
        """
        assets = self.db.get_all_assets()
        
        if not assets:
            fig = go.Figure()
            fig.add_annotation(
                text="No hay datos para visualizar",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False
            )
            return fig
        
        df = pd.DataFrame(assets)
        df = df[df['dividend_yield'] > 0].nlargest(top_n, 'dividend_yield')
        
        if df.empty:
            fig = go.Figure()
            fig.add_annotation(
                text="No hay activos con dividendos",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False
            )
            return fig
        
        # Mapear frecuencia a colores
        frequency_colors = {
            'mensual': '#2ecc71',
            'trimestral': '#3498db',
            'irregular': '#f39c12',
            'sin_dividendos': '#e74c3c'
        }
        
        df['color'] = df['dividend_frequency'].map(frequency_colors).fillna('#95a5a6')
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=df['symbol'],
            y=df['dividend_yield'],
            marker_color=df['color'],
            text=[f"{y:.2f}%" for y in df['dividend_yield']],
            textposition='outside',
            hovertemplate='<b>%{x}</b><br>Yield: %{y:.2f}%<extra></extra>'
        ))
        
        fig.update_layout(
            title=f'Top {top_n} Activos por Dividend Yield',
            xaxis_title='Símbolo',
            yaxis_title='Dividend Yield (%)',
            plot_bgcolor='white',
            paper_bgcolor='#f8f9fa',
            height=500
        )
        
        return fig
    
    def create_frequency_comparison(self, 
                                   filter_platform: Optional[str] = None,
                                   filter_payment_month: Optional[int] = None) -> go.Figure:
        """
        Crea un gráfico comparativo de métricas por frecuencia.
        
        Args:
            filter_platform: Filtrar por plataforma (opcional)
        
        Returns:
            Figura de Plotly
        """
        # Obtener datos con estrategia de filtrado combinado
        # Paso 1: Obtener conjunto base de activos
        if filter_platform:
            assets = self.db.get_assets_by_platform(filter_platform)
        else:
            assets = self.db.get_all_assets()
        
        # Paso 2: Aplicar filtro de mes de pago (si existe) - DEBE ser el último para asegurar precisión
        if filter_payment_month:
            # VALIDACIÓN CRÍTICA: Solo incluir activos cuyo mes de pago esté en la lista de meses que paga
            filtered_assets = []
            for asset in assets:
                months_data = asset.get('dividend_payment_months', '')
                
                # Si no hay datos de meses, excluir el activo
                if not months_data or str(months_data) == 'nan' or str(months_data).strip() == '':
                    continue
                
                # Parsear meses - Asegurar que siempre sea una lista de enteros
                months = []
                if isinstance(months_data, str):
                    months = self.db._parse_payment_months(months_data)
                elif isinstance(months_data, list):
                    for m in months_data:
                        if isinstance(m, int) and 1 <= m <= 12:
                            months.append(m)
                        elif isinstance(m, str) and m.strip().isdigit():
                            m_int = int(m.strip())
                            if 1 <= m_int <= 12:
                                months.append(m_int)
                else:
                    months = self.db._parse_payment_months(str(months_data))
                
                asset['dividend_payment_months'] = months
                
                # VALIDACIÓN: Verificar que el mes filtrado esté en la lista de meses que paga
                if months and filter_payment_month in months:
                    filtered_assets.append(asset)
            
            assets = filtered_assets
        
        if not assets:
            fig = go.Figure()
            fig.add_annotation(
                text="No hay datos para visualizar",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False
            )
            return fig
        
        df = pd.DataFrame(assets)
        
        # Agrupar por frecuencia y calcular promedios
        summary = df.groupby('dividend_frequency').agg({
            'dividend_yield': 'mean',
            'current_price': 'mean',
            'symbol': 'count'
        }).reset_index()
        
        summary.columns = ['frequency', 'avg_yield', 'avg_price', 'count']
        
        # Crear subplots
        fig = make_subplots(
            rows=1, cols=2,
            subplot_titles=('Yield Promedio por Frecuencia', 'Precio Promedio por Frecuencia'),
            specs=[[{"type": "bar"}, {"type": "bar"}]]
        )
        
        # Yield promedio
        fig.add_trace(
            go.Bar(
                x=summary['frequency'],
                y=summary['avg_yield'],
                name='Yield Promedio',
                marker_color='#3498db',
                text=[f"{y:.2f}%" for y in summary['avg_yield']],
                textposition='outside'
            ),
            row=1, col=1
        )
        
        # Precio promedio
        fig.add_trace(
            go.Bar(
                x=summary['frequency'],
                y=summary['avg_price'],
                name='Precio Promedio',
                marker_color='#2ecc71',
                text=[f"${p:.2f}" for p in summary['avg_price']],
                textposition='outside'
            ),
            row=1, col=2
        )
        
        fig.update_xaxes(title_text="Frecuencia", row=1, col=1)
        fig.update_xaxes(title_text="Frecuencia", row=1, col=2)
        fig.update_yaxes(title_text="Yield (%)", row=1, col=1)
        fig.update_yaxes(title_text="Precio (USD)", row=1, col=2)
        
        fig.update_layout(
            title_text="Comparación por Frecuencia de Dividendos",
            height=500,
            showlegend=False,
            plot_bgcolor='white',
            paper_bgcolor='#f8f9fa'
        )
        
        return fig
    
    def create_platform_distribution(self) -> go.Figure:
        """
        Crea un gráfico mostrando la distribución de activos por plataforma.
        
        Returns:
            Figura de Plotly
        """
        assets = self.db.get_all_assets()
        
        if not assets:
            fig = go.Figure()
            fig.add_annotation(
                text="No hay datos para visualizar",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False
            )
            return fig
        
        # Contar activos por plataforma
        platform_counts = {}
        for asset in assets:
            if asset.get('platforms') and str(asset['platforms']) != 'nan':
                platforms = [p.strip() for p in str(asset['platforms']).split(',') if p.strip()]
                for platform in platforms:
                    platform_counts[platform] = platform_counts.get(platform, 0) + 1
        
        if not platform_counts:
            fig = go.Figure()
            fig.add_annotation(
                text="No hay activos con plataformas asociadas",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False
            )
            return fig
        
        # Crear DataFrame para el gráfico
        platform_df = pd.DataFrame(
            list(platform_counts.items()),
            columns=['Plataforma', 'Cantidad']
        ).sort_values('Cantidad', ascending=False)
        
        # Crear gráfico de barras
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=platform_df['Plataforma'],
            y=platform_df['Cantidad'],
            marker_color='#3498db',
            text=[f"{int(y)}" for y in platform_df['Cantidad']],
            textposition='outside',
            hovertemplate='<b>%{x}</b><br>Activos: %{y}<extra></extra>'
        ))
        
        fig.update_layout(
            title={
                'text': 'Distribución de Activos por Plataforma',
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 20, 'color': '#2c3e50'}
            },
            xaxis_title='Plataforma',
            yaxis_title='Cantidad de Activos',
            plot_bgcolor='white',
            paper_bgcolor='#f8f9fa',
            height=500,
            xaxis=dict(tickangle=-45)
        )
        
        return fig


# ============================================================================
# EJEMPLO DE USO (Para testing durante el desarrollo)
# ============================================================================

if __name__ == "__main__":
    """
    Para probar las visualizaciones, puedes ejecutar este módulo
    y luego abrir los gráficos en un navegador.
    """
    visualizer = FinancialVisualizer()
    
    print("=" * 70)
    print("PRUEBA DEL MÓDULO 4: Visualización Financiera")
    print("=" * 70)
    
    # Crear el gráfico principal
    print("\n1. Creando 'La Búsqueda del Tesoro'...")
    fig = visualizer.create_treasure_hunt_scatter()
    
    # Guardar como HTML para visualización
    fig.write_html("treasure_hunt.html")
    print("   ✅ Gráfico guardado en 'treasure_hunt.html'")
    print("   👉 Abre el archivo en tu navegador para verlo")
    
    # Crear otros gráficos
    print("\n2. Creando distribución de yields...")
    fig2 = visualizer.create_yield_distribution()
    fig2.write_html("yield_distribution.html")
    print("   ✅ Gráfico guardado en 'yield_distribution.html'")
    
    print("\n3. Creando top performers...")
    fig3 = visualizer.create_top_performers()
    fig3.write_html("top_performers.html")
    print("   ✅ Gráfico guardado en 'top_performers.html'")
    
    print("\n" + "=" * 70)
    print("✅ Módulo 4 funcionando correctamente")
    print("=" * 70)
    print("\n💡 Tip: Abre los archivos HTML en tu navegador para ver los gráficos interactivos")

