import flet as ft
from datetime import date
import threading
import traceback
import database as db

def main(page: ft.Page):
    # ── 1. FUNZIONE PROFESSIONALE: GESTIONE GLOBALE DEI CRASH ──────────────
    def gestisci_errore_globale(e):
        """Intercetta qualsiasi eccezione non gestita nell'app e la mostra a video."""
        page.controls.clear()
        page.add(
            ft.Container(
                content=ft.Column([
                    ft.Text("⚠️ CRASH DELL'APPLICAZIONE", size=20, color=ft.colors.RED_accent, weight="bold"),
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

    # Stato globale
    stato_app = {"tasso_live": 165.0}

    # ── 3. WIDGETS DELL'INTERFACCIA ────────────────────────────────────────
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

    # ── 4. LOGICA DI BUSINESS ──────────────────────────────────────────────
    def mostra_notifica(messaggio: str, colore=ft.colors.BLUE_200):
        page.snack_bar = ft.SnackBar(ft.Text(messaggio, color=ft.colors.WHITE), bgcolor=colore)
        page.snack_bar.open = True
        page.update()

    def aggiorna_dashboard():
        operazioni = db.recupera_operazioni()
        metriche = db.calcola_metriche(operazioni, stato_app["tasso_live"])

        card_revolut.value  = f"€ {metriche['saldo_revolut_eur']:.2f}"
        card_contanti.value = f"¥ {metriche['saldo_contanti_jpy']:,.0f}"
        card_tot_jpy.value  = f"¥ {metriche['totale_jpy']:,.0f}"
        card_tot_eur.value  = f"€ {metriche['totale_eur']:.2f}"
        testo_cambio.value  = f"Tasso Live: 1 EUR = {stato_app['tasso_live']:.2f} JPY"
        page.update()

    def invia_spesa(e):
        if not importo_input.value or not cat_dropdown.value or not sorg_dropdown.value:
            mostra_notifica("⚠️ Compila tutti i campi obbligatori!", ft.colors.RED_700)
            return

        try:
            imp_val = float(importo_input.value)
        except ValueError:
            mostra_notifica("⚠️ L'importo deve essere un numero valido.", ft.colors.RED_700)
            return

        tasso = stato_app["tasso_live"]
        if sorg_dropdown.value in ("Carta Credito JPY", "Wallet Contanti"):
            imp_jpy, imp_eur = imp_val, imp_val / tasso
        else:
            imp_jpy, imp_eur = imp_val * tasso, imp_val

        db.inserisci_operazione(
            data_pagamento=str(date.today()),
            categoria=cat_dropdown.value,
            sorgente=sorg_dropdown.value,
            importo_jpy=round(imp_jpy, 0),
            importo_eur=round(imp_eur, 4),
            destinatario=dest_dropdown.value,
            stato="Spesa Effettiva",
            nota=nota_input.value or "",
        )

        importo_input.value = ""
        nota_input.value = ""
        cat_dropdown.value = None
        sorg_dropdown.value = None

        mostra_notifica("✅ Spesa registrata con successo!", ft.colors.GREEN_700)
        aggiorna_dashboard()

    def aggiorna_tasso(e):
        nuovo_tasso = db.get_live_rate()
        stato_app["tasso_live"] = nuovo_tasso
        mostra_notifica(f"Tasso aggiornato: ¥{nuovo_tasso:.2f}", ft.colors.GREEN_700)
        aggiorna_dashboard()

    # ── 5. LAYOUT E INIZIALIZZAZIONE ───────────────────────────────────────
    page.add(
        ft.Text("TOKYO TRAVEL WALLET", size=22, weight=ft.FontWeight.BOLD, letter_spacing=1.5),
        ft.Row([testo_cambio, ft.IconButton(icon=ft.icons.REFRESH, on_click=aggiorna_tasso, icon_size=16)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        ft.Divider(),
        ft.Card(content=ft.Container(content=ft.Column([ft.Text("💳 SALDO REVOLUT (STIMATO)", size=12, color=ft.colors.GREY_400), card_revolut]), padding=14)),
        ft.Card(content=ft.Container(content=ft.Column([ft.Text("💴 CONTANTI IN TASCA", size=12, color=ft.colors.GREY_400), card_contanti]), padding=14)),
        ft.Row([ft.Text("Tot. JPY:"), card_tot_jpy, ft.Text("Tot. EUR:"), card_tot_eur], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        ft.Divider(),
        ft.Text("Aggiungi Nuova Spesa", size=16, weight=ft.FontWeight.W_600),
        importo_input, cat_dropdown, sorg_dropdown, dest_dropdown, nota_input,
        ft.Container(height=10),
        ft.ElevatedButton("🚀 REGISTRA SPESA", on_click=invia_spesa, bgcolor=ft.colors.BLUE_700, color=ft.colors.WHITE, width=400, height=50),
    )

    # Caricamento asincrono all'avvio per non bloccare la UI
    def boot_app():
        try:
            stato_app["tasso_live"] = db.get_live_rate()
        except Exception:
            pass # Se fallisce, usiamo il tasso di default a 165
        aggiorna_dashboard()

    threading.Thread(target=boot_app, daemon=True).start()

ft.app(target=main)
