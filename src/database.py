import requests
import json
from config import SUPABASE_URL, SUPABASE_KEY

RECORD_LIMIT = 300

def _get_headers() -> dict:
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
    }

def get_live_rate() -> float:
    try:
        response = requests.get("https://open.er-api.com/v6/latest/EUR", timeout=5)
        if response.status_code == 200:
            data = response.json()
            return float(data["rates"]["JPY"])
        return 165.0
    except Exception:
        return 165.0  # Tasso di fallback sicuro in caso di assenza di rete

def inserisci_operazione(data_pagamento, categoria, sorgente, importo_jpy, importo_eur, destinatario, stato, nota):
    payload = {
        "data_pagamento": data_pagamento,
        "categoria": categoria,
        "sorgente": sorgente,
        "importo_jpy": float(importo_jpy),
        "importo_eur": float(importo_eur),
        "destinatario": destinatario,
        "stato": stato,
        "nota": nota,
    }
    url = f"{SUPABASE_URL}/rest/v1/operazioni"
    
    response = requests.post(url, headers=_get_headers(), json=payload, timeout=10)
    return response.text

def recupera_operazioni() -> list[dict]:
    url = f"{SUPABASE_URL}/rest/v1/operazioni?select=*&order=data_pagamento.desc&limit={RECORD_LIMIT}"
    
    response = requests.get(url, headers=_get_headers(), timeout=10)
    if response.status_code == 200:
        return response.json()
    return []

def calcola_metriche(operazioni_list: list[dict], tasso_corrente: float) -> dict:
    totale_jpy = totale_eur = ricariche_revolut_eur = spese_carta_revolut_jpy = prelievi_bancomat_jpy = spese_contanti_jpy = 0.0

    for op in operazioni_list:
        imp_jpy = float(op.get("importo_jpy", 0))
        imp_eur = float(op.get("importo_eur", 0))
        cat = op.get("categoria", "")
        sorg = op.get("sorgente", "")
        stato = op.get("stato", "")

        if stato != "Spesa Effettiva":
            continue

        if cat not in ("Ricarica Revolut", "Prelievo Contanti"):
            totale_jpy += imp_jpy
            totale_eur += imp_eur

        if cat == "Ricarica Revolut":
            ricariche_revolut_eur += imp_eur
        elif sorg == "Carta Credito JPY":
            spese_carta_revolut_jpy += imp_jpy

        if cat == "Prelievo Contanti":
            prelievi_bancomat_jpy += imp_jpy
            if sorg == "Carta Credito JPY":
                spese_carta_revolut_jpy += imp_jpy
        elif sorg == "Wallet Contanti":
            spese_contanti_jpy += imp_jpy

    saldo_revolut_eur = ricariche_revolut_eur - (spese_carta_revolut_jpy / tasso_corrente if tasso_corrente else 0)
    saldo_contanti_jpy = prelievi_bancomat_jpy - spese_contanti_jpy

    return {
        "totale_jpy": totale_jpy,
        "totale_eur": totale_eur,
        "saldo_revolut_eur": max(0.0, saldo_revolut_eur),
        "saldo_contanti_jpy": max(0.0, saldo_contanti_jpy),
    }
    
