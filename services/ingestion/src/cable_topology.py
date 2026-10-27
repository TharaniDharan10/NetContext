from typing import List, Dict, Any

# Real Submarine & Terrestrial Optical Systems operated by Tata Communications
TATA_SUBSEA_CABLES: List[Dict[str, Any]] = [
    {
        "id": "CABLE-TGN-TIC",
        "name": "Tata Indicom Cable (TGN-TIC)",
        "capacity_tbps": 5.12,
        "length_km": 3175,
        "landing_points": ["Chennai, India", "Singapore"],
        "connected_pops": ["POP-CHE-01", "POP-SG-01"],
        "status": "ACTIVE"
    },
    {
        "id": "CABLE-TGN-ATLANTIC",
        "name": "Tata Global Network Atlantic (TGN-Atlantic)",
        "capacity_tbps": 10.2,
        "length_km": 13000,
        "landing_points": ["New York, US", "Bude / Highbridge, UK"],
        "connected_pops": ["POP-NYC-01", "POP-LON-01"],
        "status": "ACTIVE"
    },
    {
        "id": "CABLE-TGN-PACIFIC",
        "name": "Tata Global Network Pacific (TGN-Pacific)",
        "capacity_tbps": 9.6,
        "length_km": 22000,
        "landing_points": ["Los Angeles / Oregon, US", "Toyohashi, Japan"],
        "connected_pops": ["POP-NYC-01", "POP-TYO-01"],
        "status": "ACTIVE"
    },
    {
        "id": "CABLE-SMW4",
        "name": "South East Asia - Middle East - Western Europe 4 (SMW-4)",
        "capacity_tbps": 4.8,
        "length_km": 18800,
        "landing_points": ["Singapore", "Chennai, India", "Mumbai, India", "Marseille, France"],
        "connected_pops": ["POP-SG-01", "POP-CHE-01", "POP-MUM-01", "POP-MRS-01"],
        "status": "ACTIVE"
    },
    {
        "id": "CABLE-TGN-INTRA-ASIA",
        "name": "TGN Intra-Asia (TGN-IA)",
        "capacity_tbps": 3.84,
        "length_km": 6700,
        "landing_points": ["Singapore", "Hong Kong", "Tokyo, Japan"],
        "connected_pops": ["POP-SG-01", "POP-TYO-01"],
        "status": "ACTIVE"
    },
    {
        "id": "CABLE-EUROPE-RING",
        "name": "Tata Europe High-Capacity Terrestrial Ring",
        "capacity_tbps": 16.0,
        "length_km": 3200,
        "landing_points": ["London, UK", "Frankfurt, Germany", "Marseille, France"],
        "connected_pops": ["POP-LON-01", "POP-FRA-01", "POP-MRS-01"],
        "status": "ACTIVE"
    },
    {
        "id": "CABLE-TGN-WESTERN-EUROPE",
        "name": "TGN-Western Europe",
        "capacity_tbps": 12.0,
        "length_km": 950,
        "landing_points": ["London, UK", "Frankfurt, Germany"],
        "connected_pops": ["POP-LON-01", "POP-FRA-01"],
        "status": "ACTIVE"
    }
]

def get_tata_cables() -> List[Dict[str, Any]]:
    return TATA_SUBSEA_CABLES
