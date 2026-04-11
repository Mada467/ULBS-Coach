from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from database import get_connection
from ai_service import get_raspuns
import os

load_dotenv()

app = Flask(__name__)
CORS(app)

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

app.run(debug=True, port=5000)