#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===========================================================================
13-w2 — ⛔⛔ LA TRAPPOLA DEL LOGOUT DI XFCE
===========================================================================

⛔⛔ QUESTO PROGRAMMA GIRA **SOLO DENTRO LA SCATOLA `rete11-xfce`**, e si lancia
    dall'ospite col suo lanciatore, che fa UNA cosa sola — `podman exec`:

        bash 13-w2-la-trappola-del-logout.sh                    # la prova sana
        bash 13-w2-la-trappola-del-logout.sh --senza-xfconf     # guasto (a)
        bash 13-w2-la-trappola-del-logout.sh --senza-cinture    # guasto (b)
        bash 13-w2-la-trappola-del-logout.sh --senza-variabile  # la misura M2
        bash 13-w2-la-trappola-del-logout.sh --certifica        # il giudice, a secco

    ⛔ Perche' conta: questo banco fa scattare APPOSTA una trappola che esegue
       `loginctl terminate-session ''`.  Fuori dalla scatola quella riga
       porterebbe via una sessione vera.  ⇒ Prima di toccare qualunque cosa il
       programma VERIFICA di essere dentro un contenitore podman (e non sull'
       ospite) e che il lanciatore l'abbia chiamato per la scatola giusta; se
       no esce **3** senza aver fatto niente.  Tutto quel che crea (l'inquilino,
       l'involucro, la chiave xfconf tolta) sta DENTRO la scatola e ne esce nel
       `finally`.

La trappola — `STUDI.md` §xfce §9.2:

    se `XFCE4_SESSION_COMPOSITOR` non contiene SIA `labwc` SIA `--session`, al
    logout `xfce4-session` esegue `loginctl terminate-session ''` — cioe'
    ammazza la sessione logind DI CHI LO HA AVVIATO: la sessione di REMOTIX.

Il prodotto porta DUE cinture (`src/sessione.c`):

    1. la variabile  `XFCE4_SESSION_COMPOSITOR=labwc -m --session xfce4-session`
                     (`SESSIONE_RIGA_XFCE`, `src/sessione.h:148`), nell'ambiente
                     di labwc e quindi di `xfce4-session`
    2. la chiave     xfconf `xfce4-session` `/general/WaylandLogoutCommand` =
                     `/bin/true`, scritta e RILETTA — ha la precedenza (§9.2).
                     ⭐ Dalla fase 15 (D-017) e' nel xfconf della SESSIONE: una
                     proprieta' BLOCCATA (`locked="*"`) nel file
                     `$XDG_RUNTIME_DIR/remotix/xdg-xfce/xfce4/xfconf/
                     xfce-perchannel-xml/xfce4-session.xml`, che `xfconfd`
                     legge perche' un drop-in del prodotto gli mette quella
                     cartella in testa a `XDG_CONFIG_DIRS`; il canale
                     dell'utente non si tocca

---------------------------------------------------------------------------
⭐ I QUATTRO MODI, e che cosa ciascuno si aspetta
---------------------------------------------------------------------------

  modo               xfconf   variabile        la sessione logind al logout
  -----------------  -------  ---------------  ----------------------------------
  (sano)             c'e'     giusta           ⭐ RESTA            ⇒ 0
  --senza-xfconf     TOLTA    giusta           ⭐ RESTA (la variabile basta)
  --senza-variabile  c'e'     `labwc` secca    ⭐ RESTA (la chiave basta: M2)
  --senza-cinture    TOLTA    `labwc` secca    ⛔ DEVE CADERE

⛔⛔ COL GUASTO INNESTATO L'ESITO SI LEGGE AL CONTRARIO — la convenzione di
    `11-gancio.sh`: *«una maglia col guasto innestato esce 0 quando il guasto
    E' STATO VISTO»* (`ha_visto_il_guasto`).
    · `--senza-xfconf` e `--senza-variabile`: il giro sano direbbe ROSSO —
      «una cintura manca» — perche' le cinture si LEGGONO, non si deducono dal
      fatto che la sessione resti.  ⭐ Senza quella lettura una cintura sola
      avrebbe lo stesso aspetto di due, e il banco sarebbe verde su un prodotto
      che ne ha perso una.  ⇒ Guasto visto = 0, a patto che la sessione sia
      RESTATA: se cade con una cintura sola in piedi, quella cintura da sola
      non regge, §9.2 e' smentita, ed e' **1** detto per nome.
    · `--senza-cinture`: il giro sano direbbe ROSSO — «la sessione e' caduta»
      ⇒ guasto visto = 0.
      ⛔⛔ E SE NON CADE, IL BANCO NON DIMOSTRA NIENTE: vuol dire che su questa
          scatola la trappola non morde (o morde un'altra sessione), e allora
          «la sessione resta» nel giro sano non e' merito delle cinture.
          ⇒ esito **3**, e lo si dice.  ⚠ E' il giro che da' valore a tutti
          gli altri: va fatto girare, non immaginato.

---------------------------------------------------------------------------
⛔ «PROVA A SMENTIRTI» — le tre domande, e la risposta a ciascuna
---------------------------------------------------------------------------

1. ⛔ LA SESSIONE CHE GUARDO E' QUELLA DELLA PROVA?
   `terminate-session ''` colpisce la sessione DEL CHIAMANTE, e logind la
   ricava dal cgroup del processo.  ⇒ La sessione giudicata si legge dal
   cgroup di **quel** `xfce4-session` (`/proc/<pid>/cgroup` → `session-X.scope`),
   non da `loginctl list-sessions` e non «l'ultima dell'utente».  E si
   verifica che sia nostra con due fatti indipendenti: `Name` e' l'inquilino
   creato NUOVO da questo banco, e il `Leader` e' il `remotix-figlio
   --figlio-interno <inquilino>` (e' lui che la apre con `pam_open_session`,
   `src/figlio.c`).  Anche `labwc` deve stare nella stessa.  Se una sola di
   queste manca: **3**.
   ⚠ E se `xfce4-session` non stesse in NESSUNA sessione, la trappola non
     avrebbe bersaglio: si dice, ed e' **3**.

2. ⛔ E SE IL LOGOUT NON PARTE PROPRIO?  (il 0 falso)
   Una sessione che «resta» dopo un logout che non c'e' stato e' il verde piu'
   comodo di tutti (`LEZIONI.md` §1.44).  ⇒ Due fatti, prima di giudicare:
     · ⭐ IL DESKTOP E' SPARITO: il pid di QUEL `xfce4-session` e quello di
       QUEL `labwc` non ci sono piu' (si aspetta l'EVENTO, tetto dichiarato
       `--attesa-logout`, e si stampa quanto ci ha messo);
     · ⭐ E' SPARITO PASSANDO DAL LOGOUT, non morendo: sul bus d'utente si
       ascolta `StateChanged` e si pretende di vedere lo stato 3 (Shutdown) o
       4 (Phase2) — `STUDI.md` §xfce §9.5.  La trappola sta alla FINE di quel
       percorso: un `xfce4-session` morto di un segnale non ci arriva, e una
       sessione che resta dopo una morte non prova niente.
   Se manca uno dei due: **3**, mai un giudizio.

3. ⛔ E L'ORECCHIO SUL BUS, SENTE?  (vuoto e proibito, `LEZIONI.md` §1.9)
   «Non ho visto lo Shutdown» ha lo stesso aspetto di «non ho sentito
   niente».  ⇒ Il controllo positivo e' sullo stesso strumento: l'ascoltatore
   deve aver visto passare **la nostra stessa chiamata `Logout`**.  Se non
   l'ha vista e' sordo, e un orecchio sordo vale **3**.
   E lo stesso per le altre letture:
     · la variabile si legge da `/proc/<pid>/environ` e vale solo se
       l'ambiente letto contiene `XDG_RUNTIME_DIR` (se no: non l'ho letto);
     · la chiave xfconf «assente» vale solo col messaggio «does not exist» di
       `xfconf-query` (LC_ALL=C); qualunque altro errore e' «non lo so».  E
       dopo averla tolta si RILEGGE (§xfce §10.6: la scrittura riesce anche
       quando non riesce);
     · «la sessione e' caduta» vale solo col «No session … known» di
       `loginctl`, o col figlio (il Leader) morto; e prima del logout la
       stessa lettura deve averla descritta col figlio vivo.  ⚠ NON con
       `State=closing`: e' lo stato normale del prodotto su ogni desktop.

---------------------------------------------------------------------------
⭐ COME SI INNESTANO I GUASTI — e perche' non si tocca il prodotto
---------------------------------------------------------------------------

  · la chiave xfconf — ⛔ FASE 15: NON piu' `xfconf-query -r` a desktop su.
    La chiave e' BLOCCATA (D-017): `xfconfd` rifiuta di toglierla, e anche
    riuscendoci `xfce4-session` non se ne accorgerebbe — `[R]` libxfconf
    legge TUTTO il canale quando lo apre (`xfconf_cache_prefetch`,
    `xfconf-channel.c:271`) e poi sente solo i cambi che il demone annuncia.
    ⇒ Si innesta PRIMA della nascita: nella casa dell'inquilino nuovo, un
    drop-in `~/.config/systemd/user/xfconfd.service.d/` con un nome che viene
    DOPO quello del prodotto (`zzzz-…` > `zz-remotix-sessione.conf`: i drop-in
    di tutte le cartelle si applicano in ordine di nome, e l'ultimo
    `Environment=` vince) rimette `XDG_CONFIG_DIRS=/etc/xdg` ⇒ il file della
    sessione non si legge, e la chiave e' ASSENTE (l'inquilino e' nuovo).
    ⚠ Il controllo positivo non e' piu' «prima di toglierla si legge
    `/bin/true`» ma: il PRODOTTO l'ha scritta — `/bin/true`, bloccata — nel
    file della sessione (letto dal disco), e la rilettura con `xfconf-query`
    dice ASSENTE (l'innesto ha morso).  Il drop-in porta una firma, e se ne
    va con la casa dell'inquilino.
  · la variabile: il prodotto la mette nell'ambiente di labwc, e `labwc
    --session xfce4-session` cerca `xfce4-session` nel `PATH` che il figlio
    compone (`/usr/local/bin` prima di `/usr/bin`, `src/figlio.c`).  ⇒ Dentro
    la scatola si mette un INVOLUCRO `/usr/local/bin/xfce4-session` che, SOLO
    per l'inquilino di questo banco, riscrive la variabile in `labwc` (senza
    `--session`) e poi `exec` il vero.  ⭐ Il processo resta `xfce4-session`
    (e' un `exec`), e l'innesto si VERIFICA leggendo il suo ambiente vero.
    ⛔ L'involucro porta una firma; un file che NON la porta non si tocca mai
       (esito 3), e uno che la porta rimasto da un giro morto si toglie prima
       di cominciare — o il giro sano di domani nascerebbe avvelenato.

---------------------------------------------------------------------------
GLI ESITI
---------------------------------------------------------------------------
  0  ⭐ ho guardato e regge — o, col guasto innestato, il guasto e' stato VISTO
  1  ⛔ ho guardato e NON regge: una cintura manca (giro sano), la sessione e'
     caduta con le cinture (giro sano), o e' caduta con UNA cintura in piedi
  3  ⛔ non ho potuto guardare, con la ragione scritta: fuori dalla scatola,
     il desktop non e' nato, la sessione non e' provata nostra, una lettura
     muta, il logout non e' avvenuto (o non e' passato dallo Shutdown), l'
     orecchio sul bus sordo, l'innesto non ha morso — ⭐ o, con
     `--senza-cinture`, la sessione NON e' caduta: il banco non dimostra niente
  2  solo per un uso sbagliato delle opzioni (lo da' `argparse`)
===========================================================================
"""
import argparse
import importlib.util
import json
import os
import pwd
import re
import shutil
import subprocess
import sys
import tempfile
import time

# ---------------------------------------------------------------------------
# LE COSTANTI, ciascuna con la sua casa
# ---------------------------------------------------------------------------
SCATOLA = "rete11-xfce"
# ⛔ La riga del prodotto: `SESSIONE_RIGA_XFCE`, `src/sessione.h:148`.  Si
#    stampa accanto a quel che si legge, ma ⭐ il giudizio usa la REGOLA di
#    `xfce4-session` (contiene `labwc` e `--session`), non l'uguaglianza: una
#    riga diversa e innocua non e' un rosso.
RIGA_PRODOTTO = "labwc -m --session xfce4-session"     # -m: D-007, fase 15
RIGA_TRAPPOLA = "labwc"           # quella che l'involucro mette: senza --session
CANALE = "xfce4-session"
CHIAVE = "/general/WaylandLogoutCommand"
VALORE_CINTURA = "/bin/true"
BUS_NOME = "org.xfce.SessionManager"
BUS_PERCORSO = "/org/xfce/SessionManager"
BUS_INTERFACCIA = "org.xfce.Session.Manager"   # ⚠ nome ≠ interfaccia, §9.5
STATO_IDLE = 1
STATI_SPEGNIMENTO = (3, 4)                      # Shutdown, Phase2
VERO = "/usr/bin/xfce4-session"
INVOLUCRO = "/usr/local/bin/xfce4-session"
FIRMA_INVOLUCRO = "# 13-w2: involucro innestato dal banco della trappola del logout"
ASSENTE = "(assente)"
# ⭐ FASE 15, D-017 — dove il prodotto scrive la chiave (xfconf della
#    SESSIONE) e il drop-in con cui il banco la rende illeggibile a xfconfd
FILE_SESSIONE = ("/run/user/%d/remotix/xdg-xfce/xfce4/xfconf/xfce-perchannel-xml/"
                 "xfce4-session.xml")
DROPIN_BANCO = "/home/%s/.config/systemd/user/xfconfd.service.d/zzzz-13w2-senza-xfconf.conf"
FIRMA_DROPIN = "# 13-w2: senza-xfconf — il xfconf della sessione non si legge"

# ⭐ Che cosa ogni modo toglie, e che cosa si aspetta.  Una tabella sola:
#    il giudice e la messa in scena la leggono tutt'e due (§1.47).
MODI = {
    "sano":            {"xfconf": True,  "variabile": True,  "deve_cadere": False},
    "senza-xfconf":    {"xfconf": False, "variabile": True,  "deve_cadere": False},
    "senza-variabile": {"xfconf": True,  "variabile": False, "deve_cadere": False},
    "senza-cinture":   {"xfconf": False, "variabile": False, "deve_cadere": True},
}


# ---------------------------------------------------------------------------
# LE CINTURE — due predicati puri
# ---------------------------------------------------------------------------
def variabile_regge(v):
    """⭐ La regola di `xfce4-session` (§9.2), non l'uguaglianza con la nostra."""
    return (v is not None and v != ASSENTE
            and "labwc" in v and "--session" in v)


def xfconf_regge(x):
    """⭐ Solo `/bin/true`: una chiave presente ma con un altro comando non e'
       una cintura — potrebbe essere proprio il `loginctl` che si temeva."""
    return x == VALORE_CINTURA


# ---------------------------------------------------------------------------
# ⭐ IL GIUDICE — funzione PURA, cosi' `--certifica` la prova senza toccare
#    niente.  Torna `(esito, motivi)`.
#
# `m` ha queste voci (⛔ `None` vuol dire SEMPRE «non ho potuto leggere»):
#   desktop_su        bool  xfce4-session e' nato ed e' arrivato a Idle
#   sessione          str   la sessione di xfce4-session, dal suo cgroup
#   legata            bool  Name = inquilino, Leader = il suo figlio, labwc dentro
#   perche_legata     str
#   variabile         str | ASSENTE | None   dall'ambiente VERO di xfce4-session
#   xfconf_prima      str | ASSENTE | None   letta prima dell'innesto
#   xfconf            str | ASSENTE | None   letta subito prima del logout
#   desktop_sparito   bool  QUEL xfce4-session e QUEL labwc non ci sono piu'
#   spegnimento       "visto" | "non-visto" | "sordo"
#   sessione_dopo     "viva" | "caduta" | None
# ---------------------------------------------------------------------------
def giudica(modo, m):
    atteso = MODI[modo]
    motivi = []

    # --- le guardie: senza queste, qualunque cosa segua e' un'opinione -----
    if not m.get("desktop_su"):
        return 3, ["il desktop XFCE non e' nato (o non e' arrivato a Idle): "
                   "non c'era niente da cui fare logout"]
    if not m.get("sessione"):
        return 3, ["⛔ `xfce4-session` non sta in NESSUNA sessione logind: la "
                   "trappola non avrebbe bersaglio, e «resta»/«cade» non "
                   "vorrebbero dire niente"]
    if not m.get("legata"):
        return 3, ["⛔ la sessione %s NON e' provata nostra: %s"
                   % (m.get("sessione"), m.get("perche_legata") or "?")]
    if m.get("variabile") is None:
        return 3, ["⛔ non ho potuto leggere l'ambiente di xfce4-session: la "
                   "prima cintura e' «non lo so», non «c'e'»"]
    if m.get("xfconf") is None:
        return 3, ["⛔ `xfconf-query` non ha risposto in modo leggibile: la "
                   "seconda cintura e' «non lo so», non «c'e'»"]

    v_ok = variabile_regge(m["variabile"])
    x_ok = xfconf_regge(m["xfconf"])
    descr = ("variabile «%s» (%s) · xfconf «%s» (%s)"
             % (m["variabile"], "regge" if v_ok else "NON regge",
                m["xfconf"], "regge" if x_ok else "NON regge"))

    if modo == "sano":
        # ⛔ Il rosso di una cintura mancante si da' SUBITO, e vale anche se
        #    la sessione poi resta: resterebbe per l'altra cintura, e un
        #    prodotto con una cintura sola e' un prodotto a un guasto dal
        #    disastro.  ⇒ E' la lettura che vede (a) e (c).
        if not (v_ok and x_ok):
            manca = []
            if not v_ok:
                manca.append("la VARIABILE (%s)" % m["variabile"])
            if not x_ok:
                manca.append("la chiave XFCONF (%s)" % m["xfconf"])
            return 1, ["⛔ una cintura MANCA a sessione accesa: " +
                       " e ".join(manca), descr]
    else:
        # ⛔ L'INNESTO DEVE AVER MORSO, e su tutt'e due i lati: la cintura
        #    tolta si legge tolta, e quella lasciata si legge in piedi.
        #    Altrimenti la scena non e' quella che il modo dichiara (§1.52).
        if not atteso["xfconf"]:
            if m.get("xfconf_prima") != VALORE_CINTURA:
                return 3, ["⛔ il PRODOTTO non ha scritto la chiave xfconf "
                           "«%s» (bloccata) nel file della sessione: leggo "
                           "«%s» — o non l'ha scritta (e allora e' il giro "
                           "SANO a doverlo dire), o il lettore non la sa "
                           "leggere ⇒ il controllo positivo manca"
                           % (VALORE_CINTURA, m.get("xfconf_prima"))]
            if m["xfconf"] != ASSENTE:
                return 3, ["⛔ l'innesto NON ha morso: tolta la chiave, la "
                           "rilettura dice ancora «%s» (§xfce §10.6)"
                           % m["xfconf"]]
        elif not x_ok:
            return 3, ["⛔ la scena non e' quella dichiarata: la chiave xfconf "
                       "doveva restare in piedi e dice «%s»" % m["xfconf"]]
        if not atteso["variabile"]:
            if m["variabile"] != RIGA_TRAPPOLA:
                return 3, ["⛔ l'innesto NON ha morso: l'ambiente vero di "
                           "xfce4-session dice «%s», non «%s» — l'involucro "
                           "non e' stato usato" % (m["variabile"],
                                                   RIGA_TRAPPOLA)]
        elif not v_ok:
            return 3, ["⛔ la scena non e' quella dichiarata: la variabile "
                       "doveva restare giusta e dice «%s»" % m["variabile"]]

    # --- il logout DEVE essere avvenuto, e passando dallo Shutdown ---------
    if not m.get("desktop_sparito"):
        return 3, ["⛔ il desktop NON e' sparito dopo la richiesta di logout: "
                   "il logout non e' avvenuto, e una sessione che «resta» qui "
                   "sarebbe un verde falso", descr]
    sp = m.get("spegnimento")
    if sp == "sordo":
        return 3, ["⛔ l'orecchio sul bus e' SORDO: non ha visto passare "
                   "nemmeno la nostra chiamata `Logout` — quindi «nessuno "
                   "Shutdown» non si puo' distinguere da «non ho sentito» "
                   "(`LEZIONI.md` §1.9)", descr]
    if sp != "visto":
        return 3, ["⛔ il desktop e' sparito SENZA passare dallo Shutdown "
                   "(StateChanged 3/4 mai visto, e l'orecchio sentiva): e' "
                   "morto, non uscito — e la trappola sta in fondo al logout",
                   descr]
    dopo = m.get("sessione_dopo")
    if dopo is None:
        return 3, ["⛔ `loginctl` non ha saputo dire che fine ha fatto la "
                   "sessione %s dopo il logout" % m["sessione"], descr]

    # --- i giudizi -----------------------------------------------------------
    s = m["sessione"]
    if modo == "sano":
        if dopo == "viva":
            return 0, ["⭐ le due cinture erano in piedi, il logout e' "
                       "avvenuto passando dallo Shutdown, e la sessione logind "
                       "%s di REMOTIX e' RESTATA" % s, descr]
        return 1, ["⛔⛔ la sessione logind %s di REMOTIX e' CADUTA al logout, "
                   "CON le due cinture in piedi" % s, descr]

    if atteso["deve_cadere"]:
        if dopo == "caduta":
            motivi = ["⭐ IL GUASTO E' STATO VISTO: senza cinture la sessione "
                      "logind %s e' caduta al logout — la trappola di §9.2 "
                      "e' vera su questa scatola, e questo banco SA vederla "
                      "cadere" % s, descr]
            return 0, motivi
        return 3, ["⛔⛔ SENZA CINTURE LA SESSIONE %s NON E' CADUTA: la "
                   "trappola qui non morde, quindi il banco NON DIMOSTRA "
                   "NIENTE — e il verde del giro sano non e' merito delle "
                   "cinture" % s, descr]

    # una cintura sola in piedi: il guasto e' visto dalla lettura, e la
    # sessione deve restare per merito dell'altra
    tolta = "la chiave xfconf" if not atteso["xfconf"] else "la variabile"
    rimasta = "la variabile" if not atteso["xfconf"] else "la chiave xfconf"
    if dopo == "viva":
        return 0, ["⭐ IL GUASTO E' STATO VISTO: tolta %s, la lettura delle "
                   "cinture la trova mancante (il giro sano direbbe ROSSO)"
                   % tolta,
                   "⭐ e %s da sola REGGE: la sessione logind %s e' restata"
                   % (rimasta, s), descr]
    return 1, ["⛔⛔ %s da sola NON REGGE: tolta %s, la sessione logind %s "
               "e' CADUTA al logout — `STUDI.md` §xfce §9.2 va corretta"
               % (rimasta.upper(), tolta, s), descr]


# ---------------------------------------------------------------------------
# --certifica: il giudice contro casi scritti a mano
# ---------------------------------------------------------------------------
def _sano(**cambi):
    m = {"desktop_su": True, "sessione": "c9", "legata": True,
         "perche_legata": "", "variabile": RIGA_PRODOTTO,
         "xfconf_prima": VALORE_CINTURA, "xfconf": VALORE_CINTURA,
         "desktop_sparito": True, "spegnimento": "visto",
         "sessione_dopo": "viva"}
    m.update(cambi)
    return m


def certifica():
    casi = [
        # (nome, modo, misure, esito atteso)
        ("sano: tutto in piedi, la sessione resta", "sano", _sano(), 0),
        ("sano: manca la chiave xfconf", "sano",
         _sano(xfconf=ASSENTE), 1),
        ("sano: la chiave c'e' ma e' un altro comando", "sano",
         _sano(xfconf="loginctl terminate-session ''"), 1),
        ("sano: la variabile senza --session", "sano",
         _sano(variabile="labwc"), 1),
        ("sano: la variabile assente", "sano", _sano(variabile=ASSENTE), 1),
        ("sano: variabile con opzioni in piu' (regge per la regola)", "sano",
         _sano(variabile="labwc --config-dir /x --session xfce4-session"), 0),
        ("sano: la sessione cade con le cinture", "sano",
         _sano(sessione_dopo="caduta"), 1),
        ("⛔ sano: il LOGOUT NON E' AVVENUTO (il 0 falso)", "sano",
         _sano(desktop_sparito=False), 3),
        ("⛔ sano: sparito senza Shutdown (morto, non uscito)", "sano",
         _sano(spegnimento="non-visto"), 3),
        ("⛔ sano: orecchio sordo", "sano", _sano(spegnimento="sordo"), 3),
        ("⛔ sano: la sessione non e' provata nostra", "sano",
         _sano(legata=False, perche_legata="Name=altro"), 3),
        ("⛔ sano: xfce4-session fuori da ogni sessione", "sano",
         _sano(sessione=None), 3),
        ("sano: ambiente illeggibile", "sano", _sano(variabile=None), 3),
        ("sano: xfconf muto", "sano", _sano(xfconf=None), 3),
        ("sano: loginctl muto dopo", "sano", _sano(sessione_dopo=None), 3),
        ("sano: il desktop non e' nato", "sano", _sano(desktop_su=False), 3),
        # (a)
        ("(a) senza-xfconf: visto, e la variabile regge", "senza-xfconf",
         _sano(xfconf=ASSENTE), 0),
        ("(a) senza-xfconf: la variabile da sola NON regge", "senza-xfconf",
         _sano(xfconf=ASSENTE, sessione_dopo="caduta"), 1),
        ("(a) innesto non morso: la chiave si rilegge ancora", "senza-xfconf",
         _sano(), 3),
        ("(a) manca il controllo positivo di prima", "senza-xfconf",
         _sano(xfconf=ASSENTE, xfconf_prima=ASSENTE), 3),
        ("(a) il logout non e' avvenuto", "senza-xfconf",
         _sano(xfconf=ASSENTE, desktop_sparito=False), 3),
        # (c) = M2
        ("(c) senza-variabile: visto, e la chiave regge (M2)",
         "senza-variabile", _sano(variabile=RIGA_TRAPPOLA), 0),
        ("(c) senza-variabile: la chiave da sola NON regge",
         "senza-variabile",
         _sano(variabile=RIGA_TRAPPOLA, sessione_dopo="caduta"), 1),
        ("(c) involucro non usato", "senza-variabile", _sano(), 3),
        # (b)
        ("(b) senza-cinture: la sessione CADE ⇒ guasto visto",
         "senza-cinture",
         _sano(xfconf=ASSENTE, variabile=RIGA_TRAPPOLA,
               sessione_dopo="caduta"), 0),
        ("⛔ (b) senza-cinture: NON cade ⇒ il banco non dimostra niente",
         "senza-cinture",
         _sano(xfconf=ASSENTE, variabile=RIGA_TRAPPOLA), 3),
        ("(b) innesto a meta': la variabile e' ancora giusta",
         "senza-cinture",
         _sano(xfconf=ASSENTE, sessione_dopo="caduta"), 3),
        ("(b) innesto a meta': la chiave c'e' ancora", "senza-cinture",
         _sano(variabile=RIGA_TRAPPOLA, sessione_dopo="caduta"), 3),
        ("⛔ (b) cade, ma senza Shutdown visto", "senza-cinture",
         _sano(xfconf=ASSENTE, variabile=RIGA_TRAPPOLA,
               sessione_dopo="caduta", spegnimento="non-visto"), 3),
        ("⛔ (b) cade, ma l'orecchio e' sordo", "senza-cinture",
         _sano(xfconf=ASSENTE, variabile=RIGA_TRAPPOLA,
               sessione_dopo="caduta", spegnimento="sordo"), 3),
        ("(b) il logout non e' avvenuto", "senza-cinture",
         _sano(xfconf=ASSENTE, variabile=RIGA_TRAPPOLA,
               desktop_sparito=False), 3),
    ]
    sbagli = 0
    print("== 13-w2 --certifica: il giudice contro %d casi scritti a mano ==\n"
          % len(casi))
    for nome, modo, m, atteso in casi:
        esito, motivi = giudica(modo, m)
        ok = esito == atteso
        sbagli += 0 if ok else 1
        print("  %s  %-62s esito=%d  atteso %d"
              % ("OK " if ok else "NO ", nome, esito, atteso))
        if not ok:
            print("       ⛔ %s" % motivi[0])
    # ⭐ E le letture pure, col loro controllo positivo.
    prove_lettura = [
        ("ambiente con la variabile",
         b"HOME=/h\0XDG_RUNTIME_DIR=/run/user/5\0XFCE4_SESSION_COMPOSITOR="
         b"labwc -m --session xfce4-session\0", RIGA_PRODOTTO),
        ("ambiente senza la variabile", b"HOME=/h\0XDG_RUNTIME_DIR=/r\0",
         ASSENTE),
        ("⛔ ambiente vuoto (illeggibile) ≠ assente", b"", None),
        ("⛔ ambiente senza XDG_RUNTIME_DIR ≠ assente", b"HOME=/h\0", None),
    ]
    for nome, grezzo, atteso in prove_lettura:
        letto = variabile_da_ambiente(grezzo)
        ok = letto == atteso
        sbagli += 0 if ok else 1
        print("  %s  %-62s letto=%r" % ("OK " if ok else "NO ", nome, letto))
    prove_orecchio = [
        ("orecchio: chiamata vista + Shutdown", [
            '{"type":"method_call","member":"Logout","payload":{"type":"bb","data":[false,false]}}',
            '{"type":"signal","member":"StateChanged","payload":{"type":"uu","data":[1,3]}}'],
         "visto"),
        ("orecchio: chiamata vista, nessuno Shutdown", [
            '{"type":"method_call","member":"Logout"}',
            '{"type":"signal","member":"StateChanged","payload":{"type":"uu","data":[1,2]}}'],
         "non-visto"),
        ("⛔ orecchio: Shutdown ma NON la nostra chiamata ⇒ sordo", [
            '{"type":"signal","member":"StateChanged","payload":{"type":"uu","data":[1,3]}}'],
         "sordo"),
        ("orecchio: niente", [], "sordo"),
    ]
    for nome, righe, atteso in prove_orecchio:
        letto = ascolta_righe(righe)
        ok = letto == atteso
        sbagli += 0 if ok else 1
        print("  %s  %-62s letto=%s" % ("OK " if ok else "NO ", nome, letto))
    # ⭐ FASE 15, D-017 — la lettura del file della sessione (il controllo
    #    positivo dell'innesto (a)), su file scritti come li scrive il prodotto
    global FILE_SESSIONE
    vero_file = FILE_SESSIONE
    cartella = tempfile.mkdtemp(prefix="13-w2-certifica-")
    riga = ('<property name="WaylandLogoutCommand" type="string" value="/bin/true"%s/>')
    prove_file = [
        ("file della sessione: bloccata", riga % ' locked="*"', VALORE_CINTURA),
        ("⛔ file della sessione: NON bloccata", riga % "",
         VALORE_CINTURA + " (NON bloccata)"),
        ("file della sessione senza la chiave", "", ASSENTE),
        ("⛔ file illeggibile ≠ assente", None, None),
        ("nessun file", False, ASSENTE),
    ]
    try:
        for i, (nome, dentro, atteso) in enumerate(prove_file):
            FILE_SESSIONE = os.path.join(cartella, "s%d-%%d.xml" % i)
            if dentro is None:
                with open(FILE_SESSIONE % 0, "w") as fo:
                    fo.write("<channel><property")
            elif dentro is not False:
                with open(FILE_SESSIONE % 0, "w") as fo:
                    fo.write('<?xml version="1.0"?><channel name="xfce4-session" '
                             'version="1.0"><property name="general" type="empty">%s'
                             '</property></channel>' % dentro)
            letto = xfconf_scritta_dal_prodotto(0)
            ok = letto == atteso
            sbagli += 0 if ok else 1
            print("  %s  %-62s letto=%r" % ("OK " if ok else "NO ", nome, letto))
    finally:
        FILE_SESSIONE = vero_file
        shutil.rmtree(cartella, ignore_errors=True)
    print()
    if sbagli:
        print("⛔⛔ %d casi sbagliati: il giudice NON e' certificato" % sbagli)
        return 1
    print("⭐ il giudice e le letture danno quel che devono in tutti i casi")
    return 0


# ---------------------------------------------------------------------------
# LE LETTURE PURE (le usa anche --certifica)
# ---------------------------------------------------------------------------
def variabile_da_ambiente(grezzo):
    """`XFCE4_SESSION_COMPOSITOR` da un `/proc/<pid>/environ`.

    ⛔ Tre risposte, e la terza non e' un «no»: il valore · `ASSENTE` · `None`.
       `ASSENTE` solo se l'ambiente letto e' VERO — cioe' contiene
       `XDG_RUNTIME_DIR`, che il prodotto mette sempre: e' il controllo
       positivo sullo stesso strumento (`LEZIONI.md` §1.9).
    """
    if not grezzo:
        return None
    voci = {}
    for pezzo in grezzo.split(b"\0"):
        if b"=" in pezzo:
            k, _, v = pezzo.partition(b"=")
            voci[k.decode(errors="replace")] = v.decode(errors="replace")
    if "XDG_RUNTIME_DIR" not in voci:
        return None
    return voci.get("XFCE4_SESSION_COMPOSITOR", ASSENTE)


def ascolta_righe(righe):
    """Da quel che l'orecchio (`busctl monitor --json=short`) ha sentito.

    ⭐ `visto` · `non-visto` · ⛔ `sordo` — e sordo vuol dire «non ho visto
       nemmeno la NOSTRA chiamata `Logout`», che e' il controllo positivo.
    """
    chiamata, stati = False, []
    for riga in righe:
        riga = riga.strip()
        if not riga:
            continue
        membro, dati = None, None
        try:
            d = json.loads(riga)
            membro = d.get("member")
            dati = (d.get("payload") or {}).get("data")
        except (ValueError, AttributeError):
            # ⚠ Se il formato cambia si ripiega sul testo, non sul silenzio.
            g = re.search(r'"member"\s*:\s*"(\w+)"', riga)
            membro = g.group(1) if g else None
            g = re.search(r'"data"\s*:\s*\[\s*(\d+)\s*,\s*(\d+)\s*\]', riga)
            dati = [int(g.group(1)), int(g.group(2))] if g else None
        if membro == "Logout":
            chiamata = True
        elif membro == "StateChanged" and isinstance(dati, list) \
                and len(dati) == 2:
            stati.append(dati[1])
    if not chiamata:
        return "sordo"
    return "visto" if any(s in STATI_SPEGNIMENTO for s in stati) else "non-visto"


# ---------------------------------------------------------------------------
# GLI ATTREZZI DELLA SCATOLA
# ---------------------------------------------------------------------------
def corri(argv, tempo=30):
    """(codice, uscita, errore).  ⛔ `codice` None = non e' nemmeno partito.
       ⚠ Si tiene anche lo stderr: e' li' che `loginctl` e `xfconf-query`
       dicono «non c'e'», ed e' quel che distingue «assente» da «muto»."""
    ambiente = dict(os.environ, LC_ALL="C", LANG="C")
    try:
        p = subprocess.run(argv, capture_output=True, text=True, timeout=tempo,
                           stdin=subprocess.DEVNULL, env=ambiente)
        return p.returncode, (p.stdout or ""), (p.stderr or "")
    except (OSError, subprocess.SubprocessError):
        return None, "", ""


def come(chi, uid, argv):
    """Il prefisso per fare una cosa COME l'inquilino, sul SUO bus d'utente."""
    return (["runuser", "-u", chi, "--", "env", "LC_ALL=C", "LANG=C",
             "XDG_RUNTIME_DIR=/run/user/%d" % uid,
             "DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/%d/bus" % uid]
            + argv)


def leggi_file(percorso, binario=False):
    try:
        with open(percorso, "rb" if binario else "r") as f:
            return f.read()
    except OSError:
        return None


def guardia_scatola():
    """⛔⛔ PRIMA DI TUTTO: sono dentro `rete11-xfce`?  Torna il motivo del no,
       o None.  Tre fatti, e servono tutti:
         · `/run/.containerenv` — podman lo mette in OGNI contenitore;
         · `container=podman` nell'ambiente del processo 1 — sull'ospite il
           processo 1 e' il systemd vero, e non lo porta;
         · `RETE11_SCATOLA=rete11-xfce` — lo passa il lanciatore, che e' l'unico
           a sapere IN QUALE scatola ha fatto `podman exec`.
    """
    if os.geteuid() != 0:
        return "va eseguito da amministratore (dentro la scatola)"
    if not os.path.exists("/run/.containerenv"):
        return ("non trovo /run/.containerenv: NON sono dentro un contenitore "
                "podman — e questo banco fuori dalla scatola potrebbe "
                "ammazzare una sessione vera")
    uno = leggi_file("/proc/1/environ", binario=True)
    if uno is None or b"container=podman" not in uno.split(b"\0"):
        return ("il processo 1 non porta `container=podman`: non mi fido di "
                "essere dentro la scatola")
    if os.environ.get("RETE11_SCATOLA") != SCATOLA:
        return ("manca RETE11_SCATOLA=%s: mi deve lanciare "
                "`13-w2-la-trappola-del-logout.sh`, che sa in quale scatola "
                "entra" % SCATOLA)
    if not os.path.exists(VERO):
        return "non c'e' %s: questa non e' la scatola di XFCE" % VERO
    if shutil.which("labwc") is None:
        return "non c'e' labwc: questa non e' la scatola di XFCE"
    return None


def processi(uid, nome):
    """I pid di `nome` (per `comm`, intero) che girano come `uid`.
       ⛔ `None` se `/proc` non si e' fatto leggere — che non e' «nessuno»."""
    try:
        elenco = os.listdir("/proc")
    except OSError:
        return None
    trovati = []
    for voce in elenco:
        if not voce.isdigit():
            continue
        try:
            if os.stat("/proc/%s" % voce).st_uid != uid:
                continue
        except OSError:
            continue
        comm = leggi_file("/proc/%s/comm" % voce)
        if comm is not None and comm.strip() == nome:
            trovati.append(int(voce))
    return sorted(trovati)


def vivo(pid):
    """⚠ Uno zombi non e' vivo: il suo `/proc` c'e' ancora, lui no."""
    stat = leggi_file("/proc/%d/stat" % pid)
    if stat is None:
        return False
    try:
        stato = stat.rsplit(")", 1)[1].split()[0]
    except IndexError:
        return True
    return stato not in ("Z", "X")


def sessione_del_processo(pid):
    """La sessione logind di un processo, dal suo cgroup — cioe' dove logind
       stesso la cerca quando qualcuno chiede `terminate-session ''`."""
    cg = leggi_file("/proc/%d/cgroup" % pid)
    if cg is None:
        return None
    g = re.search(r"/session-([^/]+)\.scope", cg)
    return g.group(1) if g else None


def proprieta_sessione(s):
    """{chiave: valore} da `loginctl show-session`, o None se muto.
       ⛔ Una sessione che logind non conosce da' {"_sparita": True}: e' una
          risposta, non un silenzio."""
    codice, uscita, errore = corri(
        ["loginctl", "show-session", s, "-p", "Name", "-p", "Leader",
         "-p", "State", "-p", "Service", "-p", "Remote", "-p", "Class"])
    if codice is None:
        return None
    if codice != 0:
        if re.search(r"No session|not known", errore + uscita):
            return {"_sparita": True}
        return None
    d = {}
    for riga in uscita.splitlines():
        if "=" in riga:
            k, _, v = riga.partition("=")
            d[k.strip()] = v.strip()
    return d if "State" in d else None


def e_il_figlio_di(pid, chi):
    """Il `Leader` e' il `remotix-figlio --figlio-interno <chi>`?"""
    grezzo = leggi_file("/proc/%s/cmdline" % pid, binario=True)
    if not grezzo:
        return False
    argv = [a.decode(errors="replace") for a in grezzo.split(b"\0") if a]
    if not argv or not argv[0].endswith("remotix-figlio"):
        return False
    try:
        i = argv.index("--figlio-interno")
    except ValueError:
        return False
    return i + 1 < len(argv) and argv[i + 1] == chi


def xfconf_leggi(chi, uid):
    """⭐ valore · `ASSENTE` (solo col «does not exist») · `None` (muto)."""
    codice, uscita, errore = corri(
        come(chi, uid, ["xfconf-query", "-c", CANALE, "-p", CHIAVE]))
    if codice == 0:
        return uscita.strip()
    if "does not exist" in (uscita + errore):
        return ASSENTE
    return None


def xfconf_scritta_dal_prodotto(uid):
    """⭐ Il controllo positivo dell'innesto (a): il valore di `CHIAVE` nel
       file della SESSIONE che il prodotto scrive (D-017), letto dal disco —
       valore · `ASSENTE` (file o proprieta' mancanti) · `None` (illeggibile).
       ⚠ Vale solo se BLOCCATA: una non bloccata la toglierebbe l'utente."""
    t = leggi_file(FILE_SESSIONE % uid)
    if t is None:
        return ASSENTE
    try:
        import xml.etree.ElementTree as ET
        radice = ET.fromstring(t)
    except Exception:
        return None
    for g in radice.findall("property"):
        if "/" + g.get("name", "") + "/" != CHIAVE[:CHIAVE.rindex("/") + 1]:
            continue
        for p in g.findall("property"):
            if p.get("name") == CHIAVE.rsplit("/", 1)[1]:
                return p.get("value") if p.get("locked") else "%s (NON bloccata)" % (
                    p.get("value"))
    return ASSENTE


def innesta_senza_xfconf(chi):
    """Il drop-in del banco, nella casa dell'inquilino NUOVO, prima della
       nascita.  Torna None se fatto, o il perche' no."""
    percorso = DROPIN_BANCO % chi
    try:
        os.makedirs(os.path.dirname(percorso), exist_ok=True)
        with open(percorso, "w") as f:
            f.write("%s\n[Service]\nEnvironment=XDG_CONFIG_DIRS=/etc/xdg\n" % FIRMA_DROPIN)
    except OSError as e:
        return str(e)
    corri(["chown", "-R", "%s:" % chi, "/home/%s/.config" % chi])
    t = leggi_file(percorso)
    return None if t and FIRMA_DROPIN in t else "il drop-in scritto non si rilegge"


def stato_xfsm(chi, uid):
    """Lo stato del gestore di sessione (0 Startup, 1 Idle, …), o None."""
    codice, uscita, _e = corri(
        come(chi, uid, ["busctl", "--user", "call", BUS_NOME, BUS_PERCORSO,
                        BUS_INTERFACCIA, "GetState"]), tempo=10)
    if codice != 0:
        return None
    g = re.match(r"\s*u\s+(\d+)", uscita)
    return int(g.group(1)) if g else None


# ---------------------------------------------------------------------------
# L'INVOLUCRO — solo dentro la scatola, solo per il NOSTRO inquilino
# ---------------------------------------------------------------------------
def testo_involucro(chi):
    return ("#!/bin/sh\n"
            "%s\n"
            "# ⛔ Tocca SOLO l'inquilino «%s»; per chiunque altro e' un exec puro.\n"
            "if [ \"$(id -un)\" = \"%s\" ]; then\n"
            "\texport XFCE4_SESSION_COMPOSITOR=\"%s\"\n"
            "fi\n"
            "exec %s \"$@\"\n"
            % (FIRMA_INVOLUCRO, chi, chi, RIGA_TRAPPOLA, VERO))


def involucro_mio():
    t = leggi_file(INVOLUCRO)
    return t is not None and FIRMA_INVOLUCRO in t


def togli_involucro():
    """⛔ Si toglie SOLO se porta la firma: un file d'altri non si tocca."""
    if os.path.lexists(INVOLUCRO) and involucro_mio():
        try:
            os.unlink(INVOLUCRO)
        except OSError:
            pass
    return not os.path.lexists(INVOLUCRO)


# ---------------------------------------------------------------------------
# L'INQUILINO — creato nuovo, e i gruppi della scheda dall'unico posto (C1)
# ---------------------------------------------------------------------------
def carica_c1(percorso):
    if not os.path.exists(percorso):
        return None
    spec = importlib.util.spec_from_file_location("c1_gruppi", percorso)
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
    except Exception:
        return None
    if not callable(getattr(mod, "garantisci_i_gruppi", None)):
        return None
    return mod


def sgombera(chi, cancella=True):
    """Lo sgombero del BANCO — ⛔ per nome, mai un modello globale (fase 10
       §7.3).  E dentro la scatola: `loginctl` e `pkill` qui vedono solo lei."""
    corri(["loginctl", "terminate-user", chi], tempo=30)
    time.sleep(1.0)
    corri(["pkill", "-KILL", "-u", chi], tempo=30)
    time.sleep(0.5)
    if cancella:
        corri(["userdel", "-r", chi], tempo=60)
        corri(["rm", "-rf", "/home/%s" % chi], tempo=30)


def coda_di(percorso, righe=6):
    t = leggi_file(percorso) or ""
    return [r for r in t.strip().splitlines()[-righe:]]


# ---------------------------------------------------------------------------
# IL GIRO
# ---------------------------------------------------------------------------
def esci(esito, motivi):
    print()
    titolo = {0: "⭐ VERDE (esito 0)", 1: "⛔⛔ ROSSO (esito 1)",
              3: "⚠ NON HO POTUTO GUARDARE (esito 3) — ⛔ e NON e' un verde"}
    print(titolo.get(esito, "esito %d" % esito))
    for r in motivi:
        print("   %s" % r)
    return esito


def giro(a, modo):
    chi = a.utente
    m = {"desktop_su": False, "sessione": None, "legata": False,
         "perche_legata": "", "variabile": None, "xfconf_prima": None,
         "xfconf": None, "desktop_sparito": False, "spegnimento": "sordo",
         "sessione_dopo": None}

    # --- l'involucro: un avanzo MIO si toglie, uno d'altri ferma tutto ----
    if os.path.lexists(INVOLUCRO):
        if not involucro_mio():
            return esci(3, ["⛔ c'e' gia' un %s che NON e' mio (niente firma): "
                            "non lo tocco, e con lui in mezzo non so che "
                            "cosa esegue labwc" % INVOLUCRO])
        print("   ⚠ trovato un involucro MIO rimasto da un giro morto: lo tolgo")
        if not togli_involucro():
            return esci(3, ["⛔ non riesco a togliere l'avanzo %s" % INVOLUCRO])

    c1 = carica_c1(a.c1)
    if c1 is None:
        return esci(3, ["⛔ non trovo (o non carica) %s: da li' vengono i "
                        "gruppi della scheda, in un posto solo (§1.47)" % a.c1])
    if not os.path.exists(a.cliente):
        return esci(3, ["⛔ non trovo il cliente di prova %s" % a.cliente])

    cliente = orecchio = None
    registro_cliente = registro_orecchio = None
    try:
        # --- l'inquilino, NUOVO (§1.39: da zero anche rispetto a me di ieri) --
        sgombera(chi)
        fatto = subprocess.run(
            ["/bin/sh", "-c", "useradd -m -s /bin/bash %s && printf '%s:%s\\n' "
             "| chpasswd" % (chi, chi, a.parola)],
            capture_output=True, text=True, stdin=subprocess.DEVNULL)
        if fatto.returncode != 0:
            return esci(3, ["⛔ non sono riuscito a creare «%s»: %s"
                            % (chi, fatto.stderr.strip()[:120])])
        uid = pwd.getpwnam(chi).pw_uid
        e_gr, perche_gr = c1.garantisci_i_gruppi(chi, "   ")
        if e_gr != 0:
            return esci(3, ["i gruppi della scheda non sono garantiti: %s"
                            % perche_gr])
        codice, uscita, _e = corri(["loginctl", "list-sessions", "--no-legend"])
        if codice is None:
            return esci(3, ["⛔ `loginctl` non risponde"])
        gia = [r for r in uscita.splitlines()
               if len(r.split()) > 2 and r.split()[2] == chi]
        if gia:
            return esci(3, ["⛔ il campo non e' libero: «%s» ha gia' %d sessioni "
                            "prima di cominciare" % (chi, len(gia))])

        # --- l'innesto della variabile va messo PRIMA che labwc parta ---------
        if not MODI[modo]["variabile"]:
            try:
                with open(INVOLUCRO, "w") as f:
                    f.write(testo_involucro(chi))
                os.chmod(INVOLUCRO, 0o755)
            except OSError as e:
                return esci(3, ["⛔ non riesco a scrivere l'involucro: %s" % e])
            # ⛔ si rilegge, non si ricopia l'intenzione (§1.48)
            if not involucro_mio():
                return esci(3, ["⛔ l'involucro scritto non si rilegge"])
            print("   ⛔ innesto: %s riscrive la variabile in «%s» per «%s»"
                  % (INVOLUCRO, RIGA_TRAPPOLA, chi))

        # --- l'innesto della chiave xfconf, anche lui PRIMA della nascita -----
        #     (FASE 15, D-017: la chiave e' bloccata nel xfconf della sessione)
        if not MODI[modo]["xfconf"]:
            no = innesta_senza_xfconf(chi)
            if no:
                return esci(3, ["⛔ non riesco a scrivere il drop-in di xfconfd: %s"
                                % no])
            print("   ⛔ innesto: %s rimette XDG_CONFIG_DIRS=/etc/xdg a xfconfd per "
                  "«%s» — il xfconf della sessione non si legge" % (DROPIN_BANCO % chi,
                                                                     chi))

        # --- il cliente fa nascere la sessione, e resta attaccato -------------
        registro_cliente = tempfile.NamedTemporaryFile(
            prefix="13-w2-cliente-", suffix=".log", delete=False).name
        with open(registro_cliente, "w") as uscita_cliente:
            cliente = subprocess.Popen(
                ["python3", a.cliente, "--indirizzo", a.indirizzo,
                 "--porta", str(a.porta), "--utente", chi, "--parola", a.parola,
                 "--resta", str(a.resta)],
                stdin=subprocess.DEVNULL, stdout=uscita_cliente,
                stderr=subprocess.STDOUT)
        # ⭐ si aspetta l'EVENTO: un xfce4-session dell'inquilino, e poi Idle
        partenza = time.time()
        scadenza = partenza + a.attesa_desktop
        pid_xs = None
        while time.time() < scadenza:
            trovati = processi(uid, "xfce4-session")
            if trovati:
                if len(trovati) > 1:
                    return esci(3, ["⛔ %d xfce4-session di «%s»: non so quale "
                                    "giudicare" % (len(trovati), chi)])
                pid_xs = trovati[0]
                break
            if cliente.poll() is not None:
                break
            time.sleep(0.5)
        if pid_xs is None:
            coda = coda_di(registro_cliente)
            amm = c1.e_stato_ammesso("\n".join(coda)) \
                if callable(getattr(c1, "e_stato_ammesso", None)) else None
            return esci(3, ["⛔ nessun xfce4-session di «%s» entro %.0f s"
                            % (chi, a.attesa_desktop),
                            "il cliente: %s" % {True: "ammesso",
                                                False: "RESPINTO",
                                                None: "muto"}[amm]]
                        + ["  | %s" % r for r in coda])
        stato = None
        while time.time() < scadenza:
            stato = stato_xfsm(chi, uid)
            if stato == STATO_IDLE or not vivo(pid_xs):
                break
            time.sleep(1.0)
        if stato != STATO_IDLE:
            return esci(3, ["⛔ xfce4-session (pid %d) non e' arrivato a Idle "
                            "entro %.0f s (ultimo stato letto: %s)"
                            % (pid_xs, a.attesa_desktop, stato)])
        m["desktop_su"] = True
        print("   ⭐ desktop su in %.1f s: xfce4-session pid %d, stato Idle"
              % (time.time() - partenza, pid_xs))

        labwc = processi(uid, "labwc") or []
        pid_lw = labwc[0] if len(labwc) == 1 else None

        # --- la prima cintura: l'ambiente VERO di xfce4-session ------------
        m["variabile"] = variabile_da_ambiente(
            leggi_file("/proc/%d/environ" % pid_xs, binario=True))
        print("   la variabile, letta in /proc/%d/environ: %s%s"
              % (pid_xs, m["variabile"],
                 "   (= la riga del prodotto)"
                 if m["variabile"] == RIGA_PRODOTTO else ""))
        exe = os.path.realpath("/proc/%d/exe" % pid_xs)
        print("   l'eseguibile di quel processo: %s" % exe)

        # --- la sessione: quella di QUEL processo, e provata nostra --------
        s = sessione_del_processo(pid_xs)
        m["sessione"] = s
        if s:
            prop = proprieta_sessione(s)
            perche = []
            if not prop or prop.get("_sparita"):
                perche.append("loginctl non la descrive (%r)" % prop)
            else:
                print("   la sessione di xfce4-session: %s · %s"
                      % (s, " · ".join("%s=%s" % kv
                                       for kv in sorted(prop.items()))))
                if prop.get("Name") != chi:
                    perche.append("Name=%s, non «%s»" % (prop.get("Name"), chi))
                if not e_il_figlio_di(prop.get("Leader", "0"), chi):
                    perche.append("il Leader %s non e' il remotix-figlio di «%s»"
                                  % (prop.get("Leader"), chi))
                # ⚠ `closing` e' lo stato NORMALE di una sessione del
                #   prodotto, su OGNI desktop: `[M]` 21 set 2026, GNOME
                #   (baseline) e XFCE danno `Service=remotix State=closing`
                #   col figlio vivo.  ⇒ «viva» = logind la descrive E il suo
                #   Leader (il figlio, provato sopra) e' vivo.
                ld = prop.get("Leader", "0")
                if prop.get("State") not in ("active", "online", "closing") \
                        or not (ld.isdigit() and vivo(int(ld))):
                    perche.append("State=%s, Leader %s %s gia' prima del "
                                  "logout — il controllo positivo di «viva» "
                                  "manca" % (prop.get("State"), ld,
                                             "vivo" if ld.isdigit()
                                             and vivo(int(ld)) else "andato"))
            if pid_lw is None:
                perche.append("non trovo UN labwc di «%s» (%d)"
                              % (chi, len(labwc)))
            elif sessione_del_processo(pid_lw) != s:
                perche.append("labwc sta nella sessione %s, non in %s"
                              % (sessione_del_processo(pid_lw), s))
            m["legata"] = not perche
            m["perche_legata"] = "; ".join(perche)
            leader = (prop or {}).get("Leader")
        else:
            leader = None

        # --- la seconda cintura, e l'innesto ------------------------------
        if not MODI[modo]["xfconf"]:
            m["xfconf_prima"] = xfconf_scritta_dal_prodotto(uid)
            print("   la chiave xfconf %s scritta dal PRODOTTO nel file della "
                  "sessione: %s" % (CHIAVE, m["xfconf_prima"]))
            m["xfconf"] = xfconf_leggi(chi, uid)
            print("   ⛔ innesto (drop-in prima della nascita): xfconf-query "
                  "RILEGGE: %s" % m["xfconf"])
        else:
            m["xfconf_prima"] = xfconf_leggi(chi, uid)
            print("   la chiave xfconf %s: %s" % (CHIAVE, m["xfconf_prima"]))
            m["xfconf"] = m["xfconf_prima"]

        # ⭐ Il giudice guarda le guardie prima di tutto: se gia' qui non si
        #   puo' giudicare, NON si fa il logout — non si fa scattare una
        #   trappola che poi non si saprebbe leggere.
        esito0, motivi0 = giudica(modo, dict(m, desktop_sparito=True,
                                             spegnimento="visto",
                                             sessione_dopo="viva"))
        if esito0 == 3:
            return esci(3, motivi0)

        # --- l'orecchio sul bus, PRIMA della chiamata ----------------------
        registro_orecchio = tempfile.NamedTemporaryFile(
            prefix="13-w2-orecchio-", suffix=".jsonl", delete=False).name
        with open(registro_orecchio, "w") as fo:
            orecchio = subprocess.Popen(
                come(chi, uid, ["stdbuf", "-oL", "busctl", "--user",
                                "--json=short", "monitor", BUS_NOME]),
                stdin=subprocess.DEVNULL, stdout=fo,
                stderr=subprocess.DEVNULL)
        time.sleep(1.5)

        # --- IL LOGOUT: il gesto dell'utente, «Esci» senza finestra --------
        print("\n   ⛔ LOGOUT: %s.Logout(false, false) sul bus d'utente"
              % BUS_INTERFACCIA)
        t_logout = time.time()
        codice, uscita, errore = corri(
            come(chi, uid, ["busctl", "--user", "--timeout=30", "call",
                            BUS_NOME, BUS_PERCORSO, BUS_INTERFACCIA,
                            "Logout", "bb", "false", "false"]), tempo=40)
        print("   la risposta: codice %s %s"
              % (codice, (errore or uscita).strip()[:100]))

        # ⭐ il desktop deve SPARIRE — QUEL pid, non «uno qualunque»
        scadenza = t_logout + a.attesa_logout
        while time.time() < scadenza:
            if not vivo(pid_xs) and (pid_lw is None or not vivo(pid_lw)):
                m["desktop_sparito"] = True
                break
            time.sleep(0.25)
        print("   il desktop: %s"
              % ("⭐ SPARITO in %.1f s (xfce4-session %d e labwc %s)"
                 % (time.time() - t_logout, pid_xs, pid_lw)
                 if m["desktop_sparito"] else
                 "⛔ ancora li' dopo %.0f s" % a.attesa_logout))

        # ⭐ la sessione, per una FINESTRA dichiarata dopo la sparizione:
        #   caduta alla prima lettura che lo dice; viva se nessuna lo dice e
        #   l'ultima l'ha vista viva.
        if m["desktop_sparito"]:
            fine = time.time() + a.finestra
            ultima, lette, mute = None, 0, 0
            while time.time() < fine:
                p = proprieta_sessione(s)
                if p is None:
                    mute += 1
                elif p.get("_sparita") or not (leader and leader.isdigit()
                                                and vivo(int(leader))):
                    # ⛔ `State=closing` NON e' piu' un segnale: e' lo stato
                    #   di sempre (vedi sopra).  Caduta = logind l'ha
                    #   dimenticata, o il figlio che la tiene e' morto.
                    ultima = "caduta"
                    print("   la sessione %s: ⛔ CADUTA dopo %.1f s dal logout "
                          "(%s)" % (s, time.time() - t_logout,
                                    "logind non la conosce piu'"
                                    if p.get("_sparita") else
                                    "il figlio (Leader %s) e' morto" % leader))
                    break
                else:
                    lette += 1
                    ultima = "viva"
                time.sleep(0.5)
            if ultima == "viva" and mute > lette:
                ultima = None          # ⛔ piu' silenzi che letture: non lo so
            m["sessione_dopo"] = ultima
            if ultima == "viva":
                print("   la sessione %s: ⭐ VIVA per tutta la finestra di "
                      "%.0f s (%d letture, %d mute)"
                      % (s, a.finestra, lette, mute))
            print("   il figlio (Leader %s): %s"
                  % (leader, "vivo" if leader and leader.isdigit()
                     and vivo(int(leader)) else "andato"))

        time.sleep(1.0)
        if orecchio is not None:
            orecchio.terminate()
            try:
                orecchio.wait(timeout=5)
            except subprocess.TimeoutExpired:
                orecchio.kill()
        m["spegnimento"] = ascolta_righe(
            (leggi_file(registro_orecchio) or "").splitlines())
        print("   l'orecchio sul bus: %s" % {
            "visto": "⭐ la nostra chiamata Logout, e poi lo Shutdown",
            "non-visto": "⛔ la nostra chiamata sì, lo Shutdown MAI",
            "sordo": "⛔ SORDO — non ha visto nemmeno la nostra chiamata"}
            [m["spegnimento"]])

        # ⚠ informativo, NON giudicato qui
        nuovi = [p for p in (processi(uid, "xfce4-session") or [])
                 if p != pid_xs]
        if nuovi:
            print("   ⚠ un xfce4-session NUOVO e' nato dopo il logout (%s): "
                  "non e' il giudizio di questa maglia, ma va detto" % nuovi)
        cod = "codice 0x10" in (leggi_file(registro_cliente) or "")
        print("   il cliente ha ricevuto 0x10 (sessione terminata): %s"
              % ("si" if cod else "no"))

        esito, motivi = giudica(modo, m)
        return esci(esito, motivi)
    finally:
        # ⛔ Chi apre, chiude (`LEZIONI.md` §9-ter) — anche col guasto, anche
        #    se il giudizio e' andato storto.  E tutto dentro la scatola.
        if orecchio is not None and orecchio.poll() is None:
            orecchio.kill()
        if cliente is not None and cliente.poll() is None:
            cliente.terminate()
            try:
                cliente.wait(timeout=10)
            except subprocess.TimeoutExpired:
                cliente.kill()
        if not togli_involucro():
            print("   ⛔⛔ NON sono riuscito a togliere %s: TOGLILO A MANO, o il "
                  "prossimo giro di «%s» nasce avvelenato" % (INVOLUCRO, chi))
        sgombera(chi)
        for f in (registro_cliente, registro_orecchio):
            if f:
                try:
                    os.unlink(f)
                except OSError:
                    pass


def main():
    p = argparse.ArgumentParser(
        prog="13-w2-la-trappola-del-logout",
        description="La trappola del logout di XFCE (STUDI.md §xfce §9.2). "
                    "⛔ Solo dentro la scatola rete11-xfce.")
    guasti = p.add_mutually_exclusive_group()
    guasti.add_argument("--senza-xfconf", action="store_true",
                        help="guasto (a): tolta la chiave xfconf, la variabile "
                             "resta giusta ⇒ visto, e la sessione deve restare")
    guasti.add_argument("--senza-cinture", action="store_true",
                        help="guasto (b): tolte tutt'e due ⇒ la sessione DEVE "
                             "cadere; se non cade, esito 3")
    guasti.add_argument("--senza-variabile", action="store_true",
                        help="la misura M2: tolta la variabile, la chiave "
                             "resta ⇒ visto, e la sessione deve restare")
    guasti.add_argument("--certifica", action="store_true",
                        help="il giudice contro casi scritti a mano: non tocca "
                             "niente e gira ovunque")
    p.add_argument("--utente", default="w2u1",
                   help="l'inquilino di prova: si crea NUOVO e si cancella")
    p.add_argument("--parola", default="provanic2026")
    p.add_argument("--porta", type=int, default=8513)
    p.add_argument("--indirizzo", default="127.0.0.1")
    p.add_argument("--cliente", default="/opt/remotix/01-b3-cliente.py")
    p.add_argument("--c1", default="/opt/remotix/11-c1-nasce-e-si-vede.py")
    p.add_argument("--resta", type=float, default=600.0,
                   help="quanto il cliente resta attaccato (piu' del giro)")
    p.add_argument("--attesa-desktop", type=float, default=180.0,
                   help="tetto per xfce4-session nato e Idle (§9.4: 8 s per "
                        "gruppo di priorita', strutturali)")
    p.add_argument("--attesa-logout", type=float, default=60.0,
                   help="tetto per la sparizione del desktop dopo il Logout")
    p.add_argument("--finestra", type=float, default=20.0,
                   help="quanto si guarda la sessione dopo che il desktop e' "
                        "sparito")
    a = p.parse_args()

    if a.certifica:
        sys.exit(certifica())

    modo = ("senza-xfconf" if a.senza_xfconf else
            "senza-cinture" if a.senza_cinture else
            "senza-variabile" if a.senza_variabile else "sano")

    no = guardia_scatola()
    if no:
        print("⛔⛔ %s" % no)
        print("   ⇒ non ho fatto NIENTE, e non ho potuto guardare: esito 3")
        sys.exit(3)

    atteso = MODI[modo]
    print("== 13-w2 — la trappola del logout di XFCE (§xfce §9.2) ==")
    print("   dentro %s · inquilino «%s» · porta %d" % (SCATOLA, a.utente,
                                                      a.porta))
    print("   modo: %s — xfconf %s, variabile %s ⇒ la sessione %s"
          % (modo, "c'e'" if atteso["xfconf"] else "TOLTA",
             "giusta" if atteso["variabile"] else "«%s»" % RIGA_TRAPPOLA,
             "DEVE CADERE" if atteso["deve_cadere"] else "deve restare"))
    if modo != "sano":
        print("   ⛔ GUASTO INNESTATO: l'esito si legge AL CONTRARIO "
              "(0 = il guasto e' stato visto)")
    print()
    sys.exit(giro(a, modo))


if __name__ == "__main__":
    main()
