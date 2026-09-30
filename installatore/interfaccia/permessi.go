package interfaccia

import (
	"errors"
	"fmt"
	"io"
	"os"
	"strings"

	"github.com/godbus/dbus/v5"

	"remotix/installatore/motore"
)

// La parte da amministratore della finestra: lo STESSO eseguibile, lanciato da root da systemd
// come unità transitoria, chiesta sul D-Bus di sistema (StartTransientUnit) col permesso di polkit
// (l'agente della sessione grafica mostra il dialogo della password). DECISIONI §10.14: con
// systemd e polkit si parla dall'interno, per D-Bus, senza lanciare programmi — e senza dipendere
// da pkexec, che non tutte le distribuzioni installano col desktop (`[M]` 30 set, debian13-kde:
// «exec: pkexec: executable file not found»). Standard input e output dell'unità sono due tubi di
// questo processo (i descrittori passano sul bus, come fa «systemd-run --pipe»).

type execStart struct {
	Path    string
	Args    []string
	Unclean bool
}

type proprieta struct {
	Nome   string
	Valore dbus.Variant
}

type ausiliaria struct {
	Nome string
	Prop []proprieta
}

// avviaDaAmministratore: il comando come unità transitoria da root; restituisce il tubo per
// scrivergli (il suo stdin) e quello per leggerlo (il suo stdout).
func avviaDaAmministratore(exe string, args []string) (io.WriteCloser, io.ReadCloser, error) {
	conn, err := dbus.ConnectSystemBus()
	if err != nil {
		return nil, nil, motore.Errore("RX-UI-004", "D-Bus di sistema: "+err.Error())
	}
	inR, inW, err := os.Pipe()
	if err != nil {
		return nil, nil, err
	}
	outR, outW, err := os.Pipe()
	if err != nil {
		return nil, nil, err
	}
	nome := fmt.Sprintf("remotix-install-finestra-%d.service", os.Getpid())
	props := []proprieta{
		{"Description", dbus.MakeVariant("REMOTIX: la parte da amministratore dell'installatore (finestra di uid " + fmt.Sprint(os.Getuid()) + ")")},
		{"ExecStart", dbus.MakeVariant([]execStart{{Path: exe, Args: append([]string{exe}, args...)}})},
		{"Type", dbus.MakeVariant("exec")},
		{"CollectMode", dbus.MakeVariant("inactive-or-failed")},
		{"StandardInputFileDescriptor", dbus.MakeVariant(dbus.UnixFD(inR.Fd()))},
		{"StandardOutputFileDescriptor", dbus.MakeVariant(dbus.UnixFD(outW.Fd()))},
		{"StandardError", dbus.MakeVariant("journal")},
		{"Environment", dbus.MakeVariant([]string{"REMOTIX_UID=" + fmt.Sprint(os.Getuid())})},
	}
	// il messaggio a mano: Object.Call di godbus toglie il flag ALLOW_INTERACTIVE_AUTHORIZATION, e
	// senza quel flag systemd risponde InteractiveAuthorizationRequired invece di far chiedere la
	// password all'agente della sessione (`[M]` 30 set, debian13-kde)
	msg := &dbus.Message{Type: dbus.TypeMethodCall, Flags: dbus.FlagAllowInteractiveAuthorization,
		Headers: map[dbus.HeaderField]dbus.Variant{
			dbus.FieldDestination: dbus.MakeVariant("org.freedesktop.systemd1"),
			dbus.FieldPath:        dbus.MakeVariant(dbus.ObjectPath("/org/freedesktop/systemd1")),
			dbus.FieldInterface:   dbus.MakeVariant("org.freedesktop.systemd1.Manager"),
			dbus.FieldMember:      dbus.MakeVariant("StartTransientUnit"),
		},
		Body: []any{nome, "fail", props, []ausiliaria{}}}
	msg.Headers[dbus.FieldSignature] = dbus.MakeVariant(dbus.SignatureOf(msg.Body...))
	var job dbus.ObjectPath
	err = (<-conn.Send(msg, make(chan *dbus.Call, 1)).Done).Store(&job)
	// i capi che restano a noi: quelli dati all'unità si chiudono qui (li tiene lei)
	inR.Close()
	outW.Close()
	if err != nil {
		inW.Close()
		outR.Close()
		var e dbus.Error
		if errors.As(err, &e) && (strings.Contains(e.Name, "AccessDenied") || strings.Contains(e.Name, "InteractiveAuthorization") ||
			strings.Contains(e.Name, "NotAuthorized") || strings.Contains(e.Name, "PolicyKit")) {
			return nil, nil, motore.Errore("RX-UI-004", e.Name)
		}
		return nil, nil, motore.Errore("RX-UI-004", err.Error())
	}
	return inW, outR, nil
}
