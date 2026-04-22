from flask import Blueprint, request, jsonify
from baza_date import adauga_materie, salveaza_material, get_materii
import fitz
import os

materiale_bp = Blueprint('materiale', __name__)

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), '..', 'carti')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@materiale_bp.route('/api/materii', methods=['GET'])
def get_materii_route():
    """Returneaza toate materiile unui student."""
    student_id = request.args.get('student_id', 'default')
    materii = get_materii(student_id)
    return jsonify([dict(m) for m in materii])


@materiale_bp.route('/api/upload-pdf', methods=['POST'])
def upload_pdf():
    """
    Upload PDF -> extrage text -> salveaza in DB -> creeaza materia automat.
    """
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
        # Extrage textul din PDF
        pdf_bytes = pdf_file.read()
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        text = ""
        for page in doc:
            page_text = page.get_text()
            if len(page_text.strip()) > 50:
                text += page_text + "\n"
        doc.close()

        if len(text) < 100:
            return jsonify({'error': 'PDF-ul nu contine text suficient!'}), 400

        # Creeaza materia in DB
        materie_id = adauga_materie(student_id, materie_nume, profesor)
        if not materie_id:
            return jsonify({'error': 'Eroare la crearea materiei!'}), 500

        # Salveaza textul in DB
        salveaza_material(materie_id, student_id, pdf_file.filename, text)

        return jsonify({
            'success': True,
            'materie_id': materie_id,
            'materie': materie_nume,
            'caractere': len(text),
            'mesaj': f'PDF procesat cu succes! {len(text)} caractere extrase.'
        })

    except Exception as e:
        print(f"[UPLOAD] Eroare: {e}")
        return jsonify({'error': f'Eroare la procesarea PDF-ului: {str(e)}'}), 500