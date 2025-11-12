# p2_multi_protesis.py
# === Sistema Multiagente para Grafo de Trámites de Prótesis (PAMI) ===

from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
from google.adk.runners import InMemoryRunner
from google.adk.tools import ToolContext
from neo4j_for_adk import graphdb, tool_success, tool_error
import asyncio, os, warnings, logging

# === CONFIGURACIÓN GENERAL ===
# === CONFIGURACIÓN DE API ===
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY no está configurada en las variables de entorno")
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY

warnings.filterwarnings("ignore")
logging.basicConfig(level=logging.CRITICAL)

llm = LiteLlm(model="openai/gpt-5-nano")

uri = os.getenv("NEO4J_URI", "neo4j+s://b0df6e44.databases.neo4j.io")
user = os.getenv("NEO4J_USER", "neo4j")
password = os.getenv("NEO4J_PASSWORD")
if not password:
    raise ValueError("NEO4J_PASSWORD no está configurada en las variables de entorno")
graphdb.connect(uri, user, password)
print("✅ Conectado a Neo4j")

# === AGENTE 1: User Intent (define objetivo del grafo) ===
PERCEIVED_USER_GOAL = "perceived_user_goal"
APPROVED_USER_GOAL = "approved_user_goal"

def set_perceived_user_goal(kind_of_graph: str, graph_description: str, tool_context: ToolContext):
    data = {"kind_of_graph": kind_of_graph, "graph_description": graph_description}
    tool_context.state[PERCEIVED_USER_GOAL] = data
    return tool_success(PERCEIVED_USER_GOAL, data)

def approve_perceived_user_goal(tool_context: ToolContext):
    if PERCEIVED_USER_GOAL not in tool_context.state:
        return tool_error("No se definió un objetivo.")
    tool_context.state[APPROVED_USER_GOAL] = tool_context.state[PERCEIVED_USER_GOAL]
    return tool_success(APPROVED_USER_GOAL, tool_context.state[APPROVED_USER_GOAL])

user_intent_agent = Agent(
    name="protesis_user_intent_agent",
    model=llm,
    description="Define el objetivo del grafo de trámites de prótesis del PAMI.",
    instruction="Tu función es comprender y registrar el propósito del grafo, relacionado con la trazabilidad de trámites de prótesis, prestadores y proveedores.",
    tools=[set_perceived_user_goal, approve_perceived_user_goal],
)

# === AGENTE 2: File Suggestion ===
def suggest_files(tool_context: ToolContext):
    files = ["afiliados.csv", "prestadores.csv", "proveedores.csv", "tramites.csv", "protesis.csv", "mensajes.csv"]
    tool_context.state["approved_files"] = files
    return tool_success("approved_files", {"files": files})

file_suggestion_agent = Agent(
    name="protesis_file_suggestion_agent",
    model=llm,
    description="Identifica los archivos relevantes del dominio de prótesis.",
    instruction="Selecciona los archivos CSV correspondientes a afiliados, trámites, prestadores, proveedores y mensajes.",
    tools=[suggest_files],
)

# === AGENTE 3: Schema Proposal ===
def propose_schema(tool_context: ToolContext):
    schema = {
        "entities": [
            "Afiliado", "Prestador", "Proveedor", "Protesis", "Tramite",
            "Mensaje", "NotificacionInterna", "Incumplimiento"
        ],
        "relationships": [
            {"from": "Tramite", "to": "Afiliado", "type": "TRAMITE_DE"},
            {"from": "Tramite", "to": "Prestador", "type": "GESTIONADO_POR"},
            {"from": "Tramite", "to": "Proveedor", "type": "ASIGNADO_A"},
            {"from": "Tramite", "to": "Protesis", "type": "SOLICITA"},
            {"from": "Mensaje", "to": "Tramite", "type": "ASOCIADO_A"},
            {"from": "NotificacionInterna", "to": "Tramite", "type": "RELACIONADA_CON"},
            {"from": "Incumplimiento", "to": "Tramite", "type": "DETECTADO_EN"}
        ],
    }
    tool_context.state["approved_schema"] = schema
    return tool_success("approved_schema", schema)

schema_agent = Agent(
    name="protesis_schema_agent",
    model=llm,
    description="Propone el esquema del grafo de trámites de prótesis.",
    instruction="Define entidades y relaciones basadas en el dominio del PAMI.",
    tools=[propose_schema],
)

# === AGENTE 4: Graph Construction ===
def construct_domain_graph(tool_context: ToolContext):
    plan = {
        "Tramite": {"construction_type": "node", "source_file": "tramites.csv",
                    "label": "Tramite", "unique_column_name": "tramite_id",
                    "properties": ["estado", "fecha_inicio", "fecha_fin"]},
        "Afiliado": {"construction_type": "node", "source_file": "afiliados.csv",
                     "label": "Afiliado", "unique_column_name": "dni",
                     "properties": ["nombre", "apellido", "edad", "region"]},
        "Prestador": {"construction_type": "node", "source_file": "prestadores.csv",
                      "label": "Prestador", "unique_column_name": "prestador_id",
                      "properties": ["nombre", "especialidad", "provincia"]},
        "Proveedor": {"construction_type": "node", "source_file": "proveedores.csv",
                      "label": "Proveedor", "unique_column_name": "proveedor_id",
                      "properties": ["razon_social", "ciudad", "reputacion"]},
        "Protesis": {"construction_type": "node", "source_file": "protesis.csv",
                     "label": "Protesis", "unique_column_name": "protesis_id",
                     "properties": ["tipo", "descripcion", "codigo"]},
        "Mensaje": {"construction_type": "node", "source_file": "mensajes.csv",
                    "label": "Mensaje", "unique_column_name": "mensaje_id",
                    "properties": ["texto", "fecha_envio", "autor"]},
        "Tramite_Afiliado": {"construction_type": "relationship", "source_file": "tramites.csv",
                             "relationship_type": "TRAMITE_DE",
                             "from_node_label": "Tramite", "from_node_column": "tramite_id",
                             "to_node_label": "Afiliado", "to_node_column": "dni",
                             "properties": []},
        "Tramite_Prestador": {"construction_type": "relationship", "source_file": "tramites.csv",
                              "relationship_type": "GESTIONADO_POR",
                              "from_node_label": "Tramite", "from_node_column": "tramite_id",
                              "to_node_label": "Prestador", "to_node_column": "prestador_id",
                              "properties": []},
        "Tramite_Proveedor": {"construction_type": "relationship", "source_file": "tramites.csv",
                              "relationship_type": "ASIGNADO_A",
                              "from_node_label": "Tramite", "from_node_column": "tramite_id",
                              "to_node_label": "Proveedor", "to_node_column": "proveedor_id",
                              "properties": []}
    }

    # Crear constraints en Neo4j
    for rule in plan.values():
        if rule["construction_type"] == "node":
            graphdb.send_query(
                f"CREATE CONSTRAINT IF NOT EXISTS FOR (n:{rule['label']}) REQUIRE n.{rule['unique_column_name']} IS UNIQUE"
            )

    tool_context.state["approved_construction_plan"] = plan
    return tool_success("approved_construction_plan", plan)

graph_construction_agent = Agent(
    name="protesis_graph_construction_agent",
    model=llm,
    description="Construye el grafo del dominio de prótesis en Neo4j.",
    instruction="Ejecuta el plan de construcción a partir de archivos CSV y esquema aprobado.",
    tools=[construct_domain_graph],
)

# === ORQUESTADOR PRINCIPAL ===
runner = InMemoryRunner(app_name="protesis_multiagent_system")
runner.register(user_intent_agent)
runner.register(file_suggestion_agent)
runner.register(schema_agent)
runner.register(graph_construction_agent)

# === EJECUCIÓN AUTOMÁTICA ===
async def main():
    print("🚀 Sistema multiagente de prótesis iniciado.")
    goal = "Analizar la trazabilidad de trámites de prótesis entre afiliados, prestadores y proveedores."
    result = await runner.run(goal)
    print("\n=== RESULTADO FINAL ===")
    print(result)
    print("\n=== ESTADO FINAL DEL CONTEXTO ===")
    print(runner.context.state)

asyncio.run(main())
