# Generación de Grafo a partir de Documentos

Este proyecto genera un grafo de conocimiento en Neo4j a partir de documentos de texto, utilizando inteligencia artificial para extraer entidades y relaciones.

## Flujo de Trabajo

###
Path de proyecto 

```bash
C:\Users\u14527001\Downloads\grafo_protesis
C:\Users\u14527001\Downloads\grafo_protesis\curso_1

Documentos sobre guia medica
https://docs.google.com/document/d/1lZvpg09X22gaiHxPvaFnQtWKVvZ8sBRMbjXqYBbmmRM/edit?tab=t.0
```
###
curso_1 

```bash
python gen_schema_txt.py # genera schema input: *.txt -- output: grafo_generado.cypher
python gen_subir_schma_a_neo.py # crea el schema en neo4j ,input: grafo_generado.cypher
python gen_query.py # consulta sobre los documentos
python gen_borrar_schema.py # borra todo el schema de NEO4J 
python gen_carga_bdv   # toma los archivos txt y los sube a Chroma (.env)
python gen_query_full.py # consulta  GRAPH Y RAG
```

```bash
El script gen_schema_txt.py usa variable entorno .env donde CARPETA_TXT= toma la carpeta donde estan:

-todos los archivos *txt
-goal.config  donde pongo el objetivo de generador 
-labels.config  pongo los well-know (posibles entidades )
```
### El output del script gen_schema_txt.py esta en "grafo_generado.cypher"


En la carpeta RESO hay archivos reso con extencion txto
En la carpeta DIGESTO hay archivo reso con extencion .pdf 
---

## 📄 gen_schema_txt.py

**Script que crea un schema de grafo listo para subir a la BD Neo4j**

### Uso

```bash
python gen_schema_txt.py
```

### Parámetros de Entrada

- **Archivos de entrada:** Todos los archivos `*.txt` que estén en el mismo directorio son levantados automáticamente para convertir a schema.
- **⚠️ IMPORTANTE:** Verificar que la variable `FOLDER_PATH` en el script apunte al directorio correcto:
  ```python
  FOLDER_PATH = r"C:\Users\u14527001\Downloads\grafo_protesis\curso_1"
  ```

### Funcionamiento

¡Absolutamente\! Me alegra que la estructura del script te sea útil.

A continuación, repito los cinco puntos clave del script, pero agregando un **ejemplo práctico** de lo que significa cada característica en el contexto de tu grafo de resoluciones:

-----

## ✨ Características Clave del Script y Ejemplos Prácticos

### 1\. Estrategia Agéntica de 2 Fases: Descubrimiento (Ontología) + Extracción (Hechos)

  * **Significado:** En lugar de intentar extraer todo de golpe, el script primero define el "vocabulario" del grafo leyendo todos los documentos (Fase 1) y luego usa ese vocabulario unificado como una plantilla estricta para la extracción de datos (Fase 2).
  * **Ejemplo Práctico:**
      * **Fase 1 (Ontología):** Lee los 4 archivos y determina que las relaciones importantes son `DEROGA`, `MODIFICA` y `EMITE`.
      * **Fase 2 (Extracción):** Al leer el texto que dice "El Director Ejecutivo **resuelve anular** la Resolución 123", el Extractor *no inventa* una relación `ANULA`, sino que la clasifica bajo la relación previamente aprobada: **`DEROGA`**.

### 2\. Contexto de Negocio: `USER_GOAL` y `WELL_KNOWN_LABELS`

  * **Significado:** Se le proporciona al modelo el objetivo del negocio y un conjunto de etiquetas aprobadas, lo que guía al LLM a priorizar la información relevante para la **evaluación normativa**.
  * **Ejemplo Práctico:**
      * **Input:** El `USER_GOAL` indica que solo son importantes las relaciones jurídicas.
      * **Resultado:** El script ignora la extracción de entidades irrelevantes como `MesaDeEntradas` o `DomicilioFiscal`, pero garantiza que la entidad `Programa` (una `WELL_KNOWN_LABEL`) sea correctamente identificada cada vez, aunque el texto la llame de diferentes maneras.

### 3\. Grafo Léxico (Trazabilidad): `:Documento` - `[:MENCIONA]` -\> `:Entidad`

  * **Significado:** Es el "Mapa del Origen de la Información". Cada entidad extraída (nodo) está conectada a la fuente de texto (`:Documento`) donde fue mencionada.
  * **Ejemplo Práctico:**
      * Si buscas la Ley **19.032**, el grafo te mostrará: `(Ley:19032)` **\<-[:MENCIONA]-** `(Documento:RESOL_2024_1967)`.
      * Esto permite validar rápidamente si la Ley fue citada en otros documentos cargados, fundamental para una auditoría o análisis de vigencia.

### 4\. Optimización: Genera `CONSTRAINTS` de Unicidad

  * **Significado:** Los *constraints* son comandos que se ejecutan una sola vez al configurar la base de datos Neo4j. Garantizan que las IDs de los nodos sean únicas, impidiendo la duplicación de datos.
  * **Ejemplo Práctico:**
      * El script genera: `CREATE CONSTRAINT constraint_Resolucion_id IF NOT EXISTS FOR (n:Resolucion) REQUIRE n.id IS UNIQUE;`
      * Si intentas cargar dos nodos `:Resolucion` con el mismo ID (`"RESOL_2024_100"`), Neo4j arrojará un error, asegurando que cada norma exista solo una vez, manteniendo la integridad de la base de datos.

### 5\. Visualización: Muestra el "Esquema Abstracto"

  * **Significado:** Antes de imprimir el Cypher final, el script resume la estructura *única* de todas las tripletas que encontró en los documentos.
  * **Ejemplo Práctico:**
      * El output te mostrará un resumen como:
        ```
        (Resolucion) --[DEROGA]--> (Resolucion)
        (Organismo) --[EMITE]--> (Resolucion)
        (Ley) --[MODIFICA]--> (Ley)
        ```
      * Esto te permite validar, de un solo vistazo, que el LLM ha entendido las relaciones clave antes de cargar los miles de comandos de datos en el grafo.
### Salida

El script genera en consola un **SCRIPT CYPHER** completo con el siguiente formato:

```
==================================================
💻 SCRIPT CYPHER GENERADO (Para Neo4j)
==================================================

// --- CREACIÓN DE NODOS (MERGE) ---
MERGE (n:Normativa {id: "RESOL_2024_2076_INSSJP_DE_INSSJP"}) ON CREATE SET n.nombre = "Resolución";
MERGE (n:Normativa {id: "EX_2020_15409689_INSSJP_USA_INSSJP"}) ON CREATE SET n.nombre = "Reglamento para Solicitar y Recibir Información Pública del Instituto";
MERGE (n:Ley {id: "LEY_19_032"}) ON CREATE SET n.nombre = "Ley 19.032";
...

// --- CREACIÓN DE RELACIONES (MATCH/MERGE) ---
MATCH (a:Normativa {id: "RESOL_2024_2076_INSSJP_DE_INSSJP"}), (b:Anexo {id: "ANEXO_I_REGlAMENTO_PARA_SOLICITAR_Y_RECIBIR_INFORMACION_PUBLICA_DEL_INST"}) MERGE (a)-[:CONTIENE]->(b);
MATCH (a:Normativa {id: "RESOL_2024_2076_INSSJP_DE_INSSJP"}), (b:Anexo {id: "ANEXO_II_FORMULARIO_DE_SOLICITUD_DE_INFORMACION_PUBLICA_DEL_INSSJP"}) MERGE (a)-[:CONTIENE]->(b);
...
```

**Nota:** Copia este script completo para usarlo en el siguiente paso.

---

## 📤 gen_subir_schma_a_neo.py

**Sube el schema generado a Neo4j**

### Uso

```bash
python gen_subir_schma_a_neo.py
```

### ⚠️ Configuración Requerida

**IMPORTANTE:** Antes de ejecutar este script, debes:

1. **Copiar el script Cypher generado** por `gen_schema_txt.py`
2. **Pegarlo en la variable `CYPHER_SCRIPT`** dentro de este archivo (línea 19)
3. Verificar las credenciales de Neo4j en el archivo `.env`:
   - `NEO4J_URI`
   - `NEO4J_USER`
   - `NEO4J_PASSWORD`

### Posibles Errores

- **Es posible que ocurran errores** si hay problemas en el texto del schema generado por el script anterior
- El script mostrará qué bloque específico causó el error para facilitar la depuración

### Funcionamiento

El script:
1. Se conecta a la base de datos Neo4j usando las credenciales del `.env`
2. Ejecuta cada bloque del script Cypher de forma secuencial
3. Muestra errores si algún bloque falla

---

## 🔍 gen_query.py

**Genera consultas en lenguaje natural sobre el grafo**

### Uso

```bash
python gen_query.py
```

### Funcionamiento

Al ejecutarse:

1. **Levanta automáticamente el schema de Neo4j** consultando la base de datos
2. **Inicia un chat interactivo** donde puedes hacer preguntas en lenguaje natural
3. **Convierte tus preguntas a Cypher** usando GPT-4o
4. **Ejecuta la consulta** en Neo4j
5. **Genera una respuesta natural** basada en los resultados

### Ejemplo de Uso

```
--- 🤖 Chat con tu Grafo (Escribe 'salir' para terminar) ---

Pregunta: ¿Qué resoluciones derogan a otras resoluciones?
  ↳ Generando consulta...
  [CYPHER]: MATCH (a:Resolucion)-[:DEROGA]->(b:Resolucion) RETURN a.nombre, b.nombre
  ↳ Se encontraron 3 registros.
  ↳ Analizando respuesta...

RESPUESTA: Se encontraron 3 casos donde una resolución deroga a otra...
```

### Para Salir

Escribe `salir` o `exit` para terminar la sesión.

---

## 📋 Requisitos Previos

1. **Variables de entorno** (archivo `.env`):
   ```
   OPENAI_API_KEY=tu_clave_api
   NEO4J_URI=neo4j+s://tu_instancia.neo4j.io
   NEO4J_USER=neo4j
   NEO4J_PASSWORD=tu_contraseña
   ```

2. **Dependencias Python**:
   - `openai`
   - `neo4j`
   - `pydantic`
   - `python-dotenv`

3. **Archivos de entrada**: Archivos `.txt` en el directorio especificado en `FOLDER_PATH`

---

## 🔄 Flujo Completo

```
Documentos .txt
      ↓
[gen_schema_txt.py] → Genera Script Cypher
      ↓
[gen_subir_schma_a_neo.py] → Sube a Neo4j
      ↓
[gen_query.py] → Consulta el grafo
```

---

## 📝 Notas

- Los IDs de los nodos se generan en formato `SNAKE_CASE_MAYUSCULA`
- El script utiliza `MERGE` para evitar duplicados en la base de datos
- El consumo de tokens de OpenAI se muestra al final de la ejecución de `gen_schema_txt.py`

