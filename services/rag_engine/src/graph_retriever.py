import json
from typing import Dict, Any, Tuple
from .cypher_repo import CypherRepository

class GraphRetriever:
    def __init__(self):
        self.repo = CypherRepository()

    def retrieve_context_for_query(self, user_query: str) -> Tuple[str, Dict[str, Any]]:
        """
        Parses natural language prompt for entity keywords, executes targeted
        multi-hop Cypher queries, and formats structured topological context.
        """
        lower_q = user_query.lower()
        context_data: Dict[str, Any] = {}
        context_type = "GENERAL_NETWORK"

        # 1. Always retrieve live baseline: severed cables, active incidents timeline, and health summary
        severed_cables = self.repo.get_severed_cables_and_backups()
        context_data["severed_cables"] = severed_cables

        incidents_timeline = self.repo.get_active_incidents_timeline()
        context_data["active_incidents"] = incidents_timeline

        health_summary = self.repo.get_network_health_summary()
        context_data["network_summary"] = health_summary

        # 2. Customer-specific query
        customer_keywords = ["skyair", "apex", "transglobal", "omniretail", "cust-"]
        for kw in customer_keywords:
            if kw in lower_q:
                subgraph = self.repo.get_customer_subgraph(kw)
                if subgraph:
                    context_data["customer_context"] = subgraph
                    context_type = "CUSTOMER_OUTAGE"
                    return context_type, context_data

        # 3. Check for specific named cable in query
        cable_id_map = {
            "tgn-tic": "CABLE-TGN-TIC",
            "tgn-atlantic": "CABLE-TGN-ATLANTIC",
            "tgn-pacific": "CABLE-TGN-PACIFIC",
            "smw4": "CABLE-SMW4",
            "smw-4": "CABLE-SMW4",
            "europe-ring": "CABLE-EUROPE-RING",
            "europe ring": "CABLE-EUROPE-RING",
            "tgn-intra-asia": "CABLE-TGN-INTRA-ASIA",
            "tgn-ia": "CABLE-TGN-INTRA-ASIA"
        }
        for kw, cid in cable_id_map.items():
            if kw in lower_q:
                blast = self.repo.get_blast_radius(cid)
                context_data["infrastructure_blast_radius"] = blast
                context_type = "CABLE_OUTAGE_AND_BACKUP"
                return context_type, context_data

        # 4. Cable cut, severed cable, or backup/failover route query
        # Catches questions like "which cable is cut", "is there a backup for it", "what is the failover", etc.
        cable_cut_backup_terms = [
            "which cable", "cable is cut", "cable cut", "cable severed", "severed",
            "backup", "failover", "reroute", "redundancy", "is there a backup",
            "any backup", "backup route", "broken cable", "damaged cable", "cut"
        ]
        if any(term in lower_q for term in cable_cut_backup_terms) or ("cable" in lower_q and severed_cables):
            context_type = "CABLE_OUTAGE_AND_BACKUP"
            return context_type, context_data

        # 5. Incident Timeline & Event Time query
        incident_time_keywords = ["time", "when", "incident", "timestamp", "duration", "clock", "date", "happened", "started"]
        if any(w in lower_q for w in incident_time_keywords):
            context_type = "INCIDENT_TIMELINE"
            return context_type, context_data

        # 6. Single Point of Failure (SPOF) query
        if any(w in lower_q for w in ["spof", "single point", "unprotected", "vulnerability", "audit"]):
            spof_data = self.repo.detect_single_points_of_failure()
            context_data["single_points_of_failure"] = spof_data
            context_type = "SPOF_AUDIT"
            return context_type, context_data

        # 7. Default to general network health overview
        return context_type, context_data
