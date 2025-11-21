import json
import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configuración de Neo4j
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

if not NEO4J_PASSWORD:
    raise ValueError("NEO4J_PASSWORD no está configurada en las variables de entorno.")


def crear_nodos_y_relaciones(driver, data):
    """
    Crea nodos Servicio, Tipo y Subtipo según cada registro.
    Usa MERGE para evitar duplicados.
    Crea relaciones (Servicio)-[:TIENE_TIPO]->(Tipo)-[:TIENE_SUBTIPO]->(Subtipo)
    """
    def _crear_grafo(tx, rec):
        # Crear nodo Servicio
        tx.run(
            "MERGE (s:Servicio {nombre: $servicio})",
            servicio=rec.get("SERVICIO")
        )

        # Crear nodo Tipo
        tx.run(
            "MERGE (t:Tipo {nombre: $tipo})",
            tipo=rec.get("TIPO")
        )

        # Crear nodo Subtipo con propiedades
        tx.run(
            """
            MERGE (st:Subtipo {id_sub: $id_sub})
            SET st.nombre = $subtipo,
                st.copete = $copete,
                st.consiste = $consiste
            """,
            id_sub=rec.get("ID_SUB"),
            subtipo=rec.get("SUBTIPO"),
            copete=rec.get("COPETE"),
            consiste=rec.get("CONSISTE")
        )

        # Crear relación (Servicio)-[:TIENE_TIPO]->(Tipo)
        tx.run(
            """
            MATCH (s:Servicio {nombre: $servicio}), (t:Tipo {nombre: $tipo})
            MERGE (s)-[:TIENE_TIPO]->(t)
            """,
            servicio=rec.get("SERVICIO"),
            tipo=rec.get("TIPO")
        )

        # Crear relación (Tipo)-[:TIENE_SUBTIPO]->(Subtipo)
        tx.run(
            """
            MATCH (t:Tipo {nombre: $tipo}), (st:Subtipo {id_sub: $id_sub})
            MERGE (t)-[:TIENE_SUBTIPO]->(st)
            """,
            tipo=rec.get("TIPO"),
            id_sub=rec.get("ID_SUB")
        )

    with driver.session() as session:
        for i, rec in enumerate(data["RECORDS"], 1):
            session.execute_write(_crear_grafo, rec)
            if i % 10 == 0:
                print(f"Procesados {i} registros...")
        print(f"Total de {len(data['RECORDS'])} registros procesados exitosamente.")


def consulta_prueba(driver):
    """
    Ejecuta una consulta de prueba: MATCH (s:Subtipo) RETURN s LIMIT 5
    Muestra los resultados por consola.
    """
    def _ejecutar_consulta(tx):
        result = tx.run("MATCH (s:Subtipo) RETURN s LIMIT 5")
        return list(result)

    with driver.session() as session:
        resultados = session.execute_read(_ejecutar_consulta)

        print("\n=== Consulta de prueba: Primeros 5 Subtipos ===")
        for i, record in enumerate(resultados, 1):
            subtipo = record["s"]
            print(f"\nSubtipo {i}:")
            print(f"  ID: {subtipo.get('id_sub')}")
            print(f"  Nombre: {subtipo.get('nombre')}")
            print(f"  Copete: {subtipo.get('copete', 'N/A')[:100]}...")  # Primeros 100 caracteres
            print(f"  Consiste: {subtipo.get('consiste', 'N/A')[:100]}...")


if __name__ == "__main__":
    # Cargar JSON
    print("Cargando datos desde datos.json...")
    with open("datos.json", encoding="utf-8") as f:
        data = json.load(f)

    num_registros = len(data.get("RECORDS", []))
    print(f"Se cargaron {num_registros} registros desde datos.json\n")

    # Conectar a Neo4j
    print(f"Conectando a Neo4j en {NEO4J_URI}...")
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

    try:
        # Crear nodos y relaciones
        print("\nCreando nodos y relaciones en Neo4j...")
        crear_nodos_y_relaciones(driver, data)

        # Ejecutar consulta de prueba
        print("\nEjecutando consulta de prueba...")
        consulta_prueba(driver)

        print("\n¡Proceso completado exitosamente!")

    finally:
        # Cerrar conexión
        driver.close()
        print("\nConexión a Neo4j cerrada.")
