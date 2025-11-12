# grafo_protesis_adk_simulado.py
from neo4j import GraphDatabase
import pandas as pd

# ============================================
# 1. Conexión a tu base Neo4j (ajustada a tu instancia)
# ============================================
URI = "neo4j+s://b0df6e44.databases.neo4j.io"
USER = "neo4j"
PASSWORD = "NQkXw6G9S7jO8wQXQIRpd5BX-g2t_bEvXweJVPSWO1g"

driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))


# ============================================
# 2. Simulación de funciones del curso ADK
# ============================================

context = {}

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

def construct_domain_graph():
    schema = context.get("approved_schema")
    plan = context.get("approved_construction_plan")

    with driver.session() as session:
        # Limpiar base antes de construir
        session.run("MATCH (n) DETACH DELETE n")
        print("🧹 Base limpiada.")

        # Crear nodos
        for entidad, archivo in plan["data_sources"].items():
            df = pd.read_csv(archivo)
            for _, fila in df.iterrows():
                props = {k: v for k, v in fila.items() if pd.notna(v)}
                session.run(f"CREATE (n:{entidad} $props)", props=props)
            print(f"✔ Nodos creados para entidad: {entidad} ({len(df)} registros)")

        # Crear relaciones
        for rel in plan["relationships"]:
            tipo = rel["type"]
            archivo = rel["file"]
            df = pd.read_csv(archivo)
            from_col = rel["from"]
            to_col = rel["to"]

            for _, fila in df.iterrows():
                session.run(
                    f"""
                    MATCH (a:{_infer_label(from_col)}) WHERE a.{from_col} = $from_id
                    MATCH (b:{_infer_label(to_col)}) WHERE b.{to_col} = $to_id
                    CREATE (a)-[r:{tipo}]->(b)
                    """,
                    {"from_id": fila[from_col], "to_id": fila[to_col]},
                )
            print(f"🔗 Relaciones {tipo} creadas desde {archivo}")

    print("✅ Grafo construido exitosamente.")

def _infer_label(col_name):
    """Deducción simple del label según el nombre del campo FK."""
    if "afiliado" in col_name: return "Afiliado"
    if "prestador" in col_name: return "Prestador"
    if "proveedor" in col_name: return "Proveedor"
    if "protesis" in col_name: return "Protesis"
    if "tramite" in col_name: return "Tramite"
    if "mensaje" in col_name: return "Mensaje"
    if "notificacion" in col_name: return "NotificacionInterna"
    if "incumplimiento" in col_name: return "Incumplimiento"
    return "Desconocido"

def query_graph(pregunta: str):
    """Simula query natural, resolviendo a consultas Cypher básicas."""
    print(f"\n🤖 Consulta: {pregunta}")
    with driver.session() as session:
        if "proveedor" in pregunta.lower() and "demora" in pregunta.lower():
            result = session.run("""
                MATCH (p:Proveedor)<-[:ASIGNADO_A]-(t:Tramite)
                WHERE t.estado = 'Demorado'
                RETURN p.nombre AS proveedor, count(t) AS total
                ORDER BY total DESC LIMIT 10
            """)
            for r in result:
                print(f"Proveedor: {r['proveedor']} | Trámites demorados: {r['total']}")
        elif "prestador" in pregunta.lower() and "incumplimiento" in pregunta.lower():
            result = session.run("""
                MATCH (pr:Prestador)<-[:GESTIONADO_POR]-(t:Tramite)<-[:DETECTADO_EN]-(i:Incumplimiento)
                RETURN pr.nombre AS prestador, count(i) AS total
                ORDER BY total DESC LIMIT 10
            """)
            for r in result:
                print(f"Prestador: {r['prestador']} | Incumplimientos: {r['total']}")
        else:
            print("⚠️ Consulta no reconocida en este modo de simulación.")

# ============================================
# 3. Ejecución del flujo como en el curso
# ============================================

# 3.1 Objetivo
set_perceived_user_goal(
    "Analizar y gestionar la trazabilidad completa de trámites de prótesis entre prestadores, proveedores, afiliados y PAMI, identificando demoras, errores y patrones de incumplimiento"
)
approve_user_goal()

# 3.2 Esquema
approved_schema = {
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
approve_schema(approved_schema)

# 3.3 Plan de construcción
approved_construction_plan = {
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
approve_construction_plan(approved_construction_plan)

# 3.4 Construcción
construct_domain_graph()

# 3.5 Consultas
query_graph("¿Qué proveedores presentan más trámites demorados?")
query_graph("¿Qué prestadores tienen más incumplimientos?")

print("\n✅ Flujo ADK completado correctamente.")
