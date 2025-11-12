# === IMPORTS ===
from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
from google.adk.runners import InMemoryRunner
from google.genai import types
from neo4j_for_adk import graphdb
import asyncio

#
def tool_success(key, value): return {"status": "success", key: value}
def tool_error(msg): return {"status": "error", "message": msg}

# === CONFIGURACIÓN GENERAL ===
llm = LiteLlm(model="openai/gpt-4o")
# Inicializamos un diccionario compartido de estado en lugar de ToolContext
shared_state = {}

# Conexión a Neo4j (usar variables de entorno si existen, con fallback seguro)
import os
uri = os.getenv("NEO4J_URI", "neo4j+s://b0df6e44.databases.neo4j.io")
user = os.getenv("NEO4J_USER", "neo4j")
password = os.getenv("NEO4J_PASSWORD", "NQkXw6G9S7jO8wQXQIRpd5BX-g2t_bEvXweJVPSWO1g")
graphdb.connect(uri, user, password)

# ------------------------------------------------------
# 1. USER INTENT AGENT
# ------------------------------------------------------

def set_perceived_user_goal():
    goal = {
        "description": (
            "Analizar y gestionar la trazabilidad completa de trámites de prótesis "
            "entre prestadores, proveedores, afiliados y PAMI, identificando demoras, errores "
            "y patrones de incumplimiento."
        )
    }
    shared_state["approved_user_goal"] = goal
    return tool_success("approved_user_goal", goal)

# ------------------------------------------------------
# 2. SCHEMA AGENT
# ------------------------------------------------------

def approve_schema():
    schema = {
        "entities": [
            "Afiliado", "Prestador", "Proveedor",
            "Protesis", "Tramite", "Mensaje",
            "NotificacionInterna", "Incumplimiento"
        ],
        "relationships": [
            {"from": "Tramite", "to": "Afiliado", "type": "TRAMITE_DE"},
            {"from": "Tramite", "to": "Prestador", "type": "GESTIONADO_POR"},
            {"from": "Tramite", "to": "Proveedor", "type": "ASIGNADO_A"},
            {"from": "Tramite", "to": "Protesis", "type": "SOLICITA"},
            {"from": "Mensaje", "to": "Tramite", "type": "ASOCIADO_A"},
            {"from": "NotificacionInterna", "to": "Tramite", "type": "RELACIONADA_CON"},
            {"from": "Incumplimiento", "to": "Tramite", "type": "DETECTADO_EN"}
        ]
    }
    shared_state["approved_schema"] = schema
    return tool_success("approved_schema", schema)

# ------------------------------------------------------
# 3. GRAPH CONSTRUCTION AGENT
# ------------------------------------------------------

def approve_construction_plan():
    plan = {
        "data_sources": {
            "Afiliado": "afiliado.csv",
            "Prestador": "prestador.csv",
            "Proveedor": "proveedor.csv",
            "Protesis": "protesis.csv",
            "Tramite": "tramite.csv",
            "Mensaje": "mensaje.csv",
            "NotificacionInterna": "notificacion_interna.csv",
            "Incumplimiento": "incumplimiento.csv"
        },
        "relationships": [
            {"file": "tramite.csv", "from": "id_tramite", "to": "id_afiliado", "type": "TRAMITE_DE"},
            {"file": "tramite.csv", "from": "id_tramite", "to": "id_prestador", "type": "GESTIONADO_POR"},
            {"file": "tramite.csv", "from": "id_tramite", "to": "id_proveedor", "type": "ASIGNADO_A"},
            {"file": "tramite.csv", "from": "id_tramite", "to": "id_protesis", "type": "SOLICITA"},
            {"file": "mensaje.csv", "from": "id_mensaje", "to": "id_tramite", "type": "ASOCIADO_A"},
            {"file": "notificacion_interna.csv", "from": "id_notificacion", "to": "id_tramite", "type": "RELACIONADA_CON"},
            {"file": "incumplimiento.csv", "from": "id_incumplimiento", "to": "id_tramite", "type": "DETECTADO_EN"}
        ]
    }
    shared_state["approved_construction_plan"] = plan
    return tool_success("approved_construction_plan", plan)

def construct_domain_graph():
    import csv
    import os

    # Mapeo de entidad a su columna ID principal y archivo CSV
    entity_config = {
        "Afiliado": ("Afiliado.csv", "id_afiliado"),
        "Prestador": ("Prestador.csv", "id_prestador"),
        "Proveedor": ("Proveedor.csv", "id_proveedor"),
        "Protesis": ("Protesis.csv", "id_protesis"),
        "Tramite": ("Tramite.csv", "id_tramite"),
        "Mensaje": ("Mensaje.csv", "id_mensaje"),
        "NotificacionInterna": ("Notificacion_Interna.csv", "id_notificacion"),
        "Incumplimiento": ("Incumplimiento.csv", "id_incumplimiento")
    }

    # Crear constraints únicos para cada entidad (usando el ID específico de cada entidad)
    for entity, (_, id_col) in entity_config.items():
        query = f"CREATE CONSTRAINT IF NOT EXISTS FOR (n:{entity}) REQUIRE n.{id_col} IS UNIQUE"
        try:
            graphdb.send_query(query)
        except Exception as e:
            print(f"Constraint para {entity} ya existe o error: {e}")

    # Cargar nodos desde CSVs
    for entity, (filename, id_col) in entity_config.items():
        filepath = os.path.join(os.getcwd(), filename)
        if not os.path.exists(filepath):
            print(f"Archivo no encontrado: {filepath}")
            continue

        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Crear nodo con todas las propiedades del CSV
                props = ", ".join([f"{k}: ${k}" for k in row.keys()])
                query = f"MERGE (n:{entity} {{{props}}})"
                graphdb.send_query(query, row)

    # Crear relaciones según el plan
    relationship_mapping = [
        ("Tramite.csv", "id_tramite", "Tramite", "id_afiliado", "Afiliado", "TRAMITE_DE"),
        ("Tramite.csv", "id_tramite", "Tramite", "id_prestador", "Prestador", "GESTIONADO_POR"),
        ("Tramite.csv", "id_tramite", "Tramite", "id_proveedor", "Proveedor", "ASIGNADO_A"),
        ("Tramite.csv", "id_tramite", "Tramite", "id_protesis", "Protesis", "SOLICITA"),
        ("Mensaje.csv", "id_mensaje", "Mensaje", "id_tramite", "Tramite", "ASOCIADO_A"),
        ("Notificacion_Interna.csv", "id_notificacion", "NotificacionInterna", "id_tramite", "Tramite", "RELACIONADA_CON"),
        ("Incumplimiento.csv", "id_incumplimiento", "Incumplimiento", "id_tramite", "Tramite", "DETECTADO_EN")
    ]

    for csv_file, from_id_col, from_entity, to_id_col, to_entity, rel_type in relationship_mapping:
        filepath = os.path.join(os.getcwd(), csv_file)
        if not os.path.exists(filepath):
            continue

        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if from_id_col in row and to_id_col in row:
                    query = f"""
                    MATCH (a:{from_entity} {{{from_id_col}: $from_id}})
                    MATCH (b:{to_entity} {{{to_id_col}: $to_id}})
                    MERGE (a)-[:{rel_type}]->(b)
                    """
                    params = {"from_id": row[from_id_col], "to_id": row[to_id_col]}
                    graphdb.send_query(query, params)

    return tool_success("graph_built", "Knowledge graph construido con éxito.")

# ------------------------------------------------------
# 4. QUERY AGENT
# ------------------------------------------------------

def run_cypher_query(query_text: str):
    result = graphdb.send_query(query_text)
    shared_state["query_result"] = result
    return tool_success("query_result", result)

# ------------------------------------------------------
# 5. ORCHESTRATOR AGENT
# ------------------------------------------------------

instruction = """
Coordina la creación y consulta del grafo de trámites de prótesis.
Usa las herramientas disponibles para:
1. Establecer el objetivo del usuario (set_perceived_user_goal)
2. Aprobar el esquema del grafo (approve_schema)
3. Aprobar el plan de construcción (approve_construction_plan)
4. Construir el grafo (construct_domain_graph)
5. Ejecutar consultas Cypher (run_cypher_query)
"""

orchestrator_agent = Agent(
    name="protesis_kg_orchestrator",
    model=llm,
    instruction=instruction,
    tools=[
        set_perceived_user_goal,
        approve_schema,
        approve_construction_plan,
        construct_domain_graph,
        run_cypher_query
    ]
)

# ------------------------------------------------------
# 6. EJECUCIÓN
# ------------------------------------------------------

async def run_workflow():
    # Crear runner para manejar el agente
    runner = InMemoryRunner(agent=orchestrator_agent, app_name="protesis_kg_app")

    print("=== Construyendo el grafo de conocimiento ===")
    # Usar run_debug para simplificar
    result = await runner.run_debug(
        "Construí el grafo de conocimiento de trámites de prótesis en PAMI.",
        user_id="user_1"
    )
    print(f"Resultado: {result}")

    print("\n=== Consultando el grafo ===")
    result = await runner.run_debug(
        "¿Qué prestadores tienen más incumplimientos detectados?",
        user_id="user_1"
    )
    print(f"Resultado: {result}")

asyncio.run(run_workflow())
