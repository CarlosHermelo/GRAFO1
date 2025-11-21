import os
import glob
import json
from typing import List, Dict
from openai import OpenAI
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Carga variables de entorno si usas un archivo .env
load_dotenv()

# Configuración del cliente
client = OpenAI()
# Asegúrate de tener os.environ["OPENAI_API_KEY"] configurado

# --- CONFIGURACIÓN DEL DIRECTORIO ---
# Usamos r"" para que Python interprete los backslashes de Windows correctamente
FOLDER_PATH = r"C:\Users\u14527001\Downloads\grafo_protesis\curso_1"

# --- 1. Carga de Datos (Dinámica desde carpeta) ---

def read_txt_files(folder_path: str) -> Dict[str, str]:
    """Lee todos los archivos .txt de la ruta especificada."""
    files_content = {}
    # Busca archivos .txt
    search_path = os.path.join(folder_path, "*.txt")
    files = glob.glob(search_path)
    
    print(f"📂 Buscando archivos en: {folder_path}")
    
    if not files:
        print("⚠️ No se encontraron archivos .txt en la ruta.")
        return {}

    for file_path in files:
        file_name = os.path.basename(file_path)
        try:
            # Intentamos leer con utf-8, si falla (común en Windows), probamos latin-1
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            files_content[file_name] = content
            print(f"  ✅ Cargado: {file_name}")
        except UnicodeDecodeError:
            # Fallback para codificaciones antiguas de Windows
            with open(file_path, 'r', encoding='latin-1') as f:
                content = f.read()
            files_content[file_name] = content
            print(f"  ✅ Cargado (latin-1): {file_name}")
        except Exception as e:
            print(f"  ❌ Error leyendo {file_name}: {e}")

    return files_content

# Cargamos los archivos
txt_files = read_txt_files(FOLDER_PATH)

[cite_start]# [cite: 181] - Objetivo del usuario (ADAPTADO AL NUEVO CONTEXTO)
# Hacemos el objetivo lo suficientemente amplio para que funcione con Resoluciones o cualquier otro tema.
user_goal = """
Analizar el contenido de los documentos proporcionados (ej. Resoluciones, Normativas o Informes) 
para extraer las entidades principales involucradas y cómo se relacionan entre sí.
Identificar actores clave, decisiones, fechas y objetos de la resolución.
"""

[cite_start]# [cite: 200] - Esquema Estructurado Existente ("Well-known Entities")
# Lo dejamos vacío o con términos muy genéricos para que el agente descubra el dominio por sí solo.
existing_schema = [] # Ej: ["Persona", "Organizacion", "Fecha"] si quisieras forzar algunos.

# --- 2. Definición de Modelos de Datos (Igual que antes) ---

class EntityProposal(BaseModel):
    entity_label: str = Field(description="El tipo de entidad (ej. 'Juez', 'Resolucion', 'Articulo'). No instancias específicas.")
    reasoning: str = Field(description="Por qué esta entidad es relevante para el texto analizado.")
    type: str = Field(description="'Well-known' si ya existe en el esquema, o 'Discovered' si es nueva.")

class FactProposal(BaseModel):
    subject: str = Field(description="Entidad origen (debe ser una entidad aprobada).")
    predicate: str = Field(description="La relación (ej. 'EMITE', 'SE_REFIERE_A').")
    object: str = Field(description="Entidad destino (debe ser una entidad aprobada).")
    reasoning: str = Field(description="Explicación de la relación.")

class EntityList(BaseModel):
    entities: List[EntityProposal]

class FactList(BaseModel):
    facts: List[FactProposal]

# --- 3. Agente NER (Named Entity Recognition) ---
[cite_start]# [cite: 71, 81] - Propósito: Proponer tipos de entidades relevantes.

def run_ner_agent(text_content: str, goal: str, known_labels: List[str]) -> List[str]:
    print(f"\n--- 🕵️ Iniciando Agente NER ---")
    print(f"Analizando texto para descubrir entidades...")

    system_prompt = f"""
    Eres un experto en análisis de textos legales, técnicos y administrativos.
    Tu objetivo es leer el contenido y proponer un ESQUEMA DE DATOS (Tipos de Entidades/Nodos).
    
    Reglas:
    1. Identifica los sustantivos abstractos clave (ej. en una resolución: 'Organismo', 'Normativa', 'Sanción').
    2. [cite_start]Diferencia entre entidades 'Well-known' (existentes: {known_labels}) y 'Discovered' (nuevas halladas en el texto)[cite: 74].
    3. [cite_start]No extraigas valores únicos como entidades (ej. no extraigas '20 de Mayo' como entidad, la entidad es 'Fecha')[cite: 98].
    4. Genera etiquetas en formato CamelCase o SnakeCase (ej. 'TipoResolucion').
    """

    user_prompt = f"""
    Objetivo del Análisis: {goal}
    
    Contenido de los archivos:
    {text_content[:20000]} # Limitamos caracteres por si son muchos archivos
    
    Propone una lista de Tipos de Entidades (Schema) para estructurar esta información.
    """

    completion = client.beta.chat.completions.parse(
        model="gpt-5-nano", # Usamos un modelo robusto. Cambia a gpt-4o-mini si quieres ahorrar.
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        response_format=EntityList,
    )

    proposals = completion.choices[0].message.parsed.entities
    
    # [cite_start]Simulación de "Aprobación Humana" [cite: 132]
    approved_entities = []
    print("\nPropuestas del Agente NER:")
    for p in proposals:
        print(f" - [{p.type}] {p.entity_label}: {p.reasoning}")
        approved_entities.append(p.entity_label)
    
    # Incluir known_labels si no fueron detectados
    for label in known_labels:
        if label not in approved_entities:
            approved_entities.append(label)
            
    return list(set(approved_entities))

# --- 4. Agente de Extracción de Hechos (Relaciones) ---
[cite_start]# [cite: 258, 270] - Propósito: Proponer tripletas.

def run_fact_agent(text_content: str, goal: str, approved_entities: List[str]) -> List[dict]:
    print(f"\n--- 🔗 Iniciando Agente de Relaciones (Facts) ---")
    print(f"Usando entidades aprobadas: {approved_entities}")

    system_prompt = f"""
    Eres un arquitecto de información. Tu trabajo es definir cómo se relacionan las entidades detectadas.
    
    [cite_start]Reglas[cite: 273]:
    1. Propone TIPOS DE RELACIONES (Predicados) genéricos.
    2. Sujeto y Objeto deben ser EXCLUSIVAMENTE de esta lista: {approved_entities}.
    3. El predicado debe ser un verbo o acción clara (ej. 'FIRMA', 'CONTIENE', 'DEROGA').
    4. No inventes entidades nuevas.
    """

    user_prompt = f"""
    Objetivo: {goal}
    
    Texto de muestra:
    {text_content[:20000]}
    
    Define los tipos de relaciones (Edges) lógicas para este dominio.
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
    # Paso 0: Verificar si hay archivos
    if not txt_files:
        print("❌ No hay archivos para procesar. Verifica la ruta.")
        return

    # [cite_start]Paso 1: Preparar datos [cite: 107]
    # Concatenamos el contenido de todos los txt con un separador
    full_text = ""
    for filename, content in txt_files.items():
        full_text += f"\n--- Archivo: {filename} ---\n{content}"
    
    print(f"\n📝 Total de caracteres a analizar: {len(full_text)}")

    # [cite_start]Paso 2: Ejecutar Agente NER [cite: 40]
    final_entities = run_ner_agent(full_text, user_goal, existing_schema)
    
    print(f"\n✅ Entidades Finales Aprobadas: {final_entities}")
    
    # [cite_start]Paso 3: Ejecutar Agente de Hechos [cite: 45]
    final_schema = run_fact_agent(full_text, user_goal, final_entities)
    
    print(f"\n🎉 ESQUEMA PROPUESTO FINAL:")
    print(json.dumps(final_schema, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()