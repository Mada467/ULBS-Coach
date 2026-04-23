-- ULBS Coach Database Schema v3.0
CREATE DATABASE IF NOT EXISTS ulbs_coach;
USE ulbs_coach;

CREATE TABLE IF NOT EXISTS materii (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id VARCHAR(64) NOT NULL,
    nume VARCHAR(100) NOT NULL,
    profesor VARCHAR(100),
    icon VARCHAR(10) DEFAULT '📚',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS materiale (
    id INT AUTO_INCREMENT PRIMARY KEY,
    materie_id INT NOT NULL,
    student_id VARCHAR(64) NOT NULL,
    nume_fisier VARCHAR(255) NOT NULL,
    text_extras LONGTEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (materie_id) REFERENCES materii(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS statistici (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id VARCHAR(64) NOT NULL,
    materie_id INT,
    materie_nume VARCHAR(100),
    intrebare TEXT NOT NULL,
    nota_ceruta VARCHAR(10),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (materie_id) REFERENCES materii(id) ON DELETE SET NULL
);

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
);

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
);

CREATE TABLE IF NOT EXISTS intrebari_salvate (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id VARCHAR(64) NOT NULL,
    materie VARCHAR(100),
    intrebare TEXT NOT NULL,
    raspuns TEXT,
    dificultate VARCHAR(20) DEFAULT 'mediu',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);