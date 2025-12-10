# Proceso de Creación y Consulta del Grafo de Conocimiento de Prótesis

## Diagrama del Proceso

![Diagrama del Proceso del Grafo de Prótesis](./diagrama_proceso.png)

*Nota: Agregar aquí la imagen del diagrama que muestra el flujo completo del proceso, desde el LLM hasta las consultas del usuario.*

---

## Descripción del Proceso

Este proceso comprende las siguientes partes:

### 1) Elaboración del Goal y Boceto del Schema

**Objetivo:** Definir la estructura del grafo de conocimiento basándose en los requerimientos del dominio.

**Herramienta:** Se utiliza NotebookLM (Google) para la asistencia en la elaboración del schema.

🔗 **Enlace a NotebookLM:** https://notebooklm.google.com/notebook/8554a208-e3f3-4cca-b1e3-3df4813bb599

**Proceso:**
- Se trabaja en colaboración con el LLM para definir:
  - Los nodos (entidades) del grafo
  - Las relaciones entre nodos
  - Las propiedades de cada nodo y relación
  - Las reglas de negocio y restricciones

**Resultado:**
- Se genera un archivo de texto con el boceto del schema llamado: `pami_schema_input.txt`

---

### 2) Conversión del Boceto TXT a JSON

**Objetivo:** Transformar el boceto en texto plano a un formato estructurado JSON que permita la extracción posterior.

**Comando:**
```bash
python gene_txt_json.py
```

**Proceso:**
- Lee el archivo `pami_schema_input.txt`
- Parsea y estructura la información
- Genera un archivo JSON con la definición del schema

**Resultados:**
- Archivo JSON estructurado con la definición del schema
- Validación de la estructura del schema

---

### 3) Extracción (Extract) de Información desde PDFs

**Objetivo:** Extraer información de documentos PDF y poblarla en Neo4j según el schema definido.

**Requisitos previos:**

1. **Archivos PDF:**
   - Colocar los archivos PDF en la subcarpeta especificada en `.env`:
     ```
     PDF_DIR=./import_data/pdf
     ```
   - Los PDFs deben contener la información relevante para el dominio (normativas, prestaciones, etc.)

2. **Archivo de configuración:**
   - Debe existir el archivo `builder_config.json` con la configuración necesaria para el proceso de extracción

**Comando:**
```bash
python gene_builder_prop.py execute   # Modo EXTRACT
```

**Proceso:**
- Lee los archivos PDF desde la carpeta especificada
- Utiliza el LLM para extraer información estructurada según el schema
- Genera consultas Cypher para crear los nodos y relaciones en Neo4j
- Ejecuta las consultas para poblar la base de datos

**Resultados:**
- **Base de datos Neo4j:** Se genera la estructura completa del schema en Neo4j
- **Archivo de log:** Se muestra y guarda el log del schema generado en el archivo `cypher_queries_log.cypher`
  - Este archivo contiene todas las consultas Cypher ejecutadas para crear la estructura del grafo

---

### 4) Consultas con el Asistente

**Objetivo:** Realizar consultas en lenguaje natural sobre el grafo de conocimiento utilizando el asistente basado en LangChain.

**Comando:**
```bash
python graph_assistant.py   # ASISTENTE
```

**Proceso:**
- Se inicializa la conexión con Neo4j
- Se carga el esquema del grafo para contexto del LLM
- Se inicializa el modelo de lenguaje (OpenAI)
- Se crea una cadena de consulta (`GraphCypherQAChain`) que:
  - Recibe preguntas en lenguaje natural
  - Genera consultas Cypher automáticamente
  - Ejecuta las consultas en Neo4j
  - Formatea las respuestas de manera legible

**Funcionalidades:**
- Consultas interactivas: El usuario puede hacer preguntas sobre normativas, prestaciones, relaciones, etc.
- Generación automática de Cypher: El LLM genera las consultas Cypher basándose en el esquema
- Visualización de consultas: Se muestra tanto la consulta Cypher generada como la respuesta final
- Modo verbose: Permite ver los pasos intermedios del proceso

**Ejemplos de consultas:**
- "¿Cuántas normativas hay en la base de datos?"
- "Lista todas las prestaciones relacionadas con prótesis dentales"
- "Muestra las relaciones entre normativas y prestaciones"
- "¿Qué prestaciones están vigentes actualmente?"

---

## Resumen del Flujo

```
1. LLM (NotebookLM) → pami_schema_input.txt
2. gene_txt_json.py → Schema en formato JSON
3. gene_builder_prop.py (EXTRACT) → Neo4j DB + cypher_queries_log.cypher
4. graph_assistant.py → Consultas interactivas del usuario
```

---

## Archivos Clave del Proceso

| Archivo | Descripción | Generado por |
|---------|-------------|--------------|
| `pami_schema_input.txt` | Boceto del schema en texto plano | Manual + NotebookLM |
| `builder_config.json` | Configuración para la extracción | Manual |
| `cypher_queries_log.cypher` | Log de consultas Cypher ejecutadas | `gene_builder_prop.py` |
| `.env` | Variables de entorno (PDF_DIR, Neo4j, OpenAI) | Manual |

---

## Variables de Entorno Requeridas

Asegúrate de tener configurado el archivo `.env` con las siguientes variables:

```env
# Neo4j
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=tu_password

# OpenAI
OPENAI_API_KEY=tu_api_key
OPENAI_MODEL=gpt-4o-mini

# Directorios
PDF_DIR=./import_data/pdf
```
