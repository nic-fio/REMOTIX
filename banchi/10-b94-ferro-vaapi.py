#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""10-b94-ferro-vaapi — che cosa il chip DICHIARA, e se OBBEDISCE quando gli si chiede per nome.

Fase 10, agente A10 — «lo studio del ferro».

⛔ Questo banco NON misura il soffitto: quello lo misura A2 col codificatore del prodotto.
Qui si interroga il driver VA-API **direttamente**, senza ffmpeg in mezzo, per rispondere a tre
domande che `vainfo` da solo non risponde:

  1. `dichiara`  — profili, ingressi, **attributi di configurazione** e il **ritmo dichiarato**
                   (`vaQueryProcessingRate`, in macroblocchi al secondo).
  2. `obbedisce` — si chiede un modo di controllo del bitrate **per nome** e si guarda che cosa
                   fa il driver. ⛔ È la verifica che `LEZIONI.md` §1.8 pretende: v1 si è fatto
                   male due volte proprio qui, col driver che deduceva il modo da come erano
                   riempiti due campi.
                   ⭐⭐ E `[M]` la risposta è a due gradini, di cui **solo il primo** sta dentro
                   VA-API: `vaCreateConfig` **rifiuta** con `VA_STATUS_ERROR_INVALID_VALUE` ogni
                   modo che non offre (bene: non surroga); ma `vaQueryConfigAttributes` sulla
                   config creata **rende la MASCHERA delle capacità**, identica per ogni
                   richiesta — ⛔ quindi *quale* modo sia in vigore **non si legge da qui**, e
                   la verifica va portata a valle, sul flusso prodotto
                   (`banchi/10-b94-ferro-carico.py`, predicato P2).
  3. `contesti`  — quanti contesti di codifica veri (config + superfici + contesto) si aprono
                   insieme, e **con quale errore esatto** il driver dice di no.

⚠ Nessun compilatore sulla macchina di prova: si parla a `libva.so.2` con `ctypes`.
⛔ `None` non è zero: ogni misura che non è riuscita torna `None` e il giudizio si rifiuta.

Modi:
    dichiara   [--nodo /dev/dri/renderD128]
    obbedisce  [--nodo …]
    contesti   [--nodo …] [--gradini 1,2,4,8,16,32] [--larghezza 1920 --altezza 1080]
    --certifica    innesta i guasti e conta sano → guasto → risanato
"""

import argparse
import ctypes
import json
import os
import sys

# ─────────────────────────────────────────────────────────────────────────────
# Le costanti di `va.h`. Non ci sono intestazioni sulla macchina: si trascrivono.
# ─────────────────────────────────────────────────────────────────────────────

PROFILI = {
    "VAProfileMPEG2Simple": 0,
    "VAProfileH264Main": 6,
    "VAProfileH264High": 7,
    "VAProfileJPEGBaseline": 12,
    "VAProfileH264ConstrainedBaseline": 13,
    "VAProfileHEVCMain": 17,
    "VAProfileHEVCMain10": 18,
    "VAProfileVP9Profile0": 19,
}

INGRESSI = {
    "VAEntrypointVLD": 1,
    "VAEntrypointEncSlice": 6,
    "VAEntrypointEncPicture": 7,
    "VAEntrypointEncSliceLP": 8,
    "VAEntrypointVideoProc": 10,
    "VAEntrypointFEI": 11,
    "VAEntrypointStats": 12,
}

ATTRIBUTI = {
    "VAConfigAttribRTFormat": 0,
    "VAConfigAttribRateControl": 5,
    "VAConfigAttribEncPackedHeaders": 10,
    "VAConfigAttribEncInterlaced": 11,
    "VAConfigAttribEncMaxRefFrames": 13,
    "VAConfigAttribEncMaxSlices": 14,
    "VAConfigAttribEncSliceStructure": 15,
    "VAConfigAttribMaxPictureWidth": 18,
    "VAConfigAttribMaxPictureHeight": 19,
    "VAConfigAttribEncQualityRange": 21,
    "VAConfigAttribEncQuantization": 22,
    "VAConfigAttribEncIntraRefresh": 23,
    "VAConfigAttribEncSkipFrame": 24,
    "VAConfigAttribEncROI": 25,
    "VAConfigAttribEncRateControlExt": 26,
    "VAConfigAttribProcessingRate": 27,
    "VAConfigAttribEncDirtyRect": 28,
    "VAConfigAttribEncParallelRateControl": 29,
    "VAConfigAttribEncTileSupport": 35,
    "VAConfigAttribMaxFrameSize": 38,
}

# I modi di controllo del bitrate, per nome. ⭐ Sono i nomi che si chiedono e si riverificano.
MODI_BITRATE = {
    "VA_RC_NONE": 0x00000001,
    "VA_RC_CBR": 0x00000002,
    "VA_RC_VBR": 0x00000004,
    "VA_RC_VCM": 0x00000008,
    "VA_RC_CQP": 0x00000010,
    "VA_RC_VBR_CONSTRAINED": 0x00000020,
    "VA_RC_ICQ": 0x00000040,
    "VA_RC_MB": 0x00000080,
    "VA_RC_CFS": 0x00000100,
    "VA_RC_PARALLEL": 0x00000200,
    "VA_RC_QVBR": 0x00000400,
    "VA_RC_AVBR": 0x00000800,
    "VA_RC_TCBRC": 0x00001000,
}

VA_RT_FORMAT_YUV420 = 0x00000001
VA_RT_FORMAT_YUV420_10 = 0x00000100
VA_PROGRESSIVE = 0x1
VA_STATUS_SUCCESS = 0
VA_ATTRIB_NOT_SUPPORTED = 0x80000000
VA_INVALID_ID = 0xFFFFFFFF


class VAConfigAttrib(ctypes.Structure):
    _fields_ = [("type", ctypes.c_int), ("value", ctypes.c_uint32)]


class VAProcessingRateParameterEnc(ctypes.Structure):
    _fields_ = [
        ("level_idc", ctypes.c_uint8),
        ("reserved", ctypes.c_uint8 * 3),
        ("quality_level", ctypes.c_uint32),
        ("intra_period", ctypes.c_uint32),
        ("ip_period", ctypes.c_uint32),
    ]


class Va:
    """Il filo diretto con `libva`. Apre il nodo, e lo chiude."""

    def __init__(self, nodo="/dev/dri/renderD128"):
        self.nodo = nodo
        self.fd = None
        self.dpy = None
        self.lib = ctypes.CDLL("libva.so.2")
        self.libdrm = ctypes.CDLL("libva-drm.so.2")
        self.libdrm.vaGetDisplayDRM.restype = ctypes.c_void_p
        self.libdrm.vaGetDisplayDRM.argtypes = [ctypes.c_int]
        self.lib.vaErrorStr.restype = ctypes.c_char_p
        self.lib.vaErrorStr.argtypes = [ctypes.c_int]

    def err(self, stato):
        return self.lib.vaErrorStr(stato).decode("utf-8", "replace")

    def apri(self):
        self.fd = os.open(self.nodo, os.O_RDWR)
        self.dpy = self.libdrm.vaGetDisplayDRM(self.fd)
        if not self.dpy:
            raise RuntimeError(f"vaGetDisplayDRM ha reso NULL su {self.nodo}")
        magg = ctypes.c_int()
        mino = ctypes.c_int()
        st = self.lib.vaInitialize(
            ctypes.c_void_p(self.dpy), ctypes.byref(magg), ctypes.byref(mino)
        )
        if st != VA_STATUS_SUCCESS:
            raise RuntimeError(f"vaInitialize: {self.err(st)}")
        self.versione = f"{magg.value}.{mino.value}"
        return self

    def chiudi(self):
        if self.dpy:
            self.lib.vaTerminate(ctypes.c_void_p(self.dpy))
            self.dpy = None
        if self.fd is not None:
            os.close(self.fd)
            self.fd = None

    def __enter__(self):
        return self.apri()

    def __exit__(self, *a):
        self.chiudi()

    # ── interrogazioni ──────────────────────────────────────────────────────
    def ingressi(self, profilo):
        n = self.lib.vaMaxNumEntrypoints(ctypes.c_void_p(self.dpy))
        arr = (ctypes.c_int * n)()
        num = ctypes.c_int()
        st = self.lib.vaQueryConfigEntrypoints(
            ctypes.c_void_p(self.dpy), profilo, arr, ctypes.byref(num)
        )
        if st != VA_STATUS_SUCCESS:
            return None
        return [arr[i] for i in range(num.value)]

    def attributi_offerti(self, profilo, ingresso, tipi):
        """`vaGetConfigAttributes` — che cosa il driver DICHIARA di sapere fare."""
        n = len(tipi)
        arr = (VAConfigAttrib * n)()
        for i, t in enumerate(tipi):
            arr[i].type = t
            arr[i].value = 0
        st = self.lib.vaGetConfigAttributes(
            ctypes.c_void_p(self.dpy), profilo, ingresso, arr, n
        )
        if st != VA_STATUS_SUCCESS:
            return None, self.err(st)
        return {tipi[i]: arr[i].value for i in range(n)}, None

    def crea_config(self, profilo, ingresso, attribs):
        """attribs: lista di (tipo, valore). Torna (config_id, None) o (None, errore)."""
        n = len(attribs)
        arr = (VAConfigAttrib * max(n, 1))()
        for i, (t, v) in enumerate(attribs):
            arr[i].type = t
            arr[i].value = v
        cfg = ctypes.c_uint32(VA_INVALID_ID)
        st = self.lib.vaCreateConfig(
            ctypes.c_void_p(self.dpy),
            profilo,
            ingresso,
            arr if n else None,
            n,
            ctypes.byref(cfg),
        )
        if st != VA_STATUS_SUCCESS:
            return None, f"{self.err(st)} (0x{st & 0xFFFFFFFF:08x})"
        return cfg.value, None

    def rileggi_config(self, config_id):
        """`vaQueryConfigAttributes` — che cosa il driver HA MESSO davvero in quella config.

        ⭐ È questa la riga che verifica l'obbedienza: non quel che si è chiesto, ma quel che
        c'è dentro dopo averlo chiesto.
        """
        n = self.lib.vaMaxNumConfigAttributes(ctypes.c_void_p(self.dpy))
        arr = (VAConfigAttrib * n)()
        prof = ctypes.c_int()
        ingr = ctypes.c_int()
        num = ctypes.c_int(n)
        st = self.lib.vaQueryConfigAttributes(
            ctypes.c_void_p(self.dpy),
            config_id,
            ctypes.byref(prof),
            ctypes.byref(ingr),
            arr,
            ctypes.byref(num),
        )
        if st != VA_STATUS_SUCCESS:
            return None, self.err(st)
        return (
            {
                "profilo": prof.value,
                "ingresso": ingr.value,
                "attributi": {arr[i].type: arr[i].value for i in range(num.value)},
            },
            None,
        )

    def distruggi_config(self, config_id):
        self.lib.vaDestroyConfig(ctypes.c_void_p(self.dpy), config_id)

    def ritmo_dichiarato(self, config_id, livello, qualita, intra=30, ip=1):
        """`vaQueryProcessingRate` — il ritmo che il DRIVER dichiara, in macroblocchi/s.

        ⚠ «dichiarato», non misurato: è una tabella dentro il driver, non un giro sul ferro.
        """
        par = VAProcessingRateParameterEnc()
        par.level_idc = livello
        par.quality_level = qualita
        par.intra_period = intra
        par.ip_period = ip
        ritmo = ctypes.c_uint32(0)
        st = self.lib.vaQueryProcessingRate(
            ctypes.c_void_p(self.dpy),
            config_id,
            ctypes.byref(par),
            ctypes.byref(ritmo),
        )
        if st != VA_STATUS_SUCCESS:
            return None, self.err(st)
        return ritmo.value, None

    def crea_superfici(self, larghezza, altezza, quante, formato=VA_RT_FORMAT_YUV420):
        arr = (ctypes.c_uint32 * quante)()
        st = self.lib.vaCreateSurfaces(
            ctypes.c_void_p(self.dpy),
            ctypes.c_uint(formato),
            ctypes.c_uint(larghezza),
            ctypes.c_uint(altezza),
            arr,
            ctypes.c_uint(quante),
            None,
            ctypes.c_uint(0),
        )
        if st != VA_STATUS_SUCCESS:
            return None, f"{self.err(st)} (0x{st & 0xFFFFFFFF:08x})"
        return arr, None

    def distruggi_superfici(self, arr, quante):
        self.lib.vaDestroySurfaces(ctypes.c_void_p(self.dpy), arr, quante)

    def crea_contesto(self, config_id, larghezza, altezza, superfici, quante):
        ctx = ctypes.c_uint32(VA_INVALID_ID)
        st = self.lib.vaCreateContext(
            ctypes.c_void_p(self.dpy),
            config_id,
            ctypes.c_int(larghezza),
            ctypes.c_int(altezza),
            ctypes.c_int(VA_PROGRESSIVE),
            superfici,
            ctypes.c_int(quante),
            ctypes.byref(ctx),
        )
        if st != VA_STATUS_SUCCESS:
            return None, f"{self.err(st)} (0x{st & 0xFFFFFFFF:08x})"
        return ctx.value, None

    def distruggi_contesto(self, ctx):
        self.lib.vaDestroyContext(ctypes.c_void_p(self.dpy), ctx)


# ─────────────────────────────────────────────────────────────────────────────
# 1 · DICHIARA
# ─────────────────────────────────────────────────────────────────────────────

def modi_dal_valore(valore):
    if valore is None or valore == VA_ATTRIB_NOT_SUPPORTED:
        return None
    return sorted(n for n, v in MODI_BITRATE.items() if valore & v)


def dichiara(nodo):
    esito = {"nodo": nodo, "profili": {}, "ritmi": {}}
    with Va(nodo) as va:
        esito["libva"] = va.versione
        tipi = list(ATTRIBUTI.values())
        nomi_tipo = {v: k for k, v in ATTRIBUTI.items()}
        for nome_p, p in PROFILI.items():
            ing = va.ingressi(p)
            if ing is None:
                continue
            for i in ing:
                if i not in (INGRESSI["VAEntrypointEncSliceLP"],
                             INGRESSI["VAEntrypointEncSlice"],
                             INGRESSI["VAEntrypointEncPicture"]):
                    continue
                nome_i = [k for k, v in INGRESSI.items() if v == i][0]
                att, errore = va.attributi_offerti(p, i, tipi)
                voce = {"errore": errore, "attributi": {}}
                if att:
                    for t, v in att.items():
                        if v == VA_ATTRIB_NOT_SUPPORTED:
                            continue
                        voce["attributi"][nomi_tipo[t]] = v
                    rc = att.get(ATTRIBUTI["VAConfigAttribRateControl"])
                    voce["modi_bitrate"] = modi_dal_valore(rc)
                esito["profili"][f"{nome_p}/{nome_i}"] = voce

        # ── il ritmo dichiarato dal driver, per i due profili che ci interessano ──
        for nome_p in ("VAProfileH264High", "VAProfileHEVCMain10"):
            p = PROFILI[nome_p]
            cfg, errore = va.crea_config(
                p, INGRESSI["VAEntrypointEncSliceLP"],
                [(ATTRIBUTI["VAConfigAttribRTFormat"], VA_RT_FORMAT_YUV420)],
            )
            if cfg is None:
                esito["ritmi"][nome_p] = {"errore": errore, "mb_al_secondo": None}
                continue
            per_qualita = {}
            for q in range(1, 8):
                r, e = va.ritmo_dichiarato(cfg, livello=51, qualita=q)
                per_qualita[q] = r if e is None else None
            esito["ritmi"][nome_p] = {"errore": None, "mb_al_secondo": per_qualita}
            va.distruggi_config(cfg)
    return esito


# ─────────────────────────────────────────────────────────────────────────────
# 2 · OBBEDISCE — `LEZIONI.md` §1.8
# ─────────────────────────────────────────────────────────────────────────────

def obbedisce(nodo, finto_driver=None, finto_permissivo=False):
    """Chiede ogni modo di bitrate PER NOME e guarda che cosa fa il driver.

    ⭐ La verifica è a DUE gradini, e solo il primo è dentro VA-API:
      1. `vaCreateConfig` deve **rifiutare** un modo che non offre — non sostituirlo;
      2. `vaQueryConfigAttributes` dovrebbe dire quale modo è in vigore.

    `finto_driver`: sostituisce la rilettura (guasto «il driver dichiara un altro modo»).
    `finto_permissivo`: fa credere che ogni `vaCreateConfig` sia riuscito
                        (guasto «il driver accetta anche quel che non sa fare»).
    """
    esito = {"nodo": nodo, "prove": []}
    with Va(nodo) as va:
        for nome_p in ("VAProfileH264High", "VAProfileHEVCMain10"):
            p = PROFILI[nome_p]
            offerti, _ = va.attributi_offerti(
                p, INGRESSI["VAEntrypointEncSliceLP"],
                [ATTRIBUTI["VAConfigAttribRateControl"]],
            )
            maschera = offerti[ATTRIBUTI["VAConfigAttribRateControl"]] if offerti else 0
            for nome_rc, val_rc in MODI_BITRATE.items():
                atteso_ok = bool(maschera & val_rc)
                cfg, errore = va.crea_config(
                    p, INGRESSI["VAEntrypointEncSliceLP"],
                    [
                        (ATTRIBUTI["VAConfigAttribRTFormat"], VA_RT_FORMAT_YUV420),
                        (ATTRIBUTI["VAConfigAttribRateControl"], val_rc),
                    ],
                )
                if finto_permissivo and cfg is None:
                    # innesto: si finge un driver che accetta tutto senza dire niente
                    cfg, errore = va.crea_config(
                        p, INGRESSI["VAEntrypointEncSliceLP"],
                        [(ATTRIBUTI["VAConfigAttribRTFormat"], VA_RT_FORMAT_YUV420)],
                    )
                voce = {
                    "profilo": nome_p,
                    "chiesto": nome_rc,
                    "offerto_da_vainfo": atteso_ok,
                    "config_creata": cfg is not None,
                    "errore_creazione": errore,
                    "riletto": None,
                    "ha_obbedito": None,
                }
                if cfg is not None:
                    if finto_driver is not None:
                        letto, e = finto_driver(nome_rc)
                    else:
                        letto, e = va.rileggi_config(cfg)
                    if letto is None:
                        voce["riletto"] = None  # ⛔ None non è zero
                        voce["errore_rilettura"] = e
                    else:
                        v = letto["attributi"].get(ATTRIBUTI["VAConfigAttribRateControl"])
                        voce["riletto"] = modi_dal_valore(v)
                        voce["riletto_grezzo"] = v
                        voce["ha_obbedito"] = voce["riletto"] == [nome_rc]
                    va.distruggi_config(cfg)
                esito["prove"].append(voce)
    return esito


def giudica_obbedienza(esito):
    """Il PRIMO gradino — quello che VA-API può davvero verificare.

    VERDE solo se: ogni modo **offerto** è stato accettato, e ogni modo **non offerto**
    è stato **RIFIUTATO** con un errore, non accettato in silenzio (`LEZIONI.md` §1.8:
    *«quando si chiede un componente per nome, non si ripiega su un altro; si fallisce
    dichiarandolo»*).

    ⛔ Se anche una sola rilettura di una config creata è `None`, il banco si RIFIUTA
    di giudicare: «non ho potuto leggere» non è «va tutto bene».
    """
    if not esito["prove"]:
        return None, "nessuna prova eseguita"
    accettati_a_torto, rifiutati_a_torto, non_letti = [], [], []
    for v in esito["prove"]:
        if v["config_creata"] and v["riletto"] is None:
            non_letti.append(v)
            continue
        if v["offerto_da_vainfo"] and not v["config_creata"]:
            rifiutati_a_torto.append(v)
        if (not v["offerto_da_vainfo"]) and v["config_creata"]:
            accettati_a_torto.append(v)
    if non_letti:
        return None, f"{len(non_letti)} riletture non riuscite: non si giudica"
    if accettati_a_torto:
        nomi = ", ".join(f"{v['profilo']}/{v['chiesto']}" for v in accettati_a_torto)
        return False, (f"⛔ {len(accettati_a_torto)} modi NON offerti accettati "
                       f"in silenzio: {nomi}")
    if rifiutati_a_torto:
        nomi = ", ".join(f"{v['profilo']}/{v['chiesto']}" for v in rifiutati_a_torto)
        return False, f"{len(rifiutati_a_torto)} modi offerti ma rifiutati: {nomi}"
    return True, (f"{len(esito['prove'])} modi chiesti per nome: gli offerti accettati, "
                  f"i non offerti rifiutati con errore")


def la_rilettura_dice_il_modo(esito):
    """Il SECONDO gradino: `vaQueryConfigAttributes` dice *quale* modo è in vigore?

    Torna (vero/falso/None, motivo). ⚠ Se torna falso, la verifica dell'obbedienza
    **non si può chiudere dentro VA-API** e va portata a valle, sul flusso prodotto.
    """
    per_profilo = {}
    for v in esito["prove"]:
        if not v["config_creata"] or v["riletto"] is None:
            continue
        per_profilo.setdefault(v["profilo"], []).append(v)
    if not per_profilo:
        return None, "nessuna config creata: non si giudica"
    dice, maschera = [], []
    for prof, prove in per_profilo.items():
        letture = {tuple(v["riletto"]) for v in prove}
        if all(v["riletto"] == [v["chiesto"]] for v in prove):
            dice.append(prof)
        elif len(letture) == 1 and len(next(iter(letture))) > 1:
            maschera.append(prof)
    if len(dice) == len(per_profilo):
        return True, "la rilettura riporta esattamente il modo chiesto"
    if len(maschera) == len(per_profilo):
        return False, ("⛔ la rilettura riporta la MASCHERA delle capacità, identica per "
                       "ogni richiesta: dentro VA-API non si può sapere quale modo è in "
                       "vigore — si verifica a valle, sul flusso")
    return False, "riletture incoerenti fra profili"


# ─────────────────────────────────────────────────────────────────────────────
# 3 · CONTESTI — quanti se ne aprono, e dove il driver dice di no
# ─────────────────────────────────────────────────────────────────────────────

def contesti(nodo, gradini, larghezza, altezza, profilo="VAProfileH264High",
             superfici_per_contesto=4, un_display_solo=True, tetto_duro=None):
    """Apre N contesti di codifica veri (config + superfici + contesto) e riferisce
    dove il driver si ferma, con l'errore esatto.

    `un_display_solo`: tutti i contesti sullo stesso VADisplay (come farebbe un server a
    un processo). Se falso, ogni contesto ha il suo VADisplay e il suo fd (come farebbero
    N processi separati).
    """
    esito = {"nodo": nodo, "profilo": profilo, "risoluzione": f"{larghezza}x{altezza}",
             "un_display_solo": un_display_solo, "gradini": []}
    p = PROFILI[profilo]
    i = INGRESSI["VAEntrypointEncSliceLP"]
    for n in gradini:
        aperti = 0
        primo_errore = None
        risorse = []
        display = []
        try:
            if un_display_solo:
                va = Va(nodo).apri()
                display.append(va)
            for k in range(n):
                if tetto_duro is not None and aperti >= tetto_duro:
                    primo_errore = f"tetto innestato dal banco a {tetto_duro}"
                    break
                if not un_display_solo:
                    try:
                        va = Va(nodo).apri()
                        display.append(va)
                    except Exception as ex:
                        primo_errore = f"vaInitialize #{k}: {ex}"
                        break
                cfg, errore = va.crea_config(
                    p, i, [(ATTRIBUTI["VAConfigAttribRTFormat"], VA_RT_FORMAT_YUV420),
                           (ATTRIBUTI["VAConfigAttribRateControl"], MODI_BITRATE["VA_RC_CQP"])],
                )
                if cfg is None:
                    primo_errore = f"vaCreateConfig #{k}: {errore}"
                    break
                sup, errore = va.crea_superfici(larghezza, altezza, superfici_per_contesto)
                if sup is None:
                    va.distruggi_config(cfg)
                    primo_errore = f"vaCreateSurfaces #{k}: {errore}"
                    break
                ctx, errore = va.crea_contesto(cfg, larghezza, altezza, sup,
                                               superfici_per_contesto)
                if ctx is None:
                    va.distruggi_superfici(sup, superfici_per_contesto)
                    va.distruggi_config(cfg)
                    primo_errore = f"vaCreateContext #{k}: {errore}"
                    break
                risorse.append((va, cfg, sup, ctx))
                aperti += 1
        finally:
            for va, cfg, sup, ctx in risorse:
                va.distruggi_contesto(ctx)
                va.distruggi_superfici(sup, superfici_per_contesto)
                va.distruggi_config(cfg)
            for va in display:
                va.chiudi()
        esito["gradini"].append({"chiesti": n, "aperti": aperti, "errore": primo_errore})
    return esito


def giudica_contesti(esito, attesi_almeno=16):
    massimo = max((g["aperti"] for g in esito["gradini"]), default=None)
    if massimo is None:
        return None, "nessun gradino eseguito"
    if massimo < attesi_almeno:
        return False, f"solo {massimo} contesti aperti, se ne attendevano ≥ {attesi_almeno}"
    return True, f"{massimo} contesti di codifica aperti insieme"


# ─────────────────────────────────────────────────────────────────────────────
# ⛔ --certifica · il banco non è finito finché non lo si è visto dare ROSSO
# ─────────────────────────────────────────────────────────────────────────────

def certifica(nodo):
    righe = []
    esiti = []

    def registra(nome, sano, guasto, risanato):
        ok = (sano is True) and (guasto is not True) and (risanato is True)
        esiti.append(ok)
        righe.append(
            f"  {'✅' if ok else '⛔'} {nome}: sano={sano} → guasto={guasto} → risanato={risanato}"
        )

    # ── G1 · il driver accetta in silenzio un modo che NON offre (il difetto di v1, §1.8) ──
    reale = obbedisce(nodo)
    s, _ = giudica_obbedienza(reale)
    g, motivo_g = giudica_obbedienza(obbedisce(nodo, finto_permissivo=True))
    r, _ = giudica_obbedienza(obbedisce(nodo))
    registra("G1 driver permissivo (accetta modi che non offre)", s, g, r)
    righe.append(f"      → col guasto il banco ha detto: {motivo_g}")

    # ── G2 · «None non è zero»: la rilettura fallisce → il banco si RIFIUTA di giudicare ──
    def driver_muto(nome_rc):
        return None, "rilettura non riuscita (innesto)"

    g2, motivo2 = giudica_obbedienza(obbedisce(nodo, finto_driver=driver_muto))
    esiti.append(g2 is None)
    righe.append(
        f"  {'✅' if g2 is None else '⛔'} G2 rilettura impossibile: giudizio={g2!r} "
        f"({motivo2}) — atteso None, non False e non True"
    )

    # ── G3 · il conteggio dei contesti: un tetto innestato deve farsi vedere ──
    gr = [1, 2, 4, 8, 16]
    s3, _ = giudica_contesti(contesti(nodo, gr, 1920, 1080), attesi_almeno=16)
    g3, _ = giudica_contesti(contesti(nodo, gr, 1920, 1080, tetto_duro=3), attesi_almeno=16)
    r3, _ = giudica_contesti(contesti(nodo, gr, 1920, 1080), attesi_almeno=16)
    registra("G3 tetto sui contesti", s3, g3, r3)

    # ── G4 · una risoluzione impossibile: errore vero, non «zero contesti» silenzioso ──
    fuori = contesti(nodo, [1], 32768, 32768)
    ok4 = fuori["gradini"][0]["aperti"] == 0 and fuori["gradini"][0]["errore"] is not None
    esiti.append(ok4)
    righe.append(
        f"  {'✅' if ok4 else '⛔'} G4 risoluzione fuori dai limiti: aperti="
        f"{fuori['gradini'][0]['aperti']}, errore={fuori['gradini'][0]['errore']!r}"
    )

    # ── G5 · il metro si tara PRIMA (§1.33): un modo NON offerto deve essere RIFIUTATO ──
    #   Controllo positivo insieme al negativo: VA_RC_CQP c'è, VA_RC_ICQ no.
    positivo = [v for v in reale["prove"]
                if v["profilo"] == "VAProfileH264High" and v["chiesto"] == "VA_RC_CQP"]
    negativo = [v for v in reale["prove"]
                if v["profilo"] == "VAProfileH264High" and v["chiesto"] == "VA_RC_ICQ"]
    ok5 = (bool(positivo) and positivo[0]["config_creata"] is True
           and bool(negativo) and negativo[0]["config_creata"] is False)
    esiti.append(ok5)
    righe.append(
        f"  {'✅' if ok5 else '⛔'} G5 taratura: CQP (offerto) accettato="
        f"{positivo[0]['config_creata'] if positivo else None}, "
        f"ICQ (non offerto) rifiutato={not negativo[0]['config_creata'] if negativo else None}"
    )

    # ── G6 · la rilettura: dice il modo, o la maschera? (fatto, non guasto) ──
    dice, motivo6 = la_rilettura_dice_il_modo(reale)
    righe.append(f"  ⚠ G6 rilettura del modo in vigore: {dice} — {motivo6}")
    esiti.append(dice is not None)

    print("⛔ CERTIFICAZIONE — sano → guasto → risanato")
    print("\n".join(righe))
    tutti = all(esiti)
    print(f"\n{'✅ CERTIFICATO' if tutti else '⛔ NON CERTIFICATO'}: "
          f"{sum(esiti)}/{len(esiti)} guasti visti e risanati")
    return 0 if tutti else 1


# ─────────────────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("modo", nargs="?", default="dichiara",
                    choices=["dichiara", "obbedisce", "contesti"])
    ap.add_argument("--nodo", default="/dev/dri/renderD128")
    ap.add_argument("--gradini", default="1,2,4,8,16,32,64")
    ap.add_argument("--larghezza", type=int, default=1920)
    ap.add_argument("--altezza", type=int, default=1080)
    ap.add_argument("--processi-separati", action="store_true",
                    help="un VADisplay per contesto invece di uno solo")
    ap.add_argument("--certifica", action="store_true")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    if a.nodo.endswith("renderD129"):
        print("⛔ renderD129 è la Radeon: DECISIONI.md §4.6-quinquies lo vieta.", file=sys.stderr)
        return 2

    if a.certifica:
        return certifica(a.nodo)

    if a.modo == "dichiara":
        e = dichiara(a.nodo)
    elif a.modo == "obbedisce":
        e = obbedisce(a.nodo)
        g, motivo = giudica_obbedienza(e)
        e["giudizio"] = g
        e["motivo"] = motivo
        d, motivo_d = la_rilettura_dice_il_modo(e)
        e["rilettura_dice_il_modo"] = d
        e["rilettura_motivo"] = motivo_d
    else:
        gr = [int(x) for x in a.gradini.split(",")]
        e = contesti(a.nodo, gr, a.larghezza, a.altezza,
                     un_display_solo=not a.processi_separati)
        g, motivo = giudica_contesti(e)
        e["giudizio"] = g
        e["motivo"] = motivo
    print(json.dumps(e, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
