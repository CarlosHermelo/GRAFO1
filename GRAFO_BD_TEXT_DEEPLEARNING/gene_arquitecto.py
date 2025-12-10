# interactive_architect.py
import os
import json
import pandas as pd
from openai import OpenAI
from typing import List, Dict, Any
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# --- CONFIGURACIÓN DESDE .ENV ---
# Directorios de los archivos (con valores por defecto si no están en .env)
CSV_DIR = os.getenv("CSV_DIR", "./import_data/csv")
TXT_DIR = os.getenv("TXT_DIR", "./import_data/txt")
# Modelo de LLM (con valor por defecto)
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4-turbo")
# ----------------------------------

# Configuración de Cliente
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ==============================================================================
# FUNCIONES DE UTILIDAD (HITL)
# ==============================================================================
def human_review(agent_name: str, proposal: Any) -> Any:
    """Función para detener el script y pedir aprobación humana."""
    print(f"\n✋ {agent_name} (Usando {LLM_MODEL}) propone:")
    print(json.dumps(proposal, indent=2, ensure_ascii=False))
    
    while True:
        choice = input(f"\nUSER: ¿Apruebas esta propuesta? (s/n) o escribe 'reintentar': ").lower().strip()
        if choice == 's':
            return proposal
        elif choice == 'n':
            print("USER: Ingresa la corrección (en formato JSON válido) o escribe 'retry' para reintentar:")
            user_edit = input("> ")
            if user_edit == 'retry':
                return None
            try:
                return json.loads(user_edit)
            except json.JSONDecodeError:
                print("❌ Error: El JSON ingresado no es válido. Intenta de nuevo.")

# ==============================================================================
# 1. AGENTE: USER INTENT
# ==============================================================================
def get_user_intent():
    """Solicita al usuario que defina su objetivo."""
    print("\n🎯 PASO 1: Definir el objetivo del grafo de conocimiento")
    user_input = input("USER: Describe el objetivo de tu grafo (o presiona Enter para usar el objetivo por defecto): ").strip()

    if not user_input:
        user_input = "Construir un grafo de conocimiento que integre datos estructurados de productos, proveedores y reseñas con información textual sobre calidad, logística y reclamos."
        print(f"📌 Usando objetivo por defecto: {user_input}")

    return {"goal": user_input}
    
# ==============================================================================
# 2. AGENTE: FILE SUGGESTION (Selección de Archivos)
# ==============================================================================
def get_file_suggestions(goal: Dict):
    """Sugiere archivos relevantes basándose en el objetivo del usuario."""
    # --- Cambio clave: Listar archivos de subcarpetas ---
    all_files_on_disk = []

    # 1. Archivos de la carpeta CSV_DIR
    if os.path.exists(CSV_DIR):
        all_files_on_disk.extend([os.path.join(CSV_DIR, f) for f in os.listdir(CSV_DIR) if os.path.isfile(os.path.join(CSV_DIR, f))])

    # 2. Archivos de la carpeta TXT_DIR
    if os.path.exists(TXT_DIR):
        all_files_on_disk.extend([os.path.join(TXT_DIR, f) for f in os.listdir(TXT_DIR) if os.path.isfile(os.path.join(TXT_DIR, f))])

    if not all_files_on_disk:
        print("⚠️ ADVERTENCIA: No se encontraron archivos en los directorios especificados.")
        return []

    # Lógica de LLM para seleccionar archivos
    prompt = f"""
Eres un asistente experto en selección de archivos para grafos de conocimiento.

Objetivo del usuario: {goal.get('goal', 'No especificado')}

Archivos disponibles:
{json.dumps(all_files_on_disk, indent=2)}

Tarea:
Selecciona TODOS los archivos relevantes para cumplir con el objetivo.
Considera archivos CSV para datos estructurados y archivos TXT/MD para información no estructurada.

Responde ÚNICAMENTE con un objeto JSON válido con esta estructura:
{{
  "approved_files": ["ruta/archivo1.csv", "ruta/archivo2.txt", ...]
}}

IMPORTANTE:
- Usa las rutas EXACTAS de los archivos listados arriba
- Incluye TODOS los archivos que puedan ser útiles
- Si todos los archivos son relevantes, inclúyelos todos
"""

    response = client.chat.completions.create(
        model=LLM_MODEL,
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        temperature=0
    )

    proposal = json.loads(response.choices[0].message.content)

    # Validar que la propuesta tenga la estructura correcta
    if 'approved_files' not in proposal:
        proposal = {'approved_files': all_files_on_disk}  # Fallback: usar todos los archivos

    final_files = human_review("📂 Agente Files", proposal)
    return final_files.get('approved_files', [])


# ==============================================================================
# 3. AGENTE: STRUCTURED SCHEMA (Plan de Construcción CSV)
# ==============================================================================
def get_construction_plan(goal: Dict, approved_files_with_paths: List[str]):
    csv_files_with_paths = [f for f in approved_files_with_paths if f.endswith('.csv')]

    schemas = {}
    for full_path in csv_files_with_paths:
        try:
            # Python lee el header con la ruta completa (ej: 'csv/products.csv')
            df = pd.read_csv(full_path, nrows=2)
            # MAESTRO: Usamos solo el nombre del archivo (os.path.basename) para el Plan de Neo4j
            schemas[os.path.basename(full_path)] = list(df.columns)
        except Exception as e:
            print(f"Error leyendo {full_path}: {e}")
            pass

    prompt = f"""
Eres un arquitecto experto en grafos de conocimiento.

Objetivo: {goal.get('goal', 'No especificado')}

Estructura de archivos CSV disponibles:
{json.dumps(schemas, indent=2)}

Tarea:
Genera un plan de construcción ('construction_plan') en formato JSON que defina:
- Nodos: Qué entidades crear a partir de los CSV
- Relaciones: Cómo conectar las entidades basándose en las columnas

Responde ÚNICAMENTE con un objeto JSON válido siguiendo esta estructura:
{{
  "nodes": [
    {{
      "label": "NombreEntidad",
      "source_file": "archivo.csv",
      "key_columns": ["columna_id"],
      "properties": ["col1", "col2"]
    }}
  ],
  "relationships": [
    {{
      "type": "TIPO_RELACION",
      "from_label": "EntidadOrigen",
      "to_label": "EntidadDestino",
      "source_file": "archivo.csv",
      "from_column": "columna_fk",
      "to_column": "columna_id"
    }}
  ]
}}

IMPORTANTE:
- La clave 'source_file' DEBE ser solo el nombre del archivo (ej: 'products.csv'), NO la ruta completa
- Usa solo columnas que existan en los CSV
"""

    response = client.chat.completions.create(
        model=LLM_MODEL,
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        temperature=0
    )
    proposal = json.loads(response.choices[0].message.content)
    final_plan = human_review("🏗️ Agente Schema (CSV)", proposal)
    return final_plan

# ==============================================================================
# 4. AGENTE: UNSTRUCTURED SCHEMA (Schema LLM para TXT)
# ==============================================================================
def get_llm_schema(goal: Dict, approved_files_with_paths: List[str]):
    txt_files = [f for f in approved_files_with_paths if f.endswith('.md') or f.endswith('.txt')]
    sample_text = ""
    if txt_files:
        # Usamos la ruta completa para leer el archivo
        try:
            with open(txt_files[0], 'r', encoding='utf-8') as f:
                sample_text = f.read(1000)
        except Exception as e:
            print(f"Error leyendo archivo de texto {txt_files[0]}: {e}")
            sample_text = "No se pudo leer el archivo"

    prompt = f"""
Eres un experto en procesamiento de lenguaje natural y diseño de grafos de conocimiento.

Objetivo: {goal.get('goal', 'No especificado')}

Muestra de texto a analizar:
---
{sample_text}
---

Tarea:
Analiza el texto y define qué Entidades y Relaciones deberían extraerse para construir el grafo de conocimiento.

Responde ÚNICAMENTE con un objeto JSON válido con esta estructura:
{{
  "entities": [
    {{
      "label": "NombreEntidad",
      "description": "Descripción de la entidad",
      "extraction_pattern": "Patrón o regla para extraer esta entidad"
    }}
  ],
  "relationships": [
    {{
      "type": "TIPO_RELACION",
      "from_entity": "EntidadOrigen",
      "to_entity": "EntidadDestino",
      "description": "Descripción de la relación"
    }}
  ]
}}

IMPORTANTE:
- Considera el contexto del objetivo
- Define entidades y relaciones relevantes para el dominio
- Proporciona patrones claros de extracción
"""

    response = client.chat.completions.create(
        model=LLM_MODEL,
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        temperature=0
    )
    proposal = json.loads(response.choices[0].message.content)
    final_schema = human_review("🧠 Agente Schema (TXT)", proposal)
    return final_schema

# ... (El resto del orquestador 'main' sigue igual)
# ==============================================================================
# ORQUESTADOR PRINCIPAL (Asegurando el inicio)
# ==============================================================================
def main():
    print(f"--- 🚀 INICIANDO ARQUITECTO DE GRAFOS ---")
    print(f"🔧 Modelo LLM configurado: {LLM_MODEL}")
    print(f"📁 Directorios: CSV={CSV_DIR}, TXT={TXT_DIR}")

    # Verificación rápida de la API Key
    if not os.getenv("OPENAI_API_KEY"):
        print("\n❌ ERROR CRÍTICO: La variable OPENAI_API_KEY no está configurada en el .env.")
        return

    # Verificar que los directorios existen
    if not os.path.exists(CSV_DIR):
        print(f"⚠️ ADVERTENCIA: El directorio CSV no existe: {CSV_DIR}")
    if not os.path.exists(TXT_DIR):
        print(f"⚠️ ADVERTENCIA: El directorio TXT no existe: {TXT_DIR}")

    try:
        # 1. Definir Objetivo
        goal = get_user_intent()
        
        # 2. Elegir Archivos
        files_with_paths = get_file_suggestions(goal)
        csv_files = [f for f in files_with_paths if f.endswith('.csv')]
        txt_files = [f for f in files_with_paths if f.endswith('.md') or f.endswith('.txt')]
        
        # 3. Plan Estructurado
        domain_plan = {}
        if csv_files:
            domain_plan = get_construction_plan(goal, csv_files)
        
        # 4. Schema No Estructurado
        llm_schema = {}
        if txt_files:
            llm_schema = get_llm_schema(goal, txt_files)
            
        # 5. Salida Final
        output_package = {
            "domain_plan": domain_plan, 
            "llm_schema": llm_schema,
            "files_to_process": txt_files
        }
        
        with open("builder_config.json", "w") as f:
            json.dump(output_package, f, indent=4)
            
        print("\n" + "="*50)
        print("✅ PLANIFICACIÓN COMPLETADA.")
        print("📁 Configuración guardada en 'builder_config.json'.")
        print("👉 Ahora ejecuta el script 'gene_builder.py execute' para construir el grafo.")
        
    except Exception as e:
        print(f"\n❌ ERROR FATAL DURANTE LA EJECUCIÓN DEL AGENTE: {e}")
        print("Verifica tu conexión a internet, la validez de tu API Key y el modelo LLM.")
        

if __name__ == "__main__":
    # Asegúrate de que todas las funciones LLM usen el parámetro `model=LLM_MODEL`
    # (Esto ya está en el código, pero es la clave para la flexibilidad).
    main()