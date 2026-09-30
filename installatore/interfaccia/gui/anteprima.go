//go:build gui

package gui

import (
	"fmt"
	"image"
	"image/png"
	"os"
	"path/filepath"
	"time"

	"gioui.org/gpu/headless"
	"gioui.org/layout"
	"gioui.org/op"
	"gioui.org/unit"

	"remotix/installatore/interfaccia"
	"remotix/installatore/motore"
)

// Anteprima: le schermate disegnate FUORI SCHERMO (Gio senza finestra, EGL) in PNG, 1120×760 come
// il prototipo — per guardarle prima di averle su un desktop vero. I dati: il profilo, il rapporto
// e il piano VERI di una macchina (dati/verifica.json da «remotix-install verifica --json»,
// dati/piano.json da «remotix-install piano --installa --json»); le varianti senza desktop e
// «bloccata», l'avanzamento a metà e il certificato si ricavano da quelli (sono dimostrazioni, e
// il nome del file lo dice solo nel registro della fase).
func Anteprima(uscita, dati string, scala float32) error {
	var ver struct {
		Fiducia  *motore.Fiducia  `json:"fiducia"`
		Profilo  *motore.Profilo  `json:"profilo"`
		Rapporto *motore.Rapporto `json:"compatibilita"`
	}
	if err := motore.LeggiJSON(filepath.Join(dati, "verifica.json"), &ver); err != nil {
		return err
	}
	var piano motore.Piano
	if err := motore.LeggiJSON(filepath.Join(dati, "piano.json"), &piano); err != nil {
		return err
	}
	if err := os.MkdirAll(uscita, 0o755); err != nil {
		return err
	}
	if scala <= 0 {
		scala = 1
	}
	W, H := int(1120*scala), int(760*scala)
	win, err := headless.NewWindow(W, H)
	if err != nil {
		return fmt.Errorf("gio senza schermo: %w", err)
	}
	defer win.Release()
	var ops op.Ops
	foto := func(f *Finestra, nome string) error {
		for i := 0; i < 2; i++ { // due giri: il primo registra i widget, il secondo disegna fermo
			ops.Reset()
			gtx := layout.Context{Ops: &ops, Now: time.Now(), Constraints: layout.Exact(image.Pt(W, H)),
				Metric: unit.Metric{PxPerDp: scala, PxPerSp: scala}}
			f.disegna(gtx)
		}
		if err := win.Frame(&ops); err != nil {
			return err
		}
		img := image.NewRGBA(image.Rectangle{Max: image.Pt(W, H)})
		if err := win.Screenshot(img); err != nil {
			return err
		}
		out, err := os.Create(filepath.Join(uscita, nome))
		if err != nil {
			return err
		}
		defer out.Close()
		fmt.Println(filepath.Join(uscita, nome))
		return png.Encode(out, img)
	}

	// la macchina vera: le domande come le fa il motore su quella macchina (senza l'ambiente: le
	// persone e il firewall dal profilo)
	dom := domandeDaProfilo(ver.Profilo, ver.Rapporto, &piano)
	ctrl := &interfaccia.Controllo{Fiducia: ver.Fiducia, Profilo: ver.Profilo, Rapporto: ver.Rapporto, Domande: dom}

	f := nuova(nil)
	f.metteControllo(ctrl)
	if err := foto(f, "1-controllo.png"); err != nil {
		return err
	}
	f.schermo = sScelte
	if err := foto(f, "2-scelte.png"); err != nil {
		return err
	}
	f.piano = &piano
	f.vp = interfaccia.VistaDelPiano(&piano, ver.Profilo, interfaccia.NomiDepositi(dom))
	f.schermo = sPiano
	if err := foto(f, "3-piano.png"); err != nil {
		return err
	}
	f.av = interfaccia.NuovoAvanzamento(f.vp)
	for _, s := range []motore.Stato{motore.NUOVA, motore.FIDATA, motore.ESAMINATA, motore.VALUTATA, motore.PIANIFICATA, motore.APPROVATA, motore.ACQUISITA, motore.IN_ESECUZIONE} {
		f.av.Evento(motore.EventoPubblico{Evento: "stato", A: s})
	}
	for i, a := range piano.Azioni {
		f.av.Evento(motore.EventoPubblico{Evento: "azione", Azione: a.ID, Fase: "INTENZIONE"})
		if a.ID == "pacchetti" {
			break
		}
		if i >= 0 {
			f.av.Evento(motore.EventoPubblico{Evento: "azione", Azione: a.ID, Fase: "FATTA"})
		}
	}
	f.schermo = sAvanzamento
	if err := foto(f, "4-avanzamento.png"); err != nil {
		return err
	}
	cert := &motore.Certificato{Stato: motore.CONFERMATA_A_CONDIZIONI, Catalogo: piano.Catalogo, Motore: piano.Motore,
		Condizioni: piano.Condizioni}
	for _, a := range piano.Azioni {
		cert.Controlli = append(cert.Controlli, motore.Controllo{ID: a.ID, Esito: "PASS"})
	}
	cert.Controlli = append(cert.Controlli, motore.Controllo{ID: "codifica-h264", Esito: "PASS", Dettaglio: "h264_vaapi"},
		motore.Controllo{ID: "pam-risolta", Esito: "PASS"}, motore.Controllo{ID: "porta-firewall", Esito: "PASS"})
	es := &interfaccia.Esito{Operazione: "(anteprima)", Stato: cert.Stato, Cartella: "/var/lib/remotix/operazioni/(anteprima)",
		Certificato: cert, Indirizzi: []string{"192.168.0.50"}}
	f.pronto = interfaccia.VistaDelPronto(es, f.vp, 7447, interfaccia.DepositoVideo(dom, f.voci))
	f.schermo = sPronto
	if err := foto(f, "5-pronto.png"); err != nil {
		return err
	}

	// la variante senza desktop: la stessa macchina, come un server Ubuntu 26.04 senza desktop
	nd := nuova(nil)
	pnd := copiaProfilo(ver.Profilo, map[string]string{"distro.id": "ubuntu", "distro.nome": "Ubuntu 26.04 LTS",
		"distro.versione": "26.04", "distro.variante": "server", "desktop.gnome": "assente", "selinux": "", "apparmor": "enforce"})
	rnd := *ver.Rapporto
	rnd.SenzaDesktop = true
	rnd.Desktop = nil
	for _, e := range ver.Rapporto.Desktop {
		e.Installato, e.Condizioni = "assente", nil
		rnd.Desktop = append(rnd.Desktop, e)
	}
	dnd := &motore.Domande{Porta: 7447, Firewall: "nessuno", Depositi: []motore.DomandaDeposito{},
		Desktop: &motore.Scelta{ID: "desktop", Opzioni: []string{"gnome", "kde", "xfce", "lxqt", "no"}, Predefinita: "gnome"},
		Persone: dom.Persone, SenzaScheda: dom.SenzaScheda}
	nd.metteControllo(&interfaccia.Controllo{Fiducia: ver.Fiducia, Profilo: pnd, Rapporto: &rnd, Domande: dnd})
	nd.schermo = sScelte
	if err := foto(nd, "variante-nessun-desktop.png"); err != nil {
		return err
	}

	// la variante bloccata: Debian 12
	bl := nuova(nil)
	pbl := copiaProfilo(ver.Profilo, map[string]string{"distro.id": "debian", "distro.nome": "Debian GNU/Linux 12 (bookworm)",
		"distro.versione": "12", "distro.variante": "", "desktop.gnome": "43.9"})
	rbl := motore.Rapporto{Piattaforma: "Debian GNU/Linux 12 (bookworm)", Riconosciuta: motore.T("comp.esclusa"), Minima: "Debian 13"}
	mot := motore.Msg("RX-COMPAT-001", "mutter 43 / GNOME 43, niente libei, niente labwc: la base è troppo vecchia")
	for _, d := range []string{"gnome", "kde", "xfce", "lxqt"} {
		inst := "assente"
		if d == "gnome" {
			inst = "43.9"
		}
		rbl.Desktop = append(rbl.Desktop, motore.EsitoDesktop{Desktop: d, Installato: inst, Livello: motore.NON_SUPPORTATA, Motivi: []motore.Messaggio{mot}})
	}
	bl.metteControllo(&interfaccia.Controllo{Fiducia: ver.Fiducia, Profilo: pbl, Rapporto: &rbl, Domande: &motore.Domande{Porta: 7447}})
	return foto(bl, "variante-bloccata.png")
}

func copiaProfilo(p *motore.Profilo, cambi map[string]string) *motore.Profilo {
	q := *p
	q.Fatti = nil
	for _, f := range p.Fatti {
		if v, ok := cambi[f.Chiave]; ok {
			f.Valore = v
			delete(cambi, f.Chiave)
		}
		q.Fatti = append(q.Fatti, f)
	}
	for k, v := range cambi {
		q.Fatti = append(q.Fatti, motore.Fatto{Chiave: k, Valore: v, Stato: motore.RILEVATO})
	}
	q.Messaggi = nil
	return &q
}

// domandeDaProfilo: per l'anteprima (niente ambiente vero): il firewall dal profilo, le persone e i
// depositi dal piano fatto su quella macchina.
func domandeDaProfilo(p *motore.Profilo, r *motore.Rapporto, pn *motore.Piano) *motore.Domande {
	d := &motore.Domande{Porta: 7447, Depositi: []motore.DomandaDeposito{}, SenzaScheda: []string{}}
	switch {
	case p.V("firewall.tipo") != "firewalld":
		d.Firewall = "nessuno"
	case p.V("firewall.porta_7447_tcp") == "aperta":
		d.Firewall = "aperto"
	default:
		d.Firewall = "chiuso"
	}
	visti := map[string]bool{}
	for _, a := range pn.Azioni {
		switch a.Tipo {
		case "aggiungi-deposito":
			if a.ID != "archivio-remotix" {
				id := a.Parametri["tipo"]
				nome := map[string]string{"rpmfusion": "RPM Fusion", "packman": "Packman", "epel": "EPEL", "openh264": "OpenH264 di Cisco"}[id]
				d.Depositi = append(d.Depositi, motore.DomandaDeposito{ID: id, Nome: nome, Per: "h264", Serve: true})
			}
		case "aggiungi-utente-a-gruppo":
			if u := a.Parametri["utente"]; !visti[u] {
				visti[u] = true
				d.Persone = append(d.Persone, u)
				d.SenzaScheda = append(d.SenzaScheda, u)
			}
		}
	}
	return d
}
