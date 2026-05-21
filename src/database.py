# src/database.py
import requests
from supabase import create_client, Client
from config import SUPABASE_URL, SUPABASE_KEY

# Inizializzazione client Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def get_live_rate() -> float:
    """Recupera il tasso di cambio JPY/EUR live con fallback sicuro."""
    try:
        response = requests.get("https://open.er-api.com/v6/latest/EUR", timeout=5)
        if response.status_code == 200:
            data = response.json()
            # Calcoliamo il tasso inverso EUR -> JPY (es. 165.40)
            return float(data["rates"]["JPY"])
    except Exception:
        pass
    return 165.0  # Fallback se non c'è internet o l'API è giù

def inserisci_operazione(data_pagamento, categoria, sorgente, importo_jpy, importo_eur, destinatario, stato, nota=""):
    """Invia una nuova transazione direttamente su Supabase."""
    payload = {
        "data_pagamento": data_pagamento,
        "categoria": categoria,
        "sorgente": sorgente,
        "importo_jpy": float(importo_jpy),
        "importo_eur": float(importo_eur),
        "destinatario": destinatario,
        "stato": stato,
        "nota": nota
    }
    response = supabase.table("operazioni").insert(payload).execute()
    return response

def recupera_operazioni():
    """Preleva tutte le operazioni ordinate dalla più recente."""
    response = supabase.table("operazioni").select("*").order("data_pagamento", descending=True).execute()
    return response.data

def calcola_metriche(operazioni_list):
    """
    Rielabora la lista delle operazioni estratte da Supabase 
    per calcolare i saldi in tempo reale.
    """
    totale_jpy = 0
    totale_eur = 0
    ricariche_revolut_eur = 0
    spese_carta_revolut_jpy = 0
    prelievi_bancomat_jpy = 0
    spese_contanti_jpy = 0
    
    for op in operazioni_list:
        imp_jpy = float(op["importo_jpy"])
        imp_eur = float(op["importo_eur"])
        cat = op["categoria"]
        sorg = op["sorgente"]
        stato = op["stato"]
        
        # Consideriamo solo le spese effettive per i saldi vivi
        if stato == "Spesa Effettiva":
            # 1. Calcolo totali generali (escludendo le ricariche che sono spostamenti di fondi)
            if cat != "Ricarica Revolut" and cat != "Prelievo Contanti":
                totale_jpy += imp_jpy
                totale_eur += imp_eur
            
            # 2. Logica flussi Revolut
            if cat == "Ricarica Revolut":
                ricariche_revolut_eur += imp_eur
            if sorg == "Carta Credito JPY":
                spese_carta_revolut_jpy += imp_jpy
                
            # 3. Logica flussi Contanti (Wallet)
            if cat == "Prelievo Contanti":
                prelievi_bancomat_jpy += imp_jpy
                # Se hai prelevato da Revolut, la carta ha speso JPY
                if sorg == "Carta Credito JPY":
                    spese_carta_revolut_jpy += imp_jpy
            if sorg == "Wallet Contanti":
                spese_contanti_jpy += imp_jpy

    # Tasso medio teorico o live per la conversione dei saldi
    tasso_corrente = get_live_rate()
    
    # Calcolo Saldo Revolut Residuo (in EUR, poi convertito per visualizzazione)
    # Ricariche in EUR meno (spese totali su carta in JPY / tasso)
    saldo_revolut_eur = ricariche_revolut_eur - (spese_carta_revolut_jpy / tasso_corrente)
    
    # Calcolo Contanti Residui in JPY
    saldo_contanti_jpy = prelievi_bancomat_jpy - spese_contanti_jpy
    
    return {
        "totale_jpy": totale_jpy,
        "totale_eur": totale_eur,
        "saldo_revolut_eur": max(0, saldo_revolut_eur),
        "saldo_contanti_jpy": max(0, saldo_contanti_jpy),
        "tasso_cambio": tasso_corrente
    }
