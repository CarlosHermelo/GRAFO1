#!/usr/bin/env python3
"""
Script de Construcción de Base de Datos Vectorial
Generado por: Agente Constructor de BD Vectoriales

Este script:
1. Analiza automáticamente el tipo de documentos (normativos, técnicos, análisis)
2. Selecciona estrategias óptimas de chunking según el tipo detectado
3. Genera embeddings usando OpenAI
4. Almacena todo en una base de datos vectorial (Chroma por defecto)
"""

import os
import sys
import json
from pathlib import Path
from typing import List, Dict, Tuple
from datetime import datetime
from dotenv import load_dotenv

try:
    from langchain_openai import OpenAIEmbeddings
    from langchain_community.vectorstores import Chroma
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    from langchain_community.document_loaders import PyPDFLoader, TextLoader
    from langchain.schema import Document
    from tqdm import tqdm
except ImportError as e:
    print(f"[ERROR] Falta instalar dependencias: {e}")
    print("\nInstala con:")
    print("  pip install langchain langchain-openai langchain-community chromadb pypdf python-dotenv tqdm")
    sys.exit(1)

# Cargar variables de entorno
load_dotenv()

# ============================================================================
# CONFIGURACIÓN
# ============================================================================

CONFIG = {
    'openai_api_key': os.getenv('OPENAI_API_KEY'),
    'embedding_model': os.getenv('EMBEDDING_MODEL', 'text-embedding-3-small'),
    'vector_db_type': os.getenv('VECTOR_DB_TYPE', 'chroma'),
    'vector_db_name': os.getenv('VECTOR_DB_NAME', 'mi_bdvectorial'),
    'vector_db_path': os.getenv('VECTOR_DB_PATH', './chroma_db/'),
    'source_path': os.getenv('SOURCE_PATH', 'contexto_dominio/'),
    'file_extensions': os.getenv('FILE_EXTENSIONS', '.pdf,.txt').split(','),
    'chunk_size': int(os.getenv('CHUNK_SIZE', '0')),  # 0 = auto-detect
    'chunk_overlap': int(os.getenv('CHUNK_OVERLAP', '0')),  # 0 = auto-detect
}

# Estrategias de chunking por tipo de documento
ESTRATEGIAS_CHUNKING = {
    'normativo': {
        'chunk_size': 1000,
        'chunk_overlap': 150,
        'separators': ["\n\nARTÍCULO", "\n\nArtículo", "\n\nArt.", "\n\n"],
        'descripcion': 'Documentos normativos (leyes, resoluciones)'
    },
    'tecnico': {
        'chunk_size': 700,
        'chunk_overlap': 100,
        'separators': ["\n\n##", "\n\n###", "\n\n", "\n"],
        'descripcion': 'Documentos técnicos (manuales, especificaciones)'
    },
    'analisis': {
        'chunk_size': 1200,
        'chunk_overlap': 200,
        'separators': ["\n\n\n", "\n\n", ". ", " "],
        'descripcion': 'Documentos de análisis (reportes, estudios)'
    }
}


# ============================================================================
# FUNCIONES DE DETECCIÓN DE TIPO DE DOCUMENTO
# ============================================================================

def detectar_tipo_documento(texto: str) -> str:
    """
    Analiza el texto y detecta el tipo de documento basándose en palabras clave
    y patrones estructurales.

    Returns:
        'normativo' | 'tecnico' | 'analisis'
    """
    # Palabras clave por tipo
    keywords_normativo = [
        'ARTÍCULO', 'RESUELVE', 'DISPONE', 'DECRETO', 'RESOLUCIÓN',
        'Artículo', 'VISTO', 'CONSIDERANDO', 'LEY', 'NORMATIVA'
    ]

    keywords_tecnico = [
        'Procedimiento', 'Especificación', 'Paso', 'Requisito',
        'Instructivo', 'Manual', 'Protocolo', '1.', '2.', '3.'
    ]

    # Contar ocurrencias
    score_normativo = sum(texto.count(kw) for kw in keywords_normativo)
    score_tecnico = sum(texto.count(kw) for kw in keywords_tecnico)

    # Heurísticas adicionales
    tiene_articulos = 'ARTÍCULO' in texto or 'Artículo' in texto
    tiene_numeracion = bool(len([line for line in texto.split('\n') if line.strip().startswith(('1.', '2.', '3.'))]) > 5)

    # Decidir tipo
    if tiene_articulos or score_normativo > 5:
        return 'normativo'
    elif tiene_numeracion or score_tecnico > 3:
        return 'tecnico'
    else:
        return 'analisis'


def obtener_estrategia_chunking(tipo_doc: str) -> Dict:
    """
    Retorna la configuración óptima de chunking según el tipo de documento.

    Args:
        tipo_doc: Tipo de documento ('normativo' | 'tecnico' | 'analisis')

    Returns:
        Diccionario con configuración de chunking
    """
    estrategia = ESTRATEGIAS_CHUNKING.get(tipo_doc, ESTRATEGIAS_CHUNKING['analisis'])

    # Sobrescribir con valores manuales si están configurados
    if CONFIG['chunk_size'] > 0:
        estrategia['chunk_size'] = CONFIG['chunk_size']
    if CONFIG['chunk_overlap'] > 0:
        estrategia['chunk_overlap'] = CONFIG['chunk_overlap']

    return estrategia


# ============================================================================
# FUNCIONES DE CARGA DE DOCUMENTOS
# ============================================================================

def cargar_documentos(source_path: str) -> List[Document]:
    """
    Carga todos los documentos (PDF y TXT) del directorio especificado.

    Args:
        source_path: Ruta al directorio con documentos

    Returns:
        Lista de objetos Document de LangChain
    """
    source_dir = Path(source_path)

    if not source_dir.exists():
        raise FileNotFoundError(f"Directorio no encontrado: {source_path}")

    documentos = []
    extensiones = [ext.strip() for ext in CONFIG['file_extensions']]

    print(f"\n[INFO] Buscando documentos en: {source_dir}")
    print(f"[INFO] Extensiones: {extensiones}")

    # Buscar archivos
    archivos = []
    for ext in extensiones:
        archivos.extend(source_dir.glob(f"*{ext}"))

    if not archivos:
        print(f"[WARNING] No se encontraron archivos en {source_dir}")
        return []

    print(f"[INFO] Encontrados {len(archivos)} archivos\n")

    # Cargar cada archivo
    for archivo in tqdm(archivos, desc="Cargando archivos"):
        try:
            if archivo.suffix.lower() == '.pdf':
                loader = PyPDFLoader(str(archivo))
                docs = loader.load()
            elif archivo.suffix.lower() == '.txt':
                loader = TextLoader(str(archivo), encoding='utf-8')
                docs = loader.load()
            else:
                print(f"[WARNING] Extensión no soportada: {archivo.suffix}")
                continue

            # Agregar metadata adicional
            for doc in docs:
                doc.metadata['filename'] = archivo.name
                doc.metadata['file_path'] = str(archivo)

            documentos.extend(docs)

        except Exception as e:
            print(f"[ERROR] Error cargando {archivo.name}: {e}")
            continue

    print(f"\n[SUCCESS] {len(documentos)} documentos cargados exitosamente")
    return documentos


# ============================================================================
# FUNCIONES DE PROCESAMIENTO Y CHUNKING
# ============================================================================

def procesar_documentos_por_tipo(documentos: List[Document]) -> Tuple[List[Document], Dict]:
    """
    Procesa documentos aplicando estrategias de chunking adaptativas según el tipo.

    Args:
        documentos: Lista de documentos cargados

    Returns:
        Tupla de (chunks procesados, estadísticas)
    """
    todos_chunks = []
    estadisticas = {
        'normativo': {'count': 0, 'chunks': 0},
        'tecnico': {'count': 0, 'chunks': 0},
        'analisis': {'count': 0, 'chunks': 0}
    }

    print("\n[INFO] Analizando tipo de documentos y aplicando chunking...")

    for doc in tqdm(documentos, desc="Procesando documentos"):
        # Detectar tipo
        tipo_doc = detectar_tipo_documento(doc.page_content)

        # Obtener estrategia
        estrategia = obtener_estrategia_chunking(tipo_doc)

        # Crear text splitter con estrategia específica
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=estrategia['chunk_size'],
            chunk_overlap=estrategia['chunk_overlap'],
            separators=estrategia['separators'],
            length_function=len
        )

        # Aplicar chunking
        chunks = text_splitter.split_documents([doc])

        # Agregar metadata de tipo y estrategia
        for chunk in chunks:
            chunk.metadata['tipo_documento'] = tipo_doc
            chunk.metadata['estrategia_chunking'] = tipo_doc
            chunk.metadata['chunk_size_usado'] = estrategia['chunk_size']
            chunk.metadata['fecha_procesamiento'] = datetime.now().isoformat()

        todos_chunks.extend(chunks)

        # Actualizar estadísticas
        estadisticas[tipo_doc]['count'] += 1
        estadisticas[tipo_doc]['chunks'] += len(chunks)

    return todos_chunks, estadisticas


# ============================================================================
# FUNCIONES DE CONSTRUCCIÓN DE BD VECTORIAL
# ============================================================================

def construir_base_vectorial(chunks: List[Document]) -> Chroma:
    """
    Construye la base de datos vectorial usando Chroma.

    Args:
        chunks: Lista de chunks de documentos procesados

    Returns:
        Objeto Chroma vectorstore
    """
    print("\n[INFO] Generando embeddings y construyendo base de datos vectorial...")
    print(f"[INFO] Modelo de embeddings: {CONFIG['embedding_model']}")
    print(f"[INFO] Total de chunks: {len(chunks)}")

    # Crear embeddings
    embeddings = OpenAIEmbeddings(
        openai_api_key=CONFIG['openai_api_key'],
        model=CONFIG['embedding_model']
    )

    # Crear directorio para la BD vectorial
    db_path = Path(CONFIG['vector_db_path']) / CONFIG['vector_db_name']
    db_path.mkdir(parents=True, exist_ok=True)

    print(f"[INFO] Ubicación BD: {db_path}")
    print("[INFO] Generando embeddings... (esto puede tardar algunos minutos)")

    # Construir vectorstore
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=str(db_path),
        collection_name=CONFIG['vector_db_name']
    )

    print("[SUCCESS] Base de datos vectorial creada exitosamente!")

    return vectorstore


def validar_base_vectorial(vectorstore: Chroma):
    """
    Valida que la base de datos vectorial funcione correctamente.

    Args:
        vectorstore: Objeto Chroma vectorstore
    """
    print("\n[INFO] Validando base de datos vectorial...")

    try:
        # Test de recuperación simple
        test_query = "documento"
        results = vectorstore.similarity_search(test_query, k=3)

        if results:
            print(f"[SUCCESS] Validación exitosa: {len(results)} documentos recuperados")
            print(f"[INFO] Ejemplo de resultado:")
            print(f"  - Archivo: {results[0].metadata.get('filename', 'N/A')}")
            print(f"  - Tipo: {results[0].metadata.get('tipo_documento', 'N/A')}")
            print(f"  - Contenido (primeros 100 chars): {results[0].page_content[:100]}...")
        else:
            print("[WARNING] No se recuperaron resultados en la validación")

    except Exception as e:
        print(f"[ERROR] Error en validación: {e}")


def guardar_metadata(estadisticas: Dict, chunks: List[Document]):
    """
    Guarda metadata del proceso de vectorización en un archivo JSON.

    Args:
        estadisticas: Estadísticas del procesamiento
        chunks: Lista de chunks procesados
    """
    metadata = {
        "database_name": CONFIG['vector_db_name'],
        "database_type": CONFIG['vector_db_type'],
        "database_path": str(Path(CONFIG['vector_db_path']) / CONFIG['vector_db_name']),
        "embedding_model": CONFIG['embedding_model'],
        "total_chunks": len(chunks),
        "total_documentos": sum(stat['count'] for stat in estadisticas.values()),
        "estadisticas_por_tipo": estadisticas,
        "source_path": CONFIG['source_path'],
        "fecha_creacion": datetime.now().isoformat(),
        "configuracion": {
            "file_extensions": CONFIG['file_extensions'],
            "estrategias_aplicadas": ESTRATEGIAS_CHUNKING
        }
    }

    # Guardar en archivo
    metadata_path = Path(CONFIG['vector_db_path']) / f"{CONFIG['vector_db_name']}_metadata.json"
    metadata_path.parent.mkdir(parents=True, exist_ok=True)

    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    print(f"\n[INFO] Metadata guardada en: {metadata_path}")


# ============================================================================
# FUNCIÓN PRINCIPAL
# ============================================================================

def validar_configuracion():
    """Valida que la configuración sea correcta antes de procesar."""
    print("=" * 70)
    print("CONSTRUCTOR DE BASE DE DATOS VECTORIAL")
    print("=" * 70)

    print("\n[INFO] Validando configuración...")

    # Validar API Key
    if not CONFIG['openai_api_key']:
        print("[ERROR] OPENAI_API_KEY no está configurada en el archivo .env")
        print("[INFO] Crea un archivo .env y agrega: OPENAI_API_KEY=sk-...")
        sys.exit(1)

    print(f"  ✓ OpenAI API Key configurada")

    # Validar directorio de origen
    if not Path(CONFIG['source_path']).exists():
        print(f"[ERROR] Directorio de documentos no encontrado: {CONFIG['source_path']}")
        sys.exit(1)

    print(f"  ✓ Directorio de documentos: {CONFIG['source_path']}")

    # Mostrar configuración
    print(f"\n[INFO] Configuración:")
    print(f"  - Modelo de embeddings: {CONFIG['embedding_model']}")
    print(f"  - Tipo de BD vectorial: {CONFIG['vector_db_type']}")
    print(f"  - Nombre de BD: {CONFIG['vector_db_name']}")
    print(f"  - Ubicación: {CONFIG['vector_db_path']}")
    print(f"  - Extensiones: {', '.join(CONFIG['file_extensions'])}")


def main():
    """Función principal del script."""
    try:
        # Validar configuración
        validar_configuracion()

        # Cargar documentos
        documentos = cargar_documentos(CONFIG['source_path'])

        if not documentos:
            print("[ERROR] No se encontraron documentos para procesar")
            sys.exit(1)

        # Procesar documentos y aplicar chunking
        chunks, estadisticas = procesar_documentos_por_tipo(documentos)

        # Mostrar estadísticas
        print("\n" + "=" * 70)
        print("ESTADÍSTICAS DE PROCESAMIENTO")
        print("=" * 70)
        for tipo, stats in estadisticas.items():
            if stats['count'] > 0:
                estrategia = ESTRATEGIAS_CHUNKING[tipo]
                print(f"\n[{tipo.upper()}] - {estrategia['descripcion']}")
                print(f"  - Documentos: {stats['count']}")
                print(f"  - Chunks generados: {stats['chunks']}")
                print(f"  - Chunk size: {estrategia['chunk_size']} tokens")
                print(f"  - Overlap: {estrategia['chunk_overlap']} tokens")

        print(f"\n[TOTAL]")
        print(f"  - Documentos procesados: {sum(s['count'] for s in estadisticas.values())}")
        print(f"  - Total de chunks: {len(chunks)}")
        print("=" * 70)

        # Construir base de datos vectorial
        vectorstore = construir_base_vectorial(chunks)

        # Validar que funcione
        validar_base_vectorial(vectorstore)

        # Guardar metadata
        guardar_metadata(estadisticas, chunks)

        # Resumen final
        print("\n" + "=" * 70)
        print("✅ BASE DE DATOS VECTORIAL CREADA EXITOSAMENTE")
        print("=" * 70)
        print(f"\n[INFO] Ubicación: {Path(CONFIG['vector_db_path']) / CONFIG['vector_db_name']}")
        print(f"[INFO] Total de chunks vectorizados: {len(chunks)}")
        print(f"[INFO] Modelo de embeddings: {CONFIG['embedding_model']}")
        print("\n[INFO] La base de datos está lista para ser utilizada en:")
        print("  - Sistemas RAG (Retrieval-Augmented Generation)")
        print("  - Búsquedas semánticas")
        print("  - Análisis de similitud de documentos")
        print("=" * 70 + "\n")

    except Exception as e:
        print(f"\n[ERROR] Error durante la ejecución: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
