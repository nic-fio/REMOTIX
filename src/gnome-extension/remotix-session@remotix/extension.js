// REMOTIX — the GNOME Shell side of DECISIONS.md §10.49.
//
// Inside a REMOTIX session the menu must NOT offer «Power Off…», «Restart…»
// nor «Suspend»; «Log Out…» stays (§4.1-ter).  The director's ruling, 11 Oct
// 2026: «quelle voci di menu non devono comparire. Questa e' una feature del
// prodotto».
//
// [R] gnome-shell 48.7, js/misc/systemActions.js:340-374: power-off and restart
//     follow gnome-session's CanShutdown, suspend follows logind's CanSuspend,
//     and ⛔ no key hides them in a user session (`disable-restart-buttons`
//     is the login screen's; `disable-log-out` would take «Log Out…» away too).
// ⇒ This extension forces the three actions to «not available» after the
//   Shell computes them.  What reads them follows: the system menu
//   (ui/status/system.js) and the search results for «power off» & co.
//
// ⭐ It is enabled ONLY in the session dconf (D-015, src/session.c,
//   `gnome_power_entries()`): the user at the monitor never runs it.
// ⛔ It does not stop anything from happening: it only removes the entries.

import {Extension} from 'resource:///org/gnome/shell/extensions/extension.js';
import * as SystemActions from 'resource:///org/gnome/shell/misc/systemActions.js';

// method that computes the actions → the actions it computes, and their properties
const HIDDEN = {
    _updatePowerOff: [['power-off', 'can-power-off'], ['restart', 'can-restart']],
    _updateSuspend: [['suspend', 'can-suspend']],
};

export default class RemotixSession extends Extension {
    enable() {
        const actions = SystemActions.getDefault();
        const proto = Object.getPrototypeOf(actions);

        this._saved = {};
        for (const [method, hidden] of Object.entries(HIDDEN)) {
            const original = proto[method];

            if (typeof original !== 'function') {
                console.warn(`REMOTIX: SystemActions.${method} is not there on this Shell: ` +
                    `${hidden.map(h => h[0]).join(', ')} NOT hidden`);
                continue;
            }
            this._saved[method] = original;
            proto[method] = function (...args) {
                original.apply(this, args);
                for (const [id, property] of hidden) {
                    const action = this._actions?.get(id);

                    if (action && action.available) {
                        action.available = false;
                        this.notify(property);
                    }
                }
            };
            actions[method]();
        }
        console.log('REMOTIX: Power Off, Restart and Suspend hidden in this session');
    }

    disable() {
        const actions = SystemActions.getDefault();
        const proto = Object.getPrototypeOf(actions);

        for (const [method, original] of Object.entries(this._saved ?? {})) {
            proto[method] = original;
            actions[method]();
        }
        this._saved = null;
    }
}
