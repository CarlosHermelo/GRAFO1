# p2.py
from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
from google.adk.runners import InMemoryRunner
from neo4j_for_adk import graphdb
import asyncio, os

# === CONFIGURACIÓN ===
llm = LiteLlm(model="openai/gpt-5-nano")  # o "gpt-5-nano"

uri = os.getenv("NEO4J_URI", "neo4j+s://b0df6e44.databases.neo4j.io")
user = os.getenv("NEO4J_USER", "neo4j")
password = os.getenv("NEO4J_PASSWORD", "NQkXw6G9S7jO8wQXQIRpd5BX-g2t_bEvXweJVPSWO1g")
graphdb.connect(uri, user, password)

# === TOOL ===
def run_cypher_query(query_text: str):
    # Limpieza básica del texto generado por el modelo
    query_text = query_text.replace("\\", "").strip().strip("```cypher").strip("```")
    print(f"\n[DEBUG] Ejecutando Cypher:\n{query_text}\n")
    result = graphdb.send_query(query_text)
    return {"status": "success", "result": result}


# === AGENTE ===
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
1. Interpretar la pregunta del usuario en lenguaje natural.
2. Generar una consulta Cypher válida que responda la pregunta, usando solo las entidades y relaciones listadas.
   - Si la pregunta implica “frecuencia” o “más de uno”, usá `COUNT(...)` y agrupá con `WITH … WHERE COUNT(...) > 1`.
   - No usar `WHERE` inmediatamente después de `RETURN`. Si se filtra por agregación, usar `WITH` antes de `WHERE`.
   - Cada variable usada debe estar declarada en `MATCH` o `WITH`.
3. Ejecutar la consulta con la herramienta `run_cypher_query`.
4. Mostrar únicamente la respuesta final de forma clara. Si la pregunta no puede ser traducida a una consulta válida con los datos disponibles, devolver “No se puede responder con los datos disponibles.
"""

query_agent = Agent(
    name="protesis_query_agent",
    model=llm,
    instruction=instruction,
    tools=[run_cypher_query]
)

# === EJECUCIÓN ===
async def run_queries():
    runner = InMemoryRunner(agent=query_agent, app_name="protesis_query_app")

    print("🧠 Agente de consultas sobre grafo de prótesis iniciado.")
    while True:
        pregunta = input("\n🟢 Ingresá tu pregunta (o 'salir'): ")
        if pregunta.lower() in ["salir", "exit", "q"]:
            break

       # result = await runner.run_debug(pregunta, user_id="user_1")
        result = await runner.run_debug(pregunta, user_id="user_1")
        print(f"\n✅ Respuesta:\n{result}\n")

asyncio.run(run_queries())
