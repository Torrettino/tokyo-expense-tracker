# src/database.py
import requests
from config import SUPABASE_URL, SUPABASE_KEY

# Limite di record per la sicurezza dell'app
RECORD_LIMIT = 300


def _get_headers() -> dict:
    """Genera gli header di autenticazione diretti per l'API di Supabase."""
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
    }


def get_live_rate() -> float:
    """Recupera il tasso di cambio EUR→JPY live."""
    try:
        response = requests.get(
            "https://open.er-api.com/v6/latest/EUR",
            timeout=5,
        )
        response.raise_for_status()
        return float(response.json()["rates"]["JPY"])
    except Exception:
        return 165.0


def inserisci_operazione(
    data_pagamento: str,
    categoria: str,
    sorgente: str,
    importo_jpy: float,
    importo_eur: float,
    destinatario: str,
    stato: str,
    nota: str = "",
):
    """Invia una nuova transazione a Supabase tramite POST HTTP nativo."""
    payload = {
        "data_pagamento": data_pagamento,
        "categoria":      categoria,
        "sorgente":        sorgente,
        "importo_jpy":    float(importo_jpy),
        "importo_eur":    float(importo_eur),
        "destinatario":   destinatario,
        "stato":          stato,
        "nota":           nota,
    }
    try:
        url = f"{SUPABASE_URL}/rest/v1/operazioni"
        response = requests.post(url, headers=_get_headers(), json=payload, timeout=10)
        response.raise_for_status()
        return response
    except Exception as e:
        raise RuntimeError(f"Errore di rete Cloud: {e}")


def recupera_operazioni() -> list[dict]:
    """Preleva le operazioni da Supabase tramite GET HTTP nativo."""
    try:
        # Interroghiamo direttamente l'endpoint REST ordinando e limitando i record
        url = f"{SUPABASE_URL}/rest/v1/operazioni?select=*&order=data_pagamento.desc&limit={RECORD_LIMIT}"
        response = requests.get(url, headers=_get_headers(), timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        raise RuntimeError(f"Impossibile scaricare i dati: {e}")


def calcola_metriche(operazioni_list: list[dict], tasso_corrente: float) -> dict:
    """Rielabora la lista delle operazioni per calcolare i saldi (Invariata)."""
    totale_jpy             = 0.0
    totale_eur             = 0.0
    ricariche_revolut_eur  = 0.0
    spese_carta_revolut_jpy = 0.0
    prelievi_bancomat_jpy  = 0.0
    spese_contanti_jpy     = 0.0

    for op in operazioni_list:
        imp_jpy = float(op.get("importo_jpy", 0))
        imp_eur = float(op.get("importo_eur", 0))
        cat     = op.get("categoria", "")
        sorg    = op.get("sorgente", "")
        stato   = op.get("stato", "")

        if stato != "Spesa Effettiva":
            continue

        if cat not in ("Ricarica Revolut", "Prelievo Contanti"):
            totale_jpy += imp_jpy
            totale_eur += imp_eur

        if cat == "Ricarica Revolut":
            ricariche_revolut_eur += imp_eur
        if sorg == "Carta Credito JPY":
            spese_carta_revolut_jpy += imp_jpy

        if cat == "Prelievo Contanti":
            prelievi_bancomat_jpy += imp_jpy
            if sorg == "Carta Credito JPY":
                spese_carta_revolut_jpy += imp_jpy
        if sorg == "Wallet Contanti":
            spese_contanti_jpy += imp_jpy

    saldo_revolut_eur = ricariche_revolut_eur - (
        spese_carta_revolut_jpy / tasso_corrente if tasso_corrente else 0
    )
    saldo_contanti_jpy = prelievi_bancomat_jpy - spese_contanti_jpy

    return {
        "totale_jpy":         totale_jpy,
        "totale_eur":         totale_eur,
        "saldo_revolut_eur": max(0.0, saldo_revolut_eur),
        "saldo_contanti_jpy": max(0.0, saldo_contanti_jpy),
        "tasso_cambio":      tasso_corrente,
    }
