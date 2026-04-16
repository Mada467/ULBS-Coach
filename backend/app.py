from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
from database import get_connection
from ai_service import get_raspuns, client
from cartonase import genereaza_cartonase
import os
import json

load_dotenv()

app = Flask(__name__)
CORS(app)

@app.route('/app')
def frontend():
    return send_from_directory('frontend', 'ULBS-Coach.html')

@app.route('/app/<path:filename>')
def frontend_static(filename):
    return send_from_directory('frontend', filename)

def verifica_etica(intrebare):
    prompt = f"""
    Esti un sistem de moderare pentru o aplicatie educationala de POO la ULBS.
    
    Verifica daca aceasta intrebare este:
    1. Relevanta pentru Programare Orientata pe Obiecte sau informatica
    2. Adecvata pentru un mediu educational
    3. Nu contine limbaj ofensator sau nepotrivit
    
    INTREBARE: {intrebare}
    
    Raspunde DOAR cu JSON valid:
    {{
        "permisa": true,
        "motiv": "Explicatie scurta"
    }}
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
    
    return json.loads(text)

@app.route('/')
def home():
    return jsonify({'status': 'ULBS Coach API functioneaza!'})

@app.route('/api/intreaba', methods=['POST'])
def intreaba():
    data = request.get_json()
    intrebare = data.get('intrebare')
    nivel_nota = data.get('nivel_nota', '7-8')
    
    if not intrebare:
        return jsonify({'error': 'Intrebarea lipseste!'}), 400
    
    try:
        etica = verifica_etica(intrebare)
        if not etica.get('permisa', True):
            return jsonify({
                'error': 'intrebare_nepermisa',
                'motiv': etica.get('motiv', 'Intrebarea nu este relevanta pentru aceasta materie.')
            }), 400
    except Exception as e:
        print(f"Eroare verificare etica: {e}")
    
    raspuns = get_raspuns(intrebare, nivel_nota)
    
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO statistici (materie_id, intrebare, nota_ceruta) VALUES (%s, %s, %s)",
            (1, intrebare, nivel_nota)
        )
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Eroare salvare statistici: {e}")
    
    return jsonify({'raspuns': raspuns})

@app.route('/api/statistici', methods=['GET'])
def statistici():
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT intrebare, nota_ceruta, created_at FROM statistici ORDER BY created_at DESC LIMIT 20")
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        result = [{'intrebare': r[0], 'nota': r[1], 'data': str(r[2])} for r in rows]
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/cartonase', methods=['POST'])
def cartonase():
    data = request.get_json()
    topic = data.get('topic')
    numar = data.get('numar', 5)
    
    if not topic:
        return jsonify({'error': 'Topicul lipseste!'}), 400
    
    try:
        cartonase_list = genereaza_cartonase(topic, numar)
        return jsonify({'cartonase': cartonase_list})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/quiz/evalueaza', methods=['POST'])
def evalueaza_raspuns():
    data = request.get_json()
    intrebare = data.get('intrebare')
    raspuns_student = data.get('raspuns_student')
    raspuns_corect = data.get('raspuns_corect')
    
    if not intrebare or not raspuns_student:
        return jsonify({'error': 'Date incomplete!'}), 400
    
    try:
        prompt = f"""
        Esti un profesor de POO la ULBS.
        Evalueaza raspunsul studentului la urmatoarea intrebare.
        
        INTREBARE: {intrebare}
        RASPUNS CORECT: {raspuns_corect}
        RASPUNS STUDENT: {raspuns_student}
        
        Dai o nota de la 1 la 10 si un feedback scurt.
        Raspunde DOAR cu JSON valid:
        {{
            "nota": 8,
            "feedback": "Feedback aici",
            "corect": true
        }}
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
        
        rezultat = json.loads(text)
        return jsonify(rezultat)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

app.run(host='0.0.0.0', port=5000, debug=True)