from src.services.report_generator import ReportGenerator
from src.repositories.proprieta_repository import ProprietaRepository
from src.cli.utils import print_colored

def visualizza_report():
    report_gen = ReportGenerator()
    prop_repo = ProprietaRepository()
    while True:
        print_colored("\n--- Visualizza Report ---", "magenta", bold=True)
        print("1. Cash Flow Personale (Mensile/Annuale)")
        print("2. Profit & Loss per Singola Proprietà (Mensile/Annuale)")
        print("3. Riepilogo Spese Fiscalmente Rilevanti (Annuale)")
        print("4. Patrimonio Netto Semplificato (Snapshot)")
        print("0. Torna al menu principale")
        scelta = input("\nSeleziona un report: ").strip()
        if scelta == "1":
            print("\n--- Cash Flow Personale ---")
            try:
                anno = int(input("Anno (es. 2024): ").strip())
            except ValueError:
                print_colored("Anno non valido.", "red")
                input("\nPremi Invio per continuare...")
                continue
            mese_str = input("Mese (1-12, Invio per tutto l'anno): ").strip()
            mese = int(mese_str) if mese_str else None
            try:
                res = report_gen.generate_cash_flow_personale(anno, mese)
                print(f"\nPeriodo: {res['periodo']}")
                print(f"Totale Entrate Personali: €{res['totale_entrate_personali']:.2f}")
                print(f"Totale Uscite Personali: €{res['totale_uscite_personali']:.2f}")
                print(f"Risparmio/Deficit: €{res['risparmio_deficit_personale']:.2f}")
            except Exception as e:
                print_colored(f"\nErrore: {e}", "red")
            input("\nPremi Invio per continuare...")
        elif scelta == "2":
            print("\n--- Profit & Loss per Proprietà ---")
            props = prop_repo.get_all(order_by="id_proprieta")
            if not props:
                print_colored("Nessuna proprietà presente.", "yellow")
                input("\nPremi Invio per continuare...")
                continue
            print("\nProprietà disponibili:")
            for p in props:
                print(f"{p.id_proprieta}. {p.nome_o_indirizzo_breve} ({p.tipo.value})")
            try:
                id_prop = int(input("ID proprietà: ").strip())
            except ValueError:
                print_colored("ID non valido.", "red")
                input("\nPremi Invio per continuare...")
                continue
            try:
                anno = int(input("Anno (es. 2024): ").strip())
            except ValueError:
                print_colored("Anno non valido.", "red")
                input("\nPremi Invio per continuare...")
                continue
            mese_str = input("Mese (1-12, Invio per tutto l'anno): ").strip()
            mese = int(mese_str) if mese_str else None
            try:
                res = report_gen.generate_pl_proprieta(id_prop, anno, mese)
                print(f"\nProprietà: {res['nome_proprieta']} ({res['tipo_proprieta']})")
                print(f"Periodo: {res['periodo']}")
                if res['totale_affitti_incassati'] is not None:
                    print(f"Totale Affitti Incassati: €{res['totale_affitti_incassati']:.2f}")
                print(f"Totale Spese Proprietà: €{res['totale_spese_proprieta']:.2f}")
                print(f"Profit/Loss Netto: €{res['profit_loss_netto']:.2f}")
            except Exception as e:
                print_colored(f"\nErrore: {e}", "red")
            input("\nPremi Invio per continuare...")
        elif scelta == "3":
            print("\n--- Riepilogo Spese Fiscalmente Rilevanti ---")
            try:
                anno = int(input("Anno (es. 2024): ").strip())
            except ValueError:
                print_colored("Anno non valido.", "red")
                input("\nPremi Invio per continuare...")
                continue
            try:
                res = report_gen.generate_riepilogo_fiscale(anno)
                print(f"\nAnno: {res['anno']}")
                print(f"Somma Totale Deducibili: €{res['somma_totale_deducibili']:.2f}")
                print("\nTransazioni deducibili:")
                for t in res['elenco_transazioni_deducibili']:
                    print(f"  Data: {t['data']}, Importo: €{t['importo']:.2f}, Categoria: {t['categoria']}, Desc: {t['descrizione']}")
                print("\nRiepilogo entrate da affitto per proprietà:")
                for nome, val in res['riepilogo_entrate_da_affitto_per_proprieta'].items():
                    print(f"  {nome}: €{val:.2f}")
                print(f"Totale entrate da affitto: €{res['totale_entrate_da_affitto']:.2f}")
            except Exception as e:
                print_colored(f"\nErrore: {e}", "red")
            input("\nPremi Invio per continuare...")
        elif scelta == "4":
            print("\n--- Patrimonio Netto Semplificato ---")
            try:
                res = report_gen.calculate_patrimonio_netto_semplificato()
                print(f"\nData calcolo: {res['data_calcolo']}")
                print(f"Somma valori proprietà: €{res['somma_valori_proprieta']:.2f}")
                print(f"Somma saldi conti attivi: €{res['somma_saldi_conti_attivi']:.2f}")
                print(f"Patrimonio netto semplificato: €{res['patrimonio_netto_semplificato']:.2f}")
            except Exception as e:
                print_colored(f"\nErrore: {e}", "red")
            input("\nPremi Invio per continuare...")
        elif scelta == "0":
            break
        else:
            print_colored("\nOpzione non valida. Riprova.", "red")
