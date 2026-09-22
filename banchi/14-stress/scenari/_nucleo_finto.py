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
     "rotto"       il browser non si accende           ⇒ atteso 3 (non lo so)
"""
import io
import re
import time

VERDE, ROSSO, CIECO = 0, 1, 3


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

    # ── la scatola ────────────────────────────────────────────────────────
    def dentro(self, desktop, copione, interprete="sh", argomenti=None, secondi=180):
        """⚠ TRE valori, come il vero: (codice, uscita, errore)."""
        self.comandi.append(copione)
        c = copione
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
        return True, "inquilino «%s» pronto in %s (per finta)" % (chi, desktop)

    def sgombera(self, desktop, chi):
        return None

    def scena(self, desktop, quale, chi, secondi=40):
        return True, "scena «%s» accesa (per finta)" % quale

    def istante_nella_scatola(self, desktop):
        return time.strftime("%H:%M:%S")

    def modello_senza_se_stesso(self, chi):
        return "[%s]%s" % (chi[0], chi[1:])

    # ── il browser e la pagina ────────────────────────────────────────────
    def avvia_browser(self, marca, porta, misura=(1600, 1000), tetto_s=40):
        if self.come == "rotto":
            raise RuntimeError("questo browser non si accende (per finta)")
        self.t0 = time.time()
        return Browser(self, marca, porta)

    def conta_dalla_pagina(self, browser):
        fermo = (self.come == "fermo" and (time.time() - self.t0) > 20)
        if not fermo and not self.schermo_nero:
            self.consegnati += self.passo
            self.dipinti += self.passo - 1
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
