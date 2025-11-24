

## Cómo ejecutarlo

1. Instala las dependencias: `pip install -r requirements.txt`.

2. Ejecuta `python data_simulation.py` para crear datos de prueba (o pon tus propios CSVs en una carpeta import_data).

3. Configura tu API Key: `export OPENAI_API_KEY="tu-key"`.

4. Ejecuta el agente: `python graph_schema_agent.py`.

####el codigo fue generado gemini 3.1 
https://gemini.google.com/app/499a1a1a806ca697
-------------------------------------------------------------------

La arquitectura se mantendrá fiel a la lógica del documento:

Coordinator/Loop: Un bucle principal que orquesta a los agentes.

Proposal Agent: Propone nodos y relaciones basándose en archivos CSV.

Critic Agent: Revisa el plan y da feedback.

State/Tools: Un gestor de estado para guardar el "plan de construcción" y herramientas para leer los archivos.

Aquí tienes los archivos necesarios.

## Archivos Generados

**graph_schema_agent.py**: El script completo en Python. Contiene la lógica de los agentes, la definición de las herramientas (Tools) y el bucle de refinamiento (Refinement Loop).

**requirements.txt**: Las librerías necesarias.

**data_simulation.py**: Un pequeño script opcional para generar archivos CSV de prueba (Productos, Proveedores, Partes) para que el agente tenga algo que analizar si no tienes datos reales a mano.

### Agente de Propuesta de Esquema

Nov 23, 12:13 AM

Open

### Generador de Datos (Opcional)

Nov 23, 12:13 AM

Open

### Dependencias

Nov 23, 12:13 AM

## Explicación de los Cambios (De ADK a Python Puro)

El documento PDF utiliza LlmAgent y LoopAgent de Google ADK, que abstraen mucho código. Aquí he deconstruido esos conceptos para que funcionen "desde cero":

**Orquestación Manual**: En lugar de LoopAgent, he creado un bucle for simple en la función main. Este bucle controla las iteraciones y decide cuándo parar basándose en la salida del crítico.

**Tools como Funciones**: En ADK, las tools se definen de una forma específica. Aquí, he definido funciones estándar de Python (search_file, etc.) y luego he creado un diccionario tools_schema que sigue el formato JSON Schema requerido por la API de OpenAI.

**Gestión de Estado (AgentState)**: ADK tiene un contexto compartido implícito. Aquí he creado una clase simple AgentState global para que las funciones (Tools) puedan modificar el construction_plan y que tanto el Proposal Agent como el Critic Agent puedan leerlo.

**Prompt Engineering**: He extraído las instrucciones clave del PDF (roles, reglas de nodos vs relaciones, verificación de IDs únicos) y las he insertado en las variables PROPOSAL_AGENT_PROMPT y CRITIC_AGENT_PROMPT.

## Cómo ejecutarlo

1. Instala las dependencias: `pip install -r requirements.txt`.

2. Ejecuta `python data_simulation.py` para crear datos de prueba (o pon tus propios CSVs en una carpeta import_data).

3. Configura tu API Key: `export OPENAI_API_KEY="tu-key"`.

4. Ejecuta el agente: `python graph_schema_agent.py`.

El script imprimirá en consola el pensamiento del agente ("Tool Calls"), la propuesta de esquema JSON y las críticas hasta que llegue a un diseño válido.

**Expliacion de que hace  `python graph_schema_agent.py`
Qué es este código

Este documento contiene el script completo para construir un agente que propone un esquema de grafo (Graph Schema Proposal Agent) usando Google ADK + Neo4j.
No es un script suelto: es todo un módulo que:

analiza archivos estructurados (CSV o similares),

detecta nodos y relaciones,

genera reglas de construcción (“construction rules”),

ejecuta una revisión automática mediante un “critic agent”,

repite un ciclo de refinamiento hasta alcanzar un esquema válido.

Subtítulo
Qué hace este código (explicación didáctica y concreta)

El código construye un sistema multi-agente con tres funciones centrales:

schema_proposal_agent

Lee los archivos aprobados.

Usa herramientas como sample_file y search_file.

Decide si cada archivo representa un nodo o una relación.

Propone cómo construir ese nodo/relación desde los CSV.

Va armando el “construction plan”, que es el esquema candidato.

Ejemplo práctico:
Si el archivo es products.csv, propone:

Nodo: Product

Identificador único: product_id

Propiedades: columnas del CSV.

schema_critic_agent

Revisa el plan propuesto.

Verifica si los identificadores son realmente únicos.

Evalúa si una entidad debería ser relación o viceversa.

Detecta nodos aislados o relaciones redundantes.

Responde solo dos opciones:

valid → continuar

retry → devolver lista de problemas

Ejemplo práctico:
“El archivo assemblies.csv tiene dos identificadores, podría ser relación en lugar de nodo.”

CheckStatusAndEscalate

Observa si la crítica dijo “valid”.

Si es válido, corta el loop.

Si no, vuelve a ejecutar el proposal agent con el feedback del critic.

Estas tres piezas funcionan dentro de un
LoopAgent → schema_refinement_loop,
que intenta hasta 2 iteraciones para converger en un esquema consistente.

Subtítulo
Qué scripts incluye internamente

El documento contiene varios módulos listos para copiar/usar:

BLOQUE DE IMPORTS

Configuración del modelo OpenAI (gpt-4o)

Instrucciones del agente de propuesta (schema_proposal_agent)

Herramientas para manipular archivos y construir reglas:

sample_file

search_file

propose_node_construction

propose_relationship_construction

remove_node_construction

remove_relationship_construction

get_proposed_construction_plan

approve_proposed_construction_plan

Definición del agente crítico

Definición del loop de refinamiento

Top-level coordinator agent (opcional), que coordina todo el proceso y habla con el usuario.

Subtítulo
Para qué sirve realmente

Sirve para automatizar la creación de un schema de grafo (GraphRAG) desde archivos estructurados.
Es la parte más difícil del proceso de GraphRAG: decidir cómo deben ser los nodos y relaciones.
Este sistema lo hace automáticamente con:

criterios,

herramientas estructuradas,

revisión crítica,

ciclo de mejora.

Subtítulo
Qué obtengo al final

Al finalizar, el sistema produce un objeto:

approved_construction_plan

Ese plan contiene todas las reglas para importar los CSV a Neo4j:

qué nodos crear,

qué relaciones crear,

qué propiedades usar,

cómo conectar todo.

Ese plan se usa luego para ejecutar el import y construir el grafo.

Si querés, puedo ahora mismo:

resumirte el flujo entero en un diagrama ASCII,

explicarte cómo adaptar este proceso a tu dominio de prótesis,

o escribirte el código limpio para ejecutarlo fuera del notebook.
