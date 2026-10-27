import os
import logging
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional

from .graph_retriever import GraphRetriever
from .rca_agent import RCAAgent
from .cypher_repo import CypherRepository

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("rag_main")

app = FastAPI(
    title="NetContext GraphRAG & AI Reasoning Engine",
    description="Translates natural language questions to Cypher, evaluates topological blast radius, and generates explainable RCA",
    version="1.0.0",
)

class QueryRequest(BaseModel):
    query: str
    include_raw_context: Optional[bool] = False

@app.get("/")
def root():
    return {
        "service": "rag-engine",
        "status": "healthy",
        "neo4j_uri": os.getenv("NEO4J_URI", "bolt://localhost:7687"),
        "llm_provider": os.getenv("LLM_PROVIDER", "gemini")
    }

@app.get("/health")
def health():
    return {"status": "UP"}

@app.post("/api/v1/query")
def process_query(req: QueryRequest):
    """
    Core GraphRAG Endpoint:
    Accepts natural language questions from network engineers,
    retrieves live multi-hop topological graph context from Neo4j,
    and produces an authoritative Root Cause Analysis (RCA) report.
    """
    try:
        retriever = GraphRetriever()
        context_type, graph_context = retriever.retrieve_context_for_query(req.query)

        agent = RCAAgent()
        result = agent.generate_analysis(
            user_query=req.query,
            context_type=context_type,
            graph_context=graph_context
        )

        if not req.include_raw_context:
            result.pop("raw_graph_context", None)

        return result
    except Exception as err:
        logger.exception("Error processing GraphRAG query")
        raise HTTPException(status_code=500, detail=str(err))

@app.get("/api/v1/topology/customer/{customer_query}")
def get_customer_topology(customer_query: str):
    """Fetches the multi-hop customer subgraph (circuits, cables, routers, SLAs)."""
    try:
        repo = CypherRepository()
        subgraph = repo.get_customer_subgraph(customer_query)
        if not subgraph:
            raise HTTPException(status_code=404, detail=f"Customer '{customer_query}' not found.")
        return subgraph
    except HTTPException:
        raise
    except Exception as err:
        raise HTTPException(status_code=500, detail=str(err))

@app.get("/api/v1/topology/spof")
def get_spof():
    """Identifies Single Points of Failure across all enterprise circuits."""
    try:
        repo = CypherRepository()
        return {"single_points_of_failure": repo.detect_single_points_of_failure()}
    except Exception as err:
        raise HTTPException(status_code=500, detail=str(err))

@app.get("/api/v1/topology/blast-radius/{entity_id}")
def get_blast_radius(entity_id: str):
    """Calculates blast radius for a specific cable or device."""
    try:
        repo = CypherRepository()
        return repo.get_blast_radius(entity_id)
    except Exception as err:
        raise HTTPException(status_code=500, detail=str(err))
