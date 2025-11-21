import os
from dotenv import load_dotenv
from neo4j import GraphDatabase
from openai import OpenAI

from langchain_openai import ChatOpenAI
from langchain_experimental.graph_transformers import LLMGraphTransformer

# ==========================================================
# Cargar .env
# ==========================================================
load_dotenv()

# ==========================================================
# Configurar OpenAI
# ==========================================================
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY no está configurada")

client = OpenAI(api_key=OPENAI_API_KEY)

# LLM para extracción de tripletas
llm = ChatOpenAI(
    model="gpt-4o-mini",
    openai_api_key=OPENAI_API_KEY,
    temperature=0
)

transformer = LLMGraphTransformer(llm=llm)

# ==========================================================
# Configurar Neo4j
# ==========================================================
uri = os.getenv("NEO4J_URI")
user = os.getenv("NEO4J_USER")
password = os.getenv("NEO4J_PASSWORD")

if not uri or not user or not password:
    raise ValueError("Variables NEO4J_URI / NEO4J_USER / NEO4J_PASSWORD no configuradas")

driver = GraphDatabase.driver(uri, auth=(user, password))

print("→ Conectado a OpenAI y Neo4j usando .env")

# ==========================================================
# Cargar texto desde archivo
# ==========================================================
archivo = "resolucion_2526.txt"

with open(archivo, encoding="utf-8") as f:
    texto = f.read()

print(f"→ Archivo cargado: {archivo}")

# ==========================================================
# Extraer tripletas con LLM
# ==========================================================
print("→ Extrayendo tripletas...")

graph_docs = transformer.convert_to_graph_documents([texto])

# LangChain devuelve GraphDocuments con .nodes y .relationships
nodos = graph_docs[0].nodes
rels = graph_docs[0].relationships

print("Nodos detectados:", len(nodos))
print("Relaciones detectadas:", len(rels))

# Mostrar tripletas detectadas
print("\nTripletas encontradas:")
for r in rels:
    print(f"({r.source.id}) -[{r.type}]-> ({r.target.id})")

# ==========================================================
# Cargar tripletas en Neo4j
# ==========================================================
print("\n→ Insertando en Neo4j...")

with driver.session() as session:
    # Crear nodos
    for n in nodos:
        session.run(
            """
            MERGE (a:Entidad {id: $id})
            SET a += $props
            """,
            id=n.id,
            props=n.properties,
        )

    # Crear relaciones
    for r in rels:
        session.run(
            f"""
            MATCH (a:Entidad {{id: $source}})
            MATCH (b:Entidad {{id: $ta
