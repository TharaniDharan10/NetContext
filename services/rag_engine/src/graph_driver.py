import os
import logging
from neo4j import GraphDatabase, Driver

logger = logging.getLogger("graph_driver")

class GraphDriver:
    _instance = None

    def __init__(self, uri: str = None, user: str = None, password: str = None):
        self.uri = uri or os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.user = user or os.getenv("NEO4J_USER", "neo4j")
        self.password = password or os.getenv("NEO4J_PASSWORD", "NetContextSecure2026!")
        self.driver: Driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
        logger.info("Initialized Neo4j driver connection to: %s", self.uri)

    @classmethod
    def get_driver(cls) -> "GraphDriver":
        if cls._instance is None:
            cls._instance = GraphDriver()
        return cls._instance

    def get_session(self):
        return self.driver.session()

    def close(self):
        if self.driver:
            self.driver.close()
            logger.info("Neo4j driver connection closed.")
