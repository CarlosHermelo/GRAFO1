from dotenv import load_dotenv
load_dotenv()

import os
import json
from openai import OpenAI
from neo4j import GraphDatabase

# ============================
# CLIENTE OPENAI
# ============================
API_KEY = os.getenv("OPENAI_API_KEY")
if not API_KEY:
    raise ValueError("OPENAI_API_KEY no está configurada en .env")

client = OpenAI(api_key=API_KEY)

# ============================
# CLIENTE NEO4J
# ============================
URI = "neo4j+s://b0df6e44.databases.neo4j.io"
USER = "neo4j"
PASSWORD = os.getenv("NEO4J_PASSWORD")

if not PASSWORD:
    raise ValueError("NEO4J_PASSWORD no está configurada en .env")

driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))

# ============================
# CAMPOS PERMITIDOS (VALIDACIÓN REAL)
# ============================
CAMPOS_VALIDOS = {
    "Afiliado": ["id_afiliado", "nombre", "dni", "telefono", "email"],
    "Prestador": ["id_prestador", "nombre", "especialidad", "contacto"],
    "Proveedor": ["id_proveedor", "nombre", "tipo_insumo", "contacto"],
    "Protesis": ["id_protesis", "codigo_pami", "descripcion", "tipo"],
    "Tramite": ["id_tramite", "id_afiliado", "id_prestador", "id_proveedor", "id_protesis", "estado"],
    "Incumplimiento": ["id_incumplimiento", "id_tramite", "parte_responsable", "descripcion", "penalidad_aplicable"],
    "Mensaje": ["id_mensaje", "id_tramite", "remitente", "destinatario", "contenido"],
    "Notificacion_interna": ["id_notificacion", "id_tramite", "tipo", "descripcion"]
}

CAMPOS_TODOS = {c for cols in CAMPOS_VALIDOS.values() for c in cols}

ESQUEMA = """
Tramite -[:TRAMITE_DE]-> Afiliado
Tramite -[:GESTIONADO_POR]-> Prestador
Tramite -[:ASIGNADO_A]-> Proveedor
Tramite -[:SOLICITA]-> Protesis
Incumplimiento -[:DETECTADO_EN]-> Tramite
Mensaje -[:ASOCIADO_A]-> Tramite
Notificacion_interna -[:RELACIONADA_CON]-> Tramite
"""


# ==========================================================
# AGENTE 1 — Detectar intención del usuario
# ==========================================================
def detectar_intencion(pregunta):
    prompt = f"""
    Devolvé SOLO un JSON válido con este formato:
    {{
      "tipo": "consulta" | "comparacion" | "estadistica",
      "entidad": "Prestador" | "Proveedor" | "Tramite" | "Protesis" | "Afiliado",
      "filtro": "<texto>"
    }}

    No agregues nada fuera del JSON.

    Pregunta: "{pregunta}"
    """

    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Devolvés SOLO JSON."},
            {"role": "user", "content": prompt}
        ]
    )

    contenido = resp.choices[0].message.content.strip()

    if contenido.startswith("```"):
        contenido = contenido.replace("```json", "").replace("```", "").strip()

    if not contenido.startswith("{"):
        raise ValueError(f"JSON inválido: {contenido}")

    return json.loads(contenido)


# ==========================================================
# AGENTE 2 — Generar Cypher
# ==========================================================
def generar_cypher(pregunta, intento):
    prompt = f"""
    Generá una consulta Cypher válida basada estrictamente en el esquema del grafo.
    Nunca inventes propiedades nuevas. Usá únicamente estas propiedades permitidas:
    {list(CAMPOS_TODOS)}

    CONTEXTO DEL DOMINIO:
    Este grafo describe la gestión de prótesis:
    - Los proveedores entregan insumos.
    - Los prestadores gestionan trámites.
    - Un incumplimiento indica un problema, retraso, falla, demora o conflicto en el trámite.
    - Por lo tanto:
        * "problemas", "retrasos", "demoras", "falla", "conflicto", "entrega tardía"
          se interpretan como Incumplimientos asociados al Trámite.
        * Para saber qué proveedor tiene más problemas:
          contar Incumplimientos conectados a Trámites asignados a un Proveedor.
        * Para saber qué prestador tiene más problemas:
          contar Incumplimientos conectados a Trámites gestionados por ese Prestador.

    ESQUEMA:
    {ESQUEMA}

    REGLAS ESTRICTAS:
    - Si la pregunta menciona “problemas”, “retrasos”, “demoras”, “fallas”, “conflictos”,
      entonces la métrica es COUNT(i) donde i es Incumplimiento.
    - La relación entre Proveedor y Incumplimiento es:
      (Proveedor)<-[:ASIGNADO_A]-(Tramite)<-[:DETECTADO_EN]-(Incumplimiento)
    - La relación entre Prestador y Incumplimiento es:
      (Prestador)<-[:GESTIONADO_POR]-(Tramite)<-[:DETECTADO_EN]-(Incumplimiento)

    FORMATO DE RESPUESTA:
    Devolvé SOLO JSON válido:
    {{
        "cypher": "<query>",
        "params": {{}}
    }}

    Intención interpretada:
    {json.dumps(intento, ensure_ascii=False)}

    Pregunta original:
    "{pregunta}"
    """

    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Generás SOLO JSON con un campo 'cypher'."},
            {"role": "user", "content": prompt}
        ]
    )

    contenido = resp.choices[0].message.content.strip()
    if contenido.startswith("```"):
        contenido = contenido.replace("```json", "").replace("```", "").strip()

    if not contenido.startswith("{"):
        raise ValueError(f"JSON inválido: {contenido}")

    data = json.loads(contenido)
    query = data["cypher"]

    # VALIDACIÓN DE PROPIEDADES
    tokens = query.replace("(", " ").replace(")", " ").replace(",", " ").replace("{", " ").replace("}", " ").split()
    for tok in tokens:
        if "." in tok:
            _, prop = tok.split(".", 1)
            if prop not in CAMPOS_TODOS:
                raise ValueError(f"El Cypher usa una propiedad inválida: {prop}")

    return data


# ==========================================================
# Validar Cypher
# ==========================================================
def validar_cypher(query):
    q = query.upper()
    if "MATCH" not in q:
        return False
    if ";" in query:
        return False
    return True


# ==========================================================
# Ejecutar Cypher
# ==========================================================
def ejecutar(query, params):
    with driver.session() as session:
        result = session.run(query, params)
        return [r.data() for r in result]


# ==========================================================
# AGENTE 3 — Resumen del resultado
# ==========================================================
def resumir_resultado(pregunta, resultado):
    if not resultado:
        return "No encontré resultados en el grafo."

    prompt = f"""
    Convertí el siguiente resultado en una respuesta clara:

    Pregunta: {pregunta}
    Resultado: {resultado}
    """

    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Resumís resultados de grafos."},
            {"role": "user", "content": prompt}
        ]
    )

    return resp.choices[0].message.content.strip()


# ==========================================================
# ASISTENTE COMPLETO
# ==========================================================
def preguntar_al_grafo(pregunta):
    intento = detectar_intencion(pregunta)
    cy = generar_cypher(pregunta, intento)

    query = cy["cypher"]
    params = cy.get("params", {})

    if not validar_cypher(query):
        return "La consulta generada no es válida."

    datos = ejecutar(query, params)
    return resumir_resultado(pregunta, datos)


# ==========================================================
# EJEMPLO
# ==========================================================
if __name__ == "__main__":
    pregunta = "¿Qué tipo de prótesis registra la mayor tasa de problemas por trámite?"
    print(preguntar_al_grafo(pregunta))
