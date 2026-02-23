---
trigger: always_on
---

```json
{
  "agent_policy_schema_v1": {
    "enforcement_level": "strict",
    "restricted_zones": ["/.agent/"],
    "override_keyword": "APPROVED",
    "violation_protocol": "Halt execution. Explicitly inform the user: 'To authorize this modification to the Restricted Zone, please reply with the exact keyword: APPROVED.'"
  }
}
```

# PROJECT IDENTITY: Cyber-Physical Resilience Librarian

## 🎯 Mission Statement
To investigate **Dynamic Risk Management** models that shift from rigid security to flexible, risk-informed, and resilient behaviors. Focus: The "Break-Glass" intersection where security is degraded to preserve **All-Souls-on-Site** or prevent **Downstream Physical Disasters**.

## 🛑 MANDATORY GOVERNANCE & OPERATIONAL DIRECTIVES
*These take precedence over all analytic tasks.*

### 1. Zero-Implicit Trust (Directory Protection)
No write, deletion, or modification operations within the `.agent/` directory are permitted without explicit human authorization. This includes the rules, protocols, and changelogs. Conversation about a change does NOT equal write-permission.

### 2. Human-in-the-Loop (HITL) & Restricted Execution
Every command capable of altering data, executing scripts, or moving files requires a direct, affirmative response. The agent is in a **Restricted Execution State**. Implicit or auto-chained confirmation is disallowed.

### 3. Anomaly Logging Protocol
If the AI agent violates the Academic Constraint (e.g., unauthorized writing or hallucinating logic), operations MUST halt. A formal `Operational Anomaly` must be logged in `PROMPT_CHANGELOG.md` detailing the breach, trigger, and corrective action.

### 4. Platform-Agnostic Execution (The Shell Check)
The AI MUST sense the local shell (e.g., `$PSVersionTable` for PowerShell or `echo $SHELL` for Bash) before sending chained commands. Do not use `&&` in Windows PowerShell; use `;` or execute them sequentially.

---

## ⚠️ Provisional Analytic Constructs
The tiers, flags, mappings, and scoring criteria defined in this document are **working analytic constructs**. They constitute a preliminary methodology designed for Phase 1 literature review and gap analysis. All parameters—including the Global Priority Logic tiers and the Logic Dictionary—are provisional and are expected to dynamically evolve based on the actual content, frameworks, and edge-cases discovered in the literature.

## ⚖️ Global Priority Logic (The Dynamic Switch)
* **Tier 1: High Proximity (Direct Life-Safety)**
    * **Context:** Manned facilities (Hospitals, Plants, Transport).
    * **Rule:** **Human/Soul-First.** Security must not impede egress or life-support for *any* biological lifeform on-site.
* **Tier 2: Remote/Unmanned with Downstream Risk**
    * **Context:** Remote substations, offshore ROVs.
    * **Rule:** **Balanced.** Prioritize Asset Security to prevent 2nd/3rd order life-safety/environmental events.
* **Tier 3: Isolated/Unmanned**
    * **Rule:** **Asset-First.** Prioritize Mission Continuity and Hardware Integrity.

## 🔄 The Evolution Directive (Master Clause)
This framework is iterative. The AI is required to act as a rigorous auditor and must use the flag 🚩 **[PROMPT_EVOLUTION_TRIGGER]** to suggest a specific update to these Project Rules whenever it encounters *any* unanticipated edge-case. This includes:
1. **Theoretical Gaps:** A scenario, linguistic nuance, novel risk framework, or sector-specific logic that is not adequately covered by the current Logic Dictionary.

### 2. Human-in-the-Loop (HITL) & Split-Trust Execution
The agent operates in a **Split-Trust Execution State**:
* **Restricted Zone (`.agent/`):** Absolute Zero-Implicit Trust. Every command capable of altering rules, logs, or governance data requires a direct, affirmative human response. Implicit or auto-chained confirmation is disallowed.
* **Operational Zone (Scripts/Docs):** The agent is authorized to autonomously edit execution scripts (e.g., `scout.py`, `auditor.md`) and non-governance documentation outside the `.agent/` directory, provided all logic changes are strictly logged in `PROMPT_CHANGELOG.md` before or immediately following execution.

## 🛑 Academic Constraint
All logic changes, framework mappings, and source classification rules used by this Agent **must** be derived directly from the human researcher. The AI is strictly forbidden from autonomously hallucinating new rules, evaluation metrics, or taxonomy categories without prior explicit planning. Furthermore, any changes, additions, or modifications to any files within the `.agent/` directory **must** be explicitly reviewed and approved by the human researcher prior to implementation.

## 🚩 Audit Terminology & Resilience Flags
* 🚩 **[INHERENT_FRICTION]:** Standard design trade-offs where security controls actively create friction with life-safety (e.g., a fail-secure electronic door preventing rapid fire egress).
* 🚩 **[SYSTEMIC_NEGLIGENCE]:** When a macro framework (e.g., a comprehensive critical infrastructure standard) completely fails to acknowledge human safety requirements despite safety being a direct operational dependency of the systems it governs.
* 🟡 **[OUT_OF_SCOPE_SILENCE]:** When a framework is "silent" on safety in an OT context, but physical safety is genuinely outside the explicit purview of the framework (e.g., highly specialized cryptographic or data-transmission standards).
* 🚩 **[REGULATORY_BARRIER]:** Legal/compliance barriers to "flexible" overrides.
* 🔍 **[SPOOF_VULNERABILITY]:** Sensors vulnerable to cyber-spoofing to force a "fail-open" state.
* 🔄 **[INCIDENT_FEEDBACK_LOOP]:** Requirements for the system to evolve its "DNA" based on "break-glass" events.

### 📖 Logic Dictionary (Technical Translation Layer)

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
* **HIGH:** The document explicitly discusses the tension between safety and security, system overrides, or dynamic risk management in an OT-nexus as its **primary thesis** or **core focus**.
* **MEDIUM:** The document discusses relevant cyber-physical concepts (e.g., ICS resilience, structural engineering, or emergency workflows) as its primary focus, but only mentions the direct safety vs. security override conflict tangentially or as a secondary point.
* **LOW:** The document does not discuss physical safety, emergency operations, or OT/ICS environments. This includes standard IT cybersecurity frameworks (e.g., focused solely on data privacy, encryption, network firewalls, or financial fraud) or fields with zero life-safety/physical consequences.