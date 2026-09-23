#!/usr/bin/env python3
"""input-sotto-carico — con la scena pesante, i tasti, il mouse e gli appunti
devono arrivare lo stesso.

⭐ PERCHE' SOTTO CARICO: l'input e l'immagine condividono la stessa connessione.
   Con la scena ferma arrivano tutti, sempre; il difetto — se c'e' — nasce
   quando la coda di uscita e' piena di fotogrammi da 300 KB.  ⇒ Una prova
   dell'input a desktop fermo dice poco di quel che l'utente sente mentre
   guarda un video.

⭐ IL GIUDIZIO in tre pezzi, e ognuno ha un testimone indipendente:
   · TASTI e PUNTATORE: le righe `input id=… POSIZIONE_TASTO / PUNTATORE` nel
     registro del SERVER — cioe' l'altro capo del filo, ⛔ non la pagina che
     dice di averli spediti;
   · APPUNTI: il testo copiato nella pagina si ritrova nella sessione (§7.4);
   · l'IMMAGINE, che nel frattempo non si deve fermare.

⚠ IL RITARDO SI DICHIARA, non si giudica: `[M]` la grana dei tempi del client e'
  grossa (§7.3) e nessuna misura fine ci si costruisce sopra.

⛔ E l'input si manda col GUIDATORE del browser (`.muovi`, `.tasto`), non con
   eventi finti in JavaScript: un evento costruito a mano prova il codice della
   pagina, non la catena che parte dal dispositivo.
"""
import time

import _comune as C

NOME = "input-sotto-carico"
DURATA_S = 180
TETTO_S = 12 * 60

# ⭐ GLI APPUNTI, E SI MISURA IL VERSO CHE SI PUO' MISURARE DAVVERO.
#
# ⛔ Il verso pagina→sessione ha bisogno di un GESTO dell'utente: un
#    `ClipboardEvent` costruito in JavaScript non mette niente negli appunti del
#    browser, e `[M]` 23 set 2026 questo scenario dava rosso al prodotto per una
#    finta del banco.  ⇒ Quel verso lo prova `11-c17`, dentro la scatola, dove
#    il gesto e' vero.
# ⭐ Qui si prova il verso SESSIONE→PAGINA, che e' vero da fuori: si copia nella
#    sessione con `wl-copy`, e si guarda l'ANNUNCIO che il server manda alla
#    pagina (§7.4: `APPUNTI.suo_id` e `suo_len` in `src/pagina.html`).
APPUNTI_STATO = """
  var A = (window.REMOTIX && REMOTIX.appunti) || null;
  if (!A) return null;
  return {suo_id: A.suo_id, suo_len: A.suo_len};
"""


def gira(desktop, marca, nucleo, opzioni=None):
    o = dict(opzioni or {})
    durata = float(o.get("durata_s", DURATA_S))
    quanti_tasti = int(o.get("tasti", 20))
    quante_mosse = int(o.get("mosse", 30))
    tetto = C.Tetto(o.get("tetto_s", TETTO_S))
    chi = o.get("chi") or C.nome_inquilino("in")
    b = C.Banco(nucleo, desktop, marca, chi, misura=o.get("misura", (1400, 1000)),
                dove=o.get("dove"))
    try:
        cod, perche = b.apparecchia("pesante")
        if cod != C.VERDE:
            return C.esito(NOME, desktop, marca, cod, perche, secondi=tetto.passati())
        time.sleep(15)          # il carico dev'esserci PRIMA dell'input

        segno = C.istante(nucleo, desktop)
        mandati = {"mosse": 0, "tasti": 0}
        try:
            for i in range(quante_mosse):
                b.browser.muovi(100 + (i * 17) % 600, 100 + (i * 29) % 400)
                mandati["mosse"] += 1
            # ⚠ `ArrowRight`, e non una lettera: la tavola dei tasti del
            #   guidatore (`12-client-veri.py` `TASTI`) ne conosce due —
            #   `Control` e `ArrowRight` — ⛔ e `tasto("a")` muore con un
            #   `KeyError` che somiglia a un guasto del prodotto e non lo e'
            #   (`[M]` 23 set 2026, primo giro vero).
            for i in range(quanti_tasti):
                b.browser.tasto(o.get("quale_tasto", "ArrowRight"))
                mandati["tasti"] += 1
        except Exception as e:                   # noqa: BLE001
            return C.non_so(NOME, desktop, marca,
                            "il guidatore non ha potuto mandare l'input (%d mosse "
                            "e %d tasti mandati): %s"
                            % (mandati["mosse"], mandati["tasti"], str(e)[:140]),
                            secondi=tetto.passati())

        # ── gli appunti, verso sessione → pagina ──────────────────────────
        segreto = "remotix-stress-%d" % int(time.time())
        appunti = {"verso": "sessione→pagina", "arrivato": None, "perche": ""}
        try:
            prima_app = b.browser.js(APPUNTI_STATO) or {}
            uid = C.uid_di(nucleo, desktop, chi) or 0
            c, t_out = C.dentro(nucleo, desktop,
                                "R=/run/user/%d; W=$(ls $R 2>/dev/null | "
                                "grep -E '^wayland-[0-9]+$' | head -1); "
                                # ⛔ `wl-copy` NON TORNA: resta in piedi a
                                #    servire quel che ha copiato (e' il
                                #    proprietario della selezione).  ⚠ Senza
                                #    staccarlo, il comando scade e la misura si
                                #    perde — `[M]` 23 set 2026, 120 s buttati.
                                "printf %%s '%s' | setsid runuser -u %s -- env "
                                "XDG_RUNTIME_DIR=$R WAYLAND_DISPLAY=$W wl-copy "
                                ">/dev/null 2>&1 & sleep 2; "
                                # ⚠ `timeout`: `wl-paste` ASPETTA l'offerta del
                                #   compositore e puo' non tornare mai; qui una
                                #   misura mancata deve costare dieci secondi,
                                #   non il tetto del comando.
                                "timeout 10 runuser -u %s -- env XDG_RUNTIME_DIR=$R "
                                "WAYLAND_DISPLAY=$W wl-paste -n 2>/dev/null | "
                                "head -c 80; echo; echo copiato=0"
                                % (uid, segreto, chi, chi), 60)
            if segreto not in (t_out or ""):
                appunti["perche"] = ("il testo non e' entrato negli appunti "
                                     "della sessione: %s" % (t_out or "")[-80:])
            else:
                fine = time.time() + 20
                while time.time() < fine:
                    dopo_app = b.browser.js(APPUNTI_STATO) or {}
                    if (dopo_app.get("suo_id") or 0) > (prima_app.get("suo_id") or 0):
                        appunti["arrivato"] = True
                        appunti["byte"] = dopo_app.get("suo_len")
                        break
                    time.sleep(1.0)
                else:
                    if prima_app:
                        appunti["arrivato"] = False
                        appunti["perche"] = ("20 s dopo la copia nella sessione la "
                                             "pagina non ha ricevuto nessun annuncio")
                    else:
                        appunti["perche"] = "la pagina non espone `REMOTIX.appunti`"
        except Exception as e:                   # noqa: BLE001
            appunti["perche"] = "non ho potuto provare gli appunti: %s" % str(e)[:120]

        # ⭐ E mentre l'input viaggia, l'occhio guarda la tela: ⛔ «i tasti sono
        #   arrivati» non vuol dire «l'immagine e' giusta», e una prova
        #   dell'input che non guarda lo schermo lascia meta' della domanda fuori.
        storia = C.guarda_per(nucleo, b.browser,
                              min(durata, max(30.0, tetto.resta() - 90)),
                              passo=5.0, tetto=tetto, occhio=b.occhio)
        cresciuta = C.cresciuti(storia[0], storia[-1])

        c, t = C.dentro(nucleo, desktop,
                        "L=%s; f() { grep -a '\\[%s\\]' $L | awk '$1>=\"%s\"'; }; "
                        "echo tasti=$(f | grep -c 'POSIZIONE_TASTO'); "
                        "echo puntatore=$(f | grep -c 'input id=.*PUNTATORE'); "
                        "echo appunti=$(f | grep -ci 'appunti')"
                        % (C.REGISTRO, chi, segno), 180)
        conti = {}
        for riga in (t or "").splitlines():
            if "=" in riga:
                k, _, v = riga.partition("=")
                try:
                    conti[k.strip()] = int(v.strip())
                except ValueError:
                    pass

        misure = {"mandati": mandati,
                  "tasti_al_server": conti.get("tasti"),
                  "puntatore_al_server": conti.get("puntatore"),
                  "righe_appunti": conti.get("appunti"),
                  "appunti": appunti,
                  "fotogrammi_nel_frattempo": cresciuta.get("consegnati"),
                  "ritardo": "⚠ non misurato: la grana dei tempi del client e' "
                             "grossa (§7.3)"}
        regole = {"tasti_mandati": quanti_tasti, "mosse_mandate": quante_mosse}
        # ⭐ Anche qui l'immagine si guarda: uno scenario sull'input che non
        #   dicesse quanti fotogrammi sono arrivati nel frattempo lascerebbe
        #   meta' della prova fuori dalla riga.
        in_vista = dict(pagina=storia[-1], server=b.server())
        misure["server"] = in_vista["server"]

        if conti.get("tasti") is None and conti.get("puntatore") is None:
            return C.non_so(NOME, desktop, marca,
                            "non ho potuto leggere il registro del server: "
                            "dell'input non so niente", misure=misure,
                            secondi=tetto.passati(), **in_vista)
        guasti = []
        if not conti.get("puntatore"):
            guasti.append("nessun movimento del puntatore e' arrivato al server")
        if not conti.get("tasti"):
            guasti.append("nessun tasto e' arrivato al server")
        if not cresciuta.get("consegnati"):
            guasti.append("mentre l'input viaggiava l'immagine si e' fermata")
        if appunti.get("arrivato") is False:
            guasti.append("il testo copiato NELLA SESSIONE non e' arrivato alla "
                          "pagina: %s (§7.4)" % appunti.get("perche"))

        C.vede_l_occhio(b, misure, guasti)
        C.conta_il_ritmo(b, misure, guasti)

        if guasti:
            return C.rosso(NOME, desktop, marca, "; ".join(guasti), misure=misure,
                           regole=regole, secondi=tetto.passati(), guasti=guasti,
                           **in_vista)
        return C.verde(NOME, desktop, marca,
                       "sotto carico sono arrivati %s movimenti e %s tasti su "
                       "%d+%d mandati, appunti: %s, e nel frattempo sono arrivati "
                       "%s fotogrammi"
                       % (conti.get("puntatore"), conti.get("tasti"),
                          quante_mosse, quanti_tasti,
                          "si, %s byte" % appunti.get("byte")
                          if appunti.get("arrivato") else
                          "non misurato: %s" % (appunti.get("perche") or "?"),
                          cresciuta.get("consegnati")),
                       misure=misure, regole=regole, secondi=tetto.passati(),
                       **in_vista)
    except Exception as e:                       # noqa: BLE001
        return C.non_so(NOME, desktop, marca, "lo strumento si e' rotto: %s"
                        % str(e)[:200], secondi=tetto.passati())
    finally:
        b.chiudi_tutto()
