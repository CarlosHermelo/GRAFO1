# grafo_protesis_preguntas.py
from neo4j import GraphDatabase

# === 1. Conexión a Neo4j ===
URI = "neo4j+s://b0df6e44.databases.neo4j.io"
USER = "neo4j"
PASSWORD = "NQkXw6G9S7jO8wQXQIRpd5BX-g2t_bEvXweJVPSWO1g"
driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))

# === 2. Función de consulta ===
def query_graph(pregunta: str):
    """Interpreta una pregunta y ejecuta la consulta Cypher correspondiente."""
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

# === 3. Ejecución de preguntas ===
#query_graph("¿Qué proveedores presentan más trámites demorados?")
query_graph("¿Qué proveedores tienen más trámites demorados o con incidencias?")
