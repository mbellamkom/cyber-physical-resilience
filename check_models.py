# --- Checks which models you have access to ---
import os
from dotenv import load_dotenv
from google import genai

# Load environment variables (like API keys) from the local .env file
load_dotenv()

# Initialize the new Gemini GenAI Client
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

print("--- Your Available Gemini Models ---")
try:
    # Loop through and list all models your API key has access to
    for model in client.models.list():
        # Just print everything to see the exact IDs
        print(f"ID: {model.name}")
except Exception as e:
    print(f"[!] Still hitting a snag: {e}")