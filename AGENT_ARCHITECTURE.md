# Architecture Document

This file maps the current logic pipeline of the `google-genai` agents.

## Core Flowchart

```mermaid
flowchart TD
    %% Define Styles
    classDef input fill:#f9f,stroke:#333,stroke-width:2px,color:#000;
    classDef agent fill:#bbf,stroke:#333,stroke-width:2px,color:#000;
    classDef logic fill:#bfb,stroke:#333,stroke-width:2px,color:#000;
    classDef output fill:#fbb,stroke:#333,stroke-width:2px,color:#000;
    classDef flag fill:#ff9,stroke:#e6b800,stroke-width:2px,color:#000;

    A[Document DB & Web Search]:::input --> B(Scout Agent):::agent
    
    subgraph Discovery[Discovery Phase]
        B --> C{Grey Lit Override}:::logic
        C -- "Yes (Dynamic Risk context)" --> D[Process Source]
        C -- "No" --> E[Reject]
        D --> F{Relevance Score}:::logic
        F -- "HIGH / MEDIUM" --> G(Librarian / Auditor Agent):::agent
        F -- "LOW" --> E
    end

    subgraph Evaluation[Evaluation Phase - The Auditor]
        G --> H{The Dynamic Switch}:::logic
        
        H -->|Tier 1: Manned| I[Human/Soul-First Priority]:::logic
        H -->|Tier 2: Remote w/ Downstream Risk| J[Balanced Priority]:::logic
        H -->|Tier 3: Isolated| K[Asset-First Priority]:::logic
        
        I & J & K --> L[Apply Logic Dictionary]:::logic
        L --> M(Extract Conflicts & Mechanisms)
    end

    subgraph OutputPhase[Output & Taxonomy Flags]
        M --> N[JSON Final Analysis]:::output
        M -.-> O[🚩 SYSTEMIC OMISSION]:::flag
        M -.-> P[🚩 INHERENT FRICTION]:::flag
        M -.-> Q[🟡 OUT OF SCOPE]:::flag
        M -.-> R[🚩 PROMPT EVOLUTION TRIGGER]:::flag
    end
```

### Legend & Flags
* **SYSTEMIC OMISSION:** A macro framework fails to acknowledge physical safety despite safety being a direct output of its scope.
* **INHERENT FRICTION:** A necessary security control that intentionally creates tension with life-safety (e.g. locks during a fire).
* **OUT OF SCOPE:** The document is highly technical and truthfully does not intersect with operational physical safety.
* **PROMPT EVOLUTION TRIGGER:** This tells the AI that if it encounters *any* edge case, novel risk framework, or linguistic nuance that breaks the rules defined in `PROJECT_RULES.md`, it must flag it. This alerts the human researcher to update the `PROMPT_CHANGELOG.md` and evolve the definitions, preventing the AI from silently forcing data to fit where it doesn't belong.
