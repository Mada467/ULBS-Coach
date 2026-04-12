# ULBS Coach - Asistent AI pentru Studenti

Un asistent AI care raspunde la intrebari din cartile profesorilor,
personalizat pe nivelul de nota dorit.

## Tehnologii folosite
- Python + Flask (backend)
- MySQL (baza de date)
- Google Gemini AI (inteligenta artificiala)
- HTML + CSS + JavaScript (frontend)
- OCR cu Tesseract (procesare PDF)
- Docker (deploy reproducibil)
- n8n (automatizari)

## Functionalitati
- Raspunsuri AI din cartea profesorului
- 3 niveluri de raspuns: 5-6, 7-8, 9-10
- Cartonase de studiu generate de AI
- Mode Quiz cu evaluare automata
- Etica intrebari — filtrare intrebari nepotrivite
- Statistici activitate student
- Istoric intrebari
- Raport zilnic automat prin n8n

## Arhitectura sistemului
Frontend (HTML/CSS/JS)
↓ HTTP
Backend Flask (Python) — port 5000
├── ai_service.py     → Gemini AI (raspunsuri)
├── cartonase.py      → Gemini AI (flashcards)
├── pdf_processor.py  → OCR Tesseract (carte PDF)
└── database.py       → MySQL (statistici)
n8n   → Raport zilnic automat
Docker → Deploy reproducibil

## Cum rulezi proiectul

### Varianta 1 — Local (recomandat pentru dezvoltare)

#### 1. Cloneaza repository-ul

git clone https://github.com/Mada467/ULBS-Coach.git
cd ULBS-Coach

#### 2. Instaleaza Tesseract OCR
Descarca de la: https://github.com/UB-Mannheim/tesseract/wiki
Instaleaza cu limba romana si engleza.

#### 3. Instaleaza pachetele Python
cd backend
pip install -r requirements.txt

#### 4. Configureaza .env
Creaza fisierul `backend/.env` cu:
GEMINI_API_KEY=cheia_ta_gemini
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=parola_ta
DB_NAME=ulbs_coach

#### 5. Initializeaza baza de date
Ruleaza fisierul `database/ulbs_coach.sql` in MySQL Workbench.

#### 6. Adauga cartea PDF
Pune fisierul PDF in folderul `backend/` si proceseaza-l:

cd backend
py -3.12 -c "from pdf_processor import extract_text_from_pdf, save_text_to_file; text = extract_text_from_pdf('Macarie Breazu - Programare Orientata pe Obiecte. Principii.pdf'); save_text_to_file(text, 'carte_poo.txt')"

#### 7. Porneste serverul
py -3.12 app.py

Sau dublu click pe `Porneste-ULBS-Coach.bat`

#### 8. Deschide interfata
Deschide `frontend/ULBS-Coach.html` in browser.

---

### Varianta 2 — Docker

#### 1. Configureaza .env
Creaza fisierul `.env` in folderul principal cu:

GEMINI_API_KEY=cheia_ta_gemini
DB_PASSWORD=parola_ta_mysql

#### 2. Porneste cu Docker

---

## Structura proiect
ULBS-Coach/
├── backend/
│   ├── app.py              # Serverul Flask
│   ├── ai_service.py       # Integrare Gemini AI
│   ├── cartonase.py        # Generare flashcards
│   ├── pdf_processor.py    # OCR carte PDF
│   ├── database.py         # Conexiune MySQL
│   ├── setup_db.py         # Initializare DB
│   └── requirements.txt    # Pachete Python
├── database/
│   └── ulbs_coach.sql      # Schema baza de date
├── frontend/
│   ├── ULBS-Coach.html     # Interfata web
│   ├── ULBS-Coach.css      # Stilizare
│   └── ULBS-Coach.js       # Logica frontend
├── Dockerfile              # Container backend
├── docker-compose.yml      # Orchestrare servicii
├── Porneste-ULBS-Coach.bat # Pornire rapida Windows
├── n8n-raport-zilnic.json  # Workflow n8n
└── README.md

## API Endpoints

| Endpoint | Metoda | Descriere |
|----------|--------|-----------|
| `/` | GET | Status API |
| `/api/intreaba` | POST | Intreaba AI |
| `/api/statistici` | GET | Statistici student |
| `/api/cartonase` | POST | Genereaza flashcards |
| `/api/quiz/evalueaza` | POST | Evalueaza raspuns quiz |

## Materii disponibile
- Programare Orientata pe Obiecte — Breazu Macarie ✅
- Mai multe materii in curand...

## Autor
Proiect realizat pentru laboratorul AI-First — ULBS Sibiu 2026

