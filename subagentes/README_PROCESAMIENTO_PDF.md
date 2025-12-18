# Procesamiento Automático de PDFs para Análisis de Schema

## ¿Qué Problema Resuelve?

Cuando el agente de diseño de schema intenta leer PDFs grandes (>100KB), puede exceder el límite de contexto. Este sistema **procesa automáticamente los PDFs en chunks** y genera resúmenes compactos.

---

## Flujo de Trabajo Simple

### 1. Agrega tus PDFs
Coloca todos tus PDFs en la carpeta `contexto_dominio/`:
```
subagentes/
  ├── contexto_dominio/
  │   ├── RESOL-2024-2563-INSSJP-DE#INSSJP.pdf
  │   ├── ley_19549.pdf
  │   └── normativa_ejemplo.pdf
  └── process_all_pdfs.py
```

### 2. Ejecuta el Procesador Automático
```bash
cd subagentes
python process_all_pdfs.py
```

**Eso es todo!** El script:
- ✅ Detecta todos los PDFs en `contexto_dominio/`
- ✅ Identifica cuáles necesitan procesamiento (>100KB)
- ✅ Los procesa en chunks de 5 páginas
- ✅ Genera resúmenes compactos (`resumen_*.md`)
- ✅ **NO reprocesa** PDFs que ya tienen resumen

### 3. Ejecuta el Agente
El agente de diseño de schema ahora:
- Lee los resúmenes pequeños en lugar de los PDFs gigantes
- No excede límites de contexto
- Procesa información de TODO el documento

---

## Comandos Disponibles

### Procesamiento Normal (Recomendado)
```bash
python process_all_pdfs.py
```
Procesa solo los PDFs que no tienen resumen.

### Listar Resúmenes Disponibles
```bash
python process_all_pdfs.py --list
```
Muestra todos los archivos `resumen_*.md` listos para usar.

### Forzar Reprocesamiento
```bash
python process_all_pdfs.py --force
```
Reprocesa TODOS los PDFs grandes, incluso si ya tienen resumen.

### Procesar Otro Directorio
```bash
python process_all_pdfs.py ruta/a/otro/directorio
```

---

## Ejemplo de Salida

```
============================================================
PROCESADOR BATCH DE PDFs - Análisis de Schema
============================================================
[INFO] Directorio: contexto_dominio
[INFO] Umbral de tamaño: 100 KB
[INFO] Biblioteca PDF: PyPDF2

[INFO] Encontrados 3 archivos PDF en contexto_dominio

------------------------------------------------------------
RESUMEN DE PDFs ENCONTRADOS:
------------------------------------------------------------

[1] RESOL-2024-2563-INSSJP-DE#INSSJP.pdf
    Tamaño: 488.0 KB
    Estado: [LISTO] Ya procesado

[2] ley_19549.pdf
    Tamaño: 320.5 KB
    Estado: [PENDIENTE] Necesita procesamiento

[3] glosario.pdf
    Tamaño: 45.2 KB
    Estado: [PEQUEÑO] No requiere chunks (<100KB)

------------------------------------------------------------
TOTAL: 3 PDFs
  - A procesar: 1
  - Ya procesados: 1
  - Pequeños (no requieren chunks): 0
------------------------------------------------------------

[INFO] Procesando 1 PDF(s)...

============================================================
Procesando: ley_19549.pdf
============================================================
[PDF] Procesando: ley_19549.pdf
[INFO] Total paginas: 65
[INFO] Tamanio del chunk: 5 paginas
[INFO] Biblioteca: PyPDF2

[CHUNK] Procesando chunk 1: paginas 1-5
   [OK] Jerarquia: 10 elementos
   [OK] Terminologia: 15 terminos
   [OK] Relaciones: 3 verbos
   [OK] Entidades: 5 entidades

...

[INFO] Consolidando resultados...
[SAVE] Resultados guardados en: contexto_dominio\analisis_ley_19549.json
[SAVE] Resumen Markdown guardado en: contexto_dominio\resumen_ley_19549.md
[SUCCESS] ley_19549.pdf procesado exitosamente!

============================================================
PROCESAMIENTO COMPLETADO
============================================================
[SUCCESS] Procesados exitosamente: 1
[INFO] Archivos de resumen disponibles: 2

[INFO] El agente puede continuar con el analisis del schema
============================================================
```

---

## Archivos Generados

Para cada PDF procesado, se generan 2 archivos:

### 1. `resumen_[nombre].md` (Recomendado para el agente)
**Tamaño:** ~1-5 KB (vs cientos de KB del PDF original)

**Contenido:**
- Jerarquía detectada (Capítulos, Artículos, Anexos)
- Terminología especializada (con frecuencia)
- Verbos de relación (DEROGA, MODIFICA, REGULA, etc.)
- Entidades detectadas (Resoluciones, Leyes, Organismos)
- Recomendaciones para el schema

**Ejemplo:** `resumen_RESOL-2024-2563-INSSJP-DE#INSSJP.md`

### 2. `analisis_[nombre].json` (Para análisis detallado)
**Tamaño:** ~2-10 KB

**Contenido:** Datos estructurados con toda la información extraída.

**Ejemplo:** `analisis_RESOL-2024-2563-INSSJP-DE#INSSJP.json`

---

## Configuración

Puedes ajustar los parámetros en `pdf_processing_config.json`:

```json
{
  "limites": {
    "pdf_grande_kb": 100,        // PDFs >100KB se procesan en chunks
    "chunk_size_default": 5,     // 5 páginas por chunk
    "chunk_size_min": 3,
    "chunk_size_max": 10
  },
  "extraccion": {
    "max_jerarquia_por_chunk": 10,
    "max_terminologia_por_chunk": 15,
    "max_entidades_por_chunk": 20,
    "min_frecuencia_terminologia": 2
  }
}
```

---

## Integración con el Agente

El agente de diseño de schema (`agente_diseño_schema.md`) tiene instrucciones para:

1. **FASE 0:** Ejecutar automáticamente `python process_all_pdfs.py`
2. **FASE 1:** Leer los resúmenes generados en lugar de los PDFs originales
3. **FASE 2+:** Continuar con el diseño del schema normalmente

---

## Requisitos

### Biblioteca PDF (Una de las siguientes)
```bash
pip install PyPDF2
# O
pip install PyMuPDF
```

El script detecta automáticamente cuál está instalada.

---

## FAQ

### ¿Qué pasa si agrego nuevos PDFs después?
Solo ejecuta de nuevo `python process_all_pdfs.py`. El script procesa **solo los nuevos** PDFs que no tienen resumen.

### ¿Puedo procesar PDFs manualmente?
Sí, puedes usar el script individual:
```bash
python pdf_chunk_processor.py contexto_dominio/mi_archivo.pdf 5
```

### ¿Los PDFs pequeños se procesan?
No. PDFs <100KB se leen directamente por el agente sin necesidad de chunks.

### ¿Puedo cambiar el umbral de tamaño?
Sí, edita `SIZE_THRESHOLD_KB` en `process_all_pdfs.py` o usa `pdf_processing_config.json`.

### ¿Qué pasa si el procesamiento falla?
El script continúa con los demás PDFs y al final muestra cuántos fallaron.

---

## Estructura de Archivos

```
subagentes/
├── contexto_dominio/                         # Coloca tus PDFs aquí
│   ├── RESOL-2024-2563-INSSJP-DE#INSSJP.pdf # PDF original (488KB)
│   ├── resumen_RESOL-2024-2563-...md        # Resumen generado (1.7KB)
│   └── analisis_RESOL-2024-2563-...json     # Datos estructurados (2.5KB)
│
├── pdf_chunk_processor.py                    # Procesador individual
├── process_all_pdfs.py                       # Procesador batch (USA ESTE)
├── pdf_processing_config.json                # Configuración
├── agente_diseño_schema.md                   # Instrucciones del agente
└── README_PROCESAMIENTO_PDF.md               # Esta guía
```

---

## Ventajas de Este Enfoque

| Aspecto | Sin Chunks | Con Chunks |
|---------|-----------|------------|
| **Tamaño procesado** | 488 KB | 1.7 KB (280x más pequeño) |
| **Límite de contexto** | ❌ Se excede | ✅ Nunca se excede |
| **Cobertura** | Solo primeras páginas | ✅ TODO el documento |
| **Tiempo de procesamiento** | N/A | ~10-30 segundos por PDF |
| **Reutilizable** | No | ✅ Sí, no reprocesa |
| **Escalabilidad** | ❌ Falla con múltiples PDFs | ✅ Procesa 1 o 100 PDFs |

---

## Soporte

Si encuentras problemas:
1. Verifica que tienes PyPDF2 o PyMuPDF instalado
2. Revisa que los PDFs no estén corruptos
3. Verifica permisos de lectura/escritura en `contexto_dominio/`

---

**¡Listo! Ahora puedes procesar todos tus PDFs automáticamente antes de diseñar el schema.**
