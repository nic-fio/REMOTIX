#!/usr/bin/env python3
"""_nucleo_finto — un nucleo per finta, per provare gli SCENARI senza il server.

⛔ NON e' un banco e non misura niente del prodotto: serve a dimostrare che gli
   otto scenari **sanno dare rosso**.  Un giudice che non e' mai stato visto
   sbagliare e' un giudice di cui non si sa niente (`PIANO.md` §0.3 regola 4).

⛔⛔ E LE FIRME SONO QUELLE VERE, una per una.  `[M]` 23 set 2026: la prima
    stesura le aveva INVENTATE (un argomento in piu' di qua, due valori invece
    di tre di la'), gli scenari ci giravano verdi sopra, e contro il nucleo vero
    morivano al primo passo con «too many values to unpack».  ⇒ Un finto che non
    ha le firme del vero non prova niente — e `_prova_scenari.py` adesso le
    CONFRONTA con `inspect`, invece di fidarsi di questa riga.

⭐ Come si comanda: `Finto("come")` decide che cosa deve succedere.

     "sano"        tutto come dev'essere               ⇒ atteso VERDE
     "fermo"       i fotogrammi si fermano a meta'     ⇒ atteso ROSSO
     "morto"       la linea muore                      ⇒ atteso ROSSO
     "strisce"     la tela esce sbavata                ⇒ atteso ROSSO
     "cresce"      il server perde descrittori         ⇒ atteso ROSSO
     "fantasma"    dopo «Esci» lo schermo lampeggia    ⇒ atteso ROSSO
     "nero"        dopo il rientro non arriva niente   ⇒ atteso ROSSO
     "spirale"     una chiave ogni pochi fotogrammi    ⇒ atteso ROSSO
     "muto"        l'input non arriva al server        ⇒ atteso ROSSO
     "a_mosaico"   ⭐⭐ i contatori sono PERFETTI e      ⇒ atteso ROSSO
                   l'immagine e' a tessere sfalsate         (solo con l'occhio)
     "catena_rotta" il server butta fotogrammi gia'    ⇒ atteso ROSSO
                   codificati e non esce nessuna            (la rete sui numeri)
                   chiave a ricucire
     "rotto"       il browser non si accende           ⇒ atteso 3 (non lo so)

   ⭐ E con QUALUNQUE `come`, il guasto innestato del topo
     (`REMOTIX_SCHERMO_CONGELATO`): il finto riconosce i copioni del
     `Congelatore` e, finche' il compositore e' «fermo», la pagina non riceve
     fotogrammi nuovi — come sul ferro.

⭐⭐ E «a_mosaico» E' IL GUASTO CHE QUESTA SUITE NON SAPEVA VEDERE.  La notte
   fra il 22 e il 23 settembre 2026 due giri hanno dato VERDE con ~7000
   fotogrammi consegnati, 7000 dipinti, zero buchi e zero linee morte — mentre
   l'utente guardava un'immagine a mosaico.  ⇒ Qui il finto fa esattamente
   quello: **nessun contatore sbagliato**, e la tela che torna dal browser e' la
   scena testimone con dentro, ogni tanto, un pezzo di fotogramma vecchio.
   ⛔ Con `REMOTIX_OCCHIO=no` questo guasto torna a passare VERDE: e' la misura
      di quanto valeva il giudizio di ieri notte.
"""
import io
import os
import re
import sys
import time

VERDE, ROSSO, CIECO = 0, 1, 3


def _vero():
    """Il nucleo VERO, per le poche cose che non ha senso imitare."""
    sopra = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if sopra not in sys.path:
        sys.path.append(sopra)
    import stress_nucleo
    return stress_nucleo


def _occhio():
    """Il modulo dell'occhio — ⛔ non se ne rifa' la scena: e' il SUO disegno che
    il finto restituisce, o il banco si proverebbe con una scena che non e'
    quella che il giudice legge."""
    sopra = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if sopra not in sys.path:
        sys.path.append(sopra)
    import stress_occhio
    return stress_occhio


# ⭐ Ogni 25 fotografie, DUE escono col pezzo di fotogramma vecchio incollato
#   dentro: l'8 % — ⚠ ed e' lo stesso ordine di grandezza del guasto vero
#   (`[M]` 26 fotografie sopra soglia su 313, cioe' l'8,3 %).
MOSAICO_OGNI = 25
MOSAICO_QUANTE = 2


def _png_testimone(passo, rotta=False, scala=0.5):
    """⭐ La scena TESTIMONE come la vedrebbe il browser, sana o a mosaico.

    ⛔ Il guasto e' quello vero, non uno a caso: una fascia rimasta a un
       fotogramma di PRIMA — che e' quel che fa un decodificatore quando applica
       i delta su un riferimento che non ha mai ricevuto.  ⚠ Pulitissima e
       completamente falsa: e' il guasto che la dispersione delle strisce non
       vede e che le celle DISCORDI vedono.
    """
    try:
        O = _occhio()
        import numpy as np                        # noqa: F401
    except Exception:                             # noqa: BLE001
        return None

    def vecchio(a):
        indietro = O._disegna((passo + 3) % O.PASSI, scala=scala, rumore=False)
        b = a.copy()
        h = a.shape[0]
        b[int(h * 0.30):int(h * 0.52), :, :] = \
            indietro[int(h * 0.30):int(h * 0.52), :, :]
        return b

    try:
        return O._png(O._disegna(passo, guasto=(vecchio if rotta else None),
                                 scala=scala, rumore=False))
    except Exception:                             # noqa: BLE001
        return None


def _png(sbavata=False, lato=256, chiaro=0.0):
    """Una finta fotografia: rumore uniforme, oppure rumore a bande larghe."""
    try:
        import numpy as np
        from PIL import Image
    except Exception:                            # noqa: BLE001
        return None
    r = np.random.RandomState(7)
    a = r.normal(128 + chiaro, 18, (lato, lato))
    if sbavata:
        # ⛔ Le bande larghe sono la firma dei delta decodificati su un
        #    riferimento sbagliato: i blocchi 8×8 divergono fra loro.
        bande = r.normal(0, 40, (lato // 32, lato // 32))
        a = a + np.kron(bande, np.ones((32, 32)))
    b = io.BytesIO()
    Image.fromarray(np.clip(a, 0, 255).astype("uint8"), "L").save(b, "PNG")
    return b.getvalue()


class Browser(object):
    """⚠ Gli stessi metodi del `Browser` vero, con le stesse firme."""

    def __init__(self, finto, marca, porta):
        self.f, self.marca, self.porta = finto, marca, porta
        self.acceso = True
        self.finestra = (0, 0)

    def apri(self, tetto_s=40):
        return True, "modulo visibile (per finta)"

    def entra(self, utente, parola, tetto_s=60):
        self.f.uscito = False
        self.f.rientri += 1
        if self.f.come == "nero" and self.f.rientri > 1:
            self.f.schermo_nero = True
        return VERDE, "«Ammesso, sessione di %s» (per finta)" % utente

    def chiudi(self):
        self.acceso = False

    def misura(self, l, a):
        self.finestra = (int(l), int(a))
        return True, ""

    def fotografa(self):
        # ⭐⭐ Se sullo schermo c'e' la scena TESTIMONE, la fotografia e' quella:
        #   l'occhio deve poterla leggere e dire VERDE quando e' sana, o non si
        #   sarebbe provato niente di lui.  ⛔ E quando la scena e' un'altra si
        #   torna al rumore di prima: il giudice della LUMINANZA di
        #   `esci-rientra` misura quello, e una scena che cambia colore quindici
        #   volte al secondo gli fabbricherebbe i fantasmi (`[M]` 8,6 livelli).
        if (self.f.scena_accesa or "").startswith("testimone"):
            self.f.scatti += 1
            rotta = (self.f.come in ("a_mosaico", "strisce")
                     and (self.f.scatti % MOSAICO_OGNI) < MOSAICO_QUANTE)
            png = _png_testimone(self.f.scatti % 6, rotta=rotta)
            if png:
                return png
        # ⭐ Col fantasma la luminanza ALTERNA: e' il lampeggio che `esci-rientra`
        #   deve vedere.
        chiaro = 0.0
        if self.f.come == "fantasma":
            self.f.scatti += 1
            chiaro = 60.0 if (self.f.scatti % 2) else -60.0
        return _png(self.f.come == "strisce", chiaro=chiaro)

    def js(self, corpo, *arg):
        if "REMOTIX" in corpo and "appunti" in corpo:
            # lo stato degli appunti: l'annuncio arriva dopo la copia
            self.f.annunci += 1 if self.f.copiato and self.f.come != "muto" else 0
            return {"suo_id": self.f.annunci, "suo_len": len(self.f.copiato or "")}
        return "fatto"

    def vai(self, url=None):
        return True, "aperta"

    def ricarica(self):
        return True, "ricaricata"

    def muovi(self, x, y):
        self.f.mosse += 1

    def clic(self, x, y):
        self.f.clic += 1

    def tasto(self, t):
        self.f.tasti += 1

    def stato(self):
        return {"sessione": True, "esito": "Ammesso"}


class Finto(object):
    def __init__(self, come="sano", passo_consegnati=40):
        self.come = come
        self.passo = passo_consegnati
        self.t0 = time.time()
        self.consegnati = self.dipinti = self.buchi = 0
        self.mosse = self.tasti = self.clic = self.scatti = 0
        self.annunci = 0
        self.rientri = 0
        self.uscito = False
        self.schermo_nero = False
        self.fd = 100
        self.copiato = ""
        self.comandi = []
        self.scena_accesa = None
        self.chi = None
        self.congelato_fino = 0.0
        self.congelamenti = 0
        # ⛔ Le scene sono QUELLE DEL NUCLEO VERO, non una lista inventata: cosi'
        #    una scena che nella notte non esiste qui non si accende, invece di
        #    sembrare accesa e non far vedere niente.
        try:
            self.SCENE = dict(_vero().SCENE)
        except Exception:                        # noqa: BLE001
            self.SCENE = {"pesante": (None, ""), "normale": (None, ""),
                          "ferma": (None, "")}

    # ── la scatola ────────────────────────────────────────────────────────
    def dentro(self, desktop, copione, interprete="sh", argomenti=None, secondi=180):
        """⚠ TRE valori, come il vero: (codice, uscita, errore)."""
        self.comandi.append(copione)
        c = copione
        # ⭐⭐ LO SCHERMO CONGELATO (il guasto innestato del topo).  Il finto fa
        #   quel che fa il ferro: col compositore in SIGSTOP non esce nessun
        #   fotogramma nuovo finche' non arriva il SIGCONT — dal tablet, o dal
        #   cane da guardia allo scadere.  ⛔ Queste prove vengono PRIMA di
        #   tutte: i copioni del congelatore si riconoscono dalla prima riga.
        testa = c.splitlines()[0] if c else ""
        if "cerca-il-compositore" in testa:
            return 0, "COMPOSITORE 4242 kwin_wayland /run/user/4099/wayland-0\n", ""
        if "# congela-il-compositore" in testa:
            m = re.search(r"sleep (\d+); kill -CONT", c)
            self.congelato_fino = time.time() + (int(m.group(1)) if m else 30)
            self.congelamenti += 1
            return 0, "STATO 4242 Tl\n", ""
        if "scongela-il-compositore" in testa:
            self.congelato_fino = 0.0
            return 0, "STATO 4242 Sl\n", ""
        # ⭐ Il deposito della scena testimone: la scatola risponde con quanti
        #   byte ha scritto, che e' quel che `deposita_scena()` legge.
        #   ⛔ Questa prova viene PRIMA delle altre: il resto del copione e' un
        #      blocco base64 lungo, e ci si puo' trovare dentro per caso una
        #      qualunque delle parole cercate piu' sotto.
        # ⭐ Le righe di RIEPILOGO del ritmo, quelle che il server scrive alla
        #   CHIUSURA della sessione e che legge `stress_occhio.conti_del_ritmo`.
        #   ⛔ I due casi sono le due misure VERE del 23 settembre 2026, prima e
        #      dopo la cura `7e0c0e2`: 24 fotogrammi buttati con UNA sola chiave
        #      (la catena rotta e mai ricucita) contro 0 buttati e 8 chiavi.
        if "il regolatore del ritmo" in c:
            chi = self.chi or "ignoto"
            if self.come == "catena_rotta":
                buttati, chiavi = 24, 1
            else:
                buttati, chiavi = 0, 8
            righe = ["04:45:57 rcp [%s] il regolatore del ritmo: ACCESO — %d "
                     "fotogrammi NON PARTITI perche' l'arretrato" % (chi, buttati),
                     "04:45:57 rcp [%s] la soglia della coda video: ACCESA — delta "
                     "TENUTI 3, abbandonati per soglia 0, e NON ACCETTATI per "
                     "credito mancato 0 (§2.3)" % chi]
            righe += ["04:4%d:0%d rcp [%s] fotogramma %d SPEDITO: CHIAVE 0x0301"
                      % (i % 6, i % 10, chi, 1 + i * 300) for i in range(chiavi)]
            return 0, "\n".join(righe), ""
        if "14-scena-testimone" in c:
            try:
                return 0, str(len(_occhio().scena_html().encode("utf-8"))), ""
            except Exception as e:               # noqa: BLE001
                return 1, "", "la scena non si scrive (per finta): %s" % e
        if "date" in c:
            return 0, time.strftime("%H:%M:%S"), ""
        if "id -u" in c:
            return 0, "4099", ""
        if "pgrep" in c and ("kwin" in c or "gnome-shell" in c or "labwc" in c):
            return 0, ("NO" if self.uscito else "SI"), ""
        if "butto le" in c:
            return 0, ("0" if self.come == "fantasma" else "3"), ""
        if "ADOTTO" in c:
            return 0, ("0" if self.come == "nero" else "2"), ""
        if "POSIZIONE_TASTO" in c:
            if self.come == "muto":
                return 0, "tasti=0\npuntatore=0\nappunti=0", ""
            return 0, ("tasti=%d\npuntatore=%d\nappunti=4"
                       % (self.tasti, self.mosse)), ""
        if "wl-paste" in c:
            # ⭐ Il finto rimanda indietro il segreto che il copione ha appena
            #   copiato: cosi' il verso sessione→pagina si prova davvero, invece
            #   di restare «non misurato» anche col finto sano.
            m = re.search(r"remotix-stress-\d+", c)
            self.copiato = m.group(0) if m else ""
            return 0, ("" if self.come == "muto" else self.copiato), ""
        if "/etc/passwd" in c:
            return 0, "\n0", ""
        if "Logout" in c or "busctl" in c:
            self.uscito = True
            return 0, "fatto=0", ""
        if "grep -c" in c:
            return 0, "0", ""
        return 0, "", ""

    def crea_inquilino(self, desktop, chi, parola):
        # ⚠ Il nome del PRIMO inquilino serve alle righe del registro: il
        #   lettore del ritmo tiene solo le righe marcate `[chi]`, e righe
        #   marcate con un altro nome verrebbero buttate via — che e' proprio
        #   quel che devono fare.
        self.chi = self.chi or chi
        return True, "inquilino «%s» pronto in %s (per finta)" % (chi, desktop)

    def sgombera(self, desktop, chi):
        return None

    def scena(self, desktop, quale, chi, secondi=40, giri=1, passo=5.0):
        """⚠ `giri` e `passo` ci sono perche' CI SONO NEL VERO (23 set 2026).

        Nel nucleo vero sono il giro d attesa per la corsa col compositore: la
        sessione grafica dell inquilino nasce nell istante dell accesso e il
        socket wayland non c e ancora.  ⛔ Qui non c e nessun compositore da
        aspettare, quindi non si dorme — ma la FIRMA dev essere quella vera, o
        questo finto torna a non provare niente.
        """
        if quale not in self.SCENE:
            return False, ("scena «%s» che non conosco (per finta: %s)"
                           % (quale, ", ".join(sorted(self.SCENE))))
        self.scena_accesa = quale
        return True, "scena «%s» accesa (per finta)" % quale

    def istante_nella_scatola(self, desktop):
        return time.strftime("%H:%M:%S")

    def modello_senza_se_stesso(self, chi):
        return "[%s]%s" % (chi[0], chi[1:])

    # ── la riga del giro ──────────────────────────────────────────────────
    # ⛔ QUESTE DUE NON SI IMITANO: sono pure (nessun server, nessuna scatola),
    #    e il finto chiama le VERE.  ⚠ Rifarle qui vorrebbe dire provare gli
    #    scenari contro un vocabolario che nella notte non esiste — lo stesso
    #    difetto delle firme inventate, un piano piu' su.
    def completa_la_riga(self, riga):
        return _vero().completa_la_riga(riga)

    def numeri_in_vista(self, roba):
        return _vero().numeri_in_vista(roba)

    # ── il browser e la pagina ────────────────────────────────────────────
    def avvia_browser(self, marca, porta, misura=(1600, 1000), tetto_s=40):
        if self.come == "rotto":
            raise RuntimeError("questo browser non si accende (per finta)")
        self.t0 = time.time()
        return Browser(self, marca, porta)

    def conta_dalla_pagina(self, browser):
        fermo = (self.come == "fermo" and (time.time() - self.t0) > 20)
        congelato = time.time() < self.congelato_fino
        if not fermo and not self.schermo_nero and not congelato:
            self.consegnati += self.passo
            # ⭐⭐ Col mosaico i contatori sono PERFETTI: consegnati == dipinti,
            #   zero buchi.  ⛔ E' il punto di tutta la storia — la notte del 22
            #   la pagina diceva «7000 consegnati, 7000 dipinti, zero buchi» e
            #   sullo schermo c'era un'immagine a tessere sfalsate.
            self.dipinti += self.passo if self.come == "a_mosaico" else self.passo - 1
        if self.come == "strisce":
            self.buchi = 40
        return {"sessione": True, "esito": "Ammesso", "sospeso": False,
                "errori_pagina": 0, "errori_testo": [],
                "consegnati": self.consegnati, "dipinti": self.dipinti,
                "buchi": self.buchi, "saltati_coda": 3, "chiavi_chieste": 2,
                "coda_decodificatore": 0}

    # ── il server ─────────────────────────────────────────────────────────
    def conta_dal_server(self, desktop, da_istante=None, chi=None):
        spediti = max(1, self.consegnati)
        self.fd += (30 if self.come == "cresce" else 0)
        return {"spediti": spediti, "delta": spediti - 3,
                "chiavi": 3 if self.come != "spirale" else spediti // 3,
                "rc_accolte": 2 if self.come != "spirale" else spediti // 3,
                "rc_ignorate": 0, "tenuti_dietro_chiave": 1,
                "linee_morte": 1 if self.come == "morto" else 0,
                "tela_non_combacia": 0, "errori_rossi": 0,
                "server_pid": 4242, "server_fd": self.fd, "server_fili": 12,
                "server_figli": 2, "inquilini": 1}
