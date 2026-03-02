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
    classDef error fill:#ffcccb,stroke:#a30000,stroke-width:2px,color:#000;

    A[Web/Academic Search]:::input --> B(Scout Agent):::agent

    subgraph ScoutPipeline[Discovery & 3-Stage Triage]
        B --> QG[DeepSeek Brainstorm Queries]
        QG --> S1{Stage 1: Python Sieve}:::logic
        S1 -- "Keyword Match" --> HUB[Extractor Hub Enrichment]
        S1 -- "No Match" --> REJ[logs/rejection_audit.md]:::output

        HUB --> S2{Stage 2: Local Bouncer}:::logic
        S2 -- "Potential HIGH/MEDIUM" --> S3{Stage 3: Cloud Specialist}:::logic
        S2 -- "LOW (Rationale Provided)" --> REJ
        S2 -- "Ollama Offline/Error" --> FAIL[Preserve as Unseen]:::error

        S3 -- "Validated HIGH/MEDIUM" --> NOTIF[Discord / Detailed Notification]
        S3 -- "Validated LOW" --> REJ
    end

    subgraph LibrarianPipeline[Technical Auditing]
        MAN[Manual PDF Sourcing]:::input --> LIB(Librarian / Auditor Agent):::agent
        LIB --> H{The Dynamic Switch}:::logic

        H -->|Tier 1: Manned| I[Human/Soul-First Priority]:::logic
        H -->|Tier 2: Remote| J[Balanced Priority]:::logic
        H -->|Tier 3: Isolated| K[Asset-First Priority]:::logic

        I & J & K --> L[Apply Logic Dictionary]:::logic
        L --> M(Extract Conflicts & Mechanisms)
    end

    subgraph FinalLogs[Research Memory]
        NOTIF & S3 & S2 --> MEM[logs/seen_sources.md]:::output
        M --> AUD[audits/ Report]:::output
        M -.-> O[🚩 SYSTEMIC OMISSION]:::flag
        M -.-> P[🚩 INHERENT FRICTION]:::flag
        M -.-> R[🚩 PROMPT EVOLUTION TRIGGER]:::flag
    end
```

### System Architecture Components

1.  **3-Stage Discovery Triage**:
    *   **Python Sieve**: Lexical filter to reduce API costs by discarding non-contextual noise.
    *   **Extractor Hub**: Attempts to enrich snippets with full-text content before secondary evaluation.
    *   **Local Bouncer (Ollama)**: Uses `deepseek-r1:8b` for cost-effective broad screening. Includes "Resilience Failure Mode" where technical errors skip logging to prevent false-negative data poisoning.
    *   **Cloud Specialist (Gemini)**: Performs final precision scoring and detailed researcher notification.

2.  **Log Consolidation (The Audit Trail)**:
    *   **`seen_sources.md`**: The source of truth for all evaluated URLs, preventing duplicates.
    *   **`rejection_audit.md`**: A unified log of all `LOW` relevance findings, fulfilling the Academic Rigor requirement for negative results.

### Legend & Flags
* **SYSTEMIC OMISSION:** A macro framework fails to acknowledge physical safety despite safety being a direct output of its scope.
* **INHERENT FRICTION:** A necessary security control that intentionally creates tension with life-safety (e.g. locks during a fire).
* **[CLAIR_SILO]**: Identifies frameworks that fail to acknowledge failure vectors outside traditional SCADA boundaries (Levels -1, 6, 7). [Link to CLAIR Model](https://isc.sans.edu/diaryimages/images/The_CLAIR_Model.pdf)
* **PROMPT EVOLUTION TRIGGER:** An audit signal that there is a gap in the `PROJECT_RULES.md` and a methodology update is required.
