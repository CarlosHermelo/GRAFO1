"""
Script de Preparación de Contexto
Prepara automáticamente el contexto del dominio procesando PDFs antes de ejecutar el agente
"""

import subprocess
import sys
from pathlib import Path


def main():
    """Prepara el contexto procesando PDFs automáticamente"""

    print("\n" + "=" * 60)
    print("PREPARACIÓN DE CONTEXTO - Agente de Diseño de Schema")
    print("=" * 60 + "\n")

    # Verificar que estamos en el directorio correcto
    if not Path("process_all_pdfs.py").exists():
        print("[ERROR] Ejecuta este script desde el directorio 'subagentes/'")
        sys.exit(1)

    # Verificar que existe el directorio de contexto
    if not Path("contexto_dominio").exists():
        print("[WARNING] El directorio 'contexto_dominio/' no existe")
        print("[INFO] Creando directorio...")
        Path("contexto_dominio").mkdir(parents=True)
        print("[INFO] Coloca tus archivos PDF en 'contexto_dominio/' y vuelve a ejecutar\n")
        sys.exit(0)

    # Verificar que hay PDFs
    pdfs = list(Path("contexto_dominio").glob("*.pdf"))
    if not pdfs:
        print("[WARNING] No se encontraron archivos PDF en 'contexto_dominio/'")
        print("[INFO] Coloca tus archivos PDF en 'contexto_dominio/' y vuelve a ejecutar\n")
        sys.exit(0)

    print(f"[INFO] Encontrados {len(pdfs)} archivo(s) PDF")
    print("[INFO] Iniciando procesamiento automático...\n")
    print("-" * 60 + "\n")

    # Ejecutar el procesador batch
    try:
        result = subprocess.run(
            [sys.executable, "process_all_pdfs.py"],
            check=True
        )

        if result.returncode == 0:
            print("\n" + "=" * 60)
            print("CONTEXTO PREPARADO EXITOSAMENTE")
            print("=" * 60)
            print("\n[INFO] Los resúmenes de PDFs están listos")
            print("[INFO] El agente puede proceder con el análisis del schema")
            print("\n[SIGUIENTE PASO] Ejecuta el agente de diseño de schema\n")

    except subprocess.CalledProcessError as e:
        print(f"\n[ERROR] Error durante el procesamiento: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
