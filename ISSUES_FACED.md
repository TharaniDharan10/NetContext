# 🛠️ Issues Faced & Resolutions Log

> **Project:** NetContext – Autonomous Telecom Context Graph & GraphRAG Platform  
> **Repository:** [TharaniDharan10/NetContext](https://github.com/TharaniDharan10/NetContext)  
> **Live Deployment:** [https://tata-netcontext.streamlit.app/](https://tata-netcontext.streamlit.app/)  
> **Purpose:** Living audit document recording architectural bottlenecks, bugs, root causes, and applied fixes.

---

## 📋 Quick Reference Index

| ID | Category | Issue Summary | Resolution | Status |
| :--- | :--- | :--- | :--- | :--- |
| **ISS-01** | Topological Routing | Geographically invalid failover (e.g. London-Frankfurt rerouted to Singapore) | Neo4j Cypher `shortestPath` with endpoint invariance + added `TGN-Western Europe` | ✅ Resolved |
| **ISS-02** | Frontend / Graph | PyVis canvas hardcoded, missing tenants (Nexus AI & Pacific Star Media) | Created `/api/v1/topology/graph-view` to dynamically stream graph nodes from Neo4j | ✅ Resolved |
| **ISS-03** | PDF Generation | 2-column sign-off block caused layout overflow & truncated legal signatures | Replaced 2-column layout with 540 pt full-width single-column ReportLab table | ✅ Resolved |
| **ISS-04** | Runtime / Python | `TypeError: generate_incident_rca_pdf() got unexpected keyword argument` | Added `**kwargs` catch-all and forced runtime module reload with `importlib.reload` | ✅ Resolved |
| **ISS-05** | DevOps / Docker | Only `neo4j` & `buildx_...` visible in Docker Desktop GUI | Identified Docker Compose project folder grouping and clarified BuildKit worker role | ✅ Resolved |
| **ISS-06** | Cloud Hosting | Netlify cannot host Python Streamlit WebSockets | Deployed to Streamlit Community Cloud with root `requirements.txt` | ✅ Resolved |
| **ISS-07** | Data Schema / Cloud | `KeyError: 'customer_name'` crashed Tab 3 on Streamlit Cloud | Aligned `FALLBACK_SPOF` schema and added defensive column reconciliation with `"N/A"` fallbacks | ✅ Resolved |
| **ISS-08** | Audit Reporting | PDF showed *"No Active Breaches"* even when cutting `SMW-4` or `TGN-Intra-Asia` | Implemented complete 7-cable `CABLE_IMPACT_MAP` covering all optical systems | ✅ Resolved |
| **ISS-09** | Schema Mismatch | PDF table rendered *"Enterprise Customer \| N/A \| $0.00/hr"* placeholders | Added multi-alias key extraction (`customer` vs `customer_name`, `circuit` vs `circuit_id`) | ✅ Resolved |

---

## 🔧 Detailed Issues & Resolutions

### ISS-01: Geographically Invalid Failover Routing (Endpoint Mismatch)
* **Symptom:** When simulating a severed Europe Ring (London ↔ Frankfurt), the failover engine recommended `CABLE-TGN-TIC` (Chennai ↔ Singapore).
* **Root Cause:** A flat heuristic selected the first active cable in the database rather than calculating a valid topological path between the circuit's fixed origin and destination POPs (`POP-LON-01` and `POP-FRA-01`).
* **Fix:**
  1. Implemented true topological shortest-path graph search in Cypher:
     ```cypher
     MATCH (src:POP {id: $src_pop}), (dst:POP {id: $dst_pop})
     MATCH p = shortestPath((src)-[:CONNECTED_VIA_CABLE*..10]-(dst))
     WHERE ALL(r IN relationships(p) WHERE r.status = 'ACTIVE')
     RETURN p, length(p) as hops ORDER BY hops ASC LIMIT 1
     ```
  2. Added real Tata redundant cable `CABLE-TGN-WESTERN-EUROPE` (London ↔ Frankfurt) to provide legitimate physical redundancy.
* **Verification:** Europe Ring cuts now consistently recommend `CABLE-TGN-WESTERN-EUROPE`, preserving endpoint invariance.

---

### ISS-02: Hardcoded PyVis Graph Canvas
* **Symptom:** Newly ingested enterprise customers (*Nexus AI* and *Pacific Star Media*) were visible in backend Neo4j queries but did not appear on the PyVis physics graph.
* **Root Cause:** `services/ui/src/app.py` contained hardcoded customer node lists that fell out of sync with the database.
* **Fix:**
  1. Built `/api/v1/topology/graph-view` endpoint in the Ingestion service returning live POPs, Cables, and Customers directly from Neo4j.
  2. Overhauled PyVis rendering in `app.py` to dynamically iterate over the API response.
* **Verification:** All 6 enterprise tenants, 8 POPs, and 7 cables render dynamically in real time.

---

### ISS-03: PDF Sign-Off Layout Overflow & Truncation
* **Symptom:** Section 4 of the downloaded incident RCA PDF pushed signature lines off-page, causing an unwanted second page with partial text.
* **Root Cause:** ReportLab table used a 2-column layout with mismatched column widths exceeding page boundary limits.
* **Fix:** Redesigned the sign-off block into a unified, full-width single-column table (`colWidths=[540]`) with explicit cell paddings and clean left-to-right hierarchy.
* **Verification:** Generated RCA PDFs fit into a clean, publication-grade document without orphan pages.

---

### ISS-04: Runtime Keyword Argument Error in UI (`generate_incident_rca_pdf`)
* **Symptom:** UI crashed with `TypeError: generate_incident_rca_pdf() got an unexpected keyword argument 'impacted_customers'`.
* **Root Cause:** Python bytecode caching in Streamlit prevented hot-reloaded module updates from taking effect when function signatures were modified.
* **Fix:**
  1. Added `**kwargs` catch-all to `generate_incident_rca_pdf()` in `rca_pdf_generator.py`.
  2. Added `importlib.reload(rca_pdf_generator)` at the top of `app.py` to ensure fresh imports.
* **Verification:** UI renders and hot-reloads cleanly across all incident states.

---

### ISS-05: Docker Desktop Container Grouping Confusion
* **Symptom:** Docker Desktop showed only two items: `neo4j` and `buildx_buildkit_xenodochial_noether0`, leading to concern that UI and API services were not running.
* **Root Cause:**
  1. Docker Desktop automatically groups Compose services into collapsible folders named after the parent directory (`neo4j`). When collapsed, only the folder title is displayed.
  2. `buildx_...` is Docker's internal BuildKit compilation worker, displayed separately as a standalone utility.
* **Fix:** Expanded the `neo4j` group to confirm all 4 microservices (`netcontext-ui`, `netcontext-ingestion`, `netcontext-rag-engine`, `netcontext-neo4j`) were healthy on their respective ports (`:8501`, `:8001`, `:8002`, `:7474`). Documented this behavior in `README.md`.
* **Verification:** Verified all containers active via `docker compose ps` and confirmed HTTP 200 on all endpoints.

---

### ISS-06: Deployment Platform Incompatibility (Netlify vs Streamlit)
* **Symptom:** User requested deploying the UI to Netlify for free.
* **Root Cause:** Netlify is a static CDN host that does not support persistent long-running Python daemons or continuous WebSockets (`ws://.../_stcore/stream`) required by Streamlit.
* **Fix:**
  1. Deployed to **Streamlit Community Cloud** ([https://tata-netcontext.streamlit.app/](https://tata-netcontext.streamlit.app/)) which natively hosts Python WebSockets for free.
  2. Added root-level `requirements.txt` to enable automatic dependency installation during cloud build.
* **Verification:** Application successfully built and launched live on `tata-netcontext.streamlit.app`.

---

### ISS-07: Streamlit Cloud `KeyError: 'customer_name'` in Tab 3
* **Symptom:** Cloud deployment crashed with `KeyError: "None of ['customer_name', ...] are in the columns"` upon opening.
* **Root Cause:** When running on Streamlit Cloud without the local Docker backend, `get_spof()` fell back to `FALLBACK_SPOF`. The fallback dictionary used shorthand keys (`customer`, `circuit`, `cable`) while Tab 3 expected exact backend keys (`customer_name`, `customer_tier`, `circuit_name`, etc.).
* **Fix:**
  1. Updated `FALLBACK_SPOF` schema to strictly match the backend RAG schema.
  2. Added defensive column reconciliation in Tab 3:
     ```python
     for c, _ in col_mappings:
         if c not in df_spof.columns:
             df_spof[c] = "N/A"
     ```
* **Verification:** Tab 3 renders gracefully on both cloud and local environments without errors.

---

### ISS-08: Inconsistent *"No Active Customer Outage Breaches"* in PDF
* **Symptom:** Cutting `SMW-4` or `TGN-Intra-Asia` generated a PDF stating `CRITICAL [OUTAGE ACTIVE]` in the header, but Section 2 claimed: *"No Active Customer Outage Breaches: All circuits operating nominally"*.
* **Root Cause:** The cloud fallback helper only mapped `Europe Ring` and `TGN-TIC`. When any other cable was cut, `get_impacted_customers()` returned an empty list `[]`, causing the PDF generator to execute its nominal `else:` block.
* **Fix:** Built `CABLE_IMPACT_MAP` in `app.py` mapping all 7 optical cable systems to their real enterprise tenants, circuits, SLAs, downtime limits, and redundancy statuses.
* **Verification:** Cutting `TGN-Intra-Asia` or `SMW-4` now correctly displays affected customers (*Pacific Star Media* / *TransGlobal*) with exact mitigation statuses.

---

### ISS-09: Generic Placeholder Data in PDF Customer Impact Table
* **Symptom:** Downloaded PDF rendered customer rows as:  
  `Enterprise Customer | Enterprise | N/A | 0 mins | $0.00/hr | Failover Recommended`.
* **Root Cause:** `app.py` emitted customer dictionaries with short keys (`customer`, `tier`, `circuit`, `sla_penalty`), while `rca_pdf_generator.py` looked up long-form keys (`customer_name`, `customer_tier`, `circuit_id`, `hourly_liability_usd`). Unmatched lookups reverted to placeholder defaults.
* **Fix:** Implemented multi-alias key extraction in `rca_pdf_generator.py`:
  ```python
  c_name = rec.get("customer_name") or rec.get("customer") or "Enterprise Customer"
  c_tier = rec.get("customer_tier") or rec.get("tier") or "Enterprise"
  cir_id = rec.get("circuit_id") or rec.get("circuit") or "N/A"
  penalty_val = rec.get('hourly_liability_usd') or rec.get('sla_penalty') or 0.0
  ```
* **Verification:** PDFs accurately print actual enterprise names, circuit IDs, SLA penalties, and mitigation statuses.

---

## 📝 Maintenance Protocol for Future Issues

When resolving new issues or extending platform capabilities:
1. **Assign Sequential ID:** Use `ISS-XX` format.
2. **Document the 4 Core Pillars:** Symptom, Root Cause, Applied Fix, and Verification.
3. **Keep Concise:** Avoid narrative filler; focus on technical specifics and reproducible verification.
