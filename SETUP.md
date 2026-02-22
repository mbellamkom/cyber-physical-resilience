# Cyber-Physical Resilience Pipeline Setup

This guide covers how to set up your environment and run the automated literature review pipeline for this project.

## Prerequisites

Before you begin, ensure you have the following installed:
* **Python 3.10+**
* A **Google Gemini API Key** (Get one from [Google AI Studio](https://aistudio.google.com/))
* A **Discord Webhook URL** (If you want notifications from the Scout script in Discord)

## 1. Installation

Clone this repository to your local machine:
```bash
git clone https://github.com/YOUR_USERNAME/Cyber-Physical-Resilience.git
cd Cyber-Physical-Resilience
```

Install the required Python dependencies:
```bash
pip install -r requirements.txt
```

## 2. Configuration

Create a file named `.env` in the root of the project. You can copy the variables below and fill in your specific paths and API keys:

```env
# API Keys
GEMINI_API_KEY="your_gemini_api_key_here"
DISCORD_WEBHOOK_URL="your_discord_webhook_url_here" # Optional, leave blank to disable alerts

# Paths (Use absolute paths for best results)
RESEARCH_PATH="C:/Users/.../Documents/Cyber-Physical-Resilience"
SOURCE_DIR="C:/Users/.../Documents/Cyber-Physical-Resilience/sources"
ARCHIVE_DIR="C:/Users/.../Documents/Cyber-Physical-Resilience/archive"

# Vector Database Path
QDRANT_LOCAL_PATH="C:/Users/.../Documents/Cyber-Physical-Resilience/.qdrant_db"
```

*Note: The system will automatically create the directories for `SOURCE_DIR`, `ARCHIVE_DIR`, and `QDRANT_LOCAL_PATH` if they do not exist when you run the diagnostics.*

## 3. Usage & Workflow

Once your environment is configured, you can run the pipeline sequentially:

### Step 1: Verify Setup
Run the diagnostic script to ensure your `.env` is loaded correctly, paths exist, and the local Qdrant vector database can initialize.
```bash
python verify_setup.py
```
*(Optional: Run `python check_models.py` to verify your Gemini API key has access to the required models).*

### Step 2: Scout for New Research
The Scout script searches Google Scholar for specific keywords. When it finds relevant papers, it sends an alert to your Discord webhook and records the link so you aren't notified again.
```bash
python scout.py
```
*(Once you find a relevant PDF through the alerts, download it directly to your `/sources` directory).*

### Step 3: Run the AI Auditor
The Librarian script iterates through all PDFs in your `/sources` directory. It uses the Gemini API, alongside the project rules (`PROJECT_RULES.md`) and persona (`auditor.md`), to extract critical insights.
```bash
python librarian.py
```
*Generated reports will be saved as clean Markdown files in your `/audits` directory, ready to be synthesized into RAG systems like NotebookLM.*
