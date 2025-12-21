# Módulo de Carga de CSV a Neo4j

## Descripción

Este módulo automatiza la carga de datos desde archivos CSV a Neo4j siguiendo un schema de grafo validado. Implementa carga batch optimizada, validación exhaustiva y genera reportes detallados del proceso.

## Características

- ✅ Carga batch optimizada con UNWIND para grandes volúmenes
- ✅ Validación de schema antes de la carga
- ✅ Creación automática de constraints e índices
- ✅ Manejo de valores NULL
- ✅ Progress logging en tiempo real
- ✅ Detección de nodos huérfanos
- ✅ Generación de reportes en JSON
- ✅ Idempotencia (puede ejecutarse múltiples veces)

## Arquitectura del Módulo

```
csv_neo4j_loader/
├── agente_carga_csv_neo4j.md      # Definición del agente
├── scripts/
│   ├── csv_neo4j_loader.py        # Script principal de carga
│   └── .env.csv_loader.example    # Configuración ejemplo
├── csv_data/                      # Directorio con archivos CSV
│   ├── products.csv
│   ├── suppliers.csv
│   └── ...
├── output/                        # Reportes y logs generados
│   └── load_report.json
└── README_CSV_LOADER.md           # Esta documentación
```

## Requisitos Previos

### 1. Software

- Python 3.8+
- Neo4j 5.x instalado y corriendo
- Acceso a instancia Neo4j (local o remota)

### 2. Dependencias Python

```bash
pip install -r requirements_csv.txt
```

Contenido de `requirements_csv.txt`:
```
neo4j>=5.0.0
pandas>=2.0.0
python-dotenv>=1.0.0
```

### 3. Schema Validado

Debes haber ejecutado previamente el **agente_schema_csv** para generar:
- `resultados/schema_csv_validado.json`

## Instalación

### Paso 1: Instalar Dependencias

```bash
cd scripts
pip install -r requirements_csv.txt
```

### Paso 2: Configurar Variables de Entorno

```bash
# Copiar archivo de configuración ejemplo
cp .env.csv_loader.example .env

# Editar .env con tus credenciales
nano .env
```

Configuración mínima requerida:
```bash
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=tu_password_real
CSV_DIR=../csv_data/
SCHEMA_PATH=../../resultados/schema_csv_validado.json
BATCH_SIZE=1000
OUTPUT_DIR=./output/
```

### Paso 3: Preparar Archivos CSV

Coloca tus archivos CSV en el directorio configurado (`CSV_DIR`). Los nombres de archivos deben coincidir con los definidos en el schema validado.

Estructura esperada de CSV:
```
csv_data/
├── products.csv       # Headers: product_id,name,price,category,supplier_id
├── suppliers.csv      # Headers: supplier_id,name,country
└── customers.csv      # Headers: customer_id,name,email
```

**Importante:**
- Primera fila debe contener headers
- Encoding UTF-8
- Separador: coma (,)

## Uso

### Ejecución Básica

```bash
cd scripts
python csv_neo4j_loader.py
```

### Salida Esperada

```
================================================================================
🚀 CARGA DE CSV A NEO4J
================================================================================

📋 PASO 1: Cargar schema validado
   Ruta: ../resultados/schema_csv_validado.json
   ✅ Schema cargado:
      - 3 tipos de nodos
      - 2 tipos de relaciones

🔒 PASO 2: Preparar Neo4j

📐 Creando constraints e índices...
   ✅ Constraint: Product (product_id)
   ✅ Constraint: Supplier (supplier_id)
   ✅ Índice: Product.name

📦 PASO 3: Cargar nodos desde CSVs

📥 Cargando nodos :Product desde products.csv
   📊 Total registros: 1,500
   🔄 Progreso: 66.7% (1,000/1,500)
   🔄 Progreso: 100.0% (1,500/1,500)
   ✅ Completado: 1,500 nodos :Product creados

📥 Cargando nodos :Supplier desde suppliers.csv
   📊 Total registros: 250
   🔄 Progreso: 100.0% (250/250)
   ✅ Completado: 250 nodos :Supplier creados

🔗 PASO 4: Cargar relaciones desde CSVs

🔗 Cargando relaciones :SUPPLIED_BY
   (Product)-[:SUPPLIED_BY]->(Supplier)
   📊 Total relaciones potenciales: 1,500
   🔄 Progreso: 100.0% (1,500/1,500)
   ✅ Completado: 1,500 relaciones creadas

✅ PASO 5: Validación post-carga

🔍 Validando carga...

   NODOS CARGADOS:
      :Product = 1,500 nodos
      :Supplier = 250 nodos
      :Customer = 800 nodos

   RELACIONES CARGADAS:
      :SUPPLIED_BY = 1,500 relaciones
      :PURCHASED = 3,200 relaciones

   NODOS HUÉRFANOS:
      ✅ No hay nodos huérfanos

================================================================================
✅ CARGA COMPLETADA
================================================================================

📊 ESTADÍSTICAS:
   ⏱️  Tiempo total: 12.45 segundos
   📦 Nodos creados: 2,550
   🔗 Relaciones creadas: 4,700

📁 Reporte guardado: output/load_report.json
================================================================================
```

## Estructura del Schema Validado

El script espera un schema con la siguiente estructura:

```json
{
  "metadata": {
    "generated_at": "2024-12-20T00:00:00",
    "objetivo": "...",
    "domain": "...",
    "source": "CSV files"
  },
  "schema": {
    "nodes": [
      {
        "label": "Product",
        "source_file": "products.csv",
        "key_columns": ["product_id"],
        "properties": ["name", "price", "category", "supplier_id"],
        "description": "Productos del catálogo"
      }
    ],
    "relationships": [
      {
        "type": "SUPPLIED_BY",
        "from_label": "Product",
        "to_label": "Supplier",
        "source_file": "products.csv",
        "from_column": "supplier_id",
        "to_column": "supplier_id",
        "properties": [],
        "description": "Producto suministrado por proveedor"
      }
    ]
  }
}
```

## Funcionalidades Detalladas

### 1. Carga Batch con UNWIND

El script usa `UNWIND` de Cypher para carga batch optimizada:

```cypher
UNWIND $batch AS row
MERGE (n:Product {product_id: row.product_id})
SET n += row
SET n.loaded_at = datetime(),
    n.loaded_from = $source_file
```

**Ventajas:**
- 10-100x más rápido que inserción individual
- Reduce overhead de red
- Transacciones optimizadas

### 2. Constraints e Índices

Se crean automáticamente antes de la carga:

**Constraints de Unicidad:**
```cypher
CREATE CONSTRAINT unique_product IF NOT EXISTS
FOR (n:Product)
REQUIRE (n.product_id) IS UNIQUE
```

**Índices de Búsqueda:**
```cypher
CREATE INDEX IF NOT EXISTS
FOR (n:Product)
ON (n.name)
```

### 3. Validación de CSV

Antes de cargar, se valida que:
- El archivo CSV existe
- Todas las columnas requeridas están presentes
- El archivo es legible

### 4. Manejo de Valores NULL

Los valores NULL de pandas se convierten a None para Neo4j:
```python
df = df.where(pd.notna(df), None)
```

### 5. Detección de Nodos Huérfanos

Post-carga, se detectan nodos sin relaciones:
```cypher
MATCH (n)
WHERE NOT (n)--()
RETURN labels(n)[0] as label, count(n) as count
```

## Reporte Generado

El script genera `output/load_report.json` con:

```json
{
  "metadata": {
    "timestamp": "2024-12-20T10:30:00",
    "duration_seconds": 12.45,
    "csv_dir": "./csv_data/",
    "schema_path": "../resultados/schema_csv_validado.json",
    "batch_size": 1000
  },
  "summary": {
    "total_nodes": 2550,
    "total_relationships": 4700,
    "nodes_by_type": {
      "Product": 1500,
      "Supplier": 250,
      "Customer": 800
    },
    "relationships_by_type": {
      "SUPPLIED_BY": 1500,
      "PURCHASED": 3200
    }
  },
  "validation": {
    "nodes": {...},
    "relationships": {...},
    "orphan_nodes": [],
    "total_nodes": 2550,
    "total_relationships": 4700
  }
}
```

## Optimización de Performance

### Tamaño de Batch

Ajustar `BATCH_SIZE` según:
- RAM disponible
- Tamaño de registros
- Latencia de red a Neo4j

Recomendaciones:
```bash
# Dataset pequeño (< 10K registros)
BATCH_SIZE=1000

# Dataset mediano (10K - 1M registros)
BATCH_SIZE=5000

# Dataset grande (> 1M registros)
BATCH_SIZE=10000
```

### Desactivar Constraints Durante Carga Inicial

Para carga inicial masiva (solo primera vez):

```cypher
// Antes de cargar
DROP CONSTRAINT unique_product;

// ... cargar datos ...

// Después de cargar
CREATE CONSTRAINT unique_product IF NOT EXISTS
FOR (n:Product)
REQUIRE (n.product_id) IS UNIQUE;
```

### Procesar CSVs Grandes por Chunks

Modificar script para leer CSV por chunks:
```python
for chunk in pd.read_csv(csv_path, chunksize=50000):
    # Procesar chunk
```

## Solución de Problemas

### Error: "Schema no encontrado"

**Causa:** No se ha generado el schema validado.

**Solución:**
```bash
# Ejecutar primero el agente de schema CSV
python scripts/schema_csv_designer.py
```

### Error: "Columnas faltantes"

**Causa:** El CSV no tiene todas las columnas definidas en el schema.

**Solución:**
1. Revisar el schema validado
2. Verificar headers del CSV
3. Actualizar CSV o regenerar schema

### Error: "Constraint violation"

**Causa:** Valores duplicados en columnas clave.

**Solución:**
1. Limpiar duplicados en CSV
2. Revisar definición de key_columns en schema

### Conexión a Neo4j Falla

**Causa:** Credenciales incorrectas o Neo4j no está corriendo.

**Solución:**
```bash
# Verificar que Neo4j esté corriendo
neo4j status

# Iniciar si es necesario
neo4j start

# Verificar credenciales en .env
```

### Nodos Huérfanos Detectados

**Causa:** Foreign keys que no coinciden con Primary keys existentes.

**Solución:**
1. Revisar integridad referencial en CSVs fuente
2. Verificar que nodos referenciados fueron cargados primero
3. Limpiar datos inconsistentes

## Validación Post-Carga

### Verificar Carga en Neo4j Browser

```cypher
// Ver todos los tipos de nodos
CALL db.labels()

// Ver todos los tipos de relaciones
CALL db.relationshipTypes()

// Contar nodos por tipo
MATCH (n:Product) RETURN count(n)

// Ver muestra de datos
MATCH (p:Product)-[:SUPPLIED_BY]->(s:Supplier)
RETURN p.name, s.name
LIMIT 10

// Verificar nodos huérfanos
MATCH (n)
WHERE NOT (n)--()
RETURN labels(n)[0] as label, count(n) as count
```

## Integración con Otros Módulos

### Flujo Completo desde CSV

1. **agente_objetivo_schema** → Define el objetivo del grafo
2. **agente_schema_csv** → Genera schema desde CSVs
3. **agente_carga_csv_neo4j** (este módulo) → Carga datos a Neo4j
4. **agente_depuracion_grafo** → Limpia y deduplica datos
5. **agente_graphrag_assistant** → Consultas inteligentes sobre el grafo

### Ejemplo de Uso Secuencial

```bash
# Paso 1: Definir objetivo
python scripts/objetivo_parser.py

# Paso 2: Generar schema desde CSVs
python scripts/schema_csv_designer.py

# Paso 3: Cargar datos a Neo4j
python scripts/csv_neo4j_loader.py

# Paso 4: (Opcional) Depurar grafo
python scripts/graph_deduplication.py

# Paso 5: Consultar con GraphRAG
python scripts/graphrag_assistant.py
```

## Mejores Prácticas

### 1. Backup Antes de Cargar

```bash
# Crear backup de Neo4j antes de carga masiva
neo4j-admin backup --backup-dir=/path/to/backup
```

### 2. Validar CSVs Antes de Cargar

```python
# Script de validación de CSVs
import pandas as pd

csv_path = "csv_data/products.csv"
df = pd.read_csv(csv_path)

# Verificar duplicados en PK
duplicates = df[df.duplicated(subset=['product_id'], keep=False)]
if not duplicates.empty:
    print(f"⚠️ Duplicados encontrados: {len(duplicates)}")
    print(duplicates)
```

### 3. Monitorear Memoria Durante Carga

```bash
# Monitorear uso de memoria de Neo4j
watch -n 1 'ps aux | grep neo4j'
```

### 4. Logs de Errores

El script maneja errores gracefully y continúa con el siguiente batch. Revisar logs para identificar problemas.

## Limitaciones Conocidas

1. **Encoding:** Solo soporta UTF-8
2. **Separador:** Solo coma (,)
3. **Quote character:** Estándar de CSV (")
4. **Tipos de datos:** Inferidos automáticamente por pandas

## Roadmap

### Mejoras Futuras

- [ ] Soporte para diferentes separadores (;, \t)
- [ ] Soporte para diferentes encodings
- [ ] Modo incremental (solo nuevos registros)
- [ ] Transformaciones de datos personalizadas
- [ ] Validación de tipos de datos estricta
- [ ] Progress bar con tqdm
- [ ] Rollback automático en caso de error
- [ ] Paralelización de carga

## Contribuir

Para reportar bugs o sugerir mejoras, crea un issue en el repositorio.

## Licencia

Este módulo es parte del proyecto de Grafos de Conocimiento para Prótesis.

---

**Documentación generada por:** agente_carga_csv_neo4j
**Versión:** 1.0
**Fecha:** 2024-12-20
