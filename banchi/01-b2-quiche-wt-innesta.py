#!/usr/bin/env python3
"""01-b2-quiche-wt-innesta.py — da' all'esempio di quiche tutto quel che la sua API C permette.

    python3 01-b2-quiche-wt-innesta.py            innesta
    python3 01-b2-quiche-wt-innesta.py --togli    rimette l'esempio com'era

---------------------------------------------------------------------------
⛔ PERCHE' ESISTE, E PERCHE' E' COSI' CORTO

Prima di misurare se `quiche` dichiara WebTransport, bisogna **chiederglielo**:
il loro esempio HTTP/3 non accende ne' la CONNECT estesa ne' i datagram, e
misurarlo cosi' misurerebbe una configurazione pigra invece della libreria.

⭐ Questo file e' il gemello di `01-b2-ngtcp2-wt-innesta.py`, e la differenza
   fra i due **e' il dato di `DECISIONI.md` §6.4**.  Qui, per adesso, ci sono
   solo le righe che accendono quel che l'API C offre.

---------------------------------------------------------------------------
⭐ LA LETTURA, E LA PREVISIONE — `[R]` 10 agosto 2026, scritta PRIMA di misurare

`quiche/src/h3/mod.rs:644`:

    pub fn set_additional_settings(&mut self, additional_settings: Vec<(u64, u64)>)

⭐ **quiche HA la funzione che a nghttp3 manca**: un modo pulito e sostenuto di
   mettere un'impostazione arbitraria nel proprio SETTINGS.  Su `ngtcp2` quel
   muro l'abbiamo aggirato riscrivendo i byte che nghttp3 ci consegnava.

⛔ **Ma non arriva all'API C.**  Zero occorrenze di `additional_settings` in
   `quiche/src/h3/ffi.rs` e zero in `include/quiche.h` `[R]`.  E il
   `quiche_h3_config` esporta **quattro** setter e basta:

       quiche_h3_config_set_max_field_section_size
       quiche_h3_config_set_qpack_max_table_capacity
       quiche_h3_config_set_qpack_blocked_streams
       quiche_h3_config_enable_extended_connect

⚠ **E su quiche il trucco di ngtcp2 non e' disponibile**: li' nghttp3 consegna
  all'applicazione i byte dello stream di controllo da scrivere, e li abbiamo
  riscritti al volo; qui l'HTTP/3 scrive dentro la connessione da se', e
  un'applicazione in C quei byte **non li vede mai**.

⇒ **PREVISIONE: `quiche`, usata dal C, NON dichiarera' WebTransport.**
  Nessuna delle due impostazioni comparira' sul filo.

⭐ **Che aspetto avrebbe il contrario**: la sonda le vede lo stesso ⇒ o quiche
   le manda da qualche altra parte, o ho letto male l'FFI.  In tutt'e due i
   casi la previsione e' sbagliata e va scritto perche'.

⛔ **E la previsione non e' il verdetto**: il server e' in C per `DECISIONI.md`
   §6.3, quindi «esiste in Rust» non e' «ce l'abbiamo».  Ma non e' nemmeno
   «impossibile»: e' una funzione che c'e' e non e' esposta, cioe' una
   **decina di righe di FFI** — e questa e' una cosa da scrivere accanto alla
   scelta, non da nascondere sotto un rosso.
"""
import subprocess
import sys

ESEMPI = "/srv/src/b2/quiche/quiche/examples"
MARCA = "REMOTIX B2"

INNESTI = [
    (
        "http3-server.c",
        "    http3_config = quiche_h3_config_new();\n",
        "    http3_config = quiche_h3_config_new();\n"
        "\n"
        "    /* ⭐ REMOTIX B2 — tutto quel che l'API C di quiche permette di\n"
        "     * accendere in vista di WebTransport.  Sono DUE righe, e la\n"
        "     * seconda non e' nel `quiche_h3_config`: i datagram si accendono\n"
        "     * sulla connessione, non sull'HTTP/3.\n"
        "     *\n"
        "     * ⛔ E manca la terza, quella che conterebbe: non c'e' modo, da\n"
        "     *    qui, di dichiarare SETTINGS_WT_MAX_SESSIONS.  In Rust si\n"
        "     *    farebbe con h3::Config::set_additional_settings; nell'FFI\n"
        "     *    quella funzione non c'e'. */\n"
        "    quiche_h3_config_enable_extended_connect(http3_config, true);\n",
        "la CONNECT estesa",
    ),
    (
        "http3-server.c",
        "    quiche_config_set_max_idle_timeout(config, 5000);\n",
        "    /* ⭐ REMOTIX B2 — RCP.md §2.2: trenta secondi imposti dal server,\n"
        "     * e i datagram abilitati (e' l'audio). */\n"
        "    quiche_config_set_max_idle_timeout(config, 30000);\n"
        "    quiche_config_enable_dgram(config, true, 1024, 1024);\n",
        "il tetto d'inattivita' e i datagram",
    ),
]


def righe_di_commento(righe):
    """⛔ UNA REGOLA SOLA PER I COMMENTI, E LA STESSA NEI TRE INNESTI.

    Qui la regola era «comincia per * oppure /*», e non riconosceva `//`; in
    `01-b3-rcp-innesta.py` era «//, /* oppure *», e classificava come commento
    le dereferenziazioni `*v = …` del C++ innestato da B2.  ⛔ Tre regole
    diverse sulla stessa grandezza sono tre numeri diversi sotto la stessa
    etichetta, ed e' con uno di quei numeri che `DECISIONI.md` §6.4 ha chiuso.

    ⚠ L'asterisco vale come commento solo quando continua o chiude un blocco
      `/* … */`, cioe' quando e' seguito da uno spazio o e' `*/`.
    """
    return sum(1 for r in righe
               if r.strip().startswith(("//", "/*", "* ", "*/"))
               or r.strip() == "*")


def main():
    if "--togli" in sys.argv:
        print("== Si rimette l'esempio com'era")
        return subprocess.run(
            ["git", "-C", "/srv/src/b2/quiche", "checkout", "--", "quiche/examples"],
        ).returncode

    print("== L'innesto minimo nell'esempio di quiche")
    print(f"   albero: {ESEMPI}")
    print(f"   {len(INNESTI)} innesti da applicare\n")

    with open(f"{ESEMPI}/http3-server.c", encoding="utf-8") as f:
        testo = f.read()
    if MARCA in testo:
        print("   ⚠ l'innesto c'e' gia': non si tocca niente.")
        return 0

    guasti = 0
    for _, appiglio, sostituto, nome in INNESTI:
        # ⛔ L'appiglio deve comparire UNA VOLTA SOLA: zero vuol dire che
        #    l'esempio e' cambiato, due che si sta innestando alla cieca.
        n = testo.count(appiglio)
        stato = "OK " if n == 1 else "NO "
        print(f"   {stato} {nome:34s} appiglio trovato {n} volta/e")
        if n != 1:
            guasti += 1
            continue
        testo = testo.replace(appiglio, sostituto, 1)

    if guasti:
        print(f"\n   ⛔ {guasti} appigli su {len(INNESTI)} non sono UNO: non si scrive niente.")
        return 2

    with open(f"{ESEMPI}/http3-server.c", "w", encoding="utf-8") as f:
        f.write(testo)
    print(f"\n   OK  {len(INNESTI)} innesti su {len(INNESTI)}")

    print("\n== Quante righe sono NOSTRE")
    d = subprocess.run(
        ["git", "-C", "/srv/src/b2/quiche", "diff", "-U0", "--", "quiche/examples"],
        capture_output=True,
        text=True,
    ).stdout.splitlines()
    agg = [r[1:] for r in d if r.startswith("+") and not r.startswith("+++")]
    vuote = sum(1 for r in agg if not r.strip())
    comm = righe_di_commento(agg)
    print(f"   righe aggiunte : {len(agg)}")
    print(f"     ⭐ di CODICE  : {len(agg) - vuote - comm}")
    print("\n   ⚠ E' l'innesto MINIMO — accende quel che c'e', non aggiunge lo")
    print("     strato.  Il paragone con ngtcp2 si fa solo se e quando lo")
    print("     strato su quiche si puo' scrivere.")
    print("\n   ⛔ E il numero di ngtcp2 NON si copia qui a mano: lo stampa")
    print("      01-b2-ngtcp2-wt-innesta.py, con la stessa regola di conteggio")
    print("      di questo script.  Qui c'era scritto «329», ed e' uno dei DUE")
    print("      numeri che circolano per la stessa grandezza — l'altro e' 333,")
    print("      in README.md.  Un numero copiato invecchia dove nessuno guarda.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
