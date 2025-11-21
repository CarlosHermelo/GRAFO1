import os
import glob
import json
from typing import List, Tuple, Set, Dict
from openai import OpenAI
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Carga variables de entorno (asume que OPENAI_API_KEY está en un archivo .env)
load_dotenv()
client = OpenAI()

# --- CONFIGURACIÓN ---
FOLDER_PATH = r"C:\Users\u14527001\Downloads\grafo_protesis\curso_1"

# --- 1. Carga de Archivos ---
def read_txt_files(folder_path: str) -> Dict[str, str]:
    """Lee todos los archivos .txt de la ruta especificada."""
    files_content = {}
    search_path = os.path.join(folder_path, "*.txt")
    files = glob.glob(search_path)
    
    print(f"📂 Buscando archivos en: {folder_path}")
    if not files:
        print("⚠️ No se encontraron archivos .txt.")
        return {}

    for file_path in files:
        file_name = os.path.basename(file_path)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                files_content[file_name] = f.read()
                print(f"  ✅ Cargado: {file_name}")
        except Exception:
            try:
                # Fallback para codificaciones latinas
                with open(file_path, 'r', encoding='latin-1') as f:
                    files_content[file_name] = f.read()
                    print(f"  ✅ Cargado (latin-1): {file_name}")
            except Exception as e:
                print(f"  ❌ Error leyendo {file_name}: {e}")
    return files_content

# --- 2. Modelos de Datos (Pydantic) ---

# Paso A: Definición del Esquema (Labels abstractos)
class SchemaDefinition(BaseModel):
    node_labels: List[str] = Field(description="Lista de tipos de nodos GENERALES (ej. 'Normativa', 'Organismo', 'Anexo'). NO usar nombres propios ni fechas.")
    relationship_types: List[str] = Field(description="Lista de verbos/relaciones posibles (ej. 'DEROGA', 'EMITE', 'MODIFICA').")

# Paso B: Extracción de Instancias (Datos reales)
class GraphNode(BaseModel):
    id: str = Field(description="Identificador único y limpio (Snake_Case) para el nodo. Ej: 'LEY_27275'.")
    label: str = Field(description="El tipo de nodo (debe coincidir con el esquema aprobado). Ej: 'Normativa'.")
    properties: str = Field(description="Resumen corto o título del nodo. Ej: 'Ley de Acceso a la Info'.")

class GraphRelationship(BaseModel):
    source_id: str = Field(description="ID del nodo origen.")
    source_label: str = Field(description="Label del nodo origen.")
    relationship: str = Field(description="Tipo de relación (UPPERCASE).")
    target_id: str = Field(description="ID del nodo destino.")
    target_label: str = Field(description="Label del nodo destino.")

class ExtractionResult(BaseModel):
    nodes: List[GraphNode]
    relationships: List[GraphRelationship]

# --- 3. Agente Ontólogo (Define los Tipos de Nodos) ---

def run_ontology_agent(text_content: str) -> Tuple[SchemaDefinition, int]:
    print(f"\n--- 🧠 Agente Ontólogo (Definiendo Esquema Abstracto) ---")
    
    system_prompt = """
    Eres un Arquitecto de Datos experto en Neo4j.
    Tu única tarea es leer el texto y definir las CATEGORÍAS (Labels) y RELACIONES abstractas.
    
    REGLAS ESTRICTAS:
    1. NO extraigas instancias específicas (ej. "Resolución 2024").
    2. Usa CamelCase para Nodos (ej. 'Normativa', 'Organismo') y UPPER_CASE para relaciones (ej. 'DEROGA', 'APLICA').
    """
    
    completion = client.beta.chat.completions.parse(
        model="gpt-5-nano",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Analiza este texto y define los Tipos de Nodos y Relaciones:\n{text_content[:15000]}"},
        ],
        response_format=SchemaDefinition,
    )
    
    schema = completion.choices[0].message.parsed
    tokens = completion.usage.total_tokens
    
    print(f"\n[ONTÓLOGO] 📈 Tokens consumidos en este paso: {tokens}")
    print(f"✅ Labels Propuestos: {schema.node_labels}")
    print(f"✅ Relaciones Propuestas: {schema.relationship_types}")
    return schema, tokens

# --- 4. Agente Extractor (Crea los Nodos y Relaciones) ---

def run_extraction_agent(text_content: str, schema: SchemaDefinition) -> Tuple[ExtractionResult, int]:
    print(f"\n--- ⛏️ Agente Extractor (Generando Datos e Instancias) ---")
    
    system_prompt = f"""
    Eres un experto en extracción de Grafos.
    Tu objetivo es extraer instancias reales del texto basándote EXCLUSIVAMENTE en este esquema:
    
    Nodos permitidos (Labels): {schema.node_labels}
    Relaciones permitidas: {schema.relationship_types}
    
    INSTRUCCIONES:
    1. Genera IDs únicos en formato SNAKE_CASE_MAYUSCULA (ej. 'RESOL_2024_2076_INSSJP').
    2. El campo 'label' debe ser uno de los Labels permitidos (ej. 'Normativa', 'Organismo').
    3. Asegúrate de extraer todas las tripletas relevantes.
    """
    
    completion = client.beta.chat.completions.parse(
        model="gpt-5-nano",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Extrae los datos del siguiente texto:\n{text_content[:25000]}"},
        ],
        response_format=ExtractionResult,
    )
    
    result = completion.choices[0].message.parsed
    tokens = completion.usage.total_tokens

    print(f"\n[EXTRACTOR] 📈 Tokens consumidos en este paso: {tokens}")
    print(f"✅ Nodos extraídos: {len(result.nodes)}")
    print(f"✅ Relaciones extraídas: {len(result.relationships)}")
    return result, tokens

# --- 5. Generador de Código Cypher (Python Puro) ---

def generate_cypher_script(data: ExtractionResult):
    """Genera las sentencias Cypher para Neo4j y muestra el esquema abstracto primero."""
    
    # ----------------------------------------------------
    # PASO 5A: Mostrar Tripletas de Esquema Abstracto (TIPO --RELACION--> TIPO)
    # ----------------------------------------------------
    schema_triplets: Set[Tuple[str, str, str]] = set()
    
    # 1. Recopilar tripletas de esquema
    for rel in data.relationships:
        # Usamos el set para obtener solo combinaciones únicas de Label-Rel-Label
        schema_triplets.add((rel.source_label, rel.relationship, rel.target_label))
    
    print("\n" + "="*50)
    print("📢 ESQUEMA ABSTRACTO DE TRIPLETAS (TIPO --RELACIÓN--> TIPO)")
    print("==================================================")
    
    # 2. Imprimir el esquema abstracto ordenado
    if schema_triplets:
        for source_label, relationship, target_label in sorted(list(schema_triplets)):
            print(f"({source_label}) --[{relationship}]--> ({target_label})")
    else:
        print("No se pudieron generar tripletas de esquema. Revise el Agente Extractor.")

    # ----------------------------------------------------
    # PASO 5B: Generar Script Cypher (Instancias)
    # ----------------------------------------------------
    
    cypher_lines = []
    
    # 1. Creación de Nodos (MERGE)
    cypher_lines.append("\n// --- CREACIÓN DE NODOS (MERGE) ---")
    generated_ids: Set[str] = set()
    
    for node in data.nodes:
        if node.id and node.id not in generated_ids:
            safe_prop = node.properties.replace('"', "'")
            line = (f'MERGE (n:{node.label} {{id: "{node.id}"}}) '
                    f'ON CREATE SET n.nombre = "{safe_prop}";')
            cypher_lines.append(line)
            generated_ids.add(node.id)
            
    # 2. Creación de Relaciones (MATCH y MERGE)
    cypher_lines.append("\n// --- CREACIÓN DE RELACIONES (MATCH/MERGE) ---")
    
    for rel in data.relationships:
        if rel.source_id in generated_ids and rel.target_id in generated_ids:
            line = (f'MATCH (a:{rel.source_label} {{id: "{rel.source_id}"}}), '
                    f'(b:{rel.target_label} {{id: "{rel.target_id}"}}) '
                    f'MERGE (a)-[:{rel.relationship}]->(b);')
            cypher_lines.append(line)

    print("\n" + "="*50)
    print("💻 SCRIPT CYPHER GENERADO (Para Neo4j)")
    print("==================================================")
    print("\n".join(cypher_lines))
    print("="*50)

# --- MAIN ---

def main():
    txt_files = read_txt_files(FOLDER_PATH)
    if not txt_files: return

    full_text = "\n".join([f"--- Archivo: {k} ---\n{v}" for k, v in txt_files.items()])
    
    # 1. Agente Ontólogo: Define las CLASES (Labels)
    schema, t1 = run_ontology_agent(full_text)
    
    # 2. Agente Extractor: Extrae las INSTANCIAS (Datos)
    data, t2 = run_extraction_agent(full_text, schema)
    
    # 3. Generador Cypher: Muestra tripletas abstractas y crea el script
    generate_cypher_script(data)
    
    # 4. Reporte final
    total_tokens = t1 + t2
    print("\n" + "="*50)
    print(f"| {'RESUMEN DE CONSUMO DE TOKENS':<46} |")
    print("-" * 50)
    print(f"| Agente Ontólogo: {t1:<33} |")
    print(f"| Agente Extractor: {t2:<32} |")
    print("-" * 50)
    print(f"| 💰 CONSUMO TOTAL: {total_tokens:<33} |")
    print("="*50)

if __name__ == "__main__":
    main()