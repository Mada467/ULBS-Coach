from google import genai
import os
import json
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))

# Incarca chunks din cartea de SO
def load_chunks():
    chunks = []
    try:
        with open('carte_so_chunks.jsonl', 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    chunks.append(json.loads(line))
        print(f"SO chunks incarcate: {len(chunks)}")
    except Exception as e:
        print(f"Eroare incarcare SO chunks: {e}")
    return chunks

so_chunks = load_chunks()

def cauta_chunks_relevante(intrebare, chunks, top_n=5):
    """Cauta cele mai relevante chunks pentru intrebare"""
    intrebare_lower = intrebare.lower()
    cuvinte = [c for c in intrebare_lower.split() if len(c) > 3]
    
    scored = []
    for chunk in chunks:
        text_lower = chunk['text'].lower()
        score = sum(1 for cuv in cuvinte if cuv in text_lower)
        if score > 0:
            scored.append((score, chunk))
    
    # Sorteaza dupa scor si returneaza top N
    scored.sort(key=lambda x: x[0], reverse=True)
    return [chunk for _, chunk in scored[:top_n]]

def get_raspuns_so(intrebare, nivel_nota='7-8'):
    """Genereaza raspuns pentru o intrebare despre Sisteme de Operare"""
    
    # Cauta chunks relevante
    chunks_relevante = cauta_chunks_relevante(intrebare, so_chunks)
    
    if chunks_relevante:
        context = '\n\n'.join([f"[Pagina {c['pagina']}]: {c['text']}" for c in chunks_relevante])
    else:
        context = "Nu am gasit informatii specifice in carte pentru aceasta intrebare."
    
    # Determina nivelul de detaliu
    if nivel_nota == '5-6':
        nivel_text = "Explica simplu si concis, pentru nota 5-6. Foloseste exemple simple."
    elif nivel_nota == '7-8':
        nivel_text = "Explica complet si clar, pentru nota 7-8. Include exemple relevante."
    else:
        nivel_text = "Explica foarte detaliat si tehnic, pentru nota 9-10. Include toate detaliile."
    
    prompt = f"""Esti un profesor expert in Sisteme de Operare la ULBS (Universitatea Lucian Blaga din Sibiu).
Predai dupa cartea "Operating System Concepts" de Silberschatz.

Foloseste urmatoarele informatii din carte pentru a raspunde:
{context}

INTREBAREA STUDENTULUI: {intrebare}

INSTRUCTIUNI: {nivel_text}
- Raspunde INTOTDEAUNA in limba ROMANA
- Bazeaza-te pe informatiile din carte dar explica in termeni clari
- Daca intrebarea nu e despre Sisteme de Operare, spune-i studentului sa puna intrebari relevante
- Foloseste formatare clara cu titluri si exemple de cod daca e cazul
"""
    
    response = client.models.generate_content(
        model='gemini-2.5-flash', # <--- Modificarea este aici
        contents=prompt
    )
    return response.text