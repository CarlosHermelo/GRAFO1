from neo4j import GraphDatabase
import re

# Configuración de Neo4j
URI = "neo4j+s://b0df6e44.databases.neo4j.io"
AUTH = ("neo4j", "NQkXw6G9S7jO8wQXQIRpd5BX-g2t_bEvXweJVPSWO1g")

driver = GraphDatabase.driver(URI, auth=AUTH)

def parse_triple(line):
    # Eliminar BOM si existe
    line = line.replace("\ufeff", "").strip()

    # Formato correcto: (A)-[REL]->(B)
    match = re.match(r'\(([^)]+)\)-\[(\w+)\]->\(([^)]+)\)', line)
    if match:
        return match.group(1), match.group(2), match.group(3)
    return None

def import_triple(tx, sujeto, relacion, objeto):
    query = """
    MERGE (s:Entidad {id: $s})
    MERGE (o:Entidad {id: $o})
    CALL apoc.merge.relationship(s, $r, {}, {}, o) YIELD rel
    SET rel.fecha = date()
    RETURN rel
    """
    tx.run(query, s=sujeto, r=relacion, o=objeto)

def main():
    with driver.session() as session:
        count = 0
        with open('triples.csv', 'r', encoding='utf-8') as f:
            for i, line in enumerate(f, 1):

                if not line.strip():
                    continue

                triple = parse_triple(line)

                if triple:
                    s, r, o = triple
                    session.execute_write(import_triple, s, r, o)
                    print(f"OK {count+1}: {s} -[{r}]-> {o}")
                    count += 1
                else:
                    print(f"Línea no reconocida {i}: {line.strip()}")

        print(f"\nImportación completada: {count} tripletas.")

if __name__ == "__main__":
    main()
