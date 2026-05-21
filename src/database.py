
# src/database.py
import requests
from supabase import create_client, Client
from config import SUPABASE_URL, SUPABASE_KEY
 
# ── Client Supabase (singleton) ───────────────────────────────────────────────
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
 
# ── Limite record per query (evita query illimitate con molti dati) ───────────
RECORD_LIMIT = 300
 
 
def get_live_rate() -> float:
    """
    Recupera il tasso di cambio EUR→JPY live da open.er-api.com.
    Fallback a 165.0 in caso di errore o timeout.
    """
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
    """
    Invia una nuova transazione su Supabase.
    Solleva RuntimeError con messaggio leggibile in caso di fallimento.
    """
    payload = {
        "data_pagamento": data_pagamento,
        "categoria":      categoria,
        "sorgente":       sorgente,
        "importo_jpy":    float(importo_jpy),
        "importo_eur":    float(importo_eur),
        "destinatario":   destinatario,
        "stato":          stato,
        "nota":           nota,
    }
    try:
        response = supabase.table("operazioni").insert(payload).execute()
        return response
    except Exception as e:
        raise RuntimeError(f"Impossibile salvare su Supabase: {e}")
 
 
def recupera_operazioni() -> list[dict]:
    """
    Preleva le operazioni più recenti ordinate per data.
    FIX: aggiunto .limit(RECORD_LIMIT) per evitare query illimitate.
    """
    try:
        response = (
            supabase
            .table("operazioni")
            .select("*")
            .order("data_pagamento", descending=True)
            .limit(RECORD_LIMIT)
            .execute()
        )
        return response.data
    except Exception as e:
        raise RuntimeError(f"Impossibile recuperare i dati: {e}")
 
 
def calcola_metriche(operazioni_list: list[dict], tasso_corrente: float) -> dict:
    """
    Rielabora la lista delle operazioni per calcolare i saldi in tempo reale.
 
    FIX: accetta il tasso come parametro invece di chiamare get_live_rate()
    internamente, eliminando la doppia chiamata HTTP per ogni operazione.
 
    Args:
        operazioni_list:  lista di dict restituita da recupera_operazioni()
        tasso_corrente:   tasso EUR→JPY già recuperato dal chiamante
    """
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
 
        # Totali generali (escluse poste di giro fondi)
        if cat not in ("Ricarica Revolut", "Prelievo Contanti"):
            totale_jpy += imp_jpy
            totale_eur += imp_eur
 
        # Flussi Revolut
        if cat == "Ricarica Revolut":
            ricariche_revolut_eur += imp_eur
        if sorg == "Carta Credito JPY":
            spese_carta_revolut_jpy += imp_jpy
 
        # Flussi Contanti
        if cat == "Prelievo Contanti":
            prelievi_bancomat_jpy += imp_jpy
            if sorg == "Carta Credito JPY":
                spese_carta_revolut_jpy += imp_jpy
        if sorg == "Wallet Contanti":
            spese_contanti_jpy += imp_jpy
 
    # Saldo Revolut stimato in EUR
    saldo_revolut_eur = ricariche_revolut_eur - (
        spese_carta_revolut_jpy / tasso_corrente if tasso_corrente else 0
    )
 
    # Saldo contanti residui in JPY
    saldo_contanti_jpy = prelievi_bancomat_jpy - spese_contanti_jpy
 
    return {
        "totale_jpy":        totale_jpy,
        "totale_eur":        totale_eur,
        "saldo_revolut_eur": max(0.0, saldo_revolut_eur),
        "saldo_contanti_jpy": max(0.0, saldo_contanti_jpy),
        "tasso_cambio":      tasso_corrente,
    }
