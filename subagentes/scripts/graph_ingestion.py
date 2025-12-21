"""
Graph Knowledge Ingestion Pipeline
Generado automáticamente por el Agente de Ingesta
Versión: 1.0
Fecha: 2024-12-17
Schema Version: 1.0

Este script extrae, normaliza, valida y carga datos desde PDFs/TXTs hacia Neo4j
siguiendo el schema diseñado y el objetivo validado del grafo de conocimiento.
"""

import os
import json
import sys
import uuid
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Tuple
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI
from neo4j import GraphDatabase

# Importar parsers locales
from objetivo_parser import parse_objetivo, format_objetivo_for_prompt
from schema_parser import parse_schema, format_schema_for_prompt, get_node_by_label

# Configurar codificación UTF-8 para Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Importaciones opcionales para PDF
try:
    import pdfplumber
    PDF_SUPPORT = "pdfplumber"
except ImportError:
    try:
        from PyPDF2 import PdfReader
        PDF_SUPPORT = "PyPDF2"
    except ImportError:
        PDF_SUPPORT = None
        print("⚠️ No se encontró soporte para PDF. Instala 'pdfplumber' o 'PyPDF2'")

# Para normalización
try:
    from dateutil import parser as date_parser
    DATE_SUPPORT = True
except ImportError:
    DATE_SUPPORT = False
    print("⚠️ No se encontró python-dateutil para normalización de fechas")

# ============================================================================
# 0. LOGGER DUAL (CONSOLA + ARCHIVO)
# ============================================================================

class DualLogger:
    """Logger que escribe tanto a consola como a archivo"""
    def __init__(self, log_file="status.log"):
        self.log_file = log_file
        self.file_handle = open(log_file, 'w', encoding='utf-8')

    def print(self, message=""):
        """Imprime mensaje en consola y archivo"""
        print(message)
        self.file_handle.write(str(message) + "\n")
        self.file_handle.flush()

    def close(self):
        """Cierra el archivo de log"""
        self.file_handle.close()

# Instanciar logger global
logger = None

# ============================================================================
# 1. CONFIGURACIÓN
# ============================================================================

load_dotenv()

# Variables de entorno
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")

# Variables para directorios de archivos
TXT_DIR = os.getenv("TXT_DIR", "../fuente/txt")
PDF_DIR = os.getenv("PDF_DIR", "../fuente/pdf")
TIPO_TEXTO = os.getenv("TIPO_TEXTO", "PDF")  # "PDF" o "TXT"

# Determinar directorio según tipo
if TIPO_TEXTO.upper() == "TXT":
    TEXT_DIR = TXT_DIR
else:
    TEXT_DIR = PDF_DIR

OUTPUT_DIR = os.getenv("OUTPUT_DIR", "../resultados")
LOG_DIR = os.getenv("LOG_DIR", "../logs")

# Validar configuración
if not all([NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD, OPENAI_API_KEY]):
    print("❌ Error: Faltan variables de entorno. Verifica tu archivo .env")
    sys.exit(1)

# Inicializar clientes
openai_client = OpenAI(api_key=OPENAI_API_KEY)

# Validar conexión a Neo4j ANTES de continuar
print("\n>>> Validando conexión a Neo4j...")
try:
    neo4j_driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    with neo4j_driver.session() as session:
        result = session.run("RETURN 1 AS test")
        result.single()
    print("[OK] Conexión a Neo4j exitosa")
except Exception as e:
    print("\n" + "="*70)
    print("[ERROR] NO SE PUDO CONECTAR A NEO4J")
    print("="*70)
    print(f"\nError: {str(e)}\n")
    print("Posibles causas:")
    print("  1. Neo4j no está corriendo")
    print("     Solución: Inicia Neo4j Desktop o el servicio neo4j")
    print("")
    print("  2. URI incorrecta en .env")
    print(f"     URI actual: {NEO4J_URI}")
    print("     Verifica que sea correcta (ej: bolt://localhost:7687 o neo4j://localhost:7687)")
    print("")
    print("  3. Credenciales incorrectas")
    print(f"     Usuario actual: {NEO4J_USER}")
    print("     Verifica NEO4J_PASSWORD en el archivo .env")
    print("")
    print("  4. Firewall o red bloqueando la conexión")
    print("     Verifica que el puerto 7687 esté abierto")
    print("")
    print("="*70)
    sys.exit(1)

# Cargar objetivo y schema
OBJETIVO_INFO = parse_objetivo("../resultados/objetivo_validado.md")
SCHEMA_INFO = parse_schema("../resultados/schema_diseñado.md")

# Nota: La configuración se imprime en main() usando el logger

# ============================================================================
# 1.5. FUNCIONES DE INICIALIZACIÓN DE NEO4J
# ============================================================================

def start_neo4j():
    """Intenta iniciar Neo4j si no está corriendo"""
    global logger
    logger.print("\n🔧 Intentando iniciar Neo4j...")

    try:
        # Intentar iniciar Neo4j Desktop (si está instalado)
        # Esto varía según la instalación
        if sys.platform == 'win32':
            # En Windows, intentar iniciar el servicio
            result = subprocess.run(
                ['net', 'start', 'neo4j'],
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0:
                logger.print("   ✅ Servicio Neo4j iniciado correctamente")
                return True
            else:
                logger.print(f"   ⚠️ No se pudo iniciar automáticamente: {result.stderr}")
                logger.print("   💡 Por favor, inicia Neo4j Desktop manualmente")
                return False
        else:
            # En Linux/Mac
            result = subprocess.run(
                ['sudo', 'systemctl', 'start', 'neo4j'],
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0:
                logger.print("   ✅ Servicio Neo4j iniciado correctamente")
                return True
            else:
                logger.print(f"   ⚠️ No se pudo iniciar automáticamente")
                logger.print("   💡 Por favor, inicia Neo4j manualmente")
                return False
    except Exception as e:
        logger.print(f"   ⚠️ Error al intentar iniciar Neo4j: {e}")
        logger.print("   💡 Por favor, inicia Neo4j Desktop manualmente")
        return False

# ============================================================================
# 2. UTILIDADES - LECTURA DE ARCHIVOS
# ============================================================================

def get_document_id(filename: str) -> str:
    """Extrae el ID limpio del nombre del archivo (sin extensión)"""
    return os.path.basename(filename).rsplit('.', 1)[0]


def read_pdf(file_path: str) -> str:
    """
    Lee contenido de PDF usando la biblioteca disponible

    Args:
        file_path: Ruta al archivo PDF

    Returns:
        Texto extraído del PDF
    """
    if PDF_SUPPORT == "pdfplumber":
        import pdfplumber
        text = ""
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        return text

    elif PDF_SUPPORT == "PyPDF2":
        from PyPDF2 import PdfReader
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text

    else:
        raise Exception("No hay soporte para PDF instalado")


def read_file_content(file_path: str) -> str:
    """
    Lee el contenido de un archivo (PDF o TXT)

    Args:
        file_path: Ruta al archivo

    Returns:
        Contenido del archivo como string
    """
    file_path = os.path.normpath(file_path)

    if file_path.lower().endswith('.pdf'):
        return read_pdf(file_path)
    else:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()


# ============================================================================
# 2. UTILIDADES - NORMALIZACIÓN
# ============================================================================

def normalize_fecha(fecha_str: str) -> str:
    """
    Normaliza fechas a formato ISO 8601 (YYYY-MM-DD)

    Args:
        fecha_str: Fecha en cualquier formato

    Returns:
        Fecha en formato ISO 8601 o None si no se puede parsear
    """
    if not DATE_SUPPORT or not fecha_str:
        return fecha_str

    try:
        # dateutil.parser es muy flexible
        dt = date_parser.parse(fecha_str, dayfirst=True)
        return dt.strftime("%Y-%m-%d")
    except:
        return fecha_str  # Retornar original si falla


def normalize_string(text: str) -> str:
    """
    Normaliza strings: lowercase, sin tildes

    Args:
        text: Texto a normalizar

    Returns:
        Texto normalizado
    """
    if not text:
        return text

    import unicodedata
    # Remover tildes
    nfkd = unicodedata.normalize('NFKD', text)
    text_sin_tildes = "".join([c for c in nfkd if not unicodedata.combining(c)])
    return text_sin_tildes.lower().strip()


def normalize_numero_ley(numero: str) -> str:
    """
    Normaliza números de ley al formato argentino estándar
    Ej: 19549 → 19.549

    Args:
        numero: Número de ley

    Returns:
        Número normalizado
    """
    if not numero:
        return numero

    # Remover puntos existentes
    numero_clean = numero.replace(".", "").replace(" ", "")

    # Si es un número de 5 dígitos, agregar punto
    if numero_clean.isdigit() and len(numero_clean) == 5:
        return f"{numero_clean[:2]}.{numero_clean[2:]}"

    return numero


def normalize_node_data(node_data: Dict, schema_node: Dict) -> Dict:
    """
    Normaliza los datos de un nodo según el schema

    Args:
        node_data: Datos del nodo a normalizar
        schema_node: Definición del nodo en el schema

    Returns:
        Datos normalizados
    """
    normalized = {}

    for prop in schema_node.get("propiedades", []):
        prop_name = prop["nombre"]
        prop_type = prop["tipo"]

        if prop_name in node_data:
            value = node_data[prop_name]

            # Normalizar según tipo
            if prop_type == "Date" and isinstance(value, str):
                normalized[prop_name] = normalize_fecha(value)
            elif prop_type == "String" and isinstance(value, str):
                # Mantener original + versión normalizada
                normalized[prop_name] = value
                if prop_name in ["nombre", "titulo"]:
                    normalized[f"{prop_name}_normalized"] = normalize_string(value)
            else:
                normalized[prop_name] = value

    # Copiar propiedades que no están en el schema
    for key, value in node_data.items():
        if key not in normalized:
            normalized[key] = value

    return normalized


# ============================================================================
# 2. UTILIDADES - VALIDACIÓN
# ============================================================================

def validate_node(node_data: Dict, schema_node: Dict) -> List[str]:
    """
    Valida un nodo contra el schema

    Args:
        node_data: Datos del nodo
        schema_node: Definición del nodo en el schema

    Returns:
        Lista de errores (vacía si es válido)
    """
    errores = []

    # 1. Validar propiedades obligatorias
    for prop in schema_node.get("propiedades", []):
        if prop.get("obligatoria", False):
            if prop["nombre"] not in node_data or not node_data[prop["nombre"]]:
                errores.append(
                    f"Propiedad obligatoria faltante: {prop['nombre']}"
                )

    # 2. Validar valores permitidos (enumeraciones)
    for prop in schema_node.get("propiedades", []):
        if "valores" in prop:
            prop_value = node_data.get(prop["nombre"])
            if prop_value and prop_value not in prop["valores"]:
                errores.append(
                    f"{prop['nombre']} debe ser uno de {prop['valores']}, "
                    f"recibido: {prop_value}"
                )

    # 3. Validar regla de identidad (clave compuesta)
    for id_prop in schema_node.get("identidad", []):
        if id_prop not in node_data or not node_data[id_prop]:
            errores.append(
                f"Propiedad de identidad faltante: {id_prop}"
            )

    return errores


# ============================================================================
# 3. EXTRACCIÓN (LLM) - CON OBJETIVO EN PROMPTS
# ============================================================================

def create_extraction_prompt(
    text_chunk: str,
    schema_info: Dict,
    objetivo_info: Dict,
    doc_id: str
) -> str:
    """
    Genera prompt dinámico basado en schema Y OBJETIVO

    Args:
        text_chunk: Fragmento de texto a analizar
        schema_info: Schema parseado
        objetivo_info: Objetivo parseado
        doc_id: ID del documento actual

    Returns:
        Prompt completo para el LLM
    """
    # Formatear objetivo y schema
    objetivo_section = format_objetivo_for_prompt(objetivo_info)
    schema_section = format_schema_for_prompt(schema_info)

    prompt = f"""
Eres un extractor de información para grafos de conocimiento.

{objetivo_section}

==========================================
CONTEXTO DE EXTRACCIÓN:
==========================================

DOCUMENTO ACTUAL:
- ID: "{doc_id}"
- Tipo: Normativa
- El texto que leerás pertenece a este documento

{schema_section}

==========================================
TEXTO A ANALIZAR:
==========================================
\"\"\"{text_chunk[:10000]}\"\"\"

==========================================
INSTRUCCIONES DE EXTRACCIÓN:
==========================================

1. Extrae TODAS las entidades mencionadas en el texto que coincidan con el schema
2. Extrae TODAS las relaciones entre entidades
3. **PRIORIZA** las entidades y relaciones que son relevantes para el OBJETIVO del grafo
4. Para cada entidad extraída:
   - Completa TODAS las propiedades obligatorias
   - Genera un ID único y semántico basado en la clave de identidad
   - Incluye el fragmento de texto de donde se extrajo (evidencia)
   - Asigna un score de confianza (0.0-1.0) según qué tan claro está en el texto
5. Para el documento raíz ("{doc_id}"), crea relaciones hacia las entidades que menciona
6. Si detectas información relevante para detectar inconsistencias, márcalo

==========================================
FORMATO DE SALIDA (JSON):
==========================================
{{
  "nodo_raiz": {{
    "label": "Normativa",
    "id": "{doc_id}",
    "propiedades": {{
      "tipo": "Resolución",
      "numero": "...",
      "anio": 2024,
      "emisor": "...",
      "fecha_emision": "YYYY-MM-DD",
      "estado": "Vigente",
      "schema_version": "1.0"
    }},
    "evidencia": {{
      "page": 1,
      "text_fragment": "fragmento literal (máx 200 chars)",
      "confidence_score": 0.95
    }}
  }},
  "entidades_extraidas": [
    {{
      "label": "Articulo",
      "id": "id_semantico",
      "propiedades": {{}},
      "evidencia": {{
        "page": 5,
        "paragraph_id": "p5-3",
        "text_fragment": "...",
        "confidence_score": 0.92
      }}
    }}
  ],
  "relaciones": [
    {{
      "type": "CONTIENE",
      "source_id": "{doc_id}",
      "target_id": "id_destino",
      "properties": {{}}
    }}
  ],
  "inconsistencias_potenciales": [
    {{
      "tipo": "Faltante | Superposición | Mal Definida",
      "descripcion": "...",
      "severidad": "Crítica | Alta | Media | Baja",
      "entidad_afectada_id": "id"
    }}
  ]
}}

IMPORTANTE:
- Usa los valores exactos permitidos en enumeraciones
- Las fechas deben estar en formato ISO 8601 (YYYY-MM-DD)
- Los IDs deben ser únicos y semánticos
- Siempre incluye el score de confianza (0.0-1.0)
- Si encuentras información ambigua, indica menor confianza
"""
    return prompt


def extract_with_llm(
    text: str,
    schema_info: Dict,
    objetivo_info: Dict,
    doc_id: str,
    extraction_log_file=None
) -> Tuple[Dict, Dict]:
    """
    Extrae datos usando LLM con objetivo en context

    Args:
        text: Texto a analizar
        schema_info: Schema parseado
        objetivo_info: Objetivo parseado
        doc_id: ID del documento
        extraction_log_file: Archivo de log de extracciones

    Returns:
        Tupla (datos_extraidos, estadisticas_tokens)
    """
    global logger
    prompt = create_extraction_prompt(text, schema_info, objetivo_info, doc_id)

    try:
        response = openai_client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        f"Eres un extractor de información experto para grafos "
                        f"de conocimiento. Tu objetivo es: "
                        f"{objetivo_info['objetivo'][:200]}..."
                    )
                },
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0
        )

        result = json.loads(response.choices[0].message.content)

        # Estadísticas de tokens
        usage_stats = {
            "prompt_tokens": response.usage.prompt_tokens,
            "completion_tokens": response.usage.completion_tokens,
            "total_tokens": response.usage.total_tokens
        }

        # Log de extracción
        if extraction_log_file:
            extraction_log_file.write(f"\n{'='*80}\n")
            extraction_log_file.write(f"EXTRACCIÓN - Documento: {doc_id}\n")
            extraction_log_file.write(f"Timestamp: {datetime.now().isoformat()}\n")
            extraction_log_file.write(f"Tokens: {usage_stats['total_tokens']}\n")
            extraction_log_file.write(f"{'='*80}\n\n")

            # Log del resultado JSON
            extraction_log_file.write("DATOS EXTRAÍDOS (JSON):\n")
            extraction_log_file.write(json.dumps(result, indent=2, ensure_ascii=False))
            extraction_log_file.write("\n\n")

            # Log de los comandos Cypher si están presentes
            extraction_log_file.write("REGISTROS EXTRAÍDOS:\n")
            extraction_log_file.write(f"- Nodo raíz: {result.get('nodo_raiz', {}).get('label', 'N/A')} ({result.get('nodo_raiz', {}).get('id', 'N/A')})\n")
            extraction_log_file.write(f"- Entidades: {len(result.get('entidades_extraidas', []))}\n")
            for i, ent in enumerate(result.get('entidades_extraidas', []), 1):
                extraction_log_file.write(f"  {i}. {ent.get('label', 'N/A')} ({ent.get('id', 'N/A')})\n")
            extraction_log_file.write(f"- Relaciones: {len(result.get('relaciones', []))}\n")
            for i, rel in enumerate(result.get('relaciones', []), 1):
                extraction_log_file.write(f"  {i}. ({rel.get('source_id', 'N/A')})-[{rel.get('type', 'N/A')}]->({rel.get('target_id', 'N/A')})\n")
            extraction_log_file.write(f"- Inconsistencias potenciales: {len(result.get('inconsistencias_potenciales', []))}\n")
            extraction_log_file.write("\n")
            extraction_log_file.flush()

        return result, usage_stats

    except Exception as e:
        if logger:
            logger.print(f"   ❌ Error en LLM: {e}")
        else:
            print(f"   ❌ Error en LLM: {e}")
        return {
            "nodo_raiz": {},
            "entidades_extraidas": [],
            "relaciones": [],
            "inconsistencias_potenciales": []
        }, {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0
        }


# ============================================================================
# 4. TRANSFORMACIÓN (Normalización + Validación + Estructuración)
# ============================================================================

def transform_extracted_data(
    raw_data: Dict,
    schema_info: Dict,
    source_metadata: Dict
) -> Dict:
    """
    Normaliza, valida y estructura datos extraídos

    Args:
        raw_data: Datos crudos del LLM
        schema_info: Schema parseado
        source_metadata: Metadatos del documento fuente

    Returns:
        Datos transformados y validados
    """
    transformed = {
        "metadata": {
            "doc_id": source_metadata["doc_id"],
            "source_type": source_metadata["source_type"],
            "source_path": source_metadata["source_path"],
            "extraction_date": datetime.now().isoformat(),
            "extractor_version": "graph_ingestion_v1.0",
            "schema_version": "1.0",
            "objetivo": OBJETIVO_INFO["objetivo"][:200]
        },
        "nodo_raiz": {},
        "entidades_extraidas": [],
        "relaciones": [],
        "inconsistencias_potenciales": [],
        "errores_validacion": []
    }

    # Procesar nodo raíz
    if "nodo_raiz" in raw_data and raw_data["nodo_raiz"]:
        nodo_raiz = raw_data["nodo_raiz"]
        label = nodo_raiz.get("label", "Normativa")
        schema_node = get_node_by_label(schema_info, label)

        if schema_node:
            # Normalizar
            propiedades_norm = normalize_node_data(
                nodo_raiz.get("propiedades", {}),
                schema_node
            )

            # Agregar propiedades de sistema
            propiedades_norm["schema_version"] = "1.0"
            propiedades_norm["created_at"] = datetime.now().isoformat()
            propiedades_norm["updated_at"] = datetime.now().isoformat()

            # Validar
            errores = validate_node(propiedades_norm, schema_node)

            transformed["nodo_raiz"] = {
                "label": label,
                "id": nodo_raiz.get("id"),
                "propiedades": propiedades_norm,
                "evidencia": {
                    **nodo_raiz.get("evidencia", {}),
                    "doc_id": source_metadata["doc_id"],
                    "source_type": source_metadata["source_type"],
                    "source_path": source_metadata["source_path"]
                },
                "validacion": {
                    "valido": len(errores) == 0,
                    "errores": errores
                }
            }

            if errores:
                transformed["errores_validacion"].append({
                    "nodo_id": nodo_raiz.get("id"),
                    "errores": errores
                })

    # Procesar entidades extraídas
    for entidad in raw_data.get("entidades_extraidas", []):
        label = entidad.get("label")
        schema_node = get_node_by_label(schema_info, label)

        if schema_node:
            # Normalizar
            propiedades_norm = normalize_node_data(
                entidad.get("propiedades", {}),
                schema_node
            )

            # Agregar propiedades de sistema
            propiedades_norm["schema_version"] = "1.0"
            propiedades_norm["created_at"] = datetime.now().isoformat()
            propiedades_norm["updated_at"] = datetime.now().isoformat()

            # Validar
            errores = validate_node(propiedades_norm, schema_node)

            transformed["entidades_extraidas"].append({
                "label": label,
                "id": entidad.get("id"),
                "propiedades": propiedades_norm,
                "evidencia": {
                    **entidad.get("evidencia", {}),
                    "doc_id": source_metadata["doc_id"],
                    "source_type": source_metadata["source_type"],
                    "source_path": source_metadata["source_path"]
                },
                "validacion": {
                    "valido": len(errores) == 0,
                    "errores": errores
                }
            })

            if errores:
                transformed["errores_validacion"].append({
                    "nodo_id": entidad.get("id"),
                    "errores": errores
                })

    # Copiar relaciones
    transformed["relaciones"] = raw_data.get("relaciones", [])

    # Copiar inconsistencias potenciales
    transformed["inconsistencias_potenciales"] = raw_data.get(
        "inconsistencias_potenciales",
        []
    )

    return transformed


# ============================================================================
# 5. CARGA (Neo4j)
# ============================================================================

def create_constraints_and_indexes(session, schema_info: Dict):
    """
    Crea constraints e índices basados en schema

    Args:
        session: Sesión de Neo4j
        schema_info: Schema parseado
    """
    global logger

    for nodo in schema_info["nodos"]:
        label = nodo["label"]
        identidad = nodo.get("identidad", [])

        if identidad:
            # Crear constraint de unicidad
            props_str = ", ".join([f"n.{prop}" for prop in identidad])
            constraint_name = f"unique_{label.lower()}"

            cypher = f"""
            CREATE CONSTRAINT {constraint_name} IF NOT EXISTS
            FOR (n:{label})
            REQUIRE ({props_str}) IS UNIQUE
            """

            try:
                session.run(cypher)
                if logger:
                    logger.print(f"   ✅ Constraint: {label} ({', '.join(identidad)})")
            except Exception as e:
                if logger:
                    logger.print(f"   ⚠️ Constraint {label}: {e}")

        # Crear índices en propiedades indexadas
        for prop in nodo.get("propiedades", []):
            # Crear índice si la propiedad es de búsqueda común
            if prop["nombre"] in ["nombre", "titulo", "descripcion", "estado"]:
                index_cypher = f"""
                CREATE INDEX IF NOT EXISTS
                FOR (n:{label})
                ON (n.{prop["nombre"]})
                """

                try:
                    session.run(index_cypher)
                    if logger:
                        logger.print(f"   ✅ Índice: {label}.{prop['nombre']}")
                except Exception as e:
                    if logger:
                        logger.print(f"   ⚠️ Índice {label}.{prop['nombre']}: {e}")


def insert_node_with_evidence(
    session,
    node_data: Dict,
    cypher_log_file
) -> Tuple[bool, str]:
    """
    Inserta un nodo y su evidencia, creando la relación RESPALDA

    Args:
        session: Sesión de Neo4j
        node_data: Datos del nodo
        cypher_log_file: Archivo de log de Cypher

    Returns:
        Tupla (éxito, mensaje)
    """
    global logger

    if not node_data or "validacion" in node_data and not node_data["validacion"]["valido"]:
        return False, "Validación falló"

    label = node_data["label"]
    node_id = node_data["id"]
    props = node_data["propiedades"]
    evidencia = node_data.get("evidencia", {})

    # 1. Insertar nodo principal
    cypher_node = f"""
    MERGE (n:`{label}` {{id: $id}})
    SET n += $props
    """

    try:
        session.run(cypher_node, id=node_id, props=props)

        # 2. Crear nodo de evidencia si existe
        if evidencia and evidencia.get("text_fragment"):
            evid_id = f"EVID-{uuid.uuid4().hex[:12]}"
            evidencia_props = {
                "id": evid_id,
                "doc_id": evidencia.get("doc_id", ""),
                "source_type": evidencia.get("source_type", "pdf"),
                "source_path": evidencia.get("source_path", ""),
                "page": evidencia.get("page"),
                "text_fragment": evidencia.get("text_fragment", "")[:500],
                "extraction_date": datetime.now().isoformat(),
                "confidence_score": evidencia.get("confidence_score", 0.0),
                "schema_version": "1.0"
            }

            cypher_evidencia = """
            MERGE (e:Evidencia {id: $evid_id})
            SET e += $evid_props

            WITH e
            MATCH (n) WHERE n.id = $node_id
            MERGE (n)-[:RESPALDA]->(e)
            """

            session.run(
                cypher_evidencia,
                evid_id=evid_id,
                evid_props=evidencia_props,
                node_id=node_id
            )

            if cypher_log_file:
                cypher_log_file.write(
                    f"\n// NODO + EVIDENCIA: {label} ({node_id})\n"
                )
                cypher_log_file.write(f"{cypher_node}\n")
                cypher_log_file.write(f"{cypher_evidencia}\n")

        return True, f"✅ {label} ({node_id})"

    except Exception as e:
        error_msg = f"❌ Error insertando nodo {node_id}: {e}"
        if logger:
            logger.print(f"   {error_msg}")
        else:
            print(f"   {error_msg}")
        return False, error_msg


def insert_relationships(
    session,
    relationships: List[Dict],
    cypher_log_file
) -> int:
    """
    Inserta relaciones

    Args:
        session: Sesión de Neo4j
        relationships: Lista de relaciones
        cypher_log_file: Archivo de log

    Returns:
        Número de relaciones insertadas
    """
    count = 0

    for rel in relationships:
        rel_type = rel.get("type")
        source_id = rel.get("source_id")
        target_id = rel.get("target_id")
        properties = rel.get("properties", {})

        if not all([rel_type, source_id, target_id]):
            continue

        cypher_rel = f"""
        MATCH (a), (b)
        WHERE a.id = $source_id AND b.id = $target_id
        MERGE (a)-[r:`{rel_type}`]->(b)
        SET r += $props
        """

        try:
            session.run(
                cypher_rel,
                source_id=source_id,
                target_id=target_id,
                props=properties
            )
            count += 1

            if cypher_log_file:
                cypher_log_file.write(
                    f"// REL: ({source_id})-[{rel_type}]->({target_id})\n"
                )
                cypher_log_file.write(f"{cypher_rel}\n")

        except Exception as e:
            print(f"   ❌ Error relación {rel_type}: {e}")

    return count


# ============================================================================
# 6. MAIN (Pipeline Orquestado)
# ============================================================================

def main():
    global logger

    # Inicializar logger
    logger = DualLogger("status.log")

    logger.print("="*80)
    logger.print("🚀 PIPELINE DE INGESTA DE GRAFOS DE CONOCIMIENTO")
    logger.print("="*80)
    logger.print(f"\n🎯 OBJETIVO: {OBJETIVO_INFO['objetivo'][:100]}...")
    logger.print(f"📊 DOMINIO: {OBJETIVO_INFO['dominio']}")
    logger.print(f"📐 SCHEMA: {len(SCHEMA_INFO['nodos'])} nodos, {len(SCHEMA_INFO['relaciones'])} relaciones")
    logger.print(f"📄 TIPO DE ARCHIVO: {TIPO_TEXTO}")

    # Preguntar si quiere iniciar Neo4j
    logger.print("\n" + "="*80)
    respuesta = input("¿Desea iniciar la base de datos de grafos Neo4j? (s/n): ").strip().lower()
    logger.print(f"¿Desea iniciar la base de datos de grafos Neo4j? (s/n): {respuesta}")
    logger.print("="*80)

    if respuesta == 's':
        start_neo4j()
        # Esperar un poco para que Neo4j se inicie
        import time
        logger.print("   ⏳ Esperando 10 segundos para que Neo4j se inicie...")
        time.sleep(10)

    # Crear directorio de salida
    os.makedirs("output", exist_ok=True)

    # 1. Preparar Neo4j (constraints + índices)
    logger.print("\n📐 Preparando Neo4j (constraints e índices)...")
    try:
        with neo4j_driver.session() as session:
            create_constraints_and_indexes(session, SCHEMA_INFO)
    except Exception as e:
        logger.print(f"❌ Error al preparar Neo4j: {e}")
        logger.print("💡 Asegúrate de que Neo4j esté corriendo e intenta de nuevo")
        logger.close()
        return

    # 2. Escanear archivos en TEXT_DIR
    logger.print(f"\n>>> Directorio de archivos: {TEXT_DIR}")

    if not os.path.exists(TEXT_DIR):
        logger.print(f"[ERROR] El directorio {TEXT_DIR} no existe")
        logger.print(f"Por favor, crea el directorio y coloca los archivos a procesar")
        logger.print(f"\nDirectorios configurados:")
        logger.print(f"  TXT_DIR: {TXT_DIR}")
        logger.print(f"  PDF_DIR: {PDF_DIR}")
        logger.print(f"  TIPO_TEXTO actual: {TIPO_TEXTO}")
        logger.close()
        return

    # Buscar archivos según el tipo configurado
    archivos = []
    if TIPO_TEXTO.upper() == "TXT":
        archivos = list(Path(TEXT_DIR).glob("*.txt"))
        extension = "TXT"
    else:
        archivos = list(Path(TEXT_DIR).glob("*.pdf"))
        extension = "PDF"

    # Convertir a strings
    archivos = [str(f) for f in archivos]

    logger.print(f">>> Archivos {extension} encontrados en {TEXT_DIR}:")
    if archivos:
        for i, archivo in enumerate(archivos, 1):
            logger.print(f"  {i}. {os.path.basename(archivo)}")
    else:
        logger.print(f"  [ADVERTENCIA] No se encontraron archivos {extension}")
        logger.print(f"  Coloca archivos {extension} en: {TEXT_DIR}")
        logger.print(f"\nPara cambiar el tipo de archivo, modifica TIPO_TEXTO en .env:")
        logger.print(f"  TIPO_TEXTO=PDF  (para archivos PDF)")
        logger.print(f"  TIPO_TEXTO=TXT  (para archivos TXT)")
        logger.close()
        return

    logger.print(f"\n>>> Total de archivos a procesar: {len(archivos)}\n")

    # Estadísticas globales
    total_tokens = 0
    total_nodes = 0
    total_rels = 0
    total_nodes_loaded = 0
    total_rels_loaded = 0

    # Archivos de log
    cypher_log_path = "output/cypher_queries_log.cypher"
    extraction_log_path = "output/extraction_log.txt"

    # 3. Procesar cada archivo
    with open(cypher_log_path, "w", encoding="utf-8") as cypher_log, \
         open(extraction_log_path, "w", encoding="utf-8") as extraction_log:

        cypher_log.write("// QUERIES CYPHER GENERADAS\n")
        cypher_log.write(f"// Fecha: {datetime.now().isoformat()}\n\n")

        extraction_log.write("LOG DE EXTRACCIONES DEL LLM\n")
        extraction_log.write(f"Fecha: {datetime.now().isoformat()}\n")
        extraction_log.write("="*80 + "\n\n")

        for archivo in archivos:
            filename = os.path.basename(archivo)
            logger.print(f"\n{'='*80}")
            logger.print(f"📄 Procesando archivo: {filename}")
            logger.print("="*80)

            doc_id = get_document_id(archivo)

            # 3.1. Leer contenido
            try:
                content = read_file_content(archivo)
                logger.print(f"   📝 Contenido total: {len(content):,} caracteres")

                # Chunking si es muy largo
                chunk_size = 15000
                chunks = [
                    content[i:i+chunk_size]
                    for i in range(0, len(content), chunk_size)
                ]
                logger.print(f"   📦 Total de chunks: {len(chunks)}")

                source_metadata = {
                    "doc_id": doc_id,
                    "source_type": "pdf" if archivo.endswith('.pdf') else "txt",
                    "source_path": archivo
                }

                file_nodes = 0
                file_rels = 0
                file_tokens = 0
                file_nodes_loaded = 0
                file_rels_loaded = 0

                for i, chunk in enumerate(chunks):
                    chunk_num = i + 1
                    chunk_size_chars = len(chunk)

                    logger.print(f"\n   {'─'*70}")
                    logger.print(f"   📦 Chunk {chunk_num}/{len(chunks)}")
                    logger.print(f"   📏 Tamaño del chunk: {chunk_size_chars:,} caracteres")
                    logger.print(f"   {'─'*70}")

                    # 3.2. Extraer con LLM (CON OBJETIVO)
                    raw_data, usage_stats = extract_with_llm(
                        chunk,
                        SCHEMA_INFO,
                        OBJETIVO_INFO,
                        doc_id,
                        extraction_log
                    )

                    file_tokens += usage_stats["total_tokens"]

                    # 3.3. Transformar (Normalizar + Validar + Estructurar)
                    transformed_data = transform_extracted_data(
                        raw_data,
                        SCHEMA_INFO,
                        source_metadata
                    )

                    # Contar registros generados por este chunk
                    chunk_nodes_count = 0
                    chunk_rels_count = len(transformed_data.get("relaciones", []))

                    if i == 0 and transformed_data.get("nodo_raiz"):
                        chunk_nodes_count += 1

                    chunk_nodes_count += len(transformed_data.get("entidades_extraidas", []))

                    logger.print(f"   📊 Registros generados en este chunk:")
                    logger.print(f"      - Nodos: {chunk_nodes_count}")
                    logger.print(f"      - Relaciones: {chunk_rels_count}")

                    # 3.4. Guardar JSON intermedio
                    json_output_path = f"output/{doc_id}_chunk_{i}.json"
                    with open(json_output_path, "w", encoding="utf-8") as f:
                        json.dump(transformed_data, f, indent=2, ensure_ascii=False)

                    # 3.5. Cargar a Neo4j
                    chunk_loaded_nodes = 0
                    chunk_loaded_rels = 0

                    logger.print(f"   💾 Cargando a Neo4j...")

                    with neo4j_driver.session() as session:
                        # Insertar nodo raíz (solo en el primer chunk)
                        if i == 0 and transformed_data.get("nodo_raiz"):
                            success, msg = insert_node_with_evidence(
                                session,
                                transformed_data["nodo_raiz"],
                                cypher_log
                            )
                            if success:
                                chunk_loaded_nodes += 1
                                logger.print(f"      {msg}")

                        # Insertar entidades
                        for entity in transformed_data["entidades_extraidas"]:
                            success, msg = insert_node_with_evidence(
                                session,
                                entity,
                                cypher_log
                            )
                            if success:
                                chunk_loaded_nodes += 1
                                # Solo imprimir el primer y último para no saturar
                                if chunk_loaded_nodes == 1 or chunk_loaded_nodes == len(transformed_data["entidades_extraidas"]):
                                    logger.print(f"      {msg}")

                        # Insertar relaciones
                        rels_inserted = insert_relationships(
                            session,
                            transformed_data["relaciones"],
                            cypher_log
                        )
                        chunk_loaded_rels = rels_inserted

                    file_nodes += chunk_nodes_count
                    file_rels += chunk_rels_count
                    file_nodes_loaded += chunk_loaded_nodes
                    file_rels_loaded += chunk_loaded_rels

                    # Resumen de carga para este chunk
                    if chunk_loaded_nodes > 0 or chunk_loaded_rels > 0:
                        logger.print(f"   ✅ Carga exitosa:")
                        logger.print(f"      - Nodos cargados: {chunk_loaded_nodes}/{chunk_nodes_count}")
                        logger.print(f"      - Relaciones cargadas: {chunk_loaded_rels}/{chunk_rels_count}")
                    else:
                        logger.print(f"   ⚠️  No se cargaron registros en Neo4j")

                # Resumen del archivo
                logger.print(f"\n   {'='*70}")
                logger.print(f"   ✅ Archivo completado: {filename}")
                logger.print(f"   {'='*70}")
                logger.print(f"   📊 Estadísticas del archivo:")
                logger.print(f"      - Total nodos generados: {file_nodes}")
                logger.print(f"      - Total nodos cargados: {file_nodes_loaded}")
                logger.print(f"      - Total relaciones generadas: {file_rels}")
                logger.print(f"      - Total relaciones cargadas: {file_rels_loaded}")
                logger.print(f"      - Total tokens usados: {file_tokens:,}")
                logger.print(f"   {'='*70}")

                total_nodes += file_nodes
                total_rels += file_rels
                total_tokens += file_tokens
                total_nodes_loaded += file_nodes_loaded
                total_rels_loaded += file_rels_loaded

            except Exception as e:
                logger.print(f"   ❌ Error procesando archivo: {e}")
                import traceback
                logger.print(traceback.format_exc())

    # 4. Reporte final
    logger.print("\n" + "="*80)
    logger.print("✅ PIPELINE COMPLETADO")
    logger.print("="*80)
    logger.print(f"📄 Archivos procesados: {len(archivos)}")
    logger.print(f"\n📊 Estadísticas totales:")
    logger.print(f"   - Total Nodos generados: {total_nodes:,}")
    logger.print(f"   - Total Nodos CARGADOS en Neo4j: {total_nodes_loaded:,}")
    logger.print(f"   - Total Relaciones generadas: {total_rels:,}")
    logger.print(f"   - Total Relaciones CARGADAS en Neo4j: {total_rels_loaded:,}")
    logger.print(f"   - Total Tokens usados: {total_tokens:,}")
    logger.print(f"\n📁 Archivos generados:")
    logger.print(f"   - Log de estado: status.log")
    logger.print(f"   - Log de extracciones: {extraction_log_path}")
    logger.print(f"   - Log Cypher: {cypher_log_path}")
    logger.print(f"   - JSONs intermedios: output/*_chunk_*.json")
    logger.print("="*80)

    if total_nodes_loaded > 0:
        logger.print(f"\n✅ SE CARGARON {total_nodes_loaded} NODOS Y {total_rels_loaded} RELACIONES EN NEO4J")
    else:
        logger.print(f"\n⚠️  NO SE CARGARON REGISTROS EN NEO4J")

    logger.print("\n🎉 ¡Proceso finalizado!")

    neo4j_driver.close()
    logger.close()


if __name__ == "__main__":
    main()
