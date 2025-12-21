"""
CSV to Neo4j Loader
Generado por: Agente de Carga CSV a Neo4j
Versión: 1.0
Fecha: 2024-12-20

Este script carga datos desde archivos CSV a Neo4j siguiendo el schema validado
generado por el agente_schema_csv. Implementa carga batch optimizada y validación.
"""

import os
import sys
import json
import time
from pathlib import Path
from typing import Dict, List, Tuple, Any
from datetime import datetime
import pandas as pd
from dotenv import load_dotenv
from neo4j import GraphDatabase

# Configurar encoding para Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# ============================================================================
# 1. CONFIGURACIÓN
# ============================================================================

load_dotenv()

CONFIG = {
    'neo4j_uri': os.getenv('NEO4J_URI'),
    'neo4j_user': os.getenv('NEO4J_USER'),
    'neo4j_password': os.getenv('NEO4J_PASSWORD'),
    'csv_dir': os.getenv('CSV_DIR', './csv_data/'),
    'schema_path': os.getenv('SCHEMA_PATH', '../resultados/schema_csv_validado.json'),
    'batch_size': int(os.getenv('BATCH_SIZE', '1000')),
    'output_dir': os.getenv('OUTPUT_DIR', './output/'),
}

# ============================================================================
# 2. FUNCIONES AUXILIARES
# ============================================================================

def print_header(text: str):
    """Imprime encabezado estilizado."""
    print("\n" + "="*80)
    print(text.center(80))
    print("="*80)

def print_step(step_num: int, text: str):
    """Imprime paso del proceso."""
    print(f"\n📋 PASO {step_num}: {text}")

def validate_config():
    """Valida configuración requerida."""
    if not all([CONFIG['neo4j_uri'], CONFIG['neo4j_user'], CONFIG['neo4j_password']]):
        print("❌ Error: Faltan variables de entorno. Verifica tu archivo .env")
        print("\nRequerido:")
        print("  NEO4J_URI=bolt://localhost:7687")
        print("  NEO4J_USER=neo4j")
        print("  NEO4J_PASSWORD=tu_password")
        sys.exit(1)

# ============================================================================
# 3. CARGA DE SCHEMA
# ============================================================================

def load_schema_validado() -> Dict:
    """
    Lee el schema validado generado por agente_schema_csv.

    Returns:
        Dict con el schema completo
    """
    schema_path = Path(CONFIG['schema_path'])

    if not schema_path.exists():
        raise FileNotFoundError(
            f"❌ Schema no encontrado: {schema_path}\n"
            "   Ejecuta primero: python scripts/schema_csv_designer.py"
        )

    print(f"   Ruta: {schema_path}")

    with open(schema_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    schema = data.get('schema', data)

    print(f"   ✅ Schema cargado:")
    print(f"      - {len(schema.get('nodes', []))} tipos de nodos")
    print(f"      - {len(schema.get('relationships', []))} tipos de relaciones")

    return schema

# ============================================================================
# 4. CONEXIÓN A NEO4J
# ============================================================================

def connect_neo4j():
    """
    Conecta a Neo4j y verifica la conexión.

    Returns:
        Driver de Neo4j
    """
    try:
        driver = GraphDatabase.driver(
            CONFIG['neo4j_uri'],
            auth=(CONFIG['neo4j_user'], CONFIG['neo4j_password'])
        )

        # Test de conexión
        with driver.session() as session:
            result = session.run("RETURN 1 as test")
            result.single()

        print(f"   ✅ Conectado a: {CONFIG['neo4j_uri']}")
        return driver

    except Exception as e:
        raise ConnectionError(f"❌ Error conectando a Neo4j: {e}")

# ============================================================================
# 5. CONSTRAINTS E ÍNDICES
# ============================================================================

def create_constraints(driver, schema: Dict):
    """
    Crea constraints de unicidad para Primary Keys e índices de búsqueda.

    Args:
        driver: Driver de Neo4j
        schema: Schema validado
    """
    print("\n📐 Creando constraints e índices...")

    with driver.session() as session:
        # Constraints para PKs
        for node_def in schema.get('nodes', []):
            label = node_def['label']
            key_columns = node_def.get('key_columns', [])

            for key_col in key_columns:
                constraint_name = f"unique_{label}_{key_col}".lower()

                cypher = f"""
                CREATE CONSTRAINT {constraint_name} IF NOT EXISTS
                FOR (n:{label})
                REQUIRE n.{key_col} IS UNIQUE
                """

                try:
                    session.run(cypher)
                    print(f"   ✅ Constraint: {label} ({key_col})")
                except Exception as e:
                    print(f"   ⚠️  Constraint {label}.{key_col}: {str(e)[:50]}")

        # Índices para propiedades comunes (name, title, etc.)
        common_index_props = ['name', 'title', 'nombre', 'codigo']

        for node_def in schema.get('nodes', []):
            label = node_def['label']
            properties = node_def.get('properties', [])

            for prop in properties:
                if prop.lower() in common_index_props:
                    index_name = f"idx_{label}_{prop}".lower()

                    cypher = f"""
                    CREATE INDEX {index_name} IF NOT EXISTS
                    FOR (n:{label})
                    ON (n.{prop})
                    """

                    try:
                        session.run(cypher)
                        print(f"   ✅ Índice: {label}.{prop}")
                    except Exception:
                        pass  # Índices son opcionales

# ============================================================================
# 6. VALIDACIÓN DE CSV
# ============================================================================

def validate_csv(csv_path: Path, required_columns: List[str]) -> Tuple[bool, str]:
    """
    Valida que el CSV existe y tiene las columnas requeridas.

    Args:
        csv_path: Ruta al archivo CSV
        required_columns: Lista de columnas requeridas

    Returns:
        (es_valido, mensaje_error)
    """
    if not csv_path.exists():
        return False, f"Archivo no encontrado: {csv_path}"

    try:
        df = pd.read_csv(csv_path, nrows=1)
        csv_columns = set(df.columns)
        required_set = set(required_columns)

        missing = required_set - csv_columns
        if missing:
            return False, f"Columnas faltantes: {missing}"

        return True, "OK"

    except Exception as e:
        return False, f"Error leyendo CSV: {e}"

# ============================================================================
# 7. CARGA DE NODOS
# ============================================================================

def load_nodes(driver, schema: Dict, csv_dir: str) -> Dict[str, int]:
    """
    Carga nodos desde CSVs usando batch UNWIND.

    Args:
        driver: Driver de Neo4j
        schema: Schema validado
        csv_dir: Directorio con CSVs

    Returns:
        Dict con conteo de nodos por tipo
    """
    nodes_created = {}
    batch_size = CONFIG['batch_size']

    for node_def in schema.get('nodes', []):
        label = node_def['label']
        source_file = node_def.get('source_file', f"{label.lower()}.csv")
        key_columns = node_def.get('key_columns', [])
        properties = node_def.get('properties', [])

        csv_path = Path(csv_dir) / source_file

        # Validar CSV
        all_columns = key_columns + properties
        is_valid, error_msg = validate_csv(csv_path, all_columns)

        if not is_valid:
            print(f"\n⚠️  Saltando {label}: {error_msg}")
            continue

        print(f"\n📥 Cargando nodos :{label} desde {source_file}")

        # Leer CSV
        df = pd.read_csv(csv_path)

        # Manejar valores NULL
        df = df.where(pd.notna(df), None)

        total_rows = len(df)
        print(f"   📊 Total registros: {total_rows:,}")

        # Cargar en batches
        nodes_count = 0

        for i in range(0, total_rows, batch_size):
            batch = df.iloc[i:i+batch_size]
            batch_records = batch.to_dict('records')

            # Query con UNWIND
            # Usar primera key_column como identificador principal
            pk = key_columns[0]

            cypher = f"""
            UNWIND $batch AS row
            MERGE (n:{label} {{{pk}: row.{pk}}})
            SET n += row
            SET n.loaded_at = datetime(),
                n.loaded_from = $source_file
            """

            with driver.session() as session:
                try:
                    result = session.run(
                        cypher,
                        batch=batch_records,
                        source_file=source_file
                    )
                    summary = result.consume()
                    nodes_count += summary.counters.nodes_created

                    # Progress
                    progress = min(i + batch_size, total_rows)
                    pct = (progress / total_rows) * 100
                    print(f"   🔄 Progreso: {pct:.1f}% ({progress:,}/{total_rows:,})")

                except Exception as e:
                    print(f"   ❌ Error en batch {i}-{i+batch_size}: {e}")

        print(f"   ✅ Completado: {nodes_count:,} nodos :{label} creados")
        nodes_created[label] = nodes_count

    return nodes_created

# ============================================================================
# 8. CARGA DE RELACIONES
# ============================================================================

def load_relationships(driver, schema: Dict, csv_dir: str) -> Dict[str, int]:
    """
    Carga relaciones desde CSVs usando batch UNWIND.

    Args:
        driver: Driver de Neo4j
        schema: Schema validado
        csv_dir: Directorio con CSVs

    Returns:
        Dict con conteo de relaciones por tipo
    """
    rels_created = {}
    batch_size = CONFIG['batch_size']

    for rel_def in schema.get('relationships', []):
        rel_type = rel_def['type']
        from_label = rel_def['from_label']
        to_label = rel_def['to_label']
        source_file = rel_def.get('source_file')
        from_column = rel_def.get('from_column')
        to_column = rel_def.get('to_column')
        rel_properties = rel_def.get('properties', [])

        if not source_file:
            print(f"\n⚠️  Saltando relación {rel_type}: sin source_file")
            continue

        csv_path = Path(csv_dir) / source_file

        # Validar CSV
        required_cols = [from_column, to_column] + rel_properties
        is_valid, error_msg = validate_csv(csv_path, required_cols)

        if not is_valid:
            print(f"\n⚠️  Saltando {rel_type}: {error_msg}")
            continue

        print(f"\n🔗 Cargando relaciones :{rel_type}")
        print(f"   ({from_label})-[:{rel_type}]->({to_label})")

        # Leer CSV
        df = pd.read_csv(csv_path)
        df = df.where(pd.notna(df), None)

        # Filtrar filas donde from o to son NULL
        df = df.dropna(subset=[from_column, to_column])

        total_rows = len(df)
        print(f"   📊 Total relaciones potenciales: {total_rows:,}")

        # Cargar en batches
        rels_count = 0

        for i in range(0, total_rows, batch_size):
            batch = df.iloc[i:i+batch_size]
            batch_records = batch.to_dict('records')

            # Construir SET para propiedades de relación
            if rel_properties:
                set_clauses = [f"r.{prop} = row.{prop}" for prop in rel_properties]
                set_statement = "SET " + ", ".join(set_clauses)
            else:
                set_statement = ""

            cypher = f"""
            UNWIND $batch AS row
            MATCH (from:{from_label} {{{from_column}: row.{from_column}}})
            MATCH (to:{to_label} {{{to_column}: row.{to_column}}})
            MERGE (from)-[r:{rel_type}]->(to)
            {set_statement}
            """

            with driver.session() as session:
                try:
                    result = session.run(cypher, batch=batch_records)
                    summary = result.consume()
                    rels_count += summary.counters.relationships_created

                    # Progress
                    progress = min(i + batch_size, total_rows)
                    pct = (progress / total_rows) * 100
                    print(f"   🔄 Progreso: {pct:.1f}% ({progress:,}/{total_rows:,})")

                except Exception as e:
                    print(f"   ❌ Error en batch {i}-{i+batch_size}: {e}")

        print(f"   ✅ Completado: {rels_count:,} relaciones creadas")
        rels_created[rel_type] = rels_count

    return rels_created

# ============================================================================
# 9. VALIDACIÓN POST-CARGA
# ============================================================================

def validate_graph(driver, schema: Dict) -> Dict:
    """
    Valida que los datos se cargaron correctamente.

    Args:
        driver: Driver de Neo4j
        schema: Schema validado

    Returns:
        Dict con estadísticas de validación
    """
    print("\n🔍 Validando carga...")

    validation_report = {
        'nodes': {},
        'relationships': {},
        'orphan_nodes': [],
        'total_nodes': 0,
        'total_relationships': 0
    }

    with driver.session() as session:
        # Validar nodos
        print("\n   NODOS CARGADOS:")
        for node_def in schema.get('nodes', []):
            label = node_def['label']

            result = session.run(f"MATCH (n:{label}) RETURN count(n) as count")
            count = result.single()['count']

            print(f"      :{label} = {count:,} nodos")
            validation_report['nodes'][label] = count
            validation_report['total_nodes'] += count

        # Validar relaciones
        print("\n   RELACIONES CARGADAS:")
        for rel_def in schema.get('relationships', []):
            rel_type = rel_def['type']

            result = session.run(f"MATCH ()-[r:{rel_type}]->() RETURN count(r) as count")
            count = result.single()['count']

            print(f"      :{rel_type} = {count:,} relaciones")
            validation_report['relationships'][rel_type] = count
            validation_report['total_relationships'] += count

        # Detectar nodos huérfanos
        print("\n   NODOS HUÉRFANOS:")
        cypher_orphans = """
        MATCH (n)
        WHERE NOT (n)--()
        RETURN labels(n)[0] as label, count(n) as count
        ORDER BY count DESC
        """

        result = session.run(cypher_orphans)
        orphans = list(result)

        if orphans:
            for record in orphans:
                label = record['label']
                count = record['count']
                print(f"      ⚠️  {label}: {count:,} nodos sin relaciones")
                validation_report['orphan_nodes'].append({
                    'label': label,
                    'count': count
                })
        else:
            print(f"      ✅ No hay nodos huérfanos")

    return validation_report

# ============================================================================
# 10. GENERACIÓN DE REPORTE
# ============================================================================

def generate_report(
    schema: Dict,
    nodes_created: Dict[str, int],
    rels_created: Dict[str, int],
    validation: Dict,
    duration: float
) -> Dict:
    """
    Genera reporte JSON de la carga.

    Args:
        schema: Schema usado
        nodes_created: Nodos creados por tipo
        rels_created: Relaciones creadas por tipo
        validation: Resultado de validación
        duration: Duración en segundos

    Returns:
        Dict con reporte completo
    """
    report = {
        'metadata': {
            'timestamp': datetime.now().isoformat(),
            'duration_seconds': round(duration, 2),
            'csv_dir': CONFIG['csv_dir'],
            'schema_path': CONFIG['schema_path'],
            'batch_size': CONFIG['batch_size'],
        },
        'summary': {
            'total_nodes': sum(nodes_created.values()),
            'total_relationships': sum(rels_created.values()),
            'nodes_by_type': nodes_created,
            'relationships_by_type': rels_created,
        },
        'validation': validation
    }

    # Guardar reporte
    output_dir = Path(CONFIG['output_dir'])
    output_dir.mkdir(exist_ok=True)

    report_path = output_dir / 'load_report.json'

    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"\n📁 Reporte guardado: {report_path}")

    return report

# ============================================================================
# 11. PIPELINE PRINCIPAL
# ============================================================================

def main():
    """Pipeline principal de carga CSV a Neo4j."""

    start_time = time.time()

    print_header("🚀 CARGA DE CSV A NEO4J")

    # Validar configuración
    validate_config()

    try:
        # Paso 1: Cargar schema
        print_step(1, "Cargar schema validado")
        schema = load_schema_validado()

        # Paso 2: Conectar a Neo4j
        print_step(2, "Conectar a Neo4j")
        driver = connect_neo4j()

        # Paso 3: Preparar Neo4j
        print_step(3, "Preparar Neo4j")
        create_constraints(driver, schema)

        # Paso 4: Cargar nodos
        print_step(4, "Cargar nodos desde CSVs")
        nodes_created = load_nodes(driver, schema, CONFIG['csv_dir'])

        # Paso 5: Cargar relaciones
        print_step(5, "Cargar relaciones desde CSVs")
        rels_created = load_relationships(driver, schema, CONFIG['csv_dir'])

        # Paso 6: Validación
        print_step(6, "Validación post-carga")
        validation = validate_graph(driver, schema)

        # Cerrar conexión
        driver.close()

        # Calcular duración
        duration = time.time() - start_time

        # Generar reporte
        print_step(7, "Generar reporte")
        report = generate_report(
            schema,
            nodes_created,
            rels_created,
            validation,
            duration
        )

        # Resumen final
        print_header("✅ CARGA COMPLETADA")
        print(f"\n📊 ESTADÍSTICAS:")
        print(f"   ⏱️  Tiempo total: {duration:.2f} segundos")
        print(f"   📦 Nodos creados: {sum(nodes_created.values()):,}")
        print(f"   🔗 Relaciones creadas: {sum(rels_created.values()):,}")
        print("\n" + "="*80)

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
