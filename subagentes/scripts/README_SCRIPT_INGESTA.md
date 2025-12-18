# Script de Ingesta de Datos para Grafo de Conocimiento

## Descripción

Este script automatiza la extracción, normalización, validación y carga de datos desde PDFs/TXTs hacia Neo4j, siguiendo el schema diseñado y el objetivo validado del grafo de conocimiento.

## Características Clave

✅ **Extracción guiada por el objetivo del grafo** - El objetivo se incluye en todos los prompts
✅ **Normalización automática de datos** - Fechas, strings, números de ley
✅ **Validación exhaustiva contra schema** - Propiedades obligatorias, tipos, enumeraciones
✅ **Estructuración en JSON intermedio** - Datos validados antes de cargar
✅ **Creación automática de evidencia (provenance)** - Cada dato tiene trazabilidad
✅ **Logging completo de queries Cypher** - Todas las queries ejecutadas
✅ **Manejo de errores robusto** - Continúa procesando aunque falle un archivo
✅ **Estadísticas de procesamiento** - Tokens, nodos, relaciones

## Arquitectura del Pipeline

```
PDFs/TXTs
  → Extracción (LLM con objetivo)
  → Normalización (fechas, strings, números)
  → Validación (contra schema)
  → Estructuración (JSON con metadatos)
  → Neo4j
```

## Prerequisitos

1. **Python 3.8+**
2. **Neo4j 5.x** instalado y corriendo
3. **Cuenta de OpenAI** con API key activa

## Instalación

### 1. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 2. Configurar variables de entorno

Copiar `.env.example` a `.env` y configurar:

```bash
cp .env.example .env
```

Editar `.env` con tus credenciales:

```env
# OpenAI
OPENAI_API_KEY=sk-proj-TU_API_KEY_AQUI
LLM_MODEL=gpt-4o-mini

# Neo4j
NEO4J_URI=neo4j+s://tu-instancia.databases.neo4j.io
NEO4J_USER=neo4j
NEO4J_PASSWORD=tu_password

# Directorios
PDF_DIR=../contexto_dominio
```

### 3. Verificar archivos necesarios

El script requiere:
- `../resultados/objetivo_validado.md` - Objetivo del grafo
- `../resultados/schema_diseñado.md` - Schema del grafo
- `../contexto_dominio/*.pdf` - PDFs a procesar

## Uso

### Ejecución básica

```bash
python graph_ingestion.py
```

### Salida esperada

```
================================================================================
🚀 PIPELINE DE INGESTA DE GRAFOS DE CONOCIMIENTO
================================================================================

🎯 OBJETIVO: Construir un grafo de conocimiento que integre prestaciones PAMI...
📊 DOMINIO: healthcare
📐 SCHEMA: 7 nodos, 8 relaciones

📐 Creando constraints e índices...
   ✅ Constraint: Normativa (tipo, numero, anio, emisor)
   ✅ Constraint: Prestacion (codigo_prestacion, tipo_prestacion)
   ✅ Índice: Normativa.titulo
   ✅ Índice: Prestacion.nombre

📁 Archivos a procesar: 3

📄 Procesando: RESOL-2024-2563-INSSJP-DE#INSSJP.pdf
   📝 Contenido: 125430 caracteres
   📦 Chunks: 9
   🔄 Chunk 1/9...
   🔄 Chunk 2/9...
   ...
   ✅ Completado - Nodos: 45, Relaciones: 38, Tokens: 12,450

================================================================================
✅ PIPELINE COMPLETADO
================================================================================
📄 Archivos procesados: 3
📊 Total Nodos creados: 123
📊 Total Relaciones creadas: 98
🔥 Total Tokens: 35,240

📁 Salidas generadas:
   - JSONs intermedios: output/*_chunk_*.json
   - Log Cypher: output/cypher_queries_log.cypher
================================================================================
```

## Archivos Generados

### 1. JSONs Intermedios
**Ubicación:** `output/{doc_id}_chunk_{i}.json`

Contienen los datos extraídos, normalizados y validados antes de cargar a Neo4j:

```json
{
  "metadata": {
    "doc_id": "RESOL-2024-2563-INSSJP-DE",
    "source_type": "pdf",
    "extraction_date": "2024-12-17T10:30:00",
    "schema_version": "1.0",
    "objetivo": "Construir un grafo..."
  },
  "nodo_raiz": {...},
  "entidades_extraidas": [...],
  "relaciones": [...],
  "inconsistencias_potenciales": [...],
  "errores_validacion": [...]
}
```

### 2. Log de Cypher
**Ubicación:** `output/cypher_queries_log.cypher`

Contiene todas las queries Cypher ejecutadas:

```cypher
// QUERIES CYPHER GENERADAS
// Fecha: 2024-12-17T10:30:00

// NODO + EVIDENCIA: Normativa (Resolución-2563-2024-INSSJP-DE)
MERGE (n:`Normativa` {id: $id})
SET n += $props
...
```

## Componentes del Script

### 1. Parsers
- `objetivo_parser.py` - Extrae información del objetivo validado
- `schema_parser.py` - Extrae información del schema diseñado

### 2. Normalización
- Fechas → ISO 8601 (YYYY-MM-DD)
- Strings → lowercase sin tildes (para búsqueda)
- Números de ley → formato estándar (19.549)

### 3. Validación
- Propiedades obligatorias
- Tipos de datos
- Valores permitidos (enumeraciones)
- Reglas de identidad (claves compuestas)

### 4. Evidencia (Provenance)
Cada dato extraído tiene un nodo `:Evidencia` vinculado:

```cypher
(:Normativa)-[:RESPALDA]->(:Evidencia {
  source_path: "contexto_dominio/RESOL-2024-2563.pdf",
  page: 5,
  text_fragment: "ARTÍCULO 5°.- Apruébase...",
  confidence_score: 0.95
})
```

## Configuración Avanzada

### Cambiar el modelo LLM

En `.env`:
```env
LLM_MODEL=gpt-4o-mini  # Más económico
# O
LLM_MODEL=gpt-4o       # Más preciso
```

### Cambiar el tamaño de chunks

En `graph_ingestion.py`, línea ~730:
```python
chunk_size = 15000  # Ajustar según necesidad
```

### Procesar PDFs de otro directorio

En `.env`:
```env
PDF_DIR=/ruta/a/otros/pdfs
```

## Troubleshooting

### Error: "No se encontró soporte para PDF"

**Solución:** Instalar pdfplumber
```bash
pip install pdfplumber
```

### Error: "Faltan variables de entorno"

**Solución:** Verificar que `.env` existe y tiene todas las variables configuradas

### Error: "Connection refused" (Neo4j)

**Solución:** Verificar que Neo4j está corriendo
```bash
# Verificar status
neo4j status

# Iniciar Neo4j
neo4j start
```

### Advertencia: Tokens muy altos

**Solución:**
1. Reducir `chunk_size`
2. Usar modelo más económico (gpt-4o-mini)
3. Procesar menos archivos a la vez

## Costos Estimados (OpenAI)

Con `gpt-4o-mini`:
- **Input:** $0.150 / 1M tokens
- **Output:** $0.600 / 1M tokens

Ejemplo para procesar 3 PDFs (~400 páginas totales):
- Tokens totales: ~35,000
- Costo estimado: **$0.03 - $0.05 USD**

## Próximos Pasos

Después de ejecutar la ingesta:

1. **Verificar datos en Neo4j**
   ```cypher
   // Contar nodos por tipo
   MATCH (n) RETURN labels(n), count(*)

   // Ver ejemplos de normativas
   MATCH (n:Normativa) RETURN n LIMIT 5
   ```

2. **Revisar JSONs intermedios** para validar extracción
3. **Ejecutar consultas del objetivo** para verificar funcionalidad
4. **Ejecutar análisis de inconsistencias** (siguiente fase)

## Soporte

Para reportar problemas o sugerencias:
- Revisar logs en `output/`
- Verificar errores de validación en JSONs intermedios
- Consultar log de Cypher para queries fallidas

## Licencia

Generado automáticamente por el Agente de Ingesta v1.0
