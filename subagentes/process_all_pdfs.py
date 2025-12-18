"""
Procesador Batch de PDFs - Procesa automáticamente todos los PDFs en contexto_dominio/
Detecta PDFs grandes, verifica si ya tienen resumen, y los procesa si es necesario
"""

import sys
from pathlib import Path
from pdf_chunk_processor import PDFChunkProcessor, PDF_LIBRARY

# Configuración
CONTEXT_DIR = "contexto_dominio"
SIZE_THRESHOLD_KB = 100  # PDFs mayores a 100KB se procesan en chunks
CHUNK_SIZE = 5


def detect_pdfs(directory: Path):
    """Detecta todos los PDFs en el directorio"""
    if not directory.exists():
        print(f"[ERROR] Directorio no encontrado: {directory}")
        return []

    pdfs = list(directory.glob("*.pdf"))
    print(f"[INFO] Encontrados {len(pdfs)} archivos PDF en {directory}\n")
    return pdfs


def check_needs_processing(pdf_path: Path):
    """Verifica si un PDF necesita ser procesado"""
    size_kb = pdf_path.stat().st_size / 1024
    base_name = pdf_path.stem

    # Verificar si ya existe resumen
    resumen_path = pdf_path.parent / f"resumen_{base_name}.md"
    analisis_path = pdf_path.parent / f"analisis_{base_name}.json"

    already_processed = resumen_path.exists() and analisis_path.exists()
    is_large = size_kb > SIZE_THRESHOLD_KB

    return {
        'path': pdf_path,
        'size_kb': size_kb,
        'is_large': is_large,
        'already_processed': already_processed,
        'needs_processing': is_large and not already_processed,
        'resumen_exists': resumen_path.exists(),
        'analisis_exists': analisis_path.exists()
    }


def process_all_pdfs(directory_path: str = CONTEXT_DIR, force_reprocess: bool = False):
    """Procesa todos los PDFs que lo necesiten"""

    directory = Path(directory_path)

    # Verificar biblioteca PDF
    if PDF_LIBRARY is None:
        print("[ERROR] No se encontro ninguna biblioteca PDF instalada")
        print("[INFO] Instala una de las siguientes:")
        print("   pip install PyPDF2")
        print("   pip install PyMuPDF")
        return False

    print("=" * 60)
    print("PROCESADOR BATCH DE PDFs - Análisis de Schema")
    print("=" * 60)
    print(f"[INFO] Directorio: {directory}")
    print(f"[INFO] Umbral de tamaño: {SIZE_THRESHOLD_KB} KB")
    print(f"[INFO] Biblioteca PDF: {PDF_LIBRARY}\n")

    # Detectar PDFs
    pdfs = detect_pdfs(directory)

    if not pdfs:
        print("[INFO] No se encontraron archivos PDF")
        return True

    # Analizar cada PDF
    pdf_status = []
    for pdf_path in pdfs:
        status = check_needs_processing(pdf_path)
        pdf_status.append(status)

    # Mostrar resumen
    print("-" * 60)
    print("RESUMEN DE PDFs ENCONTRADOS:")
    print("-" * 60)

    total_to_process = 0
    already_processed = 0
    small_pdfs = 0

    for i, status in enumerate(pdf_status, 1):
        filename = status['path'].name
        size = status['size_kb']

        print(f"\n[{i}] {filename}")
        print(f"    Tamaño: {size:.1f} KB")

        if status['already_processed'] and not force_reprocess:
            print(f"    Estado: [LISTO] Ya procesado")
            already_processed += 1
        elif status['needs_processing'] or (force_reprocess and status['is_large']):
            print(f"    Estado: [PENDIENTE] Necesita procesamiento")
            total_to_process += 1
        elif not status['is_large']:
            print(f"    Estado: [PEQUEÑO] No requiere chunks (<{SIZE_THRESHOLD_KB}KB)")
            small_pdfs += 1

    print("\n" + "-" * 60)
    print(f"TOTAL: {len(pdf_status)} PDFs")
    print(f"  - A procesar: {total_to_process}")
    print(f"  - Ya procesados: {already_processed}")
    print(f"  - Pequeños (no requieren chunks): {small_pdfs}")
    print("-" * 60 + "\n")

    # Procesar PDFs que lo necesiten
    if total_to_process == 0:
        print("[SUCCESS] Todos los PDFs grandes ya estan procesados!")
        print("[INFO] El agente puede continuar con el analisis del schema\n")
        return True

    print(f"[INFO] Procesando {total_to_process} PDF(s)...\n")

    processed_count = 0
    failed_count = 0

    for status in pdf_status:
        if not (status['needs_processing'] or (force_reprocess and status['is_large'])):
            continue

        pdf_path = status['path']
        print("=" * 60)
        print(f"Procesando: {pdf_path.name}")
        print("=" * 60)

        try:
            # Crear procesador
            processor = PDFChunkProcessor(str(pdf_path), CHUNK_SIZE)

            # Procesar en chunks
            analyses = processor.process_in_chunks()

            # Consolidar resultados
            print("\n[INFO] Consolidando resultados...")
            results = processor.consolidate_results(analyses)

            # Guardar resultados
            base_name = pdf_path.stem
            output_dir = pdf_path.parent

            processor.save_results(results, output_dir / f"analisis_{base_name}.json")
            processor.generate_markdown_summary(results, output_dir / f"resumen_{base_name}.md")

            print(f"[SUCCESS] {pdf_path.name} procesado exitosamente!\n")
            processed_count += 1

        except Exception as e:
            print(f"[ERROR] Error procesando {pdf_path.name}: {e}")
            failed_count += 1
            continue

    # Resumen final
    print("\n" + "=" * 60)
    print("PROCESAMIENTO COMPLETADO")
    print("=" * 60)
    print(f"[SUCCESS] Procesados exitosamente: {processed_count}")
    if failed_count > 0:
        print(f"[WARNING] Fallidos: {failed_count}")
    print(f"[INFO] Archivos de resumen disponibles: {already_processed + processed_count}")
    print("\n[INFO] El agente puede continuar con el analisis del schema")
    print("=" * 60 + "\n")

    return failed_count == 0


def list_available_summaries(directory_path: str = CONTEXT_DIR):
    """Lista todos los resúmenes disponibles"""
    directory = Path(directory_path)

    if not directory.exists():
        print(f"[ERROR] Directorio no encontrado: {directory}")
        return

    resumenes = list(directory.glob("resumen_*.md"))

    print("\n" + "=" * 60)
    print("RESUMENES DISPONIBLES PARA EL AGENTE")
    print("=" * 60)

    if not resumenes:
        print("[INFO] No hay resumenes disponibles aun")
        print("[INFO] Ejecuta: python process_all_pdfs.py")
    else:
        for i, resumen in enumerate(resumenes, 1):
            size_kb = resumen.stat().st_size / 1024
            print(f"[{i}] {resumen.name} ({size_kb:.1f} KB)")

    print("=" * 60 + "\n")


def main():
    """Función principal"""

    # Procesar argumentos
    force_reprocess = "--force" in sys.argv
    list_only = "--list" in sys.argv

    if list_only:
        list_available_summaries()
        return

    if force_reprocess:
        print("[INFO] Modo FORCE: Se reprocesaran todos los PDFs grandes\n")

    # Procesar todos los PDFs
    success = process_all_pdfs(force_reprocess=force_reprocess)

    if not success:
        sys.exit(1)


if __name__ == "__main__":
    # Verificar si se pasa argumento de directorio
    if len(sys.argv) > 1 and not sys.argv[1].startswith("--"):
        CONTEXT_DIR = sys.argv[1]

    main()
