import os
import glob
import json
import unicodedata
from typing import List, Tuple, Set, Dict
from openai import OpenAI
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Carga variables de entorno
load_dotenv()
client = OpenAI()

# --- CONFIGURACIÓN DEL PROYECTO ---
# Ahora la ruta de la carpeta se toma de la variable de entorno CARPETA_TXT
FOLDER_PATH = os.getenv("CARPETA_TXT")
if not FOLDER_PATH:
    raise ValueError("La variable de entorno 'CARPETA_TXT' no está definida. Por favor, configúrala.")

# Ruta al archivo goal.txt dentro de la carpeta definida
GOAL_FILE_PATH = os.path.join(FOLDER_PATH, "goal.txt")
# Ruta al archivo labels.txt dentro de la carpeta definida
LABELS_FILE_PATH = os.path.join(FOLDER_PATH, "labels.txt")

# Leer la variable de entorno para el modelo LLM
LLM_MODEL = os.getenv("MODELO")
if not LLM_MODEL:
    raise ValueError("La variable de entorno 'MODELO' (para el LLM) no está definida. Por favor, configúrala.")

# Leer USER_GOAL desde goal.txt
USER_GOAL = ""
try:
    with open(GOAL_FILE_PATH, 'r', encoding='utf-8') as f:
        USER_GOAL = f.read().strip()
    print(f"✅ 'USER_GOAL' cargado desde: {GOAL_FILE_PATH}")
except FileNotFoundError:
    raise FileNotFoundError(f"No se encontró el archivo 'goal.txt' en '{GOAL_FILE_PATH}'.")
except Exception as e:
    raise Exception(f"Error al leer 'goal.txt': {e}")

# Leer WELL_KNOWN_LABELS desde labels.txt
WELL_KNOWN_LABELS: List[str] = []
try:
    with open(LABELS_FILE_PATH, 'r', encoding='utf-8') as f:
        labels_str = f.read().strip()
        # Asumiendo que el formato es como "Label1", "Label2", ...
        # Eliminamos las comillas y separamos por coma para obtener la lista
        WELL_KNOWN_LABELS = [label.strip().strip('"') for label in labels_str.split(',') if label.strip()]
    print(f"✅ 'WELL_KNOWN_LABELS' cargado desde: {LABELS_FILE_PATH}")
except FileNotFoundError:
    raise FileNotFoundError(f"No se encontró el archivo 'labels.txt' en '{LABELS_FILE_PATH}'.")
except Exception as e:
    raise Exception(f"Error al leer 'labels.txt': {e}")

# --- FUNCIONES DE AYUDA (LIMPIEZA) ---

def remove_accents(input_str: str) -> str:
    """
    Elimina tildes y normaliza texto para evitar duplicados en el esquema.
    Ej: 'Complicación' -> 'Complicacion', 'CAÍDA' -> 'CAIDA'
    """
    if not input_str:
        return input_str
    # Normalizar a forma NFD (separa caracteres de sus marcas diacríticas)
    nfkd_form = unicodedata.normalize('NFKD', input_str)
    # Filtrar caracteres no combinables (elimina las tildes)
    return "".join([c for c in nfkd_form if not unicodedata.combining(c)])

# --- 1. Carga de Archivos ---
def read_txt_files(folder_path: str) -> Dict[str, str]:
    files_content = {}
    search_path = os.path.join(folder_path, "*.txt")
    
    # Excluir goal.txt y labels.txt de la carga de contenido principal
    excluded_files = [os.path.basename(GOAL_FILE_PATH), os.path.basename(LABELS_FILE_PATH)]
    
    files = [f for f in glob.glob(search_path) if os.path.basename(f) not in excluded_files]
    
    print(f"📂 Buscando archivos de contenido en: {folder_path} (Excluyendo goal.txt y labels.txt)")
    if not files:
        print("⚠️ No se encontraron archivos .txt de contenido.")
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

# --- 2. Modelos de Datos ---

class SchemaDefinition(BaseModel):
    node_labels: List[str] = Field(description="Lista de tipos de nodos GENERALES (ej. 'Enfermedad', 'Sintoma').")
    relationship_types: List[str] = Field(description="Lista de verbos/relaciones posibles (ej. 'PROVOCA', 'TRATA').")

class GraphNode(BaseModel):
    id: str = Field(description="Identificador único y limpio (SNAKE_CASE_MAYUSCULA) para el nodo.")
    label: str = Field(description="El tipo de nodo (debe coincidir con el esquema aprobado).")
    properties: str = Field(description="Resumen corto o nombre descriptivo del nodo.")

class GraphRelationship(BaseModel):
    source_id: str = Field(description="ID del nodo origen.")
    source_label: str = Field(description="Label del nodo origen.")
    relationship: str = Field(description="Tipo de relación (UPPERCASE).")
    target_id: str = Field(description="ID del nodo destino.")
    target_label: str = Field(description="Label del nodo destino.")

class ExtractionResult(BaseModel):
    nodes: List[GraphNode]
    relationships: List[GraphRelationship]

# --- 3. Agentes ---

def run_ontology_agent(text_content: str, goal: str, known_labels: List[str], llm_model: str) -> Tuple[SchemaDefinition, int]:
    system_prompt = f"""
    Eres un Arquitecto de Datos experto en Neo4j.
    Tu tarea es definir el ESQUEMA (Labels y Relaciones) para un Grafo de Conocimiento.
    
    OBJETIVO: {goal}
    ENTIDADES CONOCIDAS: {known_labels}
    
    REGLAS ESTRICTAS DE FORMATO:
    1. IDIOMA: Todo en CASTELLANO.
    2. **IMPORTANTE: NO USES TILDES NI ACENTOS** en los Labels ni en las Relaciones.
       - INCORRECTO: 'Complicación', 'Síntoma', 'ASOCIACIÓN'
       - CORRECTO: 'Complicacion', 'Sintoma', 'ASOCIACION'
    3. Labels en CamelCase (ej. FactorRiesgo).
    4. Relaciones en UPPER_CASE con guiones bajos (ej. PROVOCA_EFECTO).
    """
    
    content_sample = text_content[:15000]
    
    completion = client.beta.chat.completions.parse(
        model=llm_model, # Usa la variable del modelo LLM
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Analiza y define el esquema:\n{content_sample}"},
        ],
        response_format=SchemaDefinition,
    )
    
    schema = completion.choices[0].message.parsed
    
    # --- LIMPIEZA FORZADA (PYTHON) ---
    # Aunque el LLM falle, Python lo corrige aquí
    schema.node_labels = [remove_accents(l) for l in schema.node_labels]
    schema.relationship_types = [remove_accents(r) for r in schema.relationship_types]
    
    tokens = completion.usage.total_tokens
    print(f"  [ONTÓLOGO] 📈 Tokens: {tokens} | Labels: {len(schema.node_labels)} | Rels: {len(schema.relationship_types)}")
    return schema, tokens

def run_extraction_agent(text_content: str, schema: SchemaDefinition, llm_model: str) -> Tuple[ExtractionResult, int]:
    system_prompt = f"""
    Eres un experto en extracción de Grafos.
    Extrae instancias basándote en este esquema UNIFICADO:
    
    Nodos permitidos: {schema.node_labels}
    Relaciones permitidas: {schema.relationship_types}
    
    INSTRUCCIONES:
    1. Genera IDs únicos en formato SNAKE_CASE_MAYUSCULA (ej. DIABETES_TIPO_2).
    2. **NO USES TILDES EN LOS LABELS NI RELACIONES** (ej. usa 'Condicion' no 'Condición').
    3. En las 'properties' (nombres descriptivos) SÍ puedes usar tildes.
    """
    
    completion = client.beta.chat.completions.parse(
        model=llm_model, # Usa la variable del modelo LLM
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Extrae los datos:\n{text_content[:30000]}"},
        ],
        response_format=ExtractionResult,
    )
    
    result = completion.choices[0].message.parsed
    
    # --- LIMPIEZA FORZADA (PYTHON) ---
    # Limpiamos labels y relaciones de las instancias extraídas
    for node in result.nodes:
        node.label = remove_accents(node.label)
        # Nota: node.id lo dejamos como decida el LLM (generalmente uppercase), 
        # pero node.properties SÍ queremos que tenga acentos para lectura humana.

    for rel in result.relationships:
        rel.source_label = remove_accents(rel.source_label)
        rel.target_label = remove_accents(rel.target_label)
        rel.relationship = remove_accents(rel.relationship)

    tokens = completion.usage.total_tokens
    print(f"  [EXTRACTOR] 📈 Tokens: {tokens} | Nodos: {len(result.nodes)} | Rels: {len(result.relationships)}")
    return result, tokens

# --- 4. Generador Cypher ---

def generate_cypher_fragment(data: ExtractionResult, filename: str) -> str:
    cypher_lines = []
    
    # Nodo Documento (Grafo Léxico)
    doc_id = remove_accents(filename.replace(".", "_").replace(" ", "_").replace("-", "_").upper())
    cypher_lines.append(f"\n// --- ARCHIVO: {filename} ---")
    cypher_lines.append(f'MERGE (d:Documento {{id: "{doc_id}"}}) ON CREATE SET d.nombre = "{filename}";')

    generated_ids: Set[str] = set()
    
    # Nodos
    for node in data.nodes:
        if node.id and node.id not in generated_ids:
            safe_prop = node.properties.replace('"', "'")
            # Crear nodo entidad
            cypher_lines.append(f'MERGE (n:{node.label} {{id: "{node.id}"}}) ON CREATE SET n.nombre = "{safe_prop}";')
            # Conectar con Documento
            cypher_lines.append(f'MATCH (d:Documento {{id: "{doc_id}"}}), (n:{node.label} {{id: "{node.id}"}}) MERGE (d)-[:MENCIONA]->(n);')
            generated_ids.add(node.id)
            
    # Relaciones
    for rel in data.relationships:
        if rel.source_id in generated_ids and rel.target_id in generated_ids:
            cypher_lines.append(f'MATCH (a:{rel.source_label} {{id: "{rel.source_id}"}}), (b:{rel.target_label} {{id: "{rel.target_id}"}}) MERGE (a)-[:{rel.relationship}]->(b);')

    return "\n".join(cypher_lines)

# --- MAIN ---

def main():
    txt_files = read_txt_files(FOLDER_PATH)
    if not txt_files: return

    # Inicializar sets limpiando las etiquetas conocidas de entrada
    master_node_labels: Set[str] = set([remove_accents(l) for l in WELL_KNOWN_LABELS])
    master_relationship_types: Set[str] = set()
    global_schema_triplets: Set[Tuple[str, str, str]] = set()
    
    total_t1 = 0
    total_t2 = 0

    # FASE 1: DISCOVERY
    print("\n" + "#"*60)
    print("FASE 1: DESCUBRIMIENTO DEL ESQUEMA (Sin Tildes)")
    print("#"*60)

    for filename, content in txt_files.items():
        print(f"\n--- 🔎 Analizando esquema en: {filename} ---")
        # Pasamos la lista ya limpia de known_labels y el modelo LLM
        schema, t1 = run_ontology_agent(content, USER_GOAL, list(master_node_labels), LLM_MODEL)
        total_t1 += t1
        
        master_node_labels.update(schema.node_labels)
        master_relationship_types.update(schema.relationship_types)
        
    master_schema = SchemaDefinition(
        node_labels=sorted(list(master_node_labels)),
        relationship_types=sorted(list(master_relationship_types))
    )
    
    print(f"\n✅ Esquema Maestro Definido (Normalizado):")
    print(f"Labels: {master_schema.node_labels}")

    # FASE 2: EXTRACTION
    print("\n" + "#"*60)
    print("FASE 2: EXTRACCIÓN Y GENERACIÓN DE CÓDIGO")
    print("#"*60)
    
    full_cypher_script = []
    
    # Constraints (Labels ya limpios)
    full_cypher_script.append("// --- CONSTRAINTS DE UNICIDAD ---")
    for label in master_schema.node_labels:
        full_cypher_script.append(f"CREATE CONSTRAINT constraint_{label}_id IF NOT EXISTS FOR (n:{label}) REQUIRE n.id IS UNIQUE;")
    full_cypher_script.append("CREATE CONSTRAINT constraint_Documento_id IF NOT EXISTS FOR (d:Documento) REQUIRE d.id IS UNIQUE;")

    for filename, content in txt_files.items():
        print(f"\n--- ⛏️ Procesando archivo: {filename} ---")
        
        # Pasamos el modelo LLM al agente de extracción
        data, t2 = run_extraction_agent(content, master_schema, LLM_MODEL)
        total_t2 += t2
        
        for rel in data.relationships:
            global_schema_triplets.add((rel.source_label, rel.relationship, rel.target_label))

        fragment = generate_cypher_fragment(data, filename)
        full_cypher_script.append(fragment)

    # RESULTADOS
    print("\n" + "="*60)
    print("📢 ESQUEMA ABSTRACTO DESCUBIERTO (TIPO --RELACIÓN--> TIPO)")
    print("="*60)
    if global_schema_triplets:

class GraphNode(BaseModel):
    id: str = Field(description="Identificador único y limpio (SNAKE_CASE_MAYUSCULA) para el nodo.")
    label: str = Field(description="El tipo de nodo (debe coincidir con el esquema aprobado).")
    properties: str = Field(description="Resumen corto o nombre descriptivo del nodo.")

class GraphRelationship(BaseModel):
    source_id: str = Field(description="ID del nodo origen.")
    source_label: str = Field(description="Label del nodo origen.")
    relationship: str = Field(description="Tipo de relación (UPPERCASE).")
    target_id: str = Field(description="ID del nodo destino.")
    target_label: str = Field(description="Label del nodo destino.")

class ExtractionResult(BaseModel):
    nodes: List[GraphNode]
    relationships: List[GraphRelationship]

# --- 3. Agentes ---

def run_ontology_agent(text_content: str, goal: str, known_labels: List[str], llm_model: str) -> Tuple[SchemaDefinition, int]:
    system_prompt = f"""
    Eres un Arquitecto de Datos experto en Neo4j.
    Tu tarea es definir el ESQUEMA (Labels y Relaciones) para un Grafo de Conocimiento.
    
    OBJETIVO: {goal}
    ENTIDADES CONOCIDAS: {known_labels}
    
    REGLAS ESTRICTAS DE FORMATO:
    1. IDIOMA: Todo en CASTELLANO.
    2. **IMPORTANTE: NO USES TILDES NI ACENTOS** en los Labels ni en las Relaciones.
       - INCORRECTO: 'Complicación', 'Síntoma', 'ASOCIACIÓN'
       - CORRECTO: 'Complicacion', 'Sintoma', 'ASOCIACION'
    3. Labels en CamelCase (ej. FactorRiesgo).
    4. Relaciones en UPPER_CASE con guiones bajos (ej. PROVOCA_EFECTO).
    """
    
    content_sample = text_content[:15000]
    
    completion = client.beta.chat.completions.parse(
        model=llm_model, # Usa la variable del modelo LLM
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Analiza y define el esquema:\n{content_sample}"},
        ],
        response_format=SchemaDefinition,
    )
    
    schema = completion.choices[0].message.parsed
    
    # --- LIMPIEZA FORZADA (PYTHON) ---
    # Aunque el LLM falle, Python lo corrige aquí
    schema.node_labels = [remove_accents(l) for l in schema.node_labels]
    schema.relationship_types = [remove_accents(r) for r in schema.relationship_types]
    
    tokens = completion.usage.total_tokens
    print(f"  [ONTÓLOGO] 📈 Tokens: {tokens} | Labels: {len(schema.node_labels)} | Rels: {len(schema.relationship_types)}")
    return schema, tokens

def run_extraction_agent(text_content: str, schema: SchemaDefinition, llm_model: str) -> Tuple[ExtractionResult, int]:
    system_prompt = f"""
    Eres un experto en extracción de Grafos.
    Extrae instancias basándote en este esquema UNIFICADO:
    
    Nodos permitidos: {schema.node_labels}
    Relaciones permitidas: {schema.relationship_types}
    
    INSTRUCCIONES:
    1. Genera IDs únicos en formato SNAKE_CASE_MAYUSCULA (ej. DIABETES_TIPO_2).
    2. **NO USES TILDES EN LOS LABELS NI RELACIONES** (ej. usa 'Condicion' no 'Condición').
    3. En las 'properties' (nombres descriptivos) SÍ puedes usar tildes.
    """
    
    completion = client.beta.chat.completions.parse(
        model=llm_model, # Usa la variable del modelo LLM
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Extrae los datos:\n{text_content[:30000]}"},
        ],
        response_format=ExtractionResult,
    )
    
    result = completion.choices[0].message.parsed
    
    # --- LIMPIEZA FORZADA (PYTHON) ---
    # Limpiamos labels y relaciones de las instancias extraídas
    for node in result.nodes:
        node.label = remove_accents(node.label)
        # Nota: node.id lo dejamos como decida el LLM (generalmente uppercase), 
        # pero node.properties SÍ queremos que tenga acentos para lectura humana.

    for rel in result.relationships:
        rel.source_label = remove_accents(rel.source_label)
        rel.target_label = remove_accents(rel.target_label)
        rel.relationship = remove_accents(rel.relationship)

    tokens = completion.usage.total_tokens
    print(f"  [EXTRACTOR] 📈 Tokens: {tokens} | Nodos: {len(result.nodes)} | Rels: {len(result.relationships)}")
    return result, tokens

# --- 4. Generador Cypher ---

def generate_cypher_fragment(data: ExtractionResult, filename: str) -> str:
    cypher_lines = []
    
    # Nodo Documento (Grafo Léxico)
    doc_id = remove_accents(filename.replace(".", "_").replace(" ", "_").replace("-", "_").upper())
    cypher_lines.append(f"\n// --- ARCHIVO: {filename} ---")
    cypher_lines.append(f'MERGE (d:Documento {{id: "{doc_id}"}}) ON CREATE SET d.nombre = "{filename}";')

    generated_ids: Set[str] = set()
    
    # Nodos
    for node in data.nodes:
        if node.id and node.id not in generated_ids:
            safe_prop = node.properties.replace('"', "'")
            # Crear nodo entidad
            cypher_lines.append(f'MERGE (n:{node.label} {{id: "{node.id}"}}) ON CREATE SET n.nombre = "{safe_prop}";')
            # Conectar con Documento
            cypher_lines.append(f'MATCH (d:Documento {{id: "{doc_id}"}}), (n:{node.label} {{id: "{node.id}"}}) MERGE (d)-[:MENCIONA]->(n);')
            generated_ids.add(node.id)
            
    # Relaciones
    for rel in data.relationships:
        if rel.source_id in generated_ids and rel.target_id in generated_ids:
            cypher_lines.append(f'MATCH (a:{rel.source_label} {{id: "{rel.source_id}"}}), (b:{rel.target_label} {{id: "{rel.target_id}"}}) MERGE (a)-[:{rel.relationship}]->(b);')

    return "\n".join(cypher_lines)

# --- MAIN ---

def main():
    txt_files = read_txt_files(FOLDER_PATH)
    if not txt_files: return

    # Inicializar sets limpiando las etiquetas conocidas de entrada
    master_node_labels: Set[str] = set([remove_accents(l) for l in WELL_KNOWN_LABELS])
    master_relationship_types: Set[str] = set()
    global_schema_triplets: Set[Tuple[str, str, str]] = set()
    
    total_t1 = 0
    total_t2 = 0

    # FASE 1: DISCOVERY
    print("\n" + "#"*60)
    print("FASE 1: DESCUBRIMIENTO DEL ESQUEMA (Sin Tildes)")
    print("#"*60)

    for filename, content in txt_files.items():
        print(f"\n--- 🔎 Analizando esquema en: {filename} ---")
        # Pasamos la lista ya limpia de known_labels y el modelo LLM
        schema, t1 = run_ontology_agent(content, USER_GOAL, list(master_node_labels), LLM_MODEL)
        total_t1 += t1
        
        master_node_labels.update(schema.node_labels)
        master_relationship_types.update(schema.relationship_types)
        
    master_schema = SchemaDefinition(
        node_labels=sorted(list(master_node_labels)),
        relationship_types=sorted(list(master_relationship_types))
    )
    
    print(f"\n✅ Esquema Maestro Definido (Normalizado):")
    print(f"Labels: {master_schema.node_labels}")

    # FASE 2: EXTRACTION
    print("\n" + "#"*60)
    print("FASE 2: EXTRACCIÓN Y GENERACIÓN DE CÓDIGO")
    print("#"*60)
    
    full_cypher_script = []
    
    # Constraints (Labels ya limpios)
    full_cypher_script.append("// --- CONSTRAINTS DE UNICIDAD ---")
    for label in master_schema.node_labels:
        full_cypher_script.append(f"CREATE CONSTRAINT constraint_{label}_id IF NOT EXISTS FOR (n:{label}) REQUIRE n.id IS UNIQUE;")
    full_cypher_script.append("CREATE CONSTRAINT constraint_Documento_id IF NOT EXISTS FOR (d:Documento) REQUIRE d.id IS UNIQUE;")

    for filename, content in txt_files.items():
        print(f"\n--- ⛏️ Procesando archivo: {filename} ---")
        
        # Pasamos el modelo LLM al agente de extracción
        data, t2 = run_extraction_agent(content, master_schema, LLM_MODEL)
        total_t2 += t2
        
        for rel in data.relationships:
            global_schema_triplets.add((rel.source_label, rel.relationship, rel.target_label))

        fragment = generate_cypher_fragment(data, filename)
        full_cypher_script.append(fragment)

    # RESULTADOS
    print("\n" + "="*60)
    print("📢 ESQUEMA ABSTRACTO DESCUBIERTO (TIPO --RELACIÓN--> TIPO)")
    print("="*60)
    if global_schema_triplets:
        for s, r, t in sorted(list(global_schema_triplets)):
            print(f"({s}) --[{r}]--> ({t})")
    else:
        print("(No se detectaron relaciones)")

    final_script = "\n".join(full_cypher_script)
    
    with open("grafo_generado.cypher", "w", encoding="utf-8") as f:
        f.write(final_script)
    
    # GENERAR ARCHIVO DE ESQUEMA CONCEPTUAL
    conceptual_schema_lines = []
    conceptual_schema_lines.append("// ========================================")
    conceptual_schema_lines.append("// ESQUEMA CONCEPTUAL DEL GRAFO")
    conceptual_schema_lines.append("// ========================================")
    conceptual_schema_lines.append("// Patrones de relaciones descubiertas:")
    conceptual_schema_lines.append("//")
    
    if global_schema_triplets:
        for s, r, t in sorted(list(global_schema_triplets)):
            conceptual_schema_lines.append(f"// ({s}) --[{r}]--> ({t})")
    else:
        conceptual_schema_lines.append("// (No se detectaron relaciones)")
    
    conceptual_schema = "\n".join(conceptual_schema_lines)
    
    with open("grafo_concepto.cypher", "w", encoding="utf-8") as f:
        f.write(conceptual_schema)
        
    print("\n" + "="*60)
    print("💻 SCRIPT CYPHER FINAL (Guardado en 'grafo_generado.cypher')")
    print("="*60)
    # Imprime solo las primeras 20 líneas del script para no saturar la consola
    print("\n".join(final_script.split("\n")[:20]))
    
    print("\n" + "="*60)
    print("📐 ESQUEMA CONCEPTUAL (Guardado en 'grafo_concepto.cypher')")
    print("="*60)
    print(conceptual_schema)
    
    print(f"\n💰 CONSUMO TOTAL: {total_t1 + total_t2} Tokens")

if __name__ == "__main__":
    main()