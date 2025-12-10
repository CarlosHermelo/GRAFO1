"""
schema_to_cypher.py

Lee un unified_schema.json (salida del primer script) y genera:

- Cypher para constraints/índices de nodos
- Plantillas LOAD CSV para:
  - creación de nodos desde CSV
  - creación de relaciones desde CSV

Opcionalmente, puede ejecutar el Cypher en Neo4j.

Uso típico:
1) Ejecutar schema_builder.py y guardar unified_schema.json
2) Ejecutar este script:
   python schema_to_cypher.py
"""

import os
import json
from typing import Dict, Any, List

from neo4j import GraphDatabase


# -----------------------------
# CONFIGURACIÓN
# -----------------------------

UNIFIED_SCHEMA_PATH = os.getenv("UNIFIED_SCHEMA_PATH", "unified_schema.json")
CYPHER_OUTPUT_PATH = os.getenv("CYPHER_OUTPUT_PATH", "generated_schema.cypher")

# Configuración Neo4j (solo si querés ejecutar el Cypher)
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

# Directorio de import que usará Neo4j (ajustar según tu entorno)
NEO4J_IMPORT_PREFIX = os.getenv("NEO4J_IMPORT_PREFIX", "file:///")  # p.ej. "file:///var/lib/neo4j/import/"


# -----------------------------
# HELPERS
# -----------------------------

def load_unified_schema(path: str) -> Dict[str, Any]:
    if not os.path.exists(path):
        raise FileNotFoundError(f"No se encontró el unified_schema en: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_neo4j_driver():
    return GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))


# -----------------------------
# GENERACIÓN CYPHER: NODOS
# -----------------------------

def generate_node_constraints(node: Dict[str, Any]) -> List[str]:
    """
    Genera constraints básicos para un nodo.
    Usa la primera key_column como clave principal si existe.
    """
    label = node.get("label")
    key_columns = node.get("key_columns") or []

    cypher_statements = []

    if not label:
        return cypher_statements

    if key_columns:
        key = key_columns[0]
        cypher_statements.append(
            f"CREATE CONSTRAINT IF NOT EXISTS FOR (n:{label}) "
            f"REQUIRE n.{key} IS NOT NULL;"
        )
    else:
        # Opcionalmente, se podría omitir o usar otro campo
        pass

    return cypher_statements


def generate_node_load_csv(node: Dict[str, Any]) -> List[str]:
    """
    Genera un template LOAD CSV para un nodo, si tiene source_files.
    """
    label = node.get("label")
    source_files = node.get("source_files") or []
    key_columns = node.get("key_columns") or []
    properties = node.get("properties") or {}

    if not label or not source_files:
        return []

    cypher_statements = []

    # Usar primera key_column como identificador principal
    if not key_columns:
        # Si no hay key_columns, no generamos LOAD CSV automático
        return cypher_statements

    key = key_columns[0]
    other_props = [p for p in properties.keys() if p != key]

    for file_name in source_files:
        file_uri = NEO4J_IMPORT_PREFIX + file_name

        set_clauses = []
        for prop in other_props:
            set_clauses.append(f"n.{prop} = row.{prop}")

        set_clause_str = ""
        if set_clauses:
            set_clause_str = "SET " + ", ".join(set_clauses)

        cypher = f"""
// Carga de nodos :{label} desde {file_name}
LOAD CSV WITH HEADERS FROM '{file_uri}' AS row
MERGE (n:{label} {{ {key}: row.{key} }})
{set_clause_str}
;
""".strip()

        cypher_statements.append(cypher)

    return cypher_statements


# -----------------------------
# GENERACIÓN CYPHER: RELACIONES
# -----------------------------

def generate_relationship_load_csv(rel: Dict[str, Any]) -> List[str]:
    """
    Genera template LOAD CSV para relaciones si tiene:
    - source_files
    - join_hints: from_column, to_column
    """
    type_ = rel.get("type") or "RELATED_TO"
    from_label = rel.get("from")
    to_label = rel.get("to")
    source_files = rel.get("source_files") or []
    join_hints = rel.get("join_hints") or {}
    properties = rel.get("properties") or {}

    if not from_label or not to_label or not source_files:
        return []

    from_col = join_hints.get("from_column")
    to_col = join_hints.get("to_column")

    if not from_col or not to_col:
        # Sin join_hints claros, no generamos plantilla
        return []

    cypher_statements = []

    # Propiedades de la relación: excluir columnas de join si se asumen iguales
    relationship_props = [
        p for p in properties.keys()
        if p not in (from_col, to_col)
    ]

    for file_name in source_files:
        file_uri = NEO4J_IMPORT_PREFIX + file_name

        set_clauses = []
        for prop in relationship_props:
            set_clauses.append(f"r.{prop} = row.{prop}")
        set_clause_str = ""
        if set_clauses:
            set_clause_str = "SET " + ", ".join(set_clauses)

        cypher = f"""
// Carga de relaciones :{type_} desde {file_name}
LOAD CSV WITH HEADERS FROM '{file_uri}' AS row
MATCH (from:{from_label} {{ {from_col}: row.{from_col} }})
MATCH (to:{to_label} {{ {to_col}: row.{to_col} }})
MERGE (from)-[r:{type_}]->(to)
{set_clause_str}
;
""".strip()

        cypher_statements.append(cypher)

    return cypher_statements


# -----------------------------
# GENERAR TODO EL CYPHER
# -----------------------------

def generate_cypher(schema: Dict[str, Any]) -> List[str]:
    statements: List[str] = []

    nodes = schema.get("nodes", [])
    rels = schema.get("relationships", [])

    # 1) Constraints / índices de nodos
    statements.append("// === Constraints de nodos ===")
    for n in nodes:
        stmts = generate_node_constraints(n)
        statements.extend(stmts)

    # 2) LOAD CSV para nodos
    statements.append("\n// === LOAD CSV para nodos ===")
    for n in nodes:
        stmts = generate_node_load_csv(n)
        statements.extend(stmts)

    # 3) LOAD CSV para relaciones
    statements.append("\n// === LOAD CSV para relaciones ===")
    for r in rels:
        stmts = generate_relationship_load_csv(r)
        statements.extend(stmts)

    return [s for s in statements if s and s.strip()]


def save_cypher(statements: List[str], path: str) -> None:
    content = "\n\n".join(statements)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Archivo Cypher generado en: {path}")


# -----------------------------
# EJECUTAR CYPHER EN NEO4J (OPCIONAL)
# -----------------------------

def execute_cypher(statements: List[str]) -> None:
    driver = get_neo4j_driver()
    with driver.session() as session:
        for stmt in statements:
            print(f"Ejecutando:\n{stmt}\n")
            session.run(stmt)
    driver.close()
    print("Ejecución de Cypher completada.")


# -----------------------------
# ENTRYPOINT
# -----------------------------

def main():
    schema = load_unified_schema(UNIFIED_SCHEMA_PATH)
    cypher_statements = generate_cypher(schema)
    save_cypher(cypher_statements, CYPHER_OUTPUT_PATH)

    # Si querés ejecutar automáticamente en Neo4j, poné esto en True
    run_in_neo4j = False
    if run_in_neo4j:
        execute_cypher(cypher_statements)


if __name__ == "__main__":
    main()
