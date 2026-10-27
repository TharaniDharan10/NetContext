import os
import logging
from typing import Dict, Any
from neo4j import GraphDatabase, Driver

from .peeringdb_client import PeeringDBClient
from .cable_topology import get_tata_cables
from .tenant_generator import get_enterprise_data

logger = logging.getLogger("cypher_migrator")

class CypherMigrator:
    def __init__(self, uri: str = None, user: str = None, password: str = None):
        self.uri = uri or os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.user = user or os.getenv("NEO4J_USER", "neo4j")
        self.password = password or os.getenv("NEO4J_PASSWORD", "NetContextSecure2026!")
        self.driver: Driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))

    def close(self):
        self.driver.close()

    def apply_schema_constraints(self):
        """Creates uniqueness constraints and performance indexes."""
        constraints = [
            "CREATE CONSTRAINT customer_id_unique IF NOT EXISTS FOR (c:Customer) REQUIRE c.id IS UNIQUE",
            "CREATE CONSTRAINT sla_id_unique IF NOT EXISTS FOR (s:SLA) REQUIRE s.id IS UNIQUE",
            "CREATE CONSTRAINT circuit_id_unique IF NOT EXISTS FOR (cir:Circuit) REQUIRE cir.id IS UNIQUE",
            "CREATE CONSTRAINT device_id_unique IF NOT EXISTS FOR (d:Device) REQUIRE d.id IS UNIQUE",
            "CREATE CONSTRAINT pop_id_unique IF NOT EXISTS FOR (p:POP) REQUIRE p.id IS UNIQUE",
            "CREATE CONSTRAINT cable_id_unique IF NOT EXISTS FOR (cb:Cable) REQUIRE cb.id IS UNIQUE",
            "CREATE CONSTRAINT incident_id_unique IF NOT EXISTS FOR (i:Incident) REQUIRE i.id IS UNIQUE",
        ]
        indexes = [
            "CREATE INDEX device_status_idx IF NOT EXISTS FOR (d:Device) ON (d.status)",
            "CREATE INDEX circuit_status_idx IF NOT EXISTS FOR (c:Circuit) ON (c.status)",
            "CREATE INDEX incident_status_idx IF NOT EXISTS FOR (i:Incident) ON (i.status)",
            "CREATE INDEX cable_status_idx IF NOT EXISTS FOR (cb:Cable) ON (cb.status)",
        ]

        with self.driver.session() as session:
            for query in constraints:
                session.run(query)
            for query in indexes:
                session.run(query)
        logger.info("Schema constraints and indexes successfully verified.")

    def seed_complete_context_graph(self) -> Dict[str, Any]:
        """
        Pulls real infrastructure from PeeringDB, cables from TeleGeography,
        and enterprise tenants, then builds the full context graph in Neo4j.
        """
        self.apply_schema_constraints()

        pops_data = PeeringDBClient().fetch_tata_infrastructure()
        cables_data = get_tata_cables()
        enterprise_data = get_enterprise_data()

        with self.driver.session() as session:
            # 1. Ingest POPs & Devices
            for pop in pops_data:
                session.run(
                    """
                    MERGE (p:POP {id: $id})
                    SET p.name = $name,
                        p.city = $city,
                        p.country = $country,
                        p.region = $region,
                        p.lat = $lat,
                        p.lon = $lon,
                        p.facility = $facility
                    """,
                    id=pop["id"], name=pop["name"], city=pop["city"],
                    country=pop["country"], region=pop["region"],
                    lat=pop["lat"], lon=pop["lon"], facility=pop["facility"]
                )

                for dev in pop.get("devices", []):
                    session.run(
                        """
                        MERGE (d:Device {id: $id})
                        SET d.name = $name,
                            d.role = $role,
                            d.model = $model,
                            d.ip = $ip,
                            d.status = 'HEALTHY'
                        MERGE (p:POP {id: $pop_id})
                        MERGE (d)-[:LOCATED_AT]->(p)
                        """,
                        id=dev["id"], name=dev["name"], role=dev["role"],
                        model=dev["model"], ip=dev["ip"], pop_id=pop["id"]
                    )

            # 2. Ingest Subsea Cables and link to landing POPs
            for cable in cables_data:
                session.run(
                    """
                    MERGE (cb:Cable {id: $id})
                    SET cb.name = $name,
                        cb.capacity_tbps = $capacity_tbps,
                        cb.length_km = $length_km,
                        cb.status = $status
                    """,
                    id=cable["id"], name=cable["name"],
                    capacity_tbps=cable["capacity_tbps"],
                    length_km=cable["length_km"], status=cable["status"]
                )
                for pop_id in cable.get("connected_pops", []):
                    session.run(
                        """
                        MATCH (p:POP {id: $pop_id}), (cb:Cable {id: $cable_id})
                        MERGE (p)-[:CONNECTED_VIA_CABLE]->(cb)
                        """,
                        pop_id=pop_id, cable_id=cable["id"]
                    )

            # 3. Ingest SLAs
            for sla in enterprise_data["slas"]:
                session.run(
                    """
                    MERGE (s:SLA {id: $id})
                    SET s.name = $name,
                        s.tier = $tier,
                        s.max_downtime_minutes = $max_downtime_minutes,
                        s.penalty_per_minute_usd = $penalty_per_minute_usd,
                        s.target_availability_pct = $target_availability_pct
                    """,
                    id=sla["id"], name=sla["name"], tier=sla["tier"],
                    max_downtime_minutes=sla["max_downtime_minutes"],
                    penalty_per_minute_usd=sla["penalty_per_minute_usd"],
                    target_availability_pct=sla["target_availability_pct"]
                )

            # 4. Ingest Customers and Circuits
            for cust in enterprise_data["customers"]:
                session.run(
                    """
                    MERGE (c:Customer {id: $id})
                    SET c.name = $name,
                        c.industry = $industry,
                        c.tier = $tier
                    MERGE (s:SLA {id: $sla_id})
                    MERGE (c)-[:CONTRACTED_UNDER]->(s)
                    """,
                    id=cust["id"], name=cust["name"],
                    industry=cust["industry"], tier=cust["tier"],
                    sla_id=cust["sla_id"]
                )

                for cir in cust.get("circuits", []):
                    session.run(
                        """
                        MERGE (cir:Circuit {id: $id})
                        SET cir.name = $name,
                            cir.bandwidth_gbps = $bandwidth_gbps,
                            cir.protocol = $protocol,
                            cir.role = $role,
                            cir.status = $status
                        MERGE (c:Customer {id: $cust_id})
                        MERGE (c)-[:SUBSCRIBES_TO]->(cir)
                        """,
                        id=cir["id"], name=cir["name"],
                        bandwidth_gbps=cir["bandwidth_gbps"],
                        protocol=cir["protocol"], role=cir["role"],
                        status=cir["status"], cust_id=cust["id"]
                    )

                    # Link circuit to transit cable
                    if cir.get("via_cable"):
                        session.run(
                            """
                            MATCH (cir:Circuit {id: $cir_id}), (cb:Cable {id: $cable_id})
                            MERGE (cir)-[:TRAVERSES_CABLE]->(cb)
                            """,
                            cir_id=cir["id"], cable_id=cir["via_cable"]
                        )

                    # Link circuit to transit devices
                    for dev_id in cir.get("devices", []):
                        session.run(
                            """
                            MATCH (cir:Circuit {id: $cir_id}), (d:Device {id: $dev_id})
                            MERGE (cir)-[:ROUTES_THROUGH]->(d)
                            """,
                            cir_id=cir["id"], dev_id=dev_id
                        )

            # 5. Link Circuit Failover / Backup pairs
            for cust in enterprise_data["customers"]:
                for cir in cust.get("circuits", []):
                    failover_id = cir.get("failover_circuit_id")
                    if failover_id:
                        session.run(
                            """
                            MATCH (pri:Circuit {id: $pri_id}), (bck:Circuit {id: $bck_id})
                            MERGE (pri)-[:HAS_FAILOVER_ROUTE]->(bck)
                            """,
                            pri_id=cir["id"], bck_id=failover_id
                        )

        logger.info("Successfully populated NetContext Graph with real Tata infrastructure and enterprise tenants.")
        return self.get_graph_statistics()

    def get_graph_statistics(self) -> Dict[str, int]:
        """Returns node and edge counts across all entity labels."""
        with self.driver.session() as session:
            nodes_res = session.run("MATCH (n) RETURN count(n) AS node_count").single()
            edges_res = session.run("MATCH ()-[r]->() RETURN count(r) AS rel_count").single()
            labels_res = session.run("CALL db.labels() YIELD label RETURN collect(label) AS labels").single()

            return {
                "nodes": nodes_res["node_count"] if nodes_res else 0,
                "relationships": edges_res["rel_count"] if edges_res else 0,
                "labels": labels_res["labels"] if labels_res else []
            }
