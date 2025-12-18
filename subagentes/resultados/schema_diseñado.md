# SCHEMA DE GRAFO DE CONOCIMIENTO

**Fecha:** 2025-12-16
**Dominio:** healthcare (PAMI - Instituto Nacional de Servicios Sociales para Jubilados y Pensionados)
**Versión del Schema:** 1.0

---

## 1. SCHEMA SIMPLIFICADO (Vista Ejecutiva)

### Nodos Core:
- `Prestacion` - Servicios y productos provistos por PAMI
- `Normativa` - Resoluciones y disposiciones administrativas
- `Articulo` - Componentes internos de normativas
- `MarcoLegal` - Leyes y decretos que fundamentan normativas
- `CriterioCalidad` - Requisitos legales según Ley 19.549
- `Inconsistencia` - Problemas detectados en normativas
- `Evidencia` - Provenance de datos extraídos

### Relaciones Core:
- `REGULADA_POR`: (Prestacion) → (Normativa)
- `CONTIENE`: (Normativa) → (Articulo)
- `FUNDAMENTADA_EN`: (Normativa) → (MarcoLegal)
- `CUMPLE_CON`: (Normativa) → (CriterioCalidad)
- `TIENE_INCONSISTENCIA`: (Normativa/Prestacion) → (Inconsistencia)
- `SUPERPONE_CON`: (Normativa) → (Normativa)
- `DEROGA`: (Normativa) → (Normativa)
- `RESPALDA`: (Cualquier nodo) → (Evidencia)

### Diagrama Visual:
```
                    ┌─────────────┐
                    │ MarcoLegal  │
                    │ (Ley 19.549)│
                    └──────┬──────┘
                           │ FUNDAMENTADA_EN
                           ↓
┌────────────┐      ┌─────────────┐      ┌──────────────┐
│ Prestacion │─────→│  Normativa  │─────→│ Articulo     │
└────────────┘      └─────────────┘      └──────────────┘
     │ REGULADA_POR    │  │  │  │
     │                 │  │  │  └──→ CUMPLE_CON → CriterioCalidad
     │                 │  │  │
     │                 │  │  └──→ SUPERPONE_CON → Normativa
     │                 │  │
     │                 │  └──→ DEROGA → Normativa
     │                 │
     └─→ TIENE_INCONSISTENCIA → Inconsistencia
                       │
                       └──→ RESPALDA → Evidencia
```

---

## 2. NODOS DETALLADOS

### Nodo: (:Prestacion)
**Descripción:** Representa servicios, productos o tratamientos que PAMI provee a sus afiliados (pañales, traslados, prótesis, medicamentos, consultas médicas, etc.)

**Regla de Identidad (Clave Compuesta):**
- Propiedades: `(codigo_prestacion, tipo_prestacion)`
- Garantiza unicidad semántica

**Propiedades:**

*Propiedades de Identidad:*
- `codigo_prestacion`
  - Tipo: String
  - Parte de identidad: SÍ
  - Obligatoria: SÍ
  - Ejemplo: "PREST-2024-001"
  - Descripción: Código único de la prestación en el nomenclador PAMI

- `tipo_prestacion`
  - Tipo: String
  - Parte de identidad: SÍ
  - Obligatoria: SÍ
  - Valores permitidos: ["medicamento", "protesis", "traslado", "consulta", "insumo", "tratamiento", "otro"]
  - Ejemplo: "protesis"

*Propiedades Descriptivas:*
- `nombre`
  - Tipo: String
  - Obligatoria: SÍ
  - Ejemplo: "Prótesis auditiva digital"

- `descripcion`
  - Tipo: String
  - Obligatoria: No
  - Indexada: Sí
  - Ejemplo: "Prótesis auditiva retroauricular digital para hipoacusia moderada a severa"

- `categoria`
  - Tipo: String
  - Obligatoria: No
  - Ejemplo: "Ortopedia y Traumatología"

- `subcategoria`
  - Tipo: String
  - Obligatoria: No
  - Ejemplo: "Audiología"

- `estado`
  - Tipo: String
  - Obligatoria: SÍ
  - Valores permitidos: ["activa", "suspendida", "descontinuada"]
  - Default: "activa"

*Propiedades de Sistema:*
- `schema_version`: String - Versión del schema (default: "1.0")
- `created_at`: DateTime - Timestamp de creación
- `updated_at`: DateTime - Última actualización

**Ejemplo de Instancia:**
```json
{
  "codigo_prestacion": "PREST-AUDIO-2024-15",
  "tipo_prestacion": "protesis",
  "nombre": "Prótesis auditiva digital",
  "descripcion": "Prótesis auditiva retroauricular digital",
  "categoria": "Ortopedia",
  "subcategoria": "Audiología",
  "estado": "activa",
  "schema_version": "1.0",
  "created_at": "2024-12-16T10:00:00Z",
  "updated_at": "2024-12-16T10:00:00Z"
}
```

**Constraints:**
```cypher
CREATE CONSTRAINT unique_prestacion FOR (p:Prestacion)
REQUIRE (p.codigo_prestacion, p.tipo_prestacion) IS UNIQUE
```

**Índices:**
```cypher
CREATE INDEX FOR (p:Prestacion) ON (p.nombre);
CREATE INDEX FOR (p:Prestacion) ON (p.descripcion);
CREATE INDEX FOR (p:Prestacion) ON (p.estado);
CREATE INDEX FOR (p:Prestacion) ON (p.categoria);
```

---

### Nodo: (:Normativa)
**Descripción:** Resoluciones, disposiciones y actos administrativos de PAMI que regulan prestaciones, procedimientos y estructura organizacional

**Regla de Identidad (Clave Compuesta):**
- Propiedades: `(tipo, numero, anio, emisor)`
- Garantiza unicidad semántica

**Propiedades:**

*Propiedades de Identidad:*
- `tipo`
  - Tipo: String
  - Parte de identidad: SÍ
  - Obligatoria: SÍ
  - Valores permitidos: ["Resolución", "Disposición", "Circular", "Convenio"]
  - Ejemplo: "Resolución"

- `numero`
  - Tipo: String
  - Parte de identidad: SÍ
  - Obligatoria: SÍ
  - Ejemplo: "2563"

- `anio`
  - Tipo: Integer
  - Parte de identidad: SÍ
  - Obligatoria: SÍ
  - Ejemplo: 2024

- `emisor`
  - Tipo: String
  - Parte de identidad: SÍ
  - Obligatoria: SÍ
  - Ejemplo: "INSSJP-DE"

*Propiedades Descriptivas:*
- `titulo`
  - Tipo: String
  - Obligatoria: No
  - Indexada: Sí
  - Ejemplo: "Aprobación del Nomenclador de Prestaciones Audiológicas"

- `fecha_emision`
  - Tipo: Date
  - Obligatoria: SÍ
  - Formato: YYYY-MM-DD
  - Ejemplo: "2024-09-21"

- `fecha_vigencia_desde`
  - Tipo: Date
  - Obligatoria: No
  - Ejemplo: "2024-10-01"

- `fecha_vigencia_hasta`
  - Tipo: Date
  - Obligatoria: No
  - Ejemplo: null (vigente)

- `estado`
  - Tipo: String
  - Obligatoria: SÍ
  - Valores permitidos: ["Vigente", "Derogada", "Suspendida", "Modificada"]
  - Default: "Vigente"

- `tiene_fundamentacion_legal`
  - Tipo: Boolean
  - Obligatoria: SÍ
  - Descripción: ¿Cita explícitamente el marco legal (Ley 19.549, ley INSSJP)?

- `alcance`
  - Tipo: String
  - Obligatoria: No
  - Ejemplo: "Nacional - Todas las UGL"

*Propiedades de Sistema:*
- `schema_version`: String - Versión del schema
- `created_at`: DateTime - Timestamp de creación
- `updated_at`: DateTime - Última actualización

**Ejemplo de Instancia:**
```json
{
  "tipo": "Resolución",
  "numero": "2563",
  "anio": 2024,
  "emisor": "INSSJP-DE",
  "titulo": "Aprobación del Nomenclador de Prestaciones Audiológicas",
  "fecha_emision": "2024-09-21",
  "fecha_vigencia_desde": "2024-10-01",
  "fecha_vigencia_hasta": null,
  "estado": "Vigente",
  "tiene_fundamentacion_legal": true,
  "alcance": "Nacional",
  "schema_version": "1.0",
  "created_at": "2024-12-16T10:00:00Z",
  "updated_at": "2024-12-16T10:00:00Z"
}
```

**Constraints:**
```cypher
CREATE CONSTRAINT unique_normativa FOR (n:Normativa)
REQUIRE (n.tipo, n.numero, n.anio, n.emisor) IS UNIQUE
```

**Índices:**
```cypher
CREATE INDEX FOR (n:Normativa) ON (n.titulo);
CREATE INDEX FOR (n:Normativa) ON (n.estado);
CREATE INDEX FOR (n:Normativa) ON (n.fecha_emision);
CREATE INDEX FOR (n:Normativa) ON (n.anio);
```

---

### Nodo: (:Articulo)
**Descripción:** Componente interno de una normativa (artículo, inciso, anexo) que contiene disposiciones específicas

**Regla de Identidad (Clave Compuesta):**
- Propiedades: `(normativa_id, tipo_componente, numero_componente)`
- Garantiza unicidad dentro de cada normativa

**Propiedades:**

*Propiedades de Identidad:*
- `normativa_id`
  - Tipo: String
  - Parte de identidad: SÍ
  - Obligatoria: SÍ
  - Descripción: ID compuesto de la normativa padre
  - Ejemplo: "Resolución-2563-2024-INSSJP-DE"

- `tipo_componente`
  - Tipo: String
  - Parte de identidad: SÍ
  - Obligatoria: SÍ
  - Valores permitidos: ["Artículo", "Inciso", "Anexo", "Capítulo"]
  - Ejemplo: "Artículo"

- `numero_componente`
  - Tipo: String
  - Parte de identidad: SÍ
  - Obligatoria: SÍ
  - Ejemplo: "5" o "a)" o "I"

*Propiedades Descriptivas:*
- `texto_contenido`
  - Tipo: String
  - Obligatoria: No
  - Descripción: Texto literal del artículo/inciso/anexo

- `orden`
  - Tipo: Integer
  - Obligatoria: No
  - Descripción: Orden de aparición en la normativa

*Propiedades de Sistema:*
- `schema_version`: String
- `created_at`: DateTime
- `updated_at`: DateTime

**Ejemplo de Instancia:**
```json
{
  "normativa_id": "Resolución-2563-2024-INSSJP-DE",
  "tipo_componente": "Artículo",
  "numero_componente": "5",
  "texto_contenido": "Establécese el nomenclador de prestaciones audiológicas...",
  "orden": 5,
  "schema_version": "1.0",
  "created_at": "2024-12-16T10:00:00Z",
  "updated_at": "2024-12-16T10:00:00Z"
}
```

**Constraints:**
```cypher
CREATE CONSTRAINT unique_articulo FOR (a:Articulo)
REQUIRE (a.normativa_id, a.tipo_componente, a.numero_componente) IS UNIQUE
```

---

### Nodo: (:MarcoLegal)
**Descripción:** Leyes y decretos nacionales que constituyen el marco legal obligatorio para normativas administrativas

**Regla de Identidad (Clave Compuesta):**
- Propiedades: `(tipo_legal, numero_legal)`
- Garantiza unicidad semántica

**Propiedades:**

*Propiedades de Identidad:*
- `tipo_legal`
  - Tipo: String
  - Parte de identidad: SÍ
  - Obligatoria: SÍ
  - Valores permitidos: ["Ley", "Decreto", "Ley-Decreto"]
  - Ejemplo: "Ley"

- `numero_legal`
  - Tipo: String
  - Parte de identidad: SÍ
  - Obligatoria: SÍ
  - Ejemplo: "19.549"

*Propiedades Descriptivas:*
- `nombre`
  - Tipo: String
  - Obligatoria: SÍ
  - Ejemplo: "Ley de Procedimientos Administrativos"

- `fecha_promulgacion`
  - Tipo: Date
  - Obligatoria: No

- `ambito`
  - Tipo: String
  - Obligatoria: No
  - Valores permitidos: ["Nacional", "Provincial", "Municipal"]
  - Default: "Nacional"

- `resumen`
  - Tipo: String
  - Obligatoria: No

*Propiedades de Sistema:*
- `schema_version`: String
- `created_at`: DateTime
- `updated_at`: DateTime

**Ejemplo de Instancia:**
```json
{
  "tipo_legal": "Ley",
  "numero_legal": "19.549",
  "nombre": "Ley de Procedimientos Administrativos",
  "fecha_promulgacion": "1972-04-03",
  "ambito": "Nacional",
  "resumen": "Regula los procedimientos administrativos del Estado argentino",
  "schema_version": "1.0",
  "created_at": "2024-12-16T10:00:00Z",
  "updated_at": "2024-12-16T10:00:00Z"
}
```

**Constraints:**
```cypher
CREATE CONSTRAINT unique_marcolegal FOR (m:MarcoLegal)
REQUIRE (m.tipo_legal, m.numero_legal) IS UNIQUE
```

---

### Nodo: (:CriterioCalidad)
**Descripción:** Requisitos de calidad administrativa que deben cumplir las normativas según Ley 19.549

**Regla de Identidad (Clave Compuesta):**
- Propiedades: `(codigo_criterio)`
- Identificador único del criterio

**Propiedades:**

*Propiedades de Identidad:*
- `codigo_criterio`
  - Tipo: String
  - Parte de identidad: SÍ
  - Obligatoria: SÍ
  - Ejemplo: "CRIT-FUND-LEG"

*Propiedades Descriptivas:*
- `nombre`
  - Tipo: String
  - Obligatoria: SÍ
  - Ejemplo: "Fundamentación Legal Explícita"

- `descripcion`
  - Tipo: String
  - Obligatoria: SÍ
  - Ejemplo: "La normativa debe citar explícitamente la ley habilitante"

- `categoria`
  - Tipo: String
  - Obligatoria: SÍ
  - Valores permitidos: ["Forma", "Competencia", "Motivación", "Procedimiento", "Vigencia"]
  - Ejemplo: "Motivación"

- `obligatorio`
  - Tipo: Boolean
  - Obligatoria: SÍ
  - Default: true

*Propiedades de Sistema:*
- `schema_version`: String
- `created_at`: DateTime
- `updated_at`: DateTime

**Ejemplo de Instancia:**
```json
{
  "codigo_criterio": "CRIT-FUND-LEG",
  "nombre": "Fundamentación Legal Explícita",
  "descripcion": "La normativa debe citar la ley habilitante (Ley 19.549, ley INSSJP)",
  "categoria": "Motivación",
  "obligatorio": true,
  "schema_version": "1.0",
  "created_at": "2024-12-16T10:00:00Z",
  "updated_at": "2024-12-16T10:00:00Z"
}
```

**Constraints:**
```cypher
CREATE CONSTRAINT unique_criterio FOR (c:CriterioCalidad)
REQUIRE (c.codigo_criterio) IS UNIQUE
```

---

### Nodo: (:Inconsistencia)
**Descripción:** Problemas detectados en normativas o prestaciones (faltantes, superposiciones, mal definiciones)

**Regla de Identidad (Clave Compuesta):**
- Propiedades: `(id_inconsistencia)` - UUID generado
- Identificador único de la inconsistencia

**Propiedades:**

*Propiedades de Identidad:*
- `id_inconsistencia`
  - Tipo: String (UUID)
  - Parte de identidad: SÍ
  - Obligatoria: SÍ
  - Ejemplo: "INC-2024-001-UUID"

*Propiedades Descriptivas:*
- `tipo_inconsistencia`
  - Tipo: String
  - Obligatoria: SÍ
  - Valores permitidos: ["Faltante", "Superposición", "MalDefinida", "Contradicción", "Ambigüedad"]
  - Ejemplo: "Faltante"

- `descripcion`
  - Tipo: String
  - Obligatoria: SÍ
  - Ejemplo: "Prestación sin normativa que la respalde"

- `severidad`
  - Tipo: String
  - Obligatoria: SÍ
  - Valores permitidos: ["Crítica", "Alta", "Media", "Baja"]
  - Ejemplo: "Alta"

- `fecha_deteccion`
  - Tipo: DateTime
  - Obligatoria: SÍ

- `estado_resolucion`
  - Tipo: String
  - Obligatoria: SÍ
  - Valores permitidos: ["Detectada", "EnRevisión", "Resuelta", "Descartada"]
  - Default: "Detectada"

*Propiedades de Sistema:*
- `schema_version`: String
- `created_at`: DateTime
- `updated_at`: DateTime

**Ejemplo de Instancia:**
```json
{
  "id_inconsistencia": "INC-2024-001-a3f5d8c2",
  "tipo_inconsistencia": "Faltante",
  "descripcion": "Prestación 'Traslado en ambulancia' no tiene normativa vigente que la respalde",
  "severidad": "Alta",
  "fecha_deteccion": "2024-12-16T10:00:00Z",
  "estado_resolucion": "Detectada",
  "schema_version": "1.0",
  "created_at": "2024-12-16T10:00:00Z",
  "updated_at": "2024-12-16T10:00:00Z"
}
```

**Constraints:**
```cypher
CREATE CONSTRAINT unique_inconsistencia FOR (i:Inconsistencia)
REQUIRE (i.id_inconsistencia) IS UNIQUE
```

**Índices:**
```cypher
CREATE INDEX FOR (i:Inconsistencia) ON (i.tipo_inconsistencia);
CREATE INDEX FOR (i:Inconsistencia) ON (i.severidad);
CREATE INDEX FOR (i:Inconsistencia) ON (i.estado_resolucion);
```

---

## 3. NODO ESPECIAL: EVIDENCIA (Provenance)

### Nodo: (:Evidencia)
**Descripción:** Trazabilidad de datos extraídos - registra la fuente y contexto de cada dato en el grafo

**Propiedades:**
- `id`: String (UUID) - Identificador único
- `doc_id`: String - Identificador del documento fuente
- `source_type`: String - Valores: "pdf", "url", "scraping", "api", "manual"
- `source_path`: String - Ruta o URL del documento
- `page`: Integer - Número de página (si aplica)
- `paragraph_id`: String - ID del párrafo extraído
- `text_fragment`: String - Fragmento literal extraído (máx 500 chars)
- `extraction_date`: DateTime - Timestamp de extracción
- `extractor_version`: String - Versión del sistema extractor
- `confidence_score`: Float (0.0-1.0) - Confianza en la extracción
- `schema_version`: String - Versión del schema

**Ejemplo de Instancia:**
```json
{
  "id": "EVID-2024-001-uuid",
  "doc_id": "RESOL-2024-2563-INSSJP",
  "source_type": "pdf",
  "source_path": "contexto_dominio/RESOL-2024-2563-INSSJP-DE#INSSJP.pdf",
  "page": 5,
  "paragraph_id": "p5-3",
  "text_fragment": "ARTÍCULO 5°.- Apruébase el Nomenclador de Prestaciones...",
  "extraction_date": "2024-12-16T16:20:00Z",
  "extractor_version": "pdf_chunk_processor_v1.0",
  "confidence_score": 0.95,
  "schema_version": "1.0"
}
```

**Relación:** `RESPALDA`
- Conecta cualquier nodo/dato extraído con su Evidencia
- Ejemplo: `(:Normativa)-[:RESPALDA]->(:Evidencia)`

**Constraints:**
```cypher
CREATE CONSTRAINT unique_evidencia FOR (e:Evidencia)
REQUIRE (e.id) IS UNIQUE
```

---

## 4. RELACIONES DETALLADAS

### Relación: [:REGULADA_POR]
**Conecta:** (:Prestacion) → (:Normativa)
**Descripción:** Indica qué normativa regula o autoriza una prestación

**Propiedades de la Relación:**
- `fecha_desde`: Date - Desde cuándo aplica esta regulación
- `fecha_hasta`: Date - Hasta cuándo (null si vigente)
- `alcance`: String - Alcance de la regulación ("Total", "Parcial", "Condicional")
- `articulo_referencia`: String - Artículo específico que regula

**Ejemplo:**
```cypher
(:Prestacion {codigo_prestacion: "PREST-AUDIO-2024-15"})
-[:REGULADA_POR {
  fecha_desde: "2024-10-01",
  fecha_hasta: null,
  alcance: "Total",
  articulo_referencia: "Artículo 5"
}]->
(:Normativa {tipo: "Resolución", numero: "2563", anio: 2024})
```

---

### Relación: [:CONTIENE]
**Conecta:** (:Normativa) → (:Articulo)
**Descripción:** Indica que una normativa contiene un artículo/inciso/anexo

**Propiedades de la Relación:**
- `orden`: Integer - Orden de aparición

**Ejemplo:**
```cypher
(:Normativa {tipo: "Resolución", numero: "2563"})
-[:CONTIENE {orden: 5}]->
(:Articulo {tipo_componente: "Artículo", numero_componente: "5"})
```

---

### Relación: [:FUNDAMENTADA_EN]
**Conecta:** (:Normativa) → (:MarcoLegal)
**Descripción:** Indica el marco legal en que se fundamenta una normativa

**Propiedades de la Relación:**
- `tipo_fundamentacion`: String - Valores: "Explícita", "Implícita", "Por_competencia"
- `articulo_citado`: String - Artículo específico de la ley citado

**Ejemplo:**
```cypher
(:Normativa {tipo: "Resolución", numero: "2563"})
-[:FUNDAMENTADA_EN {
  tipo_fundamentacion: "Explícita",
  articulo_citado: "Art. 7 inc. b)"
}]->
(:MarcoLegal {tipo_legal: "Ley", numero_legal: "19.549"})
```

---

### Relación: [:CUMPLE_CON]
**Conecta:** (:Normativa) → (:CriterioCalidad)
**Descripción:** Indica si una normativa cumple con un criterio de calidad administrativa

**Propiedades de la Relación:**
- `cumple`: Boolean - true si cumple, false si no cumple
- `evaluacion_detalle`: String - Detalles de la evaluación
- `fecha_evaluacion`: DateTime - Cuándo se evaluó

**Ejemplo:**
```cypher
(:Normativa {tipo: "Resolución", numero: "2563"})
-[:CUMPLE_CON {
  cumple: true,
  evaluacion_detalle: "Cita explícitamente Ley 19.549 en considerandos",
  fecha_evaluacion: "2024-12-16T10:00:00Z"
}]->
(:CriterioCalidad {codigo_criterio: "CRIT-FUND-LEG"})
```

---

### Relación: [:TIENE_INCONSISTENCIA]
**Conecta:** (:Prestacion/:Normativa) → (:Inconsistencia)
**Descripción:** Vincula una prestación o normativa con una inconsistencia detectada

**Propiedades de la Relación:**
- `fecha_deteccion`: DateTime

**Ejemplo:**
```cypher
(:Prestacion {codigo_prestacion: "PREST-TRASL-001"})
-[:TIENE_INCONSISTENCIA {fecha_deteccion: "2024-12-16T10:00:00Z"}]->
(:Inconsistencia {tipo_inconsistencia: "Faltante", descripcion: "Sin normativa"})
```

---

### Relación: [:SUPERPONE_CON]
**Conecta:** (:Normativa) → (:Normativa)
**Descripción:** Indica que dos normativas regulan lo mismo con reglas diferentes (conflicto)

**Propiedades de la Relación:**
- `tipo_superposicion`: String - Valores: "Total", "Parcial", "Contradictoria"
- `ambito_superposicion`: String - Qué aspecto se superpone
- `fecha_deteccion`: DateTime
- `severidad`: String - Valores: "Crítica", "Alta", "Media", "Baja"

**Ejemplo:**
```cypher
(:Normativa {tipo: "Resolución", numero: "2563", anio: 2024})
-[:SUPERPONE_CON {
  tipo_superposicion: "Parcial",
  ambito_superposicion: "Prestaciones audiológicas",
  fecha_deteccion: "2024-12-16T10:00:00Z",
  severidad: "Media"
}]->
(:Normativa {tipo: "Resolución", numero: "1500", anio: 2023})
```

---

### Relación: [:DEROGA]
**Conecta:** (:Normativa) → (:Normativa)
**Descripción:** Indica que una normativa deroga (anula) otra anterior

**Propiedades de la Relación:**
- `fecha_vigencia`: Date - Desde cuándo aplica la derogación
- `alcance`: String - Valores: "Total", "Parcial"
- `articulos_derogados`: String - Si es parcial, qué artículos se derogan

**Ejemplo:**
```cypher
(:Normativa {tipo: "Resolución", numero: "2563", anio: 2024})
-[:DEROGA {
  fecha_vigencia: "2024-10-01",
  alcance: "Parcial",
  articulos_derogados: "Art. 3, Art. 5"
}]->
(:Normativa {tipo: "Resolución", numero: "1800", anio: 2022})
```

---

### Relación: [:MODIFICA]
**Conecta:** (:Normativa) → (:Normativa)
**Descripción:** Indica que una normativa modifica otra sin derogarla completamente

**Propiedades de la Relación:**
- `fecha_vigencia`: Date
- `tipo_modificacion`: String - Valores: "Ampliación", "Restricción", "Aclaración"
- `articulos_modificados`: String

**Ejemplo:**
```cypher
(:Normativa {tipo: "Resolución", numero: "2562", anio: 2024})
-[:MODIFICA {
  fecha_vigencia: "2024-09-01",
  tipo_modificacion: "Ampliación",
  articulos_modificados: "Art. 2"
}]->
(:Normativa {tipo: "Resolución", numero: "1200", anio: 2021})
```

---

### Relación: [:RESPALDA]
**Conecta:** (Cualquier nodo) → (:Evidencia)
**Descripción:** Vincula cualquier dato extraído con su evidencia documental (provenance)

**Propiedades de la Relación:**
- Ninguna (la evidencia está en el nodo Evidencia)

**Ejemplo:**
```cypher
(:Normativa {tipo: "Resolución", numero: "2563"})
-[:RESPALDA]->
(:Evidencia {source_path: "RESOL-2024-2563-INSSJP-DE#INSSJP.pdf", page: 1})
```

---

## 5. REGLAS DE VALIDACIÓN

### Para :Prestacion:
- `codigo_prestacion` debe seguir formato: "PREST-[CATEGORIA]-[AÑO]-[NUM]"
- `tipo_prestacion` debe ser uno de los valores permitidos
- `estado` debe ser uno de: ["activa", "suspendida", "descontinuada"]
- Debe tener al menos una relación `REGULADA_POR` a una `:Normativa` vigente (si no, es inconsistencia)

### Para :Normativa:
- `tipo` debe ser uno de: ["Resolución", "Disposición", "Circular", "Convenio"]
- `fecha_emision` debe ser válida y en el pasado
- Si `fecha_vigencia_hasta` existe, debe ser posterior a `fecha_vigencia_desde`
- Si `estado` = "Derogada", debe existir relación `DEROGA` desde otra normativa
- `tiene_fundamentacion_legal` = true DEBE implicar existencia de relación `FUNDAMENTADA_EN`

### Para :Articulo:
- `normativa_id` debe corresponder a una `:Normativa` existente
- `tipo_componente` debe ser uno de: ["Artículo", "Inciso", "Anexo", "Capítulo"]
- `numero_componente` debe ser formato válido según `tipo_componente`

### Para :MarcoLegal:
- `tipo_legal` debe ser uno de: ["Ley", "Decreto", "Ley-Decreto"]
- `numero_legal` debe seguir formato argentino (ej: "19.549", "50/2019")
- `ambito` debe ser "Nacional" (por ahora)

### Para :CriterioCalidad:
- `categoria` debe ser uno de: ["Forma", "Competencia", "Motivación", "Procedimiento", "Vigencia"]
- `obligatorio` debe ser boolean

### Para :Inconsistencia:
- `tipo_inconsistencia` debe ser uno de: ["Faltante", "Superposición", "MalDefinida", "Contradicción", "Ambigüedad"]
- `severidad` debe ser uno de: ["Crítica", "Alta", "Media", "Baja"]
- `estado_resolucion` debe ser uno de: ["Detectada", "EnRevisión", "Resuelta", "Descartada"]

---

## 6. LOG DE VERSIONADO DEL SCHEMA

**Versión Actual:** 1.0

**Historial de Cambios:**

| Versión | Fecha | Cambios | Tipo |
|---------|-------|---------|------|
| 1.0 | 2024-12-16 | Schema inicial diseñado para análisis de inconsistencias normativas PAMI | CREACIÓN |

**Reglas de Versionado:**
- **Incremento menor (1.0 → 1.1):** Agregar nodos/relaciones/propiedades opcionales sin romper consultas existentes
- **Incremento mayor (1.x → 2.0):** Cambios que rompen compatibilidad (renombrar nodos, eliminar propiedades obligatorias, cambiar tipos)
- **NUNCA borrar, solo deprecar:** Si una propiedad ya no se usa, marcarla como `deprecated` pero mantenerla

**Compatibilidad:**
- Nodos de diferentes versiones pueden coexistir en el mismo grafo
- Filtrar por `schema_version` si necesario
- Queries deben ser defensivas y no asumir existencia de propiedades opcionales

---

## 7. EJEMPLOS DE PATRONES DE CONSULTA

Basados en las consultas esperadas del objetivo:

### Consulta 1: ¿Cuáles son las normativas definidas por PAMI sobre una prestación específica?
```cypher
MATCH (p:Prestacion {nombre: "Pañales"})-[r:REGULADA_POR]->(n:Normativa)
WHERE n.estado = "Vigente"
RETURN n.tipo, n.numero, n.anio, n.titulo, r.articulo_referencia, n.fecha_vigencia_desde
ORDER BY n.anio DESC, n.numero DESC
```

### Consulta 2: ¿Las normativas de una prestación cumplen con criterios de calidad administrativa?
```cypher
MATCH (p:Prestacion {codigo_prestacion: "PREST-TRASL-001"})-[:REGULADA_POR]->(n:Normativa)
MATCH (n)-[c:CUMPLE_CON]->(crit:CriterioCalidad)
WHERE crit.obligatorio = true
RETURN n.tipo, n.numero, n.anio,
       crit.nombre, c.cumple, c.evaluacion_detalle
ORDER BY c.cumple ASC
```

### Consulta 3: ¿Hay inconsistencias en las normativas de una prestación?
```cypher
MATCH (p:Prestacion {nombre: "Pañales"})
OPTIONAL MATCH (p)-[:REGULADA_POR]->(n:Normativa)
OPTIONAL MATCH (p)-[r:TIENE_INCONSISTENCIA]->(inc:Inconsistencia)
RETURN p.codigo_prestacion, p.nombre,
       COUNT(DISTINCT n) AS normativas_count,
       COLLECT(DISTINCT inc.tipo_inconsistencia) AS inconsistencias,
       COLLECT(DISTINCT inc.descripcion) AS detalles_inconsistencias
```

### Consulta 4: ¿Qué prestaciones tienen faltantes normativos?
```cypher
MATCH (p:Prestacion)
WHERE NOT EXISTS {
  MATCH (p)-[:REGULADA_POR]->(:Normativa {estado: "Vigente"})
}
RETURN p.codigo_prestacion, p.nombre, p.tipo_prestacion, p.categoria
ORDER BY p.tipo_prestacion, p.categoria
```

### Consulta 5: ¿Qué normativas tienen superposición entre sí?
```cypher
MATCH (n1:Normativa)-[s:SUPERPONE_CON]->(n2:Normativa)
WHERE n1.estado = "Vigente" AND n2.estado = "Vigente"
RETURN n1.tipo, n1.numero, n1.anio,
       n2.tipo, n2.numero, n2.anio,
       s.tipo_superposicion, s.ambito_superposicion, s.severidad
ORDER BY s.severidad DESC
```

### Consulta 6: ¿Qué normativas no citan el marco legal obligatorio?
```cypher
MATCH (n:Normativa)
WHERE n.estado = "Vigente"
  AND NOT EXISTS {
    MATCH (n)-[:FUNDAMENTADA_EN]->(:MarcoLegal {numero_legal: "19.549"})
  }
RETURN n.tipo, n.numero, n.anio, n.titulo, n.fecha_emision
ORDER BY n.anio DESC
```

### Consulta 7: ¿Qué prestaciones están mal definidas (normativas ambiguas)?
```cypher
MATCH (p:Prestacion)-[:TIENE_INCONSISTENCIA]->(inc:Inconsistencia)
WHERE inc.tipo_inconsistencia IN ["MalDefinida", "Ambigüedad", "Contradicción"]
  AND inc.estado_resolucion = "Detectada"
RETURN p.codigo_prestacion, p.nombre, p.tipo_prestacion,
       inc.tipo_inconsistencia, inc.descripcion, inc.severidad
ORDER BY inc.severidad DESC, p.tipo_prestacion
```

### Consulta 8: Cadena de derogaciones de una normativa
```cypher
MATCH path = (n:Normativa {tipo: "Resolución", numero: "2563", anio: 2024})
             -[:DEROGA*1..5]->(anterior:Normativa)
RETURN path,
       [node IN nodes(path) | node.tipo + " " + node.numero + "/" + node.anio] AS cadena_derogacion
```

### Consulta 9: Provenance - ¿De dónde salió esta normativa?
```cypher
MATCH (n:Normativa {tipo: "Resolución", numero: "2563", anio: 2024})
      -[:RESPALDA]->(e:Evidencia)
RETURN n.tipo, n.numero, n.anio,
       e.source_path, e.page, e.text_fragment,
       e.extraction_date, e.confidence_score
```

### Consulta 10: Dashboard de inconsistencias por tipo y severidad
```cypher
MATCH (inc:Inconsistencia)
WHERE inc.estado_resolucion IN ["Detectada", "EnRevisión"]
RETURN inc.tipo_inconsistencia,
       inc.severidad,
       COUNT(*) AS cantidad
ORDER BY inc.severidad DESC, cantidad DESC
```

---

## 8. ARCHIVOS FUENTE ANALIZADOS

Archivos del dominio que informaron este diseño:

### PDF 1: RESOL-2024-2563-INSSJP-DE#INSSJP.pdf
**Contribuyó:**
- Jerarquía: Resolución → Artículo → Anexo
- Entidades: PAMI, INSSJP, Decreto N° 50/2019, Ley N° 19.032
- Terminología: NOMENCLADOR, CODIGO, HIPOACUSIA, TRASLADOS, INTERNACIÓN, PRACTICAS
- Relaciones: (implícitas, no detectadas por regex)
- **Insights:** Estructura típica de resoluciones PAMI con anexos de nomencladores

### PDF 2: RESOL-2024-2562-INSSJP-DE#INSSJP.pdf
**Contribuyó:**
- Jerarquía: Resolución → Artículo → Anexos (I, II, III)
- Entidades: INSSJP, PAMI, Ley 19.032
- Terminología: UNIDADES LOCAL, DEPARTAMENTO, PRIMARIA, RESPONSABILIDAD, ACCIONES, GESTIÓN, GERENCIA, SUBGERENCIA, COORDINACIÓN
- Relaciones: ESTABLECE
- **Insights:** Resolución organizacional que define estructura de unidades de gestión local (UGL)

### PDF 3: RESOL-2024-2526-INSSJP-DE#INSSJP.pdf
**Contribuyó:**
- Jerarquía: Resolución → Artículo → Anexo I
- Entidades: INSSJP
- Terminología: CONVENIO, FARMACÉUTICA, FEDERACIÓN, JUBILADOS, PENSIONADOS, SERVICIOS SOCIALES, CNVAD
- Relaciones: ESTABLECE
- **Insights:** Convenio entre INSSJP y farmacéuticas - muestra patrón de normativas de convenios

**Patrones Comunes Detectados:**
- Todas las resoluciones siguen estructura: ARTÍCULO 1, 2, 3... → ANEXO I, II, III...
- Los anexos contienen detalles operativos (nomencladores, organigramas, convenios)
- Terminología especializada varía según tipo de normativa (prestaciones vs organizacional vs convenios)
- Relación ESTABLECE es común en todas

---

## 9. CRITERIOS DE CALIDAD ADMINISTRATIVA (Según Ley 19.549)

El schema incluye estos criterios como nodos `:CriterioCalidad` que deben cumplir las normativas:

| Código | Nombre | Descripción | Categoría |
|--------|--------|-------------|-----------|
| CRIT-FUND-LEG | Fundamentación Legal | Referencia explícita a ley habilitante | Motivación |
| CRIT-COMP-ORG | Competencia del Órgano | El emisor tiene competencia para emitir el acto | Competencia |
| CRIT-FORM-PROC | Forma y Procedimiento | Cumple con formas establecidas (numeración, fecha, firma) | Forma |
| CRIT-MOTIV-FACT | Motivación Fáctica | Explica razones de hecho que justifican el acto | Motivación |
| CRIT-VIG-TEMP | Vigencia Temporal | Define claramente desde cuándo rige | Vigencia |
| CRIT-ALCANCE | Alcance Definido | Especifica alcance y límites de aplicación | Procedimiento |
| CRIT-NO-CONTRA | No Contradicción | No contradice normativas superiores | Motivación |

Estos criterios permiten evaluar automáticamente la calidad de las normativas mediante relaciones `CUMPLE_CON`.

---

## 10. ESTRATEGIA DE DETECCIÓN DE INCONSISTENCIAS

El schema está diseñado para detectar inconsistencias mediante patrones de grafo:

### Tipo 1: Faltantes

**Faltante Normativo en Prestación:**
```cypher
// Prestaciones sin normativa vigente
MATCH (p:Prestacion)
WHERE NOT EXISTS {
  MATCH (p)-[:REGULADA_POR]->(:Normativa {estado: "Vigente"})
}
CREATE (inc:Inconsistencia {
  tipo_inconsistencia: "Faltante",
  descripcion: "Prestación sin normativa vigente que la respalde",
  severidad: "Alta"
})
CREATE (p)-[:TIENE_INCONSISTENCIA]->(inc)
```

**Normativa sin Fundamentación Legal:**
```cypher
// Normativas que no citan Ley 19.549
MATCH (n:Normativa {estado: "Vigente"})
WHERE NOT EXISTS {
  MATCH (n)-[:FUNDAMENTADA_EN]->(:MarcoLegal {numero_legal: "19.549"})
}
CREATE (inc:Inconsistencia {
  tipo_inconsistencia: "Faltante",
  descripcion: "Normativa sin fundamentación en Ley 19.549",
  severidad: "Media"
})
CREATE (n)-[:TIENE_INCONSISTENCIA]->(inc)
```

### Tipo 2: Superposiciones

**Múltiples Normativas Vigentes para Misma Prestación:**
```cypher
// Detectar prestaciones con múltiples normativas vigentes sin relación DEROGA
MATCH (p:Prestacion)-[:REGULADA_POR]->(n1:Normativa {estado: "Vigente"})
MATCH (p)-[:REGULADA_POR]->(n2:Normativa {estado: "Vigente"})
WHERE n1 <> n2
  AND NOT EXISTS { MATCH (n1)-[:DEROGA]->(n2) }
  AND NOT EXISTS { MATCH (n2)-[:DEROGA]->(n1) }
CREATE (inc:Inconsistencia {
  tipo_inconsistencia: "Superposición",
  descripcion: "Múltiples normativas vigentes regulan la misma prestación",
  severidad: "Alta"
})
CREATE (n1)-[:SUPERPONE_CON {severidad: "Alta"}]->(n2)
CREATE (p)-[:TIENE_INCONSISTENCIA]->(inc)
```

### Tipo 3: Mal Definidas

**Normativa no Cumple Criterios Obligatorios:**
```cypher
// Normativas que no cumplen con criterios obligatorios
MATCH (n:Normativa {estado: "Vigente"})
MATCH (crit:CriterioCalidad {obligatorio: true})
MATCH (n)-[c:CUMPLE_CON]->(crit)
WHERE c.cumple = false
CREATE (inc:Inconsistencia {
  tipo_inconsistencia: "MalDefinida",
  descripcion: "Normativa no cumple con criterio obligatorio: " + crit.nombre,
  severidad: "Media"
})
CREATE (n)-[:TIENE_INCONSISTENCIA]->(inc)
```

---

## 11. PRÓXIMOS PASOS PARA IMPLEMENTACIÓN

1. **Crear Constraints e Índices en Neo4j:**
   - Ejecutar todos los comandos `CREATE CONSTRAINT` y `CREATE INDEX` definidos

2. **Poblar Nodos de Referencia:**
   - Crear nodos `:MarcoLegal` (Ley 19.549, Ley 19.032, etc.)
   - Crear nodos `:CriterioCalidad` con los 7 criterios definidos

3. **Extraer y Cargar Datos de PDFs:**
   - Usar los resúmenes generados (`resumen_*.md`) como guía
   - Extraer normativas de los 3 PDFs procesados
   - Crear nodos `:Normativa`, `:Articulo`
   - Generar nodos `:Evidencia` para cada extracción

4. **Cargar Prestaciones:**
   - Definir catálogo de prestaciones PAMI
   - Crear nodos `:Prestacion`

5. **Establecer Relaciones:**
   - Vincular prestaciones con normativas (`REGULADA_POR`)
   - Vincular normativas con marco legal (`FUNDAMENTADA_EN`)
   - Crear relaciones de jerarquía (`CONTIENE`)

6. **Ejecutar Análisis de Inconsistencias:**
   - Correr queries de detección de faltantes
   - Correr queries de detección de superposiciones
   - Evaluar cumplimiento de criterios de calidad
   - Crear nodos `:Inconsistencia` y relaciones

7. **Validación y Refinamiento:**
   - Revisar inconsistencias detectadas con expertos de dominio
   - Ajustar severidades
   - Refinar reglas de detección

---

*Schema generado por Agente de Diseño Ontológico*
*Listo para implementación en Neo4j*
*Basado en análisis de 3 PDFs de normativas PAMI y objetivo de detección de inconsistencias*
