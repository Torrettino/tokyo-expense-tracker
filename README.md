# ✈️ Tokyo Travel Wallet 🇯🇵

Applicazione mobile-first sviluppata in **Python** con il framework **Flet**, progettata per la gestione e il tracciamento del budget in tempo reale durante il viaggio in Giappone (Giugno 2026).

L'applicazione si collega a un database cloud **Supabase (PostgreSQL)** per garantire la persistenza dei dati e la sincronizzazione immediata tra i dispositivi.

## 🚀 Funzionalità Principali

*   **Mobile-First Design:** Interfaccia verticale ottimizzata per l'uso da smartphone, con tastierini numerici automatici e pulsanti rapidi.
*   **Tasso di Cambio Live:** Recupero automatico del tasso di cambio reale JPY/EUR tramite API ad ogni avvio.
*   **Gestione Doppia Sorgente:** Calcolo automatico e separato del saldo residuo sulla carta **Revolut** (in EUR) e dei **Contanti in tasca** (in JPY).
*   **Ripartizione per Destinatario:** Monitoraggio delle spese suddivise tra budget personale, di coppia o familiare.

## 🛠️ Stack Tecnologico

*   **Frontend/App Framework:** Flet (Flutter per Python)
*   **Backend & Database:** Supabase (PostgreSQL)
*   **Data Fetching:** Requests (per tassi di cambio live)

## 📁 Struttura del Progetto

```text
tokyo-expense-tracker/
│
├── requirements.txt     # Dipendenze del progetto
├── .gitignore           # Esclusione file sensibili (config.py)
└── src/
    ├── main.py          # Interfaccia grafica dell'applicazione
    ├── database.py      # Logica delle query e calcolo metriche
    └── config.py        # Chiavi API Supabase (Locale/Privato)
