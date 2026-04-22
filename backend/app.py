from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
from database import (
    get_connection, init_db, salveaza_intrebare, get_statistici,
    salveaza_sesiune_quiz, salveaza_raspuns_quiz, get_istoric_quiz,
    salveaza_intrebare_bookmark, get_bookmarks,
    salveaza_carte_uploadata, get_carti_uploadate
)
from ai_service import get_raspuns, genereaza_cu_retry
from cartonase import genereaza_cartonase
from so_service import get_raspuns_so
import os
import json
import uuid

load_dotenv()

app = Flask(__name__)
CORS(app)

# Directorul pentru carti uploadate
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'carti')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Initializeaza schema DB la pornire
init_db()


# ===== FRONTEND ROUTES =====

@app.route('/app')
def frontend():
    return send_from_directory('frontend', 'ULBS-Coach.html')

@app.route('/app/<path:filename>')
def frontend_static(filename):
    return send_from_directory('frontend', filename)

@app.route('/')
def home():
    return jsonify({'status': 'ULBS Coach API functioneaza!', 'versiune': '2.0'})


# ===== HELPER: VERIFICARE ETICA =====

def verifica_etica(intrebare, materie='POO'):
    """Verifica daca intrebarea este relevanta si adecvata."""
    prompt = f"""Esti un sistem de moderare pentru o aplicatie educationala universitara (ULBS).
Materia curenta: {materie}

Verifica daca aceasta intrebare este:
1. Relevanta pentru materia {materie}
2. Adecvata pentru un context academic

INTREBARE: {intrebare}

Raspunde DOAR cu JSON (fara markdown):
{{
    "permisa": true,
    "motiv": "Explicatie scurta"
}}
"""
    try:
        text = genereaza_cu_retry(prompt)
        text = text.strip()
        if '```json' in text:
            text = text.split('```json')[1].split('```')[0].strip()
        elif '```' in text:
            text = text.split('```')[1].split('```')[0].strip()
        return json.loads(text)
    except Exception as e:
        print(f"[ETICA] Eroare verificare: {e}")
        return {"permisa": True, "motiv": ""}


# ===== QUIZ: EVALUARE HELPER =====

def evalueaza_raspuns_ai(intrebare, raspuns_student, raspuns_corect, materie='POO'):
    """Evalueaza raspunsul unui student cu AI si ofera explicatii."""
    prompt = f"""Esti un profesor strict dar corect de {materie} la ULBS.

INTREBAREA: {intrebare}
RASPUNSUL CORECT: {raspuns_corect}
RASPUNSUL STUDENTULUI: {raspuns_student}

Evalueaza raspunsul studentului pe o scara de la 1 la 10 si ofera:
1. O nota numerica (1-10)
2. Feedback constructiv (ce a facut bine, ce a gresit)
3. O explicatie clara a raspunsului corect

Raspunde DOAR cu JSON (fara markdown):
{{
    "nota": 8,
    "feedback": "Ai inteles conceptul principal, dar...",
    "explicatie": "Raspunsul complet corect este...",
    "corect": true
}}
"""
    try:
        text = genereaza_cu_retry(prompt)
        text = text.strip()
        if '```json' in text:
            text = text.split('```json')[1].split('```')[0].strip()
        elif '```' in text:
            text = text.split('```')[1].split('```')[0].strip()

        # Gaseste JSON-ul
        start = text.find('{')
        end = text.rfind('}')
        if start != -1 and end != -1:
            text = text[start:end + 1]

        return json.loads(text)
    except Exception as e:
        print(f"[QUIZ] Eroare evaluare: {e}")
        return {
            "nota": 5,
            "feedback": "Nu am putut evalua raspunsul. Verifica manual.",
            "explicatie": raspuns_corect,
            "corect": False
        }


# ===== API ROUTES =====

@app.route('/api/intreaba', methods=['POST'])
def intreaba():
    """Endpoint pentru intrebari POO."""
    data = request.get_json()
    intrebare = data.get('intrebare', '').strip()
    nivel_nota = data.get('nivel_nota', '7-8')

    if not intrebare:
        return jsonify({'error': 'Intrebarea lipseste!'}), 400

    if len(intrebare) > 1000:
        return jsonify({'error': 'Intrebarea este prea lunga (max 1000 caractere)!'}), 400

    # Verificare etica
    etica = verifica_etica(intrebare, 'POO')
    if not etica.get('permisa', True):
        return jsonify({
            'error': 'intrebare_nepermisa',
            'motiv': etica.get('motiv', 'Intrebarea nu este adecvata.')
        }), 400

    raspuns = get_raspuns(intrebare, nivel_nota, materie='POO')

    # Salvare in DB (non-blocking)
    salveaza_intrebare(1, 'POO', intrebare, nivel_nota)

    return jsonify({'raspuns': raspuns})


@app.route('/api/so/intreaba', methods=['POST'])
def intreaba_so():
    """Endpoint pentru intrebari SO."""
    data = request.get_json()
    intrebare = data.get('intrebare', '').strip()
    nivel_nota = data.get('nivel_nota', '7-8')

    if not intrebare:
        return jsonify({'error': 'Intrebarea lipseste!'}), 400

    # Verificare etica
    etica = verifica_etica(intrebare, 'SO')
    if not etica.get('permisa', True):
        return jsonify({
            'error': 'intrebare_nepermisa',
            'motiv': etica.get('motiv', 'Intrebarea nu este adecvata.')
        }), 400

    raspuns = get_raspuns_so(intrebare, nivel_nota)

    # Salvare in DB (non-blocking)
    salveaza_intrebare(2, 'SO', intrebare, nivel_nota)

    return jsonify({'raspuns': raspuns})


@app.route('/api/statistici', methods=['GET'])
def statistici():
    """Returneaza statisticile si istoricul intrebarilor."""
    limit = request.args.get('limit', 20, type=int)
    result = get_statistici(limit)
    return jsonify(result)


@app.route('/api/statistici/quiz', methods=['GET'])
def statistici_quiz():
    """Returneaza istoricul sesiunilor de quiz."""
    limit = request.args.get('limit', 10, type=int)
    result = get_istoric_quiz(limit)
    return jsonify(result)


@app.route('/api/cartonase', methods=['POST'])
def cartonase():
    """Genereaza cartonase de studiu pentru materia selectata."""
    data = request.get_json()
    topic = data.get('topic', '').strip()
    numar = data.get('numar', 5)
    materie = data.get('materie', 'POO').upper()
    tip = data.get('tip', 'teorie')  # 'teorie' sau 'cod'

    if not topic:
        return jsonify({'error': 'Topicul lipseste!'}), 400

    # Validare materie
    materii_valide = ['POO', 'SO']
    if materie not in materii_valide:
        materie = 'POO'

    try:
        cartonase_list = genereaza_cartonase(topic, numar, materie, tip)
        return jsonify({'cartonase': cartonase_list, 'materie': materie})
    except Exception as e:
        print(f"[APP] Eroare cartonase: {e}")
        return jsonify({'error': 'AI indisponibil momentan. Incearca din nou!'}), 503


@app.route('/api/quiz/evalueaza', methods=['POST'])
def evalueaza_raspuns():
    """Evalueaza un raspuns de quiz cu AI."""
    data = request.get_json()
    intrebare = data.get('intrebare', '')
    raspuns_student = data.get('raspuns_student', '').strip()
    raspuns_corect = data.get('raspuns_corect', '')
    materie = data.get('materie', 'POO').upper()

    if not intrebare or not raspuns_student:
        return jsonify({'error': 'Date incomplete!'}), 400

    rezultat = evalueaza_raspuns_ai(intrebare, raspuns_student, raspuns_corect, materie)
    return jsonify(rezultat)


@app.route('/api/quiz/sesiune', methods=['POST'])
def salveaza_sesiune():
    """Salveaza o sesiune de quiz completata."""
    data = request.get_json()
    materie = data.get('materie', 'POO')
    topic = data.get('topic', '')
    tip = data.get('tip', 'teorie')
    numar_intrebari = data.get('numar_intrebari', 0)
    scor_final = data.get('scor_final', 0)
    nota_finala = data.get('nota_finala', 0)

    sesiune_id = salveaza_sesiune_quiz(materie, topic, tip, numar_intrebari, scor_final, nota_finala)

    # Salveaza raspunsurile individuale
    raspunsuri = data.get('raspunsuri', [])
    for r in raspunsuri:
        if sesiune_id:
            salveaza_raspuns_quiz(
                sesiune_id,
                r.get('intrebare', ''),
                r.get('raspuns_student', ''),
                r.get('raspuns_corect', ''),
                r.get('nota', 0),
                r.get('feedback', '')
            )

    return jsonify({'success': True, 'sesiune_id': sesiune_id})


@app.route('/api/bookmark', methods=['POST'])
def adauga_bookmark():
    """Salveaza o intrebare in bookmarks."""
    data = request.get_json()
    materie = data.get('materie', 'POO')
    intrebare = data.get('intrebare', '').strip()
    raspuns = data.get('raspuns', '')
    dificultate = data.get('dificultate', 'mediu')

    if not intrebare:
        return jsonify({'error': 'Intrebarea lipseste!'}), 400

    success = salveaza_intrebare_bookmark(materie, intrebare, raspuns, dificultate)
    return jsonify({'success': success})


@app.route('/api/bookmarks', methods=['GET'])
def get_bookmarks_route():
    """Returneaza intrebarile salvate."""
    materie = request.args.get('materie')
    result = get_bookmarks(materie)
    # Converteste obiectele Row in dict
    return jsonify([dict(r) for r in result])


@app.route('/api/upload-pdf', methods=['POST'])
def upload_pdf():
    """
    Upload PDF al unui profesor si proceseaza-l in text.
    Permite studentilor sa adauge materiile proprii.
    """
    if 'pdf' not in request.files:
        return jsonify({'error': 'Nu a fost trimis niciun fisier PDF!'}), 400

    pdf_file = request.files['pdf']
    materie_nume = request.form.get('materie_nume', '').strip()
    profesor = request.form.get('profesor', '').strip()

    if not materie_nume:
        return jsonify({'error': 'Numele materiei este obligatoriu!'}), 400

    if not pdf_file.filename.endswith('.pdf'):
        return jsonify({'error': 'Fisierul trebuie sa fie PDF!'}), 400

    try:
        import fitz  # PyMuPDF

        # Salveaza PDF temporar
        unique_id = str(uuid.uuid4())[:8]
        pdf_filename = f"carte_{unique_id}.pdf"
        pdf_path = os.path.join(UPLOAD_FOLDER, pdf_filename)
        pdf_file.save(pdf_path)

        # Extrage textul
        text = ""
        doc = fitz.open(pdf_path)
        for page in doc:
            page_text = page.get_text()
            if len(page_text.strip()) > 50:
                text += page_text + "\n"
        doc.close()

        if len(text) < 100:
            os.remove(pdf_path)
            return jsonify({'error': 'PDF-ul nu contine text suficient sau este scanat!'}), 400

        # Salveaza textul
        txt_filename = f"carte_{unique_id}.txt"
        txt_path = os.path.join(UPLOAD_FOLDER, txt_filename)
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(text)

        # Sterge PDF-ul (pastram doar textul)
        os.remove(pdf_path)

        # Salveaza in DB
        salveaza_carte_uploadata(materie_nume, profesor, txt_filename, txt_path, len(text))

        return jsonify({
            'success': True,
            'materie': materie_nume,
            'caractere': len(text),
            'mesaj': f'PDF procesat cu succes! {len(text)} caractere extrase.'
        })

    except ImportError:
        return jsonify({'error': 'PyMuPDF nu este instalat pe server!'}), 500
    except Exception as e:
        print(f"[UPLOAD] Eroare: {e}")
        return jsonify({'error': f'Eroare la procesarea PDF-ului: {str(e)}'}), 500


@app.route('/api/carti', methods=['GET'])
def get_carti():
    """Returneaza lista cartilor uploadate."""
    carti = get_carti_uploadate()
    return jsonify([dict(c) for c in carti])


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)