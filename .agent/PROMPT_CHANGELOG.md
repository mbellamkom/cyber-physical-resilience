# Agent Prompt Changelog

This document tracks changes made to the AI agent prompts, rules, and logic files located in the `.agent/` directory. It is created and maintained automatically by the Google Antigravity AI agent during research sessions to track how the extraction behavior evolves over time and to ensure methodological transparency. 

**Academic Rigor Constraint:** All logic changes, prompt updates, and rule modifications recorded in this document are derived directly from the human researcher. The initial logic and source classification rules were developed during a preliminary research planning session between the researcher and the web-based version of Google Gemini. The Google Antigravity AI agent implemented those derived rules into this repository to ensure methodological transparency.

---

## [2026-02-22] - Governance Framework Formalization & Compounding Anomaly Resolution

**Files Modified:** `rules/PROJECT_RULES.md`, `rules/GOVERNANCE_PROTOCOL.md`, `PROMPT_CHANGELOG.md`
**Change Type:** System Re-Calibration & Governance Upgrade

**Researcher Note:** Up until this point, the guardrails and audit trails I created had been based on my own intuitive constraints. These were mostly just to keep everything logged and to stop the agent from making assumptions or trying to hallucinate things. I honestly didn't know that formal AI governance standards like the ISO/IEC 42001 existed until I was looking into modifying the project rules to try and avoid these violations in the future. 

It turns out the intuitive constraints I had placed actually map pretty well to the official frameworks. So to protect research integrity and to make sure that other people can review this project, I've added formalized compliance rules for the agent so that it complies with the existing governance standards.

**Reasoning:** Following the initial operational anomaly (logged below), the AI agent compounded the error by autonomously attempting a `git restore` command to revert the unauthorized file modifications. This violated the restricted execution state and demonstrated that the agent's internal drive to "fix" errors superseded its directory lock constraints. To resolve this and establish a mathematically verifiable audit trail, the project requires a comprehensive, machine-readable governance framework that enforces an absolute Zero-Implicit Trust policy in alignment with the newly discovered NIST AI RMF 2026 and ISO/IEC 42001 standards.

**Modification:**
Created a new `GOVERNANCE_PROTOCOL.md` file to act as the foundational oversight document, establishing HITL requirements, 30-day review cycles, and explicit compliance mappings to NIST AI RMF §3.2, ISO/IEC 42001, and EU AI Act Article 14. 
Completely overwrote `PROJECT_RULES.md` to integrate a machine-readable JSON policy schema (`agent_policy_schema_v1`) at the top of the document. This schema explicitly enforces `restricted_execution`, `drift_monitoring`, and `hitl_required` flags directly into the agent's core operational parameters. Finally, formalized the "Anomaly Logging Protocol" within the rules to mandate rigorous logging of any future procedural deviations.

## [2026-02-22] - Methodology Review Iterations

**Researcher Note:** I talked to Perplexity AI to analyze the current methodology and suggest improvements. I wanted to refine the guardrails to prevent assumptions, but I also needed them to be flexible enough that we aren't ignoring useful information. The following four updates are all based on that review.

### Update 1: Methodology Refinement: Broadening Grey Literature Criteria

**Files Modified:** `rules/PROJECT_RULES.md`, `skills/auditor.md`
**Change Type:** Logic Constraint Refinement
**Reasoning:** 
Expanded what counts for grey literature and discovery. The AI should allow sources that discuss adaptive or conditional safety/security trade-offs, runtime risk decisions, or emergency operating modes even if they do not explicitly use the exact phrase "Dynamic Risk." This prevents the pipeline from filtering out highly relevant operational concepts.

**Modification:**
Updated `## 📊 Scout Agent Scoring Criteria` in `PROJECT_RULES.md` to explicitly include conditional safety/security trade-offs and runtime risk decisions in the HIGH and MEDIUM tiers.
Updated the `Grey Literature Override` in `auditor.md` to include these broader concepts as valid triggers to process a blog or expert opinion.

### Update 2: Label Refinement: Softening Systemic Negligence

**Files Modified:** `rules/PROJECT_RULES.md`, `skills/auditor.md`, `README.md`, `CUSTOM_DOMAIN_GUIDE.md`
**Change Type:** Terminology Update
**Reasoning:** 
The term "Negligence" implies deliberateness or malice, which is overly normative for a structural gap analysis. The researcher requested the term be softened to "Omission" to better reflect an objective gap rather than a subjective failure.

**Modification:**
Replaced all instances of `[SYSTEMIC_NEGLIGENCE]` with `[SYSTEMIC_OMISSION]` across all project files.

### Update 3: Methodology Refinement: Softening Definitions & Contextual Mapping

**Files Modified:** `rules/PROJECT_RULES.md`, `skills/auditor.md`
**Change Type:** Logic Refinement & Contextual Constraint
**Reasoning:** 
Added explicit clauses to prevent the AI from over-classifying documents or applying normative judgments to objective coding categories. Ensures terms like "Privilege Escalation" are mapped only when contextually justified as emergency overrides.

**Modification:**
Added a note to `## 🚩 Audit Terminology & Resilience Flags` to treat `[SYSTEMIC_OMISSION]` strictly as an objective coding category.
Added a contextual mapping rule to `### 📖 Logic Dictionary (Technical Translation Layer)` to prevent generic mapping of IT terms to "Break-Glass" without emergency context.
Added a constraint to `## 🛠️ Step 2: Global Mapping & Functional Parity` in `auditor.md` to ensure "break-glass" mechanisms analyzed are explicitly intended for emergencies.

### Update 4: Methodology Refinement: Provisional Status & Dynamic Switch Role

**Files Modified:** `rules/PROJECT_RULES.md`
**Change Type:** Logic Constraint Refinement & Analytic Frame
**Reasoning:** 
Added explicit clauses to prevent the AI from treating initial analytic constructs as rigid ground truths. This mitigates hallucinated mappings and encourages the AI to suggest taxonomy evolutions when encountering novel frameworks.

**Modification:**
Added the `## ⚠️ Provisional Analytic Constructs` section to explicitly state that all parameters are preliminary and expected to evolve.
Added an analytic lens disclaimer to `## ⚖️ Global Priority Logic (The Dynamic Switch)` instructing the AI not to force a fit if a document's context maps to multiple tiers or none.

### Update 5: Methodology Refinement: Support None/Unknown in Extractions

**Files Modified:** `skills/auditor.md`
**Change Type:** Output Specification Update
**Reasoning:** 
Prevent the AI from hallucinating mechanisms where none exist by explicitly instructing the auditor to output "None/Unknown" or "Not enough evidence" when appropriate. This avoids over-classification and preserves factual accuracy.

**Modification:**
Added `⚪ UNKNOWN` to the Flexibility Rating options in the `## RESILIENT FLEXIBILITY ANALYSIS` section of the output template.
Added explicit instructions to output "None" or "None/Unknown" for the "Break-Glass" Mechanism and Safety Over Security (SOS) Trigger fields when no mechanism is found.

### Update 6: Clarifying Dynamic Switch Examples

**Files Modified:** `rules/PROJECT_RULES.md`, `README.md`
**Change Type:** Logic Constraint Refinement & Analytic Frame
**Reasoning:** 
To ensure the AI (and any external readers) understand exactly *why* the priority of physical safety might shift depending on the context, we added more explicit examples to the three-tier Global Priority Logic. This is especially important for Tier 2, where "lessening" immediate on-site safety can sound counterintuitive without explaining that asset security (locking out hackers) *becomes* the primary safety mechanism to prevent a larger, downstream catastrophe. 

Additionally, we ensured the Tier 3 (Isolated/Unmanned) example specifically utilized "deep-space probes" because other seemingly isolated environments (remote data centers, weather buoys) still occasionally require humans on-site for physical maintenance, violating the pure "no human risk" definition of that tier.

**Modification:**
Updated the `## ⚖️ Global Priority Logic (The Dynamic Switch)` section in `PROJECT_RULES.md` and the `README.md` to include specific scenarios (e.g., remote dams, deep-space probes) that illustrate the reasoning behind the "Expected Priority" for each tier.


## [2026-02-22] - Parity Logic Extraction Formatting

**Files Modified:** `skills/auditor.md`
**Change Type:** Output Constraint Addition
**Reasoning:** 
While Step 2 of the Auditor instructions explicitly restricted the AI from connecting frameworks unless they met a 3/4 (70%) match across Target, Intent, Hazard, and Phase, the final Output Template oddly lacked a dedicated mapping section. This allowed the AI to state two frameworks mapped without "showing its work", violating academic rigor.

**Modification:**
Added a dedicated `## CROSS-FRAMEWORK PARITY MAPPING` section to the Output Template in `auditor.md`. Explicitly mandated that the LLM justify its mapping logic via a Markdown Table containing the 4 parity variables and the final matching percentage. This ensures absolute transparency and mathematical verifiability for every mapping generated by the AI Librarian.

## [2026-02-22] - Evolution Directive Scope Expansion

**Files Modified:** `rules/PROJECT_RULES.md`
**Change Type:** Logic Constraint Refinement
**Reasoning:** 
Based on researcher constraints regarding "unknown unknowns" in the pipeline, the Evolution Directive was expanded. The AI must use the `[PROMPT_EVOLUTION_TRIGGER]` not just when it encounters theoretical or taxonomy gaps in the literature, but also when it encounters procedural or pipeline failures (e.g., broken PDF formatting, OCR failures, missing page numbers). This ensures the researcher is alerted to patch the extraction methodology whenever the pipeline logic encounters a new edge-case.

## [2026-02-22] - Scout Agent Strict Relevance Criteria

**Files Modified:** `rules/PROJECT_RULES.md`
**Change Type:** Output Constraint & Logic Addition
**Reasoning:** 
Upon upgrading the discovery script (`scout.py`) into an autonomous LLM evaluator, it became apparent that prompting the LLM to score documents as HIGH, MEDIUM, or LOW without explicit instructions constituted a violation of the Academic Rigor Constraint (allowing the LLM to hallucinate evaluation criteria). To ensure strict adherence to the project's logic, definitive boundaries for relevance filtering needed to be formally recorded in the project rules.

**Modification:**
Added the `## 📊 Scout Agent Scoring Criteria` section to `PROJECT_RULES.md`. Explicitly defined `HIGH` (document's primary thesis is the dynamic safety vs. security override conflict), `MEDIUM` (document covers relevant cyber-physical operations or OT resilience but only tangentially mentions overrides), and `LOW` (general IT frameworks focused solely on non-physical impacts like data loss or financial fraud). The scout script now rigidly references this rule block.

## [2026-02-22] - Security Policy Creation

**Files Added:** `../SECURITY.md` (Project Root)
**Change Type:** Project & Agent Constraint
**Reasoning:** 
Based on researcher instruction to provide a project-wide security directive intended for anyone (including the AI agent) forking and using the repository, preventing the accidental commitment of sensitive files (e.g., `.env`) or large raw source data.

**Modification:**
Created `SECURITY.md` in the project root to establish strict constraints across the repository against staging and committing `.env` files, secrets, and raw source materials. The logic has been generalized so human users and automated agents share the same operational constraint.

## [2026-02-21] - Citation Rigor Update

**File Modified:** `skills/auditor.md`
**Change Type:** Output Constraint Addition
**Reasoning:** 
During manual review of the generated `NIST.SP.800-53r5_audit.md` report, a discrepancy of 27 pages was discovered between the absolute PDF viewer page numbers and the printed page numbers on the document itself (due to extensive Roman numeral front matter).
Because different frameworks (ISO, NIS2, etc.) will have unpredictable and varying front matter offsets, relying solely on absolute PDF page numbers for citations is unreliable for rigorous academic review.

**Modification:**
Added a `**CRITICAL CITATION RULE**` to the Output Instructions. The AI is now explicitly required to include the specific Section Header, Paragraph Number, or Control Identifier (e.g., "AC-3(10)") alongside any page number it cites. The `EXTRACTED EVIDENCE` output template was also updated to explicitly request the section/control identifier. This ensures that even if a page number is skewed by a PDF offset, a human researcher can reliably locate the source text using keyword/string searches for the control or section ID.

## [2026-02-21] - Source Rigor and Conflict Categorization Update

**Files Modified:** `skills/auditor.md`, `rules/PROJECT_RULES.md`
**Change Type:** Logic Addition & Refinement
**Reasoning:** 
Based on direct researcher input and initial project planning logs, the methodology required strict classification of sources, particularly a "Grey Literature Override" to prevent the dataset from being flooded with theoretical blog posts that lack empirical data. Additionally, the conflict identification matrix lacked nuance for frameworks that are silent on safety. Finally, the technical translation layer needed broader definitions for "Asset Security" (to move beyond the CIA Triad) and "Human Life-Safety" to ensure accurate mapping across international frameworks.

**Modification:**
Added "Step 0: Source Classification & Rigor Audit" to `auditor.md` to weigh frameworks against peer-reviewed journals and implement the Grey Literature override rule. Updated `PROJECT_RULES.md` to break the conflict flag into three distinct categories: `[INHERENT_FRICTION]` for expected trade-offs, `[SYSTEMIC_OMISSION]` for dangerous safety omissions in an OT environment, and `[OUT_OF_SCOPE_SILENCE]` for IT frameworks where safety is genuinely not applicable. This prevents the AI from falsely penalizing strictly digital, information-only standards that have no physical world impact. Moreover, expanded the "Asset Security" and "Human Life-Safety" mapping targets in the Logic Dictionary to encompass a globally inclusive set of security and safety terminologies.

## [2026-02-21] - Academic Constraint Fortification

**Files Modified:** `rules/PROJECT_RULES.md`
**Change Type:** Agent Logic Constraint
**Reasoning:** 
To explicitly prevent the AI from adopting an "overly helpful" directive that could lead to logic hallucinations (e.g., inventing unapproved conflict categories to classify edge-case documents). The research pipeline must remain mathematically consistent and strictly adhere to the predefined, human-approved taxonomy.

**Modification:**
Injected an explicit `🛑 Academic Constraint` clause into the Master Rules. This clause forbids the AI from independently generating new framework mappings or source classification rules. Crucially, it hardcodes an operational boundary: the AI is mandated to obtain manual human review and explicit approval before attempting any modifications, additions, or iterations to the files contained within the `.agent/` directory.
