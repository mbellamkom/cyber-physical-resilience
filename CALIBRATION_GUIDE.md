# Calibration Guide

Before running the entire research pipeline at scale, it is highly recommended to conduct a manual calibration phase. Because this framework uses AI agents governed by specific logic, verifying that the AI correctly interprets the nuances of your domain ensures the integrity of your final dataset.

## The Calibration Process

To calibrate the pipeline:

1. **Select a Sample Set:** Manually select a small, diverse sample of documents (e.g., 5-10 sources). Include a mix of primary frameworks, peer-reviewed papers, and grey literature relevant to your research.
2. **Manual Coding:** Read and manually code these documents against your own framework criteria. Determine what their "Flexibility Rating" should be, note any break-glass mechanisms, and identify relevant "Flags & Conflicts."
3. **AI Pipeline Execution:** Run the `scout.py` and `librarian.py` scripts on the exact same sample set.
4. **Compare and Adjust:** Compare your manual findings with the AI's output in the `audits/` directory.

## What to Adjust

If the AI's output diverges from your manual coding, you will need to adjust your agent rule files (`.agent/rules/PROJECT_RULES.md` and `.agent/skills/auditor.md`). Focus your adjustments on the following areas:

* **Logic Dictionary:** Does the AI need more terms mapping to "Asset Security" or "Break-Glass" for your specific sector?
* **Flags:** Is the AI over-applying or under-applying conflict flags like `[SYSTEMIC_OMISSION]`? Refine the definitions of the flags.
* **Parity Rules:** Are the 70% matching criteria too strict or too loose for your domain's literature?
* **Flexibility Ratings:** Is the AI accurately discerning between rigid, conditional, and adaptive systems? Provide more explicit examples in the auditor skill if it is struggling.

## Documentation

Remember to log any changes you make to the rules or prompts during this calibration phase in the `.agent/PROMPT_CHANGELOG.md` to maintain methodological transparency.
