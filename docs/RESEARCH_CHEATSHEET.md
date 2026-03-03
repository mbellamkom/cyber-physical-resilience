# 📖 Research Cheatsheet: Scout Agent Operations

This document provides a consolidated reference for the scoring criteria, resilience flags, and command-line operations used in the Cyber-Physical Resilience research project.

---

## 📊 Scoring Gradient (The 3-Tier Filter)

When `scout.py` evaluates a source, it assigns one of three primary scores:

| Score | Meaning | Primary Conditions |
| :--- | :--- | :--- |
| **🟢 HIGH** | **Must Include** | Discusses safety vs. security tension, emergency overrides, or foundational risk frameworks (ISO, IEC, NIST, FEMA). |
| **🟢 HIGH** | **Consequence Override** | ANY digital disruption resulting in a kinetic or physical-world impact (e.g., GPS spoofing, ransomware causing shutdowns). |
| **🟡 MEDIUM** | **Relevant** | Discusses ICS resilience or emergency workflows but only mentions safety/security overrides tangentially. |
| **🔴 LOW** | **Ignore** | Standard IT cybersecurity (data privacy, phishing) or routine workplace safety (OSHA) with no systemic resilience nexus. |

### Special Score Conditions (Flags)

- **🚩 [STRUCTURAL_OMISSION]**: A major framework governing OT/ICS that is **completely silent** on human life-safety or physical consequences. (Treated as **HIGH** for governance gap analysis).
- **💡 [EMERGING_THEME]**: Used to tag documents proposing highly novel intersections of operational risk or human communication.

---

## 🚩 Resilience Flags & Audit Terminology

Use these flags to categorize specific vulnerabilities or gaps discovered in the literature:

| Flag | Meaning |
| :--- | :--- |
| 🚩 **[INHERENT_FRICTION]** | Security controls that actively impede life-safety (e.g., fail-secure doors in a fire). |
| 🟡 **[OUT_OF_SCOPE_SILENCE]** | Legitimate safety silence in a highly specialized technical standard. |
| 🚩 **[REGULATORY_BARRIER]** | Compliance laws that prevent dynamic "flexible" overrides. |
| 🔍 **[SPOOF_VULNERABILITY]** | Sensors vulnerable to manipulation to force an unsafe "fail-open." |
| 🚩 **[CLAIR_SILO]** | Framework fails to acknowledge Primary Infrastructure (Level -1) failure vectors. [Link to CLAIR Model](https://isc.sans.edu/diaryimages/images/The_CLAIR_Model.pdf) |
| 🔄 **[INCIDENT_FEEDBACK_LOOP]** | System requirements for evolving "DNA" based on "break-glass" events. |

### 🔬 Librarian / Auditor Specialist Flags

| Flag | Meaning |
| :--- | :--- |
| 🚩 **[THEORETICAL_ONLY]** | Source discussed Dynamic Risk but lacks empirical data or architectural diagrams. |
| 🟡 **[LOW_PARITY_OUTLIER]** | Document is relevant but fails the 70% parity check against standard frameworks. |
| ⚪ **[UNKNOWN / SOS-NONE]** | Explicit tag used when no "Break-Glass" or "Safety-Over-Security" mechanism is present. |
| **[SKIP_NON_ENGLISH]** | Source discarded due to language barriers. |

---

## ⚖️ Logical Decision Rules

### 1. The 70% Parity Rule (Librarian Stage)
A mapping between two frameworks is only valid if it meets **3 out of 4** functional criteria:
- **Target**: Same asset (e.g., Valve vs. Actuator).
- **Intent**: Same goal (e.g., Access Prevention).
- **Hazard**: Same consequence (e.g., Spill).
- **Phase**: Same timeline (e.g., Emergency Response).

### 2. The Dynamic Switch (Hierarchy of Safety)
- **Tier 1 (Manned)**: **Human/Soul-First.** Security NEVER blocks egress.
- **Tier 2 (Remote)**: **Balanced.** Security *is* safety (prevents downstream disasters).
- **Tier 3 (Isolated)**: **Asset-First.** Hardware integrity is the priority.

---

## ⌨️ Command Line Interface (scout.py)

| Command | Usage | Effect |
| :--- | :--- | :--- |
| `python scout.py` | Standard Run | Executes query generation (cached), search, and evaluation. |
| `python scout.py --refresh` | **Cache Bypass** | Forces DeepSeek-R1 to brainstorm *new* search queries (useful if results feel stale). |
| `python scout.py --recheck` | **Audit Repair** | Systematic scans `seen_sources.md` for `LOW` entries and re-evaluates them (fixes false-negatives). |
| `python scout.py --overnight` | **Power Management** | Shut down the workstation after task completion to preserve hardware. |

---

## 📖 Key Definitions

| Term | Research Context |
| :--- | :--- |
| **Break-Glass** | Emergency manual overrides or administrative bypasses during crises. |
| **All-Souls-on-Site** | Prioritizing *any* biological life (crew, bypassers, patients) over data/asset security. |
| **Downstream Risk** | Cascading failures where an OT glitch causes a 2nd/3rd order physical disaster. |
| **Dynamic Risk** | Moving from static "always secure" policies to "context-aware" resilient shifts. |
