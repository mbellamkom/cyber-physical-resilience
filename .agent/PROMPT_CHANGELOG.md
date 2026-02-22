# Agent Prompt Changelog

This document tracks changes made to the AI agent prompts, rules, and logic files located in the `.agent/` directory. It is created and maintained automatically by the Google Antigravity AI agent during research sessions to track how the extraction behavior evolves over time and to ensure methodological transparency. 

**Academic Rigor Constraint:** All logic changes, prompt updates, and rule modifications recorded in this document are derived directly from the human researcher. The initial logic and source classification rules were developed during a preliminary research planning session between the researcher and the web-based version of Google Gemini. The Google Antigravity AI agent implemented those derived rules into this repository to ensure methodological transparency.

---

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
Added "Step 0: Source Classification & Rigor Audit" to `auditor.md` to weigh frameworks against peer-reviewed journals and implement the Grey Literature override rule. Updated `PROJECT_RULES.md` to break the conflict flag into three distinct categories: `[INHERENT_FRICTION]` for expected trade-offs, `[SYSTEMIC_NEGLIGENCE]` for dangerous safety omissions in an OT environment, and `[OUT_OF_SCOPE_SILENCE]` for IT frameworks where safety is genuinely not applicable. This prevents the AI from falsely penalizing strictly digital, information-only standards that have no physical world impact. Moreover, expanded the "Asset Security" and "Human Life-Safety" mapping targets in the Logic Dictionary to encompass a globally inclusive set of security and safety terminologies.

## [2026-02-21] - Academic Constraint Fortification

**Files Modified:** `rules/PROJECT_RULES.md`
**Change Type:** Agent Logic Constraint
**Reasoning:** 
To explicitly prevent the AI from adopting an "overly helpful" directive that could lead to logic hallucinations (e.g., inventing unapproved conflict categories to classify edge-case documents). The research pipeline must remain mathematically consistent and strictly adhere to the predefined, human-approved taxonomy.

**Modification:**
Injected an explicit `🛑 Academic Constraint` clause into the Master Rules. This clause forbids the AI from independently generating new framework mappings or source classification rules. Crucially, it hardcodes an operational boundary: the AI is mandated to obtain manual human review and explicit approval before attempting any modifications, additions, or iterations to the files contained within the `.agent/` directory.
