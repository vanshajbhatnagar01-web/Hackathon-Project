
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
import time
MODEL_NAME = "gemini-3.5-flash-lite"




def ask_gemini(prompt, max_attempts=3):
    """
    Send a prompt to Gemini.

    Retry temporary API errors and timeouts.
    """

    import time

    for attempt in range(1, max_attempts + 1):

        try:

            print(
                f"\nGemini request attempt {attempt}/{max_attempts}"
            )

            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt
            )

            if not response.text:
                raise ValueError("Gemini returned an empty response.")

            return response.text

        except Exception as error:

            error_message = str(error).lower()

            status_code = (
                getattr(error, "status_code", None)
                or getattr(error, "code", None)
            )

            retryable_codes = [
                429, 500, 502, 503, 504
            ]

            retryable_messages = [
                "503",
                "504",
                "unavailable",
                "high demand",
                "deadline_exceeded",
                "deadline expired",
                "getaddrinfo failed",
                "connecterror",
                "connection reset",
                "timed out",
                "timeout"
            ]

            should_retry = (
                status_code in retryable_codes
                or any(
                    message in error_message
                    for message in retryable_messages
                )
            )

            if not should_retry:
                raise

            if attempt == max_attempts:

                print("\nGemini failed after all retry attempts.")

                raise

            wait_seconds = 10 * attempt

            print("\nGemini is temporarily unavailable.")
            print("Error:", error)
            print(f"Retrying in {wait_seconds} seconds..." )

            time.sleep(wait_seconds)

    raise RuntimeError("Gemini request could not be completed.")


