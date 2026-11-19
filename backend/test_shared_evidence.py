
import sys
import time
from pathlib import Path

# Find the main project folder
PROJECT_FOLDER = Path(__file__).resolve().parents[1]

AGENTS_FOLDER = PROJECT_FOLDER / "backend" / "agents"

# Allow Python to import the agent files
sys.path.insert(0, str(AGENTS_FOLDER))

from growth360_workflow import load_business_evidence
from business_doctor_gemini import generate_business_diagnosis


if __name__ == "__main__":

    print("\nTesting Gemini Business Doctor with shared evidence")

    # Load existing reports
    evidence = load_business_evidence()

    print("\nTotal reports loaded:", len(evidence))

    # Try up to three times for temporary connection errors
    for attempt in range(1, 4):

        try:

            print(f"\nGemini attempt {attempt} of 3")

            response = generate_business_diagnosis(evidence)

            print("\nBusiness Doctor test successful!")
            break

        except Exception as error:

            error_message = str(error).lower()

            temporary_errors = [
                "503",
                "unavailable",
                "getaddrinfo failed",
                "connecterror",
                "11001",
                "timeout"
            ]

            is_temporary = any(
                message in error_message
                for message in temporary_errors
            )

            if is_temporary and attempt < 3:

                wait_seconds = attempt * 10

                print("\nGemini connection problem.")
                print(f"Retrying in {wait_seconds} seconds...")

                time.sleep(wait_seconds)

            else:

                print("\nBusiness Doctor test failed.")
                print("Error:", error)

                raise
