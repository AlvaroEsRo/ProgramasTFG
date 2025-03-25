# ProgramasTFG

#Inicializar env
# Bug Tracker Excel - Herramienta de Análisis y Gestión

## Descripción

Bug Tracker Excel es una aplicación web desarrollada en Flask que permite analizar archivos Excel de seguimiento de bugs, identificar nuevos problemas, bugs cerrados, aún abiertos y generar reportes para plataformas como Jira. Especialmente diseñada para integrarse con los procesos de Motorola.

## Características Principales

- **Análisis de Excel**: Procesa archivos Excel con información de bugs desde la fila 11
- **Detección inteligente de columnas**: Reconoce diferentes formatos de columnas en Excel
- **Clasificación automática de bugs**: Categoriza bugs como nuevos, cerrados, aún abiertos o repetidos
- **Base de datos persistente**: Almacena el historial de bugs para análisis comparativo
- **Vista detallada de bugs**: Visualización completa de cada bug con toda su información
- **Integración con Jira**: Generación de reportes formateados para Jira

## Requisitos

- Python 3.6 o superior
- Flask
- pandas
- SQLite3

## Instalación

1. Clone el repositorio:
```bash
git clone https://github.com/tuusuario/TFGProgramas.git
cd TFGProgramas