# preguntas_adk_final.py
from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
from google.adk.runners import InMemoryRunner
from neo4j_for_adk import graphdb
import asyncio, os

# === CONFIGURACIÓN GENERAL ===
llm = LiteLlm(model="openai/gpt-4o")  # o "gpt-5-nano" si querés usar otro modelo

uri = os.getenv("NEO4J_URI", "neo4j+s://b0df6e44.databases.neo4j.io")
user = os.getenv("NEO4J_USER", "neo4j")
password = os.getenv("NEO4J_PASSWORD", "NQkXw6G9S7jO8wQXQIRpd5BX-g2t_bEvXweJVPSWO1g")
graphdb.connect(uri, user, password)

# === TOOL: EJECUCIÓN DE CONSULTAS CYTHER ===
def run_cypher_query(query_text: str):
    print(f"\n🔍 Consulta generada por el modelo:\n{query_text}\n")
    result = graphdb.send_query(query_text)
    return {"status": "success", "result": result}

# === DEFINICIÓN DEL AGENTE ===
instruction = """
Sos un analista experto en Neo4j que trabaja con el grafo de trámites de prótesis del PAMI.
Entidades disponibles: Afiliado, Prestador, Proveedor, Protesis, Tramite, Mensaje, NotificacionInterna, Incumplimiento.
Relaciones disponibles:
(Tramite)-[:TRAMITE_DE]->(Afiliado)
(Tramite)-[:GESTIONADO_POR]->(Prestador)
(Tramite)-[:ASIGNADO_A]->(Proveedor)
(Tramite)-[:SOLICITA]->(Protesis)
(Mensaje)-[:ASOCIADO_A]->(Tramite)
(NotificacionInterna)-[:RELACIONADA_CON]->(Tramite)
(Incumplimiento)-[:DETECTADO_EN]->(Tramite)

Tu tarea:
- Interpretar la pregunta del usuario.
- Generar una consulta Cypher válida usando solo las entidades y relaciones indicadas.
- Ejecutarla con la herramienta run_cypher_query.
- Devolver los resultados de forma clara.
"""

query_agent = Agent(
    name="protesis_query_agent",
    model=llm,
    instruction=instruction,
    tools=[run_cypher_query]
)

# === EJECUCIÓN INTERACTIVA ===
async def run_queries():
    runner = InMemoryRunner(agent=query_agent, app_name="protesis_query_app")

    print("🧠 Agente de consultas sobre grafo de prótesis iniciado.")
    while True:
        pregunta = input("\n🟢 Ingresá tu pregunta (o 'salir'): ")
        if pregunta.lower() in ["salir", "exit", "q"]:
            break

        result = await runner.run_debug(pregunta, user_id="user_1")
        print(f"\n✅ Respuesta del agente:\n{result}\n")

asyncio.run(run_queries())
