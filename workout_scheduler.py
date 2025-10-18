import os
import json
import re
from dotenv import load_dotenv
import google.generativeai as genai

# Load the Gemini API key
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("Missing GEMINI_API_KEY in .env")

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)

# Use the most widely available model
MODEL_NAME = "gemini-2.5-flash"

def generate_workout_plan(user_goal: str):
    """
    Send a goal to Gemini and return a structured weekly workout plan as JSON.
    """
    prompt = f"""
    You are a professional fitness coach.
    The user says: "{user_goal}"

    Create a clear, progressive weekly workout plan to help them reach their goal.
    Respond ONLY with a valid JSON object (no markdown, no explanations).
    Include:
    - "weeks": a list of objects each with
      - "week" (number)
      - "sessions": list of workout sessions with fields:
        "day", "exercise", "sets", "reps", and optional "notes".
    Example:
    {{
      "weeks": [
        {{
          "week": 1,
          "sessions": [
            {{"day": "Monday", "exercise": "Pull-up negatives", "sets": 3, "reps": 5}},
            {{"day": "Tuesday", "exercise": "Rest"}}
          ]
        }}
      ]
    }}
    """

    try:
        model = genai.GenerativeModel(MODEL_NAME)
        response = model.generate_content(prompt)
        text = response.text.strip()

        # Try to extract and parse JSON
        json_match = re.search(r"\{.*\}", text, re.DOTALL)
        if json_match:
            try:
                plan = json.loads(json_match.group(0))
                return plan
            except json.JSONDecodeError:
                pass  # fallback to raw text

        # Fallback: return raw text if parsing fails
        return {"raw_text": text}

    except Exception as e:
        return {"error": str(e)}