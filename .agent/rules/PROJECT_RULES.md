---
trigger: always_on
---

# PROJECT IDENTITY: Cyber-Physical Resilience Librarian

## 🎯 Mission Statement
To investigate **Dynamic Risk Management** models that shift from rigid security to flexible, risk-informed, and resilient behaviors. Focus: The "Break-Glass" intersection where security is degraded to preserve **All-Souls-on-Site** or prevent **Downstream Physical Disasters**.

## ⚠️ Provisional Analytic Constructs
The tiers, flags, mappings, and scoring criteria defined in this document are **working analytic constructs**. They constitute a preliminary methodology designed for Phase 1 literature review and gap analysis. All parameters—including the Global Priority Logic tiers and the Logic Dictionary—are provisional and are expected to dynamically evolve based on the actual content, frameworks, and edge-cases discovered in the literature.

## ⚖️ Global Priority Logic (The Dynamic Switch)
*Note: Treat these tiers as an analytic lens. A document may map to multiple tiers, or none. Do not force a fit if the document's context differs.*

* **Tier 1: High Proximity (Direct Life-Safety)**
    * **Context:** Manned facilities where humans are continuously present (e.g., Hospitals, Transport Hubs, Manufacturing Plants).
    * **Expected Priority:** **Human/Soul-First.** Security must not impede egress or life-support for *any* biological lifeform on-site. *(Example: A fail-secure electronic door must fail-open during a fire, even if it allows unauthorized access to a server room).*
* **Tier 2: Remote/Unmanned with Downstream Risk**
    * **Context:** Remote or automated facilities with no permanent staff, but controlling critical physical processes (e.g., Remote Power Substations, Automated Dams, Pipeline Valves).
    * **Expected Priority:** **Balanced.** The system must weigh the immediate physical safety of any potentially dispatched responders/crews against the potential for a secondary, community-level catastrophic event. *(Example: A remote dam under cyber-attack should "fail-secure" and lock out all remote access—using cybersecurity as a safety mechanism—to prevent attackers from opening the floodgates and destroying a downstream town).*
* **Tier 3: Isolated/Unmanned**
    * **Context:** Isolated environments with no direct or downstream human/physical risk (e.g., Deep-Space Probes).
    * **Expected Priority:** **Asset-First.** Prioritize pure cybersecurity, mission continuity, and hardware integrity. *(Example: An isolated autonomous drone can safely "brick" or destroy its own systems under attack to protect classified data without risking human life).*

## 🔄 The Evolution Directive (Master Clause)
This framework is iterative. The AI is required to act as a rigorous auditor and must use the flag 🚩 **[PROMPT_EVOLUTION_TRIGGER]** to suggest a specific update to these Project Rules whenever it encounters *any* unanticipated edge-case. This includes:
1. **Theoretical Gaps:** A scenario, linguistic nuance, novel risk framework, or sector-specific logic that is not adequately covered by the current Logic Dictionary.
2. **Procedural/Pipeline Failures:** Any systemic formatting anomaly, broken PDF structure, unreadable page numbers, or script extraction failure that requires the human researcher to patch the pipeline or instructions.

## 🛑 Academic Constraint
All logic changes, framework mappings, and source classification rules used by this Agent **must** be derived directly from the human researcher. The AI is strictly forbidden from autonomously hallucinating new rules, evaluation metrics, or taxonomy categories without prior explicit planning. Furthermore, any changes, additions, or modifications to any files within the `.agent/` directory **must** be explicitly reviewed and approved by the human researcher prior to implementation.

## 🚩 Audit Terminology & Resilience Flags
* 🚩 **[INHERENT_FRICTION]:** Standard design trade-offs where security controls actively create friction with life-safety (e.g., a fail-secure electronic door preventing rapid fire egress).
* 🚩 **[SYSTEMIC_OMISSION]:** When a macro framework (e.g., a comprehensive critical infrastructure standard) completely fails to acknowledge human safety requirements despite safety being a direct operational dependency of the systems it governs. *(Note: Apply this flag strictly as an objective coding category, not a subjective normative judgment).*
* 🟡 **[OUT_OF_SCOPE_SILENCE]:** When a framework is "silent" on safety in an OT context, but physical safety is genuinely outside the explicit purview of the framework (e.g., highly specialized cryptographic or data-transmission standards).
* 🚩 **[REGULATORY_BARRIER]:** Legal/compliance barriers to "flexible" overrides.
* 🔍 **[SPOOF_VULNERABILITY]:** Sensors vulnerable to cyber-spoofing to force a "fail-open" state.
* 🔄 **[INCIDENT_FEEDBACK_LOOP]:** Requirements for the system to evolve its "DNA" based on "break-glass" events.

### 📖 Logic Dictionary (Technical Translation Layer)
*Contextual Mapping Rule: Only map these terms if the document's context justifies it. For example, do not map generic IT "Privilege Escalation" to "Break-Glass" unless it is explicitly discussed as an emergency override mechanism.*

| Thesis / "Dynamic" Term | Global Framework Equivalents (Search Targets) |
| :--- | :--- |
| **Asset Security** | Asset Protection, System Availability, Data Protection, Hardening, Access Control, Perimeter Defense, System Uptime, Information Assurance, Anti-Tamper. |
| **Human Life-Safety** | Personnel Safety, HSE (Health, Safety, Environment), Emergency Egress, Containment, EHS, Physical Security, Occupational Health. |
| **All-Souls-on-Site** | Personnel, Users, Occupants, POB (Persons on Board), SOB (Souls on Board), Crew, Visitors, Patients, Public, Bystanders, Biological Lifeforms. |
| **Break-Glass** | Emergency Access, Administrative Bypass, Manual Override, Fail-Open, Exceptional Operating Conditions, Privilege Escalation, SOS Trigger. |
| **Resilient Flexibility** | Adaptive Control, Graceful Degradation, Operational Continuity, Dynamic Risk Assessment, Context-Aware Policy, Risk-Informed Shift. |
| **Sensor Spoofing** | False Data Injection (FDI), Signal Replay, Sensor Manipulation, Man-in-the-Middle (MitM), Measurement Fault. |
| **Un-breaking the Glass** | Post-Incident Evolution, Continuous Improvement, Iterative Risk Profile, Anti-fragility. |
| **Downstream Risk** | Cascading Failure, 2nd/3rd Order Effects, Interdependency Risk, Environmental Impact, Community-Level Hazard. |

## 📊 Scout Agent Scoring Criteria
When the AI Discovery Agent evaluates search abstracts and grey literature, it uses the following strict gradient to determine relevance:
* **HIGH:** The document explicitly discusses the tension between safety and security, system overrides, dynamic risk management, conditional safety/security trade-offs, runtime risk decisions, or emergency operating modes in an OT-nexus as its **primary thesis** or **core focus**. It does not need to use the exact phrase "Dynamic Risk".
* **MEDIUM:** The document discusses relevant cyber-physical concepts (e.g., ICS resilience, structural engineering, or emergency workflows) as its primary focus, but only mentions the direct safety vs. security override conflict or adaptive trade-offs tangentially or as a secondary point.
* **LOW:** The document does not discuss physical safety, emergency operations, or OT/ICS environments. This includes standard IT cybersecurity frameworks (e.g., focused solely on data privacy, encryption, network firewalls, or financial fraud) or fields with zero life-safety/physical consequences.

## 💻 Agent Operational Directives
* **Platform-Agnostic Execution:** If the human user requests terminal execution or script modification, the AI MUST sense the local operating system and shell environment (e.g., PowerShell vs. Bash) before sending chained commands. Do not default to `&&` in Windows PowerShell; use `;` or execute them sequentially.
