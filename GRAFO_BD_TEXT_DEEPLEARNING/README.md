# Grafo de Conocimiento: BD Text y Deep Learning

Este proyecto permite construir un grafo de conocimiento integrado que combina datos estructurados (CSV) y texto no estructurado (reseñas, normativas, documentos) para análisis avanzados.

## 📋 Requisitos Previos

### Variables de Entorno

Configura las siguientes variables de entorno antes de ejecutar el script:

- `OPENAI_API_KEY`: Tu clave de API de OpenAI
- `NEO4J_URI`: URI de conexión a Neo4j (ej: `bolt://localhost:7687`)
- `NEO4J_USER`: Usuario de Neo4j
- `NEO4J_PASSWORD`: Contraseña de Neo4j

### Dependencias

Instala las dependencias necesarias:

```bash
pip install openai neo4j pandas
```

## 🚀 Uso Rápido

### 1. Preparar la Estructura de Carpetas

Crea las siguientes carpetas y coloca tus archivos:

```
./import_data/
├── csv/          # Archivos CSV estructurados
└── text/         # Archivos .md o .txt (reseñas, normativas, etc.)
```

**Ejemplo:**
- `./import_data/csv/` con tus archivos CSV
- `./import_data/text/` con tus archivos `.md` o `.txt` (por ejemplo, reseñas o normativas convertidas)

### 2. Ejecutar el Script

```bash
python gen_constrain_schema.py
```

## 🎯 El Objetivo (user_goal): Elemento Crítico del Sistema

### ⚠️ Importancia Fundamental

**El objetivo (`user_goal`) es el elemento más importante del sistema multi-agente**, ya que actúa como la **Restricción Raíz** que guía todas las decisiones de la IA en cascada, desde la selección de datos hasta la estructura final del grafo.

**Si el objetivo es vago o incorrecto, el grafo construido será inútil**, ya que la IA priorizará datos irrelevantes.

### 🧭 Impacto del Objetivo en el Flujo de Construcción

El `user_goal` define el alcance y la relevancia en cada paso del proceso:

#### 1. 📂 Impacto en la Sugerencia de Archivos

El objetivo determina qué fuentes de datos son pertinentes para la construcción:

| Si el objetivo es... | El agente aprueba archivos como... | Y ignora archivos como... |
|---------------------|-----------------------------------|--------------------------|
| "Analizar Fallas y Reclamos" | `reviews.csv`, `calidad_producto.txt`, `product.csv` | `supplier_sales.csv`, `employee_data.pdf` |
| "Analizar Capacidad Logística" | `supplier_sales.csv`, `assemblies.csv` | `customer_feedback.md` |

#### 2. 🏗️ Impacto en el Esquema Estructurado

El objetivo le indica al **Agente Arquitecto** qué debe priorizar al diseñar el Grafo de Dominio (los CSVs):

- **Priorización de Propiedades**: Si el CSV `supplier_product.csv` tiene 20 columnas, y el objetivo es "Minimizar Riesgo de Suministro", el agente se asegurará de que las propiedades como `lead_time_days` y `minimum_order_quantity` se incluyan en el plan, mientras que podría descartar propiedades irrelevantes para ese fin.

- **Definición de Claves**: Asegura que las columnas utilizadas para las relaciones de clave foránea (ej. conectar `:Part` y `:Supplier` vía `supplier_id`) estén correctamente mapeadas, ya que son esenciales para las consultas finales.

#### 3. 🧠 Impacto en el Esquema No Estructurado

El objetivo es el filtro más importante para la fase de extracción del LLM:

- **Definición de Entidades**: El LLM solo extraerá aquello que sea útil para el objetivo.
  - Si el objetivo es "Analizar Experiencia del Usuario", el LLM extrae entidades como `:Comodidad` y `:Feature`.
  - Si el objetivo es "Analizar Riesgos Legales", el LLM extrae `:TérminoLegal` y `:Infracción`.

### 📋 Lineamientos para Definir el user_goal

Un objetivo efectivo debe ser lo suficientemente específico para guiar la IA, pero no tan restrictivo que limite el descubrimiento.

#### A. Lineamientos de Estructura

| Lineamiento | Qué Evitar (Malo) | Qué Usar (Bueno) |
|------------|-------------------|------------------|
| **Especificidad** | "Quiero arreglar mis problemas." | "Quiero identificar las 3 principales fallas de manufactura reportadas en reseñas de productos." |
| **Accionabilidad** | "Construir un grafo bonito." | "Poder hacer consultas que muestren proveedores de piezas con alta tasa de falla." |
| **Alcance** | "Analizar todo lo que tengo." | "Integrar datos de productos y proveedores para optimizar la cadena de suministro." |

#### B. Cómo se Refleja en el Grafo

El objetivo debe reflejarse en los patrones de consulta Cypher que esperas ejecutar al final:

**Ejemplo:**

- **Meta**: Saber si un producto tiene problemas de ensamblaje.
- **Goal (Agente)**: El agente de Intención debe definir que se requieren entidades `:Issue` y `:Assembly`.
- **Consulta Final (Prueba)**: 
  ```cypher
  MATCH (p:Product)-[:CONTAINS]->(a:Assembly)-[:TIENE_FALLAS]->(f:Falla) 
  RETURN p, f
  ```

**⚠️ Advertencia**: Si el objetivo se define mal (ej. solo pides el nodo `:Product`), la IA nunca extraerá las `:Fallas` necesarias para responder a la pregunta final.

## 📁 Tipos de Entrada

El script procesa dos tipos de archivos de entrada:

### Archivos Estructurados (CSV)

**Ubicación:** `./import_data/csv/*.csv`

Estos archivos se utilizan para extraer esquemas estructurados:
- Nodos
- Claves primarias y foráneas
- Relaciones basadas en IDs
- Joins entre tablas

### Archivos No Estructurados (Texto)

**Ubicación:** 
- `./import_data/text/*.txt`
- `./import_data/text/*.md`

Estos archivos se utilizan para extraer:
- Entidades mencionadas en el texto
- Tipos de hechos y relaciones
- Tripletas (sujeto-predicado-objeto)

### Comportamiento Flexible

El script es flexible y no requiere ambos tipos de archivos:

- ✅ **Solo CSV**: Si no hay archivos `.txt/.md`, solo procesará los CSV
- ✅ **Solo Texto**: Si no hay archivos `.csv`, solo procesará el texto
- ✅ **Ambos**: Si hay ambos tipos, combinará todo en un esquema unificado

## 🎯 Dominio Actual de los Prompts

### Objetivo de Usuario (user_goal)

El script está configurado con un objetivo genérico orientado a análisis de causa raíz:

```python
user_goal = (
    "Construir un grafo de conocimiento integrado que combine datos "
    "estructurados (CSV) y reseñas de texto para análisis de causa raíz."
)
```

Este objetivo refleja un caso de uso tipo **IKEA**: productos, proveedores, reseñas y análisis de calidad/supply chain.

### Prompts del LLM

- **Para CSV**: Hablan de "tablas CSV" y "buenas prácticas de diseño de grafo", sin un dominio específico, pero influenciados por el `user_goal`
- **Para Texto**: Hablan en general de entidades, hechos y tripletas, pero también referencian el objetivo del usuario que menciona reseñas y análisis de causa raíz

### Adaptación a Otros Dominios

Para adaptar el script a otros dominios (por ejemplo, **PAMI / prótesis / normativas**), necesitas:

1. **Cambiar el `user_goal`**: 
   ```python
   user_goal = "Grafo de conocimiento de normativas PAMI sobre prótesis..."
   ```

2. **Opcionalmente, ajustar los system prompts** para hablar de:
   - Resoluciones
   - Artículos
   - Prestaciones
   - Prótesis
   - Trámites

La estructura del script se mantiene igual, solo necesitas personalizar los prompts según tu dominio específico.

## 📝 Notas

- El esquema actual está orientado a un caso "tipo IKEA": productos, proveedores, reseñas y análisis de calidad
- Si necesitas reescribir todos los prompts para un dominio concreto (por ejemplo, "Provisión de Prótesis PAMI"), puedes hacerlo manteniendo la misma estructura del código
- **Recuerda**: El `user_goal` es la base de todo el sistema. Dedica tiempo a definirlo correctamente antes de ejecutar el script

PROMPT
#############################
#############################
--- INSTRUCCIONES: ARQUITECTO DE GRAFOS DE CONOCIMIENTO (USER INTENT) ---

**TU ROL:** Eres un Arquitecto experto en Grafos de Conocimiento (Knowledge Graphs) y tu única misión es ayudar al usuario a definir un objetivo técnico claro, accionable y bien delimitado para la construcción de su grafo. Este objetivo será la "Restricción Raíz" para todos los procesos subsiguientes de la IA.

**FASES DE INTERACCIÓN:**

1.  **Indagación (Fase Inicial):** Comienza preguntándole al usuario: "¿Qué objetivo específico buscas resolver con tu grafo de conocimiento? Por favor, sé lo más descriptivo posible."
2.  **Análisis y Crítica (Fase de Refinamiento):** Una vez que el usuario responda, debes evaluar el objetivo basándote en los siguientes **Lineamientos de Estructura**:

    * **CRITERIO 1: ESPECIFICIDAD.** El objetivo no debe ser vago. (Malo: "Arreglar los problemas del producto"). Debe ser detallado: ¿Qué producto? ¿Qué tipo de problema?
    * **CRITERIO 2: ACCIONABILIDAD.** El objetivo debe permitir una consulta Cypher al final. Debe responder a un "quién", "qué" o "dónde". (Malo: "Construir algo útil"). Debe implicar acción: "Identificar la cadena de suministro de las piezas que tienen alta tasa de fallas".
    * **CRITERIO 3: ALCANCE.** Debe delimitar el dominio (Logística, Calidad, Legal, Marketing).

3.  **Si el objetivo es vago:** Haz preguntas de aclaración. Pregunta por el dominio, las entidades clave que le interesan o las consultas que le gustaría hacer al final.

**INICIO DEL PROMPT:**

"Soy tu Arquitecto de Grafos de Conocimiento. Para iniciar el proceso de diseño, necesito que me definas el objetivo central de tu grafo.

**Antes de responder, por favor, lee nuestros lineamientos:** El objetivo que definas debe ser lo suficientemente específico para guiar la IA, ya que determinará qué archivos usaremos y qué entidades extraeremos.

---

**Ahora, por favor dime: ¿Cuál es el objetivo específico y accionable que buscas resolver con tu grafo de conocimiento?**"

---

**FORMATO DE SALIDA (FINAL):**

Una vez que el objetivo haya sido refinado y aprobado por el usuario, debes terminar la conversación con la siguiente etiqueta (y solo ese texto):

**OBJETIVO TÉCNICO FINAL APROBADO:** [Escribe aquí el objetivo final, detallado y robusto.]