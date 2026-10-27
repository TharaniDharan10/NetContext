import os
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List
from neo4j import GraphDatabase, Driver

class IncidentStreamer:
    def __init__(self, uri: str = None, user: str = None, password: str = None):
        self.uri = uri or os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.user = user or os.getenv("NEO4J_USER", "neo4j")
        self.password = password or os.getenv("NEO4J_PASSWORD", "NetContextSecure2026!")
        self.driver: Driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))

    def close(self):
        self.driver.close()

    def simulate_cable_cut(self, cable_id: str, reason: str = "Subsea fiber anchor drag cut") -> Dict[str, Any]:
        """
        Simulates an undersea fiber optic cable cut event in real time.
        Mutates the Cable, degrades linked Circuits, creates an Incident, and computes blast radius.
        """
        incident_id = f"INC-CABLE-{uuid.uuid4().hex[:6].upper()}"
        now_iso = datetime.now(timezone.utc).isoformat()

        with self.driver.session() as session:
            # 1. Update cable status and create incident
            session.run(
                """
                MATCH (cb:Cable {id: $cable_id})
                SET cb.status = 'CUT'
                CREATE (inc:Incident {
                    id: $incident_id,
                    type: 'CABLE_CUT',
                    severity: 'CRITICAL',
                    status: 'OPEN',
                    description: $reason,
                    started_at: $now_iso
                })
                MERGE (inc)-[:IMPACTS]->(cb)
                """,
                cable_id=cable_id, incident_id=incident_id,
                reason=reason, now_iso=now_iso
            )

            # 2. Mutate affected circuits
            session.run(
                """
                MATCH (cir:Circuit)-[:TRAVERSES_CABLE]->(cb:Cable {id: $cable_id})
                SET cir.status = 'DOWN'
                """,
                cable_id=cable_id
            )

            # 3. Compute real-time topological blast radius and customer SLA liability
            result = session.run(
                """
                MATCH (cb:Cable {id: $cable_id})<-[:TRAVERSES_CABLE]-(cir:Circuit)<-[:SUBSCRIBES_TO]-(cust:Customer)-[:CONTRACTED_UNDER]->(sla:SLA)
                OPTIONAL MATCH (cir)-[:HAS_FAILOVER_ROUTE]->(backup:Circuit)
                RETURN 
                    cust.id AS customer_id,
                    cust.name AS customer_name,
                    cust.tier AS customer_tier,
                    cir.id AS impacted_circuit,
                    backup.id AS backup_circuit_id,
                    backup.status AS backup_status,
                    sla.penalty_per_minute_usd * 60 AS liability_usd_per_hour,
                    sla.max_downtime_minutes AS allowed_downtime_minutes
                """,
                cable_id=cable_id
            )

            impacted_customers: List[Dict[str, Any]] = []
            total_hourly_risk = 0.0

            for record in result:
                has_active_backup = (record["backup_status"] == "UP")
                hourly_liability = float(record["liability_usd_per_hour"] or 0)
                if not has_active_backup:
                    total_hourly_risk += hourly_liability

                impacted_customers.append({
                    "customer_id": record["customer_id"],
                    "customer_name": record["customer_name"],
                    "customer_tier": record["customer_tier"],
                    "impacted_circuit": record["impacted_circuit"],
                    "backup_circuit_id": record["backup_circuit_id"],
                    "backup_status": record["backup_status"],
                    "service_state": "FAILOVER_REROUTED" if has_active_backup else "OUTAGE_ACTIVE",
                    "hourly_liability_usd": hourly_liability,
                    "max_downtime_minutes": record["allowed_downtime_minutes"]
                })

            return {
                "incident_id": incident_id,
                "target_cable": cable_id,
                "event_type": "CABLE_CUT",
                "severity": "CRITICAL",
                "status": "OPEN",
                "started_at": now_iso,
                "total_impacted_customers": len(impacted_customers),
                "total_unprotected_hourly_risk_usd": round(total_hourly_risk, 2),
                "blast_radius": impacted_customers
            }

    def simulate_device_failure(self, device_id: str, reason: str = "BGP engine linecard failure") -> Dict[str, Any]:
        """
        Simulates a core or edge router failure in real time.
        """
        incident_id = f"INC-DEV-{uuid.uuid4().hex[:6].upper()}"
        now_iso = datetime.now(timezone.utc).isoformat()

        with self.driver.session() as session:
            # 1. Update device status and create incident
            session.run(
                """
                MATCH (d:Device {id: $device_id})
                SET d.status = 'FAILED'
                CREATE (inc:Incident {
                    id: $incident_id,
                    type: 'DEVICE_FAILURE',
                    severity: 'CRITICAL',
                    status: 'OPEN',
                    description: $reason,
                    started_at: $now_iso
                })
                MERGE (inc)-[:IMPACTS]->(d)
                """,
                device_id=device_id, incident_id=incident_id,
                reason=reason, now_iso=now_iso
            )

            # 2. Mutate affected circuits
            session.run(
                """
                MATCH (cir:Circuit)-[:ROUTES_THROUGH]->(d:Device {id: $device_id})
                SET cir.status = 'DOWN'
                """,
                device_id=device_id
            )

            # 3. Compute blast radius
            result = session.run(
                """
                MATCH (d:Device {id: $device_id})<-[:ROUTES_THROUGH]-(cir:Circuit)<-[:SUBSCRIBES_TO]-(cust:Customer)-[:CONTRACTED_UNDER]->(sla:SLA)
                OPTIONAL MATCH (cir)-[:HAS_FAILOVER_ROUTE]->(backup:Circuit)
                RETURN 
                    cust.id AS customer_id,
                    cust.name AS customer_name,
                    cust.tier AS customer_tier,
                    cir.id AS impacted_circuit,
                    backup.id AS backup_circuit_id,
                    backup.status AS backup_status,
                    sla.penalty_per_minute_usd * 60 AS liability_usd_per_hour,
                    sla.max_downtime_minutes AS allowed_downtime_minutes
                """,
                device_id=device_id
            )

            impacted_customers = []
            total_hourly_risk = 0.0
            for record in result:
                has_active_backup = (record["backup_status"] == "UP")
                hourly_liability = float(record["liability_usd_per_hour"] or 0)
                if not has_active_backup:
                    total_hourly_risk += hourly_liability

                impacted_customers.append({
                    "customer_id": record["customer_id"],
                    "customer_name": record["customer_name"],
                    "customer_tier": record["customer_tier"],
                    "impacted_circuit": record["impacted_circuit"],
                    "backup_circuit_id": record["backup_circuit_id"],
                    "backup_status": record["backup_status"],
                    "service_state": "FAILOVER_REROUTED" if has_active_backup else "OUTAGE_ACTIVE",
                    "hourly_liability_usd": hourly_liability,
                    "max_downtime_minutes": record["allowed_downtime_minutes"]
                })

            return {
                "incident_id": incident_id,
                "target_device": device_id,
                "event_type": "DEVICE_FAILURE",
                "severity": "CRITICAL",
                "status": "OPEN",
                "started_at": now_iso,
                "total_impacted_customers": len(impacted_customers),
                "total_unprotected_hourly_risk_usd": round(total_hourly_risk, 2),
                "blast_radius": impacted_customers
            }

    def resolve_incident(self, incident_id: str) -> Dict[str, Any]:
        """
        Resolves an active incident and restores impacted hardware and circuits.
        """
        now_iso = datetime.now(timezone.utc).isoformat()

        with self.driver.session() as session:
            # 1. Resolve incident node
            session.run(
                """
                MATCH (inc:Incident {id: $incident_id})
                SET inc.status = 'RESOLVED',
                    inc.resolved_at = $now_iso
                """,
                incident_id=incident_id, now_iso=now_iso
            )

            # 2. Restore connected cables and devices
            session.run(
                """
                MATCH (inc:Incident {id: $incident_id})-[:IMPACTS]->(target)
                FOREACH (cb IN CASE WHEN target:Cable THEN [target] ELSE [] END | SET cb.status = 'ACTIVE')
                FOREACH (d IN CASE WHEN target:Device THEN [target] ELSE [] END | SET d.status = 'HEALTHY')
                """,
                incident_id=incident_id
            )

            # 3. Restore circuits
            session.run(
                """
                MATCH (cir:Circuit)
                WHERE NOT EXISTS {
                    MATCH (cir)-[:TRAVERSES_CABLE]->(cb:Cable {status: 'CUT'})
                } AND NOT EXISTS {
                    MATCH (cir)-[:ROUTES_THROUGH]->(d:Device {status: 'FAILED'})
                }
                SET cir.status = 'UP'
                """
            )

            # 4. Clean up dynamic failover emergency circuits
            session.run(
                """
                MATCH (bck:Circuit {role: 'DYNAMIC_FAILOVER'})
                DETACH DELETE bck
                """
            )

        return {
            "incident_id": incident_id,
            "status": "RESOLVED",
            "resolved_at": now_iso,
            "message": "Incident resolved, dynamic failovers cleared, and network circuits restored to UP status."
        }

    def get_active_incidents(self) -> List[Dict[str, Any]]:
        """Returns all open network incidents with affected assets."""
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (inc:Incident {status: 'OPEN'})-[:IMPACTS]->(target)
                RETURN 
                    inc.id AS id,
                    inc.type AS type,
                    inc.severity AS severity,
                    inc.description AS description,
                    inc.started_at AS started_at,
                    labels(target)[0] AS target_type,
                    target.id AS target_id,
                    target.name AS target_name
                ORDER BY inc.started_at DESC
                """
            )
            return [dict(record) for record in result]

    def calculate_total_live_sla_risk(self) -> Dict[str, Any]:
        """
        Calculates real-time live SLA breach liability ($/hr) dynamically across all active incidents.
        Only unprotected primary circuits (down without an active backup) contribute to immediate financial exposure.
        """
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (inc:Incident {status: 'OPEN'})-[:IMPACTS]->(target)
                MATCH (target)<-[:TRAVERSES_CABLE|ROUTES_THROUGH*1..2]-(pri:Circuit {role: 'PRIMARY'})
                WHERE pri.status = 'DOWN'
                MATCH (pri)<-[:SUBSCRIBES_TO]-(cust:Customer)-[:CONTRACTED_UNDER]->(sla:SLA)
                OPTIONAL MATCH (pri)-[:HAS_FAILOVER_ROUTE]->(backup:Circuit)
                WITH cust, pri, target, sla, backup,
                     CASE WHEN backup IS NOT NULL AND backup.status = 'UP' THEN true ELSE false END AS is_protected
                WHERE is_protected = false
                RETURN 
                    cust.id AS customer_id,
                    cust.name AS customer_name,
                    cust.tier AS customer_tier,
                    pri.id AS circuit_id,
                    pri.name AS circuit_name,
                    labels(target)[0] AS target_type,
                    target.id AS target_id,
                    target.name AS target_name,
                    sla.penalty_per_minute_usd * 60 AS hourly_liability_usd,
                    sla.max_downtime_minutes AS max_downtime_minutes
                """
            )
            records = [dict(r) for r in result]
            total_hourly_risk = sum(r["hourly_liability_usd"] for r in records)
            return {
                "total_sla_risk_usd_per_hour": round(total_hourly_risk, 2),
                "unprotected_count": len(records),
                "unprotected_circuits": records
            }

    def get_impacted_customers_all_incidents(self) -> List[Dict[str, Any]]:
        """
        Returns all enterprise customers and circuits impacted by currently open incidents,
        whether primary or backup, along with SLA contract liability and current mitigation status.
        """
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (inc:Incident {status: 'OPEN'})-[:IMPACTS]->(target)
                MATCH (target)<-[:TRAVERSES_CABLE|ROUTES_THROUGH*1..2]-(cir:Circuit)<-[:SUBSCRIBES_TO]-(cust:Customer)-[:CONTRACTED_UNDER]->(sla:SLA)
                OPTIONAL MATCH (cir)-[:HAS_FAILOVER_ROUTE]->(backup:Circuit)
                RETURN DISTINCT
                    inc.id AS incident_id,
                    target.id AS severed_asset_id,
                    target.name AS severed_asset_name,
                    cust.id AS customer_id,
                    cust.name AS customer_name,
                    cust.tier AS customer_tier,
                    cir.id AS circuit_id,
                    cir.name AS circuit_name,
                    cir.role AS circuit_role,
                    cir.status AS circuit_status,
                    sla.max_downtime_minutes AS max_downtime_minutes,
                    sla.penalty_per_minute_usd * 60 AS hourly_liability_usd,
                    CASE 
                        WHEN cir.status = 'REROUTED' THEN 'FAILOVER ACTIVE'
                        WHEN cir.role = 'PRIMARY' AND backup IS NOT NULL AND backup.status = 'UP' THEN 'STANDBY BACKUP RUNNING'
                        WHEN cir.role = 'PRIMARY' THEN 'CRITICAL SLA OUTAGE'
                        ELSE 'DEGRADED REDUNDANCY'
                    END AS mitigation_status
                ORDER BY hourly_liability_usd DESC
                """
            )
            return [dict(r) for r in result]

    def get_reroute_recommendations(self) -> List[Dict[str, Any]]:
        """
        Scans for currently DOWN primary circuits that lack an active backup route,
        identifies their exact source and destination POPs, and uses Neo4j topological
        pathfinding (shortestPath) to compute a geographically valid alternative route
        connecting the same endpoints through healthy cables.
        """
        with self.driver.session() as session:
            # 1. Find all down primary circuits lacking an active backup
            down_circuits_res = session.run(
                """
                MATCH (inc:Incident {status: 'OPEN'})-[:IMPACTS]->(target)
                MATCH (target)<-[:TRAVERSES_CABLE|ROUTES_THROUGH*1..2]-(pri:Circuit {role: 'PRIMARY'})
                WHERE pri.status = 'DOWN'
                MATCH (pri)<-[:SUBSCRIBES_TO]-(cust:Customer)-[:CONTRACTED_UNDER]->(sla:SLA)
                OPTIONAL MATCH (pri)-[:HAS_FAILOVER_ROUTE]->(backup:Circuit)
                WITH cust, pri, target, sla, backup,
                     CASE WHEN backup IS NOT NULL AND backup.status = 'UP' THEN true ELSE false END AS is_protected
                WHERE is_protected = false
                MATCH (pri)-[:ROUTES_THROUGH]->(d:Device)-[:LOCATED_AT]->(p:POP)
                RETURN 
                    cust.id AS customer_id,
                    cust.name AS customer_name,
                    cust.tier AS customer_tier,
                    pri.id AS circuit_id,
                    pri.name AS circuit_name,
                    target.id AS severed_asset_id,
                    target.name AS severed_asset_name,
                    sla.penalty_per_minute_usd * 60 AS hourly_liability_usd,
                    sla.max_downtime_minutes AS max_downtime_minutes,
                    collect(DISTINCT {id: p.id, name: p.name, city: p.city}) AS endpoint_pops
                """
            )
            records = [dict(r) for r in down_circuits_res]
            recommendations = []

            for r in records:
                endpoints = r.get("endpoint_pops", [])
                src_city = endpoints[0]["city"] if len(endpoints) > 0 else "Source"
                dst_city = endpoints[1]["city"] if len(endpoints) > 1 else "Destination"
                severed_id = r["severed_asset_id"]

                chosen_cable_id = "CABLE-SMW4"
                chosen_cable_name = "SMW-4"
                action_desc = ""

                if len(endpoints) >= 2:
                    src_id = endpoints[0]["id"]
                    dst_id = endpoints[1]["id"]

                    # 2. Topological shortestPath between the circuit's actual endpoints
                    path_res = session.run(
                        """
                        MATCH (src:POP {id: $src_id}), (dst:POP {id: $dst_id})
                        OPTIONAL MATCH path = shortestPath((src)-[:CONNECTED_VIA_CABLE*..10]-(dst))
                        WHERE ALL(n IN nodes(path) WHERE NOT (n:Cable AND (n.status = 'CUT' OR n.id = $severed_id)))
                        RETURN 
                            [n IN nodes(path) WHERE n:Cable] AS route_cables,
                            [n IN nodes(path) WHERE n:POP | n.city] AS route_cities
                        """,
                        src_id=src_id, dst_id=dst_id, severed_id=severed_id
                    ).single()

                    if path_res and path_res["route_cables"]:
                        route_cables = path_res["route_cables"]
                        route_cities = path_res["route_cities"]
                        chosen_cable = route_cables[0]
                        chosen_cable_id = chosen_cable["id"]
                        chosen_cable_name = chosen_cable["name"]

                        if len(route_cables) == 1:
                            action_desc = (
                                f"Enact autonomous SD-WAN failover for {r['customer_name']} via {chosen_cable_name} "
                                f"({src_city} ↔ {dst_city} direct bypass) to arrest ${r['hourly_liability_usd']:,.2f}/hr SLA penalties."
                            )
                        else:
                            transit_path = " ➔ ".join(route_cities)
                            action_desc = (
                                f"Enact autonomous SD-WAN failover for {r['customer_name']} via {chosen_cable_name} "
                                f"over global mesh detour ({transit_path}) to arrest ${r['hourly_liability_usd']:,.2f}/hr SLA penalties."
                            )
                    else:
                        # Fallback if both endpoints are isolated within Tata's own cables
                        action_desc = (
                            f"Enact autonomous SD-WAN failover for {r['customer_name']} via Partner IXP Transit "
                            f"({src_city} ↔ {dst_city} European Interconnect) to arrest ${r['hourly_liability_usd']:,.2f}/hr SLA penalties."
                        )
                else:
                    action_desc = f"Enact autonomous SD-WAN failover for {r['customer_name']} to arrest ${r['hourly_liability_usd']:,.2f}/hr SLA penalties."

                recommendations.append({
                    "customer_id": r["customer_id"],
                    "customer_name": r["customer_name"],
                    "customer_tier": r.get("customer_tier", "Enterprise"),
                    "circuit_id": r["circuit_id"],
                    "circuit_name": r["circuit_name"],
                    "severed_asset_id": r["severed_asset_id"],
                    "severed_asset_name": r["severed_asset_name"],
                    "hourly_liability_usd": round(r["hourly_liability_usd"], 2),
                    "max_downtime_minutes": r["max_downtime_minutes"],
                    "recommended_cable_id": chosen_cable_id,
                    "recommended_cable_name": chosen_cable_name,
                    "action_description": action_desc
                })

            return recommendations

    def execute_failover_reroute(self, customer_id: str, circuit_id: str, target_cable_id: str = "CABLE-SMW4") -> Dict[str, Any]:
        """
        Executes an agentic dynamic failover reroute in Neo4j:
        - Creates/updates a dynamic failover circuit (DYNAMIC_FAILOVER)
        - Links it to the customer, primary circuit, and candidate healthy cable
        - Sets primary circuit status to 'REROUTED'
        - Creates a RemediationAction audit record
        - Eliminates active SLA financial liability
        """
        action_id = f"ACT-REROUTE-{uuid.uuid4().hex[:6].upper()}"
        now_iso = datetime.now(timezone.utc).isoformat()
        dyn_circuit_id = f"{circuit_id}-DYN-BCK"

        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (cust:Customer {id: $customer_id})-[:SUBSCRIBES_TO]->(cir:Circuit {id: $circuit_id})
                MATCH (cb:Cable {id: $target_cable_id})
                MERGE (bck:Circuit {id: $dyn_circuit_id})
                ON CREATE SET 
                    bck.name = cir.name + ' [Agentic Failover via ' + cb.name + ']',
                    bck.bandwidth_gbps = cir.bandwidth_gbps,
                    bck.protocol = 'SD_WAN_EMERGENCY',
                    bck.role = 'DYNAMIC_FAILOVER',
                    bck.status = 'UP',
                    bck.created_at = $now_iso
                ON MATCH SET
                    bck.status = 'UP'
                MERGE (cir)-[:HAS_FAILOVER_ROUTE]->(bck)
                MERGE (bck)-[:TRAVERSES_CABLE]->(cb)
                MERGE (cust)-[:SUBSCRIBES_TO]->(bck)
                SET cir.status = 'REROUTED'
                SET cir.failover_active_at = $now_iso
                CREATE (act:RemediationAction {
                    id: $action_id,
                    type: 'AUTONOMOUS_FAILOVER_REROUTE',
                    customer_id: $customer_id,
                    customer_name: cust.name,
                    circuit_id: $circuit_id,
                    backup_circuit_id: bck.id,
                    target_cable_id: cb.id,
                    target_cable_name: cb.name,
                    executed_at: $now_iso,
                    status: 'COMPLETED'
                })
                RETURN cust.name AS customer_name, cir.name AS circuit_name, cb.name AS cable_name
                """,
                customer_id=customer_id, circuit_id=circuit_id,
                target_cable_id=target_cable_id, dyn_circuit_id=dyn_circuit_id,
                action_id=action_id, now_iso=now_iso
            )
            rec = result.single()
            if not rec:
                raise ValueError(f"Customer {customer_id} or Circuit {circuit_id} not found in Knowledge Graph.")

            return {
                "status": "SUCCESS",
                "action_id": action_id,
                "customer_id": customer_id,
                "customer_name": rec["customer_name"],
                "circuit_id": circuit_id,
                "backup_circuit_id": dyn_circuit_id,
                "rerouted_via_cable": rec["cable_name"],
                "circuit_status": "REROUTED",
                "sla_risk_status": "PROTECTED",
                "executed_at": now_iso,
                "message": f"Autonomous failover enacted for {rec['customer_name']}. Circuit rerouted via {rec['cable_name']}. SLA penalty eliminated ($0.00/hr)."
            }
