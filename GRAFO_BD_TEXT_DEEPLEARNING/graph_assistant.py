import os
from dotenv import load_dotenv
from langchain_community.graphs import Neo4jGraph
from langchain_openai import ChatOpenAI
from langchain_community.chains.graph_qa.cypher import GraphCypherQAChain
from langchain_core.prompts import PromptTemplate  # <-- Importación corregida

# ==============================================================================
# 0. CONFIGURACIÓN Y CARGA DE .ENV
# ==============================================================================

# Cargar variables de entorno
load_dotenv()

# --- CONFIGURACIÓN DE MODELO Y CREDENCIALES ---
LLM_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

# ==============================================================================
# DEFINICIÓN DEL SYSTEM PROMPT PERSONALIZADO PARA CYPHER
# ==============================================================================

# Este es el System Prompt que le da la identidad y las reglas al LLM.
CUSTOM_CYPHER_GENERATION_TEMPLATE = """Task: Generate Cypher query for Neo4j graph database.

You are a Neo4j Cypher expert. Generate ONLY valid Cypher query syntax. Do not include any explanations or apologies.

Schema:
{schema}

Examples:
Question: How many nodes are there?
Cypher: MATCH (n) RETURN count(n) as count

Question: List all Normativa nodes
Cypher: MATCH (n:Normativa) RETURN n LIMIT 10

Question: Find relationships between Normativa nodes
Cypher: MATCH (n:Normativa)-[r]->(m:Normativa) RETURN n.id, type(r), m.id LIMIT 10

The question is:
{question}

Cypher query:"""

# Convertir el texto a un objeto PromptTemplate
CUSTOM_CYPHER_PROMPT = PromptTemplate(
    input_variables=["schema", "question"],
    template=CUSTOM_CYPHER_GENERATION_TEMPLATE,
)

# ==============================================================================
# 1. INICIALIZACIÓN DE COMPONENTES (Función sin cambios)
# ==============================================================================

def initialize_graph_components():
    """Inicializa la conexión a Neo4j y el modelo LLM."""
    
    if not all([OPENAI_API_KEY, NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD]):
        print("❌ ERROR CRÍTICO: Las credenciales de OPENAI o NEO4J no están configuradas en el .env.")
        return None, None
        
    print(f"🔗 Conectando al grafo en: {NEO4J_URI}...")
    try:
        graph = Neo4jGraph(
            url=NEO4J_URI,
            username=NEO4J_USER,
            password=NEO4J_PASSWORD
        )
        graph.refresh_schema() 
        print("✅ Conexión a Neo4j exitosa. Esquema cargado para el LLM.")
    except Exception as e:
        print(f"❌ ERROR al conectar con Neo4j. Verifica el URI y las credenciales. Error: {e}")
        return None, None

    print(f"🧠 Inicializando LLM: {LLM_MODEL}")
    llm = ChatOpenAI(
        model=LLM_MODEL, 
        openai_api_key=OPENAI_API_KEY, 
        temperature=0.0
    )
    
    return graph, llm

# ==============================================================================
# 2. ASISTENTE DEL GRAFO (GraphCypherQAChain)
# ==============================================================================

def run_graph_assistant(graph: Neo4jGraph, llm: ChatOpenAI):
    """
    Crea y ejecuta el asistente basado en LangChain para consultar el grafo,
    usando el prompt personalizado.
    """
    
    # Crear la cadena QA que genera Cypher
    chain = GraphCypherQAChain.from_llm(
        llm=llm,
        graph=graph,
        verbose=True,
        return_intermediate_steps=True,
        allow_dangerous_requests=True,
        # <-- INYECCIÓN DEL PROMPT PERSONALIZADO -->
        cypher_prompt=CUSTOM_CYPHER_PROMPT, 
    )

    print("\n" + "="*70)
    print("🤖 ASISTENTE DE CONSULTA DE GRAFOS (LangChain + Neo4j)")
    print("="*70)
    print("El asistente ahora puede responder preguntas sobre Normativas, Prestaciones, etc.")
    
    while True:
        question = input("\nUSER: Haz tu pregunta (o escribe 'salir'):\n> ").strip()
        
        if question.lower() == 'salir':
            print("👋 Terminando el asistente.")
            break
        
        if not question:
            continue
            
        try:
            response = chain.invoke({"query": question})

            print("\n--- 🧠 RESULTADOS ---")
            
            cypher_query = response['intermediate_steps'][0]['query']
            print(f"**CYPHER GENERADO:**\n{cypher_query}")
            
            print(f"\n**RESPUESTA DEL ASISTENTE:**\n{response['result']}")
            print("-" * 70)

        except Exception as e:
            print(f"\n❌ Ocurrió un error. Verifique la sintaxis del Cypher generado. Error: {e}")


# ==============================================================================
# 3. EJECUCIÓN PRINCIPAL (Función sin cambios)
# ==============================================================================

if __name__ == "__main__":
    graph_instance, llm_instance = initialize_graph_components()
    
    if graph_instance and llm_instance:
        run_graph_assistant(graph_instance, llm_instance)