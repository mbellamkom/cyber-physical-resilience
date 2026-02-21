import os
from dotenv import load_dotenv
from google import genai

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

print("--- Your Available Gemini Models ---")
try:
    for model in client.models.list():
        # Just print everything to see the exact IDs
        print(f"ID: {model.name}")
except Exception as e:
    print(f"[!] Still hitting a snag: {e}")