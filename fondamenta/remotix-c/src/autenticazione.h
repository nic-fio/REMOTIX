/*
 * autenticazione — PAM, e la guardia che parte da negato.
 *
 * Due regole, e nessuna delle due e' ovvia:
 *
 * R14 — senza NLA l'autenticazione avviene DENTRO il Client Info PDU, e un
 * client puo' non mandare credenziali affatto.  Un server che valida «se ci
 * sono credenziali» non valida niente.  Qui la guardia parte da negato e solo
 * un esito positivo la apre.
 *
 * §3.4 di SPECIFICA.md — PAM risponde a una domanda diversa da quella che
 * interessa: dice «questa credenziale e' buona», non «questa persona ha
 * diritto a QUESTA sessione».  Poiche' REMOTIX serve una sola sessione,
 * qualunque altro utente della macchina, con la propria password vera, si
 * troverebbe dentro il desktop di un altro.  Il confronto si fa PRIMA di PAM,
 * e con l'utente ricavato dall'uid EFFETTIVO del processo — non da $USER, che
 * e' una convenzione e puo' parlare di qualcun altro.
 */
#pragma once

#include <glib.h>

/* L'utente di cui REMOTIX serve la sessione, dall'uid effettivo.
 * Restituisce NULL se non lo si riesce a stabilire: in quel caso il server non
 * deve partire, perche' non sa di chi sia la sessione che serve. */
const char *autenticazione_utente_atteso(void);

/* Verifica nome e password. Il nome viene confrontato con l'utente atteso
 * PRIMA di interpellare PAM. */
gboolean autenticazione_verifica(const char *utente, const char *dominio, const char *parola);
