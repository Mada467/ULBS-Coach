-- ULBS Coach Database
-- Creat pentru proiectul AI-First Hackathon

CREATE DATABASE IF NOT EXISTS ulbs_coach;

USE ulbs_coach;

CREATE TABLE IF NOT EXISTS materii (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nume VARCHAR(255) NOT NULL,
    descriere TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS intrebari (
    id INT AUTO_INCREMENT PRIMARY KEY,
    materie_id INT,
    intrebare TEXT NOT NULL,
    raspuns_5_6 TEXT,
    raspuns_7_8 TEXT,
    raspuns_9_10 TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (materie_id) REFERENCES materii(id)
);

CREATE TABLE IF NOT EXISTS statistici (
    id INT AUTO_INCREMENT PRIMARY KEY,
    materie_id INT,
    intrebare TEXT NOT NULL,
    nota_ceruta VARCHAR(10),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (materie_id) REFERENCES materii(id)
);

-- Date initiale
INSERT INTO materii (nume, descriere) 
VALUES ('POO', 'Programare Orientata pe Obiecte - Breazu Macarie')
ON DUPLICATE KEY UPDATE nume=nume;