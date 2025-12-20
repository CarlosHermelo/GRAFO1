# Asistente GraphRAG - Consultas Híbridas (Vectorial + Grafo)

Este módulo contiene el **Asistente GraphRAG** que combina búsqueda semántica (BD vectorial) con búsqueda estructural (grafo Neo4j) para responder preguntas de forma inteligente y con evidencia trazable.

## ¿Qué es GraphRAG?

**GraphRAG** (Graph-Augmented Retrieval-Augmented Generation) es una técnica avanzada que combina:

1. **Búsqueda Semántica (Vectorial):** Encuentra información relevante aunque no coincidan palabras exactas
2. **Búsqueda Estructural (Grafo):** Conecta información, filtra por criterios y explica relaciones
3. **Generación con Evidencia:** Produce respuestas citando fuentes y mostrando trazabilidad

### Ventajas sobre RAG tradicional

| Característica | RAG Tradicional | GraphRAG |
|---------------|-----------------|----------|
| Búsqueda | Solo vectores | Vectores + Grafo |
| Conexiones | No explícitas | Relaciones claras |
| Filtrado | Limitado | Criterios estructurales |
| Explicabilidad | Baja | Alta (paths) |
| Trazabilidad | Chunks aislados | Contexto conectado |

## Componentes

### 1. Agente Constructor (`agente_graphrag_assistant.md`)
Agente experto que CREA el script del asistente GraphRAG personalizado.

### 2. Script del Asistente (`scripts/graphrag_assistant.py`)
Asistente ejecutable que responde preguntas combinando vectores + grafo.

### 3. Configuración (`scripts/.env`)
Variables de entorno para OpenAI, BD vectorial y Neo4j.

## Pre-requisitos

Antes de usar el asistente GraphRAG, debes tener:

✅ **BD Vectorial creada** (con `vectorial_builder.py`)
✅ **Grafo Neo4j poblado** (con `ingesta_datos.py` y `depuracion_grafo.py`)
✅ **OpenAI API Key** (para embeddings y LLM)
✅ **Neo4j ejecutándose** (local o remoto)

Opcional para estrategia de comunidades:
⚠️ **Comunidades pre-calculadas** en Neo4j (con `graph_preprocessing.py`)

## Instalación

### 1. Verificar Pre-requisitos

```bash
# Verificar que BD vectorial existe
ls chroma_db/protesis_pami_vectordb/

# Verificar que Neo4j está ejecutándose
# Abre http://localhost:7474 en tu navegador
# O ejecuta:
cypher-shell -u neo4j -p tu-password "MATCH (n) RETURN count(n);"
```

### 2. Instalar Dependencias

```bash
cd scripts
pip install -r requirements.txt
```

Instala:
- `langchain`, `langchain-openai`, `langchain-community`
- `chromadb` (para BD vectorial)
- `neo4j` (driver de Python)
- `tqdm` (barras de progreso)

### 3. Configurar Variables de Entorno

```bash
# Copiar archivo de ejemplo
cp scripts/.env.graphrag.example scripts/.env

# Editar y configurar
nano scripts/.env
```

Configuración mínima requerida:
```bash
OPENAI_API_KEY=sk-tu-api-key-aqui
LLM_MODEL=gpt-4
EMBEDDING_MODEL=text-embedding-3-small

VECTOR_DB_PATH=./chroma_db/
VECTOR_DB_NAME=protesis_pami_vectordb

NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=tu-password-neo4j
```

## Uso

### Modo Interactivo (Recomendado)

```bash
python scripts/graphrag_assistant.py
```

**Output:**
```
======================================================================
ASISTENTE GRAPHRAG - Consultas Híbridas (Vectorial + Grafo)
======================================================================

[INFO] Inicializando GraphRAG Assistant...
[SUCCESS] Asistente inicializado correctamente

Pregunta: ¿Qué proveedores están autorizados para prótesis auditivas?

[QUERY] ¿Qué proveedores están autorizados para prótesis auditivas?
[INTENT] filtrada
[VECTOR] 8 chunks encontrados
[ENTITIES] 2 entidades detectadas
[RESULTS] 5 resultados combinados

======================================================================
RESPUESTA
======================================================================
Los proveedores autorizados para prótesis auditivas son Proveedor A,
Proveedor B y Proveedor C [1][2]. Están certificados bajo la
Resolución 2024-2526 [3].

----------------------------------------------------------------------
FUENTES
----------------------------------------------------------------------
1. RESOL-2024-2526-INSSJP-DE#INSSJP.pdf (score: 0.892)
   ARTÍCULO 5: Los proveedores autorizados para prótesis...

2. RESOL-2024-2562-INSSJP-DE#INSSJP.pdf (score: 0.756)
   Se establece el listado de proveedores certificados...

----------------------------------------------------------------------
PATHS EN EL GRAFO
----------------------------------------------------------------------
  → Prestacion[Prótesis Auditivas] → requiere → Proveedor[A]
  → Normativa[2024-2526] → regula → Prestacion → requiere → Proveedor
======================================================================

Pregunta: salir

¡Hasta luego!
```

### Modo Programático

```python
from graphrag_assistant import GraphRAGAssistant

# Inicializar asistente
assistant = GraphRAGAssistant()

# Hacer pregunta
result = assistant.ask("¿Qué normativas regulan prótesis auditivas?")

# Acceder a resultados
print(result['answer'])
print(result['sources'])
print(result['graph_paths'])

# Cerrar conexiones
assistant.close()
```

## Las Estrategias de GraphRAG

El asistente implementa **5 estrategias básicas** (siempre incluidas) y **1 estrategia opcional** (Comunidades + Resúmenes).

**⚠️ IMPORTANTE:** La estrategia 5 (Comunidades + Resúmenes) es **OPCIONAL**. El agente preguntará si deseas incluirla al generar el script. Si la incluyes, necesitarás ejecutar primero el pre-procesamiento del grafo.

El asistente detecta automáticamente qué estrategia usar según el tipo de pregunta:

### 1️⃣ Semántica → Grafo (Exploratoria)

**Cuándo:** Preguntas vagas o exploratorias

**Ejemplo:**
```
Pregunta: "¿Qué información hay sobre prótesis auditivas?"

Proceso:
1. Vector search → encuentra chunks relevantes
2. Entity linking → mapea a nodos del grafo
3. Graph expansion → expande por vecinos
4. Combina evidencia textual + contexto estructural
```

### 2️⃣ Grafo → Semántica (Filtrada)

**Cuándo:** Preguntas con filtros específicos (tipo, fecha, estado)

**Ejemplo:**
```
Pregunta: "¿Qué proveedores de Tipo A están activos?"

Proceso:
1. Detecta filtros: tipo='A', estado='activo'
2. Cypher query filtra nodos en Neo4j
3. Para cada nodo, busca chunks vectoriales
4. Reranking semántico
```

### 3️⃣ Híbrido con Score Combinado

**Cuándo:** Ranking robusto en corpus grande

**Fórmula:**
```
score_final = 0.7 * similitud_vectorial
            + 0.2 * cantidad_evidencias
            + 0.1 * centralidad_nodo
```

### 4️⃣ Entity Linking + Metapaths

**Cuándo:** Preguntas de precisión

**Ejemplo:**
```
Pregunta: "¿Qué proveedores pueden suministrar la prestación X?"

Proceso:
1. Detecta entidad: Prestacion[X]
2. Ejecuta metapath: Prestacion → requiere → Proveedor
3. Retorna paths explicables
```

### 5️⃣ Comunidades + Resúmenes (OPCIONAL)

**⚠️ ESTRATEGIA OPCIONAL:** Esta estrategia NO está incluida por defecto. El agente preguntará si deseas incluirla al generar el script GraphRAG.

**Cuándo:** Preguntas de panorama ("temas principales", "resumen")

**Requisitos para habilitarla:**
1. Incluirla al generar el script (el agente preguntará)
2. Ejecutar pre-procesamiento del grafo con `graph_preprocessing.py`

**Ejemplo:**
```
Pregunta: "¿Cuáles son los temas principales en las normativas?"

Proceso:
1. Detecta comunidades (pre-calculadas)
2. Vector search sobre resúmenes de comunidades
3. Zoom en comunidad relevante
4. Retorna mapa + ejemplos
```

**Cómo habilitar esta estrategia:**

**Paso 1:** Al generar el script GraphRAG con el agente, responde "Sí" cuando pregunte:
```
¿Quieres incluir la estrategia de Comunidades + Resúmenes?
→ Selecciona: Sí
```

**Paso 2:** Genera el script de pre-procesamiento:
```bash
# El agente_preprocessing_grafo genera este script
# Sigue las instrucciones del agente para crearlo
```

**Paso 3:** Ejecuta el pre-procesamiento:
```bash
python scripts/graph_preprocessing.py
```

**Paso 4:** Ahora el asistente GraphRAG puede usar esta estrategia

### 6️⃣ Paths como Evidencia

**Cuándo:** Preguntas de "por qué" o "cómo"

**Ejemplo:**
```
Pregunta: "¿Por qué el proveedor X está autorizado para prestación Y?"

Proceso:
1. Detecta entidades: Proveedor[X], Prestacion[Y]
2. Encuentra paths entre ellos
3. Adjunta evidencia a cada paso del path
4. Retorna: "Porque Normativa N lo autoriza (ver Art. 5)"
```

## Ejemplos de Preguntas

### Preguntas Exploratorias (Estrategia 1)
```
- ¿Qué información hay sobre prótesis auditivas?
- Cuéntame sobre las normativas PAMI
- ¿Qué tipos de prestaciones existen?
```

### Preguntas Filtradas (Estrategia 2)
```
- ¿Qué proveedores de Tipo A están activos?
- Normativas del 2024 sobre prótesis
- Prestaciones con precio menor a $10000
```

### Preguntas Explicables (Estrategia 6)
```
- ¿Por qué el proveedor X está autorizado?
- ¿Cómo se relaciona la normativa Y con la prestación Z?
- Explica la conexión entre el artículo 5 y los proveedores
```

### Preguntas de Síntesis (Estrategia 5)
```
- ¿Cuáles son los temas principales en las normativas?
- Dame un panorama general de las prestaciones
- Resumen de los proveedores por categoría
```

## Configuración Avanzada

### Ajustar Pesos del Ranking Híbrido

En `.env`:
```bash
SEMANTIC_WEIGHT=0.7  # Mayor peso a similitud semántica
GRAPH_WEIGHT=0.3     # Menor peso a señales del grafo

# Para priorizar grafo:
SEMANTIC_WEIGHT=0.4
GRAPH_WEIGHT=0.6
```

### Ajustar Top-K Resultados

```bash
TOP_K_VECTORS=10  # Cantidad de chunks a recuperar
TOP_K_GRAPH=10    # Cantidad de nodos a recuperar
MAX_PATH_LENGTH=5 # Longitud máxima de paths
```

### Forzar Estrategia Específica

```bash
GRAPHRAG_STRATEGY=semantic_first  # Siempre vectores primero
# Opciones: auto | semantic_first | graph_first | hybrid
```

## Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────────────┐
│                    GraphRAG Assistant                        │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐         ┌──────────────┐                  │
│  │   Pregunta   │────────▶│   Detectar   │                  │
│  │  del Usuario │         │  Intención   │                  │
│  └──────────────┘         └──────┬───────┘                  │
│                                   │                          │
│         ┌─────────────────────────┼─────────────────────┐   │
│         │                         ▼                      │   │
│    ┌────▼─────┐            ┌────────────┐         ┌─────▼───┐
│    │  Vector  │            │  Hybrid    │         │  Graph  │
│    │  Search  │            │  Ranking   │         │ Search  │
│    └────┬─────┘            └─────┬──────┘         └─────┬───┘
│         │                        │                      │   │
│         │                        ▼                      │   │
│         │                  ┌──────────┐                 │   │
│         └─────────────────▶│  Entity  │◀────────────────┘   │
│                            │ Linking  │                     │
│                            └────┬─────┘                     │
│                                 │                           │
│                                 ▼                           │
│                          ┌─────────────┐                    │
│                          │   Generar   │                    │
│                          │  Respuesta  │                    │
│                          └─────────────┘                    │
│                                                              │
├──────────────────────────────────────────────────────────────┤
│                        Fuentes de Datos                      │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────────┐              ┌──────────────────┐      │
│  │  BD Vectorial   │              │   Grafo Neo4j    │      │
│  │   (Chroma)      │              │                  │      │
│  │                 │              │  ┌────┐  ┌────┐  │      │
│  │  [Embeddings]   │              │  │ N1 │──│ N2 │  │      │
│  │  [Chunks]       │              │  └─┬──┘  └──┬─┘  │      │
│  │  [Metadata]     │              │    │       │     │      │
│  │                 │              │  ┌─▼──┐  ┌─▼──┐  │      │
│  └─────────────────┘              │  │ N3 │──│ N4 │  │      │
│                                   │  └────┘  └────┘  │      │
│                                   └──────────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

## Troubleshooting

### Error: "BD vectorial no encontrada"

**Causa:** No existe la base de datos vectorial

**Solución:**
```bash
# Crear la BD vectorial primero
python scripts/vectorial_builder.py
```

### Error: "No se pudo conectar a Neo4j"

**Causa:** Neo4j no está ejecutándose o credenciales incorrectas

**Solución:**
```bash
# Verificar que Neo4j esté corriendo
# Opción 1: Neo4j Desktop - iniciar base de datos
# Opción 2: Docker
docker run -p 7474:7474 -p 7687:7687 neo4j

# Verificar credenciales en .env
NEO4J_PASSWORD=tu-password-correcto
```

### Error: "OPENAI_API_KEY no configurada"

**Solución:**
```bash
# Editar .env y agregar API key
nano scripts/.env
# Agregar: OPENAI_API_KEY=sk-...
```

### Warning: "No hay comunidades pre-calculadas"

**Causa:** Intentas usar estrategia de comunidades sin pre-procesamiento

**Solución:**
```bash
# Opción 1: Ejecutar pre-procesamiento (cuando esté disponible)
python scripts/graph_preprocessing.py

# Opción 2: El asistente automáticamente usa estrategia alternativa
# No es crítico, solo limita la estrategia 5
```

### Respuestas vacías o poco relevantes

**Posibles causas y soluciones:**

1. **BD vectorial vacía o de mala calidad**
   ```bash
   # Revisar metadata
   cat chroma_db/protesis_pami_vectordb_metadata.json
   ```

2. **Grafo Neo4j vacío**
   ```cypher
   // En Neo4j Browser
   MATCH (n) RETURN count(n);
   ```

3. **Embeddings diferentes entre construcción y consulta**
   ```bash
   # Verificar que EMBEDDING_MODEL sea el mismo en ambos .env
   # .env (vectorial_builder)
   # .env (graphrag_assistant)
   ```

## Costos de OpenAI

### Por Consulta

Cada pregunta consume:

**Embeddings:**
- Query embedding: ~50 tokens
- Costo: $0.000001 USD (con text-embedding-3-small)

**LLM (GPT-4):**
- Prompt: ~1000-2000 tokens (contexto + instrucciones)
- Respuesta: ~200-500 tokens
- Costo: ~$0.03-0.08 USD por consulta

**Total estimado:** $0.03-0.08 USD por pregunta con GPT-4

### Reducir Costos

```bash
# Usar GPT-3.5-turbo en lugar de GPT-4
LLM_MODEL=gpt-3.5-turbo
# Costo: ~$0.002-0.005 USD por pregunta

# Reducir contexto
TOP_K_VECTORS=5
TOP_K_GRAPH=5
```

## Integración con Otros Sistemas

### Usar en API REST

```python
from flask import Flask, request, jsonify
from graphrag_assistant import GraphRAGAssistant

app = Flask(__name__)
assistant = GraphRAGAssistant()

@app.route('/ask', methods=['POST'])
def ask():
    query = request.json.get('query')
    result = assistant.ask(query)
    return jsonify(result)

if __name__ == '__main__':
    app.run(port=5000)
```

### Usar en Chatbot

```python
import streamlit as st
from graphrag_assistant import GraphRAGAssistant

st.title("Asistente GraphRAG")

if 'assistant' not in st.session_state:
    st.session_state.assistant = GraphRAGAssistant()

query = st.text_input("Haz una pregunta:")

if query:
    result = st.session_state.assistant.ask(query)
    st.write("**Respuesta:**", result['answer'])

    with st.expander("Ver fuentes"):
        for source in result['sources']:
            st.write(f"- {source['filename']}")
```

## Comparación de Estrategias

| Estrategia | Velocidad | Precisión | Explicabilidad | Uso Típico |
|-----------|-----------|-----------|----------------|------------|
| 1. Semántica→Grafo | ⚡⚡⚡ | ⭐⭐⭐ | ⭐⭐⭐ | Exploración |
| 2. Grafo→Semántica | ⚡⚡ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | Filtros claros |
| 3. Híbrido | ⚡⚡ | ⭐⭐⭐⭐ | ⭐⭐⭐ | Corpus grande |
| 4. Metapaths | ⚡⚡⚡ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Precisión |
| 5. Comunidades | ⚡ | ⭐⭐⭐ | ⭐⭐⭐⭐ | Panorama |
| 6. Paths | ⚡⚡ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Justificación |

## Mejores Prácticas

### 1. Calidad de Datos
- Asegúrate de que la BD vectorial tenga chunks de buena calidad
- Verifica que el grafo esté bien depurado
- Mantén el schema actualizado

### 2. Formulación de Preguntas
- **Buenas:** Específicas, claras, con contexto
  - "¿Qué proveedores de Tipo A están autorizados para prótesis auditivas?"
- **Malas:** Vagas, ambiguas
  - "Dime algo"

### 3. Iteración
- Refina la pregunta si la respuesta no es satisfactoria
- Usa diferentes formulaciones
- Aprovecha las sugerencias del asistente

### 4. Validación
- Siempre revisa las fuentes citadas
- Verifica los paths del grafo
- Confirma contra documentación original

## Próximos Pasos

Una vez que tengas el asistente funcionando:

1. **Evaluar calidad** - Prueba con conjunto de preguntas de referencia
2. **Ajustar parámetros** - Optimiza pesos y top-k según resultados
3. **Calcular comunidades** - Para habilitar estrategia 5
4. **Integrar en aplicación** - API, chatbot, interfaz web
5. **Monitorear costos** - Llevar registro de consumo de OpenAI

## Recursos Adicionales

- [GraphRAG de Microsoft](https://microsoft.github.io/graphrag/)
- [Neo4j Graph Data Science](https://neo4j.com/docs/graph-data-science/)
- [LangChain Documentation](https://python.langchain.com/)
- [OpenAI API Reference](https://platform.openai.com/docs/)

## Soporte

Si encuentras problemas:

1. Revisa la sección de Troubleshooting
2. Verifica logs del script (activa modo verbose si es necesario)
3. Confirma que todos los pre-requisitos estén cumplidos
4. Revisa la configuración en `.env`
