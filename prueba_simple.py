from neo4j import GraphDatabase

URI = "neo4j+s://b0df6e44.databases.neo4j.io"
USER = "neo4j"
PASSWORD = "NQkXw6G9S7jO8wQXQIRpd5BX-g2t_bEvXweJVPSWO1g"

driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))

def test_neo4j(tx):
    tx.run("CREATE (a:Persona {nombre: 'Alice'})-[:CONOCE]->(b:Persona {nombre: 'Bob'})")
    result = tx.run("MATCH (a:Persona)-[:CONOCE]->(b:Persona) RETURN a.nombre AS origen, b.nombre AS destino")
    for record in result:
        print(f"{record['origen']} conoce a {record['destino']}")

with driver.session() as session:
    session.execute_write(test_neo4j)

driver.close()
