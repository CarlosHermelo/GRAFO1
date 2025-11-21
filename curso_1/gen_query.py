import os
import re
from typing import List, Dict, Any
from dotenv import load_dotenv
from neo4j import GraphDatabase
from openai import OpenAI

# Cargar variables de entorno
load_dotenv()

# Configuración
# cargar variables de entorno
load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI", "neo4j+s://b0df6e44.databases.neo4j.io")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

print("URI:", os.getenv("NEO4J_URI"))
print("USER:", os.getenv("NEO4J_USER"))
print("PASS:", os.getenv("NEO4J_PASSWORD"))


OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)

class GraphQA:
    def __init__(self):
        self.driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    
    def close(self):
        self.driver.close()

    def get_schema_summary(self) -> str:
        """
        Consulta la base de datos para obtener un resumen del esquema actual.
        Esto ayuda al LLM a no alucinar relaciones que no existen.
        """
        schema_query = """
        CALL db.schema.visualization()
        """
        with self.driver.session() as session:
            result = session.run(schema_query)
            node_labels = []
            relationships = []
            
            # Extraemos una estructura simple para el prompt
            # Nota: db.schema.visualization devuelve objetos complejos, 
            # para este ejemplo simplificaremos con una query más directa de metadatos:
            
            labels_q = "CALL db.labels()"
            rels_q = "CALL db.relationshipTypes()"
            
            labels = [r[0] for r in session.run(labels_q)]
            rels = [r[0] for r in session.run(rels_q)]
            
            # Query para ver ejemplos de tripletas (muy útil para el LLM)
            sample_q = """
            MATCH (a)-[r]->(b) 
            RETURN distinct labels(a)[0] as source, type(r) as rel, labels(b)[0] as target 
            LIMIT 20
            """
            triplets = [f"({r['source']}) -[:{r['rel']}]-> ({r['target']})" for r in session.run(sample_q)]
            
            schema_str = f"Node Labels: {labels}\nRelationship Types: {rels}\nSchema Patterns:\n" + "\n".join(triplets)
            return schema_str

    def text_to_cypher(self, user_question: str, schema_str: str) -> str:
        """
        Usa GPT-4o para traducir Lenguaje Natural a Cypher.
        """
        system_prompt = f"""
        Eres un experto desarrollador de Neo4j. Tu tarea es convertir preguntas en lenguaje natural a consultas CYPHER precisas.
        
        ESQUEMA DE LA BASE DE DATOS:
        {schema_str}
        
        REGLAS CRÍTICAS PARA GENERAR CYPHER:
        1. Usa SOLO los labels y relaciones provistos en el esquema.
        2. **Identificadores (IDs):** En esta base de datos, la propiedad `id` es clave. 
           - Los IDs están en formato SNAKE_CASE_MAYUSCULA. 
           - Ejemplo: "Ley 27275" se guarda como id: "LEY_27275". "Resolución 2024/80" es "RESOL_2024_80_...".
           - Cuando el usuario mencione un número de norma, intenta construir el ID usando `CONTAINS` o igualando el formato esperado.
           - Ejemplo de búsqueda flexible: `WHERE n.id CONTAINS '27275'`
        3. Devuelve SOLAMENTE el código Cypher. No incluyas bloques de markdown (```cypher ... ```), solo el código.
        4. Siempre devuelve propiedades útiles (id, nombre) en el RETURN.
        """

        completion = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Pregunta: {user_question}"}
            ],
            temperature=0
        )
        
        cypher = completion.choices[0].message.content.strip()
        
        # Limpieza básica por si el modelo pone backticks
        cypher = cypher.replace("```cypher", "").replace("```", "")
        return cypher

    def execute_cypher(self, cypher: str) -> List[Dict[str, Any]]:
        """Ejecuta el query en Neo4j"""
        with self.driver.session() as session:
            try:
                result = session.run(cypher)
                return [r.data() for r in result]
            except Exception as e:
                return [{"error": str(e)}]

    def synthesize_answer(self, question: str, data: List[Dict], cypher: str) -> str:
        """Toma los datos crudos y genera una respuesta natural."""
        if not data:
            return "No encontré información en la base de datos que responda a tu pregunta."
        
        if "error" in data[0]:
            return f"Hubo un error técnico al ejecutar la consulta: {data[0]['error']}"

        system_prompt = "Eres un asistente útil que responde preguntas basándose en datos de una base de datos de grafos."
        user_content = f"""
        Pregunta del usuario: {question}
        
        Consulta Cypher ejecutada: {cypher}
        
        Datos obtenidos de Neo4j:
        {json.dumps(data, ensure_ascii=False)}
        
        Responde la pregunta de forma clara y concisa usando los datos.
        """

        completion = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ]
        )
        return completion.choices[0].message.content

import json

def main():
    qa = GraphQA()
    
    print("--- 🧠 Obteniendo esquema del grafo... ---")
    schema = qa.get_schema_summary()
    print(f"Esquema detectado (resumen):\n{schema[:300]}...\n")
    
    print("--- 🤖 Chat con tu Grafo (Escribe 'salir' para terminar) ---")
    
    while True:
        question = input("\nPregunta: ")
        if question.lower() in ["salir", "exit"]:
            break
            
        # 1. Generar Cypher
        print("  ↳ Generando consulta...")
        cypher_query = qa.text_to_cypher(question, schema)
        print(f"  [CYPHER]: {cypher_query}")
        
        # 2. Ejecutar
        results = qa.execute_cypher(cypher_query)
        print(f"  ↳ Se encontraron {len(results)} registros.")
        
        # 3. Sintetizar respuesta
        print("  ↳ Analizando respuesta...")
        final_answer = qa.synthesize_answer(question, results, cypher_query)
        
        print(f"\nRESPUESTA: {final_answer}")
        print("-" * 50)

    qa.close()

if __name__ == "__main__":
    main()