# Cargador de CSVs a Neo4j

Este módulo contiene el **Agente Cargador de CSV a Neo4j** que crea un script para cargar archivos CSV en Neo4j siguiendo un schema de grafo previamente validado.

## ¿Para Qué Sirve?

Este módulo toma el schema validado generado por `agente_schema_csv` y carga los datos desde los archivos CSV a una base de datos Neo4j, creando nodos y relaciones según la estructura definida.

### Flujo Completo de CSV a Grafo

```
1. agente_objetivo_schema
   ↓ Define objetivo y dominio

2. agente_schema_csv
   ↓ Diseña schema desde CSVs
   ↓ Genera: schema_csv_validado.json

3. agente_carga_csv_neo4j  ← ESTE MÓDULO
   ↓ Carga CSVs a Neo4j según schema

4. Validación en Neo4j
   → Consultas Cypher para verificar datos
```

## Componentes

### 1. Agente Constructor (`agente_carga_csv_neo4j.md`)
Agente experto que CREA el script para cargar CSVs a Neo4j.

### 2. Script Cargador (`scripts/csv_to_neo4j.py`)
Script ejecutable que lee el schema validado y carga los datos a Neo4j.

### 3. Configuración (`scripts/.env`)
Variables de entorno incluyendo credenciales de Neo4j y rutas.

## Pre-requisitos

### 1. Schema Validado

Debe existir el archivo generado por `agente_schema_csv`:
```bash
resultados/schema_csv_validado.json
```

Si no existe, ejecutar primero:
```bash
python scripts/schema_csv_designer.py
```

### 2. Neo4j en Ejecución

Neo4j debe estar corriendo y accesible:

**Opción A: Neo4j Desktop**
- Descarga: https://neo4j.com/download/
- Crear una base de datos local
- Iniciar la base de datos
- Anotar: URI, usuario, contraseña

**Opción B: Neo4j Docker**
```bash
docker run \
  --name neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/your-password \
  -v $HOME/neo4j/data:/data \
  neo4j:latest
```

**Opción C: Neo4j Aura (Cloud)**
- https://neo4j.com/cloud/aura/
- Crear instancia gratuita
- Anotar credenciales

### 3. Archivos CSV Disponibles

Los CSVs deben estar en la subcarpeta configurada:
```
proyecto/
├── csv_data/              ← CSVs aquí
│   ├── products.csv
│   ├── suppliers.csv
│   ├── customers.csv
│   └── orders.csv
├── scripts/
│   ├── csv_to_neo4j.py
│   └── .env
└── resultados/
    └── schema_csv_validado.json
```

### 4. Configuración de Neo4j Import

**IMPORTANTE:** Neo4j requiere que los CSVs estén en su directorio `import/` para usar LOAD CSV.

**Opción A: Copiar CSVs a import/** (Recomendado)

El script puede copiar automáticamente los CSVs:
```bash
# Neo4j Desktop: Ubicación típica del import/
# macOS: ~/Library/Application Support/Neo4j Desktop/Application/relate-data/dbmss/dbms-xxx/import/
# Windows: C:\Users\<user>\AppData\Local\Neo4j\Relate\Data\dbmss\dbms-xxx\import\
# Linux: ~/.config/Neo4j Desktop/Application/relate-data/dbmss/dbms-xxx/import/
```

**Opción B: Configurar dbms.directories.import**

Editar `neo4j.conf`:
```
dbms.directories.import=/ruta/a/tu/csv_data
```

**Opción C: Usar Python Driver con Batch**

El script también soporta carga batch sin LOAD CSV (más lento pero no requiere import/).

## Instalación

### 1. Dependencias ya Instaladas

Las dependencias ya fueron instaladas en pasos anteriores:
```bash
cd scripts
pip install -r requirements.txt
```

Librerías necesarias:
- `neo4j` - Driver oficial de Neo4j
- `pandas` - Lectura de CSVs
- `python-dotenv` - Configuración

### 2. Configurar Variables de Entorno

```bash
# Copiar archivo de ejemplo
cp scripts/.env.carga_csv.example scripts/.env

# Editar configuración
nano scripts/.env
```

**Configuración mínima:**
```bash
# Credenciales de Neo4j
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=tu-password-aqui

# Subcarpeta con CSVs
CSV_DIR=./csv_data/

# Schema validado
SCHEMA_PATH=resultados/schema_csv_validado.json
```

### 3. Verificar Conexión a Neo4j

```bash
# Probar conexión
python -c "from neo4j import GraphDatabase; driver = GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j', 'tu-password')); driver.verify_connectivity(); print('Conexión exitosa')"
```

## Uso

### Ejecución Básica

```bash
python scripts/csv_to_neo4j.py
```

**Output esperado:**

```
======================================================================
CARGADOR DE CSVs A NEO4J
======================================================================

📋 PASO 1: Cargar schema validado
  ✓ Schema: resultados/schema_csv_validado.json
  ✓ Nodos a cargar: 3
  ✓ Relaciones a cargar: 2

🔌 PASO 2: Conectar a Neo4j
  ✓ Conectado a: bolt://localhost:7687
  ✓ Verificando conexión... OK

📁 PASO 3: Preparar CSVs para import
  ℹ Método de carga: LOAD CSV
  ✓ Copiando CSVs a import/
  ✓ products.csv → /path/to/neo4j/import/
  ✓ suppliers.csv → /path/to/neo4j/import/
  ✓ customers.csv → /path/to/neo4j/import/

🔒 PASO 4: Crear constraints e índices
  ✓ Constraint: Product.product_id
  ✓ Constraint: Supplier.supplier_id
  ✓ Constraint: Customer.customer_id

📦 PASO 5: Cargar nodos

[INFO] Cargando nodos: Product
  Archivo: products.csv
  Filas en CSV: 150
  ✓ Nodos creados: 150
  ✓ Propiedades establecidas: 600

[INFO] Cargando nodos: Supplier
  Archivo: suppliers.csv
  Filas en CSV: 25
  ✓ Nodos creados: 25
  ✓ Propiedades establecidas: 100

[INFO] Cargando nodos: Customer
  Archivo: customers.csv
  Filas en CSV: 80
  ✓ Nodos creados: 80
  ✓ Propiedades establecidas: 320

🔗 PASO 6: Cargar relaciones

[INFO] Cargando relaciones: SUPPLIED_BY
  Product → Supplier
  ✓ Relaciones creadas: 150

[INFO] Cargando relaciones: PURCHASED
  Customer → Product
  ✓ Relaciones creadas: 320

✅ PASO 7: Validar carga

======================================================================
VALIDACIÓN DE CARGA
======================================================================

NODOS CARGADOS:
  Product: 150 nodos
  Supplier: 25 nodos
  Customer: 80 nodos

RELACIONES CARGADAS:
  SUPPLIED_BY: 150 relaciones
  PURCHASED: 320 relaciones

ESTADÍSTICAS GENERALES:
  Total nodos: 255
  Total relaciones: 470

======================================================================
✅ CARGA COMPLETADA EXITOSAMENTE
======================================================================

🎉 Tu grafo está listo en Neo4j

👉 Siguiente paso: Validar con consultas Cypher en Neo4j Browser
   Abre: http://localhost:7474
```

## Proceso de Carga Paso a Paso

### Paso 1: Cargar Schema Validado

El script lee el schema JSON generado previamente:
```json
{
  "metadata": { ... },
  "schema": {
    "nodes": [
      {
        "label": "Product",
        "source_file": "products.csv",
        "key_columns": ["product_id"],
        "properties": ["product_name", "unit_price"]
      }
    ],
    "relationships": [ ... ]
  }
}
```

### Paso 2: Conectar a Neo4j

Establece conexión usando credenciales del `.env`:
- Prueba la conexión con query simple
- Valida que el usuario tenga permisos de escritura

### Paso 3: Preparar CSVs

**Si usa LOAD CSV:**
- Copia CSVs al directorio `import/` de Neo4j
- Verifica que los archivos sean accesibles

**Si usa Batch:**
- Lee CSVs con pandas
- No requiere copiar archivos

### Paso 4: Crear Constraints

Crea constraints de unicidad para Primary Keys:
```cypher
CREATE CONSTRAINT constraint_Product_product_id IF NOT EXISTS
FOR (n:Product)
REQUIRE n.product_id IS UNIQUE
```

**Importante:** Los constraints se crean ANTES de cargar datos para:
- Garantizar integridad
- Mejorar performance de MERGE
- Evitar duplicados

### Paso 5: Cargar Nodos

Para cada tipo de nodo en el schema:
```cypher
LOAD CSV WITH HEADERS FROM 'file:///products.csv' AS row
MERGE (n:Product {product_id: row.product_id})
SET n.product_name = row.product_name,
    n.unit_price = toFloat(row.unit_price)
```

**Usa MERGE** en lugar de CREATE para:
- Evitar duplicados
- Ser idempotente (puedes ejecutar múltiples veces)

### Paso 6: Cargar Relaciones

Para cada relación en el schema:
```cypher
LOAD CSV WITH HEADERS FROM 'file:///products.csv' AS row
MATCH (from:Product {product_id: row.product_id})
MATCH (to:Supplier {supplier_id: row.supplier_id})
MERGE (from)-[r:SUPPLIED_BY]->(to)
```

**Importante:** Los nodos deben existir primero (por eso se cargan antes).

### Paso 7: Validar Carga

Ejecuta queries de conteo para verificar:
- Cantidad de nodos por tipo
- Cantidad de relaciones por tipo
- Totales generales

## Métodos de Carga

El script soporta 2 métodos de carga:

### Método 1: LOAD CSV (Por Defecto)

**Cuándo usar:**
- CSVs < 1M filas
- Neo4j local o con acceso a import/
- Mejor performance

**Ventajas:**
- Muy rápido (optimizado por Neo4j)
- Simple
- Manejo automático de tipos

**Desventajas:**
- Requiere CSVs en directorio `import/`
- Menos control granular de errores

**Configuración:**
```bash
LOAD_METHOD=load_csv  # En .env
```

### Método 2: Python Driver + Batch

**Cuándo usar:**
- CSVs > 1M filas
- Neo4j remoto sin acceso a import/
- Necesitas transformar datos en Python
- Necesitas manejo detallado de errores

**Ventajas:**
- No requiere import/
- Control total de errores
- Progreso granular
- Transformaciones en Python

**Desventajas:**
- Más lento
- Más uso de memoria

**Configuración:**
```bash
LOAD_METHOD=batch     # En .env
BATCH_SIZE=1000       # Filas por batch
```

## Configuración Avanzada

### Variables de Entorno

```bash
# === NEO4J ===
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-password

# === ARCHIVOS ===
CSV_DIR=./csv_data/
SCHEMA_PATH=resultados/schema_csv_validado.json

# === MÉTODO DE CARGA ===
LOAD_METHOD=load_csv  # o 'batch'

# === PERFORMANCE ===
BATCH_SIZE=1000       # Solo para método batch

# === NEO4J IMPORT DIR (Opcional) ===
# Si no se especifica, el script intentará detectarlo
NEO4J_IMPORT_DIR=/path/to/neo4j/import/

# === OPCIONES AVANZADAS ===
# Limpiar base de datos antes de cargar
CLEAR_DATABASE=false  # true para borrar todo antes

# Continuar si falta un CSV
CONTINUE_ON_MISSING_CSV=false

# Modo verbose
VERBOSE=true
```

### Limpiar Base de Datos

**ADVERTENCIA:** Esto borrará TODOS los datos en Neo4j.

```bash
# En .env
CLEAR_DATABASE=true
```

O manualmente en Neo4j Browser:
```cypher
MATCH (n) DETACH DELETE n
```

## Validación Post-Carga

### 1. Verificar en Neo4j Browser

Abrir http://localhost:7474

**Ver todos los tipos de nodos:**
```cypher
CALL db.labels()
```

**Ver todos los tipos de relaciones:**
```cypher
CALL db.relationshipTypes()
```

**Contar nodos y relaciones:**
```cypher
MATCH (n)
RETURN labels(n) as tipo, count(n) as cantidad

MATCH ()-[r]->()
RETURN type(r) as tipo, count(r) as cantidad
```

### 2. Consultas de Ejemplo

**Ver sample de productos y proveedores:**
```cypher
MATCH (p:Product)-[:SUPPLIED_BY]->(s:Supplier)
RETURN p.product_name, s.supplier_name
LIMIT 10
```

**Ver grado de nodos (cantidad de relaciones):**
```cypher
MATCH (n:Product)
RETURN n.product_name,
       size((n)--()) as total_connections
ORDER BY total_connections DESC
LIMIT 10
```

**Encontrar nodos huérfanos (sin relaciones):**
```cypher
MATCH (n:Product)
WHERE NOT (n)--()
RETURN n.product_name
```

### 3. Verificar Constraints

```cypher
SHOW CONSTRAINTS
```

Deberías ver constraints para cada Primary Key del schema.

## Troubleshooting

### Error: "Schema no encontrado"

**Causa:** No existe `schema_csv_validado.json`

**Solución:**
```bash
# Ejecutar primero el diseñador de schema
python scripts/schema_csv_designer.py
```

### Error: "No se pudo conectar a Neo4j"

**Causa:** Neo4j no está corriendo o credenciales incorrectas

**Solución:**
```bash
# Verificar que Neo4j esté corriendo
# Neo4j Desktop: Ver panel de control
# Docker: docker ps | grep neo4j

# Verificar credenciales
cat scripts/.env | grep NEO4J

# Probar conexión manualmente en Neo4j Browser
# http://localhost:7474
```

### Error: "CSV no encontrado"

**Causa:** El archivo CSV especificado en el schema no existe en `CSV_DIR`

**Solución:**
```bash
# Verificar que los CSVs estén en la subcarpeta
ls csv_data/

# Verificar que coincidan con el schema
cat resultados/schema_csv_validado.json | grep source_file

# Copiar CSVs faltantes
cp /ruta/origen/archivo.csv csv_data/
```

### Error: "CSVs must be in import directory"

**Causa:** Usando LOAD CSV pero CSVs no están en import/

**Soluciones:**

**Opción 1: Permitir que el script copie los CSVs**
```bash
# Especificar NEO4J_IMPORT_DIR en .env
NEO4J_IMPORT_DIR=/path/to/neo4j/import/
```

**Opción 2: Copiar manualmente**
```bash
cp csv_data/*.csv /path/to/neo4j/import/
```

**Opción 3: Cambiar a método batch**
```bash
# En .env
LOAD_METHOD=batch
```

### Error: Constraint ya existe

**Causa:** Ya se ejecutó el script antes y los constraints persisten

**Solución:**

Si quieres recrear desde cero:
```cypher
// En Neo4j Browser
// Borrar constraints
DROP CONSTRAINT constraint_Product_product_id IF EXISTS

// O borrar todo
MATCH (n) DETACH DELETE n
```

O simplemente continuar (el script maneja constraints existentes).

### Error: "Relationship creation failed"

**Causa:** Nodo referenciado no existe (foreign key inválida)

**Ejemplo:**
```
products.csv tiene supplier_id = 999
pero suppliers.csv no tiene ese ID
```

**Solución:**

1. Verificar integridad referencial en CSVs:
```python
import pandas as pd

products = pd.read_csv('csv_data/products.csv')
suppliers = pd.read_csv('csv_data/suppliers.csv')

# IDs que no existen
invalid_ids = set(products['supplier_id']) - set(suppliers['supplier_id'])
print(f"IDs inválidos: {invalid_ids}")
```

2. Limpiar datos antes de cargar
3. Usar `CONTINUE_ON_MISSING_CSV=true` para continuar con advertencias

### Performance Lento

**Si la carga tarda mucho:**

**Solución 1: Verificar constraints**
```cypher
SHOW CONSTRAINTS
```
Los constraints mejoran la performance de MERGE.

**Solución 2: Ajustar batch size**
```bash
# Para método batch, aumentar el tamaño
BATCH_SIZE=5000  # En .env
```

**Solución 3: Usar LOAD CSV en lugar de batch**
```bash
LOAD_METHOD=load_csv  # Más rápido
```

**Solución 4: Aumentar memoria de Neo4j**

En Neo4j Desktop → Settings → dbms.memory.heap.max_size

## Ejemplos de Uso

### Ejemplo 1: E-commerce Simple

**Schema:**
```
(Product)-[:SUPPLIED_BY]->(Supplier)
(Customer)-[:PURCHASED]->(Product)
```

**CSVs:**
- `products.csv` (150 filas)
- `suppliers.csv` (25 filas)
- `customers.csv` (80 filas)

**Resultado:**
- 255 nodos total
- 470 relaciones total
- Tiempo: ~5 segundos

### Ejemplo 2: Sistema de Órdenes

**Schema:**
```
(Customer)-[:PLACED]->(Order)-[:CONTAINS]->(OrderItem)-[:FOR_PRODUCT]->(Product)
```

**CSVs:**
- `customers.csv` (500 filas)
- `orders.csv` (2,000 filas)
- `order_items.csv` (8,000 filas)
- `products.csv` (200 filas)

**Resultado:**
- 10,700 nodos total
- 10,000 relaciones total
- Tiempo: ~30 segundos (LOAD CSV)

### Ejemplo 3: Dataset Grande

**CSVs:**
- Total: 5M+ filas

**Configuración:**
```bash
LOAD_METHOD=batch
BATCH_SIZE=5000
```

**Resultado:**
- Tiempo: ~45 minutos
- Progreso mostrado en tiempo real

## Mejores Prácticas

### 1. Orden de Carga

El script carga automáticamente en el orden correcto:
1. Constraints
2. Nodos (en orden del schema)
3. Relaciones (después de nodos)

### 2. Idempotencia

El script usa `MERGE` para ser idempotente:
- Puedes ejecutarlo múltiples veces
- No creará duplicados
- Actualizará propiedades

### 3. Validación de Datos

Antes de cargar, verifica:
```python
import pandas as pd

# Verificar valores nulos en PKs
df = pd.read_csv('csv_data/products.csv')
print(f"Nulos en product_id: {df['product_id'].isnull().sum()}")

# Verificar duplicados en PKs
print(f"Duplicados: {df['product_id'].duplicated().sum()}")
```

### 4. Backup

Antes de cargar datos importantes:
```bash
# Backup de Neo4j
neo4j-admin dump --database=neo4j --to=/path/to/backup.dump
```

### 5. Monitoreo

Durante la carga, monitorear en Neo4j Browser:
```cypher
// Ver cantidad actual de nodos
MATCH (n) RETURN count(n)

// Ver uso de memoria
CALL dbms.queryJmx('org.neo4j:*') YIELD attributes
RETURN attributes.HeapMemoryUsage
```

## Integración con Pipeline

Este módulo es parte del pipeline completo:

```
1. Definir objetivo
   → python scripts/objetivo_schema.py
   → Genera: objetivo_validado.md

2. Diseñar schema desde CSVs
   → python scripts/schema_csv_designer.py
   → Genera: schema_csv_validado.json

3. Cargar CSVs a Neo4j  ← ESTE MÓDULO
   → python scripts/csv_to_neo4j.py
   → Genera: Grafo en Neo4j

4. (Opcional) Pre-procesar grafo
   → python scripts/graph_preprocessing.py
   → Genera: Comunidades, métricas

5. (Opcional) Crear GraphRAG
   → python scripts/graphrag_assistant.py
   → Permite: Consultas híbridas
```

## Recursos Adicionales

- [Neo4j LOAD CSV Guide](https://neo4j.com/docs/operations-manual/current/tools/import/)
- [Neo4j Constraints](https://neo4j.com/docs/cypher-manual/current/constraints/)
- [Neo4j Performance Tuning](https://neo4j.com/developer/guide-performance-tuning/)
- [neo4j Python Driver](https://neo4j.com/docs/python-manual/current/)

## Próximos Pasos

Después de cargar los datos:

1. **Validar el grafo:**
   ```cypher
   MATCH (n) RETURN labels(n), count(n)
   MATCH ()-[r]->() RETURN type(r), count(r)
   ```

2. **Explorar visualmente en Neo4j Browser:**
   ```cypher
   MATCH path = (n)-[r]->(m)
   RETURN path LIMIT 25
   ```

3. **(Opcional) Pre-procesar para GraphRAG:**
   ```bash
   python scripts/graph_preprocessing.py
   ```

4. **(Opcional) Crear asistente GraphRAG:**
   ```bash
   python scripts/graphrag_assistant.py
   ```

## Soporte

Si encuentras problemas:

1. Revisa la sección de Troubleshooting
2. Verifica que el schema validado existe
3. Confirma que Neo4j está corriendo
4. Verifica los CSVs en la subcarpeta
5. Revisa logs del script
6. Verifica configuración en `.env`
