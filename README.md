# 💰 Dividend Hunter Pro

**Aplicación de análisis de dividendos para inversores en fintech**

---

## 📚 Descripción del Proyecto

**Dividend Hunter Pro** es una aplicación completa desarrollada en Python que permite:

- 🔍 **Buscar activos** y analizar automáticamente sus dividendos
- 📊 **Detectar frecuencia de pago** (Mensual vs Trimestral) analizando historial de 12 meses
- 📥 **Importar listas de tickers** desde archivos Excel
- 💾 **Persistir datos** en base de datos SQLite
- 📈 **Visualizar métricas financieras** con gráficos interactivos
- 💎 **Encontrar "gemas"** de inversión (alto yield, bajo costo)

---

## 🎯 Estructura del Curso (5 Módulos)

Este proyecto está diseñado como un **curso guiado (Code-along)** para estudiantes intermedios de Python y Data Science en Fintech.

### **Módulo 1: Ingeniería de Datos Financieros**
- Conexión con `yfinance` para obtener datos de mercado
- **Desafío clave**: Lógica para determinar frecuencia de dividendos (Mensual vs Trimestral)
- Análisis de historial de 12 meses
- Cálculo de dividend yield

**Archivo**: `modulo1_ingenieria_datos.py`

### **Módulo 2: Persistencia de Datos**
- Diseño de base de datos SQLite optimizada
- Implementación de patrón **Upsert** (Insertar o Actualizar)
- Clase `DatabaseManager` para abstracción de BD
- Índices para búsquedas rápidas

**Archivo**: `modulo2_persistencia_datos.py`

### **Módulo 3: Interfaz de Usuario con Streamlit**
- Configuración de aplicación Streamlit
- Sidebar y navegación
- **Importador de Excel** usando `openpyxl`
- Procesamiento batch de tickers

**Archivo**: `modulo3_interfaz_usuario.py`

### **Módulo 4: Visualización Financiera**
- **"La Búsqueda del Tesoro"**: Scatter plot interactivo
  - Eje X: Precio
  - Eje Y: Yield
  - Color: Frecuencia
- Gráficos de distribución y comparación
- Visualizaciones con Plotly

**Archivo**: `modulo4_visualizacion.py`

### **Módulo 5: Refactorización y Producción**
- Manejo robusto de errores (Try/Except)
- Validación de datos
- Configuración centralizada
- Logging y monitoreo
- Código modular y mantenible

**Archivo**: `modulo5_refactorizacion.py`

### **Aplicación Final**
- `app.py`: Unificación de todos los módulos
- Aplicación completa lista para producción

---

## 🚀 Instalación

### Prerrequisitos

- Python 3.10 o superior (Python 3.14 recomendado)
- pip (gestor de paquetes de Python)

### Pasos de Instalación

1. **Clonar o descargar el proyecto**

```bash
cd v1
```

2. **Crear entorno virtual (recomendado)**

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

3. **Instalar dependencias**

```bash
pip install -r requirements.txt
```

---

## 📖 Uso

### Ejecutar la Aplicación Completa

```bash
streamlit run app.py
```

La aplicación se abrirá automáticamente en tu navegador en `http://localhost:8501`

### Ejecutar Módulos Individuales (Para Aprendizaje)

Cada módulo puede ejecutarse independientemente para pruebas:

```bash
# Módulo 1: Ingeniería de Datos
python modulo1_ingenieria_datos.py

# Módulo 2: Persistencia
python modulo2_persistencia_datos.py

# Módulo 3: Interfaz (requiere Streamlit)
streamlit run modulo3_interfaz_usuario.py

# Módulo 4: Visualización
python modulo4_visualizacion.py

# Módulo 5: Refactorización
python modulo5_refactorizacion.py
```

---

## 📁 Estructura del Proyecto

```
v1/
├── app.py                          # Aplicación principal (unifica todos los módulos)
├── modulo1_ingenieria_datos.py     # Backend: yfinance y análisis de dividendos
├── modulo2_persistencia_datos.py   # Base de datos SQLite
├── modulo3_interfaz_usuario.py     # Frontend: Streamlit
├── modulo4_visualizacion.py        # Visualizaciones: Plotly
├── modulo5_refactorizacion.py      # Utilidades y producción
├── requirements.txt                # Dependencias
├── README.md                      # Este archivo
├── dividend_hunter.db             # Base de datos (se crea automáticamente)
└── dividend_hunter.log            # Logs (se crea automáticamente)
```

---

## 🎓 Conceptos Clave Aprendidos

### 1. **Análisis de Datos Financieros**
- Uso de `yfinance` para obtener datos de mercado
- Análisis de series temporales de dividendos
- Cálculo de métricas financieras (yield, frecuencia)

### 2. **Persistencia de Datos**
- Diseño de esquema de base de datos
- Patrón Upsert para actualizaciones eficientes
- Uso de SQLite para aplicaciones ligeras

### 3. **Interfaz de Usuario**
- Desarrollo rápido con Streamlit
- Procesamiento de archivos Excel
- Procesamiento batch de datos

### 4. **Visualización de Datos**
- Gráficos interactivos con Plotly
- Visualización multidimensional (X, Y, Color)
- Interpretación de gráficos financieros

### 5. **Buenas Prácticas**
- Manejo robusto de errores
- Validación de datos
- Logging y monitoreo
- Código modular y mantenible

---

## 🔑 Funcionalidades Principales

### 1. Búsqueda de Activos
- Ingresa un símbolo de ticker (ej: AAPL, MSFT, O)
- La aplicación analiza automáticamente:
  - Precio actual
  - Dividend yield
  - Frecuencia de pago (Mensual/Trimestral/Irregular)
  - Información de la empresa

### 2. Importación desde Excel
- Sube un archivo Excel con tickers en la primera columna
- La aplicación procesa cada ticker automáticamente
- Guarda los resultados en la base de datos

### 3. Visualización "La Búsqueda del Tesoro"
- Scatter plot interactivo
- Identifica "gemas" (bajo precio, alto yield)
- Filtra por frecuencia de pago

### 4. Análisis de Portfolio
- Ver todos los activos guardados
- Filtrar por frecuencia o yield mínimo
- Estadísticas agregadas

---

## 🛠️ Stack Tecnológico

- **Python 3.14** (o versión estable reciente)
- **yfinance**: Obtención de datos financieros
- **pandas**: Manipulación y análisis de datos
- **sqlite3**: Base de datos local
- **Streamlit**: Interfaz de usuario web
- **Plotly**: Visualizaciones interactivas
- **openpyxl**: Procesamiento de archivos Excel

---

## 📝 Notas Importantes

### Limitaciones
- Los datos dependen de `yfinance`, que obtiene información de Yahoo Finance
- La frecuencia de dividendos se infiere del historial (no es 100% garantizado)
- SQLite es ideal para desarrollo, pero para producción considera PostgreSQL/MySQL

### Mejoras Futuras
- Integración con más fuentes de datos
- Análisis histórico más profundo
- Alertas y notificaciones
- Exportación a PDF/Excel
- Autenticación de usuarios
- Dashboard en tiempo real

---

## 🐛 Solución de Problemas

### Error: "No module named 'yfinance'"
```bash
pip install yfinance
```

### Error: "No se pueden obtener datos"
- Verifica tu conexión a internet
- Algunos tickers pueden no estar disponibles en Yahoo Finance
- Intenta con otro símbolo

### Error: "Base de datos bloqueada"
- Cierra otras instancias de la aplicación
- Elimina el archivo `dividend_hunter.db` y vuelve a ejecutar

---

## 📄 Licencia

Este proyecto es educativo y está diseñado para fines de aprendizaje.

---

## 👨‍🏫 Para Instructores

Este proyecto está estructurado como un curso guiado:

1. **Segmentación (Chunking)**: 5 módulos digeribles
2. **Foco en lógica de negocio**: Énfasis en la detección de frecuencia de dividendos
3. **Gamificación**: "La Búsqueda del Tesoro" hace la visualización más atractiva
4. **Doble entrega**: Explicación paso a paso + código final ensamblado

Cada módulo puede enseñarse en sesiones separadas, permitiendo a los estudiantes:
- Entender conceptos teóricos
- Ver código comentado
- Practicar con ejemplos
- Integrar todo al final

---

## 🤝 Contribuciones

Este es un proyecto educativo. Siéntete libre de:
- Modificar el código para tus necesidades
- Agregar nuevas funcionalidades
- Mejorar la documentación
- Compartir con otros estudiantes

---

## 📧 Contacto

Para preguntas o sugerencias sobre este proyecto educativo, por favor abre un issue o contacta al instructor.

---

**¡Feliz caza de dividendos! 💰📈**

