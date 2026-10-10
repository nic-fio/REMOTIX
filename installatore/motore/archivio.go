package motore

import "strings"

// Il PACCHETTO UNICO di REMOTIX (DECISIONI §10.36): un file `.run` con dentro il motore e i
// pacchetti di REMOTIX per ogni distribuzione della matrice, in packages/<bersaglio>/. Niente
// archivio da aggiungere al sistema: il gestore installa i file così come sono, e le dipendenze le
// prende dagli archivi che la macchina ha già (packaging/rilascio.sh lo costruisce).

// PacchettiRemotix: i pacchetti di REMOTIX (il prodotto, il motore e, sugli rpm con la politica
// targeted, il modulo SELinux): quelli di cui `post-upgrade` annota le versioni.
var PacchettiRemotix = []string{"remotix", "remotix-install", "remotix-selinux"}

// Bersaglio: il nome della distribuzione nel pacchetto unico (debian13, ubuntu2604, fedora44,
// alma10, tumbleweed, leap16, arch): la cartella packages/<bersaglio>/ del .run.
func Bersaglio(a *Ambiente) string {
	m, _ := OsRelease(a)
	id, v := m["ID"], strings.ReplaceAll(m["VERSION_ID"], ".", "")
	switch {
	case id == "arch" || strings.Contains(m["ID_LIKE"], "arch"):
		return "arch"
	case id == "opensuse-tumbleweed":
		return "tumbleweed"
	case id == "opensuse-leap":
		return "leap" + strings.Split(m["VERSION_ID"], ".")[0]
	case id == "almalinux" || id == "rocky" || id == "rhel":
		return "alma" + strings.Split(m["VERSION_ID"], ".")[0]
	}
	return id + v
}
