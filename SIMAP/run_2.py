# grafo_simap_adk.py
# Construcción de un grafo de conocimiento SIMAP (servicios PAMI) con flujo ADK

from neo4j import GraphDatabase
import json

# ============================================
# 1. Conexión a Neo4j
# ============================================
URI = "neo4j+s://b0df6e44.databases.neo4j.io"
USER = "neo4j"
PASSWORD = "NQkXw6G9S7jO8wQXQIRpd5BX-g2t_bEvXweJVPSWO1g"

driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))
context = {}

# ============================================
# 2. Funciones estilo ADK
# ============================================
def set_perceived_user_goal(goal: str):
    context["perceived_user_goal"] = goal
    print(f"✅ Objetivo definido: {goal}")
    return goal

def approve_user_goal():
    context["approved_user_goal"] = context.get("perceived_user_goal")
    print("✅ Objetivo aprobado.")
    return context["approved_user_goal"]

def approve_schema(schema: dict):
    context["approved_schema"] = schema
    print("✅ Esquema del grafo aprobado.")
    return schema

def approve_construction_plan(plan: dict):
    context["approved_construction_plan"] = plan
    print("✅ Plan de construcción aprobado.")
    return plan

# ============================================
# 3. Construcción del grafo desde JSON
# ============================================
def construct_domain_graph():
    plan = context.get("approved_construction_plan")
    json_path = plan["data_source"]

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)["RECORDS"]

    with driver.session() as session:
        session.run("MATCH (n) DETACH DELETE n")
        print("🧹 Base limpiada.")

        for r in data:
            servicio = r.get("SERVICIO", "").strip()
            tipo = r.get("TIPO", "").strip()
            subtipo = r.get("SUBTIPO", "").strip()

            # Crear jerarquía principal
            session.run("""
                MERGE (s:Servicio {nombre:$servicio})
                MERGE (t:Tipo {nombre:$tipo})
                MERGE (st:Subtipo {nombre:$subtipo})
                MERGE (s)-[:TIENE_TIPO]->(t)
                MERGE (t)-[:TIENE_SUBTIPO]->(st)
            """, servicio=servicio, tipo=tipo, subtipo=subtipo)

            # Crear campos textuales
            for campo, valor in r.items():
                if campo not in ["SERVICIO", "TIPO", "SUBTIPO", "ID_SUB"] and valor:
                    texto = str(valor).strip()
                    if texto:
                        session.run("""
                            MERGE (c:Campo {nombre:$campo})
                            MERGE (txt:Contenido {texto:$texto})
                            MERGE (st:Subtipo {nombre:$subtipo})
                            MERGE (st)-[:TIENE_CAMPO]->(c)
                            MERGE (c)-[:DESCRIBE]->(txt)
                        """, campo=campo, texto=texto, subtipo=subtipo)
        print("✅ Grafo SIMAP construido correctamente.")

# ============================================
# 4. Consulta simulada (sin LLM aún)
# ============================================
def query_graph(pregunta: str):
    """Simula una consulta textual simple al grafo."""
    print(f"\n🤖 Consulta: {pregunta}")
    with driver.session() as session:
        if "requisito" in pregunta.lower():
            result = session.run("""
                MATCH (st:Subtipo)-[:TIENE_CAMPO]->(c:Campo {nombre:'REQUISITOS'})-[:DESCRIBE]->(txt:Contenido)
                RETURN st.nombre AS subtipo, txt.texto AS requisitos
                LIMIT 5
            """)
            for r in result:
                print(f"🧩 {r['subtipo']}: {r['requisitos'][:150]}...")
        elif "como" in pregunta.lower():
            result = session.run("""
                MATCH (st:Subtipo)-[:TIENE_CAMPO]->(c:Campo {nombre:'COMO_LO_HACEN'})-[:DESCRIBE]->(txt:Contenido)
                RETURN st.nombre AS subtipo, txt.texto AS procedimiento
                LIMIT 5
            """)
            for r in result:
                print(f"🧩 {r['subtipo']}: {r['procedimiento'][:150]}...")
        else:
            print("⚠️ Consulta no reconocida en este modo de simulación.")

# ============================================
# 5. Flujo de ejecución estilo ADK
# ============================================
set_perceived_user_goal(
    "Organizar la información de los servicios SIMAP del PAMI en un grafo de conocimiento para responder preguntas sobre requisitos, tipos y procedimientos."
)
approve_user_goal()

approved_schema = {
    "entities": ["Servicio", "Tipo", "Subtipo", "Campo", "Contenido"],
    "relationships": [
        {"from": "Servicio", "to": "Tipo", "type": "TIENE_TIPO"},
        {"from": "Tipo", "to": "Subtipo", "type": "TIENE_SUBTIPO"},
        {"from": "Subtipo", "to": "Campo", "type": "TIENE_CAMPO"},
        {"from": "Campo", "to": "Contenido", "type": "DESCRIBE"}
    ]
}
approve_schema(approved_schema)

approved_construction_plan = {
    "data_source": "simap_docs.json"
}
approve_construction_plan(approved_construction_plan)

construct_domain_graph()

# Ejemplo de preguntas
query_graph("¿Cuáles son los requisitos?")
query_graph("¿Cómo se realiza una afiliación?")
print("\n✅ Flujo SIMAP-ADK completado correctamente.")
