import os
import sys
import json
import logging
from typing import List, Dict, Any
from dotenv import load_dotenv
from neo4j import GraphDatabase
from openai import OpenAI
from rapidfuzz import fuzz

# Cargar variables de entorno
load_dotenv()

# Configuración de Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class KnowledgeGraphBuilder:
    def __init__(self, mode="execute"):
        self.mode = mode

        # Configuración desde .env
        self.llm_model = os.getenv("LLM_MODEL", "gpt-4-turbo")
        # Para Neo4j Aura, necesitamos una URL pública o cargar datos de forma diferente
        self.csv_base_url = os.getenv("CSV_BASE_URL", "https://raw.githubusercontent.com/user/repo/main/data")
        self.use_local_import = os.getenv("USE_LOCAL_IMPORT", "true").lower() == "true"
        
        # Cliente OpenAI (necesario para la fase 'execute' de texto)
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        # Configuración según el modo
        if self.mode == "execute":
            uri = os.getenv("NEO4J_URI")
            user = os.getenv("NEO4J_USER")
            password = os.getenv("NEO4J_PASSWORD")
            
            if not uri or not password:
                raise ValueError("❌ Faltan credenciales de NEO4J en el archivo .env")
                
            self.driver = GraphDatabase.driver(uri, auth=(user, password))
            logging.info(f"🔌 Conectado a Neo4j ({uri}) en modo EXECUTE.")
            
        elif self.mode == "generate_cypher":
            self.cypher_buffer = [] # Buffer para guardar las consultas
            logging.info("📝 Iniciando en modo GENERATE_CYPHER (No se conecta a la BD).")

    def close(self):
        if hasattr(self, 'driver') and self.driver:
            self.driver.close()

    def run_query(self, query, parameters=None):
        """Ejecuta en BD o escribe en buffer, según el modo."""
        if self.mode == "execute":
            try:
                with self.driver.session() as session:
                    result = session.run(query, parameters or {})
                    return [record.data() for record in result]
            except Exception as e:
                logging.error(f"Error ejecutando Cypher: {e}")
                return []
        else:
            # En modo generación, debemos interpolar los parámetros para que el texto sea válido
            # Nota: Esta es una interpolación simple para visualización/copiado.
            clean_query = query.strip()
            if parameters:
                # Agregamos los parámetros como comentario para referencia
                clean_query = f"/* Params: {json.dumps(parameters)} */\n" + clean_query
            
            self.cypher_buffer.append(clean_query + ";\n")
            return []

    def write_cypher_file(self, filename="import_dominio.cypher"):
        """Vuelca el buffer a un archivo."""
        if self.mode == "generate_cypher" and self.cypher_buffer:
            with open(filename, "w", encoding='utf-8') as f:
                f.writelines(self.cypher_buffer)
            logging.info(f"✅ Archivo generado: {filename}")
            logging.info("👉 Copia y pega el contenido en Neo4j Browser.")

    # =========================================================================
    # FASE 1: DOMINIO (CSV) -> Compatible con 'generate_cypher'
    # =========================================================================
    
    def _get_file_url(self, source_file: str) -> str:
        """Determina la URL final del CSV (Google Drive o Base URL)."""
        if source_file.startswith("http"):
            return source_file # Es una URL completa (ej. Google Drive)
        else:
            # Es un nombre de archivo, concatenar con la base
            # Eliminar barra final de base y inicial de archivo para evitar dobles
            base = self.csv_base_url.rstrip("/")
            name = source_file.lstrip("/")
            return f"{base}/{name}"

    def load_nodes_from_csv(self, config: Dict):
        # 1. Constraint (Importante para rendimiento y unicidad)
        constraint_query = f"CREATE CONSTRAINT IF NOT EXISTS FOR (n:{config['label']}) REQUIRE n.{config['unique_column_name']} IS UNIQUE"
        self.run_query(constraint_query)

        # 2. Verificar si debemos usar importación local o desde URL
        if self.use_local_import and self.mode == "execute":
            self._load_nodes_from_local_csv(config)
        else:
            # Usar LOAD CSV con URL
            url = self._get_file_url(config['source_file'])
            query = f"""
            LOAD CSV WITH HEADERS FROM '{url}' AS row
            CALL {{
                WITH row
                MERGE (n:{config['label']} {{ {config['unique_column_name']}: row.{config['unique_column_name']} }})
                SET n += row
            }} IN TRANSACTIONS OF 1000 ROWS
            """
            logging.info(f"Fase 1: Preparando Nodos -> {config['label']}")
            self.run_query(query)

    def _load_nodes_from_local_csv(self, config: Dict):
        """Carga nodos desde CSV local usando pandas y transacciones directas."""
        import pandas as pd

        source_file = config['source_file']
        # Buscar el archivo en los directorios conocidos
        csv_dir = os.getenv("CSV_DIR", "./import_data/csv")
        file_path = os.path.join(csv_dir, source_file)

        if not os.path.exists(file_path):
            logging.error(f"Archivo CSV no encontrado: {file_path}")
            return

        logging.info(f"Fase 1: Cargando Nodos desde archivo local -> {config['label']} ({source_file})")

        try:
            df = pd.read_csv(file_path)
            label = config['label']
            unique_col = config['unique_column_name']

            # Procesar en lotes
            batch_size = 1000
            total_rows = len(df)

            for i in range(0, total_rows, batch_size):
                batch = df.iloc[i:i+batch_size]

                for _, row in batch.iterrows():
                    # Convertir la fila a diccionario y limpiar valores NaN
                    row_dict = {k: (v if pd.notna(v) else None) for k, v in row.to_dict().items()}

                    # Crear query parametrizada
                    query = f"""
                    MERGE (n:{label} {{{unique_col}: $unique_value}})
                    SET n += $properties
                    """

                    params = {
                        'unique_value': row_dict[unique_col],
                        'properties': row_dict
                    }

                    self.run_query(query, params)

                if (i + batch_size) % 1000 == 0 or (i + batch_size) >= total_rows:
                    logging.info(f"  Procesadas {min(i + batch_size, total_rows)}/{total_rows} filas...")

            logging.info(f"  ✅ Completado: {total_rows} nodos de tipo {label}")

        except Exception as e:
            logging.error(f"Error cargando nodos desde {file_path}: {e}")

    def load_relationships_from_csv(self, config: Dict):
        # Verificar si debemos usar importación local o desde URL
        if self.use_local_import and self.mode == "execute":
            self._load_relationships_from_local_csv(config)
        else:
            url = self._get_file_url(config['source_file'])
            query = f"""
            LOAD CSV WITH HEADERS FROM '{url}' AS row
            CALL {{
                WITH row
                MATCH (source:{config['from_node_label']} {{ {config['from_node_column']}: row.{config['from_node_column']} }})
                MATCH (target:{config['to_node_label']} {{ {config['to_node_column']}: row.{config['to_node_column']} }})
                MERGE (source)-[r:{config['relationship_type']}]->(target)
                SET r += row
            }} IN TRANSACTIONS OF 1000 ROWS
            """
            logging.info(f"Fase 1: Preparando Relación -> {config['relationship_type']}")
            self.run_query(query)

    def _load_relationships_from_local_csv(self, config: Dict):
        """Carga relaciones desde CSV local usando pandas y transacciones directas."""
        import pandas as pd

        source_file = config['source_file']
        csv_dir = os.getenv("CSV_DIR", "./import_data/csv")
        file_path = os.path.join(csv_dir, source_file)

        if not os.path.exists(file_path):
            logging.error(f"Archivo CSV no encontrado: {file_path}")
            return

        logging.info(f"Fase 1: Cargando Relaciones desde archivo local -> {config['relationship_type']} ({source_file})")

        try:
            df = pd.read_csv(file_path)
            rel_type = config['relationship_type']
            from_label = config['from_node_label']
            to_label = config['to_node_label']
            from_col = config['from_node_column']
            to_col = config['to_node_column']

            total_rows = len(df)
            success_count = 0

            for _, row in df.iterrows():
                row_dict = {k: (v if pd.notna(v) else None) for k, v in row.to_dict().items()}

                query = f"""
                MATCH (source:{from_label} {{{from_col}: $from_value}})
                MATCH (target:{to_label} {{{to_col}: $to_value}})
                MERGE (source)-[r:{rel_type}]->(target)
                SET r += $properties
                """

                params = {
                    'from_value': row_dict.get(from_col),
                    'to_value': row_dict.get(to_col),
                    'properties': row_dict
                }

                result = self.run_query(query, params)
                if result is not None:  # None indica error
                    success_count += 1

            logging.info(f"  ✅ Completado: {success_count}/{total_rows} relaciones de tipo {rel_type}")

        except Exception as e:
            logging.error(f"Error cargando relaciones desde {file_path}: {e}")

    # =========================================================================
    # FASE 2: TEXTO (LLM) -> Solo funciona en modo 'execute'
    # =========================================================================

    def extract_with_llm(self, chunk: str, schema: Dict) -> Dict:
        """Extrae entidades y relaciones del texto usando LLM."""
        # Extraer información del schema
        entities = schema.get('entities', [])
        relationships = schema.get('relationships', [])

        # Preparar la descripción de entidades
        entity_desc = []
        for ent in entities:
            entity_desc.append(f"- {ent.get('label')}: {ent.get('description', 'Sin descripción')}")

        # Preparar la descripción de relaciones
        rel_desc = []
        for rel in relationships:
            rel_desc.append(f"- {rel.get('type')}: {rel.get('from_entity')} -> {rel.get('to_entity')}")

        prompt = f"""
Eres un experto en extracción de información. Extrae entidades y relaciones del siguiente texto.

TEXTO A ANALIZAR:
{chunk[:2000]}

TIPOS DE ENTIDADES A EXTRAER:
{chr(10).join(entity_desc) if entity_desc else 'Sin restricciones'}

TIPOS DE RELACIONES A EXTRAER:
{chr(10).join(rel_desc) if rel_desc else 'Sin restricciones'}

IMPORTANTE:
Devuelve un objeto JSON con esta estructura exacta:
{{
  "nodes": [
    {{
      "label": "NombreEntidad",
      "id": "identificador_unico",
      "properties": {{
        "name": "nombre de la instancia",
        "description": "descripción breve"
      }}
    }}
  ],
  "relationships": [
    {{
      "type": "TIPO_RELACION",
      "from_id": "id_nodo_origen",
      "to_id": "id_nodo_destino"
    }}
  ]
}}

- Extrae solo entidades y relaciones que aparezcan explícitamente en el texto
- Usa los tipos de entidades y relaciones definidos arriba
- Cada nodo debe tener un ID único
"""

        try:
            response = self.client.chat.completions.create(
                model=self.llm_model,
                messages=[
                    {"role": "system", "content": "Eres un experto en extracción de información. Responde SOLO con JSON válido."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0
            )
            content = response.choices[0].message.content

            # Limpiar bloques de código markdown si existen
            import re
            json_match = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', content, re.DOTALL)
            if json_match:
                content = json_match.group(1).strip()

            return json.loads(content)
        except Exception as e:
            logging.error(f"Error OpenAI durante extracción: {e}")
            return {"nodes": [], "relationships": []}

    def process_text_files(self, file_paths: List[str], schema: Dict):
        if self.mode != "execute":
            logging.warning("⚠️ Saltando procesamiento de texto (Solo disponible en modo 'execute')")
            return

        for file_path in file_paths:
            logging.info(f"Fase 2: Procesando archivo -> {file_path}")
            
            if not os.path.exists(file_path):
                logging.error(f"Archivo no encontrado: {file_path}")
                continue

            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
                
            # Chunking simple por '---'
            chunks = [c.strip() for c in text.split('---') if c.strip()]
            
            for i, chunk in enumerate(chunks):
                data = self.extract_with_llm(chunk, schema)
                self.ingest_extraction(os.path.basename(file_path), i, chunk, data)

    def ingest_extraction(self, filename: str, idx: int, text: str, data: Dict):
        chunk_id = f"{filename}_chunk_{idx}"

        # Crear Chunk y Documento
        self.run_query("""
            MERGE (d:Document {name: $filename})
            MERGE (c:Chunk {id: $chunk_id})
            SET c.text = $text
            MERGE (d)-[:HAS_CHUNK]->(c)
        """, {"filename": filename, "chunk_id": chunk_id, "text": text})

        # Crear Entidades
        for node in data.get('nodes', []):
            label = node.get('label', 'Entity')
            props = node.get('properties', {})
            # Usar un ID temporal del LLM o crear uno
            node_id = node.get('id', str(hash(json.dumps(props, sort_keys=True))))

            # Sanitizar label para evitar inyecciones
            safe_label = ''.join(c for c in label if c.isalnum() or c == '_')
            if not safe_label:
                safe_label = 'Entity'

            # Crear query usando parámetros en lugar de interpolación de strings
            if props:
                query = f"""
                MERGE (n:__Entity__:{safe_label} {{id: $node_id}})
                SET n += $properties
                WITH n
                MATCH (c:Chunk {{id: $chunk_id}})
                MERGE (c)-[:MENTIONS]->(n)
                """
                params = {
                    'node_id': node_id,
                    'properties': props,
                    'chunk_id': chunk_id
                }
            else:
                # Si no hay propiedades, no intentamos hacer SET
                query = f"""
                MERGE (n:__Entity__:{safe_label} {{id: $node_id}})
                WITH n
                MATCH (c:Chunk {{id: $chunk_id}})
                MERGE (c)-[:MENTIONS]->(n)
                """
                params = {
                    'node_id': node_id,
                    'chunk_id': chunk_id
                }

            self.run_query(query, params)

        # Crear Relaciones extraídas
        for rel in data.get('relationships', []):
            rel_type = rel.get('type', 'RELATED_TO')
            from_id = rel.get('from_id')
            to_id = rel.get('to_id')

            if not from_id or not to_id:
                logging.warning(f"Relación sin IDs completos, saltando: {rel}")
                continue

            # Sanitizar tipo de relación
            safe_rel_type = ''.join(c for c in rel_type if c.isalnum() or c == '_').upper()
            if not safe_rel_type:
                safe_rel_type = 'RELATED_TO'

            query = f"""
            MATCH (from:__Entity__ {{id: $from_id}})
            MATCH (to:__Entity__ {{id: $to_id}})
            MERGE (from)-[r:{safe_rel_type}]->(to)
            """

            params = {
                'from_id': from_id,
                'to_id': to_id
            }

            self.run_query(query, params)

        logging.info(f"  ✅ Procesado chunk {idx} de {filename}: {len(data.get('nodes', []))} entidades, {len(data.get('relationships', []))} relaciones")

    # =========================================================================
    # FASE 3: RESOLUCIÓN -> Solo funciona en modo 'execute'
    # =========================================================================

    def run_entity_resolution(self, schema: Dict):
        if self.mode != "execute":
            return

        logging.info("Fase 3: Iniciando Resolución de Entidades...")

        # Extraer labels de las entidades del schema
        entities = schema.get('entities', [])
        labels = [ent.get('label') for ent in entities if ent.get('label')]

        if not labels:
            logging.warning("No hay entidades definidas en el schema para resolución")
            return
        
        for label in labels:
            # Lógica simplificada: Conectar por Nombre similar
            # Asume que ambos tienen una propiedad 'name' o similar. 
            # En producción, esto viene del 'construction_plan' también.
            
            query = f"""
            MATCH (e:__Entity__:{label})
            MATCH (d:{label}) WHERE NOT d:__Entity__
            // Aquí intentamos matchear propiedades comunes.
            // Para generalizar, usamos APOC para comparar todo el mapa de propiedades o una clave específica
            // Este ejemplo asume una coincidencia laxa en cualquier propiedad string
            WITH e, d
            WHERE any(prop in keys(e) WHERE e[prop] IS NOT NULL AND toString(d[prop]) IS NOT NULL 
                      AND apoc.text.jaroWinklerDistance(toString(e[prop]), toString(d[prop])) < 0.2)
            MERGE (e)-[r:CORRESPONDS_TO]->(d)
            SET r.score = 1.0
            """
            # Nota: Esta query es pesada. En prod, usa índices específicos.
            # Aquí solo mostramos la intención.
            self.run_query(query)

    # =========================================================================
    # MAIN PIPELINE
    # =========================================================================

    def run_pipeline_from_config(self, config_file="builder_config.json"):
        # 1. Leer Config
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
        except FileNotFoundError:
            logging.error("❌ No se encontró 'builder_config.json'. Ejecuta primero el arquitecto.")
            return

        domain_plan = config.get('domain_plan', {})
        llm_schema = config.get('llm_schema', {})
        txt_files = config.get('files_to_process', [])

        # --- FASE 1: CSV (Funciona en ambos modos) ---
        logging.info("--- 🚀 FASE 1: GRAFO DE DOMINIO ---")

        # Verificar estructura del domain_plan
        if isinstance(domain_plan, dict):
            # Caso 1: domain_plan tiene 'nodes' y 'relationships'
            if 'nodes' in domain_plan:
                logging.info("Procesando nodos del domain_plan...")
                for node_config in domain_plan.get('nodes', []):
                    try:
                        # Adaptar la estructura esperada
                        rule = {
                            'label': node_config.get('label'),
                            'source_file': node_config.get('source_file'),
                            'unique_column_name': node_config.get('key_columns', [])[0] if node_config.get('key_columns') else None
                        }
                        if rule['unique_column_name']:
                            self.load_nodes_from_csv(rule)
                    except Exception as e:
                        logging.error(f"Error procesando nodo {node_config.get('label')}: {e}")

                logging.info("Procesando relaciones del domain_plan...")
                for rel_config in domain_plan.get('relationships', []):
                    try:
                        # Adaptar la estructura esperada
                        rule = {
                            'relationship_type': rel_config.get('type'),
                            'from_node_label': rel_config.get('from_label'),
                            'to_node_label': rel_config.get('to_label'),
                            'source_file': rel_config.get('source_file'),
                            'from_node_column': rel_config.get('from_column'),
                            'to_node_column': rel_config.get('to_column')
                        }
                        if all([rule.get('relationship_type'), rule.get('from_node_label'), rule.get('to_node_label')]):
                            self.load_relationships_from_csv(rule)
                    except Exception as e:
                        logging.error(f"Error procesando relación {rel_config.get('type')}: {e}")

            # Caso 2: domain_plan tiene estructura antigua con 'construction_type'
            else:
                for key, rule in domain_plan.items():
                    try:
                        if isinstance(rule, dict):
                            if rule.get('construction_type') == 'node':
                                self.load_nodes_from_csv(rule)
                            elif rule.get('construction_type') == 'relationship':
                                self.load_relationships_from_csv(rule)
                    except Exception as e:
                        logging.error(f"Error procesando regla {key}: {e}")
        else:
            logging.warning("⚠️ domain_plan no tiene la estructura esperada")
        
        # Si es modo generar, guardamos y salimos
        if self.mode == "generate_cypher":
            self.write_cypher_file()
            logging.info("🛑 Fin de generación. Ejecuta el SQL en Neo4j y luego corre este script en modo 'execute'.")
            return

        # --- FASE 2: TXT (Solo Execute) ---
        logging.info("--- 🚀 FASE 2: GRAFO DE SUJETO (IA) ---")
        self.process_text_files(txt_files, llm_schema)

        # --- FASE 3: RESOLUCIÓN (Solo Execute) ---
        logging.info("--- 🚀 FASE 3: RESOLUCIÓN DE ENTIDADES ---")
        self.run_entity_resolution(llm_schema)

if __name__ == "__main__":
    # Detección de argumentos
    mode = "execute"
    if len(sys.argv) > 1 and sys.argv[1] == "generate_cypher":
        mode = "generate_cypher"
    
    kg = KnowledgeGraphBuilder(mode=mode)
    try:
        kg.run_pipeline_from_config()
        if mode == "execute":
            logging.info("🎉 ¡Grafo construido exitosamente!")
    except Exception as e:
        logging.error(f"Error crítico: {e}")
    finally:
        kg.close()