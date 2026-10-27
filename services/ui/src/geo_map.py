import json
from typing import List, Dict, Any

# Real-world geographic coordinates for Tata Communications global landing stations
GEO_POPS = {
    "POP-SG-01": {"name": "Singapore Tai Seng CLS", "lat": 1.3361, "lon": 103.8864, "facility": "Tata Tai Seng / Equinix SG1", "region": "APAC"},
    "POP-MUM-01": {"name": "Mumbai BKC Core Gateway", "lat": 19.0660, "lon": 72.8687, "facility": "Tata BKC Gateway", "region": "APAC"},
    "POP-CHE-01": {"name": "Chennai Santhome CLS", "lat": 13.0333, "lon": 80.2785, "facility": "Tata Santhome Cable Landing", "region": "APAC"},
    "POP-LON-01": {"name": "London Telehouse Docklands", "lat": 51.5126, "lon": -0.0076, "facility": "Telehouse North Two / LINX", "region": "EMEA"},
    "POP-FRA-01": {"name": "Frankfurt Equinix Exchange", "lat": 50.1109, "lon": 8.6821, "facility": "Equinix FR5 / DE-CIX", "region": "EMEA"},
    "POP-MRS-01": {"name": "Marseille Interxion Gateway", "lat": 43.2965, "lon": 5.3698, "facility": "Interxion MRS1 / France-IX", "region": "EMEA"},
    "POP-NYC-01": {"name": "New York 60 Hudson Gateway", "lat": 40.7180, "lon": -74.0080, "facility": "60 Hudson Street / NYIIX", "region": "AMER"},
    "POP-TYO-01": {"name": "Tokyo Shiyoda Gateway", "lat": 35.6762, "lon": 139.6503, "facility": "Equinix TY2 / JPNAP", "region": "APAC"},
    "POP-LA-01": {"name": "Los Angeles Pacific Gateway", "lat": 34.05, "lon": -118.25, "facility": "Equinix LA1 CLS", "region": "AMER"}
}

# Accurate Oceanic Cable Trajectories
GEO_CABLES = [
    {
        "id": "CABLE-TGN-TIC",
        "name": "Tata Indicom Cable (TGN-TIC)",
        "capacity": "5.12 Tbps",
        "path": [
            [13.0333, 80.2785],  # Chennai Santhome
            [11.5, 83.5],
            [9.0, 87.0],
            [6.2, 93.0],
            [5.5, 95.5],         # Entrance to Malacca Strait
            [4.0, 98.5],
            [2.8, 101.2],
            [1.3361, 103.8864]   # Singapore Tai Seng
        ],
        "endpoints": ["Chennai, India", "Singapore"]
    },
    {
        "id": "CABLE-TGN-ATLANTIC",
        "name": "TGN-Atlantic",
        "capacity": "10.2 Tbps",
        "path": [
            [40.7180, -74.0080], # New York 60 Hudson
            [40.5, -71.5],
            [41.5, -60.0],
            [45.0, -45.0],
            [48.0, -30.0],
            [50.0, -18.0],
            [49.8, -6.5],        # Celtic Sea
            [50.5, -1.5],        # English Channel approach
            [51.5126, -0.0076]   # London Telehouse
        ],
        "endpoints": ["New York, US", "London, UK"]
    },
    {
        "id": "CABLE-TGN-PACIFIC",
        "name": "TGN-Pacific",
        "capacity": "9.6 Tbps",
        # Rendered with dual seamless continuous trajectories so the cable connects
        # Tokyo and New York without hanging stubs across both Eastern and Western projections.
        "path": [
            # Segment A: Continuous eastbound from Tokyo across Pacific into LA & NYC
            [
                [35.6762, 139.6503],  # Tokyo Shiyoda
                [37.5, 155.0],
                [41.0, 170.0],
                [43.0, 180.0],
                [42.5, 195.0],        # Longitude 195° (-165°)
                [39.5, 215.0],        # Longitude 215° (-145°)
                [36.0, 232.0],        # Longitude 232° (-128°)
                [34.05, 241.75],      # Los Angeles CLS (241.75°)
                [35.5, 260.0],        # US Terrestrial Core Trunk
                [39.0, 276.0],
                [40.7180, 285.9920]   # New York 60 Hudson (285.99°)
            ],
            # Segment B: Continuous westbound from NYC/LA across Pacific into Tokyo
            [
                [40.7180, -74.0080],  # New York 60 Hudson
                [39.0, -84.0],
                [35.5, -100.0],
                [34.05, -118.25],     # Los Angeles CLS
                [36.0, -128.0],
                [39.5, -145.0],
                [42.5, -165.0],
                [43.0, -180.0],
                [41.0, -190.0],       # Longitude -190° (+170°)
                [37.5, -205.0],       # Longitude -205° (+155°)
                [35.6762, -220.3497]  # Tokyo Shiyoda (-220.35°)
            ]
        ],
        "endpoints": ["Tokyo, Japan", "Los Angeles, US", "New York, US"]
    },
    {
        "id": "CABLE-SMW4",
        "name": "South East Asia - Middle East - Western Europe 4 (SMW-4)",
        "capacity": "4.8 Tbps",
        "path": [
            [1.3361, 103.8864],  # Singapore
            [2.8, 101.2],
            [4.5, 98.5],
            [5.8, 95.5],
            [8.5, 90.0],
            [13.0333, 80.2785],  # Chennai
            [9.0, 81.8],         # Around Sri Lanka
            [5.8, 80.5],
            [7.0, 76.8],
            [14.0, 72.5],
            [19.0660, 72.8687],  # Mumbai BKC
            [17.5, 66.0],        # Arabian Sea
            [14.5, 56.0],
            [12.5, 45.0],        # Gulf of Aden
            [12.8, 43.3],        # Bab-el-Mandeb
            [18.0, 40.0],        # Red Sea
            [23.5, 37.0],
            [27.5, 34.5],
            [29.9, 32.5],        # Suez Canal
            [32.5, 31.0],        # Mediterranean Entrance
            [34.0, 24.0],
            [36.5, 15.0],
            [39.0, 8.0],
            [43.2965, 5.3698]    # Marseille Interxion
        ],
        "endpoints": ["Singapore", "Chennai", "Mumbai", "Marseille"]
    },
    {
        "id": "CABLE-TGN-INTRA-ASIA",
        "name": "TGN Intra-Asia (TGN-IA)",
        "capacity": "3.84 Tbps",
        "path": [
            [1.3361, 103.8864],  # Singapore
            [4.0, 105.5],        # South China Sea
            [10.0, 111.5],
            [16.0, 116.5],
            [20.5, 120.5],       # Luzon Strait
            [24.5, 124.0],       # East of Taiwan
            [28.0, 128.5],
            [32.0, 134.0],
            [35.6762, 139.6503]  # Tokyo
        ],
        "endpoints": ["Singapore", "Tokyo, Japan"]
    },
    {
        "id": "CABLE-EUROPE-RING",
        "name": "Tata Europe High-Capacity Terrestrial Ring",
        "capacity": "16.0 Tbps",
        "path": [
            [51.5126, -0.0076],  # London Telehouse
            [51.12, 1.31],       # Dover Strait
            [50.85, 4.35],       # Brussels
            [50.1109, 8.6821],   # Frankfurt Equinix
            [48.58, 7.75],       # Strasbourg / Rhine Corridor
            [47.56, 7.59],       # Basel
            [45.76, 4.84],       # Lyon
            [43.2965, 5.3698]    # Marseille Interxion
        ],
        "endpoints": ["London", "Frankfurt", "Marseille"]
    },
    {
        "id": "CABLE-TGN-WESTERN-EUROPE",
        "name": "TGN-Western Europe (London ↔ Frankfurt)",
        "capacity": "12.0 Tbps",
        "path": [
            [51.5126, -0.0076],  # London Telehouse
            [51.35, 1.45],       # North Sea Crossing
            [51.22, 4.40],       # Antwerp / Netherlands
            [50.93, 6.96],       # Cologne
            [50.1109, 8.6821]    # Frankfurt Equinix
        ],
        "endpoints": ["London, UK", "Frankfurt, Germany"]
    }
]

def generate_geospatial_map_html(active_incidents: List[Dict[str, Any]], theme: str = "dark") -> str:
    """
    Renders an enterprise-grade Leaflet map with zero API keys required.
    Supports both Cyber NOC Dark and Executive Light themes.
    Includes seamless Trans-Pacific multi-projection continuity and interactive NOC view controls.
    """
    is_dark = theme != "light"
    severed_cable_ids = [inc.get("target_id") for inc in active_incidents if inc.get("target_type") == "Cable"]
    is_outage = len(severed_cable_ids) > 0
    status_text = f"🔴 {len(severed_cable_ids)} CABLE OUTAGE ACTIVE" if is_outage else "🟢 ALL SUBSEA SYSTEMS NOMINAL"
    status_bg = "rgba(239, 68, 68, 0.2)" if is_outage else ("rgba(16, 185, 129, 0.2)" if is_dark else "rgba(16, 185, 129, 0.15)")
    status_border = "#EF4444" if is_outage else ("#10B981" if is_dark else "#059669")
    status_color = "#F87171" if is_outage else ("#34D399" if is_dark else "#047857")

    # Theme-adaptive palette
    body_bg = "#0A0F1D" if is_dark else "#F8FAFC"
    map_border = "#1E293B" if is_dark else "#CBD5E1"
    
    hud_bg = "rgba(10, 15, 29, 0.94)" if is_dark else "rgba(255, 255, 255, 0.94)"
    hud_border = "rgba(56, 189, 248, 0.3)" if is_dark else "rgba(148, 163, 184, 0.5)"
    hud_shadow = "0 4px 18px rgba(0, 0, 0, 0.6)" if is_dark else "0 4px 16px rgba(0, 0, 0, 0.08)"
    hud_title_color = "#38BDF8" if is_dark else "#0369A1"
    
    controls_bg = "rgba(10, 15, 29, 0.94)" if is_dark else "rgba(255, 255, 255, 0.96)"
    controls_border = "rgba(56, 189, 248, 0.3)" if is_dark else "rgba(148, 163, 184, 0.5)"
    controls_shadow = "0 8px 24px rgba(0, 0, 0, 0.5)" if is_dark else "0 6px 20px rgba(0, 0, 0, 0.12)"
    btn_color = "#94A3B8" if is_dark else "#475569"
    btn_hover_bg = "rgba(30, 41, 59, 0.8)" if is_dark else "rgba(241, 245, 249, 0.9)"
    btn_hover_color = "#38BDF8" if is_dark else "#0284C7"
    
    legend_bg = "rgba(10, 15, 29, 0.92)" if is_dark else "rgba(255, 255, 255, 0.94)"
    legend_border = "#334155" if is_dark else "#CBD5E1"
    legend_text = "#E2E8F0" if is_dark else "#1E293B"
    legend_title = "#38BDF8" if is_dark else "#0284C7"
    legend_shadow = "0 4px 14px rgba(0, 0, 0, 0.6)" if is_dark else "0 4px 14px rgba(0, 0, 0, 0.08)"
    
    popup_bg = "#0F172A" if is_dark else "#FFFFFF"
    popup_text = "#F8FAFC" if is_dark else "#0F172A"
    popup_border = "#38BDF8" if is_dark else "#0284C7"
    
    layer_menu_bg = "rgba(10, 15, 29, 0.94)" if is_dark else "rgba(255, 255, 255, 0.94)"
    layer_menu_border = "rgba(56, 189, 248, 0.3)" if is_dark else "rgba(148, 163, 184, 0.5)"
    layer_menu_text = "#CBD5E1" if is_dark else "#334155"

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
        <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
        <style>
            * {{ box-sizing: border-box; }}
            body {{ margin: 0; padding: 0; background: {body_bg}; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }}
            #map {{ height: 580px; width: 100%; border-radius: 8px; border: 1px solid {map_border}; }}
            
            /* Custom HUD Header (Top-Left) - Compact & High-Impact */
            .noc-hud-header {{
                position: absolute;
                top: 14px;
                left: 55px;
                background: {hud_bg};
                backdrop-filter: blur(12px);
                -webkit-backdrop-filter: blur(12px);
                border: 1px solid {hud_border};
                padding: 6px 12px;
                border-radius: 8px;
                z-index: 1000;
                display: flex;
                align-items: center;
                gap: 10px;
                box-shadow: {hud_shadow};
            }}
            .noc-hud-title {{
                color: {hud_title_color};
                font-size: 11px;
                font-weight: 800;
                letter-spacing: 0.6px;
                text-transform: uppercase;
                display: flex;
                align-items: center;
                gap: 6px;
            }}
            .noc-hud-status {{
                background: {status_bg};
                border: 1px solid {status_border};
                color: {status_color};
                font-size: 11px;
                font-weight: 700;
                letter-spacing: 0.3px;
                padding: 3px 8px;
                border-radius: 5px;
                box-shadow: 0 0 8px {status_border}33;
            }}

            /* Quick View Controls (Floating Bottom-Center Dock - ZERO Overlap with Top Header or Top-Right Menu!) */
            .noc-view-controls {{
                position: absolute;
                bottom: 22px;
                left: 50%;
                transform: translateX(-50%);
                background: {controls_bg};
                backdrop-filter: blur(14px);
                -webkit-backdrop-filter: blur(14px);
                border: 1px solid {controls_border};
                border-radius: 30px;
                padding: 5px 8px;
                z-index: 1000;
                display: flex;
                align-items: center;
                gap: 5px;
                box-shadow: {controls_shadow};
                white-space: nowrap;
            }}
            .view-btn {{
                background: transparent;
                border: 1px solid transparent;
                color: {btn_color};
                padding: 6px 14px;
                font-size: 11px;
                font-weight: 700;
                letter-spacing: 0.3px;
                border-radius: 20px;
                cursor: pointer;
                transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
                display: inline-flex;
                align-items: center;
                gap: 5px;
            }}
            .view-btn:hover {{
                color: {btn_hover_color};
                background: {btn_hover_bg};
                border-color: {controls_border};
            }}
            .view-btn.active {{
                background: linear-gradient(135deg, #0284C7 0%, #0369A1 100%);
                color: #FFFFFF !important;
                border-color: #38BDF8;
                box-shadow: 0 2px 10px rgba(2, 132, 199, 0.4);
            }}

            /* Legend Box (Bottom-Right) */
            .legend-box {{
                position: absolute;
                bottom: 22px;
                right: 16px;
                background: {legend_bg};
                backdrop-filter: blur(10px);
                border: 1px solid {legend_border};
                color: {legend_text};
                padding: 10px 14px;
                border-radius: 8px;
                font-size: 11px;
                z-index: 1000;
                box-shadow: {legend_shadow};
            }}
            .legend-item {{ display: flex; align-items: center; margin-bottom: 5px; }}
            .legend-item:last-child {{ margin-bottom: 0px; }}
            .legend-color {{ width: 14px; height: 14px; border-radius: 3px; margin-right: 8px; }}

            /* Pulsing Outage Animation */
            @keyframes pulse-red {{
                0% {{ opacity: 1; stroke-width: 4.8; }}
                50% {{ opacity: 0.35; stroke-width: 7.2; }}
                100% {{ opacity: 1; stroke-width: 4.8; }}
            }}
            .pulsing-severed {{
                stroke: #EF4444 !important;
                stroke-dasharray: 8, 8;
                animation: pulse-red 1.2s infinite;
            }}

            /* Popups */
            .leaflet-popup-content-wrapper {{
                background: {popup_bg} !important;
                color: {popup_text} !important;
                border-radius: 8px !important;
                border: 1px solid {popup_border} !important;
                box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.5) !important;
            }}
            .leaflet-popup-tip {{ background: {popup_bg} !important; border-top: 1px solid {popup_border}; }}

            /* Layer control (Top-Right Map Menu) */
            .leaflet-control-layers {{
                background: {layer_menu_bg} !important;
                backdrop-filter: blur(12px) !important;
                -webkit-backdrop-filter: blur(12px) !important;
                color: {layer_menu_text} !important;
                border: 1px solid {layer_menu_border} !important;
                border-radius: 8px !important;
                padding: 8px 12px !important;
                font-family: inherit !important;
                font-size: 11px !important;
                font-weight: 600 !important;
                box-shadow: {hud_shadow} !important;
                margin-top: 14px !important;
                margin-right: 14px !important;
            }}
            .leaflet-control-layers-toggle {{
                background-color: {layer_menu_bg} !important;
                border-radius: 6px !important;
                border: 1px solid {layer_menu_border} !important;
            }}
            .leaflet-control-layers-base label {{
                color: {layer_menu_text} !important;
                cursor: pointer;
                display: flex;
                align-items: center;
                gap: 6px;
                padding: 2px 0;
            }}
            .leaflet-control-layers-base label:hover {{
                color: #38BDF8 !important;
            }}

            /* Zoom Control Styling (Top-Left) */
            .leaflet-control-zoom {{
                border: 1px solid {hud_border} !important;
                border-radius: 8px !important;
                overflow: hidden !important;
                box-shadow: {hud_shadow} !important;
                margin-top: 14px !important;
                margin-left: 14px !important;
            }}
            .leaflet-control-zoom a {{
                background-color: {layer_menu_bg} !important;
                color: {btn_color} !important;
                border-bottom: 1px solid {map_border} !important;
                transition: all 0.2s ease !important;
            }}
            .leaflet-control-zoom a:hover {{
                background-color: {btn_hover_bg} !important;
                color: {btn_hover_color} !important;
            }}
        </style>
    </head>
    <body>
        <div id="map"></div>
        <div class="noc-hud-header">
            <span class="noc-hud-title">🌐 TATA COMMUNICATIONS AS6453 &bull; GLOBAL SUBSEA MESH</span>
            <span class="noc-hud-status">{status_text}</span>
        </div>

        <div class="noc-view-controls">
            <button class="view-btn active" id="btn-global" onclick="setNocView('global')">🌍 Global NOC</button>
            <button class="view-btn" id="btn-pacific" onclick="setNocView('pacific')">🌊 Trans-Pacific Focus</button>
            <button class="view-btn" id="btn-atlantic" onclick="setNocView('atlantic')">⚓ Atlantic</button>
            <button class="view-btn" id="btn-asia" onclick="setNocView('asia')">🌏 Asia-MidEast</button>
        </div>

        <div class="legend-box">
            <div style="font-weight: 700; margin-bottom: 8px; color: {legend_title}; font-size: 13px;">AS6453 Optical Inventory</div>
            <div class="legend-item"><span class="legend-color" style="background: #06B6D4;"></span>Active Subsea Cable (Nominal)</div>
            <div class="legend-item"><span class="legend-color" style="background: #EF4444;"></span>Severed Cable System (Outage)</div>
            <div class="legend-item"><span class="legend-color" style="background: #3B82F6; border-radius: 50%; border: 2px solid #FFFFFF;"></span>Cable Landing Station (CLS)</div>
        </div>

        <script>
            // 1. Basemaps (100% Free ESRI Layers, Zero API Key)
            var esriDarkBase = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{{z}}/{{y}}/{{x}}', {{
                maxZoom: 16,
                attribution: '&copy; ESRI &copy; OpenStreetMap'
            }});
            var esriDarkRef = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Reference/MapServer/tile/{{z}}/{{y}}/{{x}}', {{
                maxZoom: 16
            }});
            var darkNocGroup = L.layerGroup([esriDarkBase, esriDarkRef]);

            var esriLightBase = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_Base/MapServer/tile/{{z}}/{{y}}/{{x}}', {{
                maxZoom: 16,
                attribution: '&copy; ESRI &copy; OpenStreetMap'
            }});
            var esriLightRef = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_Reference/MapServer/tile/{{z}}/{{y}}/{{x}}', {{
                maxZoom: 16
            }});
            var lightNocGroup = L.layerGroup([esriLightBase, esriLightRef]);

            var esriSatellite = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{{z}}/{{y}}/{{x}}', {{
                maxZoom: 18,
                attribution: '&copy; ESRI Earthstar Geographics'
            }});
            var esriOcean = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Ocean/World_Ocean_Base/MapServer/tile/{{z}}/{{y}}/{{x}}', {{
                maxZoom: 13,
                attribution: '&copy; ESRI Ocean Basemap'
            }});

            var defaultBasemap = {'darkNocGroup' if is_dark else 'lightNocGroup'};

            // 2. Initialize Leaflet Map
            var map = L.map('map', {{
                center: [22.0, 35.0],
                zoom: 2.2,
                minZoom: 2,
                maxZoom: 10,
                worldCopyJump: false,
                layers: [defaultBasemap]
            }});

            // 3. Basemap control
            var baseMaps = {{
                "🌌 Dark NOC Canvas": darkNocGroup,
                "☀️ Light Executive Canvas": lightNocGroup,
                "🛰️ Satellite Imagery": esriSatellite,
                "🌊 Ocean Bathymetry": esriOcean
            }};
            L.control.layers(baseMaps, null, {{ position: 'topright' }}).addTo(map);

            // 4. Quick View Switcher
            window.setNocView = function(mode) {{
                document.querySelectorAll('.view-btn').forEach(function(b) {{ b.classList.remove('active'); }});
                var btn = document.getElementById('btn-' + mode);
                if (btn) btn.classList.add('active');

                if (mode === 'global') {{
                    map.flyTo([22.0, 35.0], 2.2, {{ duration: 1.2 }});
                }} else if (mode === 'pacific') {{
                    map.flyTo([30.0, -165.0], 2.4, {{ duration: 1.5 }});
                }} else if (mode === 'atlantic') {{
                    map.flyTo([43.0, -42.0], 3.0, {{ duration: 1.2 }});
                }} else if (mode === 'asia') {{
                    map.flyTo([16.0, 82.0], 3.2, {{ duration: 1.2 }});
                }}
            }};

            var pops = {json.dumps(GEO_POPS)};
            var cables = {json.dumps(GEO_CABLES)};
            var severedCables = {json.dumps(severed_cable_ids)};

            // 5. Draw Subsea Cables
            cables.forEach(function(cable) {{
                var isCut = severedCables.includes(cable.id);
                var cableColor = isCut ? '#EF4444' : '#06B6D4';
                var cableWeight = isCut ? 4.8 : 3.0;
                var dashArray = isCut ? '8, 8' : null;
                var className = isCut ? 'pulsing-severed' : '';

                var polyline = L.polyline(cable.path, {{
                    color: cableColor,
                    weight: cableWeight,
                    opacity: 0.92,
                    dashArray: dashArray,
                    className: className,
                    lineCap: 'round',
                    lineJoin: 'round'
                }}).addTo(map);

                var statusBadge = isCut 
                    ? '<span style="color: #EF4444; font-weight: bold; background: rgba(239, 68, 68, 0.15); padding: 2px 6px; border-radius: 4px;">🚨 SEVERED / OUTAGE ACTIVE</span>' 
                    : '<span style="color: #10B981; font-weight: bold; background: rgba(16, 185, 129, 0.15); padding: 2px 6px; border-radius: 4px;">🟢 ACTIVE & NOMINAL</span>';

                polyline.bindPopup(
                    '<div style="font-family: sans-serif; font-size: 13px; line-height: 1.6;">' +
                    '<b style="font-size: 15px; color: #38BDF8;">' + cable.name + '</b><br/>' +
                    '<b>System ID:</b> <code style="color: #93C5FD;">' + cable.id + '</code><br/>' +
                    '<b>Status:</b> ' + statusBadge + '<br/>' +
                    '<b>Capacity:</b> <span style="color: #FBBF24; font-weight: 600;">' + cable.capacity + '</span><br/>' +
                    '<b>Landing Endpoints:</b> ' + cable.endpoints.join(' ↔ ') +
                    '</div>'
                );
            }});

            // 6. Draw Landing Stations (POPs) with seamless world-wrap beacons
            function addClsBeacon(lat, lon, key, pop) {{
                // Outer glowing halo
                L.circleMarker([lat, lon], {{
                    radius: 12,
                    fillColor: '#38BDF8',
                    color: '#38BDF8',
                    weight: 1,
                    opacity: 0.4,
                    fillOpacity: 0.15
                }}).addTo(map);

                // Core beacon
                var marker = L.circleMarker([lat, lon], {{
                    radius: 6,
                    fillColor: '#0284C7',
                    color: '#FFFFFF',
                    weight: 2,
                    opacity: 1,
                    fillOpacity: 0.95
                }}).addTo(map);

                marker.bindPopup(
                    '<div style="font-family: sans-serif; font-size: 13px; line-height: 1.6;">' +
                    '<b style="font-size: 15px; color: #38BDF8;">📍 ' + pop.name + '</b><br/>' +
                    '<b>POP Code:</b> <code style="color: #93C5FD;">' + key + '</code><br/>' +
                    '<b>Facility:</b> ' + pop.facility + '<br/>' +
                    '<b>Region:</b> ' + pop.region + '<br/>' +
                    '<b>Coordinates:</b> ' + pop.lat.toFixed(4) + '&deg; N, ' + pop.lon.toFixed(4) + '&deg; E' +
                    '</div>'
                );
            }}

            for (var key in pops) {{
                var pop = pops[key];
                addClsBeacon(pop.lat, pop.lon, key, pop);

                // For trans-Pacific endpoints (Tokyo, New York, Los Angeles), also plot wrapped beacons
                if (key === 'POP-TYO-01') {{
                    addClsBeacon(pop.lat, pop.lon - 360, key + " (Pacific West Projection)", pop);
                }} else if (key === 'POP-NYC-01') {{
                    addClsBeacon(pop.lat, pop.lon + 360, key + " (Pacific East Projection)", pop);
                }} else if (key === 'POP-LA-01') {{
                    addClsBeacon(pop.lat, pop.lon + 360, key + " (Pacific East Projection)", pop);
                }}
            }}
        </script>
    </body>
    </html>
    """
    return html
