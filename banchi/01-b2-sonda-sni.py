#!/usr/bin/env python3
"""01-b2-sonda-sni.py — la prova che costa una connessione ed elimina una candidata.

    python3 01-b2-sonda-sni.py --etichetta ngtcp2 --porta 7447 --atteso passa
    python3 01-b2-sonda-sni.py --etichetta lsquic --porta 7448 --atteso fallisce

---------------------------------------------------------------------------
⛔ CHE COSA MISURA

Una cosa sola: **il server serve il suo certificato a chi NON manda SNI?**

E' il criterio nuovo di `DECISIONI.md` §6.4, nato il 9 agosto 2026 dalla morte
di `lsquic`: in modalita' HTTP/3 quella libreria pretende l'SNI per trovare il
certificato, e chi si collega a un **indirizzo IP** non lo manda — la specifica
del TLS vieta gli indirizzi letterali in quel campo.  E' il caso primario del
prodotto (`SPECIFICHE.md`: l'utente digita `https://<indirizzo>:7447`).

⭐ La regola che ne e' uscita: **si prova per prima, su ogni candidata**.  Qui e'
   costata 333 righe di collante scoperte inutili.

---------------------------------------------------------------------------
⛔ LE QUATTRO GAMBE, E PERCHE' NON BASTA LA PRIMA

  1. senza SNI, contro la candidata      <- la misura
  2. con SNI,   contro la candidata      <- il controllo che DISTINGUE
  3. senza SNI, contro `lsquic`          <- il controllo NEGATIVO
  4. con SNI,   contro `lsquic`          <- che chiude la diagnosi di lsquic

La 2 esiste perche' senza di lei un rosso alla gamba 1 ha due letture
indistinguibili: «la libreria pretende l'SNI» e «il server non e' su, o la
sonda e' rotta».  Se falliscono TUTT'E DUE, il verdetto non e' sulla libreria:
e' sul banco.

Le 3 e 4 non le esegue questo file: le esegue chi lo lancia, puntandolo al
binario di `lsquic` gia' costruito.  ⭐ E la 4 e' l'unica misura NUOVA su
`lsquic`: il 9 agosto si e' letto «SNI is not set» nel suo registro e si e'
concluso — giustamente — che pretende l'SNI.  Ma «fallisce senza» non e'
«riesce con»: finche' nessuno prova la seconda, la diagnosi resta a meta'.

---------------------------------------------------------------------------
⛔ IL DENOMINATORE, cioe' la quarta regola di `LEZIONI.md` §1.9

Una misura deve dichiarare **su che cosa ha guardato**.  Qui i denominatori
sono tre, e si stampano tutti e tre a ogni gamba:

  - ⛔ **che cosa e' finito nel ClientHello**, che NON e' quel che c'e' nella
    configurazione.  `[R]` 10 agosto 2026, letto sul ferro:

        `aioquic/asyncio/client.py:66-67`  se `server_name` e' vuoto, ci mette
                                          l'ospite — ANCHE se e' un IP;
        `aioquic/tls.py:1551-1556`        e poi, al momento di scrivere il
                                          ClientHello, se quel valore e' un
                                          indirizzo IP lo BUTTA e non spedisce
                                          nessuna estensione `server_name`.

    ⚠ Le due righe insieme fanno una trappola: la configurazione dice
      `'192.168.0.2'` e sul filo non va niente.  La prima stesura di questa
      sonda stampava la configurazione e la chiamava «SNI spedito» — cioe'
      dichiarava un denominatore FALSO, che e' peggio di non dichiararne
      nessuno.  Adesso stampa tutt'e due, e dice quale delle due e' il filo;

  - ⭐ **e il testimone indipendente e' `lsquic`**: il suo registro scrive
    «SNI is not set» quando non lo riceve.  E' un programma che non e' nostro,
    che guarda il filo dall'altro capo: e' l'unica conferma di questo
    denominatore che non venga dalla stessa libreria che l'ha prodotto;
  - **l'ALPN chiesto**: senza `h3` non si e' nemmeno in modalita' HTTP/3, che
    e' proprio la modalita' in cui `lsquic` pretende l'SNI;
  - ⭐ **il certificato ricevuto, con la sua impronta**, confrontata con quella
    del file sul disco.  «La stretta di mano riesce» non e' «il certificato e'
    stato servito»: e' il gradino di E1 sotto.  Un server che completasse la
    stretta con un certificato diverso passerebbe il primo controllo e non il
    secondo.
"""
import argparse
import asyncio
import atexit
import base64
import hashlib
import ipaddress
import ssl
import sys

from aioquic.asyncio import connect
from aioquic.h3.connection import H3_ALPN
from aioquic.quic.configuration import QuicConfiguration

PREDEFINITO_CERT = "/media/REMOTIX/b2-certificati/sessione.pem"

# ---------------------------------------------------------------------------
# ⚠ Un difetto di `aioquic` che sporca il banco, contato invece che nascosto.
#
# Il server HTTP/3 apre i suoi flussi unidirezionali di controllo; `aioquic`
# gli costruisce sopra uno `StreamWriter`, e alla chiusura quello prova a
# scrivere la fine del flusso — su un flusso che ha aperto IL PARI, dove non
# si puo' scrivere [R] `quic/connection.py:1388`.  Il raccoglitore dei rifiuti
# di Python stampa una traccia per ciascuno: sei tracce a esecuzione, che
# rendono illeggibile l'unica cosa che si voleva leggere.
#
# ⛔ Non si zittiscono e basta: si CONTANO, e il conto si stampa.  Un banco che
#    nasconde un errore altrui e' un banco che nasconderebbe anche il proprio —
#    ed e' precisamente il `2>/dev/null` che REVIEWER.md §1 punto 4 rifiuta.
_soppresse = []


def _raccogli_inudibili(arg):
    _soppresse.append(f"{type(arg.exc_value).__name__}: {arg.exc_value}")


def _riferisci_inudibili():
    if _soppresse:
        print(f"\n⚠ {len(_soppresse)} tracce di chiusura di aioquic soppresse "
              f"(difetto della libreria, non della misura); la prima era:")
        print(f"   {_soppresse[0]}")


sys.unraisablehook = _raccogli_inudibili
atexit.register(_riferisci_inudibili)


def impronta_del_file(percorso: str):
    """SHA-256 del certificato in forma DER, base64 — la stessa che va nella pagina.

    ⛔ Del certificato, non della chiave pubblica: e' il rilievo R1.14 di
       `RCP.md`, e chi sbaglia ottiene un confronto che non combacia mai.
    """
    try:
        with open(percorso, "rb") as f:
            pem = f.read()
    except OSError as e:
        return None, f"non leggibile: {e}"
    testa = b"-----BEGIN CERTIFICATE-----"
    coda = b"-----END CERTIFICATE-----"
    if testa not in pem or coda not in pem:
        return None, "il file non contiene un certificato PEM"
    corpo = pem.split(testa, 1)[1].split(coda, 1)[0]
    der = base64.b64decode(b"".join(corpo.split()))
    return base64.b64encode(hashlib.sha256(der).digest()).decode(), None


def impronta_ricevuta(protocollo):
    """L'impronta del certificato che il server ha davvero mandato.

    ⚠ Si passa da un attributo privato di `aioquic` (`_quic.tls._peer_certificate`):
      la libreria non espone il certificato del pari sul cliente.  E' dichiarato
      invece che nascosto — se un aggiornamento lo sposta, questa funzione
      restituisce il PERCHE' e la gamba lo stampa, invece di far sparire il
      controllo piu' importante in silenzio.
    """
    try:
        cert = protocollo._quic.tls._peer_certificate
    except AttributeError as e:
        return None, f"aioquic non espone piu' il certificato del pari ({e})"
    if cert is None:
        return None, "nessun certificato registrato"
    try:
        from cryptography.hazmat.primitives.serialization import Encoding

        der = cert.public_bytes(Encoding.DER)
    except Exception as e:  # noqa: BLE001 — si dichiara, non si indovina
        return None, f"non convertibile in DER: {type(e).__name__}: {e}"
    return base64.b64encode(hashlib.sha256(der).digest()).decode(), None


def sni_sul_filo(valore):
    """Che cosa finisce DAVVERO nell'estensione `server_name` del ClientHello.

    ⛔ Si applica la stessa regola di `aioquic/tls.py:1551-1556` [R]: un
       indirizzo IP viene buttato.  E' una lettura, non una misura — per
       questo la sonda la stampa accanto al valore configurato invece che al
       posto suo, e per questo il registro di `lsquic` la conferma dall'altro
       capo del filo.
    """
    if valore is None:
        return None
    try:
        ipaddress.ip_address(valore)
    except ValueError:
        return valore
    return None


async def gamba(indirizzo: str, porta: int, sni: str, attesa: float):
    """Una connessione sola.  `sni` e' il valore da configurare (o None)."""
    righe = []
    conf = QuicConfiguration(is_client=True, alpn_protocols=H3_ALPN)
    # ⛔ Dichiarato: qui NON si verifica il certificato, come nel cliente di
    #    prova.  Un browser lo verifica per impronta; noi l'impronta la
    #    confrontiamo a mano, qui sotto, che e' la stessa cosa fatta a vista.
    conf.verify_mode = ssl.CERT_NONE

    # ⚠ Il controllo «con SNI» usa un NOME, non l'indirizzo.  La prima stesura
    #   ci metteva l'IP e non controllava niente: `aioquic` lo buttava, il filo
    #   restava identico alla gamba senza SNI, e le due gambe misuravano la
    #   stessa cosa mentre la sonda dichiarava che erano opposte.
    #   ⛔ Il nome NON deve combaciare col certificato: qui non si verifica
    #      niente: serve solo a far comparire l'estensione sul filo.
    if sni is not None:
        conf.server_name = sni

    def denominatori():
        filo = sni_sul_filo(conf.server_name)
        return [
            f"server_name configurato: {conf.server_name!r}",
            f"⭐ SNI sul filo         : {filo!r}"
            + ("   (aioquic butta gli indirizzi IP, tls.py:1551)" if filo is None else ""),
            f"ALPN chiesto           : {conf.alpn_protocols}",
        ]

    try:
        async with connect(indirizzo, porta, configuration=conf) as cliente:
            await asyncio.wait_for(cliente.wait_connected(), timeout=attesa)
            # I denominatori si leggono DOPO: `connect` riempie da se'
            # `server_name`, ed e' proprio quel che si vuole vedere.
            righe.extend(denominatori())
            imp, perche = impronta_ricevuta(cliente)
            if imp is None:
                righe.append(f"certificato ricevuto   : ⚠ non leggibile — {perche}")
            else:
                righe.append(f"certificato ricevuto   : {imp}")
            # ⚠ Chiusura ordinata: senza, `aioquic` lascia dei flussi aperti e
            #   il raccoglitore dei rifiuti di Python stampa una pila di
            #   tracce a fine programma.  Sono innocue e rendono illeggibile
            #   un banco, che e' un difetto in se'.
            cliente.close()
            await cliente.wait_closed()
            return True, righe, imp
    except Exception as e:  # noqa: BLE001 — il tipo dell'errore E' la misura
        righe.extend(denominatori())
        righe.append(f"fallita                : {type(e).__name__}: {e}")
        return False, righe, None


async def principale(a) -> int:
    atteso_ip = None
    try:
        ipaddress.ip_address(a.indirizzo)
        atteso_ip = True
    except ValueError:
        atteso_ip = False

    imp_file, perche = impronta_del_file(a.certificato)

    print(f"== la sonda SNI  ->  {a.indirizzo}:{a.porta}   ({a.etichetta})")
    print(f"   atteso SENZA SNI: {a.atteso}")
    print(f"   l'indirizzo e' un IP letterale: {atteso_ip}"
          + ("" if atteso_ip else "   ⚠ allora 'senza SNI' non e' il caso del prodotto"))
    if imp_file is None:
        print(f"   ⚠ impronta attesa NON disponibile ({perche}): il confronto salta")
    else:
        print(f"   impronta attesa dal file {a.certificato}:")
        print(f"      {imp_file}")
    print()

    esiti = {}
    for nome, sni in (("SENZA SNI", None), ("CON SNI", a.sni_controllo)):
        print(f"-- gamba: {nome}"
              + (f"   (nome usato: {sni})" if sni else ""))
        riuscita, righe, imp = await gamba(a.indirizzo, a.porta, sni, a.attesa)
        for r in righe:
            print(f"   {r}")
        # ⛔ Il secondo gradino: la stretta riesce E il certificato e' QUELLO.
        combacia = None
        if riuscita and imp_file is not None and imp is not None:
            combacia = imp == imp_file
            print(f"   impronta combacia   : {'si' if combacia else '⛔ NO'}")
        print(f"   ⇒ {'riuscita' if riuscita else 'FALLITA'}")
        print()
        esiti[nome] = (riuscita, combacia)

    senza, senza_comb = esiti["SENZA SNI"]
    con, _ = esiti["CON SNI"]

    print("== Verdetto")
    # ⛔ Prima di leggere la gamba 1 come un fatto sulla libreria, si esclude
    #    che sia un fatto sul banco.  E' il controllo che nelle due revisioni
    #    del 9 agosto cadeva sempre: quello che dice «non lo so».
    if not senza and not con:
        print("   ⚠ TUTT'E DUE le gambe sono fallite.")
        print("   ⛔ Questo NON e' un verdetto sulla libreria: e' un verdetto sul banco.")
        print("      il server non e' in ascolto, oppure la porta e' un'altra, oppure")
        print("      la sonda non arriva.  Nessuna riga su §6.4 si scrive da qui.")
        return 3

    if senza:
        print(f"   ⭐ {a.etichetta} SERVE il certificato senza SNI.")
        if senza_comb is False:
            print("   ⛔ ma l'impronta NON combacia: ha servito un ALTRO certificato.")
            print("      la stretta di mano riesce e il criterio non e' soddisfatto.")
        elif senza_comb is None:
            print("   ⚠ l'impronta non e' stata confrontata (vedi sopra): il criterio")
            print("     e' soddisfatto sulla stretta di mano, non sul certificato.")
    else:
        print(f"   ⛔ {a.etichetta} NON serve il certificato senza SNI.")
        if con:
            print("   ⇒ e con l'SNI riesce: il difetto e' l'SNI, non altro.")
            print("      e' la malattia di lsquic, e il criterio di §6.4 elimina la candidata.")
        else:
            print("   ⚠ e con l'SNI non e' stato possibile stabilirlo.")

    # L'esito d'uscita segue l'ATTESO dichiarato, non la riuscita: un banco che
    # attende un rosso e ottiene un verde ha trovato qualcosa, e deve dirlo.
    voluto = (a.atteso == "passa")
    if senza == voluto:
        print(f"\n   ✅ come atteso ({a.atteso})")
        return 0
    print(f"\n   ⛔ NON come atteso: atteso '{a.atteso}', misurato "
          f"'{'passa' if senza else 'fallisce'}' — va scritto perche'")
    return 1


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="serve il certificato a chi non manda SNI?")
    p.add_argument("--indirizzo", default="192.168.0.2")
    p.add_argument("--porta", type=int, default=7447)
    p.add_argument("--etichetta", default="candidata")
    p.add_argument("--certificato", default=PREDEFINITO_CERT)
    p.add_argument("--atteso", choices=("passa", "fallisce"), default="passa")
    # ⚠ Un nome, non un indirizzo: e' l'unico modo di far comparire davvero
    #   l'estensione `server_name` sul filo (vedi `sni_sul_filo`).
    p.add_argument("--sni-controllo", default="remotix.prova",
                   help="il nome usato dalla gamba di controllo")
    p.add_argument("--attesa", type=float, default=8.0)
    a = p.parse_args()
    try:
        sys.exit(asyncio.run(principale(a)))
    except KeyboardInterrupt:
        sys.exit(130)
