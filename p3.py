# === p3_multiagent_protesis.py ===
from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
from google.adk.runners import InMemoryRunner
from neo4j_for_adk import graphdb
import asyncio, os

# === CONFIGURACIÓN GENERAL ===
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY no está configurada en las variables de entorno")
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY

uri = os.getenv("NEO4J_URI", "neo4j+s://b0df6e44.databases.neo4j.io")
user = os.getenv("NEO4J_USER", "neo4j")
password = os.getenv("NEO4J_PASSWORD")
if not password:
    raise ValueError("NEO4J_PASSWORD no está configurada en las variables de entorno")
graphdb.connect(uri, user, password)

# === TOOL ===
def run_cypher_query(query_text: str):
    query_text = query_text.replace("\\", "").replace("```", "").strip()
    print(f"\n[DEBUG] Ejecutando en Neo4j:\n{query_text}\n")
    result = graphdb.send_query(query_text)
    return {"status": "success", "result": result}

# === MODELOS ===
llm_planner = LiteLlm(model="openai/gpt-5-nano")
llm_executor = LiteLlm(model="openai/gpt-5-nano")
llm_summarizer = LiteLlm(model="openai/gpt-5-nano")

# === AGENTE PLANNER ===
planner_instruction = """
Sos un agente PLANIFICADOR experto en análisis de grafos Neo4j.
Tu tarea es descomponer la pregunta del usuario en subtareas.
Cada subtarea debe ser una instrucción concreta para el agente 'executor', expresada en lenguaje natural.
Devolvé una lista ordenada de pasos que el executor pueda seguir para obtener la respuesta final.
No ejecutes consultas.
"""

planner_agent = Agent(
    name="planner_agent",
    model=llm_planner,
    instruction=planner_instruction
)

# === AGENTE EXECUTOR ===
executor_instruction = """
Sos un agente EJECUTOR de consultas Neo4j.
Recibís subtareas desde el planner.
Para cada una, generá y ejecutá la consulta Cypher adecuada usando la herramienta 'run_cypher_query'.
Devuelve los resultados obtenidos (sin resumirlos).
"""

executor_agent = Agent(
    name="executor_agent",
    model=llm_executor,
    instruction=executor_instruction,
    tools=[run_cypher_query]
)

# === AGENTE SUMMARIZER ===
summarizer_instruction = """
Sos un agente ANALISTA.
Recibís los resultados de varias consultas y elaborás una conclusión general.
Explicá hallazgos relevantes, coincidencias o patrones detectados.
"""

summarizer_agent = Agent(
    name="summarizer_agent",
    model=llm_summarizer,
    instruction=summarizer_instruction
)

# === AGENTE PRINCIPAL (ORQUESTADOR) ===
orchestrator_instruction = """
Sos un orquestador que coordina tres agentes:
1. planner_agent: genera el plan de consultas.
2. executor_agent: ejecuta cada consulta en Neo4j.
3. summarizer_agent: interpreta los resultados y responde al usuario.

Cuando recibas una pregunta:
- Pedí al planner que genere los pasos.
- Pasá cada paso al executor.
- Entregá los resultados al summarizer.
"""

orchestrator_agent = Agent(
    name="orchestrator_agent",
    model=LiteLlm(model="openai/gpt-5-nano"),
    instruction=orchestrator_instruction,
    sub_agents=[planner_agent, executor_agent, summarizer_agent]
)

# === EJECUCIÓN INTERACTIVA ===
async def run_queries():
    runner = InMemoryRunner(agent=orchestrator_agent, app_name="multiagent_protesis")
    print("🤖 Multiagente de consultas sobre grafo de prótesis iniciado.")

    while True:
        pregunta = input("\n🟢 Ingresá tu pregunta (o 'salir'): ")
        if pregunta.lower() in ["salir", "exit", "q"]:
            break
        result = await runner.run_debug(pregunta, user_id="user_1")
        print(f"\n✅ Respuesta Final:\n{result}\n")

asyncio.run(run_queries())
