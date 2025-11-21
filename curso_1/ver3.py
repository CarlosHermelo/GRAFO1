import os
import json
from typing import List, Dict
from openai import OpenAI
from pydantic import BaseModel, Field

from dotenv import load_dotenv
load_dotenv()
client = OpenAI()
# Configura tu API KEY aquí

# --- 1. Datos de Entrada y Contexto (Simulando los archivos del PDF) ---
# [cite: 161, 188] - Datos no estructurados (Reseñas de productos)
markdown_files = {
    "gothenburg_table_reviews.md": """
    # Reseña: Mesa Gothenburg
    Usuario: MesaFan123
    Rating: 2/5
    Texto: La calidad de la madera es mala. El ensamblaje fue una pesadilla, faltaban tornillos.
    """,
    "stockholm_chair_reviews.md": """
    # Reseña: Silla Stockholm
    Usuario: SitComfort
    Rating: 1/5
    Texto: La pata se rompió después de una semana. Problema grave de durabilidad. No recomiendo este proveedor.
    """
}

# [cite: 181, 182] - Objetivo del usuario
user_goal = """
Analizar la cadena de suministro para encontrar la causa raíz de problemas. 
Agregar reseñas de productos para rastrear quejas sobre calidad, dificultad de ensamblaje o durabilidad.
"""

# [cite: 200] - Esquema Estructurado Existente ("Well-known Entities")
existing_schema = ["Product", "Assembly", "Part", "Supplier"]

# --- 2. Definición de Modelos de Datos (Salida Estructurada) ---

class EntityProposal(BaseModel):
    entity_label: str = Field(description="El tipo de entidad (ej. 'QualityIssue'). No instancias específicas.")
    reasoning: str = Field(description="Por qué esta entidad es relevante para el objetivo del usuario.")
    type: str = Field(description="'Well-known' si ya existe en el esquema, o 'Discovered' si es nueva.")

class FactProposal(BaseModel):
    subject: str = Field(description="Entidad origen (debe ser una entidad aprobada).")
    predicate: str = Field(description="La relación (ej. 'HAS_ISSUE').")
    object: str = Field(description="Entidad destino (debe ser una entidad aprobada).")
    reasoning: str = Field(description="Explicación de la relación.")

class EntityList(BaseModel):
    entities: List[EntityProposal]

class FactList(BaseModel):
    facts: List[FactProposal]

# --- 3. Agente NER (Named Entity Recognition) ---
# [cite: 71, 81] - Propósito: Proponer tipos de entidades relevantes.

def run_ner_agent(reviews: str, goal: str, known_labels: List[str]) -> List[str]:
    print(f"\n--- 🕵️ Iniciando Agente NER ---")
    print(f"Analizando texto buscando entidades relacionadas con: {known_labels}...")

    system_prompt = f"""
    Eres un experto en modelado de datos y grafos de conocimiento.
    Tu objetivo es analizar texto no estructurado y proponer TIPOS de entidades (Nodes) relevantes para el objetivo del usuario.
    
    Reglas:
    1. Distingue entre entidades 'Well-known' (ya existen: {known_labels}) y 'Discovered' (nuevas en el texto)[cite: 74].
    2. No propongas valores cuantitativos (como 'Edad' o 'Rating') como entidades, esos son propiedades[cite: 98].
    3. Busca conceptos que ayuden al análisis de causa raíz (ej. Quejas, Defectos).
    """

    user_prompt = f"""
    Objetivo del Usuario: {goal}
    
    Texto de muestra:
    {reviews}
    
    Propone una lista de Tipos de Entidades (Schema).
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
    
    # Simulación de "Aprobación Humana" [cite: 132]
    approved_entities = []
    print("\nPropuestas del Agente NER:")
    for p in proposals:
        print(f" - [{p.type}] {p.entity_label}: {p.reasoning}")
        # En un caso real, aquí iría un input() para aprobar. Asumimos aprobación automática para el demo.
        approved_entities.append(p.entity_label)
    
    # Aseguramos que las "Well-known" estén incluidas si el agente las omitió pero son base
    for label in known_labels:
        if label not in approved_entities:
            approved_entities.append(label)
            
    return list(set(approved_entities))

# --- 4. Agente de Extracción de Hechos (Relaciones) ---
# [cite: 258, 270] - Propósito: Proponer tripletas (Sujeto, Predicado, Objeto).

def run_fact_agent(reviews: str, goal: str, approved_entities: List[str]) -> List[dict]:
    print(f"\n--- 🔗 Iniciando Agente de Relaciones (Facts) ---")
    print(f"Usando entidades aprobadas: {approved_entities}")

    system_prompt = f"""
    Eres un arquitecto de Grafos de Conocimiento.
    Tu trabajo es proponer TIPOS DE HECHOS (Relaciones) basados en las entidades aprobadas.
    
    Reglas[cite: 273]:
    1. Un hecho es una tripleta (Sujeto, Predicado, Objeto).
    2. El Sujeto y el Objeto DEBEN ser elegidos estrictamente de la lista de entidades aprobadas: {approved_entities}.
    3. No inventes nuevas entidades.
    4. El predicado debe describir cómo interactúan estas entidades en el texto (ej. Product HAS_ISSUE Issue).
    5. No propongas hechos específicos (ej. "Mesa tiene tornillo roto"), sino el TIPO (Product HAS_COMPONENT Part).
    """

    user_prompt = f"""
    Objetivo del Usuario: {goal}
    
    Texto de muestra:
    {reviews}
    
    Propone los tipos de relaciones (Edges) para el esquema.
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
    
    print("\nPropuestas de Relaciones del Agente:")
    approved_schema = []
    for f in facts:
        # Validación simple 
        if f.subject in approved_entities and f.object in approved_entities:
            print(f" - ({f.subject}) --[{f.predicate}]--> ({f.object})")
            approved_schema.append({"source": f.subject, "relationship": f.predicate, "target": f.object})
        else:
            print(f" ❌ Rechazado (Entidad desconocida): ({f.subject}) -> ({f.object})")

    return approved_schema

# --- 5. Ejecución Principal (Workflow) ---

def main():
    # Paso 1: Preparar datos
    # Concatenamos una muestra del texto para que el LLM tenga contexto [cite: 107]
    sample_text = "\n".join(markdown_files.values())
    
    # Paso 2: Ejecutar Agente NER [cite: 40]
    # Input: Goal, Files, Schema existente
    # Output: Lista de entidades aprobadas
    final_entities = run_ner_agent(sample_text, user_goal, existing_schema)
    
    print(f"\n✅ Entidades Finales Aprobadas: {final_entities}")
    
    # Paso 3: Ejecutar Agente de Hechos [cite: 45]
    # Input: Entidades aprobadas
    # Output: Tripletas de esquema
    final_schema = run_fact_agent(sample_text, user_goal, final_entities)
    
    print(f"\n🎉 ESQUEMA PROPUESTO FINAL:")
    print(json.dumps(final_schema, indent=2))

if __name__ == "__main__":
    main()