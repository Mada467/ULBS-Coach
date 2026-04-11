from google import genai
import os
import json
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))

def load_carte():
    try:
        with open('carte_poo.txt', 'r', encoding='utf-8') as f:
            return f.read()
    except:
        return ""

carte_text = load_carte()

def genereaza_cartonase(topic, numar=5):
    prompt = f"""
    Esti un profesor de POO la ULBS.
    Bazeaza-te pe cartea de mai jos.
    
    CARTEA:
    {carte_text[:40000]}
    
    Genereaza exact {numar} cartonase de studiu despre: {topic}
    
    Raspunde DOAR cu un JSON valid, fara alte texte, in acest format:
    [
        {{
            "intrebare": "Intrebarea aici?",
            "raspuns": "Raspunsul complet aici",
            "dificultate": "usor/mediu/greu"
        }}
    ]
    """
    
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt
    )
    
    text = response.text.strip()
    if '```json' in text:
        text = text.split('```json')[1].split('```')[0].strip()
    elif '```' in text:
        text = text.split('```')[1].split('```')[0].strip()
    
    cartonase = json.loads(text)
    return cartonase