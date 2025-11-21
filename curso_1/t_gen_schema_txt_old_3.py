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

# --- CONFIGURACIÓN DEL PROYECTO ---
FOLDER_PATH = r"C:\Users\u14527001\Downloads\grafo_protesis\curso_1"

#  - Definimos el objetivo para filtrar entidades irrelevantes
USER_GOAL = """
Construir un Grafo de Conocimiento clínico que permita analizar de manera integrada el contenido de múltiples guías médicas, identificar relaciones entre enfermedades, tratamientos, factores de riesgo y complicaciones, y responder preguntas complejas basadas en comorbilidades.

objetivos específicos

Identificar vínculos clínicos fundamentales entre entidades médicas, tales como:
• asociación causal (FactorRiesgo → Enfermedad)
• indicación terapéutica (Enfermedad → Tratamiento)
• contraindicación o ajuste (Tratamiento → Condición)
• progresión o complicación (Enfermedad → Complicación)

Representar coherentemente la estructura clínica de cada guía:
• criterios diagnósticos
• clasificaciones (GOLD, KDIGO, grados de hipertensión, etc.)
• recomendaciones según severidad
• decisiones terapéuticas dependientes de otras enfermedades

Integrar entidades que aparecen en diferentes guías y que deben unificarse en un único espacio semántico:
• patologías compartidas
• tratamientos utilizados en varias condiciones
• factores de riesgo comunes
• complicaciones que conectan múltiples enfermedades

criterios de exclusión

Ignorar detalles administrativos o logísticos que no afecten el razonamiento clínico:
• nombres propios de instituciones
• direcciones
• datos anecdóticos sin impacto en diagnóstico, tratamiento o evolución
• valores no estandarizados sin relación explícita con decisiones clínicas

tres entidades representativas

Enfermedad: “Diabetes tipo 2”

Tratamiento: “IECA”

Complicación: “Insuficiencia renal crónica”

"""

# [cite: 439, 454] - Etiquetas conocidas para estandarizar el grafo desde el principio
WELL_KNOWN_LABELS = ["Enfermedad", "Tratamiento", "Condición", "Complicación", "FactorRiesgo"]


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
    node_labels: List[str] = Field(description="Lista de tipos de nodos GENERALES (ej. 'Resolucion', 'Organismo').")
    relationship_types: List[str] = Field(description="Lista de verbos/relaciones posibles (ej. 'DEROGA', 'EMITE').")

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

# --- 3. Agentes (Ontólogo y Extractor) ---

def run_ontology_agent(text_content: str, goal: str, known_labels: List[str]) -> Tuple[SchemaDefinition, int]:
    """
    Fase 1: Descubre el esquema abstracto basándose en el objetivo y etiquetas conocidas.
    [cite: 405, 407] - Analiza archivos buscando tipos de entidades relevantes.
    """
    system_prompt = f"""
    Eres un Arquitecto de Datos experto en Neo4j.
    Tu tarea es definir el ESQUEMA (Labels y Relaciones) para un Grafo de Conocimiento.
    
    OBJETIVO DEL USUARIO: {goal}
    ENTIDADES CONOCIDAS (Úsalas si aplican): {known_labels}
    
    REGLAS:
1. Todas las entidades, labels, tipos de nodos y nombres deben estar EN CASTELLANO.
2. Todas las relaciones deben estar EN CASTELLANO y en MAYÚSCULAS (ej. FACTOR_DE_RIESGO_DE, COMPLICA, INDICA_TRATAMIENTO, ASOCIA_A).
3. Nunca uses verbos ni labels en inglés. No usar: RESULTS_IN_COMPLICATION, CAUSES, HAS, TREATS, etc.
4. Usa CamelCase para los nombres de nodos (ej. Enfermedad, CriterioDiagnostico, FactorRiesgo).
5. Usa UPPER_CASE con guiones bajos para relaciones (ej. PRODUCE_COMPLICACION, INDICA, SE_ASOCIA_CON).
6. Usa solo las entidades relevantes para el objetivo clínico.



    """
    
    content_sample = text_content[:15000] # Muestra representativa
    
    completion = client.beta.chat.completions.parse(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Analiza este texto y define el esquema:\n{content_sample}"},
        ],
        response_format=SchemaDefinition,
    )
    
    schema = completion.choices[0].message.parsed
    tokens = completion.usage.total_tokens
    
    print(f"  [ONTÓLOGO] 📈 Tokens: {tokens} | Labels: {len(schema.node_labels)} | Rels: {len(schema.relationship_types)}")
    return schema, tokens

def run_extraction_agent(text_content: str, schema: SchemaDefinition) -> Tuple[ExtractionResult, int]:
    """
    Fase 2: Extrae instancias usando el esquema maestro unificado.
    [cite: 410, 411] - Usa el contexto aprobado para extraer tripletas.
    """
    system_prompt = f"""
    Eres un experto en extracción de Grafos.
    Tu objetivo es extraer instancias reales del texto basándote EXCLUSIVAMENTE en este esquema UNIFICADO:
    
    Nodos permitidos: {schema.node_labels}
    Relaciones permitidas: {schema.relationship_types}
    
   INSTRUCCIONES:
1. Todos los labels de nodos deben estar en castellano y en CamelCase (ej. Enfermedad, Tratamiento, Complicación, FactorRiesgo).
2. Todas las relaciones deben estar en castellano, en MAYÚSCULAS y con guiones bajos (ej. PRODUCE_COMPLICACION, AUMENTA_RIESGO_DE, INDICA_TRATAMIENTO).
3. No usar ninguna relación ni label en inglés. Nunca usar: RESULTS_IN_COMPLICATION, CAUSES, LEADS_TO, HAS, etc.
4. Genera IDs en SNAKE_CASE_MAYÚSCULA en castellano.
5. Usa solo relaciones incluidas en el esquema pasado.
6. No inventes verbos que no sean clínicos o semánticos. Usar expresiones naturales del castellano.

    """
    
    completion = client.beta.chat.completions.parse(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Extrae los datos del siguiente texto:\n{text_content[:30000]}"},
        ],
        response_format=ExtractionResult,
    )
    
    result = completion.choices[0].message.parsed
    tokens = completion.usage.total_tokens

    print(f"  [EXTRACTOR] 📈 Tokens: {tokens} | Nodos: {len(result.nodes)} | Rels: {len(result.relationships)}")
    return result, tokens

# --- 4. Generador Cypher con Trazabilidad ---

def generate_cypher_fragment(data: ExtractionResult, filename: str) -> str:
    """Genera el bloque Cypher para un archivo, incluyendo el Grafo Léxico (Documento -> Entidad)."""
    cypher_lines = []
    
    # [cite: 761] - Creación del nodo Documento (Lexical Graph)
    doc_id = filename.replace(".", "_").replace(" ", "_").replace("-", "_").upper()
    cypher_lines.append(f"\n// --- ARCHIVO: {filename} ---")
    cypher_lines.append(f'MERGE (d:Documento {{id: "{doc_id}"}}) ON CREATE SET d.nombre = "{filename}";')

    generated_ids: Set[str] = set()
    
    # Nodos y Conexión Léxica
    for node in data.nodes:
        if node.id and node.id not in generated_ids:
            safe_prop = node.properties.replace('"', "'")
            # Crear nodo entidad (Subject Graph)
            cypher_lines.append(f'MERGE (n:{node.label} {{id: "{node.id}"}}) ON CREATE SET n.nombre = "{safe_prop}";')
            
            # Conectar Documento con Entidad (Trazabilidad)
            cypher_lines.append(f'MATCH (d:Documento {{id: "{doc_id}"}}), (n:{node.label} {{id: "{node.id}"}}) MERGE (d)-[:MENCIONA]->(n);')
            
            generated_ids.add(node.id)
            
    # Relaciones Semánticas (Subject Graph)
    for rel in data.relationships:
        if rel.source_id in generated_ids and rel.target_id in generated_ids:
            cypher_lines.append(f'MATCH (a:{rel.source_label} {{id: "{rel.source_id}"}}), (b:{rel.target_label} {{id: "{rel.target_id}"}}) MERGE (a)-[:{rel.relationship}]->(b);')

    return "\n".join(cypher_lines)

# --- MAIN ---

def main():
    txt_files = read_txt_files(FOLDER_PATH)
    if not txt_files: return

    # Inicializar sets y contadores
    master_node_labels: Set[str] = set(WELL_KNOWN_LABELS) # Iniciamos con lo conocido
    master_relationship_types: Set[str] = set()
    global_schema_triplets: Set[Tuple[str, str, str]] = set()
    
    total_t1 = 0
    total_t2 = 0

    # ==========================================================
    # PASE 1: DISCOVERY (Define el Esquema Maestro)
    # ==========================================================
    print("\n" + "#"*60)
    print("FASE 1: DESCUBRIMIENTO DEL ESQUEMA (Ontología)")
    print("#"*60)

    for filename, content in txt_files.items():
        print(f"\n--- 🔎 Analizando esquema en: {filename} ---")
        schema, t1 = run_ontology_agent(content, USER_GOAL, list(master_node_labels))
        total_t1 += t1
        
        # Fusión inteligente de esquemas
        master_node_labels.update(schema.node_labels)
        master_relationship_types.update(schema.relationship_types)
        
    master_schema = SchemaDefinition(
        node_labels=sorted(list(master_node_labels)),
        relationship_types=sorted(list(master_relationship_types))
    )
    
    print(f"\n✅ Esquema Maestro Definido: {len(master_schema.node_labels)} Labels, {len(master_schema.relationship_types)} Relaciones.")

    # ==========================================================
    # PASE 2: EXTRACTION (Genera Datos y Cypher)
    # ==========================================================
    print("\n" + "#"*60)
    print("FASE 2: EXTRACCIÓN Y GENERACIÓN DE CÓDIGO")
    print("#"*60)
    
    full_cypher_script = []
    
    # [cite: 60, 66] - Optimización: Constraints de Unicidad
    full_cypher_script.append("// --- CONSTRAINTS DE UNICIDAD (Optimización) ---")
    for label in master_schema.node_labels:
        full_cypher_script.append(f"CREATE CONSTRAINT constraint_{label}_id IF NOT EXISTS FOR (n:{label}) REQUIRE n.id IS UNIQUE;")
    # Constraint para el grafo léxico
    full_cypher_script.append("CREATE CONSTRAINT constraint_Documento_id IF NOT EXISTS FOR (d:Documento) REQUIRE d.id IS UNIQUE;")

    for filename, content in txt_files.items():
        print(f"\n--- ⛏️ Procesando archivo: {filename} ---")
        
        # 1. Extracción (Usando el Esquema Maestro)
        data, t2 = run_extraction_agent(content, master_schema)
        total_t2 += t2
        
        # 2. Acumular Tripletas para visualización abstracta
        for rel in data.relationships:
            global_schema_triplets.add((rel.source_label, rel.relationship, rel.target_label))

        # 3. Generar fragmento Cypher
        fragment = generate_cypher_fragment(data, filename)
        full_cypher_script.append(fragment)

    # ==========================================================
    # RESULTADOS FINALES
    # ==========================================================

    # 1. IMPRESIÓN DEL ESQUEMA ABSTRACTO
    print("\n" + "="*60)
    print("📢 ESQUEMA ABSTRACTO DESCUBIERTO (TIPO --RELACIÓN--> TIPO)")
    print("="*60)
    if global_schema_triplets:
        for s, r, t in sorted(list(global_schema_triplets)):
            print(f"({s}) --[{r}]--> ({t})")
    else:
        print("(No se detectaron relaciones)")

    # 2. IMPRESIÓN DEL SCRIPT CYPHER
    final_script = "\n".join(full_cypher_script)
    
    # Opcional: Guardar en archivo
    with open("grafo_generado.cypher", "w", encoding="utf-8") as f:
        f.write(final_script)
        
    print("\n" + "="*60)
    print("💻 SCRIPT CYPHER FINAL (Primeras 20 líneas)")
    print("="*60)
    print("\n".join(final_script.split("\n")[:20]))
    print("...\n(Ver archivo completo 'grafo_generado.cypher')")
    print("="*60)
    
    # 3. Reporte Tokens
    print(f"\n💰 CONSUMO TOTAL: {total_t1 + total_t2} Tokens (Ontólogo: {total_t1} | Extractor: {total_t2})")

if __name__ == "__main__":
    main()