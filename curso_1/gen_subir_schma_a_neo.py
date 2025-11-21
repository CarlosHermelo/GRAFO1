import os
from dotenv import load_dotenv
from neo4j import GraphDatabase

# cargar variables de entorno
load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

# leer archivo cypher
def load_cypher_from_file(path: str) -> str:
    if not os.path.exists(path):
        raise FileNotFoundError(f"No existe el archivo: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

# ejecutar script
def run_script(cypher: str):
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    with driver.session() as session:
        statements = [s.strip() for s in cypher.split(";") if s.strip()]

        print(f"Total de sentencias a ejecutar: {len(statements)}")

        for idx, stmt in enumerate(statements, start=1):
            preview = stmt.replace("\n", " ")[:80]
            print(f"[{idx}/{len(statements)}] Ejecutando: {preview} ...")

            try:
                session.run(stmt)
            except Exception as e:
                print("Error ejecutando sentencia:")
                print(stmt)
                print(e)
                break  # detener en caso de error serio

    driver.close()
    print("Proceso finalizado.")

if __name__ == "__main__":
    path = "grafo_generado.cypher"
    cypher_script = load_cypher_from_file(path)
    print("Ejecutando Cypher...")
    run_script(cypher_script)
    print("Finalizado.")
