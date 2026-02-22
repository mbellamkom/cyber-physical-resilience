# Agent Prompt Changelog

This document tracks changes made to the AI agent prompts, rules, and logic files located in the `.agent/` directory. It is created and maintained automatically by the Google Antigravity AI agent during research sessions to track how the extraction behavior evolves over time and to ensure methodological transparency, without requiring the human researcher to manually document every prompt engineering tweak.

---

## [2026-02-21] - Citation Rigor Update

**File Modified:** `skills/auditor.md`
**Change Type:** Output Constraint Addition
**Reasoning:** 
During manual review of the generated `NIST.SP.800-53r5_audit.md` report, a discrepancy of 27 pages was discovered between the absolute PDF viewer page numbers and the printed page numbers on the document itself (due to extensive Roman numeral front matter).
Because different frameworks (ISO, NIS2, etc.) will have unpredictable and varying front matter offsets, relying solely on absolute PDF page numbers for citations is unreliable for rigorous academic review.

**Modification:**
Added a `**CRITICAL CITATION RULE**` to the Output Instructions. The AI is now explicitly required to include the specific Section Header, Paragraph Number, or Control Identifier (e.g., "AC-3(10)") alongside any page number it cites. The `EXTRACTED EVIDENCE` output template was also updated to explicitly request the section/control identifier. This ensures that even if a page number is skewed by a PDF offset, a human researcher can reliably locate the source text using keyword/string searches for the control or section ID.
