"""
Procesador de PDFs en Chunks para Análisis de Schema
Extrae información estructural de PDFs grandes sin exceder límites de contexto
"""

import re
from pathlib import Path
from typing import Dict, List, Tuple
from dataclasses import dataclass, asdict
import json

try:
    import PyPDF2
    PDF_LIBRARY = "PyPDF2"
except ImportError:
    try:
        import fitz  # PyMuPDF
        PDF_LIBRARY = "PyMuPDF"
    except ImportError:
        PDF_LIBRARY = None


@dataclass
class ChunkAnalysis:
    """Resultados del análisis de un chunk"""
    chunk_id: int
    pages: Tuple[int, int]  # (inicio, fin)
    jerarquia: List[str]  # Elementos jerárquicos encontrados
    terminologia: List[str]  # Términos especializados
    relaciones: List[str]  # Verbos/relaciones detectadas
    entidades: List[str]  # Entidades nombradas


class PDFChunkProcessor:
    """Procesa PDFs en chunks para extraer información estructural"""

    # Tamaño de chunk en páginas
    CHUNK_SIZE = 5

    # Patrones de detección
    JERARQUIA_PATTERNS = [
        r'(?:Capítulo|CAPÍTULO|Cap\.)\s+(?:[IVXLCDM]+|\d+)',
        r'(?:Sección|SECCIÓN|Sec\.)\s+(?:[IVXLCDM]+|\d+)',
        r'(?:Artículo|ARTÍCULO|Art\.)\s+\d+',
        r'(?:Inciso|INCISO|Inc\.)\s+[a-z]\)',
        r'(?:Anexo|ANEXO)\s+[IVXLCDM]+',
        r'(?:Título|TÍTULO|Tít\.)\s+[IVXLCDM]+',
    ]

    RELACIONES_VERBOS = [
        'deroga', 'modifica', 'regula', 'cita', 'fundamenta',
        'reemplaza', 'sustituye', 'aplica', 'establece', 'define',
        'determina', 'dispone', 'aprueba', 'autoriza'
    ]

    ENTIDADES_PATTERNS = [
        r'(?:Resolución|RESOLUCIÓN|Res\.)\s+N?°?\s*\d+[/-]\d+',
        r'(?:Disposición|DISPOSICIÓN|Disp\.)\s+N?°?\s*\d+[/-]\d+',
        r'(?:Ley|LEY)\s+N?°?\s*\d+\.?\d*',
        r'(?:Decreto|DECRETO|Dec\.)\s+N?°?\s*\d+[/-]\d+',
        r'INSSJP|PAMI',
    ]

    def __init__(self, pdf_path: str, chunk_size: int = CHUNK_SIZE):
        self.pdf_path = Path(pdf_path)
        self.chunk_size = chunk_size
        self.total_pages = 0

        if not self.pdf_path.exists():
            raise FileNotFoundError(f"PDF no encontrado: {pdf_path}")

    def get_pdf_info(self) -> Dict:
        """Obtiene información básica del PDF"""
        if PDF_LIBRARY == "PyPDF2":
            with open(self.pdf_path, 'rb') as file:
                pdf = PyPDF2.PdfReader(file)
                self.total_pages = len(pdf.pages)
                metadata = pdf.metadata or {}

                return {
                    'filename': self.pdf_path.name,
                    'total_pages': self.total_pages,
                    'title': metadata.get('/Title', 'Sin título'),
                    'author': metadata.get('/Author', 'Sin autor'),
                    'size_kb': self.pdf_path.stat().st_size / 1024,
                    'library': PDF_LIBRARY
                }

        elif PDF_LIBRARY == "PyMuPDF":
            doc = fitz.open(self.pdf_path)
            self.total_pages = len(doc)
            metadata = doc.metadata

            return {
                'filename': self.pdf_path.name,
                'total_pages': self.total_pages,
                'title': metadata.get('title', 'Sin título'),
                'author': metadata.get('author', 'Sin autor'),
                'size_kb': self.pdf_path.stat().st_size / 1024,
                'library': PDF_LIBRARY
            }

        else:
            raise ImportError("No se encontró ninguna biblioteca PDF (PyPDF2 o PyMuPDF)")

    def extract_text_from_pages(self, start_page: int, end_page: int) -> str:
        """Extrae texto de un rango de páginas"""
        text = ""

        if PDF_LIBRARY == "PyPDF2":
            with open(self.pdf_path, 'rb') as file:
                pdf = PyPDF2.PdfReader(file)
                for page_num in range(start_page, min(end_page, self.total_pages)):
                    page = pdf.pages[page_num]
                    text += page.extract_text() + "\n"

        elif PDF_LIBRARY == "PyMuPDF":
            doc = fitz.open(self.pdf_path)
            for page_num in range(start_page, min(end_page, self.total_pages)):
                page = doc[page_num]
                text += page.get_text() + "\n"

        return text

    def analyze_chunk(self, chunk_text: str, chunk_id: int, pages: Tuple[int, int]) -> ChunkAnalysis:
        """Analiza un chunk de texto para extraer información estructural"""

        # Detectar jerarquía
        jerarquia = []
        for pattern in self.JERARQUIA_PATTERNS:
            matches = re.findall(pattern, chunk_text, re.IGNORECASE)
            jerarquia.extend(matches)

        # Detectar relaciones (verbos)
        relaciones = []
        for verbo in self.RELACIONES_VERBOS:
            if re.search(r'\b' + verbo + r'\b', chunk_text, re.IGNORECASE):
                relaciones.append(verbo.upper())

        # Detectar entidades
        entidades = []
        for pattern in self.ENTIDADES_PATTERNS:
            matches = re.findall(pattern, chunk_text, re.IGNORECASE)
            entidades.extend(matches)

        # Detectar terminología especializada (palabras en mayúsculas repetidas)
        terminologia = []
        # Palabras de 4+ letras en mayúsculas que aparecen 2+ veces
        mayusculas = re.findall(r'\b[A-ZÁÉÍÓÚ]{4,}\b', chunk_text)
        from collections import Counter
        freq = Counter(mayusculas)
        terminologia = [word for word, count in freq.items() if count >= 2]

        return ChunkAnalysis(
            chunk_id=chunk_id,
            pages=pages,
            jerarquia=list(set(jerarquia))[:10],  # Top 10 únicos
            terminologia=list(set(terminologia))[:15],  # Top 15 únicos
            relaciones=list(set(relaciones)),
            entidades=list(set(entidades))[:20]  # Top 20 únicos
        )

    def process_in_chunks(self) -> List[ChunkAnalysis]:
        """Procesa todo el PDF en chunks"""
        info = self.get_pdf_info()
        print(f"[PDF] Procesando: {info['filename']}")
        print(f"[INFO] Total paginas: {info['total_pages']}")
        print(f"[INFO] Tamanio del chunk: {self.chunk_size} paginas")
        print(f"[INFO] Biblioteca: {info['library']}\n")

        analyses = []

        for chunk_id, start_page in enumerate(range(0, self.total_pages, self.chunk_size)):
            end_page = start_page + self.chunk_size

            print(f"[CHUNK] Procesando chunk {chunk_id + 1}: paginas {start_page + 1}-{min(end_page, self.total_pages)}")

            # Extraer texto del chunk
            chunk_text = self.extract_text_from_pages(start_page, end_page)

            # Analizar chunk
            analysis = self.analyze_chunk(chunk_text, chunk_id, (start_page + 1, min(end_page, self.total_pages)))
            analyses.append(analysis)

            print(f"   [OK] Jerarquia: {len(analysis.jerarquia)} elementos")
            print(f"   [OK] Terminologia: {len(analysis.terminologia)} terminos")
            print(f"   [OK] Relaciones: {len(analysis.relaciones)} verbos")
            print(f"   [OK] Entidades: {len(analysis.entidades)} entidades\n")

        return analyses

    def consolidate_results(self, analyses: List[ChunkAnalysis]) -> Dict:
        """Consolida los resultados de todos los chunks"""

        all_jerarquia = []
        all_terminologia = []
        all_relaciones = []
        all_entidades = []

        for analysis in analyses:
            all_jerarquia.extend(analysis.jerarquia)
            all_terminologia.extend(analysis.terminologia)
            all_relaciones.extend(analysis.relaciones)
            all_entidades.extend(analysis.entidades)

        # Eliminar duplicados y ordenar por frecuencia
        from collections import Counter

        return {
            'resumen': {
                'archivo': self.pdf_path.name,
                'total_chunks': len(analyses),
                'total_paginas': self.total_pages
            },
            'jerarquia_detectada': {
                'elementos': list(set(all_jerarquia)),
                'count': len(set(all_jerarquia)),
                'ejemplo': all_jerarquia[:5] if all_jerarquia else []
            },
            'terminologia_clave': {
                'terminos': list(Counter(all_terminologia).most_common(20)),
                'count': len(set(all_terminologia))
            },
            'relaciones_detectadas': {
                'verbos': list(set(all_relaciones)),
                'count': len(set(all_relaciones))
            },
            'entidades_detectadas': {
                'entidades': list(Counter(all_entidades).most_common(30)),
                'count': len(set(all_entidades))
            }
        }

    def save_results(self, results: Dict, output_path: str):
        """Guarda los resultados en un archivo JSON"""
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        print(f"[SAVE] Resultados guardados en: {output_file}")

    def generate_markdown_summary(self, results: Dict, output_path: str):
        """Genera un resumen en Markdown legible"""
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        md_content = f"""# Análisis Estructural de PDF en Chunks

## Archivo Analizado
- **Nombre:** {results['resumen']['archivo']}
- **Total de Páginas:** {results['resumen']['total_paginas']}
- **Chunks Procesados:** {results['resumen']['total_chunks']}

---

## 1. Jerarquía Detectada

**Total de elementos únicos:** {results['jerarquia_detectada']['count']}

**Elementos encontrados:**
"""

        for elem in results['jerarquia_detectada']['elementos'][:20]:
            md_content += f"- {elem}\n"

        md_content += f"""
**Patrón de estructura inferido:**
```
{' → '.join(results['jerarquia_detectada']['ejemplo'][:3]) if results['jerarquia_detectada']['ejemplo'] else 'No se detectó estructura'}
```

---

## 2. Terminología Especializada (Top 20)

**Total de términos únicos:** {results['terminologia_clave']['count']}

| Término | Frecuencia |
|---------|------------|
"""

        for term, freq in results['terminologia_clave']['terminos']:
            md_content += f"| {term} | {freq} |\n"

        md_content += f"""
---

## 3. Relaciones Detectadas

**Verbos de relación encontrados:** {results['relaciones_detectadas']['count']}

"""

        for verbo in results['relaciones_detectadas']['verbos']:
            md_content += f"- `{verbo}`\n"

        md_content += f"""
---

## 4. Entidades Detectadas (Top 30)

**Total de entidades únicas:** {results['entidades_detectadas']['count']}

| Entidad | Frecuencia |
|---------|------------|
"""

        for entity, freq in results['entidades_detectadas']['entidades']:
            md_content += f"| {entity} | {freq} |\n"

        md_content += """
---

## Recomendaciones para el Schema

Basado en el análisis, el schema debería incluir:

### Nodos Sugeridos:
"""

        # Inferir nodos basados en entidades
        if any('PAMI' in str(e) or 'INSSJP' in str(e) for e, _ in results['entidades_detectadas']['entidades']):
            md_content += "- `:Normativa` (Resoluciones, Disposiciones)\n"

        md_content += """
### Relaciones Sugeridas:
"""

        for verbo in results['relaciones_detectadas']['verbos'][:5]:
            md_content += f"- `:{verbo}`\n"

        md_content += """
---

*Análisis generado por pdf_chunk_processor.py*
"""

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(md_content)

        print(f"[SAVE] Resumen Markdown guardado en: {output_file}")


def main():
    """Función principal para pruebas"""
    import sys

    if len(sys.argv) < 2:
        print("Uso: python pdf_chunk_processor.py <ruta_al_pdf> [chunk_size]")
        print("Ejemplo: python pdf_chunk_processor.py contexto_dominio/documento.pdf 5")
        sys.exit(1)

    pdf_path = sys.argv[1]
    chunk_size = int(sys.argv[2]) if len(sys.argv) > 2 else 5

    if PDF_LIBRARY is None:
        print("[ERROR] No se encontro ninguna biblioteca PDF instalada")
        print("[INFO] Instala una de las siguientes:")
        print("   pip install PyPDF2")
        print("   pip install PyMuPDF")
        sys.exit(1)

    try:
        # Crear procesador
        processor = PDFChunkProcessor(pdf_path, chunk_size)

        # Procesar en chunks
        analyses = processor.process_in_chunks()

        # Consolidar resultados
        print("\n[INFO] Consolidando resultados...\n")
        results = processor.consolidate_results(analyses)

        # Guardar resultados
        base_name = Path(pdf_path).stem
        output_dir = Path(pdf_path).parent

        processor.save_results(results, output_dir / f"analisis_{base_name}.json")
        processor.generate_markdown_summary(results, output_dir / f"resumen_{base_name}.md")

        print("\n[SUCCESS] Procesamiento completado exitosamente!")

    except Exception as e:
        print(f"\n[ERROR] Error durante el procesamiento: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
