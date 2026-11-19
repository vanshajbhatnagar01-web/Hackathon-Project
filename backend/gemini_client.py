
import os
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types


project_folder = Path(__file__).resolve().parent.parent


load_dotenv(project_folder / ".env")

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY is missing from the .env file.")



client = genai.Client(
    api_key=api_key,
    http_options=types.HttpOptions(
        timeout=120000
    )
)

MODEL_NAME = "gemini-3.5-flash-lite"


def ask_gemini(prompt):
    """
    Send a prompt to Gemini and return its response.
    """

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt
    )

    if not response.text:
        raise ValueError("Gemini returned an empty response.")

    return response.text
