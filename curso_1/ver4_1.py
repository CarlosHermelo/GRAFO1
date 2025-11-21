import os
import glob
import json
from typing import List, Dict
from openai import OpenAI
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Carga variables de entorno
load_dotenv()

# Configuración del cliente
client = OpenAI()

# --- CONFIGURACIÓN DEL DIRECTORIO ---
FOLDER_PATH = r"C:\Users\u14527001\Downloads\grafo_protesis\curso_1"

# --- 1. Carga de Datos (Dinámica desde carpeta) ---

def read_txt_files(folder_path: str) -> Dict[str, str]:
    files_content = {}
    search_path = os.path.join(folder_path, "*.txt")
    files = glob.glob(search_path)

    print(f"📂 Buscando archivos en: {folder_path}")
    
    if not files:
        print("⚠️ No se encontraron archivos .txt en la ruta.")
        return {}

    for file_path in files:
        file_name = os.path.basename(file_path)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            files_content[file_name] = content
            print(f"  ✅ Cargado: {file_name}")
        except UnicodeDecodeError:
            with open(file_path, 'r', encoding='latin-1') as f:
                content = f.read()
            files_content[file_name] = content
            print(f"  ✅ Cargado (latin-1): {file_name}")
        except Exception as e:
            print(f"  ❌ Error leyendo {file_name}: {e}")

    return files_content

# Cargamos los archivos
txt_files = read_txt_files(FOLDER_PATH)

# Objetivo del análisis
user_goal = """
Analizar el contenido de los documentos proporcionados (por ejemplo resoluciones, normativas o informes)
para extraer las entidades principales involucradas y cómo se relacionan entre sí.
Identificar actores clave, decisiones, fechas y objetos de la resolución.
"""

# Esquema existente (puede quedar vacío)
existing_schema = []

# --- 2. Modelos de Datos ---

class EntityProposal(BaseModel):
    entity_label: str
    reasoning: str
    type: str

class FactProposal(BaseModel):
    subject: str
    predicate: str
    object: str
    reasoning: str

class EntityList(BaseModel):
    entities: List[EntityProposal]

class FactList(BaseModel):
    facts: List[FactProposal]

# --- 3. Agente NER (Tipos de Entidades) ---

def run_ner_agent(text_content: str, goal: str, known_labels: List[str]) -> List[str]:
    print(f"\n--- Agente NER ---")
    print(f"Analizando texto para descubrir entidades...")

    system_prompt = f"""
    Eres un experto en análisis de textos legales, técnicos y administrativos.
    Tu objetivo es leer el contenido y proponer un esquema de datos (tipos de entidades o nodos).
    
    Reglas:
    1. Identifica los sustantivos abstractos clave (por ejemplo 'Organismo', 'Normativa', 'Sanción').
    2. Distingue entre entidades 'Well-known' (existentes: {known_labels}) y 'Discovered' (nuevas).
    3. No extraigas valores únicos como entidades. La entidad es 'Fecha', no '20 de Mayo'.
    4. Usa etiquetas en formato CamelCase o SnakeCase.
    """

    user_prompt = f"""
    Objetivo del análisis: {goal}

    Contenido de los archivos:
    {text_content[:20000]}

    Proponer lista de tipos de entidades.
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

    approved_entities = []
    print("\nPropuestas del Agente NER:")
    for p in proposals:
        print(f" - [{p.type}] {p.entity_label}: {p.reasoning}")
        approved_entities.append(p.entity_label)

    for label in known_labels:
        if label not in approved_entities:
            approved_entities.append(label)

    return list(set(approved_entities))

# --- 4. Agente de Extracción de Hechos (Relaciones) ---

def run_fact_agent(text_content: str, goal: str, approved_entities: List[str]) -> List[dict]:
    print(f"\n--- Agente de Relaciones ---")
    print(f"Usando entidades aprobadas: {approved_entities}")

    system_prompt = f"""
    Eres un arquitecto de información. Tu trabajo es definir cómo se relacionan las entidades detectadas.
    
    Reglas:
    1. Propone tipos de relaciones claras (predicados).
    2. Sujeto y objeto deben ser exclusivamente de esta lista: {approved_entities}.
    3. El predicado debe ser un verbo o acción (por ejemplo 'FIRMA', 'DEROGA').
    4. No inventes entidades nuevas.
    """

    user_prompt = f"""
    Objetivo: {goal}

    Texto de muestra:
    {text_content[:20000]}

    Definir relaciones (tripletas).
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

    print("\nPropuestas de Relaciones:")
    approved_schema = []
    for f in facts:
        if f.subject in approved_entities and f.object in approved_entities:
            print(f" - ({f.subject}) --[{f.predicate}]--> ({f.object})")
            approved_schema.append({
                "source": f.subject,
                "relationship": f.predicate,
                "target": f.object
            })
        else:
            print(f" Rechazado: ({f.subject}) -> ({f.object})")

    return approved_schema

# --- 5. Ejecución Principal ---

def main():
    if not txt_files:
        print("❌ No hay archivos para procesar.")
        return

    full_text = ""
    for filename, content in txt_files.items():
        full_text += f"\n--- Archivo: {filename} ---\n{content}"

    print(f"\nTotal de caracteres a analizar: {len(full_text)}")

    final_entities = run_ner_agent(full_text, user_goal, existing_schema)
    print(f"\nEntidades aprobadas: {final_entities}")

    final_schema = run_fact_agent(full_text, user_goal, final_entities)
    
    print(f"\nEsquema final propuesto:")
    print(json.dumps(final_schema, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
