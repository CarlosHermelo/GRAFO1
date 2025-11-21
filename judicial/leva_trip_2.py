from neo4j import GraphDatabase
import re
import csv

# Configuración Neo4j
URI = "neo4j+s://b0df6e44.databases.neo4j.io"
AUTH = ("neo4j", "NQkXw6G9S7jO8wQXQIRpd5BX-g2t_bEvXweJVPSWO1g")

driver = GraphDatabase.driver(URI, auth=AUTH)

# Expresión regular para extraer la tripleta
PATRON = re.compile(r"\(([^)]+)\)-\[(\w+)\]->\(([^)]+)\)")

def procesar_tripleta(tx, sujeto, relacion, objeto):
    """
    Crea nodos Entidad para sujeto y objeto, y crea la relación correspondiente.
    """
    query = f"""
    MERGE (s:Entidad {{id: $sujeto}})
    MERGE (o:Entidad {{id: $objeto}})
    MERGE (s)-[r:{relacion}]->(o)
    SET r.fecha = date()
    """
    tx.run(query, sujeto=sujeto, objeto=objeto)

def importar_csv(ruta_csv):
    with driver.session() as session:
        with open(ruta_csv, encoding="utf-8") as f:
            for linea in f:
                linea = linea.lstrip("\ufeff")  # quita BOM
                linea = linea.strip()
                if not linea:
                    continue

                match = PATRON.match(linea)
                if not match:
                    print("Línea inválida:", linea)
                    continue

                sujeto, relacion, objeto = match.groups()

                session.execute_write(   # reemplaza write_transaction
                    procesar_tripleta,
                    sujeto,
                    relacion,
                    objeto
                )

                print("Cargado:", sujeto, relacion, objeto)
# Ejecutar importación
importar_csv("t_2.csv")

print("Importación completada.")
