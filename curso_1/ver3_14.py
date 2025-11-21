import os
import json
import unicodedata
from typing import List
from openai import OpenAI
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()
client = OpenAI()

# =========================================================
# NORMALIZACIÓN ASCII (quita acentos y caracteres Unicode)
# =========================================================

def normalize_ascii(text: str) -> str:
    nfkd = unicodedata.normalize("NFKD", text)
    return nfkd.encode("ASCII", "ignore").decode("ASCII")


# =========================================================
# LECTURA DEL ARCHIVO
# =========================================================

def load_text_from_file(path: str) -> str:
    if not os.path.exists(path):
        raise FileNotFoundError(f"No se encontró el archivo: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


# =========================================================
# MODELOS Pydantic
# =========================================================

class Concept(BaseModel):
    name: str
    reasoning: str

class ConceptList(BaseModel):
    concepts: List[Concept]

class Cluster(BaseModel):
    cluster_name: str
    members: List[str]
    reasoning: str

class ClusterList(BaseModel):
    clusters: List[Cluster]

class NormalizedEntity(BaseModel):
    original: str
    normalized_type: str
    reasoning: str

class NormalizedList(BaseModel):
    normalized: List[NormalizedEntity]

class Relation(BaseModel):
    subject: str
    predicate: str
    object: str
    reasoning: str

class RelationList(BaseModel):
    relations: List[Relation]


# =========================================================
# 1. EXTRACCIÓN DE CONCEPTOS
# =========================================================

def extract_concepts(text: str):
    system = """
Extraé conceptos generales del texto.
No incluyas nombres propios ni instancias.
No incluyas frases largas.
Devuelve solo categorías conceptuales.
"""

    user = f"Texto:\n{text}\n\nExtraé conceptos generales."

    resp = client.beta.chat.completions.parse(
        model="gpt-5-nano",
        messages=[
            {"role":"system", "content":system},
            {"role":"user", "content":user}
        ],
        response_format=ConceptList
    )

    return resp.choices[0].message.parsed.concepts


# =========================================================
# 2. CLUSTERING
# =========================================================

def cluster_concepts(concepts: List[Concept]):
    names = [c.name for c in concepts]

    system = """
Agrupá conceptos en clases conceptuales generales.
Ejemplos: Documento, Organizacion, Proceso, Norma, Persona, Accion.
"""

    user = f"Conceptos detectados:\n{names}"

    resp = client.beta.chat.completions.parse(
        model="gpt-5-nano",
        messages=[
            {"role":"system", "content":system},
            {"role":"user", "content":user}
        ],
        response_format=ClusterList
    )

    return resp.choices[0].message.parsed.clusters


# =========================================================
# 3. NORMALIZACIÓN DE ENTIDADES
# =========================================================

def normalize_entities(text: str, clusters: List[Cluster]):
    cluster_map = {c.cluster_name: c.members for c in clusters}

    system = """
Identificá entidades concretas del texto y asigná a cada una
la clase conceptual correspondiente.
"""

    user = f"Texto:\n{text}\n\nClases disponibles:\n{json.dumps(cluster_map, indent=2)}"

    resp = client.beta.chat.completions.parse(
        model="gpt-5-nano",
        messages=[
            {"role":"system", "content":system},
            {"role":"user", "content":user}
        ],
        response_format=NormalizedList
    )

    return resp.choices[0].message.parsed.normalized


# =========================================================
# 4. INFERENCIA GENÉRICA DE TIPO DE ENTIDAD
# =========================================================

def infer_generic_type(entity_name: str, clusters: List[Cluster]):
    cluster_map = {c.cluster_name: c.members for c in clusters}

    system = """
Dada una entidad concreta, inferí el tipo conceptual general que le corresponde.
Ejemplos: Documento, Norma, Organizacion, Proceso, Registro.
"""

    user = f"Entidad: {entity_name}\n\nClases conceptuales:\n{json.dumps(cluster_map, indent=2)}"

    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role":"system", "content":system},
            {"role":"user", "content":user}
        ]
    )

    return resp.choices[0].message.content.strip()


# =========================================================
# 5. EXTRACCIÓN DE RELACIONES
# =========================================================

def extract_relations(text: str, normalized_entities):
    ent_types = [e["type"] for e in normalized_entities]

    system = """
Extraé tipos generales de relaciones conceptuales entre clases.
Ejemplos: APRUEBA, DEROGA, CONTIENE, MODIFICA, REGULA.
"""

    user = f"Texto:\n{text}\n\nTipos de entidad:\n{ent_types}"

    resp = client.beta.chat.completions.parse(
        model="gpt-5-nano",
        messages=[
            {"role":"system", "content":system},
            {"role":"user", "content":user}
        ],
        response_format=RelationList
    )

    return resp.choices[0].message.parsed.relations


# =========================================================
# 6. EXPORTAR A CYPHER
# =========================================================

def export_to_cypher(normalized_entities, relations, output_file="graph_import.cypher"):
    lines = []

    # --- Crear nodos ---
    for ent in normalized_entities:
        label = normalize_ascii(ent["type"]).replace(" ", "_")
        node_id = normalize_ascii(ent["original"]).replace(" ", "_").replace("-", "_").replace("#","_")
        lines.append(f'CREATE (:{label} {{id:"{node_id}"}});')

    # --- Crear relaciones ---
    for rel in relations:
        src = normalize_ascii(rel.subject).replace(" ", "_").replace("-", "_").replace("#","_")
        trg = normalize_ascii(rel.object).replace(" ", "_").replace("-", "_").replace("#","_")
        pred = normalize_ascii(rel.predicate).replace(" ", "_")

        lines.append(
            f'MATCH (a {{id:"{src}"}}), (b {{id:"{trg}"}}) '
            f'CREATE (a)-[:{pred}]->(b);'
        )

    # Guardar a archivo
    with open(output_file, "w", encoding="utf-8") as f:
        for line in lines:
            f.write(line + "\n")

    print(f"\nArchivo Cypher generado: {output_file}")


# =========================================================
# MAIN
# =========================================================

def main():
    file_path = r"C:\Users\u14527001\Downloads\grafo_protesis\curso_1\RESOL-2024-2076.txt"

    print("Leyendo archivo...")
    text = load_text_from_file(file_path)

    print("\n=== 1) Conceptos ===")
    concepts = extract_concepts(text)
    for c in concepts:
        print("-", c.name)

    print("\n=== 2) Clustering ===")
    clusters = cluster_concepts(concepts)
    for c in clusters:
        print("\nClase:", c.cluster_name)
        print("Miembros:", c.members)

    print("\n=== 3) Normalización ===")
    normalized_raw = normalize_entities(text, clusters)
    for n in normalized_raw:
        print("-", n.original, "→", n.normalized_type)

    print("\n=== 4) Inferencia genérica ===")
    final_entities = []
    for n in normalized_raw:
        t = infer_generic_type(n.original, clusters)
        final_entities.append({"original": n.original, "type": t})
        print("-", n.original, "→", t)

    print("\n=== 5) Relaciones ===")
    relations = extract_relations(text, final_entities)
    for r in relations:
        print(f"({r.subject}) --[{r.predicate}]--> ({r.object})")

    # EXPORTAR A CYPHER
    export_to_cypher(final_entities, relations)


if __name__ == "__main__":
    main()
