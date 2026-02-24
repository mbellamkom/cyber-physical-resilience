# Contributing Guidelines

Thank you for your interest in contributing to the Cyber-Physical Resilience research project!

## Branching and Commits
To maintain the integrity of our research and codebase, **no one is permitted to make direct changes to the `main` branch aside from the core maintainers**. All updates to `main` must go through a review process.

### Branching Conventions
When creating feature branches, we generally organize them by their purpose to keep the repository history clean:
- **`housekeeping/...`**: For administrative, structural, security, or non-substantive maintenance tasks (e.g., updating documentation, tweaking `.gitignore`, configuring project setups).
- **`agent-logic/...`**: Strictly reserved for substantive changes to the core research methodology and AI extraction logic (e.g., modifying `PROJECT_RULES.md` or updating extraction prompts in `auditor.md`).
- **`feature/...` or `fix/...`**: Used for code changes to the Python execution scripts (e.g., `scout.py`, `librarian.py`) that are not intrinsically tied to a specific methodological update.

## How to Contribute
If you would like to contribute:
1. **Fork the repository** to your own GitHub account.

2. **Review the Guides**: Check the `docs/guides/` folder for important calibration and domain adaptation instructions.
3. **Create a new branch** for your feature, fix, or research addition.
4. **Make your changes**, ensuring they align with our project goals and `.agent/rules/PROJECT_RULES.md`.
5. **Submit a Pull Request (PR)** against the `main` branch of this repository. **Do NOT submit Pull Requests that alter the core logic to fit a completely different domain.** Domain adaptations should remain in your own private forks.


### Review and Merge Process
To maintain strict control over the research pipeline:
- **No one is permitted to make direct changes to the `main` branch aside from the core maintainers.** You must submit a Pull Request.
- **Your PR must be reviewed and approved** by a core maintainer before it can be merged.
- **The `.agent/` directory is strictly controlled.** As defined in our `CODEOWNERS` file, any changes to the AI logic, rules, or skills *require* explicit approval from the primary researcher (`@mbellamkom`).
- **Suggestions and Questions are welcome!** We highly encourage community suggestions on core logic, efficiency optimizations, or new frameworks. If you have questions about specific prompt change decisions, or suggestions for improving the AI logic, please submit these as distinct PRs or GitHub Issues so we can review and discuss them before deciding to integrate them into the agent's prompt files.

## General Rules
- Do not commit secrets, API keys, or `.env` files.
- Document any new research scripts or data sources clearly.
- Ensure your contributions adhere to the established project structure and logic dictionaries.
<<<<<<< HEAD
- **Suggestions and Questions are welcome!** We highly encourage community suggestions on core logic, efficiency optimizations, or new frameworks. If you have questions about specific prompt change decisions, or suggestions for improving the AI logic, please submit these as distinct PRs or GitHub Issues so we can review and discuss them before deciding to integrate them into the agent's prompt files.

## General Rules
- Do not commit secrets, API keys, or `.env` files.
- Document any new research scripts or data sources clearly.
- Ensure your contributions adhere to the established project structure and logic dictionaries.
=======
>>>>>>> cef27cd (Add Contributing, CODEOWNERS, CITATION and update License)
