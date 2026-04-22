import pymysql
import os
from dotenv import load_dotenv

load_dotenv()


def get_connection():
    return pymysql.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        user=os.getenv('DB_USER', 'root'),
        password=os.getenv('DB_PASSWORD', ''),
        database=os.getenv('DB_NAME', 'ulbs_coach'),
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )


def init_db():
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Materii dinamice per student
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS materii (
                id INT AUTO_INCREMENT PRIMARY KEY,
                student_id VARCHAR(64) NOT NULL,
                nume VARCHAR(100) NOT NULL,
                profesor VARCHAR(100),
                icon VARCHAR(10) DEFAULT '📚',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Materiale uploadate per materie
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS materiale (
                id INT AUTO_INCREMENT PRIMARY KEY,
                materie_id INT NOT NULL,
                student_id VARCHAR(64) NOT NULL,
                nume_fisier VARCHAR(255) NOT NULL,
                text_extras LONGTEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (materie_id) REFERENCES materii(id) ON DELETE CASCADE
            )
        """)

        # Statistici per student
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS statistici (
                id INT AUTO_INCREMENT PRIMARY KEY,
                student_id VARCHAR(64) NOT NULL,
                materie_id INT,
                materie_nume VARCHAR(100),
                intrebare TEXT NOT NULL,
                nota_ceruta VARCHAR(10),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (materie_id) REFERENCES materii(id) ON DELETE SET NULL
            )
        """)

        # Sesiuni quiz per student
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS quiz_sesiuni (
                id INT AUTO_INCREMENT PRIMARY KEY,
                student_id VARCHAR(64) NOT NULL,
                materie VARCHAR(100),
                topic VARCHAR(255),
                tip VARCHAR(20) DEFAULT 'teorie',
                numar_intrebari INT DEFAULT 0,
                scor_final DECIMAL(4,2) DEFAULT 0,
                nota_finala DECIMAL(3,1) DEFAULT 0,
                completata TINYINT(1) DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Raspunsuri quiz
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

        # Bookmarks per student
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS intrebari_salvate (
                id INT AUTO_INCREMENT PRIMARY KEY,
                student_id VARCHAR(64) NOT NULL,
                materie VARCHAR(100),
                intrebare TEXT NOT NULL,
                raspuns TEXT,
                dificultate VARCHAR(20) DEFAULT 'mediu',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()
        cursor.close()
        conn.close()
        print("[DB] Schema initializata cu succes!")
        return True

    except Exception as e:
        print(f"[DB] Eroare la initializare schema: {e}")
        return False


# ── MATERII ──────────────────────────────────────────────
def get_materii(student_id):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM materii WHERE student_id = %s ORDER BY created_at DESC",
            (student_id,)
        )
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return rows
    except Exception as e:
        print(f"[DB] Eroare get materii: {e}")
        return []


def adauga_materie(student_id, nume, profesor, icon='📚'):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO materii (student_id, nume, profesor, icon) VALUES (%s, %s, %s, %s)",
            (student_id, nume, profesor, icon)
        )
        materie_id = cursor.lastrowid
        conn.commit()
        cursor.close()
        conn.close()
        return materie_id
    except Exception as e:
        print(f"[DB] Eroare adaugare materie: {e}")
        return None


# ── MATERIALE ─────────────────────────────────────────────
def salveaza_material(materie_id, student_id, nume_fisier, text_extras):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO materiale (materie_id, student_id, nume_fisier, text_extras)
               VALUES (%s, %s, %s, %s)""",
            (materie_id, student_id, nume_fisier, text_extras)
        )
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"[DB] Eroare salvare material: {e}")
        return False


def get_text_materie(materie_id, student_id):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """SELECT text_extras FROM materiale 
               WHERE materie_id = %s AND student_id = %s 
               ORDER BY created_at DESC LIMIT 1""",
            (materie_id, student_id)
        )
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        return row['text_extras'] if row else None
    except Exception as e:
        print(f"[DB] Eroare get text materie: {e}")
        return None


# ── STATISTICI ────────────────────────────────────────────
def salveaza_intrebare(student_id, materie_id, materie_nume, intrebare, nota_ceruta):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO statistici (student_id, materie_id, materie_nume, intrebare, nota_ceruta)
               VALUES (%s, %s, %s, %s, %s)""",
            (student_id, materie_id, materie_nume, intrebare, nota_ceruta)
        )
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"[DB] Eroare salvare intrebare: {e}")
        return False


def get_statistici(student_id, limit=20):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """SELECT intrebare, nota_ceruta, materie_nume, created_at 
               FROM statistici WHERE student_id = %s
               ORDER BY created_at DESC LIMIT %s""",
            (student_id, limit)
        )
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return [
            {
                'intrebare': r['intrebare'],
                'nota': r['nota_ceruta'],
                'materie': r['materie_nume'],
                'data': str(r['created_at'])
            }
            for r in rows
        ]
    except Exception as e:
        print(f"[DB] Eroare get statistici: {e}")
        return []


# ── QUIZ ──────────────────────────────────────────────────
def salveaza_sesiune_quiz(student_id, materie, topic, tip, numar_intrebari, scor_final, nota_finala):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO quiz_sesiuni 
               (student_id, materie, topic, tip, numar_intrebari, scor_final, nota_finala, completata)
               VALUES (%s, %s, %s, %s, %s, %s, %s, 1)""",
            (student_id, materie, topic, tip, numar_intrebari, scor_final, nota_finala)
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
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO quiz_raspunsuri 
               (sesiune_id, intrebare, raspuns_student, raspuns_corect, nota, feedback)
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


def get_istoric_quiz(student_id, limit=10):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """SELECT materie, topic, tip, numar_intrebari, nota_finala, created_at
               FROM quiz_sesiuni WHERE completata = 1 AND student_id = %s
               ORDER BY created_at DESC LIMIT %s""",
            (student_id, limit)
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


# ── BOOKMARKS ─────────────────────────────────────────────
def salveaza_bookmark(student_id, materie, intrebare, raspuns, dificultate):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO intrebari_salvate 
               (student_id, materie, intrebare, raspuns, dificultate)
               VALUES (%s, %s, %s, %s, %s)""",
            (student_id, materie, intrebare, raspuns, dificultate)
        )
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"[DB] Eroare salvare bookmark: {e}")
        return False


def get_bookmarks(student_id, materie=None):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        if materie:
            cursor.execute(
                """SELECT * FROM intrebari_salvate 
                   WHERE student_id = %s AND materie = %s 
                   ORDER BY created_at DESC""",
                (student_id, materie)
            )
        else:
            cursor.execute(
                "SELECT * FROM intrebari_salvate WHERE student_id = %s ORDER BY created_at DESC",
                (student_id,)
            )
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return rows
    except Exception as e:
        print(f"[DB] Eroare get bookmarks: {e}")
        return []