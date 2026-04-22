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
                print(f"[CARTONASE] Incerc {model}", flush=True)
                response = client.models.generate_content(
                    model=model,
                    contents=prompt
                )
                print(f"[CARTONASE] SUCCESS cu {model}", flush=True)
                return response.text
            except Exception as e:
                eroare = str(e)
                print(f"[CARTONASE] EROARE la {model}: {eroare[:200]}", flush=True)
                if '503' in eroare or 'UNAVAILABLE' in eroare:
                    time.sleep(2 * (incercare + 1))
                    continue
                elif '429' in eroare or 'RESOURCE_EXHAUSTED' in eroare:
                    time.sleep(1)
                    break
                else:
                    break
    raise Exception("AI indisponibil momentan. Incearca din nou.")


def load_carte_poo():
    """Incarca cartea POO."""
    try:
        with open('carte_poo.txt', 'r', encoding='utf-8') as f:
            return f.read()
    except Exception:
        return ""


def load_chunks_so():
    """Incarca chunks-urile SO."""
    chunks = []
    try:
        with open('carte_so_chunks.jsonl', 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    chunks.append(json.loads(line))
    except Exception:
        pass
    return chunks


def load_carte_custom(materie_id):
    """Incarca cartea unui profesor uploadata de student."""
    try:
        filepath = f'carti/carte_{materie_id}.txt'
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception:
        return ""


carte_poo = load_carte_poo()
so_chunks = load_chunks_so()


def cauta_context(topic, text, max_chars=30000):
    """Cauta contextul relevant din text pentru un topic dat."""
    if not text:
        return ""

    topic_lower = topic.lower()
    cuvinte = [c for c in topic_lower.split() if len(c) > 2]
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

    for score, idx in scored[:15]:
        start = max(0, idx - 2)
        end = min(len(paragraphs), idx + 6)
        for i in range(start, end):
            if i not in indici_folositi:
                rezultat += paragraphs[i] + "\n"
                indici_folositi.add(i)
        if len(rezultat) > max_chars:
            break

    if len(rezultat) < 2000:
        rezultat = text[:max_chars]

    return rezultat[:max_chars]


def genereaza_cartonase(topic, numar=5, materie='POO', tip='teorie'):
    """
    Genereaza cartonase de studiu.
    
    Parametri:
    - topic: subiectul pentru cartonase
    - numar: numarul de cartonase (3, 5, 10)
    - materie: 'POO' sau 'SO'
    - tip: 'teorie' sau 'cod' (pentru quiz mode)
    """
    # Obtine contextul potrivit materiei
    if materie == 'SO':
        chunks_relevante = []
        topic_lower = topic.lower()
        cuvinte = [c for c in topic_lower.split() if len(c) > 3]
        
        for chunk in so_chunks:
            text_lower = chunk.get('text', '').lower()
            score = sum(1 for cuv in cuvinte if cuv in text_lower)
            if score > 0:
                chunks_relevante.append((score, chunk))
        
        chunks_relevante.sort(key=lambda x: x[0], reverse=True)
        top_chunks = [c for _, c in chunks_relevante[:10]]
        
        if top_chunks:
            context = '\n\n'.join([f"[Pagina {c.get('pagina', '?')}]: {c.get('text', '')}" for c in top_chunks])
        else:
            context = f"Genereaza intrebari generale despre {topic} din domeniul Sistemelor de Operare."
        
        materie_descriere = "Sisteme de Operare (Operating System Concepts - Silberschatz)"
    else:
        # POO sau alta materie cu carte uploadata
        carte = carte_poo if materie == 'POO' else load_carte_custom(materie)
        context = cauta_context(topic, carte) if carte else f"Genereaza intrebari generale despre {topic} din domeniul {materie}."
        materie_descriere = f"Programare Orientata pe Obiecte - {materie}" if materie == 'POO' else materie

    # Instructiuni diferite pentru teorie vs cod
    if tip == 'cod':
        instructiuni_tip = """
        Genereaza intrebari care cer studentului sa SCRIE COD sau sa explice cod.
        Fiecare intrebare trebuie sa implice scrierea de cod, debugging, sau analiza de cod.
        Raspunsul trebuie sa contina cod complet si functional.
        """
    else:
        instructiuni_tip = """
        Genereaza intrebari teoretice clare despre concepte, definitii, avantaje/dezavantaje.
        Raspunsurile trebuie sa fie explicatii text clare, fara cod (sau cu cod minimal ca exemplu).
        """

    prompt = f"""Esti un profesor expert de {materie_descriere} la ULBS.
Bazeaza-te pe urmatoarele informatii din carte pentru a genera cartonase de studiu relevante.

CONTEXT DIN CARTE:
{context}

CERINTA: Genereaza exact {numar} cartonase de studiu despre: "{topic}"

{instructiuni_tip}

Raspunde DOAR cu un JSON valid (fara markdown, fara ``` si fara alte texte), in exact acest format:
[
    {{
        "intrebare": "Intrebarea clara si specifica aici?",
        "raspuns": "Raspunsul complet si detaliat aici",
        "dificultate": "usor"
    }},
    {{
        "intrebare": "Alta intrebare?",
        "raspuns": "Alt raspuns complet",
        "dificultate": "mediu"
    }}
]

Valorile pentru "dificultate" pot fi: "usor", "mediu", "greu"
Genereaza EXACT {numar} cartonase, cu dificultati variate.
"""

    text = genereaza_cu_retry(prompt)
    text = text.strip()

    # Curata raspunsul de markdown
    if '```json' in text:
        text = text.split('```json')[1].split('```')[0].strip()
    elif '```' in text:
        text = text.split('```')[1].split('```')[0].strip()

    # Gaseste primul [ din raspuns
    start_idx = text.find('[')
    end_idx = text.rfind(']')
    if start_idx != -1 and end_idx != -1:
        text = text[start_idx:end_idx + 1]

    cartonase = json.loads(text)
    
    # Validare si curatare
    cartonase_validate = []
    for c in cartonase:
        if isinstance(c, dict) and 'intrebare' in c and 'raspuns' in c:
            cartonase_validate.append({
                'intrebare': str(c.get('intrebare', '')),
                'raspuns': str(c.get('raspuns', '')),
                'dificultate': c.get('dificultate', 'mediu') if c.get('dificultate') in ['usor', 'mediu', 'greu'] else 'mediu'
            })
    
    return cartonase_validate