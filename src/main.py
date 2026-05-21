# src/main.py
import flet as ft
from datetime import date
import database as db

def main(page: ft.Page):
    # Configurazione della pagina per smartphone
    page.title = "Tokyo Travel Wallet"
    page.theme_mode = ft.ThemeMode.DARK
    page.scroll = "adaptive"
    page.padding = 16

    # Funzione di utilità per aggiornare i dati della UI
    def aggiorna_dashboard():
        try:
            operazioni = db.recupera_operazioni()
            metriche = db.calcola_metriche(operazioni)
            
            # Aggiorna i testi dei saldi
            card_revolut.value = f"€ {metriche['saldo_revolut_eur']:.2f}"
            card_contanti.value = f"¥ {metriche['saldo_contanti_jpy']:,.0f}"
            card_tot_jpy.value = f"¥ {metriche['totale_jpy']:,.0f}"
            card_tot_eur.value = f"€ {metriche['totale_eur']:.2f}"
            testo_cambio.value = f"Tasso Live: 1 EUR = {metriche['tasso_cambio']:.2f} JPY"
        except Exception as ex:
            page.snack_bar = ft.SnackBar(ft.Text(f"Errore sincronizzazione: {ex}"))
            page.snack_bar.open = True
        page.update()

    # Gestione invio modulo
    def invia_spesa(e):
        if not importo_input.value or not cat_dropdown.value or not sorg_dropdown.value:
            page.snack_bar = ft.SnackBar(ft.Text("⚠️ Compila i campi obbligatori!"))
            page.snack_bar.open = True
            page.update()
            return
        
        # Calcolo al volo del controvalore in base alla sorgente scelta
        tasso_attuale = db.get_live_rate()
        imp_jpy = 0.0
        imp_eur = 0.0
        
        if sorg_dropdown.value == "Carta Credito JPY" or sorg_dropdown.value == "Wallet Contanti":
            imp_jpy = float(importo_input.value)
            imp_eur = imp_jpy / tasso_attuale
        else: # Ricariche o spese dirette in EUR
            imp_eur = float(importo_input.value)
            imp_jpy = imp_eur * tasso_attuale

        # Inserimento nel database cloud
        db.inserisci_operazione(
            data_pagamento=str(date.today()),
            categoria=cat_dropdown.value,
            sorgente=sorg_dropdown.value,
            importo_jpy=imp_jpy,
            importo_eur=imp_eur,
            destinatario=dest_dropdown.value,
            stato="Spesa Effettiva",
            nota=nota_input.value
        )

        # Reset dei campi e feedback
        importo_input.value = ""
        nota_input.value = ""
        page.snack_bar = ft.SnackBar(ft.Text("✅ Spesa registrata nel Cloud!"))
        page.snack_bar.open = True
        aggiorna_dashboard()

    # --- ELEMENTI VISIVI (WIDGETS) ---
    
    # Contenitori delle metriche (Griglia verticale per Mobile)
    card_revolut = ft.Text("€ 0.00", size=24, weight=ft.FontWeight.BOLD, color=ft.colors.BLUE_200)
    card_contanti = ft.Text("¥ 0", size=24, weight=ft.FontWeight.BOLD, color=ft.colors.GREEN_200)
    card_tot_jpy = ft.Text("¥ 0", size=18, weight=ft.FontWeight.BOLD)
    card_tot_eur = ft.Text("€ 0.00", size=18, weight=ft.FontWeight.BOLD)
    testo_cambio = ft.Text("Caricamento tasso...", size=12, italic=True, color=ft.colors.GREY_400)

    # Form di Inserimento Rapido
    importo_input = ft.TextField(label="Importo", keyboard_type=ft.KeyboardType.NUMBER, border_color=ft.colors.BLUE_400)
    
    cat_dropdown = ft.Dropdown(
        label="Categoria",
        options=[
            ft.dropdown.Option("Cibo"), ft.dropdown.Option("Trasporti"),
            ft.dropdown.Option("Alloggio"), ft.dropdown.Option("Shopping"),
            ft.dropdown.Option("Ricarica Revolut"), ft.dropdown.Option("Prelievo Contanti")
        ]
    )
    
    sorg_dropdown = ft.Dropdown(
        label="Sorgente Fondi",
        options=[
            ft.dropdown.Option("Carta Credito JPY"),
            ft.dropdown.Option("Wallet Contanti"),
            ft.dropdown.Option("Conto EUR")
        ]
    )

    dest_dropdown = ft.Dropdown(
        label="Destinatario",
        value="Personale",
        options=[
            ft.dropdown.Option("Personale"), ft.dropdown.Option("Famiglia"),
            ft.dropdown.Option("Francesco"), ft.dropdown.Option("Guia"), ft.dropdown.Option("Matilde")
        ]
    )
    
    nota_input = ft.TextField(label="Nota (Opzionale)")

    # Costruzione del Layout della Schermata
    page.add(
        ft.Text("TOKYO TRAVEL WALLET", size=22, weight=ft.FontWeight.BOLD, letter_spacing=1.5),
        testo_cambio,
        ft.Divider(),
        
        # Sezione Saldi Disponibili
        ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.Text("💳 SALDO REVOLUT (ESTIMATO)", size=12, color=ft.colors.GREY_400),
                    card_revolut
                ]), padding=14
            )
        ),
        ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.Text("💴 CONTANTI IN TASCA", size=12, color=ft.colors.GREY_400),
                    card_contanti
                ]), padding=14
            )
        ),
        
        # Sezione Riepilogo Uscite
        ft.Row([
            ft.Text("Tot. JPY:"), card_tot_jpy,
            ft.Text("Tot. EUR:"), card_eur := card_tot_eur
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        
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
            height=50
        )
    )

    # Caricamento iniziale dei dati all'apertura dell'app
    aggiorna_dashboard()

ft.app(target=main)
