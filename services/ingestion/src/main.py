import os
import logging
from typing import Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from .cypher_migrator import CypherMigrator
from .incident_streamer import IncidentStreamer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ingestion_main")

app = FastAPI(
    title="NetContext Ingestion & Event Streaming Service",
    description="Fetches real-world Tata Communications topology (AS6453) and streams real-time telemetry events",
    version="1.0.0",
)

class CableCutRequest(BaseModel):
    cable_id: str = "CABLE-TGN-TIC"
    reason: Optional[str] = "Subsea fiber anchor drag cut near Singapore Strait"

class DeviceFailureRequest(BaseModel):
    device_id: str = "DEV-SG-CR01"
    reason: Optional[str] = "BGP Route Processor hardware panic and linecard flap"

@app.get("/")
def root():
    return {
        "service": "ingestion-service",
        "status": "healthy",
        "neo4j_uri": os.getenv("NEO4J_URI", "bolt://localhost:7687")
    }

@app.get("/health")
def health():
    return {"status": "UP"}

@app.post("/api/v1/ingest/seed")
def seed_graph():
    """
    Connects to PeeringDB, fetches Tata Communications (AS6453) infrastructure,
    applies Cypher constraints, and populates the complete Knowledge Graph.
    """
    try:
        migrator = CypherMigrator()
        stats = migrator.seed_complete_context_graph()
        migrator.close()
        return {
            "status": "SUCCESS",
            "message": "NetContext Knowledge Graph successfully seeded with real Tata Communications assets.",
            "stats": stats
        }
    except Exception as err:
        logger.exception("Failed to seed context graph")
        raise HTTPException(status_code=500, detail=str(err))

@app.get("/api/v1/topology/stats")
def get_stats():
    """Returns current node, relationship, and label counts in the context graph."""
    try:
        migrator = CypherMigrator()
        stats = migrator.get_graph_statistics()
        migrator.close()
        return stats
    except Exception as err:
        raise HTTPException(status_code=500, detail=str(err))

@app.get("/api/v1/topology/graph-view")
def get_topology_graph_view():
    """
    Extracts live physical & logical topology (POPs, Cables, Customers) directly
    from Neo4j for dynamic physics graph visualization.
    """
    try:
        from neo4j import GraphDatabase
        uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        user = os.getenv("NEO4J_USER", "neo4j")
        password = os.getenv("NEO4J_PASSWORD", "NetContextSecure2026!")
        driver = GraphDatabase.driver(uri, auth=(user, password))

        with driver.session() as session:
            pops_res = session.run("""
                MATCH (p:POP)
                RETURN p.id AS id, p.name AS name, p.city AS city, p.region AS region
                ORDER BY p.city
            """)
            pops = [dict(r) for r in pops_res]

            cables_res = session.run("""
                MATCH (cb:Cable)
                OPTIONAL MATCH (p:POP)-[:CONNECTED_VIA_CABLE]->(cb)
                RETURN cb.id AS id, cb.name AS name, cb.status AS status, collect(DISTINCT p.id) AS connected_pops
                ORDER BY cb.name
            """)
            cables = [dict(r) for r in cables_res]

            cust_res = session.run("""
                MATCH (c:Customer)
                OPTIONAL MATCH (c)-[:SUBSCRIBES_TO]->(cir:Circuit)-[:ROUTES_THROUGH]->(d:Device)-[:LOCATED_AT]->(p:POP)
                RETURN c.id AS id, c.name AS name, c.tier AS tier, collect(DISTINCT p.id) AS connected_pops
                ORDER BY c.name
            """)
            customers = [dict(r) for r in cust_res]

        driver.close()
        return {
            "pops": pops,
            "cables": cables,
            "customers": customers
        }
    except Exception as err:
        logger.exception("Error extracting graph view topology")
        raise HTTPException(status_code=500, detail=str(err))

@app.post("/api/v1/incidents/simulate/cable-cut")
def simulate_cable_cut(req: CableCutRequest):
    """
    Simulates a live subsea fiber optic cut (e.g., TGN-TIC).
    Mutates graph in real time and calculates customer blast radius & SLA liabilities.
    """
    try:
        streamer = IncidentStreamer()
        result = streamer.simulate_cable_cut(cable_id=req.cable_id, reason=req.reason)
        streamer.close()
        return result
    except Exception as err:
        logger.exception("Error simulating cable cut")
        raise HTTPException(status_code=500, detail=str(err))

@app.post("/api/v1/incidents/simulate/device-failure")
def simulate_device_failure(req: DeviceFailureRequest):
    """
    Simulates a live router or switch failure (e.g., DEV-SG-CR01).
    """
    try:
        streamer = IncidentStreamer()
        result = streamer.simulate_device_failure(device_id=req.device_id, reason=req.reason)
        streamer.close()
        return result
    except Exception as err:
        logger.exception("Error simulating device failure")
        raise HTTPException(status_code=500, detail=str(err))

@app.post("/api/v1/incidents/resolve/{incident_id}")
def resolve_incident(incident_id: str):
    """
    Resolves an active incident and restores network circuit health.
    """
    try:
        streamer = IncidentStreamer()
        result = streamer.resolve_incident(incident_id=incident_id)
        streamer.close()
        return result
    except Exception as err:
        raise HTTPException(status_code=500, detail=str(err))

@app.get("/api/v1/incidents/active")
def get_active_incidents():
    """Lists all open network incidents."""
    try:
        streamer = IncidentStreamer()
        incidents = streamer.get_active_incidents()
        streamer.close()
        return {"active_incidents": incidents, "count": len(incidents)}
    except Exception as err:
        raise HTTPException(status_code=500, detail=str(err))

@app.get("/api/v1/telemetry/bgp")
def get_live_bgp_telemetry():
    """
    Fetches real live global internet routing telemetry for Tata Communications (AS6453)
    directly from the official RIPE NCC (RIPEstat) API.
    """
    try:
        from .bgp_telemetry import BGPTelemetryClient
        return BGPTelemetryClient.fetch_live_bgp_telemetry()
    except Exception as err:
        raise HTTPException(status_code=500, detail=str(err))

@app.get("/api/v1/incidents/sla-risk")
def get_live_sla_risk():
    """
    Calculates live SLA breach liability ($/hr) dynamically from the Neo4j Knowledge Graph.
    """
    try:
        streamer = IncidentStreamer()
        risk = streamer.calculate_total_live_sla_risk()
        streamer.close()
        return risk
    except Exception as err:
        logger.exception("Error calculating live SLA risk")
        raise HTTPException(status_code=500, detail=str(err))

@app.get("/api/v1/incidents/impacted-customers")
def get_impacted_customers():
    """
    Retrieves all enterprise customers, circuits, and SLAs impacted by active incidents.
    """
    try:
        streamer = IncidentStreamer()
        impacted = streamer.get_impacted_customers_all_incidents()
        streamer.close()
        return {"impacted_customers": impacted, "count": len(impacted)}
    except Exception as err:
        logger.exception("Error getting impacted customers")
        raise HTTPException(status_code=500, detail=str(err))

class RerouteExecutionRequest(BaseModel):
    customer_id: str = "CUST-OMNI-01"
    circuit_id: str = "CIR-OMNI-PRI"
    target_cable_id: Optional[str] = "CABLE-SMW4"

@app.get("/api/v1/reroute/recommendations")
def get_reroute_recommendations():
    """
    Scans graph for downed circuits and suggests autonomous failover paths.
    """
    try:
        streamer = IncidentStreamer()
        recs = streamer.get_reroute_recommendations()
        streamer.close()
        return {"recommendations": recs, "count": len(recs)}
    except Exception as err:
        logger.exception("Error getting reroute recommendations")
        raise HTTPException(status_code=500, detail=str(err))

@app.post("/api/v1/reroute/execute")
def execute_failover_reroute(req: RerouteExecutionRequest):
    """
    Executes an autonomous dynamic reroute in Neo4j, updating circuit topology and eliminating SLA risk.
    """
    try:
        streamer = IncidentStreamer()
        result = streamer.execute_failover_reroute(
            customer_id=req.customer_id,
            circuit_id=req.circuit_id,
            target_cable_id=req.target_cable_id or "CABLE-SMW4"
        )
        streamer.close()
        return result
    except Exception as err:
        logger.exception("Error executing failover reroute")
        raise HTTPException(status_code=500, detail=str(err))
