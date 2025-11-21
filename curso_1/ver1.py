# ------------------------------------------------------------
# CONFIGURACIÓN
# ------------------------------------------------------------

import os
from openai import OpenAI
from dotenv import load_dotenv

# cargar .env
load_dotenv()

# forzar que la API key exista
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY no está configurada")

# obligar a OpenAI a verla
os.environ["OPENAI_API_KEY"] = api_key

# crear cliente correctamente (sin parámetros)
client = OpenAI()


print("DEBUG → OPENAI_API_KEY =", os.getenv("OPENAI_API_KEY"))


# ------------------------------------------------------------
# FUNCIONES AUXILIARES
# ------------------------------------------------------------

def load_files(file_paths):
    textos = {}
    for path in file_paths:
        with open(path, "r", encoding="utf-8") as f:
            textos[path] = f.read()
    return textos

def call_llm(prompt):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )
    return response.choices[0].message.content

# ------------------------------------------------------------
# 1. PROPONER ENTIDADES (NER conceptual)
# ------------------------------------------------------------

def propose_entity_types(user_goal, textos):
    prompt = f"""
Tu tarea es identificar tipos de entidades relevantes para construir un grafo,
basándote en el objetivo del usuario y en los documentos provistos.

Objetivo del usuario:
{user_goal}

Documentos:
{ {k: textos[k][:2000] for k in textos} }

Reglas:
- Propone tipos de entidades, no instancias.
- Pueden ser: personas, organizaciones, conceptos, objetos, eventos, procedimientos.
- Deben servir al objetivo declarado.
- No propongas cantidades (edad, precio).
- Dejá el resultado como una lista simple: ["EntidadA", "EntidadB", ...]

Responde solo con la lista de entidades.
"""
    return call_llm(prompt)

# ------------------------------------------------------------
# 2. PROPONER TIPOS DE HECHOS / TRIPLETAS
# ------------------------------------------------------------

def propose_fact_types(user_goal, textos, entity_types):
    prompt = f"""
Generá tipos de hechos (tripletas) posibles a partir del texto y del objetivo.

Objetivo:
{user_goal}

Entidades aprobadas:
{entity_types}

Documentos:
{ {k: textos[k][:2000] for k in textos} }

Reglas:
- Cada hecho debe ser un tipo general, no un caso específico.
- Formato: (Sujeto, Predicado, Objeto)
- Sujeto y Objeto deben estar en la lista de entidades.
- El predicado debe aparecer o inferirse claramente del texto.
- Responde como una lista, por ejemplo:
[
  ("Entidad1", "predicado", "Entidad2"),
  ("EntidadX", "relaciona_con", "EntidadY")
]
"""
    return call_llm(prompt)

# ------------------------------------------------------------
# FUNCIÓN PRINCIPAL
# ------------------------------------------------------------

def build_schema_from_text(user_goal, file_paths):
    textos = load_files(file_paths)

    print("=== PROPONIENDO ENTIDADES ===")
    entity_types = propose_entity_types(user_goal, textos)
    print(entity_types)

    print("\n=== PROPONIENDO TIPOS DE HECHOS ===")
    fact_types = propose_fact_types(user_goal, textos, entity_types)
    print(fact_types)

    return entity_types, fact_types

# ------------------------------------------------------------
# EJEMPLO DE USO
# ------------------------------------------------------------

if __name__ == "__main__":
    goal = "Construir un grafo que permita analizar normativas legales y su relación entre resoluciones, artículos y organismos emisores."
    files = [
        "RESOL-2024-2076.txt"
    ]

    entities, facts = build_schema_from_text(goal, files)
