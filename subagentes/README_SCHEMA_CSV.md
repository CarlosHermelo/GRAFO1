# Diseñador de Schema de Grafo desde CSV

Este módulo contiene el **Agente Diseñador de Schema CSV** que crea un script para diseñar schemas de grafos a partir de archivos CSV provenientes de vuelcos de bases de datos relacionales.

## ¿Para Qué Sirve?

Este módulo es ideal cuando tienes:
- **Vuelcos de bases de datos relacionales** (exports a CSV)
- **Datos estructurados en tablas** que quieres migrar a un grafo
- **CSVs con relaciones** entre ellos (vía foreign keys)

### Diferencia con Schema desde Texto

| Característica | Schema desde Texto | Schema desde CSV |
|----------------|-------------------|------------------|
| **Fuente** | PDFs, documentos no estructurados | CSVs de BD relacionales |
| **Método** | NER, extracción semántica | Análisis de columnas y tipos |
| **Relaciones** | Contexto en el texto | Foreign keys, columnas compartidas |
| **Herramientas** | LangChain + LLM | Pandas + LLM |
| **Precisión** | Depende del texto | Alta (datos estructurados) |

## Componentes

### 1. Agente Constructor (`agente_diseño_schema_csv.md`)
Agente experto que CREA el script para diseñar el schema desde CSV.

### 2. Script Diseñador (`scripts/schema_csv_designer.py`)
Script ejecutable que analiza CSVs y diseña el schema del grafo.

### 3. Configuración (`scripts/.env`)
Variables de entorno incluyendo la ruta a la subcarpeta de CSVs.

## Pre-requisitos

### 1. Objetivo del Schema Definido

Debe existir el archivo generado por `agente_objetivo_schema`:
```bash
resultados/objetivo_validado.md
```

Si no existe, el script usará un objetivo por defecto.

### 2. Archivos CSV Organizados

**IMPORTANTE:** Los CSVs deben estar en una **subcarpeta dedicada**.

**Estructura recomendada:**
```
proyecto/
├── csv_data/              ← Subcarpeta con CSVs
│   ├── products.csv
│   ├── suppliers.csv
│   ├── customers.csv
│   ├── orders.csv
│   └── order_items.csv
├── scripts/
│   ├── schema_csv_designer.py
│   └── .env
└── resultados/
    └── objetivo_validado.md
```

**Formato de CSVs:**
- Encoding: UTF-8
- Separador: coma (,)
- Header: Primera fila con nombres de columnas
- Datos limpios (sin valores null problemáticos si es posible)

### 3. OpenAI API Key

Para usar el LLM en el diseño del schema.

## Instalación

### 1. Instalar Dependencias

```bash
cd scripts
pip install -r requirements.txt
```

Dependencias necesarias:
- `openai` - Cliente de OpenAI
- `pandas` - Análisis de CSVs
- `python-dotenv` - Configuración

### 2. Configurar Variables de Entorno

```bash
# Copiar archivo de ejemplo
cp scripts/.env.schema_csv.example scripts/.env

# Editar configuración
nano scripts/.env
```

**Configuración mínima:**
```bash
OPENAI_API_KEY=sk-tu-api-key-aqui
LLM_MODEL=gpt-4-turbo
CSV_DIR=./csv_data/          # ← Subcarpeta con los CSVs
```

### 3. Preparar CSVs

```bash
# Crear subcarpeta para CSVs
mkdir csv_data

# Copiar tus archivos CSV a la subcarpeta
cp /ruta/a/tus/vuelcos/*.csv csv_data/

# Verificar que los CSVs estén ahí
ls csv_data/
```

## Uso

### Ejecución Básica

```bash
python scripts/schema_csv_designer.py
```

**Output esperado:**
```
======================================================================
DISEÑADOR DE SCHEMA DE GRAFO DESDE CSV
======================================================================

🔧 Modelo LLM: gpt-4-turbo
📁 Directorio CSV: ./csv_data/

🎯 PASO 1: Cargar objetivo del schema
  ✓ Objetivo: Analizar relación entre productos, proveedores y ventas
  ✓ Dominio: commercial

📂 PASO 2: Descubrir archivos CSV
[INFO] Encontrados 5 archivos CSV

🔍 PASO 3: Analizar estructura de CSVs
  ✓ Analizado: products.csv (8 columnas)
  ✓ Analizado: suppliers.csv (5 columnas)
  ✓ Analizado: customers.csv (6 columnas)
  ✓ Analizado: orders.csv (4 columnas)
  ✓ Analizado: order_items.csv (5 columnas)

🤖 PASO 4: Proponer schema con LLM

  Intento 1/3

======================================================================
🏗️  SCHEMA DE GRAFO PROPUESTO
======================================================================
{
  "nodes": [
    {
      "label": "Product",
      "source_file": "products.csv",
      "key_columns": ["product_id"],
      "properties": ["product_name", "unit_price", "stock_quantity"],
      "description": "Productos del catálogo"
    },
    ...
  ],
  "relationships": [
    {
      "type": "SUPPLIED_BY",
      "from_label": "Product",
      "to_label": "Supplier",
      ...
    }
  ]
}
======================================================================

¿Aprobar este schema? (s/n/editar): s
✅ Schema aprobado

✅ PASO 5: Validar consistencia del schema
  ✓ Schema consistente con CSVs

💾 PASO 6: Guardar schema validado

✅ Schema guardado en: resultados/schema_csv_validado.json

======================================================================
✅ DISEÑO DE SCHEMA COMPLETADO EXITOSAMENTE
======================================================================

📁 Archivo generado: resultados/schema_csv_validado.json

👉 Siguiente paso: Ejecutar agente de carga de datos CSV a Neo4j
```

### Proceso de Revisión Humana (HITL)

Durante la ejecución, el script te pedirá aprobar el schema propuesto:

**Opción 1: Aprobar (s)**
```
¿Aprobar este schema? (s/n/editar): s
→ Continúa con el schema propuesto por el LLM
```

**Opción 2: Rechazar y regenerar (n)**
```
¿Aprobar este schema? (s/n/editar): n
→ El LLM genera un nuevo schema (intento 2/3)
```

**Opción 3: Editar manualmente (editar)**
```
¿Aprobar este schema? (s/n/editar): editar

Ingresa el schema corregido en JSON (o 'cancelar'):
> {"nodes": [...], "relationships": [...]}
→ Usa el schema que ingresaste manualmente
```

## Estructura de Archivos de Salida

Después de ejecutar el script:

```
resultados/
├── schema_csv_validado.json      ← Schema en JSON
└── schema_csv_validado.md        ← Schema en Markdown (legible)
```

### Contenido de `schema_csv_validado.json`

```json
{
  "metadata": {
    "generated_at": "2024-12-18T23:30:00",
    "objetivo": "Analizar relación entre productos, proveedores y ventas",
    "domain": "commercial",
    "source": "CSV files (relational database dump)"
  },
  "schema": {
    "nodes": [
      {
        "label": "Product",
        "source_file": "products.csv",
        "key_columns": ["product_id"],
        "properties": ["product_name", "category", "unit_price"],
        "description": "Productos del catálogo"
      },
      {
        "label": "Supplier",
        "source_file": "suppliers.csv",
        "key_columns": ["supplier_id"],
        "properties": ["supplier_name", "contact_email"],
        "description": "Proveedores de productos"
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
    ],
    "reasoning": "Schema diseñado siguiendo modelo normalizado..."
  }
}
```

## Mejores Prácticas

### 1. Organización de CSVs

**✅ RECOMENDADO:**
```
csv_data/
├── products.csv
├── suppliers.csv
├── customers.csv
└── orders.csv
```

**❌ EVITAR:**
```
/
├── products.csv           ← CSVs mezclados con scripts
├── suppliers.csv
├── schema_csv_designer.py
└── ...
```

### 2. Nombres de Archivos CSV

**✅ BUENOS:**
- `products.csv` (singular o plural consistente)
- `customer_orders.csv` (snake_case)
- `order_items.csv`

**❌ MALOS:**
- `Products Data (2024).csv` (espacios, paréntesis)
- `órdenes.csv` (caracteres especiales, acentos)
- `temp_export_final_v2.csv` (no descriptivo)

### 3. Estructura de CSVs

**Header (primera fila):**
```csv
product_id,product_name,supplier_id,unit_price
1,Laptop Dell,5,899.99
2,Mouse Logitech,3,29.99
```

**Columnas Primary Key:**
- Usar nombres claros: `product_id`, `customer_id`
- Valores únicos
- No nulos

**Columnas Foreign Key:**
- Seguir patrón: `{tabla}_id` (ej: `supplier_id`)
- Referenciar a PK de otra tabla
- Facilita detección automática

### 4. Tipos de Datos

El script detecta automáticamente tipos:
- **Numéricos:** int, float
- **Texto:** string
- **Fechas:** datetime (si están en formato ISO)
- **Booleanos:** true/false, 1/0

**Recomendación:** Mantén tipos consistentes en cada columna.

## Convenciones de Modelado

El LLM propone schemas siguiendo estas convenciones de Neo4j:

### Labels de Nodos (PascalCase)
```
✅ Product, Customer, Order, Supplier
❌ product, CUSTOMER, order_item
```

### Types de Relaciones (UPPER_SNAKE_CASE)
```
✅ PURCHASED, SUPPLIED_BY, BELONGS_TO
❌ purchased, Supplied_By, belongs-to
```

### Propiedades (snake_case)
```
✅ product_name, created_at, unit_price
❌ ProductName, createdAt, UnitPrice
```

## Ejemplos de Uso

### Ejemplo 1: E-commerce Simple

**CSVs:**
```
csv_data/
├── products.csv         (product_id, name, price, supplier_id)
├── suppliers.csv        (supplier_id, name, email)
└── customers.csv        (customer_id, name, email)
```

**Schema generado:**
```
(Product)-[:SUPPLIED_BY]->(Supplier)
(Customer)-[:PURCHASED]->(Product)
```

### Ejemplo 2: Sistema de Órdenes

**CSVs:**
```
csv_data/
├── customers.csv        (customer_id, name, email)
├── orders.csv           (order_id, customer_id, order_date)
├── order_items.csv      (item_id, order_id, product_id, quantity)
└── products.csv         (product_id, name, price)
```

**Schema generado:**
```
(Customer)-[:PLACED]->(Order)
(Order)-[:CONTAINS]->(OrderItem)-[:FOR_PRODUCT]->(Product)
```

### Ejemplo 3: Proveedores y Productos

**CSVs:**
```
csv_data/
├── suppliers.csv        (supplier_id, name, country)
├── products.csv         (product_id, name, supplier_id, category)
└── categories.csv       (category_id, category_name)
```

**Schema generado:**
```
(Product)-[:SUPPLIED_BY]->(Supplier)
(Product)-[:IN_CATEGORY]->(Category)
```

## Troubleshooting

### Error: "Directorio CSV no encontrado"

**Causa:** La ruta `CSV_DIR` en `.env` no existe

**Solución:**
```bash
# Verificar ruta en .env
cat scripts/.env | grep CSV_DIR

# Crear directorio si no existe
mkdir -p csv_data

# Verificar que los CSVs estén ahí
ls csv_data/
```

### Error: "No se encontraron archivos CSV"

**Causa:** La subcarpeta `csv_data/` está vacía o no tiene archivos .csv

**Solución:**
```bash
# Verificar contenido
ls -la csv_data/

# Copiar CSVs
cp /ruta/origen/*.csv csv_data/

# Verificar extensión (debe ser .csv)
# Si están como .CSV (mayúsculas), renombrar:
for f in csv_data/*.CSV; do mv "$f" "${f%.CSV}.csv"; done
```

### Error: "OPENAI_API_KEY no configurada"

**Solución:**
```bash
# Editar .env
nano scripts/.env

# Agregar:
OPENAI_API_KEY=sk-tu-api-key-real
```

### Error: Encoding al leer CSV

**Causa:** CSV con encoding incorrecto (no UTF-8)

**Solución:**
```bash
# Convertir a UTF-8
iconv -f ISO-8859-1 -t UTF-8 input.csv > output.csv

# O en Python:
import pandas as pd
df = pd.read_csv('input.csv', encoding='latin1')
df.to_csv('output.csv', encoding='utf-8', index=False)
```

### Schema propuesto tiene errores

**Opción 1:** Usar "n" para regenerar
```
¿Aprobar este schema? (s/n/editar): n
→ LLM intentará de nuevo
```

**Opción 2:** Usar "editar" para corregir manualmente
```
¿Aprobar este schema? (s/n/editar): editar
→ Ingresa JSON corregido
```

## Validación del Schema

El script valida automáticamente:

1. **Archivos existen:** `source_file` debe corresponder a un CSV real
2. **Columnas existen:** Todas las columnas mencionadas deben estar en el CSV
3. **Primary keys únicos:** `key_columns` deben ser únicos
4. **Foreign keys válidos:** Columnas de relaciones deben existir

**Ejemplo de error de validación:**
```
⚠️  ADVERTENCIAS DE VALIDACIÓN:
  - Nodo 'Product': columna 'supplier_id' no existe en products.csv
  - Relación 'SUPPLIED_BY': columna 'supplier_id' no existe

¿Continuar de todos modos? (s/n): n
```

## Integración con Otros Agentes

Este agente forma parte de un pipeline:

```
1. agente_objetivo_schema
   ↓ Define objetivo y dominio

2. agente_diseño_schema_csv  ← ESTE MÓDULO
   ↓ Diseña schema desde CSVs

3. agente_carga_csv_neo4j (próximo)
   ↓ Carga CSVs a Neo4j según schema

4. agente_validacion_grafo
   → Valida el grafo creado
```

## Comparación de Costos

### Usando GPT-4-turbo
- **Costo por ejecución:** ~$0.05-0.15 USD
- **Tokens promedio:** ~3,000-5,000 tokens
- **Tiempo:** 10-30 segundos

### Usando GPT-3.5-turbo
- **Costo por ejecución:** ~$0.005-0.015 USD
- **Tokens promedio:** ~3,000-5,000 tokens
- **Tiempo:** 5-15 segundos
- **⚠️ Advertencia:** Menor precisión en schema complejo

**Recomendación:** Usar GPT-4-turbo para mejor calidad de schema.

## Próximos Pasos

Después de generar el schema:

1. **Revisar schema generado:**
   ```bash
   cat resultados/schema_csv_validado.json
   ```

2. **Ejecutar agente de carga CSV a Neo4j** (cuando esté disponible):
   ```bash
   python scripts/csv_to_neo4j.py
   ```

3. **Validar el grafo creado:**
   ```cypher
   // En Neo4j Browser
   MATCH (n) RETURN labels(n), count(n)
   MATCH ()-[r]->() RETURN type(r), count(r)
   ```

## Recursos Adicionales

- [Neo4j Naming Conventions](https://neo4j.com/docs/getting-started/cypher-intro/patterns/)
- [Pandas read_csv Documentation](https://pandas.pydata.org/docs/reference/api/pandas.read_csv.html)
- [Graph Data Modeling Best Practices](https://neo4j.com/developer/guide-data-modeling/)

## Soporte

Si encuentras problemas:

1. Revisa la sección de Troubleshooting
2. Verifica que los CSVs estén en la subcarpeta correcta
3. Confirma que el objetivo del schema existe
4. Revisa logs del script
5. Verifica configuración en `.env`
