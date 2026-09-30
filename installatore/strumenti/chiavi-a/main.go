// chiavi-a: lo strumento di chi PUBBLICA, per la catena A della fiducia (fasi/17 §6.6.10): crea la
// radice e le sottochiavi, firma il catalogo e il motore, scrive l'elenco delle revoche.
//
// ⛔ Non entra mai nel motore installato (remotix-install non sa firmare): è un programma a parte,
// per la macchina che pubblica. La RADICE va tenuta fuori linea (D11: dove, chi, quante copie).
// ⚠ Le chiavi fatte in T8 sono DI PROVA: generate apposta, non proteggono niente di vero.
//
//	chiavi-a radice      <cartella>                         radice-A.chiave e radice-A.pub
//	chiavi-a sottochiave <cartella> <id> <dal> <al>         sottochiave-<id>.chiave (certificata dalla radice)
//	chiavi-a firma       <cartella> <id> <oggetto> <file> [<firmato-il>]   <file>.firma
//	chiavi-a revoche     <cartella> <sequenza> <emesso> <uscita.json> [<id>=<motivo> …]
//	chiavi-a verifica    <radice.pub> <oggetto> <file> [<data>]            (come il motore)
package main

import (
	"crypto/ed25519"
	"crypto/rand"
	"encoding/base64"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"strconv"
	"strings"
	"time"

	"remotix/installatore/motore"
)

type chiaveFile struct {
	Avviso      string              `json:"avviso"`
	Catena      string              `json:"catena"`
	Ruolo       string              `json:"ruolo"` // radice · sottochiave
	Privata     string              `json:"privata"`
	Pubblica    string              `json:"pubblica"`
	Certificato *motore.Sottochiave `json:"certificato,omitempty"`
}

const avviso = "CHIAVE DI PROVA della fase 17 (T8): generata apposta per le prove, non protegge niente di vero. D11 decide la custodia della chiave vera."

func muori(f string, a ...any) {
	fmt.Fprintf(os.Stderr, "chiavi-a: "+f+"\n", a...)
	os.Exit(1)
}

func scrivi(p string, v any, modo os.FileMode) {
	b, _ := json.MarshalIndent(v, "", "  ")
	if err := os.WriteFile(p, append(b, '\n'), modo); err != nil {
		muori("%v", err)
	}
}

func leggi(p string) chiaveFile {
	var c chiaveFile
	b, err := os.ReadFile(p)
	if err != nil {
		muori("%v", err)
	}
	if err := json.Unmarshal(b, &c); err != nil {
		muori("%s: %v", p, err)
	}
	return c
}

func privata(c chiaveFile) ed25519.PrivateKey {
	b, err := base64.StdEncoding.DecodeString(c.Privata)
	if err != nil || len(b) != ed25519.SeedSize {
		muori("chiave privata illeggibile")
	}
	return ed25519.NewKeyFromSeed(b)
}

func main() {
	if len(os.Args) < 3 {
		muori("uso: radice | sottochiave | firma | revoche | verifica (vedi il sorgente)")
	}
	a := os.Args[2:]
	switch os.Args[1] {
	case "radice":
		dir := a[0]
		os.MkdirAll(dir, 0o700)
		if _, err := os.Stat(filepath.Join(dir, "radice-A.chiave")); err == nil {
			muori("la radice c'è già: non la sovrascrivo")
		}
		pub, priv, _ := ed25519.GenerateKey(rand.Reader)
		scrivi(filepath.Join(dir, "radice-A.chiave"), chiaveFile{Avviso: avviso, Catena: "A", Ruolo: "radice",
			Privata: base64.StdEncoding.EncodeToString(priv.Seed()), Pubblica: base64.StdEncoding.EncodeToString(pub)}, 0o600)
		os.WriteFile(filepath.Join(dir, "radice-A.pub"), []byte("# "+avviso+"\n# impronta "+motore.ImprontaChiave(pub)+"\n"+
			base64.StdEncoding.EncodeToString(pub)+"\n"), 0o644)
		fmt.Println("radice", motore.ImprontaChiave(pub))
	case "sottochiave":
		if len(a) != 4 {
			muori("sottochiave <cartella> <id> <dal> <al>")
		}
		dir, id := a[0], a[1]
		r := leggi(filepath.Join(dir, "radice-A.chiave"))
		pub, priv, _ := ed25519.GenerateKey(rand.Reader)
		s := motore.CertificaSottochiave(privata(r), id, pub, a[2], a[3])
		scrivi(filepath.Join(dir, "sottochiave-"+id+".chiave"), chiaveFile{Avviso: avviso, Catena: "A", Ruolo: "sottochiave",
			Privata: base64.StdEncoding.EncodeToString(priv.Seed()), Pubblica: s.Pubblica, Certificato: s}, 0o600)
		fmt.Println("sottochiave", id, a[2], a[3], motore.ImprontaChiave(pub))
	case "firma":
		if len(a) < 4 {
			muori("firma <cartella> <id> <oggetto> <file> [<firmato-il>]")
		}
		k := leggi(filepath.Join(a[0], "sottochiave-"+a[1]+".chiave"))
		dati, err := os.ReadFile(a[3])
		if err != nil {
			muori("%v", err)
		}
		quando := time.Now().UTC().Format("2006-01-02")
		if len(a) > 4 {
			quando = a[4]
		}
		if err := os.WriteFile(a[3]+".firma", motore.Firma(privata(k), k.Certificato, a[2], dati, quando), 0o644); err != nil {
			muori("%v", err)
		}
		fmt.Println("firmato", a[3], "con", a[1])
	case "revoche":
		if len(a) < 4 {
			muori("revoche <cartella> <sequenza> <emesso> <uscita.json> [<id>=<motivo> …]")
		}
		r := leggi(filepath.Join(a[0], "radice-A.chiave"))
		n, err := strconv.Atoi(a[1])
		if err != nil {
			muori("sequenza: %v", err)
		}
		rv := motore.Revoche{Formato: motore.FormatoRevoche, Catena: "A", Sequenza: n, Emesso: a[2], Revocate: []motore.Revoca{}}
		for _, x := range a[4:] {
			id, mot, _ := strings.Cut(x, "=")
			rv.Revocate = append(rv.Revocate, motore.Revoca{ID: id, Motivo: mot})
		}
		b, _ := json.MarshalIndent(rv, "", "  ")
		b = append(b, '\n')
		if err := os.WriteFile(a[3], b, 0o644); err != nil {
			muori("%v", err)
		}
		os.WriteFile(a[3]+".firma", motore.Firma(privata(r), nil, "revoche", b, a[2]), 0o644)
		fmt.Println("revoche", n, len(rv.Revocate))
	case "verifica":
		if len(a) < 3 {
			muori("verifica <radice.pub> <oggetto> <file> [<data>]")
		}
		t, _ := os.ReadFile(a[0])
		radici, err := motore.LeggiRadici(string(t))
		if err != nil {
			muori("%v", err)
		}
		dati, _ := os.ReadFile(a[2])
		firma, _ := os.ReadFile(a[2] + ".firma")
		adesso := time.Now()
		if len(a) > 3 {
			adesso, _ = time.Parse("2006-01-02", a[3])
		}
		e, err := motore.VerificaFirma(radici, dati, firma, a[1], adesso, nil)
		if err != nil {
			muori("%v", err)
		}
		fmt.Println("verificata:", e.Sottochiave, e.Dal, e.Al)
	default:
		muori("comando sconosciuto %q", os.Args[1])
	}
}
