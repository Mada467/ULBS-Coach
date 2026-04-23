from google import genai
import os
import time
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))

MODELE = [
    'gemini-2.5-flash',
    'gemini-2.0-flash',
    'gemini-2.0-flash-lite'
]


def genereaza_cu_retry(prompt):
    """Genereaza text cu retry automat pe mai multe modele."""
    for model in MODELE:
        for incercare in range(3):
            try:
                print(f"[AI] Incerc {model} (incercarea {incercare + 1})", flush=True)
                response = client.models.generate_content(
                    model=model,
                    contents=prompt
                )
                print(f"[AI] SUCCESS cu {model}", flush=True)
                return response.text

            except Exception as e:
                eroare = str(e)
                print(f"[AI] EROARE la {model}: {eroare[:300]}", flush=True)

                if '503' in eroare or 'UNAVAILABLE' in eroare:
                    wait = 2 * (incercare + 1)
                    time.sleep(wait)
                    continue
                elif '429' in eroare or 'RESOURCE_EXHAUSTED' in eroare:
                    time.sleep(1)
                    break
                else:
                    break

    raise Exception("Serviciul AI este momentan indisponibil. Incearca din nou.")