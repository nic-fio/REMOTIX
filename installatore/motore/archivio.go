package motore

import "strings"

// REMOTIX's SINGLE PACKAGE (DECISIONI §10.36): a `.run` file containing the engine and the
// REMOTIX packages for every distribution of the matrix, in packages/<bersaglio>/. No
// repository to add to the system: the manager installs the files as they are, and takes the
// dependencies from the repositories the machine already has (packaging/rilascio.sh builds it).

// PacchettiRemotix: REMOTIX's packages (the product, the engine and, on rpm with the targeted
// policy, the SELinux module): those whose versions `post-upgrade` records.
var PacchettiRemotix = []string{"remotix", "remotix-install", "remotix-selinux"}

// Bersaglio: the name of the distribution in the single package (debian13, ubuntu2604, fedora44,
// alma10, tumbleweed, leap16, arch): the folder packages/<bersaglio>/ of the .run.
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
