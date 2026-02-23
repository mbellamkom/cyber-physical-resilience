# Custom Domain Adaptation Guide

This repository, originally built for analyzing Cyber-Physical Resilience and the intersection of physical life-safety with cybersecurity protocols, features a highly modular Python codebase. However, while adjusting a few configuration files will conceptually redirect the pipeline to *any* research domain (e.g., Medical Compliance, Financial Regulations, AI Ethics Guidelines), **adapting the actual AI logic is a rigorous research endeavor.** It requires extensive prompt engineering, strict taxonomy definitions, and iterative edge-case testing to prevent the LLM from hallucinating on new domain material.

Here is a step-by-step guide on how to fundamentally adapt the tool for your own domain.

## 1. Define Your Custom Agent Rules
The core intelligence of this pipeline lies in how the AI "Librarian" evaluates documents. 
1. Create a new directory for your rules, e.g., `my_domain_rules/`.
2. Create a `MY_RULES.md` file. In this file, define your **Global Priority Logic**, any specific nuances you want the AI to look for, and the specific constraint flags you care about (similar to `[SYSTEMIC_OMISSION]` in our example).
3. Create a `my_auditor_skill.md` file. This is the explicit instruction set for the Gemini API call telling the AI exactly *what format* you want the output in and *what steps* it should take before extracting data.

## 2. Update Environment Variables
Open your `.env` file (or copy from `.env.example`) and update the following settings:

```env
# 1. Point the Agent paths to your new rules
AGENT_RULES_PATH=./my_domain_rules/MY_RULES.md
AGENT_SKILLS_PATH=./my_domain_rules/my_auditor_skill.md

# 2. Update Domain-Specific Taxonomy Parameters
# (These are optional flavor variables you can use in your prompts)
TAXONOMY_MODE=YOUR_CUSTOM_DOMAIN
PRIMARY_LENS=FOCUS_ON_XYZ

# 3. Define the Web Scout Topics (Comma-separated)
# The scout.py agent uses these terms as "seeds" to dynamically brainstorm optimized search query variants
RESEARCH_TOPICS="Your Topic 1, Your Topic 2, Your Topic 3"
```

## 3. Verify the Pipeline
Once your rules and environment variables are set:
1. Run `python verify_setup.py` to ensure all necessary `sources/`, `archive/`, and database directories are initialized.
2. Run `python scout.py` to prompt the AI to brainstorm search queries and actively evaluate academic papers (via Google Scholar) and grey literature (via DuckDuckGo). The AI will strictly score all hits against your `MY_RULES.md` and alert you to HIGH relevance documents via Discord.
3. Manually source the PDFs you want, drop them into the `sources/` folder, and run `python librarian.py`. The agent will now audit the documents based exclusively on your custom logic rather than the default Cyber-Physical constraints!

*(Note: Always remember to abide by the `SECURITY.md` rules and never commit your `.env` file or raw source datasets).*
