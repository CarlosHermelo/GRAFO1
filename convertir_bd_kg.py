# grafo_protesis_auto_semantico.py
import os
import pandas as pd
from neo4j import GraphDatabase

# =======================================================
# 1. Conexión Neo4j
# =======================================================
URI = "neo4j+s://b0df6e44.databases.neo4j.io"
USER = "neo4j"
PASSWORD = "NQkXw6G9S7jO8wQXQIRpd5BX-g2t_bEvXweJVPSWO1g"

driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))

# =======================================================
# 2. Diccionario automático de entidades (detecta CSV)
# =======================================================
def detectar_entidades():
    archivos = [f for f in os.listdir() if f.lower().endswith(".csv")]
    entidades = {os.path.splitext(f)[0].capitalize(): f for f in archivos}
    return entidades

# =======================================================
# 3. Motor semántico
# =======================================================
SEMANTIC_RULES = {
    ("Tramite", "id_afiliado"): ("Afiliado", "TRAMITE_DE"),
    ("Tramite", "id_prestador"): ("Prestador", "GESTIONADO_POR"),
    ("Tramite", "id_proveedor"): ("Proveedor", "ASIGNADO_A"),
    ("Tramite", "id_protesis"): ("Protesis", "SOLICITA"),
    ("Mensaje", "id_tramite"): ("Tramite", "ASOCIADO_A"),
    ("Notificacion_interna", "id_tramite"): ("Tramite", "RELACIONADA_CON"),
    ("Incumplimiento", "id_tramite"): ("Tramite", "DETECTADO_EN"),
}

# =======================================================
# 4. Detectar relaciones con reglas semánticas
# =======================================================
def detectar_relaciones(entidades):
    relaciones = []

    for entidad, archivo in entidades.items():
        df = pd.read_csv(archivo)
        columnas = df.columns

        for col in columnas:
            if not col.startswith("id_"):
                continue

            clave = (entidad, col)

            # Si la regla semántica existe → relación válida
            if clave in SEMANTIC_RULES:
                target_entity, rel_name = SEMANTIC_RULES[clave]
                if target_entity in entidades:
                    relaciones.append({
                        "from": entidad,
                        "to": target_entity,
                        "type": rel_name,
                        "file": archivo,
                        "from_col": col,
                        "to_col": f"id_{target_entity.lower()}"
                    })

    return relaciones

# =======================================================
# 5. Construcción del grafo
# =======================================================
def construir_grafo(entidades, relaciones):
    with driver.session() as session:

        print("Limpiando base…")
        session.run("MATCH (n) DETACH DELETE n")

        print("Cargando nodos…")
        for entidad, archivo in entidades.items():
            df = pd.read_csv(archivo)
            for _, fila in df.iterrows():
                props = {k: v for k, v in fila.items() if pd.notna(v)}
                session.run(f"CREATE (n:{entidad} $props)", props=props)
            print(f"{entidad}: {len(df)} nodos")

        print("Cargando relaciones…")
        for rel in relaciones:
            df = pd.read_csv(rel["file"])
            for _, fila in df.iterrows():
                session.run(
                    f"""
                    MATCH (a:{rel['from']}) WHERE a.{rel['from_col']} = $from_id
                    MATCH (b:{rel['to']})   WHERE b.{rel['to_col']}   = $to_id
                    CREATE (a)-[:{rel['type']}]->(b)
                    """,
                    {"from_id": fila[rel["from_col"]], "to_id": fila[rel["to_col"]]},
                )
            print(f"Relaciones creadas: {rel['type']}")

    print("Grafo construido completamente.")

# =======================================================
# 6. Consultas de ejemplo
# =======================================================
def ejemplo_consultas():
    print("\nConsultas de ejemplo:")
    with driver.session() as session:
        result = session.run("""
            MATCH (p:Prestador)<-[:GESTIONADO_POR]-(t:Tramite)<-[:DETECTADO_EN]-(i:Incumplimiento)
            RETURN p.nombre as prestador, count(i) as total
            ORDER BY total DESC
        """)
        for r in result:
            print(r)

# =======================================================
# 7. Ejecución del pipeline automático
# =======================================================
if __name__ == "__main__":
    print("Detectando entidades…")
    entidades = detectar_entidades()
    print(entidades)

    print("\nDetectando relaciones semánticas…")
    relaciones = detectar_relaciones(entidades)
    for r in relaciones:
        print(r)

    print("\nConstruyendo grafo…")
    construir_grafo(entidades, relaciones)

    ejemplo_consultas()

    print("\nPipeline automático completo.")
