print("🔵 INICIANDO SCRIPT... (Cargando módulos)")

import sys
import os
import json

# --- IMPORTS ---
try:
    from typing import List, Dict, Any
    from dotenv import load_dotenv
    from neo4j import GraphDatabase
    from openai import OpenAI
    from langchain_chroma import Chroma
    from langchain_openai import OpenAIEmbeddings
    print("✅ Librerías importadas correctamente.")
except ImportError as e:
    print(f"❌ ERROR DE IMPORTACIÓN: {e}")
    print("Ejecuta: pip install langchain-chroma langchain-openai langchain-community chromadb neo4j openai python-dotenv")
    sys.exit(1)

# --- CLASES ---

class GraphEngine:
    def __init__(self, uri, user, password, llm_model, client_openai):
        print("   ↳ Conectando a Neo4j...")
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.client_openai = client_openai
        self.llm_model = llm_model
        self.schema_summary = self._get_schema_summary()
    
    def close(self):
        self.driver.close()

    def _get_schema_summary(self) -> str:
        with self.driver.session() as session:
            try:
                session.run("RETURN 1") # Test de conexión
                sample_q = "MATCH (a)-[r]->(b) RETURN distinct labels(a)[0] as source, type(r) as rel, labels(b)[0] as target LIMIT 10"
                triplets = [f"({r['source']}) -[:{r['rel']}]-> ({r['target']})" for r in session.run(sample_q)]
                return "Patrones:\n" + "\n".join(triplets) if triplets else "Sin relaciones detectadas."
            except Exception as e:
                return f"Error leyendo esquema: {e}"

    def query(self, user_question: str) -> Dict[str, Any]:
        """
        Devuelve un diccionario con: {'cypher': str, 'data': str}
        """
        # PROMPT CORREGIDO: Instrucciones explícitas sobre IDs y Búsqueda Flexible
        system_prompt = f"""
        Eres un experto desarrollador de Neo4j.
        
        ESQUEMA DE LA BASE DE DATOS:
        {self.schema_summary}
        
        REGLAS CRÍTICAS PARA GENERAR CYPHER:
        1. **PRIORIDAD A IDs**: Los nodos tienen una propiedad `id` en formato SNAKE_CASE_MAYUSCULA (ej. "HIPERTENSION_ARTERIAL", "DIABETES_TIPO_2").
           - Tu primera estrategia debe ser convertir la entidad del usuario a este formato y buscar por `id`.
           - Ejemplo: MATCH (n:Enfermedad {{id: 'HIPERTENSION_ARTERIAL'}})
        
        2. **BÚSQUEDA POR NOMBRE**: Si no estás seguro del ID, busca por la propiedad `nombre` usando `CONTAINS` y `toLower()` para ser flexible.
           - NUNCA asumas coincidencia exacta en el nombre (ej. NO hagas {{nombre: 'X'}}).
           - Ejemplo: WHERE toLower(n.nombre) CONTAINS 'hipertension'
        
        3. Usa SOLO los labels y relaciones provistos en el esquema.
        4. Devuelve SOLAMENTE el código Cypher limpio, sin markdown (```cypher).
        """
        
        try:
            # 1. Generar Cypher
            response = self.client_openai.chat.completions.create(
                model=self.llm_model,
                messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_question}],
                temperature=0
            )
            # Limpieza robusta de markdown
            cypher = response.choices[0].message.content.strip()
            cypher = cypher.replace("```cypher", "").replace("```", "").strip()
            
            # 2. Ejecutar Cypher
            with self.driver.session() as session:
                data_raw = [r.data() for r in session.run(cypher)]
            
            # Formateo del resultado
            result_str = json.dumps(data_raw, ensure_ascii=False) if data_raw else "Sin resultados directos en el Grafo."
            
            return {"cypher": cypher, "data": result_str}
            
        except Exception as e:
            return {"cypher": "ERROR", "data": f"Excepción en Grafo: {e}"}
class VectorEngine:
    def __init__(self, path_bdv, nombre_coleccion):
        print(f"   ↳ Conectando a Chroma en {path_bdv}...")
        self.vector_store = Chroma(
            client=None,
            collection_name=nombre_coleccion,
            persist_directory=path_bdv,
            embedding_function=OpenAIEmbeddings(model="text-embedding-3-small")
        )
        
    def query(self, user_question: str) -> str:
        try:
            results = self.vector_store.similarity_search(user_question, k=3)
            if not results:
                return "Sin resultados vectoriales."
            
            # Formateamos bonito para mostrar
            formatted_res = []
            for i, doc in enumerate(results):
                formatted_res.append(f"[Chunk {i+1}]: {doc.page_content[:200]}...") # Muestra solo primeros 200 chars
            
            return "\n".join(formatted_res)
        except Exception as e:
            return f"Error Vector: {e}"

def synthesize(client, model, question, graph_data, vector_data, goal):
    system_prompt = """
    Eres un analista de información estricto. Tu única función es sintetizar los datos proporcionados.
    
    REGLAS ABSOLUTAS (GUARDRAILS):
    1. 🚫 PROHIBIDO usar conocimiento previo o externo. No inventes ni agregues información que no esté en "DATOS PROPORCIONADOS".
    2. Si la información necesaria para responder NO está en los datos (Grafo o Vectorial), debes responder EXACTAMENTE:
       "No dispongo de información suficiente en la base de datos o documentos para responder a esta consulta."
    3. Cita la fuente de tu respuesta (ej. "Según el grafo..." o "Según el documento...").
    4. Si los datos son contradictorios, señálalo.
    """

    user_prompt = f"""
    {goal}
    
    DATOS PROPORCIONADOS (ÚNICA FUENTE DE VERDAD):
    ---------------------
    [FUENTE 1: GRAFO DE CONOCIMIENTO (Estructura y Relaciones)]
    {graph_data}
    
    [FUENTE 2: BÚSQUEDA VECTORIAL (Contexto y Texto)]
    {vector_data}
    ---------------------
    
    Pregunta del usuario: "{question}"
    
    Respuesta (basada EXCLUSIVAMENTE en los datos de arriba):
    """
    
    res = client.chat.completions.create(
        model=model, 
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0 # Temperatura 0 para máxima determinismo y mínima creatividad
    )
    return res.choices[0].message.content
# --- MAIN ---
def main():
    load_dotenv()
    print("📂 Variables de entorno cargadas.")

    # Validar variables
    if not all([os.getenv("NEO4J_URI"), os.getenv("BDV"), os.getenv("CARPETA_TXT")]):
        print("❌ Faltan variables en .env")
        return

    try:
        client_ai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        # Instanciar
        ge = GraphEngine(os.getenv("NEO4J_URI"), os.getenv("NEO4J_USER"), os.getenv("NEO4J_PASSWORD"), os.getenv("MODELO"), client_ai)
        ve = VectorEngine(os.getenv("BDV"), os.getenv("FILE_BDV"))
        
        # Cargar Goal
        goal_path = os.path.join(os.getenv("CARPETA_TXT"), "goal.config")
        goal = open(goal_path, 'r', encoding='utf-8').read() if os.path.exists(goal_path) else "Eres un asistente útil."
        
        print("\n" + "="*60)
        print("🤖 SISTEMA HÍBRIDO LISTO (Detalle Debug Activado)")
        print("="*60)
        
        while True:
            q = input("\n🗣️ Pregunta (o 'salir'): ")
            if q.lower() in ['salir', 'exit']: break
            
            print("\n" + "-"*30)
            print("🔎 1. CONSULTA AL GRAFO (NEO4J)")
            print("-" * 30)
            
            # Consulta Grafo
            g_response = ge.query(q)
            print(f"📝 [QUERY CYPHER GENERADA]:\n{g_response['cypher']}")
            print(f"\n📦 [RESULTADO JSON]:\n{g_response['data']}")
            
            print("\n" + "-"*30)
            print("🔎 2. CONSULTA VECTORIAL (CHROMA)")
            print("-" * 30)
            
            # Consulta Vectorial
            v_response = ve.query(q)
            print(f"📚 [CHUNKS RECUPERADOS]:\n{v_response}")
            
            print("\n" + "-"*30)
            print("🧠 3. SÍNTESIS (COMBINACIÓN)")
            print("-" * 30)
            
            # Síntesis Final
            final = synthesize(client_ai, os.getenv("MODELO"), q, g_response['data'], v_response, goal)
            print(f"💡 RESPUESTA FINAL:\n{final}")
            
            print("\n" + "="*60)
            
        ge.close()
        
    except Exception as e:
        print(f"❌ ERROR CRITICO EN MAIN: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()