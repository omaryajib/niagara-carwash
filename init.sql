-- Table für Waschgänge
CREATE TABLE IF NOT EXISTS washes (
    id SERIAL PRIMARY KEY,
    filiale VARCHAR(100) NOT NULL,
    wash_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabelle für tägliche Umsätze
CREATE TABLE IF NOT EXISTS daily_sales (
    id SERIAL PRIMARY KEY,
    filiale VARCHAR(100) NOT NULL,
    sale_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    normal_umsatz NUMERIC DEFAULT 0,
    subscription_card NUMERIC DEFAULT 0,
    subscription_lastschrift NUMERIC DEFAULT 0,
    water_cost NUMERIC DEFAULT 0,
    energy_cost NUMERIC DEFAULT 0,
    product_cost NUMERIC DEFAULT 0
);

-- Tabelle für Benutzer
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    password TEXT NOT NULL
);
