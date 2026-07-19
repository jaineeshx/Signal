import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

api_key = os.getenv("GEMINI_API_KEY")
print(f"Key loaded: {api_key}")
genai.configure(api_key=api_key)

try:
    model = genai.GenerativeModel("gemini-3.5-flash")
    response = model.generate_content("Say hello")
    print(f"SUCCESS: {response.text}")
except Exception as e:
    print(f"ERROR calling model: {type(e).__name__} - {e}")
