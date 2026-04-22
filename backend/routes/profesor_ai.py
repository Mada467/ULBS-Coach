from services.gemini_client import genereaza_cu_retry
from baza_date import get_text_materie, get_materii, salveaza_intrebare
import re

# ── HELPERS ───────────────────────────────────────────────

def cauta_fragmente_relevante(intrebare, text_complet, top_n=8, fragment_size=800):
    """
    Imparte textul cartii in fragmente si le scoreza dupa relevanta.
    Inlocuieste logica de chunks din fisier .jsonl.
    """
    if not text_complet:
        return []

    # Imparte textul in fragmente de ~800 caractere cu overlap
    fragmente = []
    step = fragment_size - 100  # overlap de 100 chars
    for i in range(0, len(text_complet), step):
        fragment = text_complet[i:i + fragment_size].strip()
        if len(fragment) > 100:
            fragmente.append(fragment)

    if not fragmente:
        return []

    intrebare_lower = intrebare.lower()
    cuvinte = [c for c in re.split(r'\W+', intrebare_lower) if len(c) > 3]

    if not cuvinte:
        return fragmente[:top_n]

    scored = []
    for fragment in fragmente:
        text_lower = fragment.lower()
        score = sum(1 for cuv in cuvinte if cuv in text_lower)
        if score > 0:
            scored.append((score, fragment))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [fragment for _, fragment in scored[:top_n]]


def construieste_context(intrebare, text_complet):
    """Construieste contextul pentru prompt din textul cartii."""
    fragmente = cauta_fragmente_relevante(intrebare, text_complet)

    if fragmente:
        return '\n\n---\n\n'.join(fragmente)
    return "Nu am gasit informatii specifice in materialul uploadat pentru aceasta intrebare."


# ── FUNCTIA PRINCIPALA ────────────────────────────────────

def get_raspuns(intrebare, materie_id, student_id, nivel_nota='7-8'):
    """
    Genereaza un raspuns AI bazat pe materialul uploadat pentru materia respectiva.
    
    Args:
        intrebare: Intrebarea studentului
        materie_id: ID-ul materiei din DB
        student_id: ID-ul studentului
        nivel_nota: '5-6', '7-8', sau '9-10'
    
    Returns:
        String cu raspunsul generat
    """
    # Ia textul cartii din DB
    text_complet = get_text_materie(materie_id, student_id)

    if text_complet:
        context = construieste_context(intrebare, text_complet)
        sursa_info = "materialul uploadat de student"
    else:
        context = "Nu exista material uploadat pentru aceasta materie."
        sursa_info = "cunostintele generale AI (nu exista carte uploadata)"

    instructiuni_nivel = {
        '5-6': "Explica simplu si concis pentru nota 5-6. Foloseste exemple simple si evita termeni tehnici complecsi.",
        '7-8': "Explica complet si clar pentru nota 7-8. Include exemple relevante, definitii si comparatii.",
        '9-10': "Explica foarte detaliat si tehnic pentru nota 9-10. Include toate detaliile, algoritmi, exemple de cod si nuante avansate."
    }
    nivel_text = instructiuni_nivel.get(nivel_nota, instructiuni_nivel['7-8'])

    prompt = f"""Esti Prof. ULBS Coach, un asistent educational la Universitatea Lucian Blaga din Sibiu.
Raspunzi intrebarilor studentilor bazandu-te pe {sursa_info}.

MATERIAL DIN CARTE:
{context}

INTREBAREA STUDENTULUI: {intrebare}

INSTRUCTIUNI: {nivel_text}

Reguli importante:
- Raspunde INTOTDEAUNA in limba ROMANA
- Bazeaza-te pe informatiile din materialul de mai sus ca sursa principala
- Structureaza raspunsul cu titluri si paragrafe clare
- Include exemple de cod/pseudocod acolo unde ajuta
- Fii prietenos si incurajator
- Daca intrebarea nu este legata de materie, spune-i politicos studentului
"""

    return genereaza_cu_retry(prompt)


def get_raspuns_fara_materie(intrebare, nivel_nota='7-8'):
    """
    Fallback: raspuns general AI cand nu e selectata nicio materie.
    """
    instructiuni_nivel = {
        '5-6': "Explica simplu si concis.",
        '7-8': "Explica complet si clar cu exemple.",
        '9-10': "Explica foarte detaliat si tehnic."
    }
    nivel_text = instructiuni_nivel.get(nivel_nota, instructiuni_nivel['7-8'])

    prompt = f"""Esti Prof. ULBS Coach, un asistent educational la Universitatea Lucian Blaga din Sibiu.

INTREBAREA STUDENTULUI: {intrebare}

INSTRUCTIUNI: {nivel_text}

Reguli:
- Raspunde in limba ROMANA
- Fii concis, clar si educational
- Mentioneaza ca pentru raspunsuri mai precise studentul poate uploada cartea materiei
"""
    return genereaza_cu_retry(prompt)