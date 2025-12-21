# Orquestador de Grafos de Conocimiento

## Descripción

El **Orquestador** es el subagente principal que coordina todo el sistema de construcción de Grafos de Conocimiento. Se invoca como cualquier otro subagente y guía al usuario a través de todo el proceso, invocando a los demás subagentes según sea necesario.

## Características Principales

### 🎯 Gestión de Proyectos
- Crear múltiples proyectos independientes
- Estructura de directorios organizada por proyecto
- Mantener contexto entre sesiones
- Historial completo de acciones

### 🔧 Validación de Configuración
- Verificar archivo `.env` antes de iniciar
- Validar variables requeridas según tipo de proyecto
- Mostrar estado de configuración
- Guía para completar variables faltantes

### 🔄 Coordinación de Subagentes
- **Ciclo TEXTO**: 7 fases desde objetivo hasta asistente GraphRAG
- **Ciclo CSV**: 3 fases desde objetivo hasta carga en Neo4j
- Ejecutar fases en orden lógico
- Permitir saltar fases opcionales
- Permitir repetir fases anteriores

### 📊 Gestión de Estado
- Tracking de fase actual
- Registro de fases completadas
- Historial de todas las acciones
- Persistencia entre sesiones

## Cómo Usar el Orquestador

### Invocar el Orquestador

En una conversación con Claude Code, simplemente di:

```
Por favor, lee agente_orquestador.md y asume ese rol
```

O más directamente:

```
Invoca al orquestador de grafos
```

### El Orquestador se Presentará

```
╔════════════════════════════════════════════════════════════════════╗
║            ORQUESTADOR DE GRAFOS DE CONOCIMIENTO                   ║
╚════════════════════════════════════════════════════════════════════╝

Hola, soy el orquestador del sistema de construcción de grafos de conocimiento.

Primero, déjame verificar la configuración del sistema...

[Verificará tu .env]
[Mostrará proyectos existentes]
[Mostrará menú de opciones]
```

## Flujos de Trabajo

### Ciclo TEXTO (Documentos)

```
1. Definición del Objetivo
   ↓
2. Diseño de Schema TEXTO
   ↓
3. Ingesta de Datos
   ↓
4. Depuración (opcional)
   ↓
5. Pre-procesamiento (opcional)
   ↓
6. Base de Datos Vectorial
   ↓
7. Asistente GraphRAG
```

### Ciclo CSV (BD Relacional)

```
1. Definición del Objetivo
   ↓
2. Diseño de Schema CSV
   ↓
3. Carga CSV a Neo4j
```

## Configuración Requerida

### Archivo `.env`

Antes de usar el orquestador, debes tener un archivo `.env` en `subagentes/.env` con las variables necesarias.

#### Mínimo Requerido (siempre):

```bash
OPENAI_API_KEY=sk-proj-...
LLM_MODEL=gpt-4-turbo
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=tu_password
```

#### Para Ciclo TEXTO:

```bash
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_DIMENSION=1536
```

#### Para Ciclo CSV:

```bash
CSV_DIR=./data/csv/
```

### Crear el archivo .env

1. Copia el template:
   ```bash
   cp .env.example .env
   ```

2. Edita y completa las variables:
   ```bash
   # Windows
   notepad .env

   # Linux/Mac
   nano .env
   ```

3. El orquestador validará la configuración al iniciar

## Estructura de Proyectos

El orquestador crea y gestiona proyectos en esta estructura:

```
proyectos/
└── nombre_proyecto/
    ├── config/
    │   └── proyecto.json          # Estado del proyecto
    ├── resultados/
    │   ├── objetivo_validado.md
    │   ├── schema_diseñado.json
    │   └── ...
    ├── data/
    │   ├── texto/                 # Para documentos
    │   └── csv/                   # Para CSVs
    ├── logs/
    │   └── historial.json         # Historial completo
    └── scripts/
        └── ...                    # Scripts generados
```

## Cómo Funciona la Coordinación

### Invocación de Subagentes

Cuando el orquestador necesita ejecutar una fase:

1. **Lee el archivo .md del subagente** correspondiente
2. **Asume el rol de ese subagente**
3. **Interactúa con el usuario** siguiendo las instrucciones del subagente
4. **Guarda los resultados** en el proyecto
5. **Actualiza el estado** (proyecto.json, historial.json)
6. **Vuelve al rol de orquestador** y pregunta si continuar

### Ejemplo de Flujo

```
Usuario: Invoca al orquestador

Orquestador: [Se presenta y muestra menú]

Usuario: 1 (Crear nuevo proyecto)

Orquestador: [Pregunta nombre y tipo]

Usuario: mi_proyecto, tipo TEXTO

Orquestador: [Valida .env, crea estructura]
            [Lee agente_objetivo_schema.md]
            [Asume rol de ese agente]

Agente Objetivo: ¿Qué objetivo buscas con tu grafo?

Usuario: [Describe su objetivo]

Agente Objetivo: [Refina el objetivo]
                [Guarda resultado]

Orquestador: [Vuelve a su rol]
            ✅ Fase 1 completada
            ¿Continuar con Fase 2? (s/n)

Usuario: s

Orquestador: [Lee agente_diseño_schema.md]
            [Asume rol de ese agente]

[Y así sucesivamente...]
```

## Mantenimiento del Contexto

El orquestador asegura coherencia mediante:

### 1. Objetivo Compartido
- El `objetivo_validado.md` se lee antes de cada fase
- Se pasa a todos los subagentes posteriores
- Guía las decisiones de diseño y prompts

### 2. Schema Compartido
- El `schema_diseñado.json` se usa en todas las fases post-diseño
- Asegura consistencia en entidades y relaciones
- Valida que los datos coincidan con el schema

### 3. Variables de Entorno
- El `.env` se valida al inicio
- Todos los scripts generados lo usan
- Asegura configuración consistente

### 4. Estado del Proyecto
- `proyecto.json` mantiene el estado actual
- `historial.json` registra todas las acciones
- Permite reanudar en cualquier momento

## Funcionalidades Avanzadas

### Pausar y Continuar

Puedes pausar en cualquier momento. El estado se guarda automáticamente.

Para continuar:
```
Invoca al orquestador
[Selecciona opción 2: Continuar proyecto]
[Selecciona tu proyecto]
```

### Repetir una Fase

Si una fase no dio buenos resultados:
```
[En el menú del proyecto]
Selecciona: Repetir una fase anterior
[Elige la fase]
```

### Saltar Fases Opcionales

Las fases de Depuración y Pre-procesamiento son opcionales:
```
FASE 4: DEPURACIÓN (OPCIONAL)
¿Deseas ejecutar esta fase? (s/n)

[Si dices 'n', se salta]
```

## Comandos Durante la Ejecución

Puedes usar estos comandos en cualquier momento:

- `estado` - Ver estado del proyecto actual
- `historial` - Ver historial completo
- `config` - Ver configuración del .env
- `saltar` - Saltar fase actual (si es opcional)
- `repetir` - Repetir una fase
- `menu` - Volver al menú principal

## Ejemplo de Uso Completo

### 1. Invocar el Orquestador

```
Usuario: Lee agente_orquestador.md y asume ese rol
```

### 2. Crear Proyecto

```
Orquestador: [Muestra menú]

Usuario: 1

Orquestador: Nombre del proyecto:

Usuario: analisis_contratos

Orquestador: Tipo:
            1. TEXTO
            2. CSV

Usuario: 1
```

### 3. Validación

```
Orquestador: Validando .env...
            ✅ Todas las variables configuradas

            Creando estructura de proyecto...
            ✅ Proyecto creado
```

### 4. Fase 1 - Objetivo

```
Orquestador: FASE 1: DEFINICIÓN DEL OBJETIVO
            [Asume rol de agente_objetivo_schema]

Agente: ¿Qué objetivo buscas?

Usuario: Analizar contratos de proveedores para identificar
        cláusulas de pago y penalizaciones

Agente: [Refina el objetivo]
       [Valida que sea específico]
       [Guarda en objetivo_validado.md]

Orquestador: ✅ Fase 1 completada
            ¿Continuar? s
```

### 5. Fase 2 - Schema

```
Orquestador: FASE 2: DISEÑO DE SCHEMA
            [Lee objetivo_validado.md]
            [Asume rol de agente_diseño_schema]

Agente: [Diseña schema basado en el objetivo]
       [Propone nodos: Contrato, Proveedor, Cláusula]
       [Propone relaciones: FIRMADO_CON, CONTIENE]
       [Pide aprobación]

Usuario: [Aprueba o ajusta]

Agente: [Guarda schema_diseñado.json]

Orquestador: ✅ Fase 2 completada
            ¿Continuar? s
```

### 6. Fases Siguientes

El orquestador continúa con:
- Ingesta de datos
- Depuración (opcional)
- Pre-procesamiento (opcional)
- BD Vectorial
- Asistente GraphRAG

## Archivos Generados

### Al crear un proyecto:

- `proyectos/<nombre>/config/proyecto.json`
- `proyectos/<nombre>/logs/historial.json`
- Estructura completa de directorios

### Durante las fases:

- `resultados/objetivo_validado.md` (Fase 1)
- `resultados/schema_diseñado.json` (Fase 2)
- `scripts/*.py` (Scripts generados por cada fase)
- `logs/*.json` (Logs de ejecución)

## Solución de Problemas

### "No encuentro el archivo .env"

**Solución:**
```bash
cp .env.example .env
nano .env  # Completa las variables
```

### "Faltan variables en .env"

El orquestador te dirá exactamente qué variables faltan:
```
❌ NEO4J_PASSWORD = (FALTA)
❌ CSV_DIR = (FALTA)

Para configurarlas, edita .env y agrega:
  NEO4J_PASSWORD=tu_password
  CSV_DIR=./data/csv/
```

### "No puedo continuar un proyecto"

Verifica que exista:
```bash
ls proyectos/<nombre>/config/proyecto.json
```

Si no existe, el proyecto está corrupto. Crea uno nuevo.

### "Los subagentes no se invocan"

Asegúrate de que los archivos .md de los subagentes existan:
```bash
ls agente_*.md
```

## Mejores Prácticas

### 1. Un Proyecto por Objetivo
No mezcles múltiples objetivos en un mismo proyecto.

### 2. Nombres Descriptivos
Usa nombres claros para proyectos:
- ✅ `contratos_proveedores_2024`
- ✅ `normativas_pami`
- ❌ `proyecto1`
- ❌ `test`

### 3. Valida Configuración Primero
Siempre usa opción "4. Verificar configuración" antes de crear un proyecto.

### 4. Revisa el Historial
Usa el comando `historial` para ver qué se hizo en sesiones anteriores.

### 5. Backup de Proyectos
Haz backup de la carpeta `proyectos/` regularmente.

## Extensión del Sistema

### Agregar una Nueva Fase

Para agregar una nueva fase al ciclo:

1. **Crea el archivo del subagente:**
   ```
   agente_nueva_fase.md
   ```

2. **Edita `agente_orquestador.md`:**
   - Agrégala a la tabla de fases (TEXTO o CSV)
   - Especifica si es opcional

3. **El orquestador la incluirá automáticamente**

## Documentación Relacionada

- **Especificación Técnica:** `agente_orquestador.md`
- **Inicio Rápido:** `INICIO_RAPIDO.md`
- **Template de Configuración:** `.env.example`
- **Subagentes Individuales:** `agente_*.md`

## Preguntas Frecuentes

**P: ¿Necesito ejecutar un script?**
R: No. El orquestador es un subagente que invocas en la conversación.

**P: ¿Cómo invoco al orquestador?**
R: Di: "Lee agente_orquestador.md y asume ese rol"

**P: ¿Puedo tener múltiples proyectos?**
R: Sí, puedes crear tantos proyectos como quieras.

**P: ¿Se guardan los proyectos entre sesiones?**
R: Sí, todo se guarda en `proyectos/<nombre>/`

**P: ¿Puedo cambiar el .env después de crear un proyecto?**
R: Sí, pero deberás repetir las fases que dependan de esos valores.

**P: ¿Qué pasa si interrumpo en medio de una fase?**
R: El estado se guarda. Puedes continuar desde donde lo dejaste.

---

**Versión:** 2.0.0 (Subagente)
**Última actualización:** 2025-12-20
