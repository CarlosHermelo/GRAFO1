# grafo_autodetect.py
# Versión automática completa sin ADK

import os
import pandas as pd
from neo4j import GraphDatabase

# ============================================
# 1. Conexión Neo4j
# ============================================
URI = "neo4j+s://b0df6e44.databases.neo4j.io"
USER = "neo4j"
PASSWORD = "NQkXw6G9S7jO8wQXQIRpd5BX-g2t_bEvXweJVPSWO1g"

driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))

# ============================================
# 2. Utilidades
# ============================================

def normalize_entity(filename):
    base = filename.replace(".csv", "")
    return base.capitalize()

def detect_entities(csv_files):
    return {normalize_entity(f): f for f in csv_files}

def detect_relationships(entities, dataframes):
    relaciones = []
    entity_names = set(entities.keys())

    for entidad, df in dataframes.items():
        columnas = df.columns
        for col in columnas:
            if col.startswith("id_"):
                posible = col.replace("id_", "").capitalize()
                if posible in entity_names:
                    relaciones.append({
                        "from": entidad,
                        "to": posible,
                        "type": f"{entidad.upper()}_TO_{posible.upper()}",
                        "file": entities[entidad],
                        "from_col": col,
                        "to_col": f"id_{posible.lower()}"
                    })

    return relaciones

def validate_csv(df, archivo):
    if df.empty:
        raise ValueError(f"El archivo {archivo} está vacío.")
    if df.isna().all().all():
        raise ValueError(f"El archivo {archivo} no tiene datos útiles.")

def load_data(entities):
    dataframes = {}
    for entidad, archivo in entities.items():
        df = pd.read_csv(archivo)
        validate_csv(df, archivo)
        dataframes[entidad] = df
    return dataframes

def validate_relationships(relaciones, dataframes):
    for rel in relaciones:
        df_rel = dataframes[rel["from"]]
        if rel["from_col"] not in df_rel.columns:
            raise ValueError(f"Columna {rel['from_col']} no existe en {rel['file']}.")

        destino = rel["to"]
        if rel["to_col"] not in dataframes[destino].columns:
            raise ValueError(f"Columna destino {rel['to_col']} no existe en entidad {destino}.")

# ============================================
# 3. Construcción del grafo
# ============================================

def build_graph(entities, relationships, dataframes):
    print("Limpiando base...")
    with driver.session() as session:
        session.run("MATCH (n) DETACH DELETE n")

        print("Cargando nodos...")
        for entidad, df in dataframes.items():
            for _, fila in df.iterrows():
                props = {k: v for k, v in fila.items() if pd.notna(v)}
                session.run(f"CREATE (n:{entidad} $props)", props=props)
            print(f"{entidad}: {len(df)} nodos")

        print("Cargando relaciones...")
        for rel in relationships:
            origen = rel["from"]
            destino = rel["to"]
            archivo = rel["file"]
            df = pd.read_csv(archivo)

            for _, fila in df.iterrows():
                session.run(
                    f"""
                    MATCH (a:{origen}) WHERE a.{rel['from_col']} = $from_id
                    MATCH (b:{destino}) WHERE b.{rel['to_col']} = $to_id
                    CREATE (a)-[:{rel['type']}]->(b)
                    """,
                    {"from_id": fila[rel["from_col"]], "to_id": fila[rel["to_col"]]},
                )

            print(f"Relaciones creadas: {rel['type']}")

    print("Grafo construido completamente.")

# ============================================
# 4. Consultas básicas
# ============================================

def query_graph(pregunta):
    p = pregunta.lower()

    with driver.session() as session:
        if "demora" in p and "proveedor" in p:
            result = session.run("""
                MATCH (p:Proveedor)<-[]-(t:Tramite)
                WHERE t.estado = 'Demorado'
                RETURN p.nombre AS proveedor, count(t) AS total
            """)
            for r in result:
                print(r)

        elif "prestador" in p and "incumplimiento" in p:
            result = session.run("""
                MATCH (pr:Prestador)<-[]-(t:Tramite)<-[]-(i:Incumplimiento)
                RETURN pr.nombre AS prestador, count(i) AS total
            """)
            for r in result:
                print(r)

        else:
            print("Consulta no reconocida.")

# ============================================
# 5. Pipeline principal
# ============================================

def ejecutar_pipeline():
    print("\nDetectando archivos CSV...")
    csv_files = [f for f in os.listdir() if f.endswith(".csv")]
    if not csv_files:
        raise ValueError("No se encontraron archivos CSV en el directorio.")

    print("Archivos detectados:")
    for f in csv_files:
        print(" -", f)

    print("\nDetectando entidades...")
    entities = detect_entities(csv_files)
    print("Entidades:", entities)

    print("\nCargando datos...")
    dataframes = load_data(entities)

    print("\nDetectando relaciones...")
    relationships = detect_relationships(entities, dataframes)
    print("Relaciones inferidas:")
    for r in relationships:
        print(r)

    print("\nValidando relaciones...")
    validate_relationships(relationships, dataframes)

    print("\nConstruyendo grafo...")
    build_graph(entities, relationships, dataframes)

    print("\nConsultas de ejemplo:")
    query_graph("¿Qué proveedores presentan más trámites demorados?")
    query_graph("¿Qué prestadores tienen más incumplimientos?")

    print("\nPipeline automático completo.")

if __name__ == "__main__":
    ejecutar_pipeline()
