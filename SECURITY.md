# Project Security Policy

When forking or contributing to this repository, all users and automated agents must adhere to the following data handling and security rules to protect sensitive information and avoid bloating the version control history.

## Rule 1: Never Commit Environment Variables
**Do not stage, commit, or otherwise expose any `.env` files, API keys, credentials, or secret tokens.** 
If such files are created locally for configuring tools (e.g., LLM keys, database URIs), ensure they are actively ignored by Git.

## Rule 2: Never Commit Raw Source Files
**Do not stage or commit raw source datasets unless explicitly intended for public release.**
Source data includes PDFs, large CSV datasets, vector database dumps (e.g., the `.qdrant_db/` directory), or any third-party intellectual property that should remain confined to your local environment.

## Enforcement Best Practices
When working within this repository, proactively:
1. Verify that `.env` is present in your local `.gitignore`.
2. Verify that `.qdrant_db/` and any other raw data directories are in your `.gitignore`.
3. Use `git status` carefully before staging files to verify no sensitive or untracked bulk data files are added by mistake.
