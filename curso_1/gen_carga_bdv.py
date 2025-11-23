import os
import glob
import chromadb
from typing import List
from dotenv import load_dotenv

# Librerías de LangChain para facilitar el split y el embedding
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
from chromadb.errors import NotFoundError
# --- 1. CONFIGURACIÓN E INICIALIZACIÓN ---
load_dotenv()

# Verificación de variables de entorno
CARPETA_TXT = os.getenv("CARPETA_TXT")
PATH_BDV = os.getenv("BDV")
NOMBRE_COLECCION = os.getenv("FILE_BDV")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not all([CARPETA_TXT, PATH_BDV, NOMBRE_COLECCION, OPENAI_API_KEY]):
    raise ValueError("❌ Faltan variables de entorno. Revisa CARPETA_TXT, BDV, FILE_BDV y OPENAI_API_KEY en tu .env")

print(f"🔵 Configuración detectada:")
print(f"   - Origen TXT: {CARPETA_TXT}")
print(f"   - Destino BDV: {PATH_BDV}")
print(f"   - Colección: {NOMBRE_COLECCION}")

# --- 2. LIMPIEZA DE LA BASE DE DATOS (RESET) ---
print("\n🧹 Iniciando limpieza de la colección anterior...")

# Usamos el cliente nativo de Chroma para gestionar la eliminación
client = chromadb.PersistentClient(path=PATH_BDV)



try:
    client.delete_collection(name=NOMBRE_COLECCION)
    print(f"   ✅ Colección '{NOMBRE_COLECCION}' eliminada correctamente.")
except (ValueError, NotFoundError):
    print(f"   ℹ️ La colección '{NOMBRE_COLECCION}' no existía, se creará una nueva.")
# --- 3. CARGA Y SPLIT DE DOCUMENTOS ---
def cargar_documentos(folder_path: str) -> List[Document]:
    docs = []
    search_path = os.path.join(folder_path, "*.txt")
    files = glob.glob(search_path)
    
    print(f"\n📂 Procesando archivos en: {folder_path}")
    
    for file_path in files:
        try:
            # Intentamos UTF-8
            loader = TextLoader(file_path, encoding='utf-8')
            docs.extend(loader.load())
            print(f"   Running: {os.path.basename(file_path)}")
        except Exception:
            try:
                # Fallback a Latin-1 si falla UTF-8 (común en español legacy)
                loader = TextLoader(file_path, encoding='latin-1')
                docs.extend(loader.load())
                print(f"   Running (latin-1): {os.path.basename(file_path)}")
            except Exception as e:
                print(f"   ❌ Error cargando {os.path.basename(file_path)}: {e}")
    
    return docs

raw_documents = cargar_documentos(CARPETA_TXT)

if not raw_documents:
    print("⚠️ No se encontraron documentos para procesar. Finalizando.")
    exit()

# Dividir el texto en Chunks
# chunk_size=1000 y overlap=200 son estándares buenos para RAG
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,
    separators=["\n\n", "\n", " ", ""]
)

chunks = text_splitter.split_documents(raw_documents)
print(f"\n🧩 Documentos divididos en {len(chunks)} chunks.")

# --- 4. INGESTA EN CHROMA DB ---
print("\n🚀 Iniciando generación de Embeddings e Inserción en BDV...")

# Inicializamos el modelo de Embeddings (usa OPENAI_API_KEY por defecto)
embedding_function = OpenAIEmbeddings(model="text-embedding-3-small")

# Creamos/Conectamos a la BD a través de LangChain
# Nota: LangChain gestionará la creación de la colección usando el cliente persistente
vector_store = Chroma.from_documents(
    documents=chunks,
    embedding=embedding_function,
    client=client, # Usamos el mismo cliente que configuramos arriba
    collection_name=NOMBRE_COLECCION,
    collection_metadata={"hnsw:space": "cosine"} # Opcional: define métrica de distancia
)

print(f"\n✅ ¡ÉXITO! Base de datos actualizada en: {PATH_BDV}")
print(f"   Colección: {NOMBRE_COLECCION}")
print(f"   Total registros insertados: {len(chunks)}")