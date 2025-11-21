import os
from neo4j import GraphDatabase
from openai import OpenAI
from dotenv import load_dotenv

# Cargar .env
load_dotenv()

# ================================
# Configuración OpenAI
# ================================
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY no está configurada")

client = OpenAI(api_key=OPENAI_API_KEY)

# ================================
# Configuración Neo4j
# ================================
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER") or os.getenv("NEO4J_USERNAME")  # acepta ambos
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

if not NEO4J_URI or not NEO4J_USER or not NEO4J_PASSWORD:
    raise ValueError("Faltan variables de entorno NEO4J_URI / NEO4J_USER / NEO4J_PASSWORD")

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

# ================================
# Esquema del grafo
# ================================
ESQUEMA = """
Nodos:

1. Servicio
   - nombre

2. Tipo
   - nombre

3. Subtipo
   - id_sub
   - nombre
   - copete
   - consiste

Relaciones:

(Servicio)-[:TIENE_TIPO]->(Tipo)
(Tipo)-[:TIENE_SUBTIPO]->(Subtipo)
"""

# ================================
# Generar Cypher con IA
# ================================
def generar_cypher(pregunta):
    prompt = f"""
Sos un generador experto de consultas Cypher.
Convertí esta pregunta en una única consulta Cypher válida:

Pregunta:
\"\"\"{pregunta}\"\"\"

Usá únicamente este esquema:
{ESQUEMA}

Reglas:
- No inventes campos ni nodos.
- No expliques nada.
- Tu salida debe ser SOLO la consulta Cypher.

"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )

    return response.choices[0].message.content.strip()

# ================================
# Limpiar código Cypher
# ================================
def limpiar_cypher(cypher):
    """
    Elimina delimitadores de código markdown si están presentes.
    Por ejemplo: ```cypher ... ``` o ``` ... ```
    """
    cypher = cypher.strip()

    # Remover delimitadores de markdown
    if cypher.startswith("```cypher"):
        cypher = cypher[9:]  # Remover ```cypher
    elif cypher.startswith("```"):
        cypher = cypher[3:]  # Remover ```

    if cypher.endswith("```"):
        cypher = cypher[:-3]  # Remover ``` final

    return cypher.strip()

# ================================
# Ejecutar Cypher en Neo4j
# ================================
def ejecutar_cypher(cypher):
    # Limpiar el código antes de ejecutar
    cypher_limpio = limpiar_cypher(cypher)

    with driver.session() as session:
        result = session.run(cypher_limpio)
        return list(result)

# ================================
# Preguntar → Cypher → Resultado
# ================================
def preguntar_grafo(pregunta):
    print("\n=== Pregunta del usuario ===")
    print(pregunta)

    print("\n=== Generando consulta Cypher... ===")
    cypher = generar_cypher(pregunta)
    print(cypher)

    print("\n=== Ejecutando... ===")
    resultados = ejecutar_cypher(cypher)

    print("\n=== Resultados ===")
    if not resultados:
        print("Sin resultados.")
    else:
        for r in resultados:
            print(r)

    return resultados
