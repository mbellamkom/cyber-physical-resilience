# Contributing Guidelines

Thank you for your interest in contributing to the Cyber-Physical Resilience research project!

## Branching and Commits
To maintain the integrity of our research and codebase, **all active development takes place in the `dev` branch**. The `main` branch is reserved for stable, verified releases.

### Branching Conventions
All updates should be submitted as Pull Requests (PRs) targeting the **`dev`** branch. When creating feature branches, we generally organize them by their purpose:
- **`housekeeping/...`**: For administrative, structural, security, or non-substantive maintenance tasks (e.g., updating documentation, tweaking `.gitignore`).
- **`agent-logic/...`**: Strictly reserved for substantive changes to the core research methodology and AI extraction logic (e.g., modifying `PROJECT_RULES.md`).
- **`feature/...` or `fix/...`**: Used for code changes to the Python execution scripts (e.g., `scout.py`, `librarian.py`).

## How to Contribute
If you would like to contribute:
1. **Fork the repository** to your own GitHub account.
2. **Review the Guides**: Check the `docs/guides/` folder for important calibration and domain adaptation instructions.
3. **Create a new branch** from `dev` for your feature, fix, or research addition.
4. **Make your changes**, ensuring they align with our project goals and `.agent/rules/PROJECT_RULES.md`.
5. **Submit a Pull Request (PR)** against the **`dev`** branch of this repository. **Do NOT submit Pull Requests that alter the core logic to fit a completely different domain.** Domain adaptations should remain in your own private forks.

### Review and Merge Process
To maintain strict control over the research pipeline:
- **No one is permitted to make direct changes to the `main` or `dev` branches aside from the core maintainers.**
- **Your PR must be reviewed and approved** by a core maintainer before it can be merged into `dev`.
- **The `.agent/` directory is strictly controlled.** As defined in our `CODEOWNERS` file, any changes to the AI logic, rules, or skills *require* explicit approval from the primary researcher (`@mbellamkom`).
- **Suggestions and Questions are welcome!** We highly encourage community suggestions on core logic or efficiency optimizations. Please submit these as distinct PRs or GitHub Issues for discussion.

## General Rules
- Do not commit secrets, API keys, or `.env` files.
- Document any new research scripts or data sources clearly.
- Ensure your contributions adhere to the established project structure and logic dictionaries.
