import os
from dotenv import load_dotenv
from neo4j import GraphDatabase

# --------------------------------------------------
# 1. Cargar variables de entorno
# --------------------------------------------------
load_dotenv()

URI = os.getenv("NEO4J_URI")
USER = os.getenv("NEO4J_USER")
PASSWORD = os.getenv("NEO4J_PASSWORD")

if not URI or not USER or not PASSWORD:
    raise ValueError("Faltan variables NEO4J_URI, NEO4J_USER o NEO4J_PASSWORD en el .env")

driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))


# --------------------------------------------------
# 2. Borrar todos los nodos y relaciones
# --------------------------------------------------
def delete_all_nodes(tx):
    tx.run("MATCH (n) DETACH DELETE n")


# --------------------------------------------------
# 3. Listar constraints
# --------------------------------------------------
def list_constraints(tx):
    result = tx.run("SHOW CONSTRAINTS YIELD name RETURN name")
    return [record["name"] for record in result]


# --------------------------------------------------
# 4. Borrar constraint por nombre
# --------------------------------------------------
def drop_constraint(tx, name):
    query = f"DROP CONSTRAINT {name} IF EXISTS"
    tx.run(query)


# --------------------------------------------------
# MAIN
# --------------------------------------------------
with driver.session() as session:

    print("Eliminando todos los nodos y relaciones...")
    session.execute_write(delete_all_nodes)
    print("✔ Nodos y relaciones eliminados.\n")

    print("Listado de constraints...")
    constraints = session.execute_read(list_constraints)

    if not constraints:
        print("No se encontraron constraints.")
    else:
        print(f"Encontradas {len(constraints)} constraints:")
        for c in constraints:
            print(" -", c)

        print("\nEliminando constraints...")
        for c in constraints:
            session.execute_write(drop_constraint, c)
            print(f"✔ Eliminada: {c}")

driver.close()
print("\nProceso completado.")
