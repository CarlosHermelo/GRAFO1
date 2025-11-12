# p4_multi_protesis_query_light.py
# === Multiagente liviano para consultas sobre grafo de Prótesis (PAMI) ===

import os, asyncio
from openai import AsyncOpenAI
from neo4j import GraphDatabase

# === CONFIGURACIÓN ===
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY no está configurada en las variables de entorno")
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
client = AsyncOpenAI(api_key=OPENAI_API_KEY)

# Configuración Neo4j
uri = os.getenv("NEO4J_URI", "neo4j+s://b0df6e44.databases.neo4j.io")
user = os.getenv("NEO4J_USER", "neo4j")
password = os.getenv("NEO4J_PASSWORD")
if not password:
    raise ValueError("NEO4J_PASSWORD no está configurada en las variables de entorno")
driver = GraphDatabase.driver(uri, auth=(user, password))
print("✅ Conectado a Neo4j")

# === AGENTES ===
async def agent_intent(question: str) -> str:
    """Detecta intención y reformula la pregunta."""
    prompt = f"""
Sos un analista de datos del PAMI. El usuario pregunta: "{question}".
Reformulá la intención brevemente (por ejemplo: 'Obtener cantidad de trámites demorados por proveedor').
Solo devolvé la reformulación.
"""
    r = await client.chat.completions.create(model="gpt-5-nano", messages=[{"role": "user", "content": prompt}])
    return r.choices[0].message.content.strip()

async def agent_plan(intent: str) -> str:
    """Decide entidades y relaciones a usar."""
    prompt = f"""
Dado el objetivo: "{intent}", indicá qué entidades y relaciones del grafo de prótesis se necesitan:
Entidades disponibles: Afiliado, Prestador, Proveedor, Protesis, Tramite, Mensaje, NotificacionInterna, Incumplimiento.
Relaciones:
(Tramite)-[:TRAMITE_DE]->(Afiliado)
(Tramite)-[:GESTIONADO_POR]->(Prestador)
(Tramite)-[:ASIGNADO_A]->(Proveedor)
(Tramite)-[:SOLICITA]->(Protesis)
(Mensaje)-[:ASOCIADO_A]->(Tramite)
(NotificacionInterna)-[:RELACIONADA_CON]->(Tramite)
(Incumplimiento)-[:DETECTADO_EN]->(Tramite)
Resumí qué entidades usarías.
"""
    r = await client.chat.completions.create(model="gpt-5-nano", messages=[{"role": "user", "content": prompt}])
    return r.choices[0].message.content.strip()

async def agent_cypher(intent: str, plan: str) -> str:
    """Genera la consulta Cypher."""
    prompt = f"""
Basado en el objetivo: "{intent}"
y el plan: "{plan}"
Generá una consulta Cypher válida que responda eso, usando las entidades y relaciones del dominio.
No inventes campos.
"""
    r = await client.chat.completions.create(model="gpt-5-nano", messages=[{"role": "user", "content": prompt}])
    return r.choices[0].message.content.strip("`").replace("cypher", "").strip()

def agent_execute(cypher: str):
    """Ejecuta solo la primera consulta Cypher válida, filtrando texto explicativo."""
    try:
        lines = cypher.splitlines()
        valid_starts = ("MATCH", "CALL", "CREATE", "MERGE", "WITH")
        start_idx = next((i for i, l in enumerate(lines) if l.strip().upper().startswith(valid_starts)), None)
        if start_idx is None:
            raise ValueError("No se encontró una consulta Cypher válida en el texto generado.")

        sublines = lines[start_idx:]
        # Cortar si aparecen explicaciones comunes
        end_markers = ["Notas:", "Note:", "Explanation", "Observaciones", "#", "//"]
        clean_lines = []
        for l in sublines:
            if any(marker in l for marker in end_markers):
                break
            clean_lines.append(l)
        clean_query = "\n".join(clean_lines).split(";")[0].strip()

        print(f"\n[DEBUG] Ejecutando Cypher limpio:\n{clean_query}\n")

        with driver.session() as session:
            result = session.run(clean_query)
            records = [r.data() for r in result]
        return records or [{"mensaje": "Sin resultados"}]

    except Exception as e:
        return {"error": str(e)}

# === COORDINADOR ===
async def run_agentic_query():
    print("🧠 Multiagente de consultas sobre grafo de Prótesis iniciado.")
    while True:
        q = input("\n🟢 Ingresá tu pregunta (o 'salir'): ")
        if q.lower() in ["salir", "exit", "q"]:
            break

        intent = await agent_intent(q)
        print(f"\n🎯 Intención detectada: {intent}")

        plan = await agent_plan(intent)
        print(f"\n🗺️ Plan: {plan}")

        cypher = await agent_cypher(intent, plan)
        print(f"\n⚙️ Consulta Cypher generada:\n{cypher}")

        result = agent_execute(cypher)
        print(f"\n✅ Resultado:\n{result}")


# === MODO FRAUDE AUTOMATIZADO ===
import sys, csv

async def run_fraud_analysis():
    print("\n🚨 Iniciando modo FRAUDE AUTOMATIZADO...\n")

    # Consulta 1 — Pares prestador–proveedor con más trámites demorados
    query1 = """
    MATCH (p:Prestador)-[:GESTIONADO_POR]<-(t:Tramite)-[:ASIGNADO_A]->(v:Proveedor),
          (i:Incumplimiento)-[:DETECTADO_EN]->(t)
    WITH p, v, count(t) AS total_incumplimientos
    WHERE total_incumplimientos > 2
    RETURN p.nombre AS Prestador, v.nombre AS Proveedor, total_incumplimientos
    ORDER BY total_incumplimientos DESC
    """

    # Consulta 2 — Proveedores con mayor concentración de incumplimientos
    query2 = """
    MATCH (v:Proveedor)<-[:ASIGNADO_A]-(t:Tramite)
    OPTIONAL MATCH (i:Incumplimiento)-[:DETECTADO_EN]->(t)
    WITH v, count(i) AS incum, count(t) AS total, toFloat(count(i))/count(t) AS ratio
    WHERE total > 3
    RETURN v.nombre AS Proveedor, incum, total, round(ratio,2) AS Riesgo
    ORDER BY Riesgo DESC
    """

    # Consulta 3 — Scoring de riesgo entre prestadores y proveedores
    query3 = """
    MATCH (p:Prestador)-[:GESTIONADO_POR]<-(t:Tramite)-[:ASIGNADO_A]->(v:Proveedor)
    OPTIONAL MATCH (i:Incumplimiento)-[:DETECTADO_EN]->(t)
    WITH p, v,
         count(t) AS total,
         count(i) AS con_incumplimiento,
         toFloat(count(i)) / count(t) AS riesgo
    WHERE total > 2
    RETURN p.nombre AS Prestador, v.nombre AS Proveedor, total, con_incumplimiento, round(riesgo,2) AS Riesgo
    ORDER BY Riesgo DESC
    """

    consultas = [
        ("Pares Prestador–Proveedor con más demoras", query1),
        ("Proveedores con mayor concentración de incumplimientos", query2),
        ("Scoring de riesgo de colusión", query3)
    ]

    resultados_totales = []

    with driver.session() as session:
        for titulo, q in consultas:
            print(f"🔍 {titulo}")
            res = session.run(q)
            datos = [r.data() for r in res]
            resultados_totales.append((titulo, datos))
            for r in datos[:10]:
                print(r)
            print("----\n")

    # Guardar reporte CSV
    with open("reporte_fraude.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Prestador", "Proveedor", "Total_Tramites", "Incumplimientos", "Riesgo", "Tipo"])
        for titulo, datos in resultados_totales:
            for r in datos:
                writer.writerow([
                    r.get("Prestador", ""),
                    r.get("Proveedor", ""),
                    r.get("total") or r.get("total_incumplimientos") or "",
                    r.get("con_incumplimiento") or r.get("incum") or "",
                    r.get("Riesgo", ""),
                    titulo
                ])
    print("✅ Reporte guardado como 'reporte_fraude.csv'.")


# === SELECTOR DE MODO ===
if __name__ == "__main__":
    modo = "interactivo"
    if len(sys.argv) > 1 and sys.argv[1].lower() == "fraude":
        modo = "fraude"

    if modo == "fraude":
        asyncio.run(run_fraud_analysis())
    else:
        asyncio.run(run_agentic_query())
