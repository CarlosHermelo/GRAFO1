# OBJETIVO TÉCNICO VALIDADO

**Fecha:** 2025-12-16

**Objetivo del Usuario:**
Construir un grafo de conocimiento que integre todas las prestaciones PAMI y sus normativas asociadas, permitiendo detectar inconsistencias normativas (faltantes, superposiciones, mal definiciones) mediante validación contra el marco legal administrativo argentino. El análisis se apoya en la Ley 19.549 de Procedimientos Administrativos y su reglamentación, junto con la ley específica de creación del INSSJP (PAMI), para determinar si las prestaciones están correctamente reguladas según criterios legales y administrativos del Estado argentino.

**Dominio:**
healthcare

**Entidades Clave Identificadas:**
- **Prestación**: Servicios y productos que PAMI provee a sus afiliados (pañales, traslados en ambulancia, prótesis, medicamentos, consultas médicas, etc.)
- **Normativa**: Resoluciones, disposiciones y actos administrativos de PAMI que regulan prestaciones
- **Marco Legal**: Ley 19.549, reglamentación de procedimientos administrativos, y ley de creación del INSSJP
- **Criterio de Calidad Administrativa**: Requisitos legales que debe cumplir una normativa válida (referencia legal, vigencia, alcance, no superposición, etc.)
- **Inconsistencia**: Problemas detectados en la definición normativa (faltantes, superposición, ambigüedad)

**Relaciones Clave:**
- Prestación → REGULADA_POR → Normativa
- Normativa → CUMPLE_CON → Criterio de Calidad Administrativa
- Normativa → FUNDAMENTADA_EN → Marco Legal (Ley 19.549, ley INSSJP)
- Normativa → TIENE_INCONSISTENCIA → Inconsistencia
- Prestación → TIENE_FALTANTE_NORMATIVO → (cuando no hay normativa que la respalde)
- Normativa1 → SUPERPONE_CON → Normativa2 (cuando regulan lo mismo con reglas diferentes)

**Consultas Esperadas (Ejemplos):**
1. "¿Cuáles son las normativas definidas por PAMI sobre la prestación de pañales?"
2. "¿Las normativas relacionadas al traslado en ambulancia cumplen con las normativas de calidad administrativa para aplicar esa prestación?"
3. "¿Hay inconsistencias en las normativas definidas para la prestación de entrega de pañales?"
4. "¿Qué prestaciones tienen faltantes normativos (no están respaldadas por ninguna normativa)?"
5. "¿Qué normativas tienen superposición entre sí para la misma prestación?"
6. "¿Qué normativas no citan correctamente la Ley 19.549 o la ley de creación del INSSJP como fundamento legal?"
7. "¿Qué prestaciones están mal definidas (con normativas ambiguas o contradictorias)?"

**Tipos de Inconsistencias a Detectar:**

1. **Faltantes:**
   - Prestaciones sin normativa que las respalde
   - Normativas que no referencian el marco legal obligatorio (Ley 19.549, ley INSSJP)
   - Falta de especificación de vigencia, alcance o criterios de aplicación

2. **Superposición:**
   - Dos o más normativas que regulan la misma prestación con reglas diferentes o contradictorias
   - Normativas nuevas que no derogan explícitamente las anteriores
   - Conflictos de vigencia temporal

3. **Mal Definidas:**
   - Normativas con lenguaje ambiguo que no especifica claramente qué cubre o excluye
   - Falta de criterios de elegibilidad o aplicación
   - Normativas que no cumplen con los requisitos formales de la Ley 19.549

**Validación:**
- ✓ **Específico:** Define claramente el dominio (PAMI), las entidades principales (prestaciones, normativas, marco legal), los tipos de inconsistencias (faltantes, superposición, mal definición), y el marco legal de referencia (Ley 19.549 + ley INSSJP)
- ✓ **Accionable:** Permite traducirse a consultas Cypher concretas sobre relaciones entre prestaciones y normativas, detección de inconsistencias mediante patrones de grafo, y validación de cumplimiento de criterios administrativos
- ✓ **Alcance definido:** Se limita al contexto de prestaciones PAMI y su validación normativa contra el marco legal administrativo argentino, sin incluir otros aspectos como análisis financiero o operativo

**Criterios de Calidad Administrativa (según Ley 19.549):**
Las normativas deben cumplir con:
- Fundamentación legal explícita (referencia a ley habilitante)
- Competencia del órgano emisor
- Forma y procedimientos establecidos
- Motivación (razones de hecho y derecho)
- Vigencia temporal definida
- Alcance y límites claros
- No contradicción con normativas superiores o vigentes

---
*Este archivo será utilizado como entrada por el siguiente agente: Agente de Diseño de Schema*
