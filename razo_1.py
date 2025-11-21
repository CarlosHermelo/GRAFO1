# razonamiento_causa_raiz.py
from neo4j import GraphDatabase

# ===========================================
# 1. Conexión (reutiliza tu configuración)
# ===========================================
URI = "neo4j+s://b0df6e44.databases.neo4j.io"
USER = "neo4j"
PASSWORD = "NQkXw6G9S7jO8wQXQIRpd5BX-g2t_bEvXweJVPSWO1g"

driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))

# ===========================================
# 2. CONSULTAS ESTÁNDAR — FRECUENCIA
# ===========================================
def prestadores_con_mas_incumplimientos():
    query = """
    MATCH (p:Prestador)<-[:GESTIONADO_POR]-(t:Tramite)<-[:DETECTADO_EN]-(i:Incumplimiento)
    RETURN p.nombre AS prestador, count(i) AS problemas
    ORDER BY problemas DESC
    """
    with driver.session() as session:
        return session.run(query).data()

def proveedores_con_mas_probemas():
    query = """
    MATCH (prov:Proveedor)<-[:ASIGNADO_A]-(t:Tramite)<-[:DETECTADO_EN]-(i:Incumplimiento)
    RETURN prov.nombre AS proveedor, count(i) AS problemas
    ORDER BY problemas DESC
    """
    with driver.session() as session:
        return session.run(query).data()

def protesis_con_mas_fallos():
    query = """
    MATCH (pr:Protesis)<-[:SOLICITA]-(t:Tramite)<-[:DETECTADO_EN]-(i:Incumplimiento)
    RETURN pr.descripcion AS protesis, count(i) AS problemas
    ORDER BY problemas DESC
    """
    with driver.session() as session:
        return session.run(query).data()

# ===========================================
# 3. RUTAS TÍPICAS HACIA INCUMPLIMIENTOS
# ===========================================
def rutas_hacia_incumplimiento():
    query = """
    MATCH p = (t:Tramite)-[:ASOCIADO_A|RELACIONADA_CON|DETECTADO_EN*]->(i:Incumplimiento)
    RETURN t.id_tramite AS tramite, nodes(p) AS nodos, relationships(p) AS relaciones
    LIMIT 20
    """
    with driver.session() as session:
        return session.run(query).data()

def cantidad_mensajes_antes_de_fallo():
    query = """
    MATCH (m:Mensaje)-[:ASOCIADO_A]->(t:Tramite)<-[:DETECTADO_EN]-(i:Incumplimiento)
    RETURN t.id_tramite AS tramite, count(m) AS mensajes_previos
    ORDER BY mensajes_previos DESC
    """
    with driver.session() as session:
        return session.run(query).data()

# ===========================================
# 4. ESTRUCTURA DEL GRAFO — NODOS CRÍTICOS
# ===========================================
# Neo4j no tiene algoritmos de centralidad por defecto en Cypher puro:
# si tu instancia tiene APOC/Graph Data Science, activo esto:
def hubs_por_conectividad():
    query = """
    MATCH (n)-[r]->()
    RETURN labels(n)[0] AS entidad, n.nombre AS nombre, count(r) AS conexiones
    ORDER BY conexiones DESC
    LIMIT 20
    """
    with driver.session() as session:
        return session.run(query).data()

# ===========================================
# 5. ANÁLISIS EXPLICATIVO DE CAUSAS RAÍZ
# ===========================================
def causas_raiz_probables():
    resultados = {}

    resultados["prestadores"] = prestadores_con_mas_incumplimientos()
    resultados["proveedores"] = proveedores_con_mas_probemas()
    resultados["protesis"] = protesis_con_mas_fallos()
    resultados["mensajes_previos"] = cantidad_mensajes_antes_de_fallo()
    resultados["hubs"] = hubs_por_conectividad()

    return resultados

# ===========================================
# 6. RESUMEN DE CAUSA RAIZ EN TEXTO
# ===========================================
def resumen_causa_raiz():
    data = causas_raiz_probables()

    texto = []
    texto.append("=== ANÁLISIS DE CAUSAS RAÍZ ===")

    # Prestadores críticos
    if data["prestadores"]:
        texto.append("\nPrestadores más asociados a incumplimientos:")
        for r in data["prestadores"][:5]:
            texto.append(f"- {r['prestador']}: {r['problemas']} problemas")

    # Proveedores críticos
    if data["proveedores"]:
        texto.append("\nProveedores más problemáticos:")
        for r in data["proveedores"][:5]:
            texto.append(f"- {r['proveedor']}: {r['problemas']} problemas")

    # Prótesis asociadas a problemas
    if data["protesis"]:
        texto.append("\nTipos de prótesis con más fallos:")
        for r in data["protesis"][:5]:
            texto.append(f"- {r['protesis']}: {r['problemas']} problemas")

    # Hubs críticos
    if data["hubs"]:
        texto.append("\nNodos más conectados (cuellos de botella):")
        for r in data["hubs"][:5]:
            texto.append(f"- {r['nombre']} ({r['entidad']}): {r['conexiones']} conexiones")

    return "\n".join(texto)

# ===========================================
# 7. Ejecución directa
# ===========================================
if __name__ == "__main__":
    print(resumen_causa_raiz())
