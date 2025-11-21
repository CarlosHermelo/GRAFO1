# Generación de Grafo a partir de Documentos

Este proyecto genera un grafo de conocimiento en Neo4j a partir de documentos de texto, utilizando inteligencia artificial para extraer entidades y relaciones.

## Flujo de Trabajo

```bash
python gen_schema_txt.py # genera schema a partir de txt
python gen_subir_schma_a_neo.py # crea el schema en neo4j 
python gen_query.py # consulta sobre los documentos
```

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

El script realiza dos fases:

1. **FASE 1: Descubrimiento del Esquema Maestro**
   - Analiza todos los archivos `.txt` para identificar tipos de nodos y relaciones
   - Genera un esquema unificado con todos los labels y tipos de relaciones encontrados

2. **FASE 2: Extracción de Hechos**
   - Extrae instancias específicas (nodos y relaciones) de cada documento
   - Utiliza el esquema maestro para mantener consistencia

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

