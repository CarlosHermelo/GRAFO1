# Cambios Realizados a graph_schema_agent.py

## 📋 Resumen

Se ha mejorado `graph_schema_agent.py` integrando **5 niveles de validación** para asegurar la calidad del esquema antes de generar código Cypher.

---

## ✅ Validaciones Implementadas

### 1. **Validación de Unicidad de IDs** ✔️
**Método:** `PlanValidator.check_unique_ids()`

- **Detecta:** IDs duplicados en la columna `unique_column` de cada nodo
- **Nivel:** Automático (sin LLM)
- **Fuente:** Lee directamente desde archivos CSV
- **Ejemplo de Error:**
  ```
  ❌ Producto: 5 IDs duplicados en 'product_id': ['PROD_001', 'PROD_002']
  ```

**Implementación:**
```python
duplicates = df[unique_column].duplicated().sum()
if duplicates > 0:
    # Reportar valores duplicados
```

---

### 2. **Detección de Relaciones Redundantes** ✔️
**Método:** `PlanValidator.check_redundant_relationships()`

- **Detecta:** Relaciones duplicadas (mismo source→type→target)
- **Nivel:** Automático (sin LLM)
- **Ejemplo de Error:**
  ```
  ❌ Relación redundante: (Producto) --[PERTENECE_A]--> (Categoria)
  ❌ Relación redundante: (Producto) --[PERTENECE_A]--> (Categoria)
  ```

**Implementación:**
```python
rel_tuple = (from_node, rel_type, to_node)
if rel_tuple in rel_tuples:
    # Es una redundancia
```

---

### 3. **Detección de Grafos Desconectados** ✔️
**Método:** `PlanValidator.check_disconnected_nodes()`

- **Detecta:** Nodos sin participar en ninguna relación (aislados)
- **Nivel:** Automático (warning, no error)
- **Ejemplo de Warning:**
  ```
  ⚠️ Nodos desconectados (sin relaciones): {'TipoProducto', 'Proveedor'}
  ```

**Implementación:**
```python
connected_nodes = set()
for rel in relationships:
    connected_nodes.add(rel.from_node)
    connected_nodes.add(rel.to_node)

isolated = set(nodes.keys()) - connected_nodes
```

---

### 4. **Validación de Coherencia (Nodos ↔ Relaciones)** ✔️
**Método:** `PlanValidator.check_node_relationship_coherence()`

- **Detecta:** Relaciones que referencian nodos inexistentes
- **Nivel:** Automático (sin LLM)
- **Ejemplo de Error:**
  ```
  ❌ Nodo origen 'ClienteInvalido' no existe en el plan
  ❌ Nodo destino 'OtherNode' no existe en el plan
  ```

**Implementación:**
```python
node_labels = {item.label for item in nodos}

for rel in relaciones:
    if rel.from_node not in node_labels:
        # Error: nodo no existe
```

---

### 5. **Validación con Critic Agent (LLM)** ✔️
**Método:** `run_agent(CRITIC_AGENT_PROMPT)`

- **Detecta:** Incoherencias semánticas y lógicas
- **Nivel:** LLM-basado (GPT-4o)
- **Acceso a validaciones automáticas:** Sí (las lee como contexto)
- **Respuestas:**
  - `VALID` → Esquema aprobado
  - `RETRY` → Requiere refinamiento

**Nuevas instrucciones del Critic:**
```
Busca estos problemas ADICIONALES (además de los ya validados):
1. Incoherencias lógicas en el modelado
2. Relaciones que no tienen sentido semántico
3. Archivos no cubiertos por el plan
4. Esquema incompleto para el objetivo del usuario
```

---

## 🔄 Loop de Refinamiento

El script ahora ejecuta hasta **3 iteraciones**:

```
ITERACIÓN 1
├── Proposal Agent (propone esquema)
├── Validaciones Automáticas (comprueba)
│   ├── ❌ Errores críticos? → Ir a iteración 2
│   └── ✅ OK? → Continuar
├── Critic Agent (valida semántica con contexto de auto-validaciones)
│   ├── VALID? → ✅ FIN
│   └── RETRY? → Ir a iteración 2

ITERACIÓN 2 y 3 (igual flujo, pero mejorando basado en feedback)
```

---

## 📁 Cambios en Clases y Funciones

### Nueva Clase: `PlanValidator`

```python
class PlanValidator:
    def __init__(self, import_dir: str)
    def check_unique_ids(plan) → (bool, List[str])
    def check_redundant_relationships(plan) → (bool, List[str])
    def check_disconnected_nodes(plan) → (bool, List[str])
    def check_node_relationship_coherence(plan) → (bool, List[str])
    def validate_all(plan) → (bool, str)  # Ejecuta todas
```

### Cambios en `AgentState`

```python
class AgentState:
    # Nuevo:
    + validator = PlanValidator(IMPORT_DIR)
    + auto_validation_report = ""
```

### Cambios en `main()`

```python
for i in range(max_iterations):
    # 2. PROPOSAL AGENT
    proposal_response = run_agent(proposal_prompt)

    # 2.5 VALIDACIONES AUTOMÁTICAS (NUEVO)
    auto_valid, auto_report = state.validator.validate_all(plan)

    # Si hay errores críticos, saltar Critic y refinar
    if not auto_valid and "❌" in auto_report:
        continue  # Ir a siguiente iteración

    # 3. CRITIC AGENT (con contexto de auto-validaciones)
    critic_prompt = CRITIC_AGENT_PROMPT.format(
        auto_validation_report=auto_report
    )
    critic_response = run_agent(critic_prompt)
```

---

## 📊 Importaciones Nuevas

```python
from typing import List, Dict, Any, Tuple  # Agregado: Tuple
from collections import defaultdict  # Nuevo (importado pero opcional para uso futuro)
```

---

## 💰 Impacto en Consumo de API

| Validación | Requiere API | Costo |
|---|---|---|
| check_unique_ids | ❌ No | Gratis |
| check_redundant_relationships | ❌ No | Gratis |
| check_disconnected_nodes | ❌ No | Gratis |
| check_node_relationship_coherence | ❌ No | Gratis |
| Critic Agent | ✅ Sí | 1 llamada/iteración |

**Resultado:** Mejor calidad con IGUAL o MENOR consumo de API (evita llamadas innecesarias al Critic)

---

## 🎯 Beneficios

### ✅ Detección temprana
- Los errores se detectan antes de llamar al Critic Agent
- Ahorra llamadas a API costosas

### ✅ Mejor feedback
- El Critic Agent recibe contexto de validaciones automáticas
- Se enfoca en problemas semánticos/lógicos, no técnicos

### ✅ Mayor confiabilidad
- Múltiples capas de validación
- Menos riesgo de esquemas inválidos

### ✅ Mejor experiencia
- Mensajes claros sobre qué está mal
- Refinamiento dirigido

---

## 📝 Ejemplo de Salida

```
=== ITERACIÓN 1 ===

>> Ejecutando Proposal Agent...
Respuesta Proposal: He analizado los archivos y propongo...
Plan Actual: {
  "Producto": {...},
  "Categoria": {...},
  "PERTENECE_A": {...}
}

>> Ejecutando Validaciones Automáticas...

============================================================
🔍 VALIDACIONES AUTOMÁTICAS PRE-CRÍTICA
============================================================

✅ Producto: IDs únicos en 'product_id' (1000 registros)
✅ Categoria: IDs únicos en 'category_id' (50 registros)
✅ No hay relaciones redundantes (1 relación única)
⚠️ Nodos desconectados (sin relaciones): {'TipoProducto'}
✅ Coherencia de nodos-relaciones verificada

>> Ejecutando Critic Agent...

📋 Respuesta del Crítico:
RETRY - El nodo TipoProducto está aislado. Considerar si debería
conectarse a Producto. También verificar si hay archivos sin procesar.

... Refinando esquema basado en feedback ...


=== ITERACIÓN 2 ===

>> Ejecutando Proposal Agent...
Respuesta Proposal: Revisando el feedback, ahora propongo...
Plan Actual: {
  "Producto": {...},
  "Categoria": {...},
  "TipoProducto": {...},
  "PERTENECE_A": {...},
  "TIENE_TIPO": {...}
}

>> Ejecutando Validaciones Automáticas...
✅ Producto: IDs únicos en 'product_id' (1000 registros)
✅ Categoria: IDs únicos en 'category_id' (50 registros)
✅ TipoProducto: IDs únicos en 'type_id' (20 registros)
✅ No hay relaciones redundantes (2 relaciones únicas)
✅ Todos los nodos están conectados (3 nodos)
✅ Coherencia de nodos-relaciones verificada

>> Ejecutando Critic Agent...

📋 Respuesta del Crítico:
VALID

🎉 🎉 🎉 🎉 🎉 🎉 🎉 🎉 🎉 🎉 🎉 🎉 🎉 🎉 🎉
*** ¡ESQUEMA APROBADO! ***
🎉 🎉 🎉 🎉 🎉 🎉 🎉 🎉 🎉 🎉 🎉 🎉 🎉 🎉 🎉

============================================================
📊 RESUMEN FINAL
============================================================

✅ Generando código Cypher de ejemplo basado en el plan...

Cypher sugerido: LOAD CSV... MERGE (n:Producto {id: row.product_id})
Cypher sugerido: LOAD CSV... MERGE (n:Categoria {id: row.category_id})
Cypher sugerido: LOAD CSV... MERGE (n:TipoProducto {id: row.type_id})
```

---

## 🚀 Cómo Usar

El script se usa igual que antes:

```bash
python ESTRUCTURA/graph_schema_agent.py
```

No hay cambios en la interfaz, solo mejoras internas de validación.

---

## 🔧 Personalización

### Cambiar máximo de iteraciones
```python
max_iterations = 5  # Cambiar de 3 a 5
```

### Desactivar validaciones automáticas (no recomendado)
En `main()`, comentar:
```python
# auto_valid, auto_report = state.validator.validate_all(state.construction_plan)
state.auto_validation_report = "Validaciones desactivadas"
```

### Cambiar objetivo del usuario
```python
state.user_goal = "Tu objetivo aquí"
```

---

## 📚 Comparativa: Antes vs Después

| Aspecto | Antes | Después |
|---|---|---|
| **Validación de unicidad** | ❌ No | ✅ Automática |
| **Detección redundancias** | ❌ No | ✅ Automática |
| **Nodos desconectados** | ❌ Mención en prompt | ✅ Detección real |
| **Coherencia nodos-rels** | ❌ No | ✅ Automática |
| **Critic context** | ❌ Sin contexto | ✅ Con validaciones |
| **API calls** | 1 Proposal + 1 Critic | 1 Proposal + 1 Critic (igual o menos) |
| **Confiabilidad** | Baja | Alta |
| **Iteraciones** | Hasta 3 | Hasta 3 (mejoradas) |

---

## ⚠️ Notas Importantes

1. **Las validaciones automáticas no detienen el proceso**, solo informan
2. **Los errores críticos (❌) causan refinamiento automático** sin llamar al Critic
3. **Los warnings (⚠️) se pasan al Critic como contexto**
4. El Critic Agent ahora se enfoca en **lógica y semántica**, no en validaciones técnicas

---

## 📞 Soporte

Si tienes dudas:
- Revisa los ejemplos de salida arriba
- Ejecuta el script y observa el flujo de validaciones
- Ajusta `max_iterations` si necesitas más refinamientos
