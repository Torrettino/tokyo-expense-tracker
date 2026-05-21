import flet as ft
from datetime import date
import threading
import traceback

# L'import di database avviene solo dentro il main per proteggere la stabilità del boot.

def main(page: ft.Page):
    # ── 1. GESTIONE GLOBALE DEI CRASH ──────────────────────────────────────
    def gestisci_errore_globale(e):
        page.controls.clear()
        page.add(
            ft.Container(
                content=ft.Column([
                    ft.Text("⚠️ CRASH DELL'APPLICAZIONE", size=20, color="redaccent", weight="bold"),
                    ft.Text("Dettagli dell'errore (fai uno screenshot):", size=14, color="grey300"),
                    ft.Container(
                        content=ft.Text(str(e.data), size=12, font_family="monospace", selectable=True),
                        bgcolor="surfacevariant",
                        padding=10,
                        border_radius=8
                    )
                ]),
                padding=20
            )
        )
        page.update()

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
        page.add(
            ft.Text("⚠️ ERRORE CRITICO DI AVVIO DATABASE", color="redaccent", size=18, weight="bold"),
            ft.Text(traceback.format_exc(), selectable=True, font_family="monospace", size=12)
        )
        page.update()
        return

    # Stato globale
    stato_app = {"tasso_live": 165.0}

    # ── 4. WIDGETS DELL'INTERFACCIA (CON COLORI IN STRINGA COMPATIBILI) ────
    card_revolut  = ft.Text("€ 0.00", size=24, weight=ft.FontWeight.BOLD, color="blue200")
    card_contanti = ft.Text("¥ 0",    size=24, weight=ft.FontWeight.BOLD, color="green200")
    card_tot_jpy  = ft.Text("¥ 0",    size=18, weight=ft.FontWeight.BOLD)
    card_tot_eur  = ft.Text("€ 0.00", size=18, weight=ft.FontWeight.BOLD)
    testo_cambio  = ft.Text("Sincronizzazione cloud...", size=12, italic=True, color="blue200")

    importo_input = ft.TextField(label="Importo", keyboard_type=ft.KeyboardType.NUMBER, border_color="blue400")
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
    def mostra_notifica(messaggio: str, colore="blue200"):
        page.snack_bar = ft.SnackBar(ft.Text(messaggio, color="white"), bgcolor=colore)
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
            testo_cambio.value  = f"Tasso Live: 1 EUR = {stato_app['tasso_live']:.2f} JPY"
            page.update()
        except Exception:
            page.on_error(ft.ControlEvent("error", str(traceback.format_exc()), "", page))

    def invia_spesa(e):
        if not importo_input.value or not cat_dropdown.value or not sorg_dropdown.value:
            mostra_notifica("⚠️ Compila tutti i campi obbligatori!", "red700")
            return

        try:
            imp_val = float(importo_input.value)
        except ValueError:
            mostra_notifica("⚠️ L'importo deve essere un numero valido.", "red700")
            return

        tasso = stato_app["tasso_live"]
        if sorg_dropdown.value in ("Carta Credito JPY", "Wallet Contanti"):
            imp_jpy, imp_eur = imp_val, imp_val / tasso
        else:
            imp_jpy, imp_eur = imp_val * tasso, imp_val

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

            importo_input.value = ""
            nota_input.value = ""
            cat_dropdown.value = None
            sorg_dropdown.value = None

            mostra_notifica("✅ Spesa registrata con successo!", "green700")
            aggiorna_dashboard()
        except Exception:
             page.on_error(ft.ControlEvent("error", str(traceback.format_exc()), "", page))

    def aggiorna_tasso(e):
        try:
            nuovo_tasso = db.get_live_rate()
            stato_app["tasso_live"] = nuovo_tasso
            mostra_notifica(f"Tasso aggiornato: ¥{nuovo_tasso:.2f}", "green700")
            aggiorna_dashboard()
        except Exception:
             page.on_error(ft.ControlEvent("error", str(traceback.format_exc()), "", page))

    # ── 6. LAYOUT E INTERFACCIA ────────────────────────────────────────────
    page.add(
        ft.Text("TOKYO TRAVEL WALLET", size=22, weight=ft.FontWeight.BOLD, letter_spacing=1.5),
        ft.Row([testo_cambio, ft.IconButton(icon=ft.icons.REFRESH, on_click=aggiorna_tasso, icon_size=16)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        ft.Divider(),
        ft.Card(content=ft.Container(content=ft.Column([ft.Text("💳 SALDO REVOLUT (STIMATO)", size=12, color="grey400"), card_revolut]), padding=14)),
        ft.Card(content=ft.Container(content=ft.Column([ft.Text("💴 CONTANTI IN TASCA", size=12, color="grey400"), card_contanti]), padding=14)),
        ft.Row([ft.Text("Tot. JPY:"), card_tot_jpy, ft.Text("Tot. EUR:"), card_tot_eur], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        ft.Divider(),
        ft.Text("Aggiungi Nuova Spesa", size=16, weight=ft.FontWeight.W_600),
        importo_input, cat_dropdown, sorg_dropdown, dest_dropdown, nota_input,
        ft.Container(height=10),
        ft.ElevatedButton("🚀 REGISTRA SPESA", on_click=invia_spesa, bgcolor="blue700", color="white", width=400, height=50),
    )

    # Il caricamento iniziale viene renderizzato solo DOPO che la pagina principale è stata disegnata stabilmente.
    def boot_app():
        try:
            stato_app["tasso_live"] = db.get_live_rate()
        except Exception:
            pass
        aggiorna_dashboard()

    # Avviamo il thread in modo sicuro
    threading.Thread(target=boot_app, daemon=True).start()

ft.app(target=main)
