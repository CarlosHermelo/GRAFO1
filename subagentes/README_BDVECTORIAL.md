# Constructor de Bases de Datos Vectoriales

Este módulo contiene el **Agente Constructor de BD Vectoriales** y el script `vectorial_builder.py` para crear bases de datos vectoriales optimizadas a partir de documentos PDF y texto.

## Descripción

El sistema convierte documentos en una base de datos vectorial mediante:
- **Análisis automático** del tipo de documento (normativo, técnico, análisis)
- **Chunking inteligente** adaptado al tipo de contenido
- **Embeddings de OpenAI** para representación vectorial
- **Almacenamiento en Chroma** (o Qdrant) para búsqueda semántica

## Componentes

### 1. Agente Constructor (`agente_bdvectorial.md`)
Agente experto que CREA scripts de construcción de BD vectoriales personalizados para tu proyecto.

### 2. Script de Vectorización (`scripts/vectorial_builder.py`)
Script ejecutable que procesa documentos y genera la base de datos vectorial.

### 3. Configuración (`scripts/.env`)
Archivo de variables de entorno para configurar el script.

## Instalación

### 1. Instalar Dependencias

```bash
cd scripts
pip install -r requirements.txt
```

Esto instalará:
- `langchain` - Framework para procesamiento de documentos
- `langchain-openai` - Integración con OpenAI
- `chromadb` - Base de datos vectorial local
- `pypdf` - Procesamiento de PDFs
- `tqdm` - Barras de progreso
- Y otras dependencias necesarias

### 2. Configurar Variables de Entorno

```bash
# Copiar el archivo de ejemplo
cp scripts/.env.vectorial.example scripts/.env

# Editar el archivo .env
nano scripts/.env
```

Configuración mínima requerida:
```bash
OPENAI_API_KEY=sk-tu-api-key-aqui
EMBEDDING_MODEL=text-embedding-3-small
VECTOR_DB_TYPE=chroma
VECTOR_DB_NAME=mi_proyecto_vectordb
SOURCE_PATH=contexto_dominio/
```

## Uso

### Opción 1: Ejecutar el Script Directamente

Si ya tienes el script `vectorial_builder.py` configurado:

```bash
python scripts/vectorial_builder.py
```

El script:
1. Validará la configuración
2. Cargará todos los PDFs y TXTs del directorio `SOURCE_PATH`
3. Detectará automáticamente el tipo de cada documento
4. Aplicará la estrategia de chunking óptima
5. Generará embeddings usando OpenAI
6. Creará la base de datos vectorial en `VECTOR_DB_PATH`

### Opción 2: Usar el Agente para Crear un Script Personalizado

Si necesitas un script personalizado para tu proyecto:

1. Invoca al agente (usando Claude Code u otro sistema)
2. El agente te preguntará por el tipo de BD vectorial (Chroma/Qdrant)
3. El agente leerá tu `objetivo_validado.md` para entender tu dominio
4. El agente generará un script optimizado para tu caso específico

## Estrategias de Chunking

El script detecta automáticamente el tipo de documento y aplica la estrategia óptima:

### Documentos Normativos
**Detecta:** ARTÍCULO, RESUELVE, DISPONE, LEY, NORMATIVA

**Estrategia:**
- Chunk size: 1000 tokens
- Overlap: 150 tokens
- Separadores: Artículos, secciones normativas
- Ideal para: Leyes, resoluciones, decretos, normativas PAMI

### Documentos Técnicos
**Detecta:** Procedimientos, especificaciones, listas numeradas

**Estrategia:**
- Chunk size: 700 tokens
- Overlap: 100 tokens
- Separadores: Encabezados, pasos numerados
- Ideal para: Manuales, protocolos, guías técnicas

### Documentos de Análisis
**Detecta:** Párrafos narrativos, estilo ensayo

**Estrategia:**
- Chunk size: 1200 tokens
- Overlap: 200 tokens
- Separadores: Párrafos, saltos de línea
- Ideal para: Reportes, análisis, estudios

## Estructura de Archivos Generados

Después de ejecutar el script, se crearán:

```
chroma_db/
└── mi_proyecto_vectordb/          # Base de datos vectorial
    ├── chroma.sqlite3              # Base de datos SQLite interna
    └── [archivos de índice]        # Índices vectoriales

chroma_db/
└── mi_proyecto_vectordb_metadata.json  # Metadata del proceso
```

### Contenido del archivo metadata:

```json
{
  "database_name": "mi_proyecto_vectordb",
  "database_type": "chroma",
  "embedding_model": "text-embedding-3-small",
  "total_chunks": 156,
  "total_documentos": 12,
  "estadisticas_por_tipo": {
    "normativo": {
      "count": 8,
      "chunks": 98
    },
    "tecnico": {
      "count": 3,
      "chunks": 42
    },
    "analisis": {
      "count": 1,
      "chunks": 16
    }
  },
  "fecha_creacion": "2024-12-17T15:30:00",
  ...
}
```

## Ejemplos de Uso

### Ejemplo 1: Proyecto de Prótesis PAMI

```bash
# .env
OPENAI_API_KEY=sk-abc123...
EMBEDDING_MODEL=text-embedding-3-small
VECTOR_DB_TYPE=chroma
VECTOR_DB_NAME=protesis_pami_vectordb
VECTOR_DB_PATH=./chroma_db/
SOURCE_PATH=contexto_dominio/
FILE_EXTENSIONS=.pdf,.txt
```

```bash
python scripts/vectorial_builder.py
```

Salida esperada:
```
======================================================================
CONSTRUCTOR DE BASE DE DATOS VECTORIAL
======================================================================

[INFO] Validando configuración...
  ✓ OpenAI API Key configurada
  ✓ Directorio de documentos: contexto_dominio/

[INFO] Buscando documentos en: contexto_dominio/
[INFO] Encontrados 8 archivos

Cargando archivos: 100%|████████████| 8/8 [00:03<00:00]
[SUCCESS] 8 documentos cargados exitosamente

[INFO] Analizando tipo de documentos y aplicando chunking...
Procesando documentos: 100%|████████| 8/8 [00:05<00:00]

======================================================================
ESTADÍSTICAS DE PROCESAMIENTO
======================================================================

[NORMATIVO] - Documentos normativos (leyes, resoluciones)
  - Documentos: 5
  - Chunks generados: 67
  - Chunk size: 1000 tokens
  - Overlap: 150 tokens

[TECNICO] - Documentos técnicos (manuales, especificaciones)
  - Documentos: 2
  - Chunks generados: 28
  - Chunk size: 700 tokens
  - Overlap: 100 tokens

[ANALISIS] - Documentos de análisis (reportes, estudios)
  - Documentos: 1
  - Chunks generados: 12
  - Chunk size: 1200 tokens
  - Overlap: 200 tokens

[TOTAL]
  - Documentos procesados: 8
  - Total de chunks: 107
======================================================================

[INFO] Generando embeddings y construyendo base de datos vectorial...
[INFO] Modelo de embeddings: text-embedding-3-small
[INFO] Total de chunks: 107
[INFO] Ubicación BD: chroma_db/protesis_pami_vectordb
[INFO] Generando embeddings... (esto puede tardar algunos minutos)
[SUCCESS] Base de datos vectorial creada exitosamente!

[INFO] Validando base de datos vectorial...
[SUCCESS] Validación exitosa: 3 documentos recuperados

======================================================================
✅ BASE DE DATOS VECTORIAL CREADA EXITOSAMENTE
======================================================================

[INFO] Ubicación: chroma_db/protesis_pami_vectordb
[INFO] Total de chunks vectorizados: 107
[INFO] Modelo de embeddings: text-embedding-3-small

[INFO] La base de datos está lista para ser utilizada en:
  - Sistemas RAG (Retrieval-Augmented Generation)
  - Búsquedas semánticas
  - Análisis de similitud de documentos
======================================================================
```

### Ejemplo 2: Solo Procesar PDFs Normativos

```bash
# .env - Configuración para solo PDFs con chunking manual
OPENAI_API_KEY=sk-abc123...
EMBEDDING_MODEL=text-embedding-3-small
VECTOR_DB_TYPE=chroma
VECTOR_DB_NAME=normativas_vectordb
SOURCE_PATH=/ruta/a/normativas/
FILE_EXTENSIONS=.pdf
CHUNK_SIZE=1000
CHUNK_OVERLAP=150
```

## Usar la BD Vectorial Creada

### Con LangChain (Python)

```python
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings

# Cargar la BD vectorial existente
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

vectorstore = Chroma(
    persist_directory="./chroma_db/protesis_pami_vectordb",
    embedding_function=embeddings,
    collection_name="protesis_pami_vectordb"
)

# Búsqueda semántica
query = "¿Qué normativas regulan las prótesis auditivas?"
results = vectorstore.similarity_search(query, k=5)

for doc in results:
    print(f"Archivo: {doc.metadata['filename']}")
    print(f"Tipo: {doc.metadata['tipo_documento']}")
    print(f"Contenido: {doc.page_content[:200]}...")
    print("-" * 50)
```

### RAG (Retrieval-Augmented Generation)

```python
from langchain_openai import ChatOpenAI
from langchain.chains import RetrievalQA

# Crear chain RAG
llm = ChatOpenAI(model="gpt-4", temperature=0)

qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    chain_type="stuff",
    retriever=vectorstore.as_retriever(search_kwargs={"k": 5})
)

# Hacer preguntas sobre los documentos
respuesta = qa_chain.run("¿Qué proveedores están autorizados para prótesis?")
print(respuesta)
```

## Configuración Avanzada

### Usar Qdrant en lugar de Chroma

```bash
# 1. Instalar cliente de Qdrant
pip install qdrant-client

# 2. Levantar servidor Qdrant con Docker
docker run -p 6333:6333 qdrant/qdrant

# 3. Configurar .env
VECTOR_DB_TYPE=qdrant
QDRANT_URL=http://localhost:6333
VECTOR_DB_NAME=mi_proyecto_vectordb
```

### Chunking Manual (Sobrescribir Auto-detección)

Si necesitas control total sobre el chunking:

```bash
# .env
CHUNK_SIZE=800        # Sobrescribe la detección automática
CHUNK_OVERLAP=100     # Sobrescribe la detección automática
```

Nota: Solo úsalo si sabes exactamente qué estás haciendo. La detección automática es generalmente óptima.

## Troubleshooting

### Error: "OPENAI_API_KEY no está configurada"

**Solución:**
```bash
# Verifica que .env existe
ls scripts/.env

# Verifica que tiene el API key
cat scripts/.env | grep OPENAI_API_KEY

# Si no existe, copia el ejemplo
cp scripts/.env.vectorial.example scripts/.env
nano scripts/.env  # Agrega tu API key
```

### Error: "Directorio de documentos no encontrado"

**Solución:**
```bash
# Verifica que el directorio existe
ls contexto_dominio/

# O ajusta la ruta en .env
SOURCE_PATH=/ruta/completa/a/documentos/
```

### Error: "Falta instalar dependencias"

**Solución:**
```bash
cd scripts
pip install -r requirements.txt
```

### La BD vectorial no recupera buenos resultados

**Posibles causas:**
1. **Chunks muy grandes o muy pequeños** - Ajusta `CHUNK_SIZE`
2. **Overlap insuficiente** - Aumenta `CHUNK_OVERLAP`
3. **Modelo de embeddings no adecuado** - Prueba `text-embedding-3-large`
4. **Documentos de mala calidad** - Limpia o mejora los PDFs fuente

## Costos de OpenAI

Usando `text-embedding-3-small`:
- **Costo:** $0.02 por 1M tokens
- **Ejemplo:** 100 páginas (~250K tokens) = $0.005 USD

Usando `text-embedding-3-large`:
- **Costo:** $0.13 por 1M tokens
- **Ejemplo:** 100 páginas (~250K tokens) = $0.0325 USD

**Recomendación:** Usa `text-embedding-3-small` para empezar. Solo migra a `large` si necesitas mayor precisión.

## Próximos Pasos

Una vez creada la BD vectorial, puedes:

1. **Integrarla con tu grafo de conocimiento** - Combinar búsqueda vectorial con consultas Cypher
2. **Crear un sistema RAG** - Responder preguntas basándote en los documentos
3. **Análisis de similitud** - Encontrar documentos relacionados
4. **Clustering** - Agrupar documentos por contenido semántico

## Recursos Adicionales

- [Documentación de LangChain](https://python.langchain.com/)
- [Documentación de ChromaDB](https://docs.trychroma.com/)
- [OpenAI Embeddings Guide](https://platform.openai.com/docs/guides/embeddings)
- [Qdrant Documentation](https://qdrant.tech/documentation/)

## Soporte

Si encuentras problemas:
1. Revisa la sección de Troubleshooting
2. Verifica los logs del script
3. Consulta el archivo `*_metadata.json` para entender qué se procesó
4. Revisa la configuración en `.env`
