import pymysql
import os
from dotenv import load_dotenv

load_dotenv()


def get_connection():
    """Returneaza o conexiune la baza de date MySQL."""
    return pymysql.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        user=os.getenv('DB_USER', 'root'),
        password=os.getenv('DB_PASSWORD', ''),
        database=os.getenv('DB_NAME', 'ulbs_coach'),
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )


def test_connection():
    """Testeaza conexiunea la baza de date."""
    try:
        conn = get_connection()
        print("[DB] Conexiune MySQL reusita!")
        conn.close()
        return True
    except Exception as e:
        print(f"[DB] Eroare conexiune: {e}")
        return False


def init_db():
    """Initializeaza schema bazei de date cu toate tabelele necesare."""
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Tabel materii
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS materii (
                id INT AUTO_INCREMENT PRIMARY KEY,
                nume VARCHAR(50) NOT NULL UNIQUE,
                descriere TEXT,
                icon VARCHAR(10) DEFAULT '📚',
                activa TINYINT(1) DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Tabel statistici (intrebari puse)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS statistici (
                id INT AUTO_INCREMENT PRIMARY KEY,
                materie_id INT,
                materie_nume VARCHAR(50),
                intrebare TEXT NOT NULL,
                nota_ceruta VARCHAR(10),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (materie_id) REFERENCES materii(id) ON DELETE SET NULL
            )
        """)

        # Tabel sesiuni quiz
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS quiz_sesiuni (
                id INT AUTO_INCREMENT PRIMARY KEY,
                materie VARCHAR(50),
                topic VARCHAR(255),
                tip VARCHAR(20) DEFAULT 'teorie',
                numar_intrebari INT DEFAULT 0,
                scor_final DECIMAL(4,2) DEFAULT 0,
                nota_finala DECIMAL(3,1) DEFAULT 0,
                completata TINYINT(1) DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Tabel raspunsuri quiz (pentru istoric detaliat)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS quiz_raspunsuri (
                id INT AUTO_INCREMENT PRIMARY KEY,
                sesiune_id INT,
                intrebare TEXT,
                raspuns_student TEXT,
                raspuns_corect TEXT,
                nota DECIMAL(3,1),
                feedback TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (sesiune_id) REFERENCES quiz_sesiuni(id) ON DELETE CASCADE
            )
        """)

        # Tabel intrebari salvate (bookmark)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS intrebari_salvate (
                id INT AUTO_INCREMENT PRIMARY KEY,
                materie VARCHAR(50),
                intrebare TEXT NOT NULL,
                raspuns TEXT,
                dificultate VARCHAR(20) DEFAULT 'mediu',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Tabel carti uploadate de studenti
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS carti_uploadate (
                id INT AUTO_INCREMENT PRIMARY KEY,
                materie_nume VARCHAR(100) NOT NULL,
                profesor VARCHAR(100),
                filename VARCHAR(255),
                filepath VARCHAR(500),
                size_chars INT DEFAULT 0,
                activa TINYINT(1) DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Insereaza materiile default daca nu exista
        cursor.execute("""
            INSERT IGNORE INTO materii (nume, descriere, icon) VALUES
            ('POO', 'Programare Orientata pe Obiecte - Breazu Macarie', '💻'),
            ('SO', 'Sisteme de Operare - Breazu Macarie', '🖥️')
        """)

        conn.commit()
        cursor.close()
        conn.close()
        print("[DB] Schema initializata cu succes!")
        return True

    except Exception as e:
        print(f"[DB] Eroare la initializare schema: {e}")
        return False


def salveaza_intrebare(materie_id, materie_nume, intrebare, nota_ceruta):
    """Salveaza o intrebare in statistici."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO statistici (materie_id, materie_nume, intrebare, nota_ceruta) VALUES (%s, %s, %s, %s)",
            (materie_id, materie_nume, intrebare, nota_ceruta)
        )
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"[DB] Eroare salvare intrebare: {e}")
        return False


def get_statistici(limit=20):
    """Returneaza istoricul intrebarilor."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT intrebare, nota_ceruta, materie_nume, created_at FROM statistici ORDER BY created_at DESC LIMIT %s",
            (limit,)
        )
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return [
            {
                'intrebare': r['intrebare'],
                'nota': r['nota_ceruta'],
                'materie': r['materie_nume'] or 'POO',
                'data': str(r['created_at'])
            }
            for r in rows
        ]
    except Exception as e:
        print(f"[DB] Eroare get statistici: {e}")
        return []


def salveaza_sesiune_quiz(materie, topic, tip, numar_intrebari, scor_final, nota_finala):
    """Salveaza o sesiune de quiz completata."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO quiz_sesiuni (materie, topic, tip, numar_intrebari, scor_final, nota_finala, completata)
               VALUES (%s, %s, %s, %s, %s, %s, 1)""",
            (materie, topic, tip, numar_intrebari, scor_final, nota_finala)
        )
        sesiune_id = cursor.lastrowid
        conn.commit()
        cursor.close()
        conn.close()
        return sesiune_id
    except Exception as e:
        print(f"[DB] Eroare salvare sesiune quiz: {e}")
        return None


def salveaza_raspuns_quiz(sesiune_id, intrebare, raspuns_student, raspuns_corect, nota, feedback):
    """Salveaza un raspuns individual din quiz."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO quiz_raspunsuri (sesiune_id, intrebare, raspuns_student, raspuns_corect, nota, feedback)
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (sesiune_id, intrebare, raspuns_student, raspuns_corect, nota, feedback)
        )
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"[DB] Eroare salvare raspuns quiz: {e}")
        return False


def get_istoric_quiz(limit=10):
    """Returneaza istoricul sesiunilor de quiz."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """SELECT materie, topic, tip, numar_intrebari, nota_finala, created_at
               FROM quiz_sesiuni WHERE completata = 1
               ORDER BY created_at DESC LIMIT %s""",
            (limit,)
        )
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return [
            {
                'materie': r['materie'],
                'topic': r['topic'],
                'tip': r['tip'],
                'numar_intrebari': r['numar_intrebari'],
                'nota': float(r['nota_finala']),
                'data': str(r['created_at'])
            }
            for r in rows
        ]
    except Exception as e:
        print(f"[DB] Eroare get istoric quiz: {e}")
        return []


def salveaza_intrebare_bookmark(materie, intrebare, raspuns, dificultate):
    """Salveaza o intrebare in lista de bookmarks."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO intrebari_salvate (materie, intrebare, raspuns, dificultate)
               VALUES (%s, %s, %s, %s)""",
            (materie, intrebare, raspuns, dificultate)
        )
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"[DB] Eroare salvare bookmark: {e}")
        return False


def get_bookmarks(materie=None):
    """Returneaza intrebarile salvate."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        if materie:
            cursor.execute(
                "SELECT * FROM intrebari_salvate WHERE materie = %s ORDER BY created_at DESC",
                (materie,)
            )
        else:
            cursor.execute("SELECT * FROM intrebari_salvate ORDER BY created_at DESC")
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return rows
    except Exception as e:
        print(f"[DB] Eroare get bookmarks: {e}")
        return []


def salveaza_carte_uploadata(materie_nume, profesor, filename, filepath, size_chars):
    """Salveaza informatii despre o carte uploadata."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO carti_uploadate (materie_nume, profesor, filename, filepath, size_chars)
               VALUES (%s, %s, %s, %s, %s)""",
            (materie_nume, profesor, filename, filepath, size_chars)
        )
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"[DB] Eroare salvare carte: {e}")
        return False


def get_carti_uploadate():
    """Returneaza lista cartilor uploadate."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM carti_uploadate WHERE activa = 1 ORDER BY created_at DESC")
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return rows
    except Exception as e:
        print(f"[DB] Eroare get carti: {e}")
        return []