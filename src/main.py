import flet as ft
from datetime import date
import threading
import traceback

# ❌ NESSUN IMPORT DEL DATABASE QUI IN CIMA! ❌
# Questo salva l'app dal crash istantaneo (schermo nero) all'avvio.

def main(page: ft.Page):
    # ── 1. FUNZIONE PROFESSIONALE: GESTIONE GLOBALE DEI CRASH ──────────────
    def gestisci_errore_globale(e):
        """Intercetta qualsiasi eccezione non gestita nell'app e la mostra a video."""
        page.controls.clear()
        page.add(
            ft.Container(
                content=ft.Column([
                    ft.Text("⚠️ CRASH DELL'APPLICAZIONE", size=20, color=ft.colors.RED_ACCENT, weight="bold"),
                    ft.Text("Dettagli dell'errore (fai uno screenshot):", size=14, color=ft.colors.GREY_300),
                    ft.Container(
                        content=ft.Text(str(e.data), size=12, font_family="monospace", selectable=True),
                        bgcolor=ft.colors.SURFACE_VARIANT,
                        padding=10,
                        border_radius=8
                    )
                ]),
                padding=20
            )
        )
        page.update()

    # Agganciamo il gestore errori nativo alla pagina Flet
    page.on_error = gestisci_errore_globale

    # ── 2. CONFIGURAZIONE PAGINA ───────────────────────────────────────────
    page.title = "Tokyo Travel Wallet"
    page.theme_mode = ft.ThemeMode.DARK
    page.scroll = "adaptive"
    page.padding = 16

    # ── 3. IMPORT SICURO DEL DATABASE ──────────────────────────────────────
    try:
        import database as db
    except Exception as ex:
        # Se c'è un errore in database.py o config.py, ora lo vediamo a schermo!
        page.add(
            ft.Text("⚠️ ERRORE CRITICO DI AVVIO DATABASE", color=ft.colors.RED_ACCENT, size=18, weight="bold"),
            ft.Text(traceback.format_exc(), selectable=True, font_family="monospace", size=12)
        )
        page.update()
        return

    # Stato globale
    stato_app = {"tasso_live": 165.0}

    # ── 4. WIDGETS DELL'INTERFACCIA ────────────────────────────────────────
    card_revolut  = ft.Text("€ 0.00", size=24, weight=ft.FontWeight.BOLD, color=ft.colors.BLUE_200)
    card_contanti = ft.Text("¥ 0",    size=24, weight=ft.FontWeight.BOLD, color=ft.colors.GREEN_200)
    card_tot_jpy  = ft.Text("¥ 0",    size=18, weight=ft.FontWeight.BOLD)
    card_tot_eur  = ft.Text("€ 0.00", size=18, weight=ft.FontWeight.BOLD)
    testo_cambio  = ft.Text("Sincronizzazione cloud...", size=12, italic=True, color=ft.colors.BLUE_200)

    importo_input = ft.TextField(label="Importo", keyboard_type=ft.KeyboardType.NUMBER, border_color=ft.colors.BLUE_400)
    cat_dropdown = ft.Dropdown(
        label="Categoria",
        options=[
            ft.dropdown.Option("Cibo"), ft.dropdown.Option("Trasporti"),
            ft.dropdown.Option("Alloggio"), ft.dropdown.Option("Shopping"),
            ft.dropdown.Option("Ricarica Revolut"), ft.dropdown.Option("Prelievo Contanti"),
        ],
    )
    sorg_dropdown = ft.Dropdown(
        label="Sorgente Fondi",
        options=[
            ft.dropdown.Option("Carta Credito JPY"), 
            ft.dropdown.Option("Wallet Contanti"), 
            ft.dropdown.Option("Conto EUR")
        ],
    )
    dest_dropdown = ft.Dropdown(
        label="Destinatario",
        value="Personale",
        options=[
            ft.dropdown.Option("Personale"), ft.dropdown.Option("Famiglia"), 
            ft.dropdown.Option("Francesco"), ft.dropdown.Option("Guia"), 
            ft.dropdown.Option("Matilde")
        ],
    )
    nota_input = ft.TextField(label="Nota (Opzionale)")

    # ── 5. LOGICA DI BUSINESS ──────────────────────────────────────────────
    def mostra_notifica(messaggio: str, colore=ft.colors.BLUE_200):
        page.snack_bar = ft.SnackBar(ft.Text(messaggio, color=ft.colors.WHITE), bgcolor=colore)
        page.snack_bar.open = True
        page.update()

    def aggiorna_dashboard():
        try:
            operazioni = db.recupera_operazioni()
            metriche = db.calcola_metriche(operazioni, stato_app["tasso_live"])

            card_revolut.value  = f"€ {metriche['saldo_revolut_eur']:.2f}"
            card_contanti.value = f"¥ {metriche['saldo_contanti_jpy']:,.0f}"
            card_tot_jpy.value  = f"¥ {metriche['totale_jpy']:,.0f}"
            card_tot_eur.value  = f"€ {metriche['totale_eur']:.2f}"
            testo_cambio.value  = f"Tasso Live: 1 EUR = {
            
