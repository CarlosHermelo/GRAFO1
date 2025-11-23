¡Entendido! Voy a adaptar la arquitectura descrita en el PDF (Lección 6) para eliminar la dependencia de Google ADK. En su lugar, utilizaremos Python puro, la librería oficial de OpenAI para el manejo del LLM y las llamadas a funciones (Tools), y el driver de Neo4j.

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

