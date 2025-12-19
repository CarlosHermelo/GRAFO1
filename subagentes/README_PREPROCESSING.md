# Pre-procesamiento de Grafo de Conocimiento

Este módulo contiene el script de **Pre-procesamiento de Grafo** que ejecuta algoritmos de detección de comunidades, cálculo de métricas de centralidad y generación de resúmenes estructurales en Neo4j.

## ¿Para Qué Sirve?

El pre-procesamiento prepara el grafo para que el **Asistente GraphRAG** pueda usar la **Estrategia 5: Comunidades + Resúmenes** de forma eficiente.

### Sin Pre-procesamiento

```
Usuario: "¿Cuáles son los temas principales en las normativas?"

GraphRAG:
❌ No puede usar estrategia de comunidades
✓ Usa estrategia alternativa (exploratoria)
→ Respuesta menos estructurada
```

### Con Pre-procesamiento

```
Usuario: "¿Cuáles son los temas principales en las normativas?"

GraphRAG:
✓ Usa estrategia de comunidades
→ "Hay 3 temas principales:
   1. Prótesis (45 normativas)
   2. Medicamentos (32 normativas)
   3. Tratamientos (28 normativas)"
→ Respuesta estructurada y clara
```

## Componentes

### 1. Agente Constructor (`agente_preprocessing_grafo.md`)
Agente experto que CREA el script de pre-procesamiento personalizado.

### 2. Script de Pre-procesamiento (`scripts/graph_preprocessing.py`)
Script ejecutable que procesa el grafo en Neo4j.

### 3. Configuración (`scripts/.env`)
Variables de entorno para Neo4j y OpenAI.

## Pre-requisitos

### 1. Neo4j con Graph Data Science (GDS) Plugin

**¿Qué es GDS?**
Plugin oficial de Neo4j para análisis avanzado de grafos (clustering, centralidad, similitud, etc.)

**Instalación:**

#### Opción A: Neo4j Desktop (Recomendado)
```
1. Abrir Neo4j Desktop
2. Seleccionar tu base de datos
3. Click en "Plugins"
4. Buscar "Graph Data Science"
5. Click en "Install"
6. Restart database
```

#### Opción B: Neo4j Server (Docker)
```bash
docker run \
    -p 7474:7474 -p 7687:7687 \
    -e NEO4J_AUTH=neo4j/your-password \
    -e NEO4J_PLUGINS='["graph-data-science"]' \
    neo4j:latest
```

#### Opción C: Neo4j Server (Manual)
```bash
# 1. Descargar GDS plugin
wget https://github.com/neo4j/graph-data-science/releases/download/2.5.0/neo4j-graph-data-science-2.5.0.jar

# 2. Copiar a plugins/
cp neo4j-graph-data-science-2.5.0.jar $NEO4J_HOME/plugins/

# 3. Editar neo4j.conf
echo "dbms.security.procedures.unrestricted=gds.*" >> $NEO4J_HOME/conf/neo4j.conf

# 4. Reiniciar Neo4j
neo4j restart
```

**Verificar instalación:**
```cypher
// En Neo4j Browser
RETURN gds.version()
```

### 2. Grafo Poblado

El grafo debe tener datos:
```bash
# Verificar que hay nodos
cypher-shell -u neo4j -p password "MATCH (n) RETURN count(n);"
# Debe retornar > 0
```

### 3. OpenAI API Key (Opcional)

Solo necesario si quieres generar resúmenes de comunidades con LLM.

## Instalación

### 1. Instalar Dependencias

```bash
cd scripts
pip install -r requirements.txt
```

Instala:
- `neo4j` (driver de Python)
- `langchain-openai` (para resúmenes con LLM)
- `tqdm` (barras de progreso)

### 2. Configurar Variables de Entorno

```bash
# Copiar archivo de ejemplo
cp scripts/.env.preprocessing.example scripts/.env

# Editar y configurar
nano scripts/.env
```

Configuración mínima:
```bash
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=tu-password

# Opcional (solo si generas resúmenes)
OPENAI_API_KEY=sk-tu-api-key-aqui
```

## Uso

### Ejecución Básica

```bash
python scripts/graph_preprocessing.py
```

**Output esperado:**
```
======================================================================
PRE-PROCESAMIENTO DE GRAFO DE CONOCIMIENTO
======================================================================

[INFO] Verificando Neo4j GDS plugin...
[INFO] Neo4j GDS versión: 2.5.0
[SUCCESS] GDS plugin disponible

[INFO] Limpiando procesamiento previo...
[INFO] Limpieza completada

[INFO] Proyectando grafo en memoria...
[SUCCESS] Grafo proyectado: 1,234 nodos, 3,456 relaciones

[INFO] Ejecutando louvain...
  - Comunidades detectadas: 12
  - Modularidad: 0.7834
[SUCCESS] 12 comunidades detectadas

[INFO] Calculando métricas de centralidad...
  ✓ PageRank calculado
  ✓ Betweenness Centrality calculado
  ✓ Degree Centrality calculado
[SUCCESS] Métricas calculadas

[INFO] Generando resúmenes de comunidades...
Generando resúmenes: 100%|████████████| 12/12 [00:45<00:00]
[SUCCESS] Resúmenes generados

[INFO] Validando pre-procesamiento...
  ✓ Nodos con community_id: 1,234
  ✓ Nodos Community creados: 12
  ✓ Métricas calculadas: pagerank, betweenness, degree
[SUCCESS] Validación completada exitosamente

======================================================================
✅ PRE-PROCESAMIENTO COMPLETADO EXITOSAMENTE
======================================================================

[INFO] El grafo está listo para GraphRAG con estrategia de comunidades
```

### Verificar Resultados en Neo4j

```cypher
// Ver comunidades detectadas
MATCH (c:Community)
RETURN c.id, c.name, c.summary, c.node_count
ORDER BY c.node_count DESC

// Ver nodos con comunidad asignada
MATCH (n)
WHERE n.community_id IS NOT NULL
RETURN labels(n)[0] as tipo,
       n.nombre as nombre,
       n.community_id as comunidad,
       n.pagerank as pagerank
ORDER BY n.pagerank DESC
LIMIT 20

// Distribución de nodos por comunidad
MATCH (n)
WHERE n.community_id IS NOT NULL
RETURN n.community_id as comunidad, count(n) as cantidad
ORDER BY cantidad DESC
```

## Algoritmos Disponibles

### 1. Louvain (Por Defecto - Recomendado)

**Qué hace:** Detecta comunidades maximizando modularidad

**Ventajas:**
- Excelente balance calidad/velocidad
- Resultados jerárquicos
- Ampliamente usado y validado

**Cuándo usar:** Detección general de comunidades (caso por defecto)

**Configuración:**
```bash
COMMUNITY_ALGORITHM=louvain
```

### 2. Label Propagation

**Qué hace:** Propaga etiquetas entre vecinos hasta convergencia

**Ventajas:**
- Muy rápido (O(n + m))
- Bajo uso de memoria
- Bueno para grafos grandes

**Cuándo usar:** Grafos muy grandes (> 1M nodos), necesitas velocidad

**Configuración:**
```bash
COMMUNITY_ALGORITHM=labelPropagation
```

### 3. Weakly Connected Components (WCC)

**Qué hace:** Encuentra componentes débilmente conectados

**Ventajas:**
- Muy rápido
- Determínístico
- Útil para detectar islas

**Cuándo usar:** Detectar componentes desconectados del grafo

**Configuración:**
```bash
COMMUNITY_ALGORITHM=wcc
```

## Métricas de Centralidad

### PageRank

**Qué mide:** Importancia/autoridad de un nodo

**Uso en GraphRAG:**
- Rankear resultados
- Priorizar fuentes autorizadas
- Identificar nodos clave

**Ejemplo:**
```cypher
// Nodos más importantes (mayor PageRank)
MATCH (n)
WHERE n.pagerank IS NOT NULL
RETURN labels(n)[0] as tipo, n.nombre, n.pagerank
ORDER BY n.pagerank DESC
LIMIT 10
```

### Betweenness Centrality

**Qué mide:** Cuántos paths pasan por un nodo

**Uso en GraphRAG:**
- Identificar nodos "puente"
- Detectar cuellos de botella
- Encontrar conectores clave

**Ejemplo:**
```cypher
// Nodos puente (mayor Betweenness)
MATCH (n)
WHERE n.betweenness IS NOT NULL
RETURN labels(n)[0] as tipo, n.nombre, n.betweenness
ORDER BY n.betweenness DESC
LIMIT 10
```

### Degree Centrality

**Qué mide:** Cantidad de conexiones de un nodo

**Uso en GraphRAG:**
- Identificar hubs
- Nodos altamente conectados

**Ejemplo:**
```cypher
// Nodos más conectados (mayor Degree)
MATCH (n)
WHERE n.degree IS NOT NULL
RETURN labels(n)[0] as tipo, n.nombre, n.degree
ORDER BY n.degree DESC
LIMIT 10
```

## Resúmenes de Comunidades

Si habilitas `GENERATE_SUMMARIES=true`, el script genera resúmenes automáticos usando LLM.

**Ejemplo de resumen generado:**

```
Community ID: 1
Name: Comunidad_Prótesis
Summary: "Esta comunidad agrupa normativas, prestaciones y proveedores
relacionados con dispositivos protésicos, principalmente prótesis auditivas
y ortopédicas. Incluye regulaciones sobre autorización de proveedores y
requisitos de calidad."
Node Count: 45
```

**¿Cómo se usa en GraphRAG?**

```
Usuario: "¿Cuáles son los temas principales?"

GraphRAG:
1. Vector search sobre resúmenes de comunidades
2. Identifica comunidad más relevante
3. Zoom en esa comunidad específica
4. Retorna resumen + ejemplos de nodos
```

## Configuración Avanzada

### Ajustar Algoritmo de Comunidades

```bash
# .env
COMMUNITY_ALGORITHM=louvain

# Opciones: louvain | labelPropagation | wcc
```

### Habilitar/Deshabilitar Métricas

```bash
# .env
COMPUTE_PAGERANK=true       # Calcular PageRank
COMPUTE_BETWEENNESS=false   # No calcular Betweenness (más lento)
COMPUTE_DEGREE=true         # Calcular Degree
```

### Controlar Generación de Resúmenes

```bash
# .env
GENERATE_SUMMARIES=true  # Generar resúmenes con LLM
MAX_COMMUNITIES_TO_SUMMARIZE=20  # Limitar cantidad (controlar costos)
```

## Re-ejecutar Pre-procesamiento

El script es **idempotente**: puedes re-ejecutarlo sin problemas.

```bash
# Re-ejecutar con diferentes parámetros
# El script limpia automáticamente resultados previos

python scripts/graph_preprocessing.py
```

**¿Cuándo re-ejecutar?**
- Cambió el grafo (nuevos nodos/relaciones)
- Quieres probar otro algoritmo de comunidades
- Necesitas recalcular métricas

## Troubleshooting

### Error: "GDS plugin no está instalado"

**Causa:** Neo4j no tiene el plugin Graph Data Science

**Solución:**
```
1. Neo4j Desktop: Plugins → Graph Data Science → Install
2. Neo4j Server: Ver sección "Pre-requisitos" arriba
3. Reiniciar Neo4j
```

**Verificar:**
```cypher
RETURN gds.version()
// Debe retornar versión, ej: "2.5.0"
```

### Error: "Out of memory" durante pre-procesamiento

**Causa:** Grafo muy grande para memoria disponible

**Soluciones:**

**Opción 1: Aumentar memoria de Neo4j**
```
# neo4j.conf
dbms.memory.heap.initial_size=2G
dbms.memory.heap.max_size=4G
```

**Opción 2: Procesar solo subgrafo**
```python
# Modificar script para proyectar solo ciertos tipos de nodos
CALL gds.graph.project(
  'preprocessGraph',
  ['Normativa', 'Prestacion'],  # Solo estos tipos
  '*'
)
```

**Opción 3: Usar algoritmo más liviano**
```bash
# .env - Cambiar a Label Propagation (menos memoria)
COMMUNITY_ALGORITHM=labelPropagation
```

### Error: "Connection refused" a Neo4j

**Causa:** Neo4j no está ejecutándose

**Solución:**
```bash
# Iniciar Neo4j
neo4j start

# O en Neo4j Desktop: Start database

# Verificar
neo4j status
```

### Resúmenes de baja calidad

**Causa:** Comunidades muy heterogéneas o LLM inadecuado

**Soluciones:**

**Opción 1: Usar mejor modelo**
```bash
# .env
LLM_MODEL=gpt-4  # En lugar de gpt-3.5-turbo
```

**Opción 2: Probar otro algoritmo**
```bash
# .env
COMMUNITY_ALGORITHM=louvain  # En lugar de labelPropagation
```

**Opción 3: Generar manualmente**
```bash
# .env
GENERATE_SUMMARIES=false

# Luego crear resúmenes manualmente en Neo4j
MERGE (c:Community {id: 1})
SET c.summary = "Tu resumen personalizado aquí"
```

## Costos de OpenAI

### Solo Resúmenes

Si `GENERATE_SUMMARIES=true`:

**Por comunidad:**
- Prompt: ~300-500 tokens (lista de nodos)
- Respuesta: ~50-100 tokens (resumen)
- **Costo:** ~$0.005-0.01 USD por comunidad (con GPT-4)

**Ejemplo con 20 comunidades:**
- Total: ~$0.10-0.20 USD

### Sin Resúmenes

Si `GENERATE_SUMMARIES=false`:
- **Costo:** $0 USD (no usa OpenAI)
- Solo ejecuta algoritmos de Neo4j GDS (gratis)

## Comparación de Algoritmos

| Algoritmo | Velocidad | Calidad | Uso de Memoria | Determinístico |
|-----------|-----------|---------|----------------|----------------|
| Louvain | ⚡⚡⚡ | ⭐⭐⭐⭐⭐ | ⬆️⬆️⬆️ | ❌ No |
| Label Propagation | ⚡⚡⚡⚡⚡ | ⭐⭐⭐ | ⬆️⬆️ | ❌ No |
| WCC | ⚡⚡⚡⚡⚡ | ⭐⭐ | ⬆️ | ✅ Sí |

**Recomendación general:** Usar **Louvain** (mejor balance)

## Integración con GraphRAG

Después de ejecutar el pre-procesamiento:

```bash
# 1. Pre-procesar grafo
python scripts/graph_preprocessing.py

# 2. Usar asistente GraphRAG
python scripts/graphrag_assistant.py

# Ahora el asistente puede usar estrategia de comunidades
```

**Pregunta de prueba:**
```
Pregunta: ¿Cuáles son los temas principales en el grafo?

GraphRAG (con pre-procesamiento):
→ Detecta que hay comunidades
→ Usa estrategia 5 (Comunidades + Resúmenes)
→ "Hay 3 temas principales:
   1. Prótesis: 45 normativas relacionadas con dispositivos protésicos
   2. Medicamentos: 32 normativas sobre prescripciones farmacéuticas
   3. Tratamientos: 28 normativas de procedimientos médicos"
```

## Mejores Prácticas

### 1. Ejecutar Después de Cambios al Grafo

```bash
# Cada vez que ingieras nuevos datos
python scripts/ingesta_datos.py
python scripts/depuracion_grafo.py
python scripts/graph_preprocessing.py  # ← Actualizar comunidades
```

### 2. Validar Comunidades Generadas

```cypher
// ¿Las comunidades tienen sentido?
MATCH (c:Community)
RETURN c.id, c.name, c.node_count
ORDER BY c.node_count DESC

// ¿Hay comunidades muy pequeñas/grandes?
MATCH (n)
WHERE n.community_id IS NOT NULL
WITH n.community_id as comm, count(n) as size
RETURN size, count(comm) as quantity
ORDER BY size
```

### 3. Documentar Qué Algoritmo Usaste

```bash
# Agregar metadata
echo "COMMUNITY_ALGORITHM=louvain" >> preprocessing_metadata.txt
echo "DATE=$(date)" >> preprocessing_metadata.txt
```

### 4. Experimentar con Diferentes Algoritmos

```bash
# Probar Louvain
COMMUNITY_ALGORITHM=louvain python scripts/graph_preprocessing.py

# Probar Label Propagation
COMMUNITY_ALGORITHM=labelPropagation python scripts/graph_preprocessing.py

# Comparar resultados en Neo4j
```

## Ejemplo Completo de Workflow

```bash
# ===============================================================
# WORKFLOW COMPLETO: Desde cero hasta GraphRAG con comunidades
# ===============================================================

# 1. Ingestar datos al grafo
python scripts/ingesta_datos.py

# 2. Depurar grafo
python scripts/depuracion_grafo.py

# 3. Crear BD vectorial
python scripts/vectorial_builder.py

# 4. PRE-PROCESAR GRAFO (este módulo)
python scripts/graph_preprocessing.py

# 5. Usar asistente GraphRAG con todas las estrategias
python scripts/graphrag_assistant.py

# Pregunta que usa comunidades:
# "¿Cuáles son los temas principales en las normativas?"
```

## Recursos Adicionales

- [Neo4j Graph Data Science Documentation](https://neo4j.com/docs/graph-data-science/)
- [Louvain Algorithm](https://neo4j.com/docs/graph-data-science/current/algorithms/louvain/)
- [PageRank Algorithm](https://neo4j.com/docs/graph-data-science/current/algorithms/page-rank/)
- [Community Detection Overview](https://neo4j.com/docs/graph-data-science/current/algorithms/community/)

## Soporte

Si encuentras problemas:

1. Revisa la sección de Troubleshooting
2. Verifica que GDS plugin esté instalado (`RETURN gds.version()`)
3. Revisa logs del script
4. Confirma que el grafo tiene datos (`MATCH (n) RETURN count(n)`)
5. Revisa configuración en `.env`
