from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
from baza_date import (
    get_connection, init_db, salveaza_intrebare, get_statistici,
    salveaza_sesiune_quiz, salveaza_raspuns_quiz, get_istoric_quiz,
    salveaza_bookmark, get_bookmarks,
    salveaza_material, get_materii, adauga_materie, get_text_materie
)
from services.gemini_client import genereaza_cu_retry
from routes.profesor_ai import get_raspuns, get_raspuns_fara_materie
from services.carte_procesor import extract_text_from_pdf
import os
import json
import tempfile
import fitz

load_dotenv()

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'carti')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

init_db()


# ===== FRONTEND =====

@app.route('/app')
def frontend():
    return send_from_directory('frontend', 'index.html')

@app.route('/app/<path:filename>')
def frontend_static(filename):
    return send_from_directory('frontend', filename)

@app.route('/')
def home():
    return jsonify({'status': 'ULBS Coach API functioneaza!', 'versiune': '3.0'})


# ===== HELPERS =====

def verifica_etica(intrebare, materie_nume=''):
    prompt = f"""Esti un sistem de moderare pentru o aplicatie educationala universitara (ULBS).
Materia curenta: {materie_nume}

Verifica daca aceasta intrebare este adecvata pentru un context academic.

INTREBARE: {intrebare}

Raspunde DOAR cu JSON (fara markdown):
{{
    "permisa": true,
    "motiv": "Explicatie scurta"
}}
"""
    try:
        text = genereaza_cu_retry(prompt).strip()
        if '```' in text:
            text = text.split('```')[1].split('```')[0].replace('json', '').strip()
        return json.loads(text)
    except Exception as e:
        print(f"[ETICA] Eroare: {e}")
        return {"permisa": True, "motiv": ""}


def evalueaza_raspuns_ai(intrebare, raspuns_student, raspuns_corect, materie_nume=''):
    prompt = f"""Esti un profesor strict dar corect la ULBS.
Materia: {materie_nume}

INTREBAREA: {intrebare}
RASPUNSUL CORECT: {raspuns_corect}
RASPUNSUL STUDENTULUI: {raspuns_student}

Evalueaza raspunsul studentului si raspunde DOAR cu JSON (fara markdown):
{{
    "nota": 8,
    "feedback": "Ce a facut bine si ce a gresit...",
    "explicatie": "Raspunsul complet corect este...",
    "corect": true
}}
"""
    try:
        text = genereaza_cu_retry(prompt).strip()
        if '```' in text:
            text = text.split('```')[1].split('```')[0].replace('json', '').strip()
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


# ===== MATERII =====

@app.route('/api/materii', methods=['GET'])
def get_materii_route():
    student_id = request.args.get('student_id', 'default')
    materii = get_materii(student_id)
    return jsonify([dict(m) for m in materii])


# ===== INTREABA AI =====

@app.route('/api/intreaba', methods=['POST'])
def intreaba():
    data = request.get_json()
    intrebare = data.get('intrebare', '').strip()
    nivel_nota = data.get('nivel_nota', '7-8')
    materie_id = data.get('materie_id')
    materie_nume = data.get('materie_nume', '')
    student_id = data.get('student_id', 'default')

    if not intrebare:
        return jsonify({'error': 'Intrebarea lipseste!'}), 400

    if len(intrebare) > 1000:
        return jsonify({'error': 'Intrebarea este prea lunga (max 1000 caractere)!'}), 400

    etica = verifica_etica(intrebare, materie_nume)
    if not etica.get('permisa', True):
        return jsonify({
            'error': 'intrebare_nepermisa',
            'motiv': etica.get('motiv', 'Intrebarea nu este adecvata.')
        }), 400

    if materie_id:
        raspuns = get_raspuns(intrebare, materie_id, student_id, nivel_nota)
    else:
        raspuns = get_raspuns_fara_materie(intrebare, nivel_nota)

    salveaza_intrebare(student_id, materie_id, materie_nume, intrebare, nivel_nota)

    return jsonify({'raspuns': raspuns})


# ===== CARTONASE =====

@app.route('/api/cartonase', methods=['POST'])
def cartonase():
    data = request.get_json()
    topic = data.get('topic', '').strip()
    numar = data.get('numar', 5)
    materie_id = data.get('materie_id')
    materie_nume = data.get('materie_nume', '')
    student_id = data.get('student_id', 'default')
    tip = data.get('tip', 'teorie')

    if not topic:
        return jsonify({'error': 'Topicul lipseste!'}), 400

    context = ''
    if materie_id:
        from routes.profesor_ai import cauta_fragmente_relevante
        text_complet = get_text_materie(materie_id, student_id)
        if text_complet:
            fragmente = cauta_fragmente_relevante(topic, text_complet, top_n=5)
            context = '\n\n'.join(fragmente)

    context = context[:3000] if context else ""
    context_prompt = f"\n\nCONTEXT DIN CARTE:\n{context}" if context else ""

    prompt = f"""Esti Prof. ULBS Coach. Genereaza {numar} cartonase de studiu pentru materia "{materie_nume}".
Topic: {topic}
Tip: {tip} (teorie = concepte teoretice, cod = exemple de cod){context_prompt}

Raspunde DOAR cu JSON valid (fara markdown):
{{
    "cartonase": [
        {{
            "intrebare": "...",
            "raspuns": "...",
            "dificultate": "usor|mediu|greu"
        }}
    ]
}}
"""
    try:
        text = genereaza_cu_retry(prompt).strip()
        if '```' in text:
            text = text.split('```')[1].split('```')[0].replace('json', '').strip()
        start = text.find('[')
        end = text.rfind(']')
        if start != -1 and end != -1:
            text = '{"cartonase":' + text[start:end + 1] + '}'
        else:
            start = text.find('{')
            end = text.rfind('}')
            if start != -1 and end != -1:
                text = text[start:end + 1]
        result = json.loads(text)
        cartonase_list = result.get('cartonase', result if isinstance(result, list) else [])
        return jsonify({'cartonase': cartonase_list, 'materie': materie_nume})
    except Exception as e:
        print(f"[CARTONASE] Eroare: {e}")
        return jsonify({'error': 'AI indisponibil momentan. Incearca din nou!'}), 503


# ===== QUIZ =====

@app.route('/api/quiz/evalueaza', methods=['POST'])
def evalueaza_raspuns():
    data = request.get_json()
    intrebare = data.get('intrebare', '')
    raspuns_student = data.get('raspuns_student', '').strip()
    raspuns_corect = data.get('raspuns_corect', '')
    materie_nume = data.get('materie_nume', data.get('materie', ''))

    if not intrebare or not raspuns_student:
        return jsonify({'error': 'Date incomplete!'}), 400

    rezultat = evalueaza_raspuns_ai(intrebare, raspuns_student, raspuns_corect, materie_nume)
    return jsonify(rezultat)


@app.route('/api/quiz/sesiune', methods=['POST'])
def salveaza_sesiune():
    data = request.get_json()
    student_id = data.get('student_id', 'default')
    materie = data.get('materie_nume', data.get('materie', ''))
    topic = data.get('topic', '')
    tip = data.get('tip', 'teorie')
    numar_intrebari = data.get('numar_intrebari', 0)
    scor_final = data.get('scor_final', 0)
    nota_finala = data.get('nota_finala', 0)

    sesiune_id = salveaza_sesiune_quiz(student_id, materie, topic, tip, numar_intrebari, scor_final, nota_finala)

    for r in data.get('raspunsuri', []):
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


# ===== STATISTICI =====

@app.route('/api/statistici', methods=['GET'])
def statistici():
    student_id = request.args.get('student_id', 'default')
    limit = request.args.get('limit', 20, type=int)
    return jsonify(get_statistici(student_id, limit))


@app.route('/api/statistici/quiz', methods=['GET'])
def statistici_quiz():
    student_id = request.args.get('student_id', 'default')
    limit = request.args.get('limit', 10, type=int)
    return jsonify(get_istoric_quiz(student_id, limit))


# ===== BOOKMARKS =====

@app.route('/api/bookmark', methods=['POST'])
def adauga_bookmark_route():
    data = request.get_json()
    student_id = data.get('student_id', 'default')
    materie = data.get('materie', '')
    intrebare = data.get('intrebare', '').strip()
    raspuns = data.get('raspuns', '')
    dificultate = data.get('dificultate', 'mediu')

    if not intrebare:
        return jsonify({'error': 'Intrebarea lipseste!'}), 400

    success = salveaza_bookmark(student_id, materie, intrebare, raspuns, dificultate)
    return jsonify({'success': success})


@app.route('/api/bookmarks', methods=['GET'])
def get_bookmarks_route():
    student_id = request.args.get('student_id', 'default')
    materie = request.args.get('materie')
    return jsonify([dict(r) for r in get_bookmarks(student_id, materie)])


# ===== UPLOAD PDF =====

@app.route('/api/upload-pdf', methods=['POST'])
def upload_pdf():
    if 'pdf' not in request.files:
        return jsonify({'error': 'Nu a fost trimis niciun fisier PDF!'}), 400

    pdf_file = request.files['pdf']
    materie_nume = request.form.get('materie_nume', '').strip()
    profesor = request.form.get('profesor', '').strip()
    student_id = request.form.get('student_id', 'default').strip()

    if not materie_nume:
        return jsonify({'error': 'Numele materiei este obligatoriu!'}), 400

    if not pdf_file.filename.endswith('.pdf'):
        return jsonify({'error': 'Fisierul trebuie sa fie PDF!'}), 400

    try:
        pdf_bytes = pdf_file.read()
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            tmp.write(pdf_bytes)
            tmp_path = tmp.name

        text = ""
        doc = fitz.open(tmp_path)
        for page in doc:
            page_text = page.get_text()
            if len(page_text.strip()) > 50:
                text += page_text + "\n"
        doc.close()

        if len(text) < 100:
            print("[UPLOAD] Text insuficient, incerc OCR...", flush=True)
            text = extract_text_from_pdf(tmp_path) or ""

        os.remove(tmp_path)

        if len(text) < 100:
            return jsonify({'error': 'PDF-ul nu contine text suficient!'}), 400

        materie_id = adauga_materie(student_id, materie_nume, profesor)
        if not materie_id:
            return jsonify({'error': 'Eroare la crearea materiei!'}), 500

        salveaza_material(materie_id, student_id, pdf_file.filename, text)

        return jsonify({
            'success': True,
            'materie_id': materie_id,
            'materie': materie_nume,
            'caractere': len(text),
            'mesaj': f'PDF procesat! {len(text)} caractere extrase.'
        })

    except Exception as e:
        print(f"[UPLOAD] Eroare: {e}")
        return jsonify({'error': f'Eroare la procesarea PDF-ului: {str(e)}'}), 500


@app.route('/api/carti', methods=['GET'])
def get_carti():
    student_id = request.args.get('student_id', 'default')
    materii = get_materii(student_id)
    result = []
    for m in materii:
        result.append({
            'materie_id': m['id'],
            'materie_nume': m['nume'],
            'profesor': m.get('profesor', ''),
            'created_at': str(m['created_at'])
        })
    return jsonify(result)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)