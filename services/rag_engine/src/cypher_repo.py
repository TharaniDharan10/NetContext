from typing import List, Dict, Any, Optional
from .graph_driver import GraphDriver

class CypherRepository:
    def __init__(self):
        self.driver_wrapper = GraphDriver.get_driver()

    def get_customer_subgraph(self, customer_query: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves the complete multi-hop context for a customer:
        Customer -> SLA -> Circuits -> Cables/Devices/POPs -> Active Incidents.
        """
        query = """
        MATCH (c:Customer)
        WHERE toLower(c.name) CONTAINS toLower($cust_query) OR toLower(c.id) CONTAINS toLower($cust_query)
        MATCH (c)-[:CONTRACTED_UNDER]->(s:SLA)
        MATCH (c)-[:SUBSCRIBES_TO]->(cir:Circuit)
        OPTIONAL MATCH (cir)-[:TRAVERSES_CABLE]->(cb:Cable)
        OPTIONAL MATCH (cir)-[:ROUTES_THROUGH]->(d:Device)-[:LOCATED_AT]->(p:POP)
        OPTIONAL MATCH (cir)-[:HAS_FAILOVER_ROUTE]->(bck:Circuit)
        OPTIONAL MATCH (inc:Incident {status: 'OPEN'})-[:IMPACTS]->(impacted)
        WHERE impacted IN [cb, d, cir]
        RETURN 
            c.id AS customer_id,
            c.name AS customer_name,
            c.industry AS industry,
            c.tier AS tier,
            s.name AS sla_name,
            s.max_downtime_minutes AS max_downtime_minutes,
            s.penalty_per_minute_usd * 60 AS penalty_usd_per_hour,
            collect(DISTINCT {
                circuit_id: cir.id,
                name: cir.name,
                role: cir.role,
                status: cir.status,
                bandwidth_gbps: cir.bandwidth_gbps,
                protocol: cir.protocol,
                cable_id: cb.id,
                cable_name: cb.name,
                cable_status: cb.status,
                backup_circuit_id: bck.id,
                backup_status: bck.status
            }) AS circuits,
            collect(DISTINCT {
                device_id: d.id,
                device_name: d.name,
                role: d.role,
                status: d.status,
                pop_id: p.id,
                pop_city: p.city,
                pop_country: p.country
            }) AS transit_devices,
            collect(DISTINCT {
                incident_id: inc.id,
                type: inc.type,
                severity: inc.severity,
                description: inc.description,
                started_at: inc.started_at
            }) AS active_incidents
        """
        with self.driver_wrapper.get_session() as session:
            record = session.run(query, cust_query=customer_query).single()
            if not record:
                return None
            return dict(record)

    def get_blast_radius(self, entity_id: str) -> Dict[str, Any]:
        """
        Calculates the topological blast radius for a given cable or device.
        """
        query = """
        MATCH (target) WHERE target.id = $entity_id
        OPTIONAL MATCH (target)<-[:TRAVERSES_CABLE|ROUTES_THROUGH*1..2]-(cir:Circuit)<-[:SUBSCRIBES_TO]-(c:Customer)-[:CONTRACTED_UNDER]->(s:SLA)
        OPTIONAL MATCH (cir)-[:HAS_FAILOVER_ROUTE]->(bck:Circuit)
        OPTIONAL MATCH (bck)-[:TRAVERSES_CABLE]->(bck_cb:Cable)
        RETURN 
            labels(target)[0] AS entity_type,
            target.id AS entity_id,
            target.name AS entity_name,
            target.status AS entity_status,
            collect(DISTINCT {
                customer_id: c.id,
                customer_name: c.name,
                customer_tier: c.tier,
                impacted_circuit: cir.id,
                impacted_circuit_name: cir.name,
                circuit_status: cir.status,
                backup_circuit_id: bck.id,
                backup_circuit_name: bck.name,
                backup_status: bck.status,
                backup_cable_id: bck_cb.id,
                backup_cable_name: bck_cb.name,
                sla_name: s.name,
                penalty_usd_per_hour: s.penalty_per_minute_usd * 60,
                max_downtime_minutes: s.max_downtime_minutes,
                protected: CASE WHEN bck IS NOT NULL AND bck.status = 'UP' THEN true ELSE false END
            }) AS impacted_customers
        """
        with self.driver_wrapper.get_session() as session:
            record = session.run(query, entity_id=entity_id).single()
            if not record:
                return {"entity_id": entity_id, "found": False}
            return dict(record)

    def get_severed_cables_and_backups(self) -> List[Dict[str, Any]]:
        """
        Retrieves all currently severed cables, failure details, impacted customer circuits,
        and whether automated backup/failover routes exist.
        """
        query = """
        MATCH (cb:Cable)
        WHERE cb.status = 'CUT'
        OPTIONAL MATCH (inc:Incident {status: 'OPEN'})-[:IMPACTS]->(cb)
        OPTIONAL MATCH (cir:Circuit)-[:TRAVERSES_CABLE]->(cb)
        OPTIONAL MATCH (cir)<-[:SUBSCRIBES_TO]-(cust:Customer)-[:CONTRACTED_UNDER]->(sla:SLA)
        OPTIONAL MATCH (cir)-[:HAS_FAILOVER_ROUTE]->(bck:Circuit)
        OPTIONAL MATCH (bck)-[:TRAVERSES_CABLE]->(bck_cb:Cable)
        RETURN 
            cb.id AS cable_id,
            cb.name AS cable_name,
            cb.status AS cable_status,
            cb.capacity_tbps AS capacity_tbps,
            inc.id AS incident_id,
            inc.description AS failure_reason,
            inc.started_at AS started_at,
            collect(DISTINCT {
                customer_id: cust.id,
                customer_name: cust.name,
                customer_tier: cust.tier,
                impacted_circuit_id: cir.id,
                impacted_circuit_name: cir.name,
                impacted_circuit_status: cir.status,
                backup_circuit_id: bck.id,
                backup_circuit_name: bck.name,
                backup_circuit_status: bck.status,
                backup_cable_id: bck_cb.id,
                backup_cable_name: bck_cb.name,
                is_protected: CASE WHEN bck IS NOT NULL AND bck.status = 'UP' THEN true ELSE false END,
                hourly_penalty_usd: sla.penalty_per_minute_usd * 60,
                max_downtime_minutes: sla.max_downtime_minutes
            }) AS impacted_circuits
        ORDER BY cb.name ASC
        """
        with self.driver_wrapper.get_session() as session:
            result = session.run(query)
            return [dict(record) for record in result]

    def detect_single_points_of_failure(self) -> List[Dict[str, Any]]:
        """
        Identifies circuits that have no backup route provisioned.
        """
        query = """
        MATCH (c:Customer)-[:SUBSCRIBES_TO]->(cir:Circuit {role: 'PRIMARY'})
        MATCH (c)-[:CONTRACTED_UNDER]->(s:SLA)
        WHERE NOT (cir)-[:HAS_FAILOVER_ROUTE]->(:Circuit)
        OPTIONAL MATCH (cir)-[:TRAVERSES_CABLE]->(cb:Cable)
        RETURN 
            c.id AS customer_id,
            c.name AS customer_name,
            c.tier AS customer_tier,
            cir.id AS circuit_id,
            cir.name AS circuit_name,
            cir.status AS circuit_status,
            cb.name AS transit_cable,
            s.name AS sla_name,
            s.penalty_per_minute_usd * 60 AS penalty_usd_per_hour,
            s.max_downtime_minutes AS allowed_downtime_mins
        ORDER BY penalty_usd_per_hour DESC
        """
        with self.driver_wrapper.get_session() as session:
            result = session.run(query)
            return [dict(record) for record in result]

    def get_network_health_summary(self) -> Dict[str, Any]:
        """
        Summarizes overall network asset health, broken cables/devices, and active SLA financial risk.
        """
        query = """
        MATCH (cb:Cable) WITH count(cb) AS total_cables, sum(CASE WHEN cb.status <> 'ACTIVE' THEN 1 ELSE 0 END) AS severed_cables
        MATCH (d:Device) WITH total_cables, severed_cables, count(d) AS total_devices, sum(CASE WHEN d.status <> 'HEALTHY' THEN 1 ELSE 0 END) AS failed_devices
        MATCH (cir:Circuit) WITH total_cables, severed_cables, total_devices, failed_devices, count(cir) AS total_circuits, sum(CASE WHEN cir.status = 'DOWN' THEN 1 ELSE 0 END) AS down_circuits
        OPTIONAL MATCH (inc:Incident {status: 'OPEN'})
        RETURN 
            total_cables, severed_cables,
            total_devices, failed_devices,
            total_circuits, down_circuits,
            count(inc) AS open_incidents
        """
        with self.driver_wrapper.get_session() as session:
            record = session.run(query).single()
            return dict(record) if record else {}

    def get_active_incidents_timeline(self) -> List[Dict[str, Any]]:
        """
        Retrieves all incidents with precise timestamps, descriptions, affected assets, and impacted tenants.
        """
        query = """
        MATCH (inc:Incident)
        OPTIONAL MATCH (inc)-[:IMPACTS]->(target)
        OPTIONAL MATCH (target)<-[:TRAVERSES_CABLE|ROUTES_THROUGH*1..2]-(cir:Circuit)<-[:SUBSCRIBES_TO]-(cust:Customer)-[:CONTRACTED_UNDER]->(sla:SLA)
        RETURN 
            inc.id AS incident_id,
            inc.type AS incident_type,
            inc.severity AS severity,
            inc.status AS status,
            inc.description AS description,
            inc.started_at AS started_at,
            inc.resolved_at AS resolved_at,
            labels(target)[0] AS target_type,
            target.name AS target_name,
            target.id AS target_id,
            collect(DISTINCT {
                customer_name: cust.name,
                circuit_id: cir.id,
                penalty_usd_per_hour: sla.penalty_per_minute_usd * 60,
                max_downtime_minutes: sla.max_downtime_minutes
            }) AS impacted_customers
        ORDER BY CASE WHEN inc.status = 'OPEN' THEN 0 ELSE 1 END, inc.started_at DESC
        LIMIT 3
        """
        with self.driver_wrapper.get_session() as session:
            result = session.run(query)
            return [dict(record) for record in result]
