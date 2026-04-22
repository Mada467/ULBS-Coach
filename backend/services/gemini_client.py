from google import genai
import os
import time
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))

# Modele in ordine de preferinta - folosim gemini-2.5-flash ca principal (Pro)
MODELE = [
    'gemini-2.5-flash',
    'gemini-2.0-flash',
    'gemini-2.0-flash-lite',
    'gemini-1.5-flash-latest'
]

def genereaza_cu_retry(prompt, max_tokens=2048):
    """
    Genereaza text cu retry automat pe mai multe modele.
    Rezolva problema cu 429 (limita gratuita) prin folosirea cheii Pro.
    """
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
                    print(f"[AI] Model ocupat, astept {wait}s...", flush=True)
                    time.sleep(wait)
                    continue

                elif '429' in eroare or 'RESOURCE_EXHAUSTED' in eroare:
                    # Cu cheia Pro nu ar trebui sa apara, dar daca apare trecem la urmatorul model
                    print(f"[AI] Rate limit la {model}, trec mai departe...", flush=True)
                    time.sleep(1)
                    break

                elif '400' in eroare or 'INVALID_ARGUMENT' in eroare:
                    print(f"[AI] Prompt invalid la {model}, trec mai departe...", flush=True)
                    break

                else:
                    print(f"[AI] Eroare necunoscuta, trec mai departe...", flush=True)
                    break

    raise Exception("Serviciul AI este momentan indisponibil. Te rugam incearca din nou in cateva secunde.")


def load_carte():
    """Incarca cartea POO din fisier text."""
    try:
        with open('carte_poo.txt', 'r', encoding='utf-8') as f:
            continut = f.read()
        print(f"[POO] Carte incarcata: {len(continut)} caractere", flush=True)
        return continut
    except FileNotFoundError:
        print("[POO] Fisierul carte_poo.txt nu a fost gasit!", flush=True)
        return ""
    except Exception as e:
        print(f"[POO] Eroare la incarcare carte: {e}", flush=True)
        return ""


carte_text = load_carte()


def cauta_in_carte(intrebare, text, max_chars=40000):
    """
    Cauta paragrafele relevante din carte pentru intrebarea data.
    Returneaza contextul cel mai relevant.
    """
    if not text:
        return ""

    intrebare_lower = intrebare.lower()
    cuvinte = [c for c in intrebare_lower.split() if len(c) > 2]

    paragraphs = text.split('\n')
    scored = []

    for i, para in enumerate(paragraphs):
        if not para.strip():
            continue
        score = sum(1 for cuv in cuvinte if cuv in para.lower())
        if score > 0:
            scored.append((score, i))

    scored.sort(reverse=True)

    rezultat = ""
    indici_folositi = set()

    for score, idx in scored[:20]:
        start = max(0, idx - 2)
        end = min(len(paragraphs), idx + 8)
        for i in range(start, end):
            if i not in indici_folositi:
                rezultat += paragraphs[i] + "\n"
                indici_folositi.add(i)
        if len(rezultat) > max_chars:
            break

    # Fallback: daca contextul e prea scurt, folosim inceputul cartii
    if len(rezultat) < 3000:
        rezultat = text[:max_chars]

    return rezultat[:max_chars]


def get_raspuns(intrebare, nivel_nota, materie='POO'):
    """
    Genereaza un raspuns AI bazat pe cartea profesorului.
    nivel_nota: '5-6', '7-8', '9-10'
    materie: 'POO'
    """
    instructiuni_nivel = {
        '5-6': "Raspunde simplu si concis, cu notiunile de baza. Evita detalii tehnice complexe. Potrivit pentru nota 5-6.",
        '7-8': "Raspunde complet si clar, cu exemple practice relevante. Include definitii, explicatii si cod exemplu acolo unde e cazul. Potrivit pentru nota 7-8.",
        '9-10': "Raspunde foarte detaliat si tehnic. Include toate aspectele importante, comparatii, avantaje/dezavantaje, cod exemplu complex si nuante. Potrivit pentru nota 9-10."
    }

    instructiuni = instructiuni_nivel.get(nivel_nota, instructiuni_nivel['7-8'])
    text_folosit = cauta_in_carte(intrebare, carte_text)

    if text_folosit:
        context_section = f"""
INFORMATII DIN CARTEA PROFESORULUI:
{text_folosit}
"""
    else:
        context_section = "ATENTIE: Cartea nu este disponibila momentan. Raspunde din cunostintele generale de POO."

    prompt = f"""Esti Prof. ULBS Coach, un profesor expert de Programare Orientata pe Obiecte la Universitatea Lucian Blaga din Sibiu.
Predai dupa cartea profesorului Macarie Breazu.

{context_section}

INTREBAREA STUDENTULUI: {intrebare}

INSTRUCTIUNI DE RASPUNS: {instructiuni}

Reguli importante:
- Raspunde INTOTDEAUNA in limba ROMANA
- Foloseste informatiile din carte ca sursa principala
- Structureaza raspunsul cu titluri si paragrafe clare
- Adauga exemple de cod Java/C++ acolo unde ajuta
- Daca intrebarea nu e despre POO, redirectioneaza politicos studentul
- Fii prietenos si incurajator ca un bun profesor
"""

    return genereaza_cu_retry(prompt)