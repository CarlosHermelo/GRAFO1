import os
import re
import json
import openai

openai.api_key = os.getenv("OPENAI_API_KEY")


def load_text(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


# ---------------------------------------------------------------
# 1. extracción automática de entidades jurídicas desde el texto
# ---------------------------------------------------------------

def extract_raw_legal_entities(text):
    entities = set()

    # leyes
    for m in re.findall(r"\b[Ll]ey\s+[\d\.\/-]+", text):
        entities.add(("Ley", m.strip()))

    # resoluciones
    for m in re.findall(r"RESOL[-\w\/\.]+", text):
        entities.add(("Resolución", m.strip()))

    # decretos
    for m in re.findall(r"\b[Dd]ecreto\s+[\d\/\.-]+", text):
        entities.add(("Decreto", m.strip()))

    # artículos
    for m in re.findall(r"\b[Aa]rt[ií]culo\s+\d+", text):
        entities.add(("Artículo", m.strip()))

    # organismos (mayúsculas sostenidas, 3+ letras)
    for m in re.findall(r"\b[A-Z]{3,}\b", text):
        entities.add(("Organismo", m.strip()))

    # anexos
    for m in re.findall(r"\bAnexo\s+[IVX0-9-]+", text):
        entities.add(("Anexo", m.strip()))

    # reglamentos
    if "Reglamento" in text:
        entities.add(("Reglamento", "Reglamento"))

    return list(entities)


# ---------------------------------------------------------------
# 2. inferencia automática de tipos de entidades
#    sin hardcode: se deduce de los patrones anteriores
# ---------------------------------------------------------------

def infer_entity_types(raw_entities):
    types = set()
    for t, val in raw_entities:
        types.add(t)
    return list(types)


# ---------------------------------------------------------------
# 3. pedir al LLM tipos de hechos, pero restringidos a tipos
# ---------------------------------------------------------------

def propose_fact_types(entity_types, text):
    prompt = f"""
Analizá los siguientes tipos de entidades extraídos automáticamente del texto:

{entity_types}

Texto:
{text[:6000]}

Generá TIPOS de hechos (tripletas), por ejemplo:
["Resolución","deroga","Resolución"]

Reglas:
- Usar SOLO tipos de entidad listados.
- El predicado debe aparecer en el texto.
- No generar instancias concretas ni códigos.
- Devolver JSON.
"""
    r = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )

    content = r["choices"][0]["message"]["content"]
    try:
        facts = json.loads(content)
    except:
        facts = []

    # filtro simple: sujeto y objeto deben ser tipos
    filtered = []
    for triple in facts:
        if len(triple) != 3:
            continue
        s, p, o = triple
        if s in entity_types and o in entity_types:
            filtered.append((s, p, o))
    return filtered


# ---------------------------------------------------------------
# pipeline principal
# ---------------------------------------------------------------

def extract_schema_auto(files):
    text = "\n".join(load_text(f) for f in files)

    # entidades por patrón
    raw_entities = extract_raw_legal_entities(text)
    entity_types = infer_entity_types(raw_entities)

    # hechos
    fact_types = propose_fact_types(entity_types, text)

    return {
        "entity_types": entity_types,
        "fact_types": fact_types,
        "raw_entities_detected": raw_entities
    }


if __name__ == "__main__":
    files = ["resolucion2024.txt"]  # tu archivo convertido
    result = extract_schema_auto(files)

    print("=== TIPOS DE ENTIDAD ===")
    print(result["entity_types"])

    print("\n=== ENTIDADES DETECTADAS ===")
    print(result["raw_entities_detected"])

    print("\n=== TIPOS DE HECHOS ===")
    print(result["fact_types"])
