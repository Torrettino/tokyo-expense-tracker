# src/main.py
import flet as ft
from datetime import date
import database as db
import threading


def main(page: ft.Page):
    # ── Configurazione pagina ─────────────────────────────────────────────────
    page.title = "Tokyo Travel Wallet"
    page.theme_mode = ft.ThemeMode.DARK
    page.scroll = "adaptive"
    page.padding = 16

    # ── Tasso cambio in memoria (evita doppia chiamata API) ───────────────────
    tasso_live: dict = {"valore": 165.0}

    # ── Utility: mostra snackbar ──────────────────────────────────────────────
    def snack(messaggio: str):
        page.snack_bar = ft.SnackBar(ft.Text(messaggio))
        page.snack_bar.open = True
        page.update()

    # ── Aggiornamento dashboard ───────────────────────────────────────────────
    def aggiorna_dashboard():
        try:
            operazioni = db.recupera_operazioni()
            metriche = db.calcola_metriche(operazioni, tasso_live["valore"])

            card_revolut.value  = f"€ {metriche['saldo_revolut_eur']:.2f}"
            card_contanti.value = f"¥ {metriche['saldo_contanti_jpy']:,.0f}"
            card_tot_jpy.value  = f"¥ {metriche['totale_jpy']:,.0f}"
            card_tot_eur.value  = f"€ {metriche['totale_eur']:.2f}"
            testo_cambio.value  = f"Tasso Live: 1 EUR = {tasso_live['valore']:.2f} JPY"
        except Exception as ex:
            snack(f"Errore sincronizzazione: {ex}")
        page.update()

    # ── Invio spesa ───────────────────────────────────────────────────────────
    def invia_spesa(e):
        if not importo_input.value or not cat_dropdown.value or not sorg_dropdown.value:
            snack("⚠️ Compila tutti i campi obbligatori!")
            return

        try:
            imp_val = float(importo_input.value)
        except ValueError:
            snack("⚠️ Importo non valido — inserisci un numero.")
            return

        if imp_val <= 0:
            snack("⚠️ L'importo deve essere maggiore di zero.")
            return

        tasso = tasso_live["valore"]

        if sorg_dropdown.value in ("Carta Credito JPY", "Wallet Contanti"):
            imp_jpy = imp_val
            imp_eur = imp_val / tasso
        else:
            imp_eur = imp_val
            imp_jpy = imp_val * tasso

        try:
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
        except RuntimeError as ex:
            snack(f"❌ {ex}")
            return

        importo_input.value  = ""
        nota_input.value     = ""
        cat_dropdown.value   = None
        sorg_dropdown.value  = None

        snack("✅ Spesa registrata nel Cloud!")
        aggiorna_dashboard()

    # ── Aggiornamento tasso live on-demand ────────────────────────────────────
    def aggiorna_tasso(e):
        try:
            nuovo = db.get_live_rate()
            tasso_live["valore"] = nuovo
            testo_cambio.value = f"Tasso Live: 1 EUR = {nuovo:.2f} JPY"
            snack(f"Tasso aggiornato: ¥{nuovo:.2f}")
        except Exception as ex:
            snack(f"Errore recupero tasso: {ex}")
        page.update()

    # ── Widgets ───────────────────────────────────────────────────────────────
    card_revolut  = ft.Text("€ 0.00", size=24, weight=ft.FontWeight.BOLD, color=ft.colors.BLUE_200)
    card_contanti = ft.Text("¥ 0",    size=24, weight=ft.FontWeight.BOLD, color=ft.colors.GREEN_200)
    card_tot_jpy  = ft.Text("¥ 0",    size=18, weight=ft.FontWeight.BOLD)
    card_tot_eur  = ft.Text("€ 0.00", size=18, weight=ft.FontWeight.BOLD)
    testo_cambio  = ft.Text("Sincronizzazione cloud...", size=12, italic=True, color=ft.colors.BLUE_200)

    importo_input = ft.TextField(
        label="Importo",
        keyboard_type=ft.KeyboardType.NUMBER,
        border_color=ft.colors.BLUE_400,
    )
    cat_dropdown = ft.Dropdown(
        label="Categoria",
        options=[
            ft.dropdown.Option("Cibo"),
            ft.dropdown.Option("Trasporti"),
            ft.dropdown.Option("Alloggio"),
            ft.dropdown.Option("Shopping"),
            ft.dropdown.Option("Ricarica Revolut"),
            ft.dropdown.Option("Prelievo Contanti"),
        ],
    )
    sorg_dropdown = ft.Dropdown(
        label="Sorgente Fondi",
        options=[
            ft.dropdown.Option("Carta Credito JPY"),
            ft.dropdown.Option("Wallet Contanti"),
            ft.dropdown.Option("Conto EUR"),
        ],
    )
    dest_dropdown = ft.Dropdown(
        label="Destinatario",
        value="Personale",
        options=[
            ft.dropdown.Option("Personale"),
            ft.dropdown.Option("Famiglia"),
            ft.dropdown.Option("Francesco"),
            ft.dropdown.Option("Guia"),
            ft.dropdown.Option("Matilde"),
        ],
    )
    nota_input = ft.TextField(label="Nota (Opzionale)")

    # ── Layout ────────────────────────────────────────────────────────────────
    page.add(
        ft.Text("TOKYO TRAVEL WALLET", size=22, weight=ft.FontWeight.BOLD, letter_spacing=1.5),
        ft.Row(
            [
                testo_cambio,
                ft.IconButton(
                    icon=ft.icons.REFRESH,
                    tooltip="Aggiorna tasso live",
                    on_click=aggiorna_tasso,
                    icon_size=16,
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        ),
        ft.Divider(),

        # Saldi
        ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.Text("💳 SALDO REVOLUT (STIMATO)", size=12, color=ft.colors.GREY_400),
                    card_revolut,
                ]),
                padding=14,
            )
        ),
        ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.Text("💴 CONTANTI IN TASCA", size=12, color=ft.colors.GREY_400),
                    card_contanti,
                ]),
                padding=14,
            )
        ),

        # Totali
        ft.Row(
            [
                ft.Text("Tot. JPY:"), card_tot_jpy,
                ft.Text("Tot. EUR:"), card_tot_eur,
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        ),

        ft.Divider(),
        ft.Text("Aggiungi Nuova Spesa", size=16, weight=ft.FontWeight.W_600),
        importo_input,
        cat_dropdown,
        sorg_dropdown,
        dest_dropdown,
        nota_input,
        ft.VerticalDivider(height=10),
        ft.ElevatedButton(
            text="🚀 REGISTRA SPESA",
            style=ft.ButtonStyle(bgcolor=ft.colors.BLUE_700, color=ft.colors.WHITE),
            on_click=invia_spesa,
            width=400,
            height=50,
        ),
    )

    # ── Caricamento asincrono sicuro in background ───────────────────────────
    def carica_dati_silenziosamente():
        try:
            tasso_real = db.get_live_rate()
            tasso_live["valore"] = tasso_real
            testo_cambio.value = f"Tasso Live: 1 EUR = {tasso_real:.2f} JPY"
        except Exception:
            testo_cambio.value = f"Tasso Offline (Default): 1 EUR = {tasso_live['valore']:.2f} JPY"
        aggiorna_dashboard()

    # Lanciamo il thread: l'interfaccia si apre all'istante, i dati appaiono dopo un secondo
    threading.Thread(target=carica_dati_silenziosamente, daemon=True).start()


ft.app(target=main)

    # ── Widgets ───────────────────────────────────────────────────────────────
    card_revolut  = ft.Text("€ 0.00", size=24, weight=ft.FontWeight.BOLD, color=ft.colors.BLUE_200)
    card_contanti = ft.Text("¥ 0",    size=24, weight=ft.FontWeight.BOLD, color=ft.colors.GREEN_200)
    card_tot_jpy  = ft.Text("¥ 0",    size=18, weight=ft.FontWeight.BOLD)
    card_tot_eur  = ft.Text("€ 0.00", size=18, weight=ft.FontWeight.BOLD)
    testo_cambio  = ft.Text("Sincronizzazione in corso...", size=12, italic=True, color=ft.colors.BLUE_200)

    importo_input = ft.TextField(
        label="Importo",
        keyboard_type=ft.KeyboardType.NUMBER,
        border_color=ft.colors.BLUE_400,
    )
    cat_dropdown = ft.Dropdown(
        label="Categoria",
        options=[
            ft.dropdown.Option("Cibo"),
            ft.dropdown.Option("Trasporti"),
            ft.dropdown.Option("Alloggio"),
            ft.dropdown.Option("Shopping"),
            ft.dropdown.Option("Ricarica Revolut"),
            ft.dropdown.Option("Prelievo Contanti"),
        ],
    )
    sorg_dropdown = ft.Dropdown(
        label="Sorgente Fondi",
        options=[
            ft.dropdown.Option("Carta Credito JPY"),
            ft.dropdown.Option("Wallet Contanti"),
            ft.dropdown.Option("Conto EUR"),
        ],
    )
    dest_dropdown = ft.Dropdown(
        label="Destinatario",
        value="Personale",
        options=[
            ft.dropdown.Option("Personale"),
            ft.dropdown.Option("Famiglia"),
            ft.dropdown.Option("Francesco"),
            ft.dropdown.Option("Guia"),
            ft.dropdown.Option("Matilde"),
        ],
    )
    nota_input = ft.TextField(label="Nota (Opzionale)")

    # ── Layout ────────────────────────────────────────────────────────────────
    page.add(
        ft.Text("TOKYO TRAVEL WALLET", size=22, weight=ft.FontWeight.BOLD, letter_spacing=1.5),
        ft.Row(
            [
                testo_cambio,
                ft.IconButton(
                    icon=ft.icons.REFRESH,
                    tooltip="Aggiorna tasso live",
                    on_click=aggiorna_tasso,
                    icon_size=16,
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        ),
        ft.Divider(),

        # Saldi
        ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.Text("💳 SALDO REVOLUT (STIMATO)", size=12, color=ft.colors.GREY_400),
                    card_revolut,
                ]),
                padding=14,
            )
        ),
        ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.Text("💴 CONTANTI IN TASCA", size=12, color=ft.colors.GREY_400),
                    card_contanti,
                ]),
                padding=14,
            )
        ),

        # Totali
        ft.Row(
            [
                ft.Text("Tot. JPY:"), card_tot_jpy,
                ft.Text("Tot. EUR:"), card_tot_eur,
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        ),

        ft.Divider(),
        ft.Text("Aggiungi Nuova Spesa", size=16, weight=ft.FontWeight.W_600),
        importo_input,
        cat_dropdown,
        sorg_dropdown,
        dest_dropdown,
        nota_input,
        ft.VerticalDivider(height=10),
        ft.ElevatedButton(
            text="🚀 REGISTRA SPESA",
            style=ft.ButtonStyle(bgcolor=ft.colors.BLUE_700, color=ft.colors.WHITE),
            on_click=invia_spesa,
            width=400,
            height=50,
        ),
    )


ft.app(target=main)
