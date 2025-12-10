import os
import json
import re
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# --- CONFIGURACIÓN DESDE .ENV ---
# Archivo de texto de entrada con la definición del esquema
SCHEMA_INPUT_TXT = os.getenv("LLM_SCHEMA_INPUT_FILE", "./pami_schema_input.txt")
# Directorio donde están los archivos TXT/PDF para listar
SOURCE_DIRECTORY = os.getenv("TXT_DIR", "./import_data/txt") 
# ----------------------------------

def parse_txt_to_schema(file_path: str) -> dict:
    """Intenta parsear el esquema de entidades y relaciones desde el archivo de texto."""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    schema = {"entities": [], "relationships": []}
    
    # --- PARSING DE ENTIDADES (NODOS) ---
    # Busca líneas que empiecen con '(:Label)'
    # Usamos una regex para capturar la etiqueta, la descripción y las propiedades
    
    # Patrón: (:LABEL)DescripciónPropiedad1... (La estructura de texto es muy densa, la regex es compleja)
    # Buscaremos líneas que comiencen con (: y terminemos antes de la siguiente sección (2. Relaciones)
    
    # 1. Extraer el bloque de Entidades (para evitar contaminación)
    entities_block_match = re.search(r'1\. Nodos \(Entidades\).*?(2\. Relaciones \(Edges\))', content, re.DOTALL)
    if entities_block_match:
        entities_block = entities_block_match.group(0)
    else:
        print("❌ Error de parsing: No se encontró el bloque '1. Nodos (Entidades)'.")
        return None

    # Patrón específico para capturar la Etiqueta y el resto de la descripción en el bloque
    entity_lines = re.findall(r'\((:[\w_]+)\)(.+?)(\((?::[\w_]+)\)|\n|2\. Relaciones \(Edges\))', entities_block, re.DOTALL)
    
    for match in re.finditer(r'\((:[\w_]+)\)(.+?)(?=\((:[\w_]+)\)|\n|2\. Relaciones)', entities_block, re.DOTALL):
        label_full = match.group(1) # (:Normativa)
        description_raw = match.group(2).strip()
        
        # Intentamos separar la descripción inicial de la lista de propiedades/tipos
        
        # Separación heurística: la primera frase después de la etiqueta es la descripción, el resto son propiedades
        if label_full == ":Normativa":
             # Caso Normativa: Documento legal (...) + codigoStringtipo_normaString...
             description = "Documento legal (Ley, Resolución, Disposición, Convenio). Propiedades: codigo, tipo_norma, fecha_emision, estado, objeto_principal."
             pattern = "Extraer documentos oficiales identificados como Ley, Resolución, Disposición, etc."
        elif label_full == ":Prestacion":
             description = "Servicio, insumo o módulo codificado del Nomenclador. Propiedades: codigo_practica, descripcion, tipo_prestacion, unidad_prestacional."
             pattern = "Buscar códigos y descripciones de prácticas médicas, sociales u odontológicas."
        else:
             # Para el resto, usamos una simplificación
             # La descripción es la primera frase que termina con un paréntesis o punto.
             desc_match = re.search(r'(.+?\)).*$', description_raw, re.DOTALL) or re.search(r'(.+?\.).*$', description_raw, re.DOTALL)
             description = desc_match.group(1).strip() if desc_match else description_raw[:100].strip() + '...'
             pattern = f"Patrón de extracción genérico para la entidad {label_full.replace(':', '')}."
        
        schema["entities"].append({
            "label": label_full.replace(':', ''),
            "description": description,
            "extraction_pattern": pattern
        })
        
    # --- PARSING DE RELACIONES ---
    # Busca líneas que empiecen con '[:RELACION]'
    
    # 1. Extraer el bloque de Relaciones
    relationships_block_match = re.search(r'2\. Relaciones \(Edges\).*', content, re.DOTALL)
    if relationships_block_match:
        relationships_block = relationships_block_match.group(0)
    else:
        print("❌ Error de parsing: No se encontró el bloque '2. Relaciones (Edges)'.")
        return None

    # Patrón para capturar: [:RELACION](:Origen) → (:Destino) (Propiedades...)
    relation_pattern = re.compile(r'\[(:[\w_]+)\]\((:[\w_]+)\)\s*[/]?[^→]*→\s*\((:[\w_]+)\)(.*)', re.DOTALL)

    for line in relationships_block.split('\n'):
        match = relation_pattern.search(line)
        if match:
            type_rel = match.group(1).replace(':', '')
            from_entity = match.group(2).replace(':', '')
            to_entity = match.group(3).replace(':', '')
            
            # La descripción es simplemente la lista de propiedades de contexto
            properties_raw = match.group(4).strip()
            if properties_raw:
                description = f"Relación contextual que incluye propiedades como: {properties_raw.split('String')[0].split('Float')[0].split('Date')[0].split('Date')[0].strip()}."
            else:
                 description = f"Conexión directa sin propiedades de contexto explícitas."

            schema["relationships"].append({
                "type": type_rel,
                "from_entity": from_entity,
                "to_entity": to_entity,
                "description": description
            })

    return schema


def scan_files_for_processing(directory: str) -> list:
    """Escanea el directorio en busca de archivos TXT, MD y PDF."""
    files_to_process = []
    if os.path.exists(directory):
        for filename in os.listdir(directory):
            if filename.lower().endswith(('.pdf', '.txt', '.md')):
                files_to_process.append(os.path.join(directory, filename))
    return files_to_process


def main():
    print("--- 🤖 INICIANDO GENERADOR TXT A JSON DE CONFIGURACIÓN ---")

    # 1. Cargar el Schema desde el archivo de texto
    llm_schema = parse_txt_to_schema(SCHEMA_INPUT_TXT)
    if llm_schema is None:
        print("\n⛔ La generación falló debido a errores en el parsing del esquema de texto.")
        return

    print(f"\n✅ Schema de {len(llm_schema['entities'])} Entidades y {len(llm_schema['relationships'])} Relaciones parseado.")

    # 2. Escaneo Automático de Archivos
    files_to_process = scan_files_for_processing(SOURCE_DIRECTORY)
    if not files_to_process:
        print(f"⚠️ ADVERTENCIA: No se encontraron archivos en '{SOURCE_DIRECTORY}'.")
    else:
        print(f"✅ Encontrados {len(files_to_process)} archivos en el directorio.")

    # 3. Armado y Guardado del Paquete Final
    output_package = {
        "domain_plan": {}, # Se mantiene vacío (para CSVs si hubiera)
        "llm_schema": llm_schema,  # <--- Schema parseado
        "files_to_process": files_to_process
    }

    filename = "builder_config.json"
    try:
        with open(filename, "w", encoding='utf-8') as f:
            json.dump(output_package, f, indent=4, ensure_ascii=False)
        
        print("\n" + "="*50)
        print(f"💾 ÉXITO: Archivo de configuración generado: {filename}")
        print("Muestra del output: ", json.dumps(output_package['llm_schema']['entities'][0], indent=2))
        print(f"👉 Archivos de entrada listados: {len(files_to_process)}")
        print("="*50)
            
    except Exception as e:
        print(f"\n❌ Error fatal guardando el JSON: {e}")

if __name__ == "__main__":
    main()