# Script de Depuración de Grafos de Conocimiento

## Descripción

Este script aplica **Entity Resolution (ER) por capas** para detectar y consolidar nodos duplicados en el grafo de conocimiento generado por el script de ingesta. Preserva la trazabilidad completa mediante aliases y auditoría de cada merge realizado.

## Características Clave

✅ **Entity Resolution en 4 capas** - Determinística, Fuzzy, Contextual, Semántica
✅ **Blocking inteligente** - Reduce comparaciones O(n²) a O(n*k)
✅ **Merge controlado** - Resolución de conflictos automática (timestamp, fuente, votación)
✅ **Preservación de provenance** - Mantiene aliases y evidencias
✅ **Auditoría completa** - Cada merge queda registrado en Neo4j
✅ **Embeddings opcionales** - Búsqueda semántica con OpenAI
✅ **Reporte detallado** - Estadísticas antes/después con métricas

## Arquitectura del Pipeline

```
Grafo Inicial
  → Capa 1: ER Determinística (clave exacta)
  → Capa 2: ER Fuzzy (similitud de texto)
  → Capa 3: ER Contextual (vecinos compartidos)
  → Capa 4: ER Semántica (embeddings - opcional)
  → Merge Controlado (preserva aliases + evidencias)
  → Auditoría (nodos :MergeAudit)
  → Grafo Depurado
```

## Prerequisitos

1. **Haber ejecutado el script de ingesta** (`graph_ingestion.py`)
2. **Neo4j corriendo** con datos cargados
3. **Python 3.8+**
4. **APOC plugin** instalado en Neo4j (opcional, mejora performance)

## Instalación

### 1. Instalar dependencias

```bash
pip install -r requirements.txt
```

Esto instalará:
- `rapidfuzz` - Similitud fuzzy (Levenshtein, Jaro-Winkler)
- `numpy` - Operaciones con embeddings
- Otras dependencias ya instaladas del script de ingesta

### 2. Configurar variables de entorno

El script usa las mismas variables de `.env` que el script de ingesta:

```env
NEO4J_URI=neo4j+s://tu-instancia.databases.neo4j.io
NEO4J_USER=neo4j
NEO4J_PASSWORD=tu_password

# Opcional para embeddings
OPENAI_API_KEY=sk-proj-TU_API_KEY
```

### 3. Configurar embeddings (opcional)

Si quieres usar ER semántico con embeddings:

```bash
cp embedding_config.json.example embedding_config.json
```

Editar `embedding_config.json`:

```json
{
  "enabled": true,
  "model": "text-embedding-3-small",
  "nodos_con_embedding": [
    {
      "label": "Prestacion",
      "embedding_property": "embedding",
      "text_source": ["nombre", "descripcion"],
      "threshold": 0.85
    }
  ]
}
```

**Si no creas este archivo**, el script saltará la fase de embeddings automáticamente.

## Uso

### Ejecución básica

```bash
python graph_deduplication.py
```

### Salida esperada

```
================================================================================
🧹 PIPELINE DE DEPURACIÓN DE GRAFOS DE CONOCIMIENTO
================================================================================

📊 Recopilando estadísticas iniciales...
   Nodos totales: 1,250
   Relaciones totales: 3,420

================================================================================
🔍 ENTITY RESOLUTION POR CAPAS
================================================================================

================================================================================
📋 Procesando: Normativa
================================================================================

   🔍 Capa Determinística: Normativa
      ✅ 12 duplicados encontrados

   🔍 Capa Fuzzy: Normativa
      Campos: ['titulo'], Umbral: 0.85, Blocking: anio
      Bloques creados: 5
      Comparaciones: 245
      ✅ 5 duplicados encontrados

   🔍 Capa Contextual: Normativa
      Relaciones: ['REGULADA_POR', 'CONTIENE'], Min compartidos: 3
      ✅ 3 duplicados encontrados

================================================================================
🔨 EJECUTANDO MERGES
================================================================================

Total de duplicados a mergear: 61
   Procesados: 10/61
   Procesados: 20/61
   ...
✅ Merges completados: 61/61

📊 Recopilando estadísticas finales...
📝 Generando reporte...

================================================================================
REPORTE DE DEPURACIÓN DEL GRAFO DE CONOCIMIENTO
================================================================================

...

================================================================================
✅ DEPURACIÓN COMPLETADA
================================================================================
```

## Conceptos de Entity Resolution

### 1. Capa Determinística (Exacta)

**Objetivo:** Encontrar duplicados con clave idéntica (después de normalizar)

**Ejemplo:**
- "Resolución 123/2024 INSSJP"
- "RES 123/2024 INSSJP"
- **Normalización:** tipo="resolucion", numero="123", anio=2024, emisor="inssjp"
- **Resultado:** MERGE (score=1.0)

**Configuración por entidad:**
```python
"Normativa": {
    "identity_keys": ["tipo", "numero", "anio", "emisor"],
    "normalize_keys": ["tipo", "emisor"]  # Estos se normalizan a lowercase
}
```

### 2. Capa Fuzzy (Similitud de Texto)

**Objetivo:** Encontrar duplicados con nombres similares pero no idénticos

**Algoritmos:**
- Levenshtein ratio
- Jaro-Winkler
- Token set ratio

**Ejemplo:**
- "Prótesis auditiva digital retroauricular"
- "Protesis audifiva digital retro-auricular"
- **Similitud:** 0.92 > umbral (0.85)
- **Resultado:** MERGE

**Blocking:** Para evitar O(n²), agrupa por clave parcial:
```python
"fuzzy": {
    "compare_fields": ["titulo", "nombre"],
    "threshold": 0.85,
    "blocking_key": "anio"  # Solo compara dentro del mismo año
}
```

### 3. Capa Contextual (Vecinos Compartidos)

**Objetivo:** Detectar duplicados por relaciones similares

**Ejemplo:**
- Normativa A REGULA prestaciones [P1, P2, P3, P4, P5]
- Normativa B REGULA prestaciones [P1, P2, P3, P4, P5]
- **Vecinos compartidos:** 5 >= 3 (umbral)
- **Resultado:** MERGE

**Configuración:**
```python
"contextual": {
    "enabled": True,
    "shared_relations": ["REGULADA_POR", "CONTIENE"],
    "min_shared": 3  # Mínimo de vecinos en común
}
```

### 4. Capa Semántica (Embeddings - Opcional)

**Objetivo:** Detectar duplicados semánticamente similares

**Ejemplo:**
- "Prótesis de cadera con revestimiento de titanio"
- "Implante femoral recubierto en aleación de titanio"
- **Embedding similarity:** 0.88 > umbral (0.85)
- **Resultado:** MERGE

**Requiere:**
1. Generar embeddings primero
2. Configuración en `embedding_config.json`

**Cómo funciona:**
```python
# 1. Generar embedding de concatenación de campos
text = f"{nombre} - {descripcion}"
embedding = openai.embeddings.create(text)

# 2. Comparar similitud coseno
similarity = cosine_similarity(emb1, emb2)

# 3. Merge si > umbral
if similarity >= 0.85:
    merge()
```

## Merge Controlado

### Consolidación de Propiedades

**Problema:** Ambos nodos tienen la misma propiedad con valores diferentes

**Soluciones implementadas:**

#### 1. Resolución por Timestamp (default)
```python
# El valor más reciente prevalece
if canonical.updated_at > duplicate.updated_at:
    usar canonical.titulo
else:
    usar duplicate.titulo
```

#### 2. Resolución por Fuente Autorizada
```python
# Ranking de confianza
RANKING = {
    "documento_oficial": 1.0,
    "pdf_scraping": 0.7,
    "api_externa": 0.5
}

# Usa el valor de la fuente con mayor confianza
```

#### 3. Resolución por Votación
```python
# Si múltiples duplicados, la mayoría gana
valores = ["Resolución", "Resolucion", "Resolución"]
# "Resolución" aparece 2 veces → gana
```

### Preservación de Aliases

Todos los IDs previos se mantienen:

```cypher
(:Normativa {
  id: "Resolución-2563-2024-INSSJP-DE",  // ID canónico
  aliases: [
    "RES-2563-2024-INSSJP",
    "Resol-2563-24-INSSJP",
    "RESOL-2563-INSSJP-DE"
  ],
  titulo: "Aprobación del Nomenclador...",
  updated_at: "2024-12-17T10:30:00Z"
})
```

**Ventaja:** Búsquedas por cualquier ID anterior siguen funcionando:

```cypher
MATCH (n:Normativa)
WHERE n.id = "RES-2563-2024" OR "RES-2563-2024" IN n.aliases
RETURN n
```

### Preservación de Evidencias

Todas las evidencias se mantienen:

```cypher
// Antes del merge
(Duplicate)-[:RESPALDA]->(Evidencia1)
(Duplicate)-[:RESPALDA]->(Evidencia2)

// Después del merge
(Canonical)-[:RESPALDA]->(Evidencia1)
(Canonical)-[:RESPALDA]->(Evidencia2)
// Duplicate eliminado
```

## Auditoría Completa

Cada merge crea un nodo `:MergeAudit`:

```cypher
(:MergeAudit {
  id: "MERGE-a3f5d8c29b47",
  canonical_id: "Resolución-2563-2024-INSSJP-DE",
  merged_id: "RES-2563-2024-INSSJP",
  razon: "deterministic",
  score: 1.0,
  fecha: "2024-12-17T10:30:15Z",
  revertido: false,
  aliases_count: 3
})
```

### Consultas de Auditoría

**Ver todos los merges:**
```cypher
MATCH (audit:MergeAudit)
RETURN audit
ORDER BY audit.fecha DESC
```

**Ver merges de una entidad específica:**
```cypher
MATCH (audit:MergeAudit)
WHERE audit.canonical_id = "Resolución-2563-2024-INSSJP-DE"
   OR audit.merged_id = "Resolución-2563-2024-INSSJP-DE"
RETURN audit
```

**Ver merges por capa:**
```cypher
MATCH (audit:MergeAudit)
WHERE audit.razon = "fuzzy"
RETURN audit.canonical_id, audit.merged_id, audit.score
ORDER BY audit.score DESC
```

**Ver merges con score bajo (revisar manualmente):**
```cypher
MATCH (audit:MergeAudit)
WHERE audit.score < 0.90 AND audit.razon IN ["fuzzy", "semantic"]
RETURN audit
```

## Archivos Generados

### 1. Reporte de Depuración
**Ubicación:** `output/deduplication_report.txt`

Contiene:
- Estadísticas antes/después
- Merges por capa
- Reducción de nodos
- Archivos generados

**Ejemplo:**
```
================================================================================
REPORTE DE DEPURACIÓN DEL GRAFO DE CONOCIMIENTO
================================================================================

**Fecha:** 2024-12-17T10:45:00
**Schema Version:** 1.0

## 1. ESTADÍSTICAS INICIALES

**Antes de la depuración:**
- Total de nodos: 1,250
- Total de relaciones: 3,420

**Distribución por tipo:**
| Tipo Nodo     | Cantidad |
|---------------|----------|
| Normativa     |      150 |
| Prestacion    |      420 |
| Articulo      |      580 |
...

## 2. ENTITY RESOLUTION APLICADO

### 2.1 Capa Deterministic

**Duplicados mergeados:** 20
**Score promedio:** 1.000

### 2.2 Capa Fuzzy

**Duplicados mergeados:** 16
**Score promedio:** 0.890

...

## 3. CONSOLIDACIÓN FINAL

**Después de la depuración:**
- Total de nodos: 1,189 (reducción: 61 nodos / 4.9%)
- Total de relaciones: 3,520
```

### 2. Log de Auditoría
**Ubicación:** `output/merge_audit.json`

Array JSON con todos los merges:

```json
[
  {
    "merge_id": "MERGE-a3f5d8c29b47",
    "canonical_id": "Resolución-2563-2024-INSSJP-DE",
    "merged_id": "RES-2563-2024-INSSJP",
    "razon": "deterministic",
    "score": 1.0,
    "fecha": "2024-12-17T10:30:15Z",
    "aliases_count": 3,
    "props_merged": 8
  },
  ...
]
```

## Configuración Avanzada

### Ajustar Umbrales de Similitud

En el código, modificar:

```python
er_rules = {
    "Prestacion": {
        "fuzzy": {
            "threshold": 0.90  # Más estricto (menos falsos positivos)
        }
    }
}
```

**Recomendaciones:**
- **0.95-1.0:** Muy estricto (solo variaciones mínimas)
- **0.85-0.94:** Balanceado (recomendado)
- **0.70-0.84:** Permisivo (más falsos positivos)

### Deshabilitar Capas

```python
"fuzzy": {
    "enabled": False  # Salta la capa fuzzy
}
```

### Cambiar Estrategia de Blocking

```python
"fuzzy": {
    "blocking_key": "emisor"  # Agrupar por emisor en vez de año
}
```

## Troubleshooting

### Error: "No se encontró rapidfuzz"

**Solución:**
```bash
pip install rapidfuzz
```

### Error: "APOC procedure not found"

El script intenta usar APOC para merge eficiente, pero si falla, usa un método manual.

**Para mejor performance, instalar APOC:**
1. Descargar APOC desde https://github.com/neo4j-contrib/neo4j-apoc-procedures
2. Copiar JAR a `plugins/` de Neo4j
3. Reiniciar Neo4j

### Warning: "Muchos duplicados fuzzy con score bajo"

**Causa:** Umbral muy permisivo

**Solución:** Aumentar threshold:
```python
"threshold": 0.90  # En vez de 0.85
```

### Performance lento en grafos grandes

**Solución 1:** Ajustar blocking
```python
"blocking_key": "tipo_prestacion"  # Bloques más pequeños
```

**Solución 2:** Procesar por lotes
```python
# En el código, agregar LIMIT
query = f"""
MATCH (n:{label})
WHERE n.{blocking_key} IS NOT NULL
WITH n LIMIT 1000  # Procesar de a 1000
...
"""
```

## Métricas de Calidad

### Precisión y Recall

Para evaluar la calidad del ER:

1. **Crear muestra manual** (50-100 pares)
2. **Marcar manualmente** si son duplicados o no
3. **Comparar con resultados del script**

**Fórmulas:**
- **Precision = TP / (TP + FP)**
  - TP: Script dijo duplicado Y era duplicado
  - FP: Script dijo duplicado pero NO era duplicado

- **Recall = TP / (TP + FN)**
  - FN: Script dijo NO duplicado pero SÍ era duplicado

- **F1 = 2 * (Precision * Recall) / (Precision + Recall)**

**Valores buenos:**
- Precision > 0.90
- Recall > 0.85
- F1 > 0.87

## Integración con el Pipeline

### Orden de Ejecución

```bash
# 1. Ingesta (carga datos al grafo)
python graph_ingestion.py

# 2. Depuración (consolida duplicados)
python graph_deduplication.py

# 3. Análisis (próximo paso - detección de inconsistencias)
# ... futuro script
```

### Automatización

Crear script bash `pipeline.sh`:

```bash
#!/bin/bash

echo "=== PIPELINE DE GRAFOS DE CONOCIMIENTO ==="

# Paso 1: Ingesta
echo "1. Ejecutando ingesta..."
python graph_ingestion.py

# Paso 2: Depuración
echo "2. Ejecutando depuración..."
python graph_deduplication.py

echo "=== PIPELINE COMPLETADO ==="
```

Ejecutar:
```bash
chmod +x pipeline.sh
./pipeline.sh
```

## Próximos Pasos

Después de ejecutar la depuración:

1. **Revisar reporte** en `output/deduplication_report.txt`
2. **Validar merges** con score < 0.90
3. **Consultar nodos consolidados** en Neo4j
4. **Ejecutar consultas del objetivo** para verificar funcionalidad
5. **Próxima fase:** Análisis de inconsistencias normativas

## Soporte

Para reportar problemas:
- Revisar logs en `output/`
- Consultar `merge_audit.json` para ver qué se mergeó
- Verificar queries en Neo4j

## Licencia

Generado automáticamente por el Agente de Depuración v1.0
