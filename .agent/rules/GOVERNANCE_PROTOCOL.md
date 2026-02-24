{
  "schema_ref": "agent_governance_schema_v1",
  "policy_id": "ANTIGRAVITY-GOV-01",
  "version": "1.0",
  "repository": "cyber-physical-resilience",
  "hitl_required": true,
  "authorization_required": true,
  "review_cycle_days": 30,
  "approvers": ["Lead Researcher"],
  "compliance_refs": [
    "NIST AI RMF 2026 §3.2",
    "ISO/IEC 42001",
    "COPE Guidelines 2025",
    "EU AI Act Article 14"
  ],
  "last_reviewed": "2026-02-22T21:00-05:00",
  "signature_required": true
}

## 1. Governance Scope
This protocol governs authorship, revision, and oversight of operational rule files contained in the .agent/ framework. It establishes the procedures through which policies like PROJECT_RULES.md are created, verified, and amended.

## 2. Review and Amendment Procedures
All modifications to PROJECT_RULES.md require explicit authorization by the Lead Researcher. Updates must state purpose, compliance category, and relevant anomaly context.

## 3. Anomaly Audit and Escalation
Operational Anomalies collected from PROMPT_CHANGELOG.md form the basis of post-hoc auditing. If recurrent patterns appear, the researcher must flag the issue for procedural revision.

## 4. Compliance Framework Mapping
| Regulatory Framework | Implemented Control |
| :--- | :--- |
| NIST AI RMF (2026) | Continuous monitoring through Verbose Mode. |
| ISO/IEC 42001 | Formalized AI governance and approval mechanisms. |
| EU AI Act Art. 14 | Guaranteed Human-in-the-Loop oversight. |

## 5. Split-Trust Architecture
The agent operates in a **Split-Trust Execution State**:
* **The Restricted Zone:** The `.agent/` directory is strictly locked. NO modifications can be made to rules, skills, or logs without the human providing the exact APPROVED keyword.
* **The Operational Zone:** The repository root and python scripts (like `scout.py` and `librarian.py`) remain fully open for autonomous AI execution to ensure high-velocity research.
