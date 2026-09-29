package motore

import "encoding/json"

// I passi che il motore CONOSCE ma non sa ancora eseguire (T4, prima parte). Stanno qui perché
// l'installatore è l'unica via (DECISIONI §10.12): il pacchetto porta i pezzi inerti, e tocca al
// motore, come passi del piano col registro, iscrivere le persone ai gruppi (fatto:
// aggiungi-utente-a-gruppo), attivare le tre cinture (D4), aprire il firewall (fatto, firewalld:
// regola-firewall), installare il desktop se manca (DECISIONI §10.7), aggiungere un deposito di
// terzi (D5), far installare i pacchetti al gestore della distribuzione, abilitare e accendere il
// servizio. I passi dichiarati entrano nel piano (si vedono, si approvano, sono nell'impronta), ma
// un'operazione che ne contiene uno si ferma PRIMA di toccare la macchina, con RX-AZIONE-004.

// nonAncoraFatti: tipo → che cosa manca per farlo.
var nonAncoraFatti = map[string]string{
	"installa-desktop":   "serve il gestore di pacchetti (fasi 5-6)",
	"installa-pacchetti": "la transazione del gestore di pacchetti e il suo rimedio alla ripresa (§6.6.3), T5",
	"aggiungi-deposito":  "i depositi di terzi col consenso (D5), T5",
	"attiva-cintura":     "le tre cinture in /etc dai file spenti di /usr/share/remotix/cinture/ (D4), T5",
	"accendi-servizio":   "l'accensione fra 7a e 7b (§6.0), T5",
}

func init() {
	for t := range nonAncoraFatti {
		registraTipo(t, func(p AzionePiano) (Azione, error) { return nonAncoraFatta{p.Tipo}, nil })
	}
}

// PianoDesktop: il desktop che manca, dagli archivi della distribuzione, SENZA schermata d'accesso
// locale né avvio in grafica (R38). AL_MEGLIO: toglierlo non rende la macchina identica.
func PianoDesktop(id, desktop string) AzionePiano {
	return AzionePiano{
		ID: id, Tipo: "installa-desktop",
		Parametri:      map[string]string{"desktop": desktop},
		Descrizione:    T("az.desktop", NomeDesktop(desktop)),
		ComeSiFa:       T("az.desktop.fa", NomeDesktop(desktop)),
		ComeSiVerifica: T("az.desktop.verifica"),
		ComeSiAnnulla:  T("az.desktop.annulla"),
		Reversibilita:  AL_MEGLIO,
	}
}

// PianoCintura: una delle tre cinture (niente spegnimento, sospensione, tasti) accesa in /etc dal
// file spento che il pacchetto porta. Se è predefinita o scelta è la decisione D4, aperta.
func PianoCintura(id, sorgente, destinazione string) AzionePiano {
	return AzionePiano{
		ID: id, Tipo: "attiva-cintura",
		Parametri:      map[string]string{"sorgente": sorgente, "percorso": destinazione},
		Descrizione:    T("az.cintura", destinazione),
		ComeSiFa:       T("az.cintura.fa", sorgente, destinazione),
		ComeSiVerifica: T("az.cintura.verifica"),
		ComeSiAnnulla:  T("az.cintura.annulla"),
		Reversibilita:  ESATTA,
		Consenso:       T("az.cintura.consenso"),
	}
}

// PianoAccendiServizio: abilitare e accendere remotix.service, dopo i controlli 7a.
func PianoAccendiServizio(id string) AzionePiano {
	return AzionePiano{
		ID: id, Tipo: "accendi-servizio",
		Parametri:      map[string]string{"unita": "remotix.service"},
		Descrizione:    T("az.servizio"),
		ComeSiFa:       T("az.servizio.fa"),
		ComeSiVerifica: T("az.servizio.verifica"),
		ComeSiAnnulla:  T("az.servizio.annulla"),
		Reversibilita:  ESATTA,
	}
}

type nonAncoraFatta struct{ tipo string }

func (n nonAncoraFatta) err() error {
	return Errore("RX-AZIONE-004", n.tipo+": "+nonAncoraFatti[n.tipo])
}

func (n nonAncoraFatta) Vincoli(*Contesto) ([]string, error) { return nil, nil }
func (n nonAncoraFatta) Fotografa(*Contesto) (json.RawMessage, Origine, error) {
	return nil, "", n.err()
}
func (n nonAncoraFatta) Fai(*Contesto, json.RawMessage) error { return n.err() }
func (n nonAncoraFatta) Controlla(*Contesto, json.RawMessage) (Esito, string, error) {
	return "", "", n.err()
}
func (n nonAncoraFatta) Annulla(*Contesto, json.RawMessage) error { return n.err() }
func (n nonAncoraFatta) Annullata(*Contesto, json.RawMessage) (bool, string, error) {
	return false, "", n.err()
}

// PassiNonFatti: i passi del piano che il motore non sa ancora eseguire.
func PassiNonFatti(p *Piano) []string {
	var r []string
	for _, a := range p.Azioni {
		if m, ok := nonAncoraFatti[a.Tipo]; ok {
			r = append(r, a.ID+" ("+a.Tipo+": "+m+")")
		}
	}
	return r
}
