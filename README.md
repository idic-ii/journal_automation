# Journal Automation

Generador automático de informes técnicos sobre integridad científica y métricas de revistas académicas para el IDIC (Universidad de Lima).

## Arquitectura

El proyecto está dividido en dos servicios principales:

- **Backend (`/backend`)**: API construida en Python con **FastAPI**. Extrae datos de la API de Scopus, Web of Science, y realiza scraping con Playwright. Se comunica mediante WebSockets para streaming en tiempo real y genera documentos de Word (`.docx`).
- **Frontend (`/frontend`)**: Interfaz de usuario construida en **React y Vite**. Muestra la recolección de datos en tiempo real mediante WebSockets y permite la previsualización del documento generado.

## Inicio Rápido

Para iniciar ambos servicios al mismo tiempo en Windows, simplemente haz doble clic en el archivo:
`iniciar.bat`

Esto levantará el backend, el frontend, y abrirá automáticamente tu navegador.
