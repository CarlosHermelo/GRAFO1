import json
import os
from neo4j import GraphDatabase
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# === Configuración OpenAI ===
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# === Config Neo4j ===
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))


# ============================================================
# 1. Genera Cypher conceptual a partir de la pregunta del usuario
# ============================================================
def generar_cypher_semantico(pregunta):
    prompt = f"""
Sos un analizador semántico de grafos.
Debés generar EXCLUSIVAMENTE una consulta Cypher que busque nodos Subtipo
a partir de las ideas presentes en la pregunta del usuario.

La búsqueda debe ser:
- basada en conceptos
- sin igualdad exacta
- usando coincidencias en los textos de nombre, copete y consiste

Esquema disponible:
(Subtipo {{nombre, copete, consiste}})

Pregunta del usuario:
\"\"\"{pregunta}\"\"\"


La consulta debe tener esta estructura:

MATCH (s:Subtipo)
WHERE s.nombre =~ '(?i).*<palabra o concepto>.*'
   OR s.copete =~ '(?i).*<palabra o concepto>.*'
   OR s.consiste =~ '(?i).*<palabra o concepto>.*'
RETURN s LIMIT 20

No inventes propiedades.

Devolvé solo la consulta Cypher, sin comillas ni markdown.
"""

    respuesta = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )

    return respuesta.choices[0].message.content.strip()


# ============================================================
# 2. Ejecutar consulta en Neo4j
# ============================================================
def ejecutar_cypher(query):
    with driver.session() as session:
        result = session.run(query)
        return list(result)


# ============================================================
# 3. Síntesis final de los textos encontrados
# ============================================================
def sintetizar_respuesta(pregunta, resultados):
    textos = []

    for r in resultados:
        nodo = r["s"]
        txt = f"Nombre: {nodo.get('nombre','')}\nCopete: {nodo.get('copete','')}\nConsiste: {nodo.get('consiste','')}"
        textos.append(txt)

    texto_grafo = "\n\n".join(textos)

    prompt = f"""
Sos un experto en normativa PAMI.
El usuario hizo esta pregunta:
\"\"\"{pregunta}\"\"\".

Tenés estos datos provenientes del grafo:
\"\"\"{texto_grafo}\"\"\".

A partir de esa información:
- Respondé de forma clara y directa.
- Si corresponde la afiliación, explicalo.
- Si no corresponde, explicalo.
- Mostrá el subtipo aplicable.
- No inventes nada.

Respuesta:
"""

    respuesta = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )

    return respuesta.choices[0].message.content.strip()


# ============================================================
# 4. Función final: preguntar → grafo → respuesta natural
# ============================================================
def preguntar_normativa(pregunta):
    print("\n=== PREGUNTA ===")
    print(pregunta)

    print("\n=== Generando Cypher semántico… ===")
    cypher = generar_cypher_semantico(pregunta)
    print(cypher)

    print("\n=== Ejecutando consulta… ===")
    resultados = ejecutar_cypher(cypher)
    print(f"{len(resultados)} nodos relevantes encontrados.")

    print("\n=== Sintetizando respuesta final… ===")
    respuesta = sintetizar_respuesta(pregunta, resultados)

    print("\n=== RESPUESTA FINAL ===")
    print(respuesta)

    return respuesta
