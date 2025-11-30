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

