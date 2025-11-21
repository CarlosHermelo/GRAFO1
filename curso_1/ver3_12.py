import os
import json
from typing import List, Dict
from openai import OpenAI
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()
client = OpenAI()


# ============================================================
# LECTOR DE ARCHIVO
# ============================================================

def load_text_from_file(path: str) -> str:
    if not os.path.exists(path):
        raise FileNotFoundError(f"No se encontró el archivo: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


# ============================================================
# MODELOS Pydantic
# ============================================================

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


# ============================================================
# 1) CONCEPT MINING (Extracción de conceptos del texto)
# ============================================================

def extract_concepts(text: str):
    system = """
Extraé SOLO tipos conceptuales generales del texto.
NO nombres propios.
NO instancias concretas.
NO frases largas.
Ejemplos de buenos conceptos: Organismo, Documento, Procedimiento, Anexo.
"""

    user = f"""
Texto a analizar:
{text}

Devolvé SOLO conceptos generales encontrados en el texto.
"""

    resp = client.beta.chat.completions.parse(
        model="gpt-5-nano",
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        response_format=ConceptList,
    )

    return resp.choices[0].message.parsed.concepts


# ============================================================
# 2) CLUSTERING (Agrupar conceptos en clases abstractas)
# ============================================================

def cluster_concepts(concepts: List[Concept]):
    names = [c.name for c in concepts]

    system = """
Agrupá los conceptos en CLASES ABSTRACTAS.
Ejemplos típicos de clusters:
- Organismo
- DocumentoNormativo
- ProcedimientoAdministrativo
- RolInstitucional
- UnidadOrganizativa
- InstrumentoLegal
"""

    user = f"""
Conceptos detectados:
{names}

Agrupá en clases abstractas. No inventes conceptos externos al texto.
"""

    resp = client.beta.chat.completions.parse(
        model="gpt-5-nano",
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        response_format=ClusterList,
    )

    return resp.choices[0].message.parsed.clusters


# ============================================================
# 3) NORMALIZER AGENT (Mapear instancias → clases)
# ============================================================

def normalize_entities(text: str, clusters: List[Cluster]):
    system = """
Dado un texto y un conjunto de CLASES abstractas, detectá instancias concretas
y mapéalas a su CLASE correspondiente.
"""

    cluster_map = {c.cluster_name: c.members for c in clusters}

    user = f"""
Texto:
{text}

Clases abstractas detectadas:
{cluster_map}

Detectá entidades concretas del texto y asigná a cada una su tipo conceptual.
"""

    resp = client.beta.chat.completions.parse(
        model="gpt-5-nano",
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        response_format=NormalizedList,
    )

    return resp.choices[0].message.parsed.normalized


# ============================================================
# 4) RELATION INDUCTION (Predicados conceptuales)
# ============================================================

def extract_relations(text: str, normalized_entities: List[NormalizedEntity]):
    system = """
Extraé TIPOS DE RELACIONES conceptuales, no relaciones textuales específicas.
Predicados típicos:
APRUEBA, MODIFICA, DEJA_SIN_EFECTO, CONTIENE,
ES_AUTORIDAD_DE_APLICACION_DE, SUPRIME, ESTABLECE.
"""

    entity_types = list({e.normalized_type for e in normalized_entities})

    user = f"""
Texto:
{text}

Tipos de entidades disponibles:
{entity_types}

Extraé TIPOS de relaciones entre categorías conceptuales.
"""

    resp = client.beta.chat.completions.parse(
        model="gpt-5-nano",
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        response_format=RelationList,
    )

    return resp.choices[0].message.parsed.relations


# ============================================================
# MAIN PIPELINE
# ============================================================

def main():
    file_path = r"C:\Users\u14527001\Downloads\grafo_protesis\curso_1\RESOL-2024-2076.txt"

    print("Leyendo archivo...")
    text = load_text_from_file(file_path)

    print("\n=== 1) EXTRACCIÓN DE CONCEPTOS ===")
    concepts = extract_concepts(text)
    for c in concepts:
        print(f"- {c.name}")

    print("\n=== 2) CLUSTERING (CLASES ABSTRACTAS) ===")
    clusters = cluster_concepts(concepts)
    for c in clusters:
        print(f"\nClase: {c.cluster_name}")
        print(f"Miembros: {c.members}")

    print("\n=== 3) NORMALIZACIÓN DE ENTIDADES ===")
    normalized = normalize_entities(text, clusters)
    for n in normalized:
        print(f"- {n.original} → {n.normalized_type}")

    print("\n=== 4) RELACIONES CONCEPTUALES ===")
    relations = extract_relations(text, normalized)
    for r in relations:
        print(f"({r.subject}) --[{r.predicate}]--> ({r.object})")

    print("\n=== ESQUEMA FINAL (CONCEPTUAL) ===")
    schema = [
        {
            "source_type": r.subject,
            "relationship": r.predicate,
            "target_type": r.object
        }
        for r in relations
    ]

    print(json.dumps(schema, indent=2))


if __name__ == "__main__":
    main()
