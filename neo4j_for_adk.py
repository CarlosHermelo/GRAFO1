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
