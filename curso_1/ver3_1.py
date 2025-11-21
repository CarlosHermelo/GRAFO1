import os
import json
from typing import List, Dict
from openai import OpenAI
from pydantic import BaseModel, Field

from dotenv import load_dotenv
load_dotenv()

client = OpenAI()


# ------------------------------------------------------------
# FUNCIÓN NUEVA: Leer un archivo .txt o .md desde el disco
# ------------------------------------------------------------

def load_text_from_file(path: str) -> str:
    if not os.path.exists(path):
        raise FileNotFoundError(f"No se encontró el archivo: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


# ------------------------------------------------------------
# CONFIGURACIÓN: Objetivo del usuario (puede ser mínimo)
# ------------------------------------------------------------

user_goal = """
Identificar conceptos y relaciones contenidos en el texto para construir un grafo de conocimiento.
Todo debe surgir exclusivamente del contenido.
"""

# Si no querés sesgo, dejá esta lista vacía
existing_schema = []


# ------------------------------------------------------------
# MODELOS Pydantic
# ------------------------------------------------------------

class EntityProposal(BaseModel):
    entity_label: str
    reasoning: str
    type: str = "Discovered"

class FactProposal(BaseModel):
    subject: str
    predicate: str
    object: str
    reasoning: str

class EntityList(BaseModel):
    entities: List[EntityProposal]

class FactList(BaseModel):
    facts: List[FactProposal]


# ------------------------------------------------------------
# AGENTE NER
# ------------------------------------------------------------

def run_ner_agent(text: str, goal: str, known_labels: List[str]) -> List[str]:
    print(f"\n--- Iniciando Agente NER ---")

    system_prompt = """
Sos un experto en modelado de datos.
Debés identificar TIPOS DE ENTIDADES basadas únicamente en el contenido del texto.

Reglas:
1. No uses entidades “well-known” salvo que realmente aparezcan en el texto.
2. Las entidades deben ser conceptos generales, no instancias.
3. No incluyas números o fechas como entidades.
4. No inventes entidades externas.
"""

    user_prompt = f"""
Objetivo del usuario:
{goal}

Texto analizado:
{text}

Proponé una lista de tipos de entidades.
"""

    completion = client.beta.chat.completions.parse(
        model="gpt-5-nano",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        response_format=EntityList,
    )

    proposals = completion.choices[0].message.parsed.entities

    print("\nPropuestas del Agente NER:")
    final_entities = []
    for p in proposals:
        print(f" - {p.entity_label}: {p.reasoning}")
        final_entities.append(p.entity_label)

    return list(set(final_entities))


# ------------------------------------------------------------
# AGENTE DE RELACIONES
# ------------------------------------------------------------

def run_fact_agent(text: str, goal: str, approved_entities: List[str]) -> List[dict]:
    print(f"\n--- Iniciando Agente de Relaciones (Fact Agent) ---")

    system_prompt = """
Sos un generador de tipos de relaciones para grafos.
Reglas:
1. Un hecho es (Sujeto, Predicado, Objeto).
2. Sujeto y Objeto deben estar en la lista de entidades aprobadas.
3. No inventes entidades nuevas.
4. El predicado debe surgir del texto.
5. No describas casos específicos; solo tipos.
"""

    user_prompt = f"""
Objetivo:
{goal}

Entidades disponibles:
{approved_entities}

Texto analizado:
{text}

Proponé tipos de relaciones.
"""

    completion = client.beta.chat.completions.parse(
        model="gpt-5-nano",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        response_format=FactList,
    )

    facts = completion.choices[0].message.parsed.facts

    print("\nRelaciones propuestas:")
    schema = []
    for f in facts:
        if f.subject in approved_entities and f.object in approved_entities:
            print(f" - ({f.subject}) --[{f.predicate}]--> ({f.object})")
            schema.append({
                "source": f.subject,
                "relationship": f.predicate,
                "target": f.object
            })
        else:
            print(f" ❌ Rechazado: entidad no reconocida en ({f.subject}) -> ({f.object})")

    return schema


# ------------------------------------------------------------
# MAIN
# ------------------------------------------------------------

def main():
    # Ruta del archivo a procesar
    # CAMBIAR ESTA RUTA POR TU ARCHIVO REAL
    file_path = r"C:\Users\u14527001\Downloads\grafo_protesis\curso_1\RESOL-2024-2076.txt"

    print("Leyendo archivo...")
    sample_text = load_text_from_file(file_path)

    print("\nEjecutando NER...")
    final_entities = run_ner_agent(sample_text, user_goal, existing_schema)

    print("\nEntidades finales aprobadas:", final_entities)

    print("\nEjecutando Fact Agent...")
    final_schema = run_fact_agent(sample_text, user_goal, final_entities)

    print("\nEsquema final:")
    print(json.dumps(final_schema, indent=2))


if __name__ == "__main__":
    main()
