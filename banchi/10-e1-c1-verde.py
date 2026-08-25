#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
10-e1-c1-verde — ⭐ IL SOLO BRACCIO DEL VERDE di `10-c1-cure.py`, sull'albero
                 CUCITO (incarico 10-e1, quinto giro).

    porta 8310 · utenti provaf1…provaf7 · albero /media/REMOTIX/src/10e1-src
    lavoro /media/REMOTIX/tmp/10e1 · unita' remotix-8310 · lucchetto `10-e1`

═══════════════════════════════════════════════════════════════════════════
⛔ PERCHE' NON SI LANCIA `10-c1-cure.py tutto`, e perche' NON e' una scorciatoia
═══════════════════════════════════════════════════════════════════════════

`10-c1-cure.py` misura **una cura**: gira due volte, sul binario di ieri e su
quello curato, piu' il controllo negativo.  ⇒ Il suo giro pieno vale
`3 × (2×45 + 120 + 7×240)` per la sola prova B, cioe' oltre un'ora e mezza di
**lucchetto della GPU** — e i due bracci del rosso li ha gia' misurati il suo
autore, sul suo albero.

⛔ La domanda di QUESTO incarico e' un'altra: *«cucite insieme, le quattro cure
   ritrovano il proprio numero?»*  ⇒ Serve **il braccio del verde**, sul
   binario dell'albero cucito, con **gli stessi predicati** — non un banco
   nuovo.  ⭐ Percio' qui non si riscrive niente: si importa `10-c1-cure.py` e
   si chiamano **le sue** funzioni e **i suoi** giudizi.

⚠ E QUEL CHE QUESTO GIRO NON PUO' DIRE, dichiarato prima:
  ⛔ **non c'e' il rosso di confronto** — il numero si paragona a quello che
     l'autore ha misurato **sul suo albero**, non a un rosso di oggi.  ⇒ Se
     differisce, si dice **di quanto**, e non lo si fa combaciare a forza
     (`LEZIONI.md` §1.28).
  ⛔ **non c'e' il controllo negativo**: il banco importato lo sa fare, e il suo
     `--certifica` (44/44) lo dimostra ancora; qui non lo si rifa' perche'
     costerebbe un terzo braccio di lucchetto e proverebbe una cosa gia'
     provata.

═══════════════════════════════════════════════════════════════════════════
⛔ LE DUE PEZZE, e sono dichiarate perche' toccano l'isolamento
═══════════════════════════════════════════════════════════════════════════

 1. ⛔ `10-c1-cure.sgombra()` chiude i clienti con
    `pkill -f -- '--giornale [/]srv/remotix/tmp/10c1/'` — **la cartella di
    QUELL'incarico, scritta a mano**.  Con la mia (`…/10e1`) quel modello non
    combacia con niente: i miei clienti resterebbero vivi e il giro dopo
    misurerebbe una macchina piu' carica di quella dichiarata.  ⇒ Si
    ri-costruisce **lo stesso modello** sulla mia cartella.  ⚠ E resta
    **specifico**, mai globale: la quinta trappola di §7.3 (un modello globale
    che ammazza i clienti di un altro banco) non si ripete.
 2. ⭐ Il lucchetto lo tiene chi lancia (`banchi/10-e1-lucchetto.sh`), e qui non
    si prende ne' si molla: `prendi()` non e' rientrante.

Uso:
    LUCCHETTO_ESTERNO=1 python3 -u banchi/10-e1-c1-verde.py b
    LUCCHETTO_ESTERNO=1 python3 -u banchi/10-e1-c1-verde.py a
    LUCCHETTO_ESTERNO=1 python3 -u banchi/10-e1-c1-verde.py tutto
"""
import importlib.util
import json
import os
import sys
import time

QUI = os.path.dirname(os.path.abspath(__file__))

# ⛔ L'ISOLAMENTO PRIMA DELL'IMPORT: `10-c1-cure.py` legge l'ambiente con
#    `setdefault` **al momento in cui viene importato**.  Metterlo dopo vorrebbe
#    dire misurare sulla porta 8210 di un altro incarico.
os.environ.setdefault("IO_SONO", "10-e1")
os.environ.setdefault("PORTA", "8310")
os.environ.setdefault("LAV", "/media/REMOTIX/tmp/10e1")
os.environ.setdefault("ALBERO", "/media/REMOTIX/src/10e1-src")
os.environ.setdefault("DENTRO_ALB", "/srv/src/10e1-src")
os.environ.setdefault("DENTRO_LAV", "/srv/remotix/tmp/10e1")
os.environ.setdefault("UNITA", "remotix-8310")
os.environ.setdefault("SHM_BASE", "10e1")
os.environ.setdefault("STAGING", "/tmp/10-e1-repo")
os.environ.setdefault("QUANTI", "7")
os.environ.setdefault("FUORI", "/tmp/10-e1")
os.environ.setdefault("BINARIO_ALBERO", "remotix-cura-inn")

_s = importlib.util.spec_from_file_location("c1", os.path.join(QUI, "10-c1-cure.py"))
C1 = importlib.util.module_from_spec(_s)
_s.loader.exec_module(C1)

_ok, _ko, _dub, _inf, _log = C1._ok, C1._ko, C1._dub, C1._inf, C1._log
BINARIO = os.environ.get("BINARIO", "remotix-cura-inn")


def sgombra_mio(quanti=7, dillo=True):
    """⛔ Lo sgombero di `10-c1-cure.py`, con la MIA cartella nel modello."""
    C1.b92.root("printf 'sgombro -1\\n' > %s" % C1.b97.FILE_RITARDO)
    for i in range(1, quanti + 1):
        C1.b92.root("pkill -u %d -f '04-b30-scena' ; true" % C1.b92.uid(i))
    # ⛔ La classe `[/]` sulla prima barra, e non e' un vezzo: `pkill -f`
    #    acchiappa **la riga di comando che lo esegue** (§7.3), e senza la
    #    classe il modello troverebbe se stesso.
    C1.b92.root("pkill -f -- '--giornale [/]%s/' ; true"
                % os.environ["DENTRO_LAV"].lstrip("/"))
    time.sleep(2)
    C1.b92.chiudi_palchi(quanti, dillo=dillo)


def due_sfratti(esiti):
    """⭐⭐ DUE SFRATTI A DISTANZA — e serve all'INCROCIO n. 2, non a C1.

    ⛔ `webtransport.c:4786` dice che `fermo_ms=` sono *«i millisecondi in cui il
       ciclo del padre NON ha girato **da quando questa sessione e' nata**»*, ma
       la riga passa `giro_fermo_ms`, che e' **globale e cumulativo
       dall'accensione**.  ⇒ Su un server acceso da un giorno, uno sfratto dopo
       dieci secondi direbbe `fermo_ms=40000`, e chi legge **assolve la rete
       quando la rete c'entrava** — l'errore inverso di quello che la cura
       esiste per togliere.

    ⚠ Un solo sfratto non lo dimostra: `fermo_ms=0` sta bene a tutt'e due le
      letture.  ⇒ Ne servono **due**, con dei buchi in mezzo, e si guarda se il
      secondo **riparte**.  ⛔ Se in mezzo non ci sono buchi il banco lo dice e
      NON giudica: senza sollecitazione non si giudica (`LEZIONI.md` §1.30).
    """
    _log("I2-ter · DUE sfratti a distanza — `fermo_ms` riparte, o e' globale?")
    fuori = {"scatti": [], "buchi_in_mezzo": None}
    r0 = C1.b97.registro_byte()
    for n in (1, 2):
        guai = C1.b97.apri_fino_a(1, 3600, gia=0)
        if guai:
            for g in guai:
                _ko(g)
            return None
        time.sleep(4)
        if n == 2:
            # ⛔ Fra i due sfratti si FERMA il ciclo, o `fermo_ms` resterebbe
            #    zero in tutt'e due e la domanda non avrebbe risposta.
            ok, perche = C1.b97.ritardo_poni("e1-i2-%d" % int(time.time()),
                                             C1.A_D_MS)
            _inf("la leva fra i due sfratti: %s" % perche)
            time.sleep(25)
            C1.b97.ritardo_poni("e1-i2-fine-%d" % int(time.time()), 0)
        _inf("sfratto %d: `kill -9` sul client" % n)
        C1.b92.root("pkill -9 -f -- '%s' ; true" % C1.b92.cerca_giornale(1))
        time.sleep(C1.A_MORTO_ATTESA_S)
        C1.b97.riapri_i_caduti(1, 3600)
    r1 = C1.b97.registro_byte()
    fetta = C1.b97.registro_fetta(r0, r1)
    fuori["scatti"] = (fetta.get("scatti")
                       if fetta.get("esito") == "letto" else None)
    if fuori["scatti"] is None:
        _dub("⚠ non ho letto il registro: NON GIUDICO")
    else:
        for s in fuori["scatti"]:
            _inf("   %s causa=%s fermo_ms=%s giri_fermi=%s saltati=%s"
                 % (s.get("provenienza"), s.get("causa"), s.get("fermo_ms", "-"),
                    s.get("giri_fermi", "-"), s.get("saltati", "-")))
        v = [s.get("fermo_ms") for s in fuori["scatti"]
             if s.get("fermo_ms") is not None]
        if len(v) < 2:
            _dub("⚠ meno di due sfratti col campo `fermo_ms`: NON GIUDICO")
        elif all(v[i + 1] >= v[i] for i in range(len(v) - 1)) and v[-1] > 0:
            _ko("⛔ `fermo_ms` NON riparte (%s): e' il contatore GLOBALE, e il "
                "commento dice «da quando questa sessione e' nata»" % v)
        else:
            _ok("⭐ `fermo_ms` riparte (%s): e' per sessione" % v)
    esiti["i2_due_sfratti"] = fuori
    return fuori


def fermo_di_chi_e_nato_dopo(esiti):
    """⛔⛔ LA PROVA DECISIVA SU `fermo_ms=`, e la prima che avevo tentato NON LO ERA.

    ⚠ Il primo tentativo sfrattava **due volte la stessa sessione**: quella era
      viva durante i buchi, quindi «globale» e «per sessione» dicono lo STESSO
      numero e la prova non separa niente.  ⭐ Qui la scena e' un'altra, e
      separa: si accumulano i buchi con **s1**, la si manda via, e poi si fa
      nascere **s2 — un altro utente, dopo** — e si sfratta lei.

      · se `fermo_ms` di s2 e' **0**, il campo e' per sessione, come dice il
        commento di `webtransport.c:4786`;
      · se e' **> 0**, il campo e' il contatore GLOBALE `giro_fermo_ms`, e la
        riga dello sfratto attribuisce a s2 un fermo di **prima che nascesse**.

    ⛔ E se i buchi non si accumulano il banco NON giudica: senza sollecitazione
       non c'e' niente da leggere (`LEZIONI.md` §1.30).
    """
    _log("I2-ter · `fermo_ms` su una sessione NATA DOPO i buchi")
    r0 = C1.b97.registro_byte()

    _inf("1 · s1 (%s) accumula i buchi col ciclo fermo a %d ms"
         % (C1.b92.utente(1), C1.A_D_MS))
    guai = C1.b97.apri_fino_a(1, 3600, gia=0)
    if guai:
        for g in guai:
            _ko(g)
        return None
    time.sleep(4)
    ok, perche = C1.b97.ritardo_poni("e1-fermo-%d" % int(time.time()), C1.A_D_MS)
    _inf("la leva: %s" % perche)
    if not ok:
        _dub("⚠ la leva non ha preso: NON GIUDICO")
        return None
    time.sleep(50)
    C1.b97.ritardo_poni("e1-fermo-off-%d" % int(time.time()), 0)
    r_mezzo = C1.b97.registro_byte()
    # ⛔ `buchi_nella_fetta()` e' di `10-c1-cure.py` e torna `None` se non ha
    #    letto: «zero buchi» e «non ho letto» non devono avere la stessa faccia.
    b = C1.buchi_nella_fetta(r0, r_mezzo)
    buchi = None if b is None else len(b)
    _inf("buchi del ciclo accumulati da s1: %s" % buchi)
    if buchi is None:
        _dub("⚠ non ho letto il registro: NON GIUDICO")
        return None
    if not buchi:
        _dub("⚠ nessun buco: la prova non ha morso, NON GIUDICO")
        return None

    _inf("2 · s1 se ne va, e nasce s2 (%s) — DOPO i buchi"
         % C1.b92.utente(2))
    C1.b92.root("pkill -9 -f -- '%s' ; true" % C1.b92.cerca_giornale(1))
    # ⛔ Si aspetta lo sfratto del fantasma (`--sfratto-ms` 15 000) col margine,
    #    o il posto di s1 sarebbe ancora occupato e s2 non sarebbe una scena
    #    pulita.
    time.sleep(C1.B_SFRATTO_ATTESA_S)
    r1 = C1.b97.registro_byte()
    guai = C1.b97.apri_fino_a(2, 3600, gia=1)
    if guai:
        for g in guai:
            _ko(g)
        return None
    time.sleep(6)
    _inf("3 · `kill -9` su s2, e si legge il suo `fermo_ms`")
    C1.b92.root("pkill -9 -f -- '%s' ; true" % C1.b92.cerca_giornale(2))
    time.sleep(C1.A_MORTO_ATTESA_S)
    r2 = C1.b97.registro_byte()
    fetta = C1.b97.registro_fetta(r1, r2)
    sc = fetta.get("scatti") if fetta.get("esito") == "letto" else None
    esiti["i2_ter"] = {"buchi_di_s1": buchi, "scatti_di_s2": sc}
    if sc is None:
        _dub("⚠ non ho letto il registro: NON GIUDICO")
        return None
    if not sc:
        _dub("⚠ s2 non e' stata sfrattata: NON GIUDICO")
        return None
    for s in sc:
        _inf("   %s causa=%s fermo_ms=%s giri_fermi=%s saltati=%s"
             % (s.get("provenienza"), s.get("causa"), s.get("fermo_ms", "-"),
                s.get("giri_fermi", "-"), s.get("saltati", "-")))
    v = sc[0].get("fermo_ms")
    if v is None:
        _dub("⚠ il campo `fermo_ms` non c'e': NON GIUDICO")
    elif int(v) > 0:
        _ko("⛔⛔ s2 e' NATA DOPO i buchi e la sua riga di sfratto dice "
            "`fermo_ms=%s`: e' il contatore GLOBALE, non «da quando questa "
            "sessione e' nata» — chi legge assolve o accusa la rete sul numero "
            "sbagliato" % v)
    else:
        _ok("⭐ `fermo_ms=0` su una sessione nata dopo i buchi: il campo e' per "
            "sessione, come dice il commento")
    return sc


def principale():
    passo = sys.argv[1] if len(sys.argv) > 1 else "tutto"
    C1.apri_attrezzi()
    # ⛔ La pezza n. 1, e si applica DOPO `apri_attrezzi()` (prima `b92` non c'e').
    C1.sgombra = sgombra_mio
    os.makedirs(C1.FUORI, exist_ok=True)
    esiti = {"quando": time.strftime("%Y-%m-%d %H:%M:%S"),
             "porta": C1.PORTA, "albero": os.environ["ALBERO"],
             "binario": BINARIO, "passo": passo}
    rossi, muti = [], []

    _log("SGOMBERO DI PARTENZA")
    sgombra_mio()

    guai = C1.b97.spedisci_attrezzi()
    if guai:
        for g in guai:
            _ko(g)
        return 2

    _log("IL BINARIO DELL'ALBERO, prima del terreno")
    if C1.metti_binario(os.environ["BINARIO_ALBERO"]) is None:
        _ko("⛔ NON MISURO: non ho potuto rimettere il binario dell'albero")
        return 2

    _log("⛔ IL TERRENO DELLA FASE 10 — si guarda PRIMA di misurare")
    rc = C1.b97.terreno(lucchetto_mio=True)
    if rc != 0:
        _ko("⛔ il terreno non ha dato verde (uscita %d): NON misuro" % rc)
        return 2

    try:
        if passo in ("a", "tutto"):
            dopo = C1.braccio_a(BINARIO, "cucito", esiti)
            if dopo is None:
                muti.append("A: il braccio con la cura non e' stato misurato")
            else:
                C1.dillo("A/cucito · la leva",
                         C1.leva_ha_preso(dopo["ciclo_fermo"]), rossi, muti)
                C1.dillo("A1/cucito · ⛔⛔ NESSUNO viene sfrattato",
                         C1.a1_sfratto_ingiusto(dopo["ciclo_fermo"], "verde"),
                         rossi, muti)
                C1.dillo("A1/cucito · la guardia si arma quando deve",
                         C1.a1_si_arma(dopo["ciclo_fermo"]), rossi, muti)
                C1.dillo("A2/cucito · e NON si arma su una macchina sana",
                         C1.a2_non_si_arma(dopo["sana_macchina"]), rossi, muti)
                C1.dillo("A3/cucito · ⛔ e la linea morta funziona ANCORA",
                         C1.a3_linea_morta_regge(dopo["client_morto"]),
                         rossi, muti)
            sgombra_mio()

        if passo in ("b", "tutto"):
            due = C1.braccio_b(BINARIO, "cucito", esiti)
            if due is None:
                muti.append("B: il braccio con la cura non e' stato misurato")
            else:
                fermo, carico = due
                C1.dillo("B/cucito · la leva", C1.leva_ha_preso(carico),
                         rossi, muti)
                C1.dillo("B/cucito · una domanda sola",
                         C1.b_chiamate(carico, C1.B_ENNE, 1), rossi, muti)
                C1.dillo("B/cucito · il ritmo NON cala",
                         C1.b_ritmo(fermo.get("fot_s"), carico.get("fot_s"),
                                    "verde"), rossi, muti)
                C1.dillo("B/cucito · chi e' rimasto",
                         C1.nessuno_staccato(carico, C1.B_ENNE), rossi, muti)
                ch, du = carico.get("chiamate"), carico.get("durata_s")
                _inf("⭐ i numeri da ritrovare: fot/s a guardiano fermo %s · "
                     "sotto carico %s · chiamate per ripasso %s"
                     % (fermo.get("fot_s"), carico.get("fot_s"),
                        "?" if (ch is None or not du)
                        else "%.2f" % (ch / (du / 2.0))))
                p = (carico.get("porta") or {}).get("esito")
                C1.dillo("B/cucito · la porta a chi arriva",
                         (C1._si("⭐ l'inquilino nuovo entra") if p is True
                          else C1._no("⛔ NON entra: %s"
                                      % (carico.get("porta") or {}).get("perche", "?"))),
                         rossi, muti)
            sgombra_mio()

        if passo in ("i2", "tutto"):
            due_sfratti(esiti)
            sgombra_mio()

        if passo == "fermo":
            fermo_di_chi_e_nato_dopo(esiti)
            sgombra_mio()
    finally:
        try:
            sgombra_mio()
            C1.terreno_sh("spegni")
        except Exception as e:
            _dub("⚠ lo sgombero finale non e' riuscito: %s" % e)
        with open(os.path.join(C1.FUORI, "e1-c1.json"), "w") as f:
            json.dump(esiti, f, indent=1, default=str)
        _inf("gli esiti crudi in %s/e1-c1.json" % C1.FUORI)

    _log("IL VERDETTO")
    for r in rossi:
        _ko(r)
    for m in muti:
        _dub(m)
    if rossi:
        return 1
    if muti:
        return 3
    _ok("⭐ il braccio del verde ha ritrovato i suoi numeri sull'albero cucito")
    return 0


if __name__ == "__main__":
    sys.exit(principale())
