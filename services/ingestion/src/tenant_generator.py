from typing import List, Dict, Any

ENTERPRISE_SLAS: List[Dict[str, Any]] = [
    {
        "id": "SLA-CRITICAL-AIRLINE",
        "tier": "TIER_1",
        "name": "Mission-Critical Aviation Flight Operations SLA",
        "max_downtime_minutes": 15,
        "penalty_per_minute_usd": 416.67,  # $25,000 per hour
        "target_availability_pct": 99.999
    },
    {
        "id": "SLA-CRITICAL-FINANCE",
        "tier": "TIER_1",
        "name": "Tier-1 High-Frequency Financial Settlement SLA",
        "max_downtime_minutes": 5,
        "penalty_per_minute_usd": 583.33,  # $35,000 per hour
        "target_availability_pct": 99.999
    },
    {
        "id": "SLA-STANDARD-LOGISTICS",
        "tier": "TIER_2",
        "name": "Enterprise Maritime Logistics Telemetry SLA",
        "max_downtime_minutes": 30,
        "penalty_per_minute_usd": 100.00,  # $6,000 per hour
        "target_availability_pct": 99.95
    },
    {
        "id": "SLA-STANDARD-RETAIL",
        "tier": "TIER_2",
        "name": "Omnichannel Global E-Commerce SLA",
        "max_downtime_minutes": 45,
        "penalty_per_minute_usd": 133.33,  # $8,000 per hour
        "target_availability_pct": 99.90
    }
]

ENTERPRISE_CUSTOMERS: List[Dict[str, Any]] = [
    {
        "id": "CUST-SKYAIR-01",
        "name": "SkyAir Global Airlines",
        "industry": "Aviation",
        "tier": "TIER_1",
        "sla_id": "SLA-CRITICAL-AIRLINE",
        "circuits": [
            {
                "id": "CIR-SKYAIR-PRI",
                "name": "SkyAir APAC Core Trunk (SIN-CHE)",
                "bandwidth_gbps": 10,
                "protocol": "MPLS",
                "role": "PRIMARY",
                "status": "UP",
                "via_cable": "CABLE-TGN-TIC",
                "devices": ["DEV-SG-CR01", "DEV-CHE-CR01"],
                "failover_circuit_id": "CIR-SKYAIR-BCK"
            },
            {
                "id": "CIR-SKYAIR-BCK",
                "name": "SkyAir APAC Failover Trunk (SIN-TYO)",
                "bandwidth_gbps": 5,
                "protocol": "SD_WAN",
                "role": "BACKUP",
                "status": "UP",
                "via_cable": "CABLE-TGN-INTRA-ASIA",
                "devices": ["DEV-SG-CR01", "DEV-TYO-CR01"],
                "failover_circuit_id": None
            }
        ]
    },
    {
        "id": "CUST-APEX-01",
        "name": "Apex Global Banking Corp",
        "industry": "Banking & Financial Services",
        "tier": "TIER_1",
        "sla_id": "SLA-CRITICAL-FINANCE",
        "circuits": [
            {
                "id": "CIR-APEX-PRI",
                "name": "Apex Transatlantic Low-Latency Link (NYC-LON)",
                "bandwidth_gbps": 40,
                "protocol": "MPLS",
                "role": "PRIMARY",
                "status": "UP",
                "via_cable": "CABLE-TGN-ATLANTIC",
                "devices": ["DEV-NYC-CR01", "DEV-LON-CR01"],
                "failover_circuit_id": "CIR-APEX-BCK"
            },
            {
                "id": "CIR-APEX-BCK",
                "name": "Apex Pacific Alternate Link (NYC-TYO)",
                "bandwidth_gbps": 10,
                "protocol": "SD_WAN",
                "role": "BACKUP",
                "status": "UP",
                "via_cable": "CABLE-TGN-PACIFIC",
                "devices": ["DEV-NYC-CR01", "DEV-TYO-CR01"],
                "failover_circuit_id": None
            }
        ]
    },
    {
        "id": "CUST-TRANS-01",
        "name": "TransGlobal Maritime Logistics",
        "industry": "Logistics & Supply Chain",
        "tier": "TIER_2",
        "sla_id": "SLA-STANDARD-LOGISTICS",
        "circuits": [
            {
                "id": "CIR-TRANS-PRI",
                "name": "TransGlobal Euro-Asia Pipeline (MUM-MRS)",
                "bandwidth_gbps": 5,
                "protocol": "IP_TRANSIT",
                "role": "PRIMARY",
                "status": "UP",
                "via_cable": "CABLE-SMW4",
                "devices": ["DEV-MUM-CR01", "DEV-MRS-CR01"],
                "failover_circuit_id": "CIR-TRANS-BCK"
            },
            {
                "id": "CIR-TRANS-BCK",
                "name": "TransGlobal Europe Ring (MRS-FRA)",
                "bandwidth_gbps": 2,
                "protocol": "SD_WAN",
                "role": "BACKUP",
                "status": "UP",
                "via_cable": "CABLE-EUROPE-RING",
                "devices": ["DEV-MRS-CR01", "DEV-FRA-CR01"],
                "failover_circuit_id": None
            }
        ]
    },
    {
        "id": "CUST-OMNI-01",
        "name": "OmniRetail Global Commerce",
        "industry": "E-Commerce",
        "tier": "TIER_2",
        "sla_id": "SLA-STANDARD-RETAIL",
        "circuits": [
            {
                "id": "CIR-OMNI-PRI",
                "name": "OmniRetail Euro Core (LON-FRA)",
                "bandwidth_gbps": 20,
                "protocol": "MPLS",
                "role": "PRIMARY",
                "status": "UP",
                "via_cable": "CABLE-EUROPE-RING",
                "devices": ["DEV-LON-CR01", "DEV-FRA-CR01"],
                "failover_circuit_id": None  # Intentionally no backup circuit to demonstrate SLA breach risk!
            }
        ]
    },
    {
        "id": "CUST-NEXUS-01",
        "name": "Nexus AI & Cloud Hyperscaler",
        "industry": "Cloud & AI Infrastructure",
        "tier": "TIER_1",
        "sla_id": "SLA-CRITICAL-FINANCE",
        "circuits": [
            {
                "id": "CIR-NEXUS-PRI",
                "name": "Nexus Trans-Pacific AI Highway (LAX-TYO)",
                "bandwidth_gbps": 100,
                "protocol": "MPLS",
                "role": "PRIMARY",
                "status": "UP",
                "via_cable": "CABLE-TGN-PACIFIC",
                "devices": ["DEV-NYC-CR01", "DEV-TYO-CR01"],
                "failover_circuit_id": "CIR-NEXUS-BCK"
            },
            {
                "id": "CIR-NEXUS-BCK",
                "name": "Nexus Trans-Pacific Secondary (LAX-TYO)",
                "bandwidth_gbps": 40,
                "protocol": "SD_WAN",
                "role": "BACKUP",
                "status": "UP",
                "via_cable": "CABLE-TGN-INTRA-ASIA",
                "devices": ["DEV-SG-CR01", "DEV-TYO-CR01"],
                "failover_circuit_id": None
            }
        ]
    },
    {
        "id": "CUST-PACIFIC-01",
        "name": "Pacific Star Media & Broadcast",
        "industry": "Digital Media & Streaming",
        "tier": "TIER_2",
        "sla_id": "SLA-STANDARD-LOGISTICS",
        "circuits": [
            {
                "id": "CIR-PACIFIC-PRI",
                "name": "Pacific Star Broadcast Corridor (TYO-SIN)",
                "bandwidth_gbps": 10,
                "protocol": "IP_TRANSIT",
                "role": "PRIMARY",
                "status": "UP",
                "via_cable": "CABLE-TGN-INTRA-ASIA",
                "devices": ["DEV-TYO-CR01", "DEV-SG-CR01"],
                "failover_circuit_id": None
            }
        ]
    }
]

def get_enterprise_data() -> Dict[str, Any]:
    return {
        "slas": ENTERPRISE_SLAS,
        "customers": ENTERPRISE_CUSTOMERS
    }
