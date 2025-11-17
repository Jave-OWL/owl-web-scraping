# 🧠 ScrapingFichas – Extracción automatizada de fichas técnicas de fondos de inversión

Este proyecto implementa un sistema inteligente de **web scraping semántico** que permite localizar, filtrar y descargar automáticamente las **fichas técnicas de Fondos de Inversión Colectiva (FIC)** publicadas por diferentes entidades financieras en Colombia (Bancolombia, BBVA, Davivienda, Itaú, Fidubogotá, entre otras).

Su enfoque combina **procesamiento de texto**, **análisis contextual** y **automatización de navegación web**, logrando identificar de forma precisa el enlace correcto entre múltiples candidatos, incluso en sitios con estructuras dinámicas o sin patrones uniformes.

---

## 📋 Características principales

* 🔍 **Identificación inteligente de enlaces:** sistema de ponderación que analiza coincidencias entre nombre del fondo, fecha (mes/año) y términos clave como “ficha técnica”.
* 🧾 **Normalización avanzada de texto:** eliminación de acentos, codificaciones URL, UUIDs y parámetros dinámicos.
* 🧠 **Coincidencias semánticas:** detección de variaciones en los nombres de los fondos (abreviaciones, palabras omitidas, orden alterado).
* 📆 **Análisis temporal:** reconocimiento de meses y años en formato textual y numérico (ej. `sep`, `09`, `2025`, `202509`).
* 🌐 **Navegación híbrida:** uso de **Selenium** y **Playwright** para cubrir tanto páginas estáticas como visores PDF dinámicos.
* 💾 **Descarga estructurada:** los archivos se guardan con jerarquía organizada por entidad, año y mes.
* ⚙️ **Extensible:** agregar una nueva administradora requiere solo incluir su enlace base en el archivo JSON de configuración.

---

## 🧩 Arquitectura del sistema

El proyecto se compone de tres módulos principales:

1. **`LinkExtractor`**

   * Lee el archivo JSON con las administradoras y los enlaces base.
   * Genera una lista de tuplas `(administradora, fondo, url)` que alimenta al scraper.

2. **`Scraping`**

   * Núcleo del sistema.
   * Normaliza textos, genera variaciones de nombres y fechas, aplica el modelo de ponderación y descarga los archivos seleccionados.

3. **Script principal (`crawler` o `main.py`)**

   * Orquesta la ejecución del scraping.
   * Navega con Selenium o Playwright según el caso.
   * Llama a `filter_links_with_ai()` para seleccionar el enlace correcto.

---

## 🧠 Lógica de ponderación

Cada enlace encontrado en una página es evaluado mediante un **sistema de pesos** que combina tres criterios:

| Criterio          | Descripción                                                                   | Peso máximo |
| ----------------- | ----------------------------------------------------------------------------- | ----------- |
| Nombre del fondo  | Coincidencias exactas o parciales con variaciones generadas                   | 1.5         |
| Fecha (mes y año) | Coincidencias numéricas o textuales, con patrones tipo `MMYYYY` o `YYYYMMDD`  | 3.0         |
| Palabra clave     | Presencia de términos como “ficha técnica”, “fichatecnica”, “fichas técnicas” | 1.5         |

El enlace con mayor puntuación acumulada es considerado el más relevante y se selecciona para la descarga.

---

## 🧰 Requisitos del entorno

* **Python 3.11 o superior**
* Librerías necesarias:

  ```bash
  pip install requests beautifulsoup4 selenium playwright unidecode urllib3
  ```
* Configurar **Playwright** tras la instalación:

  ```bash
  playwright install
  ```

---

## 🚀 Ejecución

1. Colocar el archivo `fondos.json` en el directorio raíz con la estructura:

   ```json
   {
     "bancolombia": {
       "fiducuenta": "https://fiduciaria.grupobancolombia.com/productos-servicios/fondos-inversion-colectiva/fichas-tecnicas"
     },
     "bbva": {
       "digital": "https://www.bbvaassetmanagement.com/co/index.html#!/fichaco/BBVFDIGCB"
     }
   }
   ```

2. Ejecutar el script principal indicando el mes y año deseado:

   ```bash
   python main.py septiembre 2025
   ```

3. Los archivos se descargarán en:

   ```
   ScrapingFichas/
   └── Fichas tecnicas/
       ├── Bancolombia_2025/
       │   └── 09/
       │       └── FIC_PlanSemilla.pdf
       └── BBVA_2025/
           └── 09/
               └── FIC_Digital.pdf
   ```

---

## 📊 Resultados esperados

Durante las pruebas, el sistema alcanzó los siguientes indicadores promedio:

| Métrica | Descripción                                                           | Valor    |
| ------- | --------------------------------------------------------------------- | -------- |
| **PE**  | Precisión de enlace: porcentaje de fichas correctamente identificadas | **92 %** |
| **CS**  | Cobertura semántica: casos con coincidencias parciales válidas        | **97 %** |
| **TD**  | Tasa de éxito de descarga: archivos PDF descargados sin error         | **95 %** |

Estos resultados evidencian la efectividad del modelo semántico ponderado frente a estructuras web heterogéneas.

---

## 🧱 Estructura del repositorio

```
ScrapingFichas/
│
├── Scraping.py          # Lógica principal de normalización, pesos y descarga
├── LinkExtractor.py     # Módulo para leer el JSON de administradoras
├── main.py              # Script orquestador del proceso
├── fondos.json          # Configuración de administradoras y enlaces base
├── Fichas tecnicas/     # Carpeta de salida de las descargas
│   └── {Admin}_{Año}/{Mes}/
└── README.md
```

---

## 📈 Conclusión

El módulo **Scraping** constituye una herramienta robusta de automatización semántica que combina **procesamiento de texto, análisis de contexto y navegación automatizada**.
Gracias a su diseño modular, puede adaptarse fácilmente a nuevas fuentes y mantener un alto nivel de precisión en la identificación de fichas técnicas de fondos de inversión, contribuyendo directamente al flujo ETL y análisis posterior de la información financiera.
