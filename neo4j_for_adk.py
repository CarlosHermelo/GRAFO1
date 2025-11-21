# neo4j_for_adk.py
from neo4j import GraphDatabase

class GraphDB:
    def __init__(self):
        self.driver = None

    def connect(self, uri, username, password):
        self.driver = GraphDatabase.driver(uri, auth=(username, password))

    def send_query(self, query, params=None):
        with self.driver.session() as session:
            result = session.run(query, params or {})
            return [record.data() for record in result]

graphdb = GraphDB()

# Funciones de utilidad para herramientas
def tool_success(key: str, value):
    """Retorna un diccionario indicando éxito de la herramienta."""
    return {
        "status": "success",
        key: value
    }

def tool_error(message: str):
    """Retorna un diccionario indicando error de la herramienta."""
    return {
        "status": "error",
        "error_message": message
    }
