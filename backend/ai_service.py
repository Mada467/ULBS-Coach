from google import genai
import os
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
print(f"Carte incarcata: {len(carte_text)} caractere")

def cauta_in_carte(intrebare, text):
    intrebare_lower = intrebare.lower()
    cuvinte = [c for c in intrebare_lower.split() if len(c) > 2]
    
    paragraphs = text.split('\n')
    scored = []
    
    for i, para in enumerate(paragraphs):
        score = sum(1 for cuv in cuvinte if cuv in para.lower())
        if score > 0:
            scored.append((score, i))
    
    scored.sort(reverse=True)
    
    rezultat = ""
    indici_folositi = set()
    
    for score, idx in scored[:20]:
        start = max(0, idx - 3)
        end = min(len(paragraphs), idx + 10)
        for i in range(start, end):
            if i not in indici_folositi:
                rezultat += paragraphs[i] + "\n"
                indici_folositi.add(i)
        if len(rezultat) > 40000:
            break
    
    if len(rezultat) < 5000:
        rezultat = text[:50000]
    
    return rezultat

def get_raspuns(intrebare, nivel_nota):
    if nivel_nota == "5-6":
        instructiuni = "Raspunde simplu si scurt, cu notiuni de baza, ca pentru nota 5-6."
    elif nivel_nota == "7-8":
        instructiuni = "Raspunde complet si clar, cu exemple, ca pentru nota 7-8."
    else:
        instructiuni = "Raspunde foarte detaliat, cu exemple si explicatii profunde, ca pentru nota 9-10."

    text_folosit = cauta_in_carte(intrebare, carte_text)

    prompt = f"""
    Esti un profesor de Programare Orientata pe Obiecte la ULBS.
    Foloseste DOAR informatiile din cartea de mai jos pentru a raspunde.
    
    CARTEA:
    {text_folosit}
    
    INTREBARE: {intrebare}
    
    INSTRUCTIUNI: {instructiuni}
    
    Raspunde in limba romana.
    """

    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt
    )
    return response.text