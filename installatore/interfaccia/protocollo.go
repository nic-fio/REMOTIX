package interfaccia

import (
	"bufio"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"os"
	"os/exec"
	"sync"

	"remotix/installatore/motore"
)

// Il protocollo fra la finestra (come l'utente) e il motore (da root, lo STESSO eseguibile fatto
// partire da systemd col permesso di polkit: DECISIONI §10.14). JSON a righe su due tubi:
//
//	finestra → motore   {"cmd":"controlla","porta":7447}
//	                    {"cmd":"piano","voci":{…}}           (le voci del file di risposte)
//	                    {"cmd":"applica","digest":"…"}      (il digest del piano che la persona ha visto)
//	                    {"cmd":"ferma"}                      (durante applica: fermarsi e annullare)
//	motore → finestra   {"tipo":"pronto"} · {"tipo":"controllo",…} · {"tipo":"piano",…} ·
//	                    {"tipo":"evento","evento":{…}} (gli eventi del motore, §6.6.1) ·
//	                    {"tipo":"esito",…} · {"tipo":"errore","errore":{…}}
//
// ⚠ la parte da root non eredita l'ambiente: la lingua va passata esplicitamente (--lingua,
// DECISIONI §10.15).

type richiesta struct {
	Cmd    string            `json:"cmd"`
	Porta  int               `json:"porta,omitempty"`
	Voci   map[string]string `json:"voci,omitempty"`
	Digest string            `json:"digest,omitempty"`
}

type risposta struct {
	Formato   string                 `json:"formato"`
	Tipo      string                 `json:"tipo"`
	Controllo *Controllo             `json:"controllo,omitempty"`
	Piano     *motore.Piano          `json:"piano,omitempty"`
	Evento    *motore.EventoPubblico `json:"evento,omitempty"`
	Esito     *Esito                 `json:"esito,omitempty"`
	Errore    *motore.Messaggio      `json:"errore,omitempty"`
}

// Servi: il lato da root. Legge le richieste una per volta; «ferma» arriva mentre applica lavora.
func Servi(s *Sessione, in io.Reader, out io.Writer) error {
	var mu sync.Mutex
	manda := func(r risposta) {
		r.Formato = Formato
		b, _ := json.Marshal(r)
		mu.Lock()
		fmt.Fprintln(out, string(b))
		mu.Unlock()
	}
	manda(risposta{Tipo: "pronto"})
	sc := bufio.NewScanner(in)
	sc.Buffer(make([]byte, 1<<20), 1<<24)
	richieste := make(chan richiesta)
	go func() {
		for sc.Scan() {
			var r richiesta
			if json.Unmarshal(sc.Bytes(), &r) != nil {
				continue
			}
			if r.Cmd == "ferma" { // subito, anche mentre applica lavora
				s.Ferma()
				continue
			}
			richieste <- r
		}
		close(richieste)
	}()
	for r := range richieste {
		switch r.Cmd {
		case "controlla":
			c, err := s.Controlla(r.Porta)
			if err != nil {
				manda(risposta{Tipo: "errore", Errore: messaggioDi(err)})
				continue
			}
			manda(risposta{Tipo: "controllo", Controllo: c})
		case "piano":
			p, err := s.Piano(r.Voci)
			if err != nil {
				manda(risposta{Tipo: "errore", Errore: messaggioDi(err)})
				continue
			}
			manda(risposta{Tipo: "piano", Piano: p})
		case "applica":
			es, err := s.Applica(r.Digest, func(ev motore.EventoPubblico) { manda(risposta{Tipo: "evento", Evento: &ev}) })
			if err != nil {
				manda(risposta{Tipo: "errore", Errore: messaggioDi(err)})
				continue
			}
			manda(risposta{Tipo: "esito", Esito: es})
		case "fine":
			return nil
		}
	}
	return nil
}

// Cliente: il lato della finestra. Fa partire lo stesso eseguibile da root (systemd, col permesso
// di polkit: permessi.go) la prima volta che serve il motore — la password di un amministratore
// si chiede UNA volta, all'inizio.
type Cliente struct {
	Argomenti []string // gli argomenti della parte da root (lingua, archivio, …)
	// Comando: vuoto = systemd via D-Bus; le prove possono dare un comando («sudo -n»)
	Comando []string

	cmd     *exec.Cmd
	in      io.WriteCloser
	righe   chan risposta
	errore  error
	blocco  sync.Mutex
	avviato bool
}

func (c *Cliente) avvia() error {
	if c.avviato {
		return c.errore
	}
	c.avviato = true
	var out io.ReadCloser
	if len(c.Comando) == 0 {
		// la strada vera: systemd, via D-Bus, col permesso di polkit (permessi.go)
		exe, err := os.Executable()
		if err != nil {
			c.errore = err
			return err
		}
		in, o, err := avviaDaAmministratore(exe, append([]string{"motore-interfaccia"}, c.Argomenti...))
		if err != nil {
			c.errore = err
			return err
		}
		c.in, out = in, o
	} else {
		// le prove: un comando dato (per esempio «sudo -n <eseguibile>»)
		args := append(append([]string{}, c.Comando[1:]...), "motore-interfaccia")
		args = append(args, c.Argomenti...)
		c.cmd = exec.Command(c.Comando[0], args...)
		c.cmd.Stderr = os.Stderr
		var err error
		if c.in, err = c.cmd.StdinPipe(); err != nil {
			c.errore = err
			return err
		}
		if out, err = c.cmd.StdoutPipe(); err != nil {
			c.errore = err
			return err
		}
		if err := c.cmd.Start(); err != nil {
			c.errore = motore.Errore("RX-UI-004", err.Error())
			return c.errore
		}
	}
	c.righe = make(chan risposta, 64)
	go func() {
		sc := bufio.NewScanner(out)
		sc.Buffer(make([]byte, 1<<20), 1<<26)
		for sc.Scan() {
			var r risposta
			if json.Unmarshal(sc.Bytes(), &r) == nil {
				c.righe <- r
			}
		}
		close(c.righe)
	}()
	r, ok := <-c.righe
	if !ok || r.Tipo != "pronto" {
		det := "la parte da amministratore non ha risposto"
		if c.cmd != nil {
			det = fmt.Sprint(c.cmd.Wait())
		}
		c.errore = motore.Errore("RX-UI-004", det)
		return c.errore
	}
	return nil
}

func (c *Cliente) chiedi(r richiesta, eventi func(motore.EventoPubblico)) (risposta, error) {
	c.blocco.Lock()
	defer c.blocco.Unlock()
	if err := c.avvia(); err != nil {
		return risposta{}, err
	}
	b, _ := json.Marshal(r)
	if _, err := fmt.Fprintln(c.in, string(b)); err != nil {
		return risposta{}, motore.Errore("RX-UI-005", err.Error())
	}
	for x := range c.righe {
		switch x.Tipo {
		case "evento":
			if eventi != nil && x.Evento != nil {
				eventi(*x.Evento)
			}
		case "errore":
			if x.Errore != nil {
				return x, &motore.ErroreRX{M: *x.Errore}
			}
			return x, errors.New("errore")
		default:
			return x, nil
		}
	}
	return risposta{}, motore.Errore("RX-UI-005", "")
}

func (c *Cliente) Controlla(porta int) (*Controllo, error) {
	r, err := c.chiedi(richiesta{Cmd: "controlla", Porta: porta}, nil)
	return r.Controllo, err
}

func (c *Cliente) Piano(voci map[string]string) (*motore.Piano, error) {
	r, err := c.chiedi(richiesta{Cmd: "piano", Voci: voci}, nil)
	return r.Piano, err
}

func (c *Cliente) Applica(digest string, eventi func(motore.EventoPubblico)) (*Esito, error) {
	r, err := c.chiedi(richiesta{Cmd: "applica", Digest: digest}, eventi)
	return r.Esito, err
}

// Ferma: non passa dal blocco (applica lo tiene finché lavora).
func (c *Cliente) Ferma() {
	if c.in != nil {
		fmt.Fprintln(c.in, `{"cmd":"ferma"}`)
	}
}

func (c *Cliente) Chiudi() {
	if c.in != nil {
		fmt.Fprintln(c.in, `{"cmd":"fine"}`)
		c.in.Close()
	}
	if c.cmd != nil && c.cmd.Process != nil {
		c.cmd.Wait()
	}
}
