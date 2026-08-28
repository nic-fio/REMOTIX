#!/usr/bin/env python3
"""10-f2-globali.py — ⭐ CHE COSA VEDE UN CLIENT WAYLAND QUALUNQUE dentro la
sessione remota, e in particolare **se c'e' un `wl_output`**.

    python3 10-f2-globali.py                  (come l'utente della sessione)
    python3 10-f2-globali.py --json
    python3 10-f2-globali.py --certifica      ⭐ senza sessione e senza macchina

---------------------------------------------------------------------------
⛔ PERCHE' ESISTE

Firefox, dentro il desktop remoto, sputa a valanga
`gdk_monitor_get_workarea: assertion 'GDK_IS_MONITOR (monitor)' failed`.
Quell'asserzione fallisce quando GDK **non ha nessun `GdkMonitor`**, e GDK
costruisce i suoi monitor **uno per `wl_output`**.  ⇒ La domanda non e' «GTK
e' rotto»: e' **la sessione annuncia un `wl_output`, si' o no**.

⛔ E la si deve fare **dal posto in cui si trova Firefox**, cioe' da un client
   Wayland qualunque attaccato allo stesso socket — non dal compositore.
   Mutter puo' benissimo avere un monitor in scena e non annunciarlo: sono due
   fatti diversi, e finora sono stati confusi.

---------------------------------------------------------------------------
⭐ COME, e perche' non serve nessuna libreria

Il protocollo Wayland, per **elencare i globali**, e' tre messaggi:

    -> wl_display@1.get_registry(new_id 2)      opcode 1
    -> wl_display@1.sync(new_id 3)              opcode 0
    <- wl_registry@2.global(name, interface, version)   opcode 0, N volte
    <- wl_callback@3.done(serial)               opcode 0  ⇒ l'elenco e' finito

L'intestazione di ogni messaggio e' `<II`: l'oggetto, e poi
`(dimensione << 16) | opcode`.  Le stringhe sono `<I` di lunghezza (col NUL
dentro) seguita dai byte, imbottiti a multiplo di 4.

⭐ `sync` e' la parte che rende la misura una MISURA e non un'attesa: senza,
   «ho letto zero `wl_output`» e «ho smesso di leggere troppo presto» hanno la
   stessa faccia — ed e' esattamente la forma d'errore che `LEZIONI.md` §1.9
   chiama «vuoto e giusto con la stessa faccia».  ⛔ Finche' `done` non e'
   arrivato, l'esito e' `None`, non zero.

---------------------------------------------------------------------------
⛔ `None` NON E' ZERO — i tre esiti

    ok        ho parlato col compositore e l'elenco e' COMPLETO (done arrivato)
    None      ⛔ non ho potuto misurare: niente socket, permesso negato,
              connessione caduta, `done` mai arrivato.  ⚠ Non e' «zero output».

---------------------------------------------------------------------------
⭐ LA TARATURA (`LEZIONI.md` §1.33): il metro si tara PRIMA

Da solo questo file non puo' tararsi contro un valore noto — il numero di
`wl_output` e' proprio quel che non si sa.  ⇒ La taratura si fa **contro un
secondo strumento indipendente**, `org.gnome.Mutter.DisplayConfig`
(`--taratura`): il compositore dichiara quanti monitor logici ha, e questo
elenco dichiara quanti `wl_output` annuncia.  ⛔ Se i due non concordano, e'
proprio quello il difetto — e va detto, non nascosto.

`--certifica` innesta i guasti che il lettore deve saper vedere.
"""

import argparse
import json
import os
import socket
import struct
import subprocess
import sys
import time

# ⛔ Gli identificativi sono fissi e li scegliamo noi: 1 e' sempre wl_display.
ID_DISPLAY = 1
ID_REGISTRY = 2
ID_SYNC = 3


def _msg(oggetto, opcode, carico=b""):
	"""Un messaggio Wayland: intestazione `<II` + carico."""
	dim = 8 + len(carico)
	return struct.pack("<II", oggetto, (dim << 16) | opcode) + carico


def _stringa(buf, off):
	"""Una stringa del protocollo: lunghezza col NUL, byte, imbottitura a 4."""
	(n,) = struct.unpack_from("<I", buf, off)
	off += 4
	s = buf[off:off + n - 1].decode("utf-8", "replace")
	off += (n + 3) & ~3
	return s, off


def leggi_globali(socket_path, scadenza=5.0):
	"""L'elenco dei globali annunciati, o `None` se NON ho potuto misurare.

	Torna `(elenco, motivo)`: `elenco` e' una lista di `(nome, interfaccia,
	versione)` **solo se `done` e' arrivato**; altrimenti `None` e il motivo.
	"""
	try:
		s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
		s.settimeout(scadenza)
		s.connect(socket_path)
	except OSError as e:
		return None, f"non mi collego a {socket_path}: {e}"

	try:
		s.sendall(_msg(ID_DISPLAY, 1, struct.pack("<I", ID_REGISTRY)))
		s.sendall(_msg(ID_DISPLAY, 0, struct.pack("<I", ID_SYNC)))
	except OSError as e:
		s.close()
		return None, f"non ho potuto chiedere l'elenco: {e}"

	buf = b""
	globali = []
	finito = False
	errore = None
	fine = time.monotonic() + scadenza
	while not finito and time.monotonic() < fine:
		try:
			# ⚠ `recvmsg` e non `recv`: il compositore puo' mandare descrittori
			#   insieme ai byte, e un `recv` semplice li lascerebbe in coda.
			dati, _anc, _fl, _ind = s.recvmsg(4096, socket.CMSG_SPACE(16 * 4))
		except socket.timeout:
			break
		except OSError as e:
			errore = f"lettura caduta: {e}"
			break
		if not dati:
			errore = "il compositore ha chiuso il socket"
			break
		buf += dati
		while len(buf) >= 8:
			oggetto, parola = struct.unpack_from("<II", buf, 0)
			dim = parola >> 16
			opcode = parola & 0xFFFF
			if dim < 8 or len(buf) < dim:
				break
			corpo = buf[8:dim]
			buf = buf[dim:]
			if oggetto == ID_REGISTRY and opcode == 0:
				(nome,) = struct.unpack_from("<I", corpo, 0)
				interfaccia, off = _stringa(corpo, 4)
				(versione,) = struct.unpack_from("<I", corpo, off)
				globali.append((nome, interfaccia, versione))
			elif oggetto == ID_SYNC and opcode == 0:
				finito = True
			elif oggetto == ID_DISPLAY and opcode == 0:
				# wl_display.error(object_id, code, message)
				_o, _c = struct.unpack_from("<II", corpo, 0)
				msg, _ = _stringa(corpo, 8)
				errore = f"il compositore ha risposto errore: {msg}"
				finito = True
				globali = None
	s.close()
	if globali is None:
		return None, errore or "errore dal compositore"
	if not finito:
		# ⛔ Qui sta la differenza fra una misura e un'illusione: senza `done`
		#    l'elenco puo' essere monco, e un elenco monco senza `wl_output`
		#    direbbe «non c'e' monitor» su una sessione che ce l'ha.
		return None, errore or "il `done` di wl_display.sync non e' mai arrivato"
	return globali, None


def conta_output(globali):
	if globali is None:
		return None
	return sum(1 for _n, i, _v in globali if i == "wl_output")


def monitor_secondo_mutter(scadenza=10.0):
	"""⭐ IL SECONDO STRUMENTO: quanti monitor logici dichiara Mutter.

	⛔ Serve a TARARE l'elenco dei globali, non a sostituirlo: e' la vista del
	   compositore, e la domanda di questo banco e' che cosa vede il CLIENT.
	   Torna `None` se non ho potuto chiedere.
	"""
	try:
		p = subprocess.run(
			["gdbus", "call", "--session", "--dest", "org.gnome.Mutter.DisplayConfig",
			 "--object-path", "/org/gnome/Mutter/DisplayConfig",
			 "--method", "org.gnome.Mutter.DisplayConfig.GetCurrentState"],
			capture_output=True, text=True, timeout=scadenza)
	except (OSError, subprocess.TimeoutExpired) as e:
		return None, f"gdbus non ha risposto: {e}"
	if p.returncode != 0:
		return None, f"gdbus errore: {p.stderr.strip()[:200]}"
	testo = p.stdout
	# ⚠ Non si analizza la tupla GVariant per intero: si contano i monitor dal
	#   marcatore che OGNI monitor porta nelle sue proprieta'.  Basta al
	#   confronto, e non finge una precisione che non serve.
	#
	# ⛔⛔ E il marcatore e' `is-builtin`, NON `connector-type` — costato una
	#    misura, il 25 agosto 2026.  `connector-type` ce l'hanno i monitor di
	#    un'uscita vera; ⭐ il monitor della nostra cattura e' un **monitor
	#    virtuale** («Meta-0», *Virtual remote monitor*) e quella chiave non
	#    ce l'ha.  ⇒ Il metro contava **zero** su una sessione che il monitor
	#    ce l'aveva, e diceva «i due strumenti non concordano» invece di
	#    «non so leggerlo»: la forma cattiva di `LEZIONI.md` §1.9, un numero
	#    al posto di un `None`.
	if not testo.strip().startswith("(") or "uint32" not in testo:
		return None, "non riconosco la risposta di DisplayConfig"
	return testo.count("'is-builtin'"), None


# ═══════════════════════════════════════════════════════════════════════════
#  ⛔ IL MODO CHE CERTIFICA SE STESSO — i guasti si INNESTANO e si fanno girare
# ═══════════════════════════════════════════════════════════════════════════

def _finto_compositore(percorso, globali, manda_done=True, manda_errore=False):
	"""Un compositore finto che annuncia i globali che gli si dice.

	⭐ E' il valore NOTO della taratura: se il lettore ritrova esattamente
	   quel che questo ha annunciato, il metro misura.
	"""
	import threading

	srv = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
	srv.bind(percorso)
	srv.listen(1)

	def servi():
		try:
			c, _ = srv.accept()
			c.settimeout(3.0)
			try:
				c.recv(4096)
			except OSError:
				pass
			if manda_errore:
				corpo = struct.pack("<II", 1, 0) + _pack_str("finto errore")
				c.sendall(_msg(ID_DISPLAY, 0, corpo))
			else:
				for nome, interfaccia, versione in globali:
					corpo = struct.pack("<I", nome) + _pack_str(interfaccia) \
						+ struct.pack("<I", versione)
					c.sendall(_msg(ID_REGISTRY, 0, corpo))
				if manda_done:
					c.sendall(_msg(ID_SYNC, 0, struct.pack("<I", 1)))
			time.sleep(0.5)
			c.close()
		except OSError:
			pass
		finally:
			srv.close()

	t = threading.Thread(target=servi, daemon=True)
	t.start()
	return t


def _pack_str(s):
	b = s.encode("utf-8") + b"\0"
	n = len(b)
	return struct.pack("<I", n) + b + b"\0" * ((-n) & 3)


def certifica():
	import tempfile

	casi = []

	def caso(nome, atteso, ottenuto, spiega=""):
		ok = atteso == ottenuto
		casi.append((nome, ok, atteso, ottenuto, spiega))
		print(f"   {'⭐ VERDE' if ok else '⛔ ROSSO'}  {nome}: atteso {atteso!r}, "
		      f"ottenuto {ottenuto!r} {spiega}")

	base = tempfile.mkdtemp(prefix="10f2-cert-")

	# ── SANO: tre globali di cui UNO wl_output, con `done` ──────────────────
	p = os.path.join(base, "sano")
	_finto_compositore(p, [(1, "wl_compositor", 6), (2, "wl_output", 4),
	                       (3, "wl_seat", 9)])
	g, mot = leggi_globali(p, 3.0)
	caso("sano · elenco letto", 3, None if g is None else len(g), f"({mot or ''})")
	caso("sano · wl_output contati", 1, conta_output(g))

	# ── GUASTO 1: NESSUN wl_output (e' il caso che si va a cercare) ─────────
	p = os.path.join(base, "senza-output")
	_finto_compositore(p, [(1, "wl_compositor", 6), (3, "wl_seat", 9)])
	g, _ = leggi_globali(p, 3.0)
	caso("guasto · zero wl_output ⇒ 0, NON None", 0, conta_output(g))

	# ── GUASTO 2: DUE wl_output ─────────────────────────────────────────────
	p = os.path.join(base, "due-output")
	_finto_compositore(p, [(2, "wl_output", 4), (5, "wl_output", 4)])
	g, _ = leggi_globali(p, 3.0)
	caso("guasto · due wl_output ⇒ 2", 2, conta_output(g))

	# ── GUASTO 3: elenco MONCO, il `done` non arriva mai ────────────────────
	#    ⛔ E' la forma cattiva: senza questo controllo si leggerebbe «zero
	#       output» da una sessione che non ha finito di parlare.
	p = os.path.join(base, "senza-done")
	_finto_compositore(p, [(1, "wl_compositor", 6)], manda_done=False)
	g, mot = leggi_globali(p, 1.5)
	caso("guasto · niente `done` ⇒ None (non zero)", None, conta_output(g),
	     f"— motivo: {mot}")

	# ── GUASTO 4: il socket non c'e' ────────────────────────────────────────
	g, mot = leggi_globali(os.path.join(base, "che-non-esiste"), 1.0)
	caso("guasto · socket assente ⇒ None", None, conta_output(g),
	     f"— motivo: {mot}")

	# ── GUASTO 5: il compositore risponde ERRORE ────────────────────────────
	p = os.path.join(base, "errore")
	_finto_compositore(p, [], manda_errore=True)
	g, mot = leggi_globali(p, 2.0)
	caso("guasto · wl_display.error ⇒ None", None, conta_output(g),
	     f"— motivo: {mot}")

	# ── GUASTO 6: qualcuno chiude in faccia a meta' elenco ──────────────────
	p = os.path.join(base, "chiuso")

	def chiudi_subito():
		srv = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
		srv.bind(p)
		srv.listen(1)
		c, _ = srv.accept()
		c.close()
		srv.close()

	import threading
	threading.Thread(target=chiudi_subito, daemon=True).start()
	time.sleep(0.2)
	g, mot = leggi_globali(p, 2.0)
	caso("guasto · socket chiuso a meta' ⇒ None", None, conta_output(g),
	     f"— motivo: {mot}")

	# ── RISANATO: si rimette il caso sano e deve tornare verde ──────────────
	p = os.path.join(base, "risanato")
	_finto_compositore(p, [(2, "wl_output", 4)])
	g, _ = leggi_globali(p, 3.0)
	caso("risanato · torna a vedere l'output", 1, conta_output(g))

	rossi = [c for c in casi if not c[1]]
	print()
	print(f"   {len(casi) - len(rossi)} su {len(casi)} come attesi")
	return 0 if not rossi else 1


def principale():
	p = argparse.ArgumentParser()
	p.add_argument("--socket", default="",
	               help="il socket Wayland (def. $XDG_RUNTIME_DIR/$WAYLAND_DISPLAY)")
	p.add_argument("--taratura", action="store_true",
	               help="chiede anche a Mutter quanti monitor logici ha, e "
	                    "confronta: e' il secondo strumento della taratura")
	p.add_argument("--json", action="store_true")
	p.add_argument("--certifica", action="store_true")
	a = p.parse_args()

	if a.certifica:
		return certifica()

	percorso = a.socket
	if not percorso:
		run = os.environ.get("XDG_RUNTIME_DIR", "")
		disp = os.environ.get("WAYLAND_DISPLAY", "wayland-0")
		if not run:
			print("⛔ NON MISURO: XDG_RUNTIME_DIR non c'e'", file=sys.stderr)
			return 2
		percorso = disp if disp.startswith("/") else os.path.join(run, disp)

	globali, motivo = leggi_globali(percorso)
	n_out = conta_output(globali)
	esito = {
		"socket": percorso,
		"globali": None if globali is None else
			[{"nome": n, "interfaccia": i, "versione": v} for n, i, v in globali],
		"n_globali": None if globali is None else len(globali),
		"wl_output": n_out,
		"motivo": motivo,
	}
	if a.taratura:
		n_mon, mot_mon = monitor_secondo_mutter()
		esito["monitor_mutter"] = n_mon
		esito["motivo_mutter"] = mot_mon
		if n_out is not None and n_mon is not None:
			esito["concordano"] = (n_out == n_mon)

	if a.json:
		print(json.dumps(esito, ensure_ascii=False))
	else:
		if globali is None:
			print(f"⛔ NON MISURATO: {motivo}")
		else:
			for n, i, v in globali:
				print(f"   {n:4d}  {i}  v{v}")
			print(f"\n   globali: {len(globali)} · ⭐ wl_output: {n_out}")
		if a.taratura:
			print(f"   monitor secondo Mutter: {esito.get('monitor_mutter')} "
			      f"({esito.get('motivo_mutter') or 'letto'})")
			if "concordano" in esito:
				print("   ⭐ i due strumenti CONCORDANO" if esito["concordano"]
				      else "   ⛔ i due strumenti NON concordano")
	return 0 if globali is not None else 1


if __name__ == "__main__":
	sys.exit(principale())
