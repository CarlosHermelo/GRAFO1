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
                with open(file_path, 'r', encoding='latin-1') as f:
                    files_content[file_name] = f.read()
                    print(f"  ✅ Cargado (latin-1): {file_name}")
            except Exception as e:
                print(f"  ❌ Error leyendo {file_name}: {e}")
    return files_content

# --- 2. Modelos de Datos (Pydantic) ---

class SchemaDefinition(BaseModel):
    node_labels: List[str] = Field(description="Lista de tipos de nodos GENERALES (ej. 'Normativa', 'Organismo').")
    relationship_types: List[str] = Field(description="Lista de verbos/relaciones posibles (ej. 'DEROGA', 'EMITE').")

class GraphNode(BaseModel):
    id: str = Field(description="Identificador único y limpio (Snake_Case) para el nodo.")
    label: str = Field(description="El tipo de nodo (debe coincidir con el esquema aprobado).")
    properties: str = Field(description="Resumen corto o título del nodo.")

class GraphRelationship(BaseModel):
    source_id: str = Field(description="ID del nodo origen.")
    source_label: str = Field(description="Label del nodo origen.")
    relationship: str = Field(description="Tipo de relación (UPPERCASE).")
    target_id: str = Field(description="ID del nodo destino.")
    target_label: str = Field(description="Label del nodo destino.")

class ExtractionResult(BaseModel):
    nodes: List[GraphNode]
    relationships: List[GraphRelationship]

# --- 3. Agentes (Ontólogo y Extractor) ---

def run_ontology_agent(text_content: str) -> Tuple[SchemaDefinition, int]:
    system_prompt = """
    Eres un Arquitecto de Datos experto en Neo4j.
    Tu única tarea es leer el texto y definir las CATEGORÍAS (Labels) y RELACIONES abstractas.
    REGLAS: No extraigas instancias. Usa CamelCase para Nodos y UPPER_CASE para relaciones.
    """
    content_sample = text_content[:10000]
    completion = client.beta.chat.completions.parse(
        model="gpt-5-nano",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Analiza y define el esquema:\n{content_sample}"},
        ],
        response_format=SchemaDefinition,
    )
    schema = completion.choices[0].message.parsed
    tokens = completion.usage.total_tokens
    print(f"  [ONTÓLOGO] 📈 Tokens: {tokens} | Labels: {len(schema.node_labels)} | Rels: {len(schema.relationship_types)}")
    return schema, tokens

def run_extraction_agent(text_content: str, schema: SchemaDefinition) -> Tuple[ExtractionResult, int]:
    system_prompt = f"""
    Eres un experto en extracción de Grafos.
    Extrae instancias reales basándote EXCLUSIVAMENTE en este esquema:
    Nodos: {schema.node_labels}
    Relaciones: {schema.relationship_types}
    INSTRUCCIONES: Genera IDs únicos (SNAKE_CASE). Extrae tripletas.
    """
    completion = client.beta.chat.completions.parse(
        model="gpt-5-nano",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Extrae datos:\n{text_content[:25000]}"},
        ],
        response_format=ExtractionResult,
    )
    result = completion.choices[0].message.parsed
    tokens = completion.usage.total_tokens
    print(f"  [EXTRACTOR] 📈 Tokens: {tokens} | Nodos: {len(result.nodes)} | Rels: {len(result.relationships)}")
    return result, tokens

# --- 4. Generador Cypher con Trazabilidad ---

def generate_cypher_fragment(data: ExtractionResult, filename: str) -> str:
    """Genera el bloque Cypher para un archivo específico, incluyendo trazabilidad."""
    cypher_lines = []
    
    # [cite_start]A. Nodo Documento (Grafo Léxico) [cite: 12]
    doc_id = filename.replace(".", "_").replace(" ", "_").upper()
    cypher_lines.append(f"\n// --- ARCHIVO: {filename} ---")
    cypher_lines.append(f'MERGE (d:Documento {{id: "{doc_id}"}}) ON CREATE SET d.nombre = "{filename}";')

    # B. Nodos y Conexión al Documento
    generated_ids: Set[str] = set()
    for node in data.nodes:
        if node.id and node.id not in generated_ids:
            safe_prop = node.properties.replace('"', "'")
            # Crear nodo entidad
            cypher_lines.append(f'MERGE (n:{node.label} {{id: "{node.id}"}}) ON CREATE SET n.nombre = "{safe_prop}";')
            # Relación de trazabilidad: Documento -> MENCIONA -> Entidad
            cypher_lines.append(f'MATCH (d:Documento {{id: "{doc_id}"}}), (n:{node.label} {{id: "{node.id}"}}) MERGE (d)-[:MENCIONA]->(n);')
            generated_ids.add(node.id)
            
    # C. Relaciones Semánticas
    for rel in data.relationships:
        if rel.source_id in generated_ids and rel.target_id in generated_ids:
            cypher_lines.append(f'MATCH (a:{rel.source_label} {{id: "{rel.source_id}"}}), (b:{rel.target_label} {{id: "{rel.target_id}"}}) MERGE (a)-[:{rel.relationship}]->(b);')

    return "\n".join(cypher_lines)

# --- MAIN ---

def main():
    txt_files = read_txt_files(FOLDER_PATH)
    if not txt_files: return

    # Contadores Globales
    master_node_labels: Set[str] = set()
    master_relationship_types: Set[str] = set()
    global_schema_triplets: Set[Tuple[str, str, str]] = set() # <--- Aquí acumularemos el esquema abstracto
    
    total_t1 = 0
    total_t2 = 0

    # ==========================================================
    # PASE 1: DISCOVERY (Define el Esquema Maestro)
    # ==========================================================
    print("\n" + "#"*50)
    print("FASE 1: DESCUBRIMIENTO DEL ESQUEMA")
    print("#"*50)

    for filename, content in txt_files.items():
        print(f"\n--- 🔎 Analizando: {filename} ---")
        schema, t1 = run_ontology_agent(content)
        total_t1 += t1
        master_node_labels.update(schema.node_labels)
        master_relationship_types.update(schema.relationship_types)
        
    master_schema = SchemaDefinition(
        node_labels=sorted(list(master_node_labels)),
        relationship_types=sorted(list(master_relationship_types))
    )

    # ==========================================================
    # PASE 2: EXTRACTION (Genera Datos y Cypher)
    # ==========================================================
    print("\n" + "#"*50)
    print("FASE 2: EXTRACCIÓN Y GENERACIÓN DE CÓDIGO")
    print("#"*50)
    
    full_cypher_script = []
    
    # [cite_start]Optimización: Constraints [cite: 11]
    full_cypher_script.append("// --- CONSTRAINTS DE UNICIDAD ---")
    for label in master_schema.node_labels:
        full_cypher_script.append(f"CREATE CONSTRAINT constraint_{label}_id IF NOT EXISTS FOR (n:{label}) REQUIRE n.id IS UNIQUE;")
    full_cypher_script.append("CREATE CONSTRAINT constraint_Documento_id IF NOT EXISTS FOR (d:Documento) REQUIRE d.id IS UNIQUE;")

    for filename, content in txt_files.items():
        print(f"\n--- ⛏️ Procesando: {filename} ---")
        
        # 1. Extracción
        data, t2 = run_extraction_agent(content, master_schema)
        total_t2 += t2
        
        # 2. Acumular Tripletas para el Esquema Abstracto (Lo que pediste agregar)
        for rel in data.relationships:
            global_schema_triplets.add((rel.source_label, rel.relationship, rel.target_label))

        # 3. Generar fragmento Cypher
        fragment = generate_cypher_fragment(data, filename)
        full_cypher_script.append(fragment)

    # ==========================================================
    # RESULTADOS FINALES
    # ==========================================================

    # 1. IMPRESIÓN DEL ESQUEMA ABSTRACTO (Aquí está de vuelta)
    print("\n" + "="*50)
    print("📢 ESQUEMA ABSTRACTO DE TRIPLETAS (TIPO --RELACIÓN--> TIPO)")
    print("==================================================")
    if global_schema_triplets:
        for s, r, t in sorted(list(global_schema_triplets)):
            print(f"({s}) --[{r}]--> ({t})")
    else:
        print("(No se detectaron relaciones)")

    # 2. IMPRESIÓN DEL SCRIPT CYPHER
    final_script = "\n".join(full_cypher_script)
    print("\n" + "="*50)
    print("💻 SCRIPT CYPHER FINAL (Con Constraints y Trazabilidad)")
    print("==================================================")
    print(final_script)
    print("="*50)
    
    # 3. Reporte Tokens
    print(f"\n💰 CONSUMO TOTAL: {total_t1 + total_t2} Tokens (Ontólogo: {total_t1} | Extractor: {total_t2})")

if __name__ == "__main__":
    main()