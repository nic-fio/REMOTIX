#!/usr/bin/env python3
# Applica le tre modifiche REMOTIX all'albero b/ (gnome-shell 50.3).
import io, os, sys

B = '/var/tmp/rmx-L2/b'

def sostituisci(path, vecchio, nuovo):
    p = os.path.join(B, path)
    s = io.open(p, encoding='utf-8').read()
    if s.count(vecchio) != 1:
        sys.exit('ANCORA NON UNICA in %s: %d occorrenze' % (path, s.count(vecchio)))
    io.open(p, 'w', encoding='utf-8').write(s.replace(vecchio, nuovo))
    print('ok %s' % path)

# --- 1. loginManager.js: l'unica copia della regola -----------------------
v = """/**
 * @returns {boolean}
 */
export function canLock() {"""
n = """/**
 * REMOTIX — IL BLOCCO SCHERMO, IN UNA SESSIONE REMOTA, È UNA DISCONNESSIONE.
 *
 * Ogni sessione ripassa dalla PROPRIA porta d'ingresso: la grafica locale da
 * GDM, la remota dal greeter di REMOTIX.  Non è una scorciatoia: lo sblocco di
 * GNOME passa dal canale di riautenticazione di gdm (js/gdm/util.js) e la
 * sessione remota NON è avviata da gdm — lasciare chiudere la serratura interna
 * significa consegnare all'utente una schermata di blocco che non si sblocca.
 *
 * Il nome `org.gnome.SessionManager` in questa sessione è di REMOTIX (il
 * gnome-session vero non c'è), quindi la chiamata resta in casa.  L'interfaccia
 * è a parte — `.Remotix` — perché `Detach` non esiste in gnome-session e
 * appenderla all'interfaccia standard sarebbe una bugia sul bus.
 *
 * Asincrona di proposito: chi chiama è dentro un gestore di eventi della shell,
 * e una chiamata sincrona lo fermerebbe finché il server non risponde.  Se la
 * chiamata fallisce NON si ripiega sul blocco vero: meglio un gesto che non fa
 * niente e lo scrive nel journal che una schermata senza uscita.
 *
 * @param {string} motivo - finisce nel journal del server
 */
export function remotixDetach(motivo) {
    Gio.DBus.session.call(
        'org.gnome.SessionManager',
        '/org/gnome/SessionManager',
        'org.gnome.SessionManager.Remotix',
        'Detach',
        new GLib.Variant('(s)', [motivo]),
        null, Gio.DBusCallFlags.NONE, -1, null,
        (conn, res) => {
            try {
                conn.call_finish(res);
            } catch (e) {
                logError(e, `REMOTIX: Detach (${motivo}) non riuscita`);
            }
        });
}

/**
 * @returns {boolean}
 */
export function canLock() {"""
sostituisci('js/misc/loginManager.js', v, n)

# --- 2a. systemActions.js: la voce non dipende dal gdm dell'host ----------
v = """        this._actions.get(LOCK_SCREEN_ACTION_ID).available = showLock && allowLockScreen && LoginManager.canLock();"""
n = """        // REMOTIX: via la dipendenza da LoginManager.canLock(), che interroga
        // org.gnome.DisplayManager sul bus di SISTEMA (loginManager.js:38-54) e
        // su un host senza gdm torna false.  Senza questa riga la voce «Blocca»
        // sparirebbe dal menu per una proprietà dell'HOST che con la sessione
        // remota non c'entra: da noi il gesto non chiude nessuna serratura,
        // disconnette, e non ha bisogno del display manager di nessuno.
        //
        // `allowLockScreen` RESTA: è org.gnome.desktop.lockdown/disable-lock-screen,
        // cioè il modo dell'operatore di togliere del tutto la voce.  Toglierlo
        // anche da qui gli porterebbe via l'interruttore.
        this._actions.get(LOCK_SCREEN_ACTION_ID).available = showLock && allowLockScreen;"""
sostituisci('js/misc/systemActions.js', v, n)

# --- 2b. systemActions.js: la voce di menu -------------------------------
v = """    activateLockScreen() {
        if (!this._actions.get(LOCK_SCREEN_ACTION_ID).available)
            throw new Error('The lock-screen action is not available!');

        Main.screenShield.lock(true);
    }"""
n = """    activateLockScreen() {
        if (!this._actions.get(LOCK_SCREEN_ACTION_ID).available)
            throw new Error('The lock-screen action is not available!');

        // REMOTIX: bloccare, in remoto, è disconnettersi.
        //
        // E la chiamata NON passa da Main.screenShield, che qui può essere
        // `null`: main.js:237-238 lo costruisce solo se LoginManager.canLock(),
        // e con la riga qui sopra la voce esiste anche dove quello è falso.
        // Andare comunque per screenShield.lock() darebbe un TypeError dentro
        // il gestore del clic — cioè un menu che non risponde e una riga di
        // JS nel journal, invece di un gesto.
        LoginManager.remotixDetach('voce «Blocca» del menu di sistema');
    }"""
sostituisci('js/misc/systemActions.js', v, n)

# --- 3. screenShield.js: la strozzatura di TUTTI gli altri gesti ----------
v = """    lock(animate) {
        if (this._lockSettings.get_boolean(DISABLE_LOCK_KEY)) {"""
n = """    lock(animate) {
        // REMOTIX: la strozzatura.  Qui dentro passano TUTTI i gesti di blocco
        // che non sono la voce di menu, e vanno deviati tutti allo stesso modo:
        //
        //   - Super+L      → gsd-media-keys → org.gnome.ScreenSaver.Lock →
        //                    shellDBus.js:539-547 (LockAsync) → lock(true);
        //   - loginctl lock-session → segnale `Lock` di logind, agganciato in
        //                    screenShield.js:150-151 → lock(false);
        //   - inattività   → activate() arma un timeout che chiama lock(false)
        //                    (screenShield.js:258-269), se `lock-enabled`;
        //   - lockIfWasLocked() dopo un crash della shell.
        //
        // Deviare solo `activateLockScreen()` ne coprirebbe UNO su cinque, e gli
        // altri quattro produrrebbero la schermata che non si sblocca — che è
        // precisamente il guasto che questa patch esiste per non avere.
        //
        // Prima del controllo su DISABLE_LOCK_KEY di proposito: anche con la
        // serratura disarmata per politica il gesto deve fare QUALCOSA di
        // sensato, non tornare indietro in silenzio.
        LoginManager.remotixDetach(`blocco schermo (animate=${animate})`);
        return;

        /* Da qui in giù c'è il blocco VERO di GNOME, ed è irraggiungibile.
         * Non è stato cancellato apposta: così, al prossimo aggiornamento di
         * gnome-shell, `patch` fallisce se upstream ha toccato queste righe e
         * la deviazione si RIVERIFICA invece di essere riscritta a memoria. */
        if (this._lockSettings.get_boolean(DISABLE_LOCK_KEY)) {"""
sostituisci('js/ui/screenShield.js', v, n)
