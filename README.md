# ULBS Coach - Asistent AI pentru Studenti

Un asistent AI care raspunde la intrebari din cartile profesorilor,
personalizat pe nivelul de nota dorit.

## Tehnologii folosite
- Python + Flask (backend)
- MySQL (baza de date)
- Google Gemini AI (inteligenta artificiala)
- HTML + CSS + JavaScript (frontend)
- OCR cu Tesseract (procesare PDF)

## Cum rulezi proiectul

### 1. Cloneaza repository-ul
git clone https://github.com/Mada467/ULBS-Coach.git
cd ULBS-Coach
### 2. Instaleaza pachetele Python
cd backend
pip install -r requirements.txt
### 3. Configureaza .env
Creaza fisierul `backend/.env` cu:
GEMINI_API_KEY=cheia_ta_gemini
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=parola_ta
DB_NAME=ulbs_coach
### 4. Initializeaza baza de date
Ruleaza fisierul `database/ulbs_coach.sql` in MySQL Workbench.

### 5. Proceseaza cartea PDF
cd backend
py -3.12 -c "from pdf_processor import extract_text_from_pdf, save_text_to_file; text = extract_text_from_pdf('Macarie Breazu - Programare Orientata pe Obiecte. Principii.pdf'); save_text_to_file(text, 'carte_poo.txt')"
### 6. Porneste serverul
py -3.12 app.py
### 7. Deschide interfata
Deschide `frontend/ULBS-Coach.html` in browser.

## Functionalitati
- Raspunsuri AI din cartea profesorului
- 3 niveluri de raspuns: 5-6, 7-8, 9-10
- Statistici activitate student
- Istoric intrebari
- Intrebari rapide predefinite

## Structura proiect
ULBS-Coach/
├── backend/
│   ├── app.py
│   ├── ai_service.py
│   ├── database.py
│   ├── pdf_processor.py
│   ├── setup_db.py
│   └── requirements.txt
├── database/
│   └── ulbs_coach.sql
└── frontend/
├── ULBS-Coach.html
├── ULBS-Coach.css
└── ULBS-Coach.js
## Materii disponibile
- Programare Orientata pe Obiecte (Breazu Macarie) ✅
- Mai multe materii in curand...