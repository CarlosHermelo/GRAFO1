import os
import json
import pandas as pd
from typing import List, Dict, Any
from openai import OpenAI
from neo4j import GraphDatabase

# --- CONFIGURACIÓN ---
# Asegúrate de tener las variables de entorno: OPENAI_API_KEY, NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD
# O defínelas aquí directamente (no recomendado para producción)
api_key = os.getenv("OPENAI_API_KEY", "") 
client = OpenAI(api_key=api_key)

# Directorio donde están tus CSVs
IMPORT_DIR = "./import_data" 

# --- GESTIÓN DEL ESTADO DEL AGENTE ---
class AgentState:
    def __init__(self):
        self.approved_files = []
        self.user_goal = ""
        self.construction_plan = {} # Aquí se guardará el esquema propuesto
        self.feedback = "" # Feedback del crítico

state = AgentState()

# --- HERRAMIENTAS (TOOLS) ---
# Estas funciones imitan las herramientas descritas en el PDF pero en Python puro

def get_approved_files():
    """Devuelve la lista de archivos CSV disponibles en el directorio."""
    try:
        files = [f for f in os.listdir(IMPORT_DIR) if f.endswith('.csv')]
        state.approved_files = files
        return json.dumps(files)
    except FileNotFoundError:
        return "Error: Directorio de importación no encontrado."

def search_file(file_name: str, query: str):
    """Busca una cadena dentro de un archivo (tipo grep simple). Útil para verificar IDs."""
    path = os.path.join(IMPORT_DIR, file_name)
    try:
        # Leemos solo las primeras filas para no saturar, o usamos pandas para buscar en columnas
        df = pd.read_csv(path)
        # Búsqueda simple en string de las primeras 5 filas para simular 'grep'
        sample = df.head(5).to_string()
        if query.lower() in sample.lower():
             return f"Encontrado '{query}' en {file_name}. Muestra: {sample}"
        
        # Verificar si es nombre de columna
        if query in df.columns:
            return f"'{query}' es una columna en {file_name}."
            
        return f"No se encontró '{query}' en las primeras filas de {file_name}."
    except Exception as e:
        return f"Error leyendo archivo: {str(e)}"

def sample_file(file_name: str):
    """Devuelve las primeras 3 filas de un archivo para inspeccionar su estructura."""
    path = os.path.join(IMPORT_DIR, file_name)
    try:
        df = pd.read_csv(path)
        return df.head(3).to_markdown()
    except Exception as e:
        return f"Error: {str(e)}"

def propose_node_construction(source_file: str, label: str, unique_column: str, properties: List[str]):
    """Herramienta para proponer la creación de un NODO."""
    proposal = {
        "type": "node",
        "source_file": source_file,
        "label": label,
        "unique_column": unique_column,
        "properties": properties
    }
    state.construction_plan[label] = proposal
    return f"Construcción de nodo '{label}' registrada exitosamente."

def propose_relationship_construction(source_file: str, rel_type: str, source_node: str, source_col: str, target_node: str, target_col: str):
    """Herramienta para proponer la creación de una RELACIÓN."""
    proposal = {
        "type": "relationship",
        "source_file": source_file,
        "relationship_type": rel_type,
        "from_node": {"label": source_node, "column": source_col},
        "to_node": {"label": target_node, "column": target_col}
    }
    state.construction_plan[rel_type] = proposal
    return f"Construcción de relación '{rel_type}' registrada exitosamente."

def get_proposed_construction_plan():
    """Devuelve el plan actual."""
    return json.dumps(state.construction_plan, indent=2)

def remove_construction(key: str):
    """Elimina una propuesta del plan."""
    if key in state.construction_plan:
        del state.construction_plan[key]
        return f"Eliminado {key} del plan."
    return "Clave no encontrada."

# Definición de herramientas para OpenAI
tools_schema = [
    {
        "type": "function",
        "function": {
            "name": "get_approved_files",
            "description": "Obtiene la lista de archivos CSV aprobados para el análisis.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "sample_file",
            "description": "Lee las primeras filas de un archivo para entender su estructura y columnas.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_name": {"type": "string", "description": "Nombre del archivo CSV"}
                },
                "required": ["file_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_file",
            "description": "Busca términos o columnas específicas dentro de un archivo para verificar identificadores únicos.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_name": {"type": "string"},
                    "query": {"type": "string", "description": "Texto o nombre de columna a buscar"}
                },
                "required": ["file_name", "query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "propose_node_construction",
            "description": "Propone una regla para crear nodos desde un archivo.",
            "parameters": {
                "type": "object",
                "properties": {
                    "source_file": {"type": "string"},
                    "label": {"type": "string", "description": "Etiqueta del nodo (ej: Producto)"},
                    "unique_column": {"type": "string", "description": "Columna ID única"},
                    "properties": {"type": "array", "items": {"type": "string"}, "description": "Lista de columnas a usar como propiedades"}
                },
                "required": ["source_file", "label", "unique_column", "properties"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "propose_relationship_construction",
            "description": "Propone una regla para crear relaciones entre nodos.",
            "parameters": {
                "type": "object",
                "properties": {
                    "source_file": {"type": "string"},
                    "rel_type": {"type": "string", "description": "Tipo de relación (ej: COMPRADO_A)"},
                    "source_node": {"type": "string", "description": "Label del nodo origen"},
                    "source_col": {"type": "string", "description": "Columna FK del origen"},
                    "target_node": {"type": "string", "description": "Label del nodo destino"},
                    "target_col": {"type": "string", "description": "Columna ID del destino"}
                },
                "required": ["source_file", "rel_type", "source_node", "source_col", "target_node", "target_col"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_proposed_construction_plan",
            "description": "Obtiene el plan JSON actual.",
            "parameters": {"type": "object", "properties": {}}
        }
    }
]

# Map de nombres a funciones reales
available_tools = {
    "get_approved_files": get_approved_files,
    "sample_file": sample_file,
    "search_file": search_file,
    "propose_node_construction": propose_node_construction,
    "propose_relationship_construction": propose_relationship_construction,
    "get_proposed_construction_plan": get_proposed_construction_plan,
    "remove_construction": remove_construction
}

# --- PROMPTS (Basados en el PDF) ---

PROPOSAL_AGENT_PROMPT = """
Eres un experto en modelado de Grafos de Conocimiento (Property Graphs).
Tu objetivo es proponer un esquema (Schema) especificando reglas de construcción para transformar archivos CSV en Nodos o Relaciones en Neo4j.

INSTRUCCIONES:
1. Analiza cada archivo usando 'sample_file'.
2. Determina si representa un Nodo o una Relación.
   - Nodos: Tienen ID único.
   - Relaciones: Conectan dos entidades (suelen tener claves foráneas o nombres compuestos).
3. Verifica identificadores con 'search_file'.
4. Usa 'propose_node_construction' o 'propose_relationship_construction' para armar el plan.
5. Si recibes feedback del Crítico, ajusta tu plan eliminando o añadiendo reglas.

OBJETIVO DEL USUARIO: {user_goal}
FEEDBACK PREVIO (CRÍTICO): {feedback}
"""

CRITIC_AGENT_PROMPT = """
Eres un experto crítico en modelado de grafos. Revisa el plan de construcción propuesto.
Tu salida debe ser estricta:
- Si el plan es perfecto y cubre los archivos lógicamente, responde SOLAMENTE con la palabra: "VALID".
- Si hay problemas, responde con "RETRY" seguido de una lista de críticas (ej: IDs no únicos, relaciones redundantes, grafos desconectados).

Usa las herramientas 'get_proposed_construction_plan' y 'sample_file' para verificar la lógica.
"""

# --- MOTOR DE EJECUCIÓN ---

def run_agent(system_prompt, model="gpt-4o", stop_check=False):
    """Ejecuta una llamada al LLM manejando el ciclo de uso de herramientas."""
    messages = [{"role": "system", "content": system_prompt}]
    
    # Primera llamada
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        tools=tools_schema,
        tool_choice="auto"
    )
    
    message = response.choices[0].message

    # Si el modelo quiere usar herramientas
    if message.tool_calls:
        messages.append(message) # Añadir la intención del asistente al historial
        
        for tool_call in message.tool_calls:
            function_name = tool_call.function.name
            function_args = json.loads(tool_call.function.arguments)
            
            print(f"  [Tool Call] {function_name} args: {function_args}")
            
            # Ejecutar función Python
            function_to_call = available_tools.get(function_name)
            if function_to_call:
                tool_output = function_to_call(**function_args)
            else:
                tool_output = "Error: Función no encontrada"
                
            # Añadir resultado al historial
            messages.append({
                "tool_call_id": tool_call.id,
                "role": "tool",
                "name": function_name,
                "content": str(tool_output)
            })
            
        # Segunda llamada para que el modelo interprete los resultados
        second_response = client.chat.completions.create(
            model=model,
            messages=messages
        )
        return second_response.choices[0].message.content
    
    return message.content

# --- COORDINADOR PRINCIPAL (REFINEMENT LOOP) ---

def main():
    # 1. Configuración Inicial
    if not os.path.exists(IMPORT_DIR):
        print(f"Error: Crea la carpeta '{IMPORT_DIR}' y pon tus CSVs ahí.")
        return

    state.user_goal = "Analizar la cadena de suministro. Identificar productos, partes y proveedores."
    print(f"--- INICIANDO AGENTE DE ESQUEMA ---\nObjetivo: {state.user_goal}\n")

    max_iterations = 3
    is_valid = False

    for i in range(max_iterations):
        print(f"\n\n=== ITERACIÓN {i+1} ===")
        
        # 2. PROPOSAL AGENT
        print(">> Ejecutando Proposal Agent...")
        proposal_prompt = PROPOSAL_AGENT_PROMPT.format(
            user_goal=state.user_goal,
            feedback=state.feedback
        )
        proposal_response = run_agent(proposal_prompt)
        print(f"Respuesta Proposal: {proposal_response}")
        
        # Mostrar estado actual del plan
        print(f"Plan Actual: {json.dumps(state.construction_plan, indent=2)}")

        # 3. CRITIC AGENT
        print("\n>> Ejecutando Critic Agent...")
        critic_response = run_agent(CRITIC_AGENT_PROMPT)
        print(f"Evaluación del Crítico: {critic_response}")

        # 4. CHECK STATUS
        if "VALID" in critic_response.upper() and "RETRY" not in critic_response.upper():
            print("\n*** ¡ESQUEMA APROBADO! ***")
            is_valid = True
            break
        else:
            state.feedback = critic_response
            print("\n... Refinando esquema basado en feedback ...")

    # 5. RESULTADO FINAL
    if is_valid:
        print("\nGenerando código Cypher de ejemplo basado en el plan (Simulación)...")
        # Aquí podrías iterar sobre state.construction_plan y generar CREATE/MERGE queries
        for key, item in state.construction_plan.items():
            if item['type'] == 'node':
                print(f"Cypher sugerido: LOAD CSV... MERGE (n:{item['label']} {{id: row.{item['unique_column']}}})")
    else:
        print("No se llegó a un consenso en el número máximo de iteraciones.")

if __name__ == "__main__":
    main()