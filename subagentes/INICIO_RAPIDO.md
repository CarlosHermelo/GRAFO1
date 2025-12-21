# Inicio Rápido - Orquestador de Grafos de Conocimiento

Empieza a construir grafos de conocimiento en **menos de 5 minutos**.

## Paso 1: Prerrequisitos

- ✅ **Python 3.8+**
- ✅ **Neo4j** (local o remoto)
- ✅ **OpenAI API Key**
- ✅ **Claude Code** (para interactuar con los subagentes)

## Paso 2: Configurar Variables de Entorno

### 1. Copia el template:
```bash
cp .env.example .env
```

### 2. Edita `.env` con tus credenciales:

```bash
# Windows
notepad .env

# Linux/Mac
nano .env
```

### 3. Completa las variables MÍNIMAS:

```bash
OPENAI_API_KEY=sk-proj-XXXXXXXX
LLM_MODEL=gpt-4-turbo
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=tu_password
```

### 4. Para TEXTO, agregar:

```bash
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_DIMENSION=1536
```

### 5. Para CSV, agregar:

```bash
CSV_DIR=./data/csv/
```

## Paso 3: Invocar el Orquestador

En tu conversación con Claude Code, escribe:

```
Lee agente_orquestador.md y asume ese rol
```

O más directamente:

```
Invoca al orquestador de grafos
```

## Paso 4: El Orquestador se Presenta

Verás algo como:

```
╔════════════════════════════════════════════════════════════════════╗
║            ORQUESTADOR DE GRAFOS DE CONOCIMIENTO                   ║
╚════════════════════════════════════════════════════════════════════╝

Hola, soy el orquestador del sistema de construcción de grafos de conocimiento.

Primero, déjame verificar la configuración del sistema...

[Verifica .env]
[Muestra proyectos existentes]

¿Qué deseas hacer?
1. Crear nuevo proyecto
2. Continuar proyecto existente
3. Listar proyectos
4. Verificar configuración (.env)
```

## Paso 5: Crear tu Primer Proyecto

### 1. Selecciona opción 1:

```
Usuario: 1
```

### 2. Ingresa un nombre (sin espacios):

```
Orquestador: Nombre del proyecto (sin espacios, usa guiones):

Usuario: mi_primer_grafo
```

### 3. Selecciona el tipo:

```
Orquestador: Tipo de fuente de datos:
            1. TEXTO - Documentos (PDF, TXT, MD)
            2. CSV - Base de datos relacional

Usuario: 1
```

### 4. El orquestador validará y creará el proyecto:

```
Orquestador: Validando .env...
            ✅ Todas las variables configuradas

            Creando estructura de proyecto...
            ✅ Proyecto creado en: proyectos/mi_primer_grafo/
```

## Ejemplo Completo - Proyecto TEXTO

### Fase 1: Definición del Objetivo

```
Orquestador: FASE 1: DEFINICIÓN DEL OBJETIVO

            A continuación, asumiré el rol del Agente de Objetivo...

            ¿Qué objetivo específico buscas resolver con tu grafo de conocimiento?
```

**Tu respuesta (ejemplo):**

```
Usuario: Quiero construir un grafo que relacione normativas de PAMI con tipos de
        prótesis y proveedores autorizados, para poder consultar qué normativas
        regulan cada tipo de prótesis.
```

**El agente refinará tu objetivo:**

```
Agente: Perfecto, voy a refinar tu objetivo...

        OBJETIVO TÉCNICO VALIDADO:

        Objetivo: Construir un grafo de conocimiento que integre normativas PAMI,
        tipos de prótesis y proveedores, permitiendo consultar qué normativas
        regulan cada tipo de prótesis y qué proveedores están autorizados.

        Dominio: healthcare

        Entidades Clave:
        - Normativa: Resoluciones y disposiciones PAMI
        - Prótesis: Tipos específicos de prótesis
        - Proveedor: Empresas autorizadas

        ✅ Guardado en: proyectos/mi_primer_grafo/resultados/objetivo_validado.md

Orquestador: ✅ Fase 1 completada

            ¿Deseas continuar con la siguiente fase (Diseño de Schema)? (s/n)
```

### Fase 2: Diseño de Schema

```
Usuario: s

Orquestador: FASE 2: DISEÑO DE SCHEMA

            Asumiré el rol del Agente de Diseño de Schema...
            [Lee tu objetivo validado]

Agente: Basándome en tu objetivo, propongo este schema:

        NODOS:
        - Normativa (propiedades: numero, fecha, titulo)
        - Prótesis (propiedades: tipo, codigo, descripcion)
        - Proveedor (propiedades: nombre, cuit)

        RELACIONES:
        - (Normativa)-[:REGULA]->(Prótesis)
        - (Proveedor)-[:SUMINISTRA]->(Prótesis)

        ¿Apruebas este schema? (s/n/editar)

Usuario: s

Agente: ✅ Schema guardado en: proyectos/mi_primer_grafo/resultados/schema_diseñado.json

Orquestador: ✅ Fase 2 completada

            ¿Continuar con Fase 3 (Ingesta de Datos)? (s/n)
```

### Fase 3: Ingesta de Datos

**Antes de esta fase, coloca tus documentos en:**
```
proyectos/mi_primer_grafo/data/texto/
```

```
Usuario: s

Orquestador: FASE 3: INGESTA DE DATOS

            Asumiré el rol del Agente de Ingesta...

Agente: [Genera script de ingesta]
        [Procesa documentos]
        [Extrae entidades y relaciones]
        [Carga en Neo4j]

        ✅ Ingesta completada:
           • 1,247 entidades creadas
           • 3,891 relaciones establecidas

Orquestador: ✅ Fase 3 completada

            Siguiente fase: Depuración del Grafo (OPCIONAL)
            ¿Ejecutar? (s/n)
```

### Fases 4-7: Continuación

El orquestador te guiará por las fases restantes:

- **Fase 4:** Depuración (opcional)
- **Fase 5:** Pre-procesamiento (opcional)
- **Fase 6:** Base de Datos Vectorial
- **Fase 7:** Asistente GraphRAG

## Verificar Resultados

### En Neo4j Browser

1. Abre: http://localhost:7474
2. Ejecuta:
   ```cypher
   MATCH (n) RETURN n LIMIT 25
   ```

### Ver Archivos Generados

```bash
ls proyectos/mi_primer_grafo/resultados/
```

Verás:
- `objetivo_validado.md`
- `schema_diseñado.json`
- `ingesta_log.json`
- etc.

## Comandos Útiles Durante la Ejecución

En cualquier momento puedes decir:

- `estado` - Ver estado del proyecto
- `historial` - Ver historial completo
- `config` - Ver configuración
- `saltar` - Saltar fase actual (si es opcional)
- `repetir` - Repetir una fase
- `menu` - Volver al menú principal

## Continuar un Proyecto Existente

Si cerraste la sesión y quieres continuar:

```
Usuario: Invoca al orquestador

Orquestador: [Muestra menú]

Usuario: 2

Orquestador: Proyectos disponibles:
            1. mi_primer_grafo (TEXTO) - Fase actual: ingesta

Usuario: 1

Orquestador: Proyecto: mi_primer_grafo
            Fases completadas:
              ✅ Objetivo
              ✅ Schema
              ✅ Ingesta

            Fase actual: Depuración

            ¿Continuar? (s/n)
```

## Estructura de Archivos Generada

```
proyectos/
└── mi_primer_grafo/
    ├── config/
    │   └── proyecto.json        # Estado del proyecto
    ├── resultados/
    │   ├── objetivo_validado.md
    │   ├── schema_diseñado.json
    │   └── ...
    ├── data/
    │   └── texto/               # COLOCA TUS DOCUMENTOS AQUÍ
    │       ├── doc1.pdf
    │       └── doc2.txt
    ├── logs/
    │   └── historial.json
    └── scripts/
        └── (scripts generados)
```

## Solución Rápida de Problemas

### "No encuentra el .env"

```bash
cp .env.example .env
nano .env  # Completa las variables
```

### "Faltan variables en .env"

El orquestador te dirá exactamente cuáles:

```
❌ NEO4J_PASSWORD = (FALTA)

Para configurarla, edita .env y agrega:
  NEO4J_PASSWORD=tu_password
```

### "Error de conexión a Neo4j"

```bash
# Verifica que Neo4j esté corriendo
docker ps | grep neo4j

# Si no, inicia Neo4j
docker start neo4j
```

## Ciclo CSV (Base de Datos Relacional)

Si tienes archivos CSV de una BD relacional:

### 1. Coloca los CSVs en:
```
proyectos/mi_proyecto/data/csv/
```

### 2. Al crear el proyecto, selecciona tipo 2 (CSV)

### 3. El flujo será:
- Fase 1: Definición del Objetivo
- Fase 2: Diseño de Schema desde CSV
- Fase 3: Carga CSV a Neo4j

## Próximos Pasos

Una vez completado tu primer proyecto:

1. **Explora el grafo en Neo4j Browser**
2. **Usa el Asistente GraphRAG** (última fase) para consultas
3. **Crea nuevos proyectos** con diferentes objetivos
4. **Lee la documentación completa:** `README_ORQUESTADOR.md`

## Recursos

- **Documentación Completa:** `README_ORQUESTADOR.md`
- **Especificación del Agente:** `agente_orquestador.md`
- **Template de Variables:** `.env.example`

## Consejos

### 1. Sé Específico en el Objetivo
❌ "Quiero un grafo de documentos"
✅ "Quiero un grafo que relacione normativas PAMI con prótesis y proveedores"

### 2. Coloca los Documentos Antes de la Ingesta
Asegúrate de que tus archivos estén en `data/texto/` o `data/csv/` antes de la fase 3.

### 3. Valida el Schema
Revisa cuidadosamente el schema propuesto antes de aprobarlo. Es la base de todo.

### 4. Usa las Fases Opcionales
La depuración y pre-procesamiento mejoran significativamente la calidad del grafo.

## Ayuda

Para verificar la configuración en cualquier momento:

```
Usuario: Invoca al orquestador
        [Selecciona opción 4: Verificar configuración]
```

---

**¡Listo para comenzar!** 🚀

```
Invoca al orquestador de grafos
```
