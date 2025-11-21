import os
import json
from typing import List, Dict
from openai import OpenAI
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()
client = OpenAI()


# lector de archivo

def load_text_from_file(path: str) -> str:
    if not os.path.exists(path):
        raise FileNotFoundError(f"No se encontró el archivo: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


# modelos pydantic

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


# 1. extracción de conceptos

def extract_concepts(text: str):
    system = """
Extraé conceptos generales del texto.
No incluyas nombres propios ni instancias concretas.
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


# 2. clustering de conceptos

def cluster_concepts(concepts: List[Concept]):
    names = [c.name for c in concepts]

    system = """
Agrupá conceptos en clases conceptuales generales.
Ejemplos: Documento, Organizacion, Proceso, Norma, Persona, Accion.
Las clases deben ser reutilizables en cualquier dominio.
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


# 3. normalización de entidades concretas → clases conceptuales

def normalize_entities(text: str, clusters: List[Cluster]):
    cluster_map = {c.cluster_name: c.members for c in clusters}

    system = """
Identificá entidades concretas presentes en el texto
y asigná cada una a la clase conceptual que le corresponda.
Si no existe clase adecuada, creá una nueva clase general (no específica).
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


# 4. inferencia genérica de tipo de entidad (modelo agnóstico al dominio)

def infer_generic_type(entity_name: str, clusters: List[Cluster]):
    cluster_map = {c.cluster_name: c.members for c in clusters}

    system = """
Dada una entidad concreta, inferí el tipo conceptual que le corresponde.
Debe ser general y aplicable en cualquier dominio.
Ejemplos: Documento, Proceso, Organizacion, Norma, Registro, Item, Persona.
Si ninguna clase conocida aplica, creá un tipo conceptual nuevo pero general.
"""

    user = f"Entidad: {entity_name}\n\nClases conceptuales:\n{json.dumps(cluster_map, indent=2)}"

    resp = client.chat.completions.create(
        model="gpt-5-nano",
        messages=[
            {"role":"system", "content":system},
            {"role":"user", "content":user}
        ]
    )
    return resp.choices[0].message.content.strip()


# 5. extracción de relaciones conceptuales

def extract_relations(text: str, normalized_entities: List[Dict]):
    types = [e["type"] for e in normalized_entities]

    system = """
Extraé tipos generales de relaciones conceptuales entre clases.
Ejemplos: APRUEBA, CONTIENE, RELACIONA, DEPENDE_DE, DEFINE, MODIFICA.
Las relaciones deben ser abstractas, no específicas del documento.
"""

    user = f"Texto:\n{text}\n\nTipos de entidad disponibles:\n{types}"

    resp = client.beta.chat.completions.parse(
        model="gpt-5-nano",
        messages=[
            {"role":"system", "content":system},
            {"role":"user", "content":user}
        ],
        response_format=RelationList
    )

    return resp.choices[0].message.parsed.relations


# main

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
        print(f"\nClase:", c.cluster_name)
        print("Miembros:", c.members)

    print("\n=== 3) Normalización ===")
    normalized_raw = normalize_entities(text, clusters)
    for n in normalized_raw:
        print("-", n.original, "→", n.normalized_type)

    print("\n=== 4) Inferencia genérica de tipo de entidad ===")
    final_entities = []
    for n in normalized_raw:
        inferred = infer_generic_type(n.original, clusters)
        final_entities.append({"original": n.original, "type": inferred})
        print("-", n.original, "→", inferred)

    print("\n=== 5) Relaciones conceptuales ===")
    relations = extract_relations(text, final_entities)
    for r in relations:
        print(f"({r.subject}) --[{r.predicate}]--> ({r.object})")

    print("\n=== Esquema final ===")
    schema = [
        {"source_type": r.subject, "relationship": r.predicate, "target_type": r.object}
        for r in relations
    ]
    print(json.dumps(schema, indent=2))


if __name__ == "__main__":
    main()
