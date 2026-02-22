# Custom Domain Adaptation Guide

This repository, originally built for analyzing Cyber-Physical Resilience and the intersection of physical life-safety with cybersecurity protocols, is designed to be highly modular. By adjusting a few configuration files and environment variables, you can repurpose this AI Librarian pipeline for *any* research domain (e.g., Medical Compliance, Financial Regulations, AI Ethics Guidelines).

Here is a step-by-step guide on how to adapt the tool for your own domain.

## 1. Define Your Custom Agent Rules
The core intelligence of this pipeline lies in how the AI "Librarian" evaluates documents. 
1. Create a new directory for your rules, e.g., `my_domain_rules/`.
2. Create a `MY_RULES.md` file. In this file, define your **Global Priority Logic**, any specific nuances you want the AI to look for, and the specific constraint flags you care about (similar to `[SYSTEMIC_NEGLIGENCE]` in our example).
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
# The scout.py file will use these terms when searching Google Scholar
RESEARCH_TOPICS="Your Topic 1, Your Topic 2, Your Topic 3"
```

## 3. Verify the Pipeline
Once your rules and environment variables are set:
1. Run `python verify_setup.py` to ensure all necessary `sources/`, `archive/`, and database directories are initialized.
2. Run `python scout.py` to automatically harvest academic papers based on your new `RESEARCH_TOPICS`.
3. Drop the downloaded PDFs into the `sources/` folder and run `python librarian.py`. The agent will now audit the documents based exclusively on your custom logic rather than the default Cyber-Physical constraints!

*(Note: Always remember to abide by the `SECURITY.md` rules and never commit your `.env` file or raw source datasets).*
