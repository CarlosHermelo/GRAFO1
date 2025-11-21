import os
import json
import unicodedata
from typing import List, Dict
from openai import OpenAI
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()
client = OpenAI()

# ======================================================
# NORMALIZACIÓN: elimina acentos y caracteres Unicode
# ======================================================
def normalize_ascii(text: str) -> str:
    if not isinstance(text, str):
        return text
    nfkd = unicodedata.normalize("NFKD", text)
    return nfkd.encode("ASCII", "ignore").decode("ASCII")


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


# ============ 1. extracción de conceptos ============

def extract_concepts(text: str):
    system = """
Extrae conceptos generales del texto.
No incluyas nombres propios ni instancias concretas.
No incluyas frases largas.
Devuelve solo categorías conceptuales.
"""

    user = f"Texto:\n{text}\n\nExtrae conceptos generales."

    resp = client.beta.chat.completions.parse(
        model="gpt-5-nano",
        messages=[
            {"role":"system", "content":system},
            {"role":"user", "content":user}
        ],
        response_format=ConceptList
    )

    return resp.choices[0].message.parsed.concepts


# ============ 2. clustering ============

def cluster_concepts(concepts: List[Concept]):
    names = [normalize_ascii(c.name) for c in concepts]

    system = """
Agrupa conceptos en clases conceptuales generales.
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


# ============ 3. normalización de entidades ============

def normalize_entities(text: str, clusters: List[Cluster]):
    cluster_map = {normalize_ascii(c.cluster_name): [normalize_ascii(m) for m in c.members] for c in clusters}

    system = """
Identifica entidades concretas presentes en el texto
y asigna cada una a la clase conceptual adecuada.
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


# ============ 4. inferencia tipo general ============

def infer_generic_type(entity_name: str, clusters: List[Cluster]):
    cluster_map = {normalize_ascii(c.cluster_name): [normalize_ascii(m) for m in c.members] for c in clusters}

    system = """
Dada una entidad concreta, inferi el tipo conceptual general.
"""

    user = f"Entidad: {normalize_ascii(entity_name)}\n\nClases:\n{json.dumps(cluster_map, indent=2)}"

    resp = client.chat.completions.create(
        model="gpt-5-nano",
        messages=[
            {"role":"system", "content":system},
            {"role":"user", "content":user}
        ]
    )
    return normalize_ascii(resp.choices[0].message.content.strip())


# ============ 5. extracción de relaciones ============

def extract_relations(text: str, normalized_entities: List[Dict]):
    types = [normalize_ascii(e["type"]) for e in normalized_entities]

    system = """
Extrae relaciones conceptuales generales.
"""

    user = f"Texto:\n{text}\n\nTipos disponibles:\n{types}"

    resp = client.beta.chat.completions.parse(
        model="gpt-5-nano",
        messages=[
            {"role":"system", "content":system},
            {"role":"user", "content":user}
        ],
        response_format=RelationList
    )

    # normalizamos todo
    cleaned = []
    for r in resp.choices[0].message.parsed.relations:
        cleaned.append(
            Relation(
                subject=normalize_ascii(r.subject),
                predicate=normalize_ascii(r.predicate),
                object=normalize_ascii(r.object),
                reasoning=normalize_ascii(r.reasoning)
            )
        )
    return cleaned


# ============ MAIN ============

def main():
    file_path = r"C:\Users\u14527001\Downloads\grafo_protesis\curso_1\RESOL-2024-2076.txt"

    print("Leyendo archivo...")
    text = load_text_from_file(file_path)

    print("\n=== 1) Conceptos ===")
    concepts = extract_concepts(text)
    for c in concepts:
        print("-", normalize_ascii(c.name))

    print("\n=== 2) Clustering ===")
    clusters = cluster_concepts(concepts)
    for c in clusters:
        print("\nClase:", normalize_ascii(c.cluster_name))
        print("Miembros:", [normalize_ascii(m) for m in c.members])

    print("\n=== 3) Normalización ===")
    normalized_raw = normalize_entities(text, clusters)
    for n in normalized_raw:
        print("-", normalize_ascii(n.original), "→", normalize_ascii(n.normalized_type))

    print("\n=== 4) Inferencia ===")
    final_entities = []
    for n in normalized_raw:
        inferred = infer_generic_type(n.original, clusters)
        final_entities.append({"original": normalize_ascii(n.original), "type": normalize_ascii(inferred)})
        print("-", normalize_ascii(n.original), "→", normalize_ascii(inferred))

    print("\n=== 5) Relaciones ===")
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
