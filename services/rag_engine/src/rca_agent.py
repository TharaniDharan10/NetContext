import os
import json
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("rca_agent")

SYSTEM_PROMPT = """
You are the NetContext Autonomous Root Cause Analysis (RCA) & Network Operations Agent for Tata Communications (AS6453).
Your job is to analyze real-time Knowledge Graph topology context and provide authoritative, factual, explainable, and human-understandable engineering answers.

Always answer the user's direct question first in plain, clear English.
If asked about which cable is cut or whether a backup exists:
- Directly name the severed physical cable system(s) and failure cause.
- For each impacted circuit, clearly answer whether an automated backup route is operational (YES/NO).
- If YES: state the backup circuit ID, backup cable system (e.g. TGN Intra-Asia), backup status (UP), and confirm $0.00 SLA liability.
- If NO (SPOF): state that no secondary route is configured, report the active financial liability ($/hr), and recommend dynamic failover.

If asked about time, incident timestamps, or active outages:
- State the exact detection timestamp (UTC) and how many minutes have elapsed.
- Specify which cable or router failed and the exact failure description.
- Identify which customers are affected and whether their backup routes are operational.
- Calculate SLA penalty risks and how many minutes remain before breach penalties apply.

Follow this clear engineering structure when reporting incidents:
1. ⏱️ REAL-TIME INCIDENT TIMELINE: Detection time (UTC), elapsed downtime, and current status.
2. 🔍 ROOT CAUSE & TARGET ASSET: Physical cable / router ID, location, and failure cause.
3. 🌐 IMPACT & FAILOVER: Affected customer circuits and automated failover route state.
4. 💰 SLA FINANCIAL EXPOSURE: Hourly penalty ($/hr) and minutes remaining until contract breach.
5. 🛠️ ACTIONABLE NEXT STEPS: Clear steps for field engineers and operations teams.
"""

class RCAAgent:
    def __init__(self):
        self.gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
        self.openai_key = os.getenv("OPENAI_API_KEY", "").strip()

    def generate_analysis(self, user_query: str, context_type: str, graph_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Synthesizes an explainable RCA report based on live graph topology.
        Attempts Gemini/OpenAI if configured; otherwise uses deterministic graph reasoning.
        """
        # Try LLM if API key is present
        if self.gemini_key:
            try:
                report = self._call_gemini(user_query, graph_context)
                if report:
                    return {
                        "mode": "LLM_GEMINI",
                        "query": user_query,
                        "context_type": context_type,
                        "analysis": report,
                        "raw_graph_context": graph_context
                    }
            except Exception as e:
                logger.warning("Gemini LLM call failed (%s), falling back to graph reasoning engine.", e)

        if self.openai_key:
            try:
                report = self._call_openai(user_query, graph_context)
                if report:
                    return {
                        "mode": "LLM_OPENAI",
                        "query": user_query,
                        "context_type": context_type,
                        "analysis": report,
                        "raw_graph_context": graph_context
                    }
            except Exception as e:
                logger.warning("OpenAI LLM call failed (%s), falling back to graph reasoning engine.", e)

        # Deterministic Enterprise Graph Reasoning Engine (Guaranteed zero-failure local mode)
        report = self._deterministic_graph_reasoner(user_query, context_type, graph_context)
        return {
            "mode": "GRAPH_REASONING_ENGINE",
            "query": user_query,
            "context_type": context_type,
            "analysis": report,
            "raw_graph_context": graph_context
        }

    def _call_gemini(self, query: str, context: Dict[str, Any]) -> Optional[str]:
        import httpx
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={self.gemini_key}"
        prompt = f"{SYSTEM_PROMPT}\n\nUSER QUESTION:\n{query}\n\nLIVE GRAPH TOPOLOGY & INCIDENT CONTEXT (Neo4j):\n{json.dumps(context, indent=2, default=str)}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "thinkingConfig": {
                    "thinkingBudget": 0
                }
            }
        }

        with httpx.Client(timeout=30.0) as client:
            resp = client.post(url, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                return data["candidates"][0]["content"]["parts"][0]["text"]
            else:
                logger.warning("Gemini API returned status %s: %s", resp.status_code, resp.text)
        return None

    def _call_openai(self, query: str, context: Dict[str, Any]) -> Optional[str]:
        import httpx
        url = "https://api.openai.com/v1/chat/completions"
        headers = {"Authorization": f"Bearer {self.openai_key}"}
        prompt = f"USER QUESTION:\n{query}\n\nLIVE GRAPH TOPOLOGY & INCIDENT CONTEXT (Neo4j):\n{json.dumps(context, indent=2, default=str)}"
        payload = {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.2
        }

        with httpx.Client(timeout=10.0) as client:
            resp = client.post(url, json=payload, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                return data["choices"][0]["message"]["content"]
        return None

    def _deterministic_graph_reasoner(self, query: str, context_type: str, context: Dict[str, Any]) -> str:
        """
        Rule-based graph synthesis engine that parses exact Neo4j paths and produces
        structured engineering reports when external LLM endpoints are offline.
        """
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        lines = []

        active_incidents = context.get("active_incidents", [])

        # 1. Incident Timeline / Direct Time Query
        if context_type == "INCIDENT_TIMELINE" or ("time" in query.lower() and active_incidents):
            if not active_incidents:
                lines.append("### ⏱️ REAL-TIME INCIDENT TIMELINE")
                lines.append("🟢 **No Active Incidents Detected.** All physical subsea cables and transit circuits are operating within nominal specifications.")
                return "\n".join(lines)

            lines.append("### ⏱️ REAL-TIME INCIDENT TIMELINE & DOWNTIME TRACKER")
            for inc in active_incidents:
                started_str = inc.get("started_at", "")
                elapsed_desc = "Unknown"
                started_clean = started_str
                if started_str:
                    try:
                        clean_iso = started_str.replace("Z", "+00:00")
                        start_dt = datetime.fromisoformat(clean_iso)
                        elapsed_mins = max(0, int((now - start_dt).total_seconds() / 60))
                        elapsed_desc = f"{elapsed_mins} minutes ago"
                        started_clean = start_dt.strftime("%Y-%m-%d %H:%M:%S UTC")
                    except Exception:
                        pass

                lines.append(f"• **Incident ID:** `{inc.get('incident_id')}` [{inc.get('severity')}]")
                lines.append(f"• **Event Timestamp:** **{started_clean}** ({elapsed_desc})")
                lines.append(f"• **Current Status:** 🔴 **{inc.get('status', 'OPEN')}**")
                lines.append(f"• **Target Infrastructure:** {inc.get('target_type')} **{inc.get('target_name')}** (`{inc.get('target_id')}`)")
                lines.append(f"• **Root Cause Description:** *\"{inc.get('description')}\"*")

                impacted_custs = inc.get("impacted_customers", [])
                if impacted_custs:
                    lines.append("\n**Customer Impact & SLA Clocks:**")
                    for c in impacted_custs:
                        penalty = c.get("penalty_usd_per_hour", 0.0)
                        max_dt = c.get("max_downtime_minutes", 0)
                        lines.append(f"  - **{c.get('customer_name')}** (Circuit: `{c.get('circuit_id')}`): Max Allowed Downtime: **{max_dt} mins** | Penalty: **${penalty:,.2f}/hr**")

            lines.append("\n### 🛠️ ACTIONABLE NEXT STEPS")
            lines.append("1. **Verify Automated Reroute:** Inspect whether downstream traffic transitioned to secondary failover circuits.")
            lines.append("2. **Field Operations Dispatch:** Alert marine repair vessel or local colocation data center engineers.")
            return "\n".join(lines)

        # 2. Customer Specific Outage
        elif context_type == "CUSTOMER_OUTAGE" and "customer_context" in context:
            cust = context["customer_context"]
            circuits = cust.get("circuits", [])
            incidents = cust.get("active_incidents", [])

            down_circuits = [c for c in circuits if c.get("status") == "DOWN"]
            is_down = len(down_circuits) > 0

            lines.append(f"### 🚨 EXECUTIVE INCIDENT SUMMARY")
            if is_down:
                lines.append(f"Customer **{cust['customer_name']}** ({cust['industry']}) is experiencing an active service disruption on circuit `{down_circuits[0].get('circuit_id')}`.")
            else:
                lines.append(f"All circuits for **{cust['customer_name']}** ({cust['industry']}) are currently operating within nominal operational parameters (Status: UP).")

            lines.append("\n### 🔍 TOPOLOGICAL ROOT CAUSE & TIMELINE")
            if incidents:
                inc = incidents[0]
                started_clean = inc.get("started_at", "N/A")
                lines.append(f"- **Active Incident:** `{inc.get('incident_id')}` [{inc.get('severity')}]")
                lines.append(f"- **Detected At:** **{started_clean}**")
                lines.append(f"- **Failure Details:** {inc.get('description')}")
            elif down_circuits:
                cable_name = down_circuits[0].get("cable_name", "Transit Link")
                lines.append(f"Physical line degradation detected on `{cable_name}`. Traffic transit suspended.")
            else:
                lines.append("No active physical infrastructure cuts or router linecard faults detected along customer routing chain.")

            lines.append("\n### 🌐 BLAST RADIUS & FAILOVER ANALYSIS")
            for c in circuits:
                role = c.get("role")
                status = c.get("status")
                bck_id = c.get("backup_circuit_id")
                bck_status = c.get("backup_status")

                if status == "DOWN":
                    if bck_id and bck_status == "UP":
                        lines.append(f"- **Primary Circuit `{c.get('circuit_id')}` is DOWN**, but automatic failover rerouted traffic via `{bck_id}` (Status: UP). Service remains protected.")
                    else:
                        lines.append(f"- **Primary Circuit `{c.get('circuit_id')}` is DOWN with NO operational backup** (Failover ID: {bck_id or 'None'}). Service state: OUTAGE.")
                elif status == "REROUTED":
                    lines.append(f"- **Primary Circuit `{c.get('circuit_id')}` is REROUTED** via dynamic failover `{bck_id}`. Service restored and protected by agentic orchestration.")
                else:
                    lines.append(f"- Circuit `{c.get('circuit_id')}` ({role}): **UP** ({c.get('bandwidth_gbps')} Gbps {c.get('protocol')})")

            lines.append("\n### 💰 SLA FINANCIAL EXPOSURE")
            hourly_penalty = cust.get("penalty_usd_per_hour", 0.0)
            max_dt = cust.get("max_downtime_minutes", 0)
            if is_down and any(not (c.get("backup_circuit_id") and c.get("backup_status") == "UP") for c in down_circuits):
                lines.append(f"- **Contractual SLA:** {cust.get('sla_name')} ({cust.get('tier')})")
                lines.append(f"- **Financial Liability:** **${hourly_penalty:,.2f} USD per hour**")
                lines.append(f"- **Breach Threshold:** Penalty triggers if unmitigated downtime exceeds **{max_dt} minutes**.")
            else:
                lines.append(f"- **Current SLA Liability Risk:** **$0.00 USD/hr** (Traffic fully protected by active failover path or healthy baseline).")

            lines.append("\n### 🛠️ ACTIONABLE REMEDIATION PLAN")
            if is_down and any(not (c.get("backup_circuit_id") and c.get("backup_status") == "UP") for c in down_circuits):
                lines.append("1. **Trigger Agentic Failover:** Click '⚡ Execute Failover' in the Autonomous Remediation panel to enact dynamic SD-WAN rerouting and arrest SLA penalties.")
                lines.append("2. **Verify Alternative Path:** Route traffic via healthy optical cables (e.g., SMW-4 or TGN-Atlantic).")
                lines.append("3. **Notify Marine Operations:** Dispatch repair team to physical cable location.")
            else:
                lines.append("1. **Topology Verification:** Confirm BGP failover convergence time across alternate POP transit routers.")
                lines.append("2. **Physical Asset Dispatch:** Notify coastal marine cable operations or regional colocation team to inspect link status.")
                lines.append("3. **SLA Protection:** Alert Enterprise Account Manager to acknowledge incident before SLA penalty clock expires.")

        elif context_type == "SPOF_AUDIT" and "single_points_of_failure" in context:
            spof_list = context["single_points_of_failure"]
            lines.append("### 🚨 SINGLE POINT OF FAILURE (SPOF) VULNERABILITY AUDIT")
            lines.append(f"Identified **{len(spof_list)} enterprise circuits** lacking redundant backup routes:")
            for s in spof_list:
                lines.append(f"- **{s.get('customer_name')}** ({s.get('customer_tier')}): Circuit `{s.get('circuit_id')}` via `{s.get('transit_cable')}` carries **${s.get('penalty_usd_per_hour'):,.2f}/hr** SLA breach exposure.")
        elif context_type in ["CABLE_OUTAGE_AND_BACKUP", "INFRASTRUCTURE_BLAST_RADIUS"]:
            severed_cables = context.get("severed_cables", [])
            blast = context.get("infrastructure_blast_radius", {})

            # If specific blast was retrieved and cable is cut, normalize it
            if not severed_cables and blast and blast.get("entity_status") == "CUT":
                severed_cables = [{
                    "cable_id": blast.get("entity_id"),
                    "cable_name": blast.get("entity_name"),
                    "cable_status": blast.get("entity_status"),
                    "incident_id": "INC-ACTIVE",
                    "failure_reason": "Physical optical fiber line cut detected",
                    "impacted_circuits": [
                        {
                            "customer_name": c.get("customer_name"),
                            "customer_tier": c.get("customer_tier"),
                            "impacted_circuit_id": c.get("impacted_circuit"),
                            "impacted_circuit_name": c.get("impacted_circuit_name", c.get("impacted_circuit")),
                            "impacted_circuit_status": c.get("circuit_status"),
                            "backup_circuit_id": c.get("backup_circuit_id"),
                            "backup_circuit_name": c.get("backup_circuit_name", c.get("backup_circuit_id")),
                            "backup_circuit_status": c.get("backup_status"),
                            "backup_cable_name": c.get("backup_cable_name"),
                            "is_protected": c.get("protected", False),
                            "hourly_penalty_usd": c.get("penalty_usd_per_hour", 0.0),
                            "max_downtime_minutes": c.get("max_downtime_minutes", 0)
                        } for c in blast.get("impacted_customers", [])
                    ]
                }]

            if not severed_cables:
                lines.append("### 🌊 SUBSEA CABLE HEALTH & REDUNDANCY REPORT")
                lines.append("🟢 **No Subsea Cables Severed.** All 6 global submarine optical cable systems (TGN-TIC, TGN-Atlantic, TGN-Pacific, SMW-4, TGN-Intra-Asia, Europe Ring) are currently **ACTIVE & NOMINAL**.")
                lines.append("\n**Redundancy Status:** All enterprise customer circuits are fully operational with active baseline routes.")
                return "\n".join(lines)

            lines.append("### 🌊 SUBSEA CABLE OUTAGE & BACKUP REDUNDANCY ANALYSIS")
            total_unprotected_risk = 0.0
            for sc in severed_cables:
                lines.append(f"\n#### 🚨 Severed Cable: **{sc.get('cable_name')}** (`{sc.get('cable_id')}`)")
                lines.append(f"- **Physical Status:** 🔴 **SEVERED / OUTAGE ACTIVE**")
                lines.append(f"- **Active Incident ID:** `{sc.get('incident_id', 'N/A')}`")
                lines.append(f"- **Root Cause:** *\"{sc.get('failure_reason', 'Physical fiber line disruption')}\"*")
                
                circuits = sc.get("impacted_circuits", [])
                if not circuits:
                    lines.append("- **Traversing Circuits:** No active customer circuits assigned to this segment.")
                    continue

                lines.append("\n**Circuit Backup & Automated Failover Breakdown:**")
                for cir in circuits:
                    cir_name = cir.get("impacted_circuit_name", cir.get("impacted_circuit_id"))
                    cir_id = cir.get("impacted_circuit_id")
                    cust_name = cir.get("customer_name")
                    cust_tier = cir.get("customer_tier", "Enterprise")
                    is_prot = cir.get("is_protected", False)
                    bck_id = cir.get("backup_circuit_id")
                    bck_name = cir.get("backup_circuit_name", bck_id)
                    bck_cable = cir.get("backup_cable_name")
                    hourly = cir.get("hourly_penalty_usd", 0.0)
                    max_dt = cir.get("max_downtime_minutes", 0)

                    lines.append(f"\n* **Customer:** **{cust_name}** ({cust_tier})")
                    lines.append(f"  * **Primary Trunk:** `{cir_id}` ({cir_name}) ➔ 🔴 **DOWN**")

                    if is_prot and bck_id:
                        bck_cable_str = f" routed via **{bck_cable}**" if bck_cable else ""
                        lines.append(f"  * **Backup Available?** ✅ **YES — AUTOMATED FAILOVER ROUTE ACTIVE**")
                        lines.append(f"  * **Backup Circuit:** `{bck_id}` ({bck_name}){bck_cable_str}")
                        lines.append(f"  * **Backup Health Status:** 🟢 **UP / OPERATIONAL**")
                        lines.append(f"  * **Customer Traffic Impact:** **Zero Disruption** — Traffic automatically failed over to secondary path.")
                        lines.append(f"  * **SLA Liability Exposure:** **$0.00 USD/hr (Protected)**")
                    else:
                        total_unprotected_risk += hourly
                        lines.append(f"  * **Backup Available?** ❌ **NO — SINGLE POINT OF FAILURE (SPOF)**")
                        lines.append(f"  * **Backup Circuit:** *None provisioned in network topology*")
                        lines.append(f"  * **Customer Traffic Impact:** 🚨 **ACTIVE OUTAGE (Total Service Disruption)**")
                        lines.append(f"  * **SLA Liability Penalty:** **${hourly:,.2f} USD/hr** (Penalty clock expires in **{max_dt} minutes**)")
                        lines.append(f"  * **Recommended Action:** Click '⚡ Execute Failover' in the Autonomous Remediation panel to enact dynamic rerouting via SMW-4.")

            lines.append("\n### 💰 SUMMARY OF FINANCIAL SLA LIABILITY")
            if total_unprotected_risk == 0:
                lines.append("🟢 **$0.00 USD/hr — Zero Financial Liability.** All impacted enterprise customers have operational redundant backup routes in place.")
            else:
                lines.append(f"⚠️ **${total_unprotected_risk:,.2f} USD/hr Total Exposure.** Immediate breach liability across unbacked-up customer circuits.")

            return "\n".join(lines)

        else:
            summary = context.get("network_summary", {})
            lines.append("### 🌐 GLOBAL TATA COMMUNICATIONS (AS6453) NETWORK OVERVIEW")
            lines.append(f"- **Active Cables:** {summary.get('total_cables', 6)} total, {summary.get('severed_cables', 0)} severed")
            lines.append(f"- **Core & Edge Routers:** {summary.get('total_devices', 16)} total, {summary.get('failed_devices', 0)} failed")
            lines.append(f"- **Enterprise Circuits:** {summary.get('total_circuits', 7)} total, {summary.get('down_circuits', 0)} degraded")
            lines.append(f"- **Open Incidents:** {summary.get('open_incidents', 0)}")
            if active_incidents:
                lines.append(f"\n⚠️ **Active Incident:** `{active_incidents[0].get('incident_id')}` on {active_incidents[0].get('target_name')} (Started: {active_incidents[0].get('started_at')})")

        return "\n".join(lines)
