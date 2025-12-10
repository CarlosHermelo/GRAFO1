import os
import json
import sys
from typing import Dict
from dotenv import load_dotenv
from openai import OpenAI
from neo4j import GraphDatabase

# Configurar codificación UTF-8 para Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Intentar importar biblioteca de PDF
try:
    import pdfplumber
    PDF_SUPPORT = True
except ImportError:
    try:
        from PyPDF2 import PdfReader
        PDF_SUPPORT = True
    except ImportError:
        PDF_SUPPORT = False

# Cargar variables de entorno
load_dotenv()

# --- CONFIGURACIÓN ---
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4-turbo")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Nueva variable de entorno para el directorio de PDFs
PDF_DIR = os.getenv("PDF_DIR", "./import_data/pdf") 

# Configurar clientes
client = OpenAI(api_key=OPENAI_API_KEY)
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

# ==============================================================================
# 0. UTILIDADES DE ARCHIVO Y TEXTO (Sin cambios)
# ==============================================================================
def get_document_id(filename: str) -> str:
    """Extrae el ID limpio del nombre del archivo (sin extensión)."""
    return os.path.basename(filename).rsplit('.', 1)[0]

def read_file_content(file_path: str) -> str:
    """Lee el contenido de un archivo, soportando TXT y PDF."""
    file_path = os.path.normpath(file_path)

    if file_path.lower().endswith('.pdf'):
        if not PDF_SUPPORT:
            raise Exception("No hay soporte para PDF instalado. Instala 'pdfplumber' o 'PyPDF2'.")
        try:
            # Preferencia por pdfplumber
            import pdfplumber
            text = ""
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            return text
        except:
            # Fallback a PyPDF2
            from PyPDF2 import PdfReader
            reader = PdfReader(file_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text
    else:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()

# [Otras funciones (create_extraction_prompt, extract_graph_data, ensure_root_node_exists, ingest_data_to_neo4j) se mantienen sin cambios]

# ==============================================================================
# 1. GENERACIÓN DE PROMPT CON CONTEXTO DEL NODO RAÍZ (Sin cambios)
# ==============================================================================
def create_extraction_prompt(text_chunk: str, schema: Dict, root_node_id: str) -> str:
    """
    Construye un prompt que instruye al LLM sobre el esquema Y sobre el documento padre.
    """

    # 1. Formatear Entidades y Relaciones del Esquema
    entities_str = ""
    for ent in schema.get("entities", []):
        props = ", ".join([f"{p['name']} ({p['type']})" for p in ent.get("properties", [])])
        entities_str += f"- TIPO: {ent['label']}\n  Descripción: {ent['description']}\n  PROPIEDADES A EXTRAER: {props}\n\n"

    rels_str = ""
    for rel in schema.get("relationships", []):
        props = ", ".join([f"{p['name']} ({p['type']})" for p in rel.get("properties", [])])
        props_text = f" (Propiedades: {props})" if props else ""
        rels_str += f"- {rel['type']}: De {rel['from_entity']} -> {rel['to_entity']}{props_text}\n"

    # 2. PROMPT REFORZADO CON EL NODO PROTAGONISTA
    prompt = f"""
Eres un arquitecto de Grafos de Conocimiento especializado en normativa.
Tu tarea es analizar el texto y extraer relaciones, pero SIEMPRE teniendo en cuenta el DOCUMENTO ORIGEN.

--- DOCUMENTO PROTAGONISTA (NODO RAÍZ) ---
ID DEL DOCUMENTO ACTUAL: "{root_node_id}"
TIPO DE NODO: Normativa
ESTADO: Vigente

IMPORTANTE: El texto que vas a leer pertenece a este documento ("{root_node_id}").
1. Si el texto menciona una Ley o Resolución anterior, crea una relación [:CITA] desde "{root_node_id}" hacia la norma citada.
2. Si el texto establece una Prestación, crea una relación [:REGULA] desde "{root_node_id}" hacia la Prestación.
3. NO crees relaciones flotantes. Usa "{root_node_id}" como el origen de la acción normativa.

--- ESQUEMA DE EXTRACCIÓN ---
ENTIDADES DISPONIBLES:
{entities_str}

RELACIONES DISPONIBLES:
{rels_str}

--- TEXTO A ANALIZAR ---
"{text_chunk}"
-------------------------

FORMATO DE SALIDA:
Genera un JSON válido con esta estructura:
{{
  "nodes": [
    {{
      "label": "TipoDeEntidad",
      "id": "identificador_unico",
      "properties": {{
        "propiedad1": "valor",
        "propiedad2": "valor"
      }}
    }}
  ],
  "relationships": [
    {{
      "type": "TIPO_RELACION",
      "source_id": "id_del_nodo_origen",
      "target_id": "id_del_nodo_destino",
      "properties": {{
        "propiedad": "valor"
      }}
    }}
  ]
}}

Asegúrate de incluir "{root_node_id}" en las relaciones como source_id cuando corresponda.
"""
    return prompt

# ==============================================================================
# 2. PROCESAMIENTO CON LLM (Sin cambios)
# ==============================================================================
def extract_graph_data(text: str, schema: Dict, root_node_id: str) -> tuple[Dict, Dict]:
    """Envía el texto al LLM con el contexto del documento padre. Retorna (resultado, usage_stats)"""

    prompt = create_extraction_prompt(text, schema, root_node_id)

    try:
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": "Eres un extractor de datos preciso. Responde solo en JSON válido."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0
        )
        result = json.loads(response.choices[0].message.content)

        # Obtener estadísticas de uso de tokens
        usage_stats = {
            "prompt_tokens": response.usage.prompt_tokens,
            "completion_tokens": response.usage.completion_tokens,
            "total_tokens": response.usage.total_tokens
        }

        return result, usage_stats
    except Exception as e:
        print(f"❌ Error en LLM: {e}")
        return {"nodes": [], "relationships": []}, {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}

# ==============================================================================
# 3. INGESTA EN NEO4J (Dynamic Cypher) (Sin cambios)
# ==============================================================================
def ensure_root_node_exists(session, doc_id: str, cypher_log_file):
    """
    Crea explícitamente el nodo del documento antes de procesar su contenido.
    """
    cypher_root = """
    MERGE (n:Normativa {id: $id})
    SET n.codigo = $id,
        n.tipo_norma = 'Resolución',
        n.estado = 'Vigente',
        n.fecha_ingesta = date()
    """

    if cypher_log_file:
        cypher_log_file.write(f"\n// CREACIÓN FORZADA DEL NODO RAÍZ\n")
        cypher_log_file.write(f"{cypher_root}\n// Params: id='{doc_id}'\n")

    try:
        session.run(cypher_root, id=doc_id)
    except Exception as e:
        print(f"   ❌ Error creando nodo raíz: {e}")

def ingest_data_to_neo4j(session, data: Dict, cypher_log_file=None):
    """Inserta los datos extraídos y retorna contadores."""
    nodes_created = 0
    relationships_created = 0

    if not data.get("nodes"):
        return nodes_created, relationships_created

    # 1. Insertar Nodos (Entidades extraídas)
    for node in data["nodes"]:
        if "label" not in node and "tipo" not in node:
            continue
        if "id" not in node:
            continue

        label = node.get("label") or node.get("tipo")
        node_id = node["id"]

        if "properties" in node:
            properties = node.get("properties", {})
        else:
            properties = {k: v for k, v in node.items() if k not in ["label", "tipo", "id"]}

        clean_props = {k: v for k, v in properties.items() if v is not None}
        clean_props["id"] = node_id

        cypher_node = f"MERGE (n:`{label}` {{id: $id}}) SET n += $props"

        if cypher_log_file:
            cypher_log_file.write(f"\n// NODO: {label} ({node_id})\n")
            cypher_log_file.write(f"{cypher_node}\n// Params: {clean_props}\n")

        try:
            session.run(cypher_node, id=node_id, props=clean_props)
            nodes_created += 1
        except Exception as e:
            print(f"   ❌ Error nodo {node_id}: {e}")

    # 2. Insertar Relaciones
    for rel in data.get("relationships", []):
        rel_type = rel["type"]
        source_id = rel["source_id"]
        target_id = rel["target_id"]
        properties = rel.get("properties", {})
        clean_props = {k: v for k, v in properties.items() if v is not None}

        cypher_rel = f"""
        MATCH (a), (b)
        WHERE a.id = $source_id AND b.id = $target_id
        MERGE (a)-[r:`{rel_type}`]->(b)
        SET r += $props
        """

        if cypher_log_file:
            cypher_log_file.write(f"// REL: ({source_id})-[{rel_type}]->({target_id})\n")
            cypher_log_file.write(f"{cypher_rel}\n// Params: {clean_props}\n")

        try:
            session.run(cypher_rel, source_id=source_id, target_id=target_id, props=clean_props)
            relationships_created += 1
        except Exception as e:
            print(f"   ❌ Error relación {rel_type}: {e}")

    return nodes_created, relationships_created

# ==============================================================================
# MAIN (MODIFICADO PARA USAR PDF_DIR)
# ==============================================================================
def main():
    print("--- 🏗️ INICIANDO GENE BUILDER (MODO PDF_DIR) ---")

    if not os.path.exists("builder_config.json"):
        print("❌ Falta 'builder_config.json'.")
        return

    with open("builder_config.json", "r", encoding="utf-8") as f:
        config = json.load(f)

    llm_schema = config.get("llm_schema", {})

    # ESCANEAR DIRECTORIO PDF_DIR
    files_to_process = []

    if os.path.exists(PDF_DIR): # <-- Usamos la nueva variable global PDF_DIR
        for filename in os.listdir(PDF_DIR):
            # Mantenemos todas las extensiones por si hay TXT en esa carpeta, 
            # pero el enfoque es en la carpeta de PDFs.
            if filename.lower().endswith(('.pdf', '.txt', '.md')): 
                file_path = os.path.join(PDF_DIR, filename)
                files_to_process.append(file_path)
        print(f"📁 Escaneando directorio: {PDF_DIR}")
        print(f"📄 Archivos encontrados: {len(files_to_process)}")
    else:
        print(f"❌ Directorio no encontrado: {PDF_DIR}. Asegúrate de que exista y que la variable PDF_DIR esté configurada.")
        return

    if not files_to_process:
        print("❌ No se encontraron archivos para procesar.")
        return

    cypher_log_path = "cypher_queries_log.cypher"

    # Contadores globales
    total_prompt_tokens = 0
    total_completion_tokens = 0
    total_tokens = 0
    total_nodes = 0
    total_relationships = 0
    file_stats = []

    with driver.session() as session:
        with open(cypher_log_path, "w", encoding="utf-8") as cypher_log:

            for file_path in files_to_process:
                file_name = os.path.basename(file_path)
                print(f"\n📂 Procesando: {file_name}")

                # Contadores por archivo (inicialización)
                file_prompt_tokens = 0
                file_completion_tokens = 0
                file_total_tokens = 0
                file_nodes = 0
                file_relationships = 0

                # --- PASO 1: DETERMINAR ID Y CREAR NODO RAÍZ ---
                doc_id = get_document_id(file_path)
                ensure_root_node_exists(session, doc_id, cypher_log)

                # --- PASO 2: LEER Y CHUNKING ---
                try:
                    content = read_file_content(file_path)
                    chunk_size = 15000
                    chunks = [content[i:i+chunk_size] for i in range(0, len(content), chunk_size)]

                    for i, chunk in enumerate(chunks):
                        # --- PASO 3: EXTRAER CON CONTEXTO DEL NODO RAÍZ ---
                        extracted_data, usage_stats = extract_graph_data(chunk, llm_schema, doc_id)

                        # Acumular tokens del fragmento
                        file_prompt_tokens += usage_stats["prompt_tokens"]
                        file_completion_tokens += usage_stats["completion_tokens"]
                        file_total_tokens += usage_stats["total_tokens"]

                        # --- PASO 4: INGESTAR RESULTADOS ---
                        nodes, rels = ingest_data_to_neo4j(session, extracted_data, cypher_log)
                        file_nodes += nodes
                        file_relationships += rels

                    # Resumen por archivo
                    print(f"   ✅ Completado - Nodos: {file_nodes} | Relaciones: {file_relationships} | Tokens: {file_total_tokens:,}")

                    # Guardar estadísticas
                    file_stats.append({
                        "file": file_name,
                        "chars": len(content),
                        "chunks": len(chunks),
                        "nodes": file_nodes,
                        "rels": file_relationships,
                        "tokens": file_total_tokens
                    })

                    # Acumular al total global
                    total_prompt_tokens += file_prompt_tokens
                    total_completion_tokens += file_completion_tokens
                    total_tokens += file_total_tokens
                    total_nodes += file_nodes
                    total_relationships += file_relationships

                except Exception as e:
                    print(f"   ❌ Error procesando el archivo: {e}")

    # REPORTE FINAL
    print("\n" + "="*70)
    print("✅ PROCESO COMPLETADO")
    print("="*70)
    print(f"📄 Queries Cypher guardadas en: {cypher_log_path}")
    print(f"\n📊 RESUMEN GENERAL:")
    print(f"   • Archivos procesados: {len(file_stats)}")
    print(f"   • Total Nodos creados: {total_nodes:,}")
    print(f"   • Total Relaciones creadas: {total_relationships:,}")
    print(f"   • Total Tokens Input: {total_prompt_tokens:,}")
    print(f"   • Total Tokens Output: {total_completion_tokens:,}")
    print(f"   • 🔥 TOTAL TOKENS: {total_tokens:,}")

    # Tabla de archivos
    if file_stats:
        print(f"\n📋 DETALLE POR ARCHIVO:")
        print(f"{'Archivo':<40} {'Nodos':>8} {'Rels':>8} {'Tokens':>12}")
        print("-" * 72)
        for stat in file_stats:
            print(f"{stat['file']:<40} {stat['nodes']:>8} {stat['rels']:>8} {stat['tokens']:>12,}")

    print("="*70)
    driver.close()

if __name__ == "__main__":
    main()