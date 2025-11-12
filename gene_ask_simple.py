# === IMPORTS ===
from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
from neo4j_for_adk import graphdb
import os

# === CONFIGURACIÓN GENERAL ===
llm = LiteLlm(model="openai/gpt-4o")

# Conexión a Neo4j
uri = os.getenv("NEO4J_URI", "neo4j+s://b0df6e44.databases.neo4j.io")
user = os.getenv("NEO4J_USER", "neo4j")
password = os.getenv("NEO4J_PASSWORD", "NQkXw6G9S7jO8wQXQIRpd5BX-g2t_bEvXweJVPSWO1g")
graphdb.connect(uri, user, password)

# Estado compartido entre herramientas
shared_state = {}

def tool_success(key, value):
    return {"status": "success", key: value}

def tool_error(msg):
    return {"status": "error", "message": msg}

# === HERRAMIENTAS ===

def set_perceived_user_goal():
    """Establece el objetivo del análisis de trámites de prótesis."""
    goal = {
        "description": (
            "Analizar y gestionar la trazabilidad completa de trámites de prótesis "
            "entre prestadores, proveedores, afiliados y PAMI, identificando demoras, errores "
            "y patrones de incumplimiento."
        )
    }
    shared_state["approved_user_goal"] = goal
    return tool_success("approved_user_goal", goal)

def approve_schema():
    """Define las entidades y relaciones del grafo."""
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

def approve_construction_plan():
    """Define el plan para construir el grafo desde archivos CSV."""
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
    """Construye el grafo en Neo4j según el plan aprobado."""
    if "approved_construction_plan" not in shared_state:
        return tool_error("Primero debes aprobar el plan de construcción")
    if "approved_schema" not in shared_state:
        return tool_error("Primero debes aprobar el esquema")

    plan = shared_state["approved_construction_plan"]
    schema = shared_state["approved_schema"]

    # Crear constraints para cada entidad
    for entity in schema["entities"]:
        query = f"CREATE CONSTRAINT IF NOT EXISTS FOR (n:{entity}) REQUIRE n.id IS UNIQUE"
        try:
            graphdb.send_query(query)
        except Exception as e:
            return tool_error(f"Error creando constraint para {entity}: {str(e)}")

    # Crear relaciones según plan
    for rel in plan["relationships"]:
        q = (
            f"LOAD CSV WITH HEADERS FROM 'file:///{rel['file']}' AS row "
            f"MATCH (a:{rel['from']} {{id: row.{rel['from']}}}), "
            f"(b:{rel['to']} {{id: row.{rel['to']}}}) "
            f"MERGE (a)-[:{rel['type']}]->(b)"
        )
        try:
            graphdb.send_query(q)
        except Exception as e:
            return tool_error(f"Error creando relación {rel['type']}: {str(e)}")

    return tool_success("graph_built", "Knowledge graph construido con éxito.")

def run_cypher_query(query_text: str):
    """Ejecuta una consulta Cypher en Neo4j.

    Args:
        query_text: La consulta Cypher a ejecutar
    """
    try:
        result = graphdb.send_query(query_text)
        shared_state["query_result"] = result
        return tool_success("query_result", result)
    except Exception as e:
        return tool_error(f"Error ejecutando consulta: {str(e)}")

# === EJECUCIÓN MANUAL (sin agente) ===
if __name__ == "__main__":
    print("=== Iniciando construcción del grafo de conocimiento ===\n")

    # Paso 1: Establecer objetivo
    print("1. Estableciendo objetivo del usuario...")
    result = set_perceived_user_goal()
    print(f"   OK {result}\n")

    # Paso 2: Aprobar esquema
    print("2. Aprobando esquema del grafo...")
    result = approve_schema()
    print(f"   OK Schema aprobado con {len(result['approved_schema']['entities'])} entidades\n")

    # Paso 3: Aprobar plan de construcción
    print("3. Aprobando plan de construcción...")
    result = approve_construction_plan()
    print(f"   OK Plan aprobado\n")

    # Paso 4: Construir grafo
    print("4. Construyendo grafo en Neo4j...")
    result = construct_domain_graph()
    print(f"   OK {result}\n")

    # Paso 5: Consultar prestadores con más incumplimientos
    print("5. Consultando prestadores con más incumplimientos...")
    query = """
    MATCH (p:Prestador)<-[:GESTIONADO_POR]-(t:Tramite)<-[:DETECTADO_EN]-(i:Incumplimiento)
    RETURN p.nombre AS prestador, COUNT(i) AS incumplimientos
    ORDER BY incumplimientos DESC
    LIMIT 10
    """
    result = run_cypher_query(query)
    if result["status"] == "success":
        print(f"   OK Resultados:")
        for row in result.get("query_result", []):
            print(f"     - {row}")
    else:
        print(f"   ERROR {result}")

    print("\n=== Proceso completado ===")
