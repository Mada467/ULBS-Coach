from database import get_connection

conn = get_connection()
cursor = conn.cursor()

cursor.execute("""
    INSERT INTO materii (nume, descriere) 
    VALUES ('POO', 'Programare Orientata pe Obiecte - Breazu Macarie')
""")

conn.commit()
print('Materie adaugata cu succes!')
cursor.close()
conn.close()