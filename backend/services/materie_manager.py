from google import genai
import os
import json
import time
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))

MODELE = [
    'gemini-2.5-flash',
    'gemini-2.0-flash',
    'gemini-2.0-flash-lite',
    'gemini-1.5-flash-latest'
]


def genereaza_cu_retry(prompt):
    """Genereaza text cu retry pe mai multe modele."""
    for model in MODELE:
        for incercare in range(3):
            try:
                print(f"[SO] Incerc {model} (incercarea {incercare + 1})", flush=True)
                response = client.models.generate_content(
                    model=model,
                    contents=prompt
                )
                print(f"[SO] SUCCESS cu {model}", flush=True)
                return response.text

            except Exception as e:
                eroare = str(e)
                print(f"[SO] EROARE la {model}: {eroare[:300]}", flush=True)

                if '503' in eroare or 'UNAVAILABLE' in eroare:
                    wait = 2 * (incercare + 1)
                    time.sleep(wait)
                    continue
                elif '429' in eroare or 'RESOURCE_EXHAUSTED' in eroare:
                    time.sleep(1)
                    break
                else:
                    break

    raise Exception("Serviciul AI este momentan indisponibil. Te rugam incearca din nou.")


def load_chunks():
    """Incarca chunks-urile din cartea SO."""
    chunks = []
    try:
        with open('carte_so_chunks.jsonl', 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    chunks.append(json.loads(line))
        print(f"[SO] Chunks incarcate: {len(chunks)}", flush=True)
    except FileNotFoundError:
        print("[SO] Fisierul carte_so_chunks.jsonl nu a fost gasit!", flush=True)
    except Exception as e:
        print(f"[SO] Eroare la incarcare chunks: {e}", flush=True)
    return chunks


so_chunks = load_chunks()


def cauta_chunks_relevante(intrebare, chunks, top_n=8):
    """Cauta cele mai relevante chunks pentru intrebarea data."""
    if not chunks:
        return []

    intrebare_lower = intrebare.lower()
    cuvinte = [c for c in intrebare_lower.split() if len(c) > 3]

    if not cuvinte:
        return chunks[:top_n]

    scored = []
    for chunk in chunks:
        text_lower = chunk.get('text', '').lower()
        score = sum(1 for cuv in cuvinte if cuv in text_lower)
        if score > 0:
            scored.append((score, chunk))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [chunk for _, chunk in scored[:top_n]]


def get_raspuns_so(intrebare, nivel_nota='7-8'):
    """
    Genereaza un raspuns AI pentru intrebari de Sisteme de Operare.
    nivel_nota: '5-6', '7-8', '9-10'
    """
    chunks_relevante = cauta_chunks_relevante(intrebare, so_chunks)

    if chunks_relevante:
        context = '\n\n'.join([
            f"[Pagina {c.get('pagina', '?')}]: {c.get('text', '')}"
            for c in chunks_relevante
        ])
    else:
        context = "Nu am gasit informatii specifice in carte pentru aceasta intrebare."

    instructiuni_nivel = {
        '5-6': "Explica simplu si concis pentru nota 5-6. Foloseste exemple simple si evita termeni tehnici complecsi.",
        '7-8': "Explica complet si clar pentru nota 7-8. Include exemple relevante, definitii si comparatii.",
        '9-10': "Explica foarte detaliat si tehnic pentru nota 9-10. Include toate detaliile, algoritmi, exemple de cod si nuante avansate."
    }

    nivel_text = instructiuni_nivel.get(nivel_nota, instructiuni_nivel['7-8'])

    prompt = f"""Esti Prof. ULBS Coach, un profesor expert de Sisteme de Operare la Universitatea Lucian Blaga din Sibiu.
Predai dupa cartea "Operating System Concepts" de Silberschatz, Galvin si Gagne.

INFORMATII DIN CARTEA PROFESORULUI:
{context}

INTREBAREA STUDENTULUI: {intrebare}

INSTRUCTIUNI: {nivel_text}

Reguli importante:
- Raspunde INTOTDEAUNA in limba ROMANA
- Bazeaza-te pe informatiile din carte ca sursa principala
- Structureaza raspunsul cu titluri si paragrafe clare
- Include exemple de cod/pseudocod acolo unde ajuta
- Daca intrebarea nu e despre Sisteme de Operare, spune-i studentului politicos sa puna intrebari relevante
- Fii prietenos si incurajator
"""

    return genereaza_cu_retry(prompt)