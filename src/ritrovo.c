/*
 * ritrovo.c — i desktop REMOTIX vivi che nessun figlio tiene.
 *
 * Il perche' e il criterio stanno in `ritrovo.h`, che si legge prima.  Qui
 * c'e' solo il come.
 */
#include "ritrovo.h"

#include <dirent.h>
#include <errno.h>
#include <fcntl.h>
#include <gio/gio.h>
#include <pwd.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <unistd.h>

#define NOME_LOGIND "org.freedesktop.login1"
#define PERCORSO_LOGIND "/org/freedesktop/login1"
#define IFACE_MANAGER "org.freedesktop.login1.Manager"
#define IFACE_SESSIONE "org.freedesktop.login1.Session"
/* ⚠ Lo stesso tetto di `sentinella.c`, e per la stessa ragione: la domanda
 *   parte dal ciclo che consegna i fotogrammi. */
#define ATTESA_MS 300
/* Quante sessioni `remotix` si guardano in una volta.  ⚠ Ogni riattacco ne
 * lascia una in piu' col capo morto (`[M]` T2, §5.2 punto b): 256 e' largo. */
#define QUANTE_CANDIDATE 256

struct candidata {
	uid_t uid;
	char id[32];
	char scope[128];
	char utente[257];
};

/* Il contenuto di un file piccolo di /proc, chiuso con '\0'.  -1 se non c'e'. */
static ssize_t leggi_piccolo(const char *percorso, char *buf, size_t cap)
{
	int fd = open(percorso, O_RDONLY | O_CLOEXEC);
	ssize_t n;

	if (fd < 0)
		return -1;
	n = read(fd, buf, cap - 1);
	close(fd);
	if (n < 0)
		return -1;
	buf[n] = '\0';
	return n;
}

/* La cgroup unificata (riga `0::`) del processo, senza il `\n`.  false se non
 * si legge (processo morto nel frattempo: la corsa normale di /proc). */
static bool cgroup_di(pid_t pid, char *dove, size_t cap)
{
	char percorso[64], buf[2048];
	char *r;

	snprintf(percorso, sizeof percorso, "/proc/%ld/cgroup", (long)pid);
	if (leggi_piccolo(percorso, buf, sizeof buf) < 0)
		return false;
	for (r = buf; r && *r; r = strchr(r, '\n') ? strchr(r, '\n') + 1 : NULL) {
		if (strncmp(r, "0::", 3) == 0) {
			size_t n = strcspn(r + 3, "\n");

			if (n >= cap)
				return false;
			memcpy(dove, r + 3, n);
			dove[n] = '\0';
			return true;
		}
	}
	return false;
}

static const char *ultimo_pezzo(const char *cg)
{
	const char *u = strrchr(cg, '/');
	return u ? u + 1 : cg;
}

/* Le sessioni logind col servizio PAM `remotix`.  -1 se logind non risponde. */
static int candidate(struct candidata *v, int cap, char *perche, size_t quanto)
{
	g_autoptr(GError) sbaglio = NULL;
	g_autoptr(GDBusConnection) bus = g_bus_get_sync(G_BUS_TYPE_SYSTEM, NULL, &sbaglio);
	g_autoptr(GVariant) elenco = NULL;
	g_autoptr(GVariantIter) it = NULL;
	const char *id, *nome, *sede, *percorso;
	guint32 uid;
	int n = 0;

	if (!bus) {
		snprintf(perche, quanto, "bus di sistema: %s",
		         sbaglio ? sbaglio->message : "senza motivo");
		return -1;
	}
	elenco = g_dbus_connection_call_sync(bus, NOME_LOGIND, PERCORSO_LOGIND, IFACE_MANAGER,
	                                     "ListSessions", NULL, G_VARIANT_TYPE("(a(susso))"),
	                                     G_DBUS_CALL_FLAGS_NONE, ATTESA_MS, NULL, &sbaglio);
	if (!elenco) {
		snprintf(perche, quanto, "logind ListSessions: %s",
		         sbaglio ? sbaglio->message : "senza motivo");
		return -1;
	}
	g_variant_get(elenco, "(a(susso))", &it);
	while (g_variant_iter_next(it, "(&su&s&s&o)", &id, &uid, &nome, &sede, &percorso)) {
		g_autoptr(GVariant) r = NULL;
		g_autoptr(GVariant) prop = NULL;
		g_autoptr(GVariant) v_serv = NULL;
		g_autoptr(GVariant) v_scope = NULL;

		if (n >= cap)
			break;
		r = g_dbus_connection_call_sync(bus, NOME_LOGIND, percorso,
		                                "org.freedesktop.DBus.Properties", "GetAll",
		                                g_variant_new("(s)", IFACE_SESSIONE),
		                                G_VARIANT_TYPE("(a{sv})"), G_DBUS_CALL_FLAGS_NONE,
		                                ATTESA_MS, NULL, NULL);
		/* ⚠ Sparita fra l'elenco e la domanda: la corsa normale di logind. */
		if (!r)
			continue;
		prop = g_variant_get_child_value(r, 0);
		v_serv = g_variant_lookup_value(prop, "Service", G_VARIANT_TYPE_STRING);
		v_scope = g_variant_lookup_value(prop, "Scope", G_VARIANT_TYPE_STRING);
		if (!v_serv || !v_scope ||
		    strcmp(g_variant_get_string(v_serv, NULL), RITROVO_SERVIZIO_PAM) != 0 ||
		    !g_variant_get_string(v_scope, NULL)[0])
			continue;
		v[n].uid = (uid_t)uid;
		snprintf(v[n].id, sizeof v[n].id, "%s", id);
		snprintf(v[n].scope, sizeof v[n].scope, "%s", g_variant_get_string(v_scope, NULL));
		snprintf(v[n].utente, sizeof v[n].utente, "%s", nome);
		n++;
	}
	return n;
}

/* ⭐ Il cuore: una passata sola su /proc per tutte le candidate.  `solo_uid`
 * (se non (uid_t)-1) restringe a un utente. */
static int cerca(RitrovoDesktop *v, int cap, uid_t solo_uid, char *perche, size_t quanto)
{
	struct candidata *c = calloc(QUANTE_CANDIDATE, sizeof *c);
	int nc, trovati = 0;
	DIR *proc;
	struct dirent *e;

	if (!c) {
		snprintf(perche, quanto, "memoria");
		return -1;
	}
	nc = candidate(c, QUANTE_CANDIDATE, perche, quanto);
	if (nc <= 0) {
		free(c);
		return nc;
	}
	proc = opendir("/proc");
	if (!proc) {
		snprintf(perche, quanto, "/proc: %s", strerror(errno));
		free(c);
		return -1;
	}
	while ((e = readdir(proc)) != NULL) {
		char percorso[64], stat_buf[1024], cg[1024], cg_padre[1024];
		const char *chiusa;
		long pid, ppid = 0, pgrp = 0, sid = 0;
		char stato;
		struct stat st;
		int quale = -1;

		if (e->d_name[0] < '1' || e->d_name[0] > '9')
			continue;
		pid = strtol(e->d_name, NULL, 10);
		snprintf(percorso, sizeof percorso, "/proc/%ld/stat", pid);
		if (leggi_piccolo(percorso, stat_buf, sizeof stat_buf) < 0)
			continue;
		/* ⚠ Il nome sta fra parentesi e puo' contenerne: si parte dall'ULTIMA. */
		chiusa = strrchr(stat_buf, ')');
		if (!chiusa || sscanf(chiusa + 1, " %c %ld %ld %ld", &stato, &ppid, &pgrp, &sid) != 4)
			continue;
		/* 1. capo della propria sessione di processi — la firma di setsid */
		if (sid != pid || stato == 'Z')
			continue;
		snprintf(percorso, sizeof percorso, "/proc/%ld", pid);
		if (stat(percorso, &st) != 0 || st.st_uid == 0)
			continue;
		if (solo_uid != (uid_t)-1 && st.st_uid != solo_uid)
			continue;
		/* 2. dentro la scope di una sessione `remotix` dello stesso utente */
		if (!cgroup_di((pid_t)pid, cg, sizeof cg))
			continue;
		for (int i = 0; i < nc; i++)
			if (c[i].uid == st.st_uid && strcmp(ultimo_pezzo(cg), c[i].scope) == 0) {
				quale = i;
				break;
			}
		if (quale < 0)
			continue;
		/* 3. e il padre FUORI da quella scope: orfano di `setsid --fork`, non la
		 *    shell di un terminale aperto nel desktop */
		if (ppid > 0 && cgroup_di((pid_t)ppid, cg_padre, sizeof cg_padre) &&
		    strcmp(cg_padre, cg) == 0)
			continue;
		/* uno per utente: il primo trovato; gli altri si contano soltanto */
		{
			int gia = -1;

			for (int k = 0; k < trovati; k++)
				if (v[k].uid == st.st_uid)
					gia = k;
			if (gia >= 0 || trovati >= cap)
				continue;
			memset(&v[trovati], 0, sizeof v[trovati]);
			snprintf(v[trovati].utente, sizeof v[trovati].utente, "%s", c[quale].utente);
			v[trovati].uid = st.st_uid;
			snprintf(v[trovati].sessione, sizeof v[trovati].sessione, "%s", c[quale].id);
			v[trovati].palco = (pid_t)pid;
			{
				const char *aperta = strchr(stat_buf, '(');
				size_t n = aperta ? (size_t)(chiusa - aperta - 1) : 0;

				if (n >= sizeof v[trovati].comm)
					n = sizeof v[trovati].comm - 1;
				if (aperta)
					memcpy(v[trovati].comm, aperta + 1, n);
				v[trovati].comm[n] = '\0';
			}
			trovati++;
		}
	}
	closedir(proc);
	for (int k = 0; k < trovati; k++)
		for (int i = 0; i < nc; i++)
			if (c[i].uid == v[k].uid)
				v[k].sessioni++;
	free(c);
	return trovati;
}

int ritrovo_cerca(RitrovoDesktop *v, int cap, char *perche, size_t quanto)
{
	if (perche && quanto)
		perche[0] = '\0';
	if (!v || cap <= 0)
		return 0;
	return cerca(v, cap, (uid_t)-1, perche, quanto);
}

int ritrovo_vivo(uid_t uid, RitrovoDesktop *d)
{
	RitrovoDesktop uno;
	char perche[256] = "";
	int n = cerca(&uno, 1, uid, perche, sizeof perche);

	if (n < 0)
		return -1;
	if (n > 0 && d)
		*d = uno;
	return n > 0 ? 1 : 0;
}
