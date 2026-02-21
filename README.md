# Dynamic Risk Management: Cyber-Physical Research Pipeline

## 1. Project Overview
This project investigates **Dynamic Risk Management** in critical infrastructure, specifically, models that shift organizations from rigid security postures to flexible, risk-informed, and resilient behaviors such as adaptability (the ability to recognize when one risk outweighs another), [graceful degradation](https://www.sciencedirect.com/topics/computer-science/graceful-degradation) (maintaining critical components while letting non-critical ones degrade) and [post-incident evolution](https://dl.acm.org/doi/10.1145/3643666.3648578) (adjusting the existing system to incorporate lessons learned from an incident). 

The core focus of this research is the **"Break-Glass" intersection**: the critical moment during an emergency where cybersecurity lockdowns must be intentionally degraded or bypassed to save lives or prevent a physical disaster. 

When these cyber-physical emergencies occur, practitioners are caught between two operational philosophies:
* **Cybersecurity (Traditonally Fail-Secure):** Defaults to locking systems down to protect data and hardware.
* **Emergency Management (Fail-Safe):** Defaults to keeping access open to preserve life and maintain critical operations.



To evaluate how different global frameworks (like NIST, ISO, and FEMA) handle this conflict, this project utilizes a semi-automated literature review pipeline. The pipeline uses a three-tier **Dynamic Switch** logic to determine how systems *should* behave in an emergency:

* **Tier 1: Manned Facilities (High Proximity):** In locations like hospitals or transport hubs, the rule is **Human/Soul-First**. Security must fail-open to ensure it never impedes escape routes or life-support for **All-Souls-on-Site** (prioritizing biological life over data or hardware).
* **Tier 2: Remote Sites with Downstream Risk:** In unmanned locations like remote power substations or dams, the rule is **Balanced**. The system must prioritize asset security (locking down) specifically to prevent secondary, community-level physical disasters or environmental hazards.
* **Tier 3: Isolated/Unmanned Sites:** In completely isolated environments, the rule is **Asset-First**, prioritizing strict mission continuity and hardware integrity above all else.

---

## 2. The Automation Pipeline
Reading hundreds of technical frameworks, academic papers, incident reports, and other relevant pieces of media manually is a massive bottleneck. To solve this, the project uses local Python scripts and AI to automate the discovery and note-taking process.



The workflow is broken into three steps:

* **Step 1: Discovery (`scout.py`)** A background script that monitors academic databases for specific search terms related to system overrides and safety friction. When it finds a match, it downloads the PDF. It keeps a "smart memory" log of what it has already seen so it doesn't send duplicate alerts.
* **Step 2: Technical Extraction (`librarian.py`)** A script that uses an AI model (Gemini) to read the downloaded PDFs. Instead of generating general summaries, the AI is programmed to extract specific decision models, safety triggers, and framework rules. It saves these notes as clean Markdown text files.
* **Step 3: Synthesis** The extracted notes and metadata are pushed via a command-line interface into NotebookLM. This creates a searchable, private Retrieval-Augmented Generation (RAG) library that I can use to connect the dots, map frameworks together, and draft the final analysis.

---

## 3. Agent Directives: Controlling the AI

I didn't want the AI to summarize or draw conclusions for me. I want to do the analysis myself. So, to force the AI to produce rigorous, usable data, it operates under strict rule files located in the `.agent/directory:

### A. The Master Rules (`PROJECT_RULES.md`)
This file acts as the AI's logic board:
* **Priority Logic:** Enforces the 3-tier Dynamic Switch (Human/Soul-First vs. Asset-First) mentioned above.
* **Technical Translation Dictionary:** Equips the AI to translate jargon across industries. For example, if a cybersecurity paper mentions "Privilege Escalation," the AI tags it as a physical "Break-Glass" mechanism. It also translates organizational terms like "Personnel" into universal safety terms like "All-Souls-on-Site."
* **The Evolution Directive:** Instructs the AI to be iterative. If it reads a paper that introduces a completely novel way of handling risk, it flags a suggested rule update to the me. This was made so that I didn't have to try and think of every issue that could potentially arise. 

### B. The Auditor Persona (`auditor.md`)
This file dictates *how* the AI reads the text and formats its notes:
* **The Persona & Kill Switch:** The AI acts exclusively as a "Senior Cyber-Physical Resilience Auditor." It is instructed to immediately stop reading and skip any document that is 100% focused on information security (data loss) with zero physical consequences.
* **70% Parity Mapping:** When comparing different global frameworks, the AI is forbidden from using simple keyword matching. A mapping is only valid if it meets 3 out of 4 functional criteria: *Target* (same asset), *Intent* (same goal), *Hazard* (same consequence), and *Phase* (same timeline).



* **FEMA Lifeline Translation:** To bridge the gap between digital and physical impacts, the AI maps any extracted cyber failures directly to FEMA's 7 Community Lifelines (e.g., mapping a "network outage" directly to the physical "Energy" impact). These lifelines are mapped to ISO critical sectors to account for international frameworks and terminology. 

---

## 4. Adapting this Framework for Your Own Research
This setup is highly adaptable. While this specific project focuses on translating cybersecurity doctrine into operational emergency management risk, the underlying code can be used for large-scale literature reviews in any field. 

By simply replacing the search terms in the Scout script and rewriting the rule files to fit your specific domain, you can force the AI to evaluate literature against your own theoretical frameworks.

---

## 5. Directory Structure
```text
/Cyber-Physical-Resilience
├── README.md            # You are here
├── scout.py             # Discovery & Smart Memory script
├── librarian.py         # AI Auditor script
├── seen_sources.txt     # The Scout's memory log
├── .env                 # API Keys & Path Configs
├── sources/             # Raw PDF storage for ingestion
├── audits/              # Generated Markdown notes
└── .agent/    
    ├── rules/           
    │   └── PROJECT_RULES.md  # Core project constraints & priority logic
    └── skills/          
        └── auditor.md        # Librarian persona & evaluation logic
