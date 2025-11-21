import os
import json
from neo4j import GraphDatabase
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from dotenv import load_dotenv

# Cargar variables de entorno desde archivo .env
load_dotenv()

# === CONFIGURACIÓN ===
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY no está configurada en las variables de entorno.")
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
if not NEO4J_PASSWORD:
    raise ValueError("NEO4J_PASSWORD no está configurada en las variables de entorno.")

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

# Inicializar embeddings y splitter
embedding_model = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
splitter = RecursiveCharacterTextSplitter(chunk_size=512, chunk_overlap=64)

# Funciones para carga de datos
def insert_record(tx, rec):
    tx.run(
        "MERGE (s:Servicio {nombre: $serv})",
        serv=rec["SERVICIO"]
    )
    tx.run(
        "MERGE (st:Subtipo {id_sub: $id_sub, nombre: $subtipo})",
        id_sub=rec["ID_SUB"],
        subtipo=rec["SUBTIPO"]
    )
    tx.run(
        """
        MATCH (s:Servicio {nombre: $serv}), (st:Subtipo {id_sub: $id_sub})
        MERGE (s)-[:OFRECE]->(st)
        """,
        serv=rec["SERVICIO"],
        id_sub=rec["ID_SUB"]
    )
    tx.run(
        """
        CREATE (d:Tramite {
            id_sub: $id_sub,
            tipo: $tipo,
            copete: $copete,
            consiste: $consiste,
            quien_puede: $quien_puede,
            requisitos: $requisitos,
            pautas: $pautas,
            quienes_pueden: $quienes_pueden,
            como_lo_hacen: $como_lo_hacen
        })
        """,
        id_sub=rec["ID_SUB"],
        tipo=rec["TIPO"],
        copete=rec.get("COPETE"),
        consiste=rec.get("CONSISTE"),
        quien_puede=rec.get("QUIEN_PUEDE"),
        requisitos=rec.get("REQUISITOS"),
        pautas=rec.get("PAUTAS"),
        quienes_pueden=rec.get("QUIENES_PUEDEN"),
        como_lo_hacen=rec.get("COMO_LO_HACEN")
    )
    tx.run(
        """
        MATCH (st:Subtipo {id_sub: $id_sub}), (d:Tramite {id_sub: $id_sub})
        MERGE (st)-[:TIENE]->(d)
        """,
        id_sub=rec["ID_SUB"]
    )

def add_embedding_property(tx, id_sub, embedding_vector):
    tx.run(
        """
        MATCH (d:Tramite {id_sub: $id_sub})
        SET d.embedding = $vec
        """,
        id_sub=id_sub,
        vec=embedding_vector
    )

def create_vector_index(tx, label="Tramite", prop="embedding", dimensions=1536):
    tx.run(
        f"""
        CREATE VECTOR INDEX idx_{label}_{prop}
        FOR (n:{label})
        ON (n.{prop})
        OPTIONS {{ indexConfig: {{ `vector.dimensions`: {dimensions}, `vector.similarity_function`: 'cosine' }} }}
        """
    )

# Cargar JSON
with open("datos.json", encoding="utf-8") as f:
    data = json.load(f)

with driver.session() as session:
    # Inserción de todos los registros
    for rec in data["RECORDS"]:
        session.execute_write(insert_record, rec)

    # Generación de embeddings y actualización de nodos
    for rec in data["RECORDS"]:
        id_sub = rec["ID_SUB"]
        text = (rec.get("CONSISTE","") + "\n" + rec.get("PAUTAS","")).strip()
        if not text:
            continue
        chunks = splitter.split_text(text)
        first_chunk = chunks[0]
        vec = embedding_model.embed_documents([first_chunk])[0]
        session.execute_write(add_embedding_property, id_sub, vec)

    # Crear índice vectorial
    session.execute_write(create_vector_index)

driver.close()
