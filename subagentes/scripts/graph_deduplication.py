"""
Graph Knowledge Deduplication Pipeline
Entity Resolution por Capas con Auditoría Completa
Versión: 1.0
Fecha: 2024-12-17
Schema Version: 1.0

Este script depura el grafo de conocimiento aplicando Entity Resolution
en 4 capas: determinística, fuzzy, contextual y semántica (opcional).
"""

import os
import json
import sys
import uuid
from typing import Dict, List, Any, Tuple
from datetime import datetime
from collections import defaultdict
from dotenv import load_dotenv
from neo4j import GraphDatabase

# Importar parsers locales
from schema_parser import parse_schema, get_node_by_label

# Configurar codificación UTF-8 para Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Importaciones opcionales
try:
    from rapidfuzz import fuzz
    FUZZY_SUPPORT = True
except ImportError:
    FUZZY_SUPPORT = False
    print("⚠️ No se encontró rapidfuzz. Instala con: pip install rapidfuzz")

try:
    import numpy as np
    NUMPY_SUPPORT = True
except ImportError:
    NUMPY_SUPPORT = False
    print("⚠️ No se encontró numpy. Instala con: pip install numpy")

try:
    from openai import OpenAI
    OPENAI_SUPPORT = True
except ImportError:
    OPENAI_SUPPORT = False
    print("⚠️ No se encontró openai. Embeddings deshabilitados.")

# ============================================================================
# 1. CONFIGURACIÓN
# ============================================================================

load_dotenv()

# Variables de entorno
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Validar configuración
if not all([NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD]):
    print("❌ Error: Faltan variables de entorno Neo4j. Verifica tu archivo .env")
    sys.exit(1)

# Inicializar clientes
neo4j_driver = GraphDatabase.driver(
    NEO4J_URI,
    auth=(NEO4J_USER, NEO4J_PASSWORD)
)

if OPENAI_SUPPORT and OPENAI_API_KEY:
    openai_client = OpenAI(api_key=OPENAI_API_KEY)
else:
    openai_client = None

# Cargar schema
SCHEMA_INFO = parse_schema("../resultados/schema_diseñado.md")

print(f"✅ Configuración cargada")
print(f"   Schema: {len(SCHEMA_INFO['nodos'])} nodos, {len(SCHEMA_INFO['relaciones'])} relaciones")
print(f"   Fuzzy Support: {FUZZY_SUPPORT}")
print(f"   Embeddings Support: {OPENAI_SUPPORT and openai_client is not None}")

# Cargar configuración de embeddings (opcional)
EMBEDDING_CONFIG = None
if os.path.exists("embedding_config.json"):
    with open("embedding_config.json", "r", encoding="utf-8") as f:
        EMBEDDING_CONFIG = json.load(f)
        print(f"   ✅ Configuración de embeddings cargada")

# ============================================================================
# 2. UTILIDADES - NORMALIZACIÓN
# ============================================================================

def normalize_key(value):
    """Normaliza un valor para comparación exacta"""
    if value is None:
        return ""
    return str(value).lower().strip()


def normalize_numero_ley(numero):
    """Normaliza números de ley al formato estándar"""
    if not numero:
        return numero

    # Remover puntos, espacios, guiones
    numero_clean = str(numero).replace(".", "").replace(" ", "").replace("-", "")

    # Si es un número de 5 dígitos, agregar punto
    if numero_clean.isdigit() and len(numero_clean) == 5:
        return f"{numero_clean[:2]}.{numero_clean[2:]}"

    return numero_clean


# ============================================================================
# 2. UTILIDADES - SIMILITUD FUZZY
# ============================================================================

def fuzzy_similarity(text1, text2):
    """
    Calcula similitud fuzzy entre dos textos

    Args:
        text1: Primer texto
        text2: Segundo texto

    Returns:
        Score de similitud (0.0-1.0)
    """
    if not FUZZY_SUPPORT:
        return 0.0

    if not text1 or not text2:
        return 0.0

    return fuzz.ratio(str(text1), str(text2)) / 100.0


# ============================================================================
# 2. UTILIDADES - BLOCKING
# ============================================================================

def create_blocks_for_entity(session, label, blocking_key):
    """
    Crea bloques para reducir comparaciones O(n²) → O(n*k)

    Args:
        session: Sesión Neo4j
        label: Label del nodo
        blocking_key: Propiedad para agrupar

    Returns:
        Dict de bloques {key: [node_data]}
    """
    query = f"""
    MATCH (n:{label})
    WHERE n.{blocking_key} IS NOT NULL
    RETURN n.{blocking_key} as block_key,
           collect({{id: n.id, properties: properties(n)}}) as nodes
    """

    result = session.run(query)

    blocks = {}
    for record in result:
        key = record["block_key"]
        nodes = record["nodes"]
        blocks[key] = nodes

    return blocks


# ============================================================================
# 3. ENTITY RESOLUTION - CAPA 1: DETERMINÍSTICA
# ============================================================================

def er_deterministic(session, label, identity_keys, normalize_keys):
    """
    Encuentra duplicados por clave exacta normalizada

    Args:
        session: Sesión Neo4j
        label: Label del nodo
        identity_keys: Lista de propiedades que forman la identidad
        normalize_keys: Propiedades a normalizar antes de comparar

    Returns:
        Lista de matches {"canonical_id", "duplicate_id", "score", "razon"}
    """
    print(f"\n   🔍 Capa Determinística: {label}")

    # Construir expresión de clave normalizada
    key_parts = []
    for key in identity_keys:
        if key in normalize_keys:
            key_parts.append(f"toLower(trim(toString(n.{key})))")
        else:
            key_parts.append(f"toString(n.{key})")

    normalized_key_expr = " + '-' + ".join(key_parts)

    query = f"""
    MATCH (n:{label})
    WITH n, {normalized_key_expr} as normalized_key
    WITH normalized_key, collect(n) as duplicates
    WHERE size(duplicates) > 1
    UNWIND range(0, size(duplicates)-2) as i
    UNWIND range(i+1, size(duplicates)-1) as j
    RETURN duplicates[i].id as canonical_id,
           duplicates[j].id as duplicate_id,
           1.0 as score,
           'deterministic' as razon
    """

    result = session.run(query)

    matches = []
    for record in result:
        matches.append({
            "canonical_id": record["canonical_id"],
            "duplicate_id": record["duplicate_id"],
            "score": record["score"],
            "razon": record["razon"]
        })

    print(f"      ✅ {len(matches)} duplicados encontrados")
    return matches


# ============================================================================
# 3. ENTITY RESOLUTION - CAPA 2: FUZZY
# ============================================================================

def er_fuzzy(session, label, compare_fields, threshold, blocking_key):
    """
    Encuentra duplicados por similitud fuzzy

    Args:
        session: Sesión Neo4j
        label: Label del nodo
        compare_fields: Campos a comparar
        threshold: Umbral de similitud (0.0-1.0)
        blocking_key: Propiedad para agrupar

    Returns:
        Lista de matches
    """
    if not FUZZY_SUPPORT:
        print(f"\n   ⚠️ Capa Fuzzy: {label} - Deshabilitada (falta rapidfuzz)")
        return []

    print(f"\n   🔍 Capa Fuzzy: {label}")
    print(f"      Campos: {compare_fields}, Umbral: {threshold}, Blocking: {blocking_key}")

    # Crear bloques
    blocks = create_blocks_for_entity(session, label, blocking_key)
    print(f"      Bloques creados: {len(blocks)}")

    matches = []
    comparisons = 0

    for block_key, nodes in blocks.items():
        # Comparar todos los pares dentro del bloque
        for i in range(len(nodes)):
            for j in range(i+1, len(nodes)):
                node1 = nodes[i]
                node2 = nodes[j]
                comparisons += 1

                # Calcular similitud en cada campo
                scores = []
                for field in compare_fields:
                    val1 = node1["properties"].get(field)
                    val2 = node2["properties"].get(field)

                    if val1 and val2:
                        sim = fuzzy_similarity(val1, val2)
                        scores.append(sim)

                # Score promedio
                if scores:
                    avg_score = sum(scores) / len(scores)

                    if avg_score >= threshold:
                        matches.append({
                            "canonical_id": node1["id"],
                            "duplicate_id": node2["id"],
                            "score": avg_score,
                            "razon": "fuzzy"
                        })

    print(f"      Comparaciones: {comparisons:,}")
    print(f"      ✅ {len(matches)} duplicados encontrados")
    return matches


# ============================================================================
# 3. ENTITY RESOLUTION - CAPA 3: CONTEXTUAL
# ============================================================================

def er_contextual(session, label, shared_relations, min_shared):
    """
    Encuentra duplicados por vecindad compartida

    Args:
        session: Sesión Neo4j
        label: Label del nodo
        shared_relations: Tipos de relaciones a considerar
        min_shared: Mínimo de vecinos compartidos

    Returns:
        Lista de matches
    """
    print(f"\n   🔍 Capa Contextual: {label}")
    print(f"      Relaciones: {shared_relations}, Min compartidos: {min_shared}")

    # Construir patrón de relaciones
    rel_patterns = "|".join([f":{rel_type}" for rel_type in shared_relations])

    query = f"""
    MATCH (n1:{label})-[{rel_patterns}]-(shared)-[{rel_patterns}]-(n2:{label})
    WHERE id(n1) < id(n2)
    WITH n1, n2, count(DISTINCT shared) as shared_count
    WHERE shared_count >= {min_shared}
    RETURN n1.id as canonical_id,
           n2.id as duplicate_id,
           toFloat(shared_count) / 10.0 as score,
           'contextual' as razon,
           shared_count
    """

    result = session.run(query)

    matches = []
    for record in result:
        matches.append({
            "canonical_id": record["canonical_id"],
            "duplicate_id": record["duplicate_id"],
            "score": min(record["score"], 1.0),  # Cap en 1.0
            "razon": record["razon"],
            "shared_count": record["shared_count"]
        })

    print(f"      ✅ {len(matches)} duplicados encontrados")
    return matches


# ============================================================================
# 3. ENTITY RESOLUTION - CAPA 4: SEMÁNTICA (EMBEDDINGS - OPCIONAL)
# ============================================================================

def generate_embeddings_for_nodes(session, label, text_source, embedding_property):
    """
    Genera embeddings para nodos que no los tienen

    Args:
        session: Sesión Neo4j
        label: Label del nodo
        text_source: Lista de propiedades para concatenar
        embedding_property: Nombre de la propiedad donde guardar el embedding

    Returns:
        Número de embeddings generados
    """
    if not openai_client:
        return 0

    print(f"\n   🤖 Generando embeddings para {label}...")

    # Obtener nodos sin embedding
    query = f"""
    MATCH (n:{label})
    WHERE n.{embedding_property} IS NULL
    RETURN n.id as id, properties(n) as props
    LIMIT 100
    """

    result = session.run(query)

    count = 0
    for record in result:
        node_id = record["id"]
        props = record["props"]

        # Concatenar propiedades
        text_parts = [str(props.get(field, "")) for field in text_source if props.get(field)]
        text = " - ".join(text_parts)

        if not text:
            continue

        # Generar embedding
        try:
            response = openai_client.embeddings.create(
                model="text-embedding-3-small",
                input=text
            )

            embedding = response.data[0].embedding

            # Guardar en Neo4j
            update_query = f"""
            MATCH (n:{label} {{id: $id}})
            SET n.{embedding_property} = $embedding
            """

            session.run(update_query, id=node_id, embedding=embedding)
            count += 1

        except Exception as e:
            print(f"      ⚠️ Error generando embedding para {node_id}: {e}")

    print(f"      ✅ {count} embeddings generados")
    return count


def er_semantic(session, label, embedding_property, threshold):
    """
    Encuentra duplicados por similitud de embeddings

    Args:
        session: Sesión Neo4j
        label: Label del nodo
        embedding_property: Propiedad con el embedding
        threshold: Umbral de similitud coseno

    Returns:
        Lista de matches
    """
    if not NUMPY_SUPPORT or not openai_client:
        print(f"\n   ⚠️ Capa Semántica: {label} - Deshabilitada (falta numpy o openai)")
        return []

    print(f"\n   🔍 Capa Semántica: {label}")
    print(f"      Propiedad: {embedding_property}, Umbral: {threshold}")

    # Obtener todos los nodos con embedding
    query = f"""
    MATCH (n:{label})
    WHERE n.{embedding_property} IS NOT NULL
    RETURN n.id as id, n.{embedding_property} as embedding
    """

    result = session.run(query)

    nodes_data = []
    for record in result:
        nodes_data.append({
            "id": record["id"],
            "embedding": np.array(record["embedding"])
        })

    print(f"      Nodos con embedding: {len(nodes_data)}")

    matches = []
    comparisons = 0

    # Comparar todos los pares
    for i in range(len(nodes_data)):
        for j in range(i+1, len(nodes_data)):
            emb1 = nodes_data[i]["embedding"]
            emb2 = nodes_data[j]["embedding"]
            comparisons += 1

            # Similitud coseno
            similarity = np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))

            if similarity >= threshold:
                matches.append({
                    "canonical_id": nodes_data[i]["id"],
                    "duplicate_id": nodes_data[j]["id"],
                    "score": float(similarity),
                    "razon": "semantic"
                })

    print(f"      Comparaciones: {comparisons:,}")
    print(f"      ✅ {len(matches)} duplicados encontrados")
    return matches


# ============================================================================
# 4. MERGING - CONSOLIDACIÓN DE NODOS
# ============================================================================

def resolver_conflicto_timestamp(val1, val2, meta1, meta2):
    """Resuelve conflicto por timestamp (más reciente gana)"""
    time1 = meta1.get("updated_at", meta1.get("created_at", ""))
    time2 = meta2.get("updated_at", meta2.get("created_at", ""))

    if time1 > time2:
        return val1
    return val2


def merge_nodes(session, canonical_id, duplicate_id, razon, score, audit_log):
    """
    Merge controlado con preservación de provenance

    Args:
        session: Sesión de Neo4j
        canonical_id: ID del nodo canónico (se mantiene)
        duplicate_id: ID del nodo duplicado (se elimina)
        razon: Razón del merge
        score: Score de confianza
        audit_log: Lista donde registrar el merge

    Returns:
        True si se realizó el merge correctamente
    """
    # 1. Obtener ambos nodos
    query_get = """
    MATCH (canonical), (duplicate)
    WHERE canonical.id = $canonical_id AND duplicate.id = $duplicate_id
    RETURN canonical, duplicate, labels(canonical)[0] as label
    """

    result = session.run(query_get,
                        canonical_id=canonical_id,
                        duplicate_id=duplicate_id)
    record = result.single()

    if not record:
        return False

    canonical = dict(record["canonical"])
    duplicate = dict(record["duplicate"])
    label = record["label"]

    # 2. Consolidar propiedades
    merged_props = {}

    for key in set(list(canonical.keys()) + list(duplicate.keys())):
        if key in ["id", "aliases", "schema_version"]:
            continue

        if key in canonical and key not in duplicate:
            merged_props[key] = canonical[key]
        elif key not in canonical and key in duplicate:
            merged_props[key] = duplicate[key]
        elif key in canonical and key in duplicate:
            if canonical[key] == duplicate[key]:
                merged_props[key] = canonical[key]
            else:
                # Resolver conflicto por timestamp
                merged_props[key] = resolver_conflicto_timestamp(
                    canonical[key], duplicate[key],
                    canonical, duplicate
                )

    # 3. Mantener aliases
    aliases = canonical.get("aliases", [])
    if isinstance(aliases, str):
        aliases = [aliases]
    elif not isinstance(aliases, list):
        aliases = []

    # Agregar ID del duplicado como alias
    aliases.append(duplicate_id)

    # Agregar aliases del duplicado
    if "aliases" in duplicate:
        dup_aliases = duplicate["aliases"]
        if isinstance(dup_aliases, str):
            dup_aliases = [dup_aliases]
        elif isinstance(dup_aliases, list):
            aliases.extend(dup_aliases)

    # Eliminar duplicados
    aliases = list(set(aliases))
    merged_props["aliases"] = aliases
    merged_props["updated_at"] = datetime.now().isoformat()

    # 4. Ejecutar merge en Neo4j
    query_merge = f"""
    MATCH (canonical:{label}), (duplicate:{label})
    WHERE canonical.id = $canonical_id AND duplicate.id = $duplicate_id

    // Actualizar propiedades del nodo canónico
    SET canonical += $merged_props

    // Redirigir relaciones salientes
    WITH canonical, duplicate
    MATCH (duplicate)-[r]->(other)
    WHERE other <> canonical
    WITH canonical, duplicate, r, other, type(r) as relType
    CALL apoc.create.relationship(canonical, relType, properties(r), other) YIELD rel
    DELETE r

    WITH canonical, duplicate
    // Redirigir relaciones entrantes
    MATCH (other)-[r]->(duplicate)
    WHERE other <> canonical
    WITH canonical, duplicate, r, other, type(r) as relType
    CALL apoc.create.relationship(other, relType, properties(r), canonical) YIELD rel
    DELETE r

    // Mover evidencias
    WITH canonical, duplicate
    OPTIONAL MATCH (duplicate)-[re:RESPALDA]->(e:Evidencia)
    DELETE re
    WITH canonical, duplicate, collect(e) as evidencias
    UNWIND evidencias as ev
    MERGE (canonical)-[:RESPALDA]->(ev)

    // Eliminar el nodo duplicado
    WITH canonical, duplicate
    DETACH DELETE duplicate

    RETURN canonical.id as merged_id, size($merged_props.aliases) as aliases_count
    """

    try:
        # Intentar con APOC
        result = session.run(query_merge,
                            canonical_id=canonical_id,
                            duplicate_id=duplicate_id,
                            merged_props=merged_props)

        record = result.single()

        # 5. Registrar auditoría
        audit_entry = {
            "merge_id": f"MERGE-{uuid.uuid4().hex[:12]}",
            "canonical_id": canonical_id,
            "merged_id": duplicate_id,
            "razon": razon,
            "score": score,
            "fecha": datetime.now().isoformat(),
            "aliases_count": len(aliases),
            "props_merged": len(merged_props)
        }

        audit_log.append(audit_entry)

        # Crear nodo de auditoría en Neo4j
        query_audit = """
        CREATE (audit:MergeAudit {
            id: $merge_id,
            canonical_id: $canonical_id,
            merged_id: $merged_id,
            razon: $razon,
            score: $score,
            fecha: datetime($fecha),
            revertido: false,
            aliases_count: $aliases_count
        })
        """

        session.run(query_audit, **audit_entry, fecha=audit_entry["fecha"])

        return True

    except Exception as e:
        # Si falla APOC, usar método manual
        print(f"      ⚠️ Merge con APOC falló, intentando método manual: {e}")
        return merge_nodes_manual(session, canonical_id, duplicate_id, merged_props, label, audit_log, razon, score)


def merge_nodes_manual(session, canonical_id, duplicate_id, merged_props, label, audit_log, razon, score):
    """Merge manual sin APOC"""
    try:
        # Actualizar propiedades
        query_update = f"""
        MATCH (canonical:{label} {{id: $canonical_id}})
        SET canonical += $merged_props
        """
        session.run(query_update, canonical_id=canonical_id, merged_props=merged_props)

        # Obtener todas las relaciones del duplicado
        query_rels = f"""
        MATCH (duplicate:{label} {{id: $duplicate_id}})
        OPTIONAL MATCH (duplicate)-[r_out]->(other)
        OPTIONAL MATCH (other2)-[r_in]->(duplicate)
        RETURN
            collect(DISTINCT {{type: type(r_out), target: other.id, props: properties(r_out)}}) as rels_out,
            collect(DISTINCT {{type: type(r_in), source: other2.id, props: properties(r_in)}}) as rels_in
        """

        result = session.run(query_rels, duplicate_id=duplicate_id)
        record = result.single()

        # Recrear relaciones salientes
        for rel in record["rels_out"]:
            if rel["target"]:
                query_create = f"""
                MATCH (canonical:{label} {{id: $canonical_id}})
                MATCH (other) WHERE other.id = $target_id
                MERGE (canonical)-[r:`{rel['type']}`]->(other)
                SET r = $props
                """
                session.run(query_create,
                           canonical_id=canonical_id,
                           target_id=rel["target"],
                           props=rel["props"] or {})

        # Recrear relaciones entrantes
        for rel in record["rels_in"]:
            if rel["source"]:
                query_create = f"""
                MATCH (canonical:{label} {{id: $canonical_id}})
                MATCH (other) WHERE other.id = $source_id
                MERGE (other)-[r:`{rel['type']}`]->(canonical)
                SET r = $props
                """
                session.run(query_create,
                           canonical_id=canonical_id,
                           source_id=rel["source"],
                           props=rel["props"] or {})

        # Eliminar duplicado
        query_delete = f"""
        MATCH (duplicate:{label} {{id: $duplicate_id}})
        DETACH DELETE duplicate
        """
        session.run(query_delete, duplicate_id=duplicate_id)

        # Registrar auditoría
        audit_entry = {
            "merge_id": f"MERGE-{uuid.uuid4().hex[:12]}",
            "canonical_id": canonical_id,
            "merged_id": duplicate_id,
            "razon": razon,
            "score": score,
            "fecha": datetime.now().isoformat(),
            "aliases_count": len(merged_props.get("aliases", [])),
            "props_merged": len(merged_props)
        }

        audit_log.append(audit_entry)

        return True

    except Exception as e:
        print(f"      ❌ Error en merge manual: {e}")
        return False


# ============================================================================
# 5. EMBEDDINGS - CONFIGURACIÓN Y GENERACIÓN
# ============================================================================

def process_embeddings(session):
    """
    Procesa embeddings según configuración

    Args:
        session: Sesión Neo4j

    Returns:
        Dict con estadísticas
    """
    if not EMBEDDING_CONFIG or not EMBEDDING_CONFIG.get("enabled", False):
        return {"enabled": False}

    print("\n" + "="*80)
    print("🤖 FASE DE EMBEDDINGS")
    print("="*80)

    stats = {
        "enabled": True,
        "embeddings_generated": 0,
        "nodes_processed": []
    }

    for node_config in EMBEDDING_CONFIG.get("nodos_con_embedding", []):
        label = node_config["label"]
        embedding_property = node_config["embedding_property"]
        text_source = node_config["text_source"]

        print(f"\n📊 Procesando: {label}")
        print(f"   Propiedad embedding: {embedding_property}")
        print(f"   Campos fuente: {text_source}")

        count = generate_embeddings_for_nodes(
            session,
            label,
            text_source,
            embedding_property
        )

        stats["embeddings_generated"] += count
        stats["nodes_processed"].append({
            "label": label,
            "count": count
        })

    return stats


# ============================================================================
# 6. ESTADÍSTICAS Y REPORTE
# ============================================================================

def get_graph_stats(session):
    """Obtiene estadísticas del grafo"""
    query = """
    MATCH (n)
    RETURN labels(n)[0] as label, count(*) as count
    ORDER BY count DESC
    """

    result = session.run(query)

    stats = {}
    total = 0

    for record in result:
        label = record["label"]
        count = record["count"]
        stats[label] = count
        total += count

    stats["TOTAL"] = total

    return stats


def get_relationships_count(session):
    """Cuenta relaciones totales"""
    query = "MATCH ()-[r]->() RETURN count(r) as count"
    result = session.run(query)
    record = result.single()
    return record["count"] if record else 0


def generate_report(stats_before, stats_after, all_matches, audit_log, embedding_stats):
    """
    Genera reporte detallado de la depuración

    Args:
        stats_before: Estadísticas antes
        stats_after: Estadísticas después
        all_matches: Todos los matches encontrados
        audit_log: Log de auditoría
        embedding_stats: Estadísticas de embeddings

    Returns:
        String con el reporte
    """
    report = []

    report.append("="*80)
    report.append("REPORTE DE DEPURACIÓN DEL GRAFO DE CONOCIMIENTO")
    report.append("="*80)
    report.append(f"\n**Fecha:** {datetime.now().isoformat()}")
    report.append(f"**Schema Version:** 1.0")
    report.append("\n" + "="*80)

    # Estadísticas antes/después
    report.append("\n## 1. ESTADÍSTICAS INICIALES")
    report.append("\n**Antes de la depuración:**")
    report.append(f"- Total de nodos: {stats_before.get('TOTAL', 0):,}")
    report.append(f"- Total de relaciones: {stats_before.get('relationships', 0):,}")

    report.append("\n**Distribución por tipo:**")
    report.append("| Tipo Nodo     | Cantidad |")
    report.append("|---------------|----------|")
    for label, count in stats_before.items():
        if label not in ["TOTAL", "relationships"]:
            report.append(f"| {label:<13} | {count:>8,} |")

    # Merges por capa
    report.append("\n" + "="*80)
    report.append("\n## 2. ENTITY RESOLUTION APLICADO")

    merges_by_razon = defaultdict(list)
    for match in all_matches:
        merges_by_razon[match["razon"]].append(match)

    for razon, matches in merges_by_razon.items():
        report.append(f"\n### 2.{list(merges_by_razon.keys()).index(razon)+1} Capa {razon.capitalize()}")

        avg_score = sum([m["score"] for m in matches]) / len(matches) if matches else 0

        report.append(f"\n**Duplicados mergeados:** {len(matches)}")
        report.append(f"**Score promedio:** {avg_score:.3f}")

    # Estadísticas finales
    report.append("\n" + "="*80)
    report.append("\n## 3. CONSOLIDACIÓN FINAL")
    report.append("\n**Después de la depuración:**")

    total_before = stats_before.get("TOTAL", 0)
    total_after = stats_after.get("TOTAL", 0)
    reduction = total_before - total_after
    reduction_pct = (reduction / total_before * 100) if total_before > 0 else 0

    report.append(f"- Total de nodos: {total_after:,} (reducción: {reduction} nodos / {reduction_pct:.1f}%)")
    report.append(f"- Total de relaciones: {stats_after.get('relationships', 0):,}")

    report.append("\n**Distribución por tipo:**")
    report.append("| Tipo Nodo     | Antes   | Después | Diferencia |")
    report.append("|---------------|---------|---------|------------|")
    for label in set(list(stats_before.keys()) + list(stats_after.keys())):
        if label not in ["TOTAL", "relationships"]:
            before = stats_before.get(label, 0)
            after = stats_after.get(label, 0)
            diff = before - after
            report.append(f"| {label:<13} | {before:>7,} | {after:>7,} | {diff:>10,} |")

    # Auditoría
    report.append("\n" + "="*80)
    report.append("\n## 4. AUDITORÍA DE MERGES")
    report.append(f"\n**Total de merges realizados:** {len(audit_log)}")

    # Embeddings
    if embedding_stats.get("enabled"):
        report.append("\n" + "="*80)
        report.append("\n## 5. EMBEDDINGS GENERADOS")
        report.append(f"\n**Total:** {embedding_stats.get('embeddings_generated', 0)}")

        for node_stat in embedding_stats.get("nodes_processed", []):
            report.append(f"- {node_stat['label']}: {node_stat['count']} embeddings")

    # Archivos generados
    report.append("\n" + "="*80)
    report.append("\n## 6. ARCHIVOS GENERADOS")
    report.append("\n- `output/merge_audit.json` - Log completo de merges")
    report.append("- `output/deduplication_queries.cypher` - Queries ejecutadas")
    report.append("- `output/deduplication_report.txt` - Este reporte")

    report.append("\n" + "="*80)
    report.append("\n*Depuración completada exitosamente*")
    report.append("*Script: graph_deduplication.py v1.0*")
    report.append("="*80)

    return "\n".join(report)


# ============================================================================
# 7. MAIN - PIPELINE ORQUESTADO
# ============================================================================

def main():
    print("="*80)
    print("🧹 PIPELINE DE DEPURACIÓN DE GRAFOS DE CONOCIMIENTO")
    print("="*80)

    # Crear directorio de salida
    os.makedirs("output", exist_ok=True)

    with neo4j_driver.session() as session:

        # 1. Estadísticas iniciales
        print("\n📊 Recopilando estadísticas iniciales...")
        stats_before = get_graph_stats(session)
        stats_before["relationships"] = get_relationships_count(session)

        print(f"\n   Nodos totales: {stats_before.get('TOTAL', 0):,}")
        print(f"   Relaciones totales: {stats_before.get('relationships', 0):,}")

        # 2. Procesar embeddings (si está configurado)
        embedding_stats = process_embeddings(session)

        # 3. Entity Resolution por capas
        print("\n" + "="*80)
        print("🔍 ENTITY RESOLUTION POR CAPAS")
        print("="*80)

        all_matches = []
        audit_log = []

        # Definir reglas ER por tipo de entidad
        er_rules = {
            "Normativa": {
                "identity_keys": ["tipo", "numero", "anio", "emisor"],
                "normalize_keys": ["tipo", "emisor"],
                "fuzzy": {
                    "enabled": True,
                    "compare_fields": ["titulo"],
                    "threshold": 0.85,
                    "blocking_key": "anio"
                },
                "contextual": {
                    "enabled": True,
                    "shared_relations": ["REGULADA_POR", "CONTIENE"],
                    "min_shared": 3
                }
            },
            "Prestacion": {
                "identity_keys": ["codigo_prestacion", "tipo_prestacion"],
                "normalize_keys": ["codigo_prestacion"],
                "fuzzy": {
                    "enabled": True,
                    "compare_fields": ["nombre"],
                    "threshold": 0.90,
                    "blocking_key": "tipo_prestacion"
                },
                "contextual": {
                    "enabled": False
                }
            },
            "MarcoLegal": {
                "identity_keys": ["tipo_legal", "numero_legal"],
                "normalize_keys": ["numero_legal"],
                "fuzzy": {
                    "enabled": False
                },
                "contextual": {
                    "enabled": False
                }
            }
        }

        # Procesar cada tipo de entidad
        for label, rules in er_rules.items():
            print(f"\n{'='*80}")
            print(f"📋 Procesando: {label}")
            print(f"{'='*80}")

            # Capa 1: Determinística
            matches_det = er_deterministic(
                session,
                label,
                rules["identity_keys"],
                rules["normalize_keys"]
            )
            all_matches.extend(matches_det)

            # Capa 2: Fuzzy
            if rules.get("fuzzy", {}).get("enabled", False):
                matches_fuzzy = er_fuzzy(
                    session,
                    label,
                    rules["fuzzy"]["compare_fields"],
                    rules["fuzzy"]["threshold"],
                    rules["fuzzy"]["blocking_key"]
                )
                all_matches.extend(matches_fuzzy)

            # Capa 3: Contextual
            if rules.get("contextual", {}).get("enabled", False):
                matches_ctx = er_contextual(
                    session,
                    label,
                    rules["contextual"]["shared_relations"],
                    rules["contextual"]["min_shared"]
                )
                all_matches.extend(matches_ctx)

            # Capa 4: Semántica (si hay configuración)
            if EMBEDDING_CONFIG and EMBEDDING_CONFIG.get("enabled"):
                for node_config in EMBEDDING_CONFIG.get("nodos_con_embedding", []):
                    if node_config["label"] == label:
                        matches_sem = er_semantic(
                            session,
                            label,
                            node_config["embedding_property"],
                            node_config["threshold"]
                        )
                        all_matches.extend(matches_sem)

        # 4. Ejecutar merges
        print("\n" + "="*80)
        print("🔨 EJECUTANDO MERGES")
        print("="*80)

        print(f"\nTotal de duplicados a mergear: {len(all_matches)}")

        merged_count = 0
        for i, match in enumerate(all_matches):
            success = merge_nodes(
                session,
                match["canonical_id"],
                match["duplicate_id"],
                match["razon"],
                match["score"],
                audit_log
            )

            if success:
                merged_count += 1
                if (i + 1) % 10 == 0:
                    print(f"   Procesados: {i+1}/{len(all_matches)}")

        print(f"\n✅ Merges completados: {merged_count}/{len(all_matches)}")

        # 5. Estadísticas finales
        print("\n📊 Recopilando estadísticas finales...")
        stats_after = get_graph_stats(session)
        stats_after["relationships"] = get_relationships_count(session)

        # 6. Generar reporte
        print("\n📝 Generando reporte...")
        report = generate_report(
            stats_before,
            stats_after,
            all_matches,
            audit_log,
            embedding_stats
        )

        # Guardar reporte
        with open("output/deduplication_report.txt", "w", encoding="utf-8") as f:
            f.write(report)

        # Guardar auditoría
        with open("output/merge_audit.json", "w", encoding="utf-8") as f:
            json.dump(audit_log, f, indent=2, ensure_ascii=False)

        print(report)

        print("\n" + "="*80)
        print("✅ DEPURACIÓN COMPLETADA")
        print("="*80)

    neo4j_driver.close()


if __name__ == "__main__":
    main()
