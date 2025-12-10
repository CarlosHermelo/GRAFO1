# Grafo de Prótesis - Proyecto Principal

Este proyecto gestiona un grafo de conocimiento sobre prótesis en Neo4j, permitiendo cargar datos desde archivos CSV y realizar consultas.


## 📋 Comandos a Ejecutar

```bash
python convertir_bd_kg.py # toma .csv y convierte en un schmea
python consulta_protesis.py # no recuerdo 
```

## 🚀 Esto es una prueba Convertir de unas tablas a grafos .Toma archivos .csv y crea los NODOS y las Relaciones .
```bash
Los dos propgramas el que carga y el que consulta
python consulta_protesis.py # no recuerdo 
```
1)tomar arhivos *.csv 
2) en el codigo (DEFINE_RULES) define las relaciones (esto lo debo haber generado con un llms)
3) los atribuos deben tener un propieda que sea un foreing keyu

Sí. Para que este script funcione son necesarios los tres elementos.
Sin alguno de ellos, el pipeline no puede construirse.

requisitos mínimos
1. archivos CSV

Cada CSV representa una entidad del grafo.
El nombre del archivo define el nombre del nodo:

Ejemplo:
tramite.csv → nodo Tramite

2. columnas con nombres tipo id_*

Son el mecanismo para detectar vínculos.
Si no hay columnas id_xxx, no se detectan relaciones.

Ejemplo:
id_afiliado en tramite.csv permite crear una relación hacia Afiliado.

3. diccionario SEMANTIC_RULES

Es indispensable.
Define qué relación crear a partir de cada columna id_xxx.

Ejemplo:

("Tramite", "id_afiliado") → ("Afiliado", "TRAMITE_DE")

### Activar el Entorno Virtual

```bash
cd C:\Users\u14527001\Downloads\grafo_protesis
gra\Scripts\activate
```

Una vez activado, deberías ver:

```
(gra) C:\Users\u14527001\Downloads\grafo_protesis
```

---

## 🗄️ Configuración de Neo4j

### Crear Cuenta Gratuita

1. Crea una cuenta gratuita en Neo4j:
   - **URL:** https://console-preview.neo4j.io/tools/query

2. **Credenciales de Conexión:**
   - **URI:** `neo4j+s://b0df6e44.databases.neo4j.io`
   - **Username:** `neo4j`
   - **Password:** `NQkXw6G9S7jO8wQXQIRpd5BX-g2t_bEvXweJVPSWO1g`

3. Configura estas credenciales en tu archivo `.env`:
   ```
   NEO4J_URI=neo4j+s://b0df6e44.databases.neo4j.io
   NEO4J_USER=neo4j
   NEO4J_PASSWORD=NQkXw6G9S7jO8wQXQIRpd5BX-g2t_bEvXweJVPSWO1g
   ```

---

---

## 📄 convertir_bd_kg.py

**Crea un schema de prótesis en Neo4j y levanta archivos CSV a nodos y relaciones**

### Uso

```bash
python convertir_bd_kg.py
```

### ⚠️ Requisitos

- **Archivos CSV necesarios:** El script requiere archivos `.csv` en el mismo directorio
- **⚠️ IMPORTANTE:** Asegúrate de tener los archivos CSV necesarios antes de ejecutar el script

### Funcionamiento

El script:
1. **Crea el schema** del grafo de prótesis en Neo4j
2. **Lee los archivos CSV** del directorio actual
3. **Carga los datos** como nodos y relaciones en la base de datos

---

## 🔍 consulta_protesis.py

**Realiza consultas al Grafo de Conocimiento (KG) de Prótesis**

### Uso

```bash
python consulta_protesis.py
```

### Funcionamiento

Este script permite realizar consultas sobre el grafo de prótesis cargado en Neo4j, proporcionando una interfaz para explorar y consultar los datos del conocimiento sobre prótesis.

---

## 📁 Estructura del Proyecto

```
grafo_protesis/
├── README.md                    # Este archivo
├── convertir_bd_kg.py          # Carga CSV y crea schema en Neo4j
├── consulta_protesis.py        # Consultas al KG de prótesis
├── curso_1/                    # Módulo de generación de grafos desde texto
│   ├── README.md
│   ├── gen_schema_txt.py
│   ├── gen_subir_schma_a_neo.py
│   └── gen_query.py
└── *.csv                        # Archivos CSV con datos de prótesis
```

---

## 📝 Notas

- Asegúrate de tener el entorno virtual activado antes de ejecutar los scripts
- Los archivos CSV deben estar en el mismo directorio que `convertir_bd_kg.py`
- Verifica que las credenciales de Neo4j estén correctamente configuradas en el archivo `.env`
