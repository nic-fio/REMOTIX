//! Traduzione dei tasti dal linguaggio di RDP a quello di Linux.
//!
//! # Le due lingue
//!
//! RDP parla di **posizioni sulla tastiera**, non di lettere: manda lo scancode
//! del set 1 dei PC IBM, cioe' il numero che la tastiera genera per il tasto
//! *fisico* premuto, piu' un bit che dice se lo scancode era preceduto da 0xE0
//! — il prefisso che distingue, per esempio, l'invio del tastierino dall'invio
//! grande.
//!
//! Linux parla di **codici evdev**, che sono un'altra numerazione delle stesse
//! posizioni fisiche. Mutter accetta questi ultimi.
//!
//! Sulle prime ottantotto posizioni le due numerazioni coincidono per
//! costruzione — `KEY_ESC` vale 1 come lo scancode di Esc — ma la coincidenza
//! ha buchi, e sui tasti estesi non vale affatto. Serve quindi una tabella.
//!
//! # Da dove viene la tabella
//!
//! Da `common/scancode.c` di xrdp, che a sua volta la deriva da
//! `/usr/share/X11/xkb/keycodes/evdev`. Li' i codici sono quelli di X11, che
//! valgono evdev + 8: la tabella qui sotto e' la stessa con l'otto gia'
//! sottratto. E' stata trascritta da un programma, non a mano.
//!
//! # Cosa non si traduce, e perche' si accetta
//!
//! **Pausa.** Sulla tastiera vera e' l'unico tasto col prefisso 0xE1, e RDP lo
//! segnala con un flag che IronRDP non ci consegna: ci arriva come 0x1D, cioe'
//! Ctrl sinistro. Preme e rilascia un Ctrl a vuoto, che e' innocuo.
//!
//! **La disposizione.** Mandando posizioni fisiche, la lettera che ne esce la
//! decide la disposizione configurata **dentro** la sessione remota. Se il
//! client ha una tastiera italiana e la sessione e' configurata americana, i
//! simboli non corrispondono. Farle combaciare e' materia della fase 5: qui si
//! rimedia in parte con gli eventi Unicode, che alcuni client mandano per i
//! caratteri che la loro disposizione non colloca su nessun tasto.

/// Scancode RDP — con `0x100` a marcare quelli estesi — e codice evdev.
///
/// Ordinata per scancode: la ricerca e' binaria.
const SCANCODE_A_EVDEV: &[(u16, u16)] = &[
    (0x001, 1),   // VK_ESCAPE ESC
    (0x002, 2),   // VK_1 AE01
    (0x003, 3),   // VK_2 AE02
    (0x004, 4),   // VK_3 AE03
    (0x005, 5),   // VK_4 AE04
    (0x006, 6),   // VK_5 AE05
    (0x007, 7),   // VK_6 AE06
    (0x008, 8),   // VK_7 AE07
    (0x009, 9),   // VK_8 AE08
    (0x00a, 10),  // VK_9 AE09
    (0x00b, 11),  // VK_0 AE10
    (0x00c, 12),  // VK_OEM_MINUS AE11
    (0x00d, 13),  // VK_OEM_PLUS AE12
    (0x00e, 14),  // VK_BACK BKSP
    (0x00f, 15),  // VK_TAB TAB
    (0x010, 16),  // VK_Q AD01
    (0x011, 17),  // VK_W AD02
    (0x012, 18),  // VK_E AD03
    (0x013, 19),  // VK_R AD04
    (0x014, 20),  // VK_T AD05
    (0x015, 21),  // VK_Y AD06
    (0x016, 22),  // VK_U AD07
    (0x017, 23),  // VK_I AD08
    (0x018, 24),  // VK_O AD09
    (0x019, 25),  // VK_P AD10
    (0x01a, 26),  // VK_OEM_4 AD11
    (0x01b, 27),  // VK_OEM_6 AD12
    (0x01c, 28),  // VK_RETURN RTRN
    (0x01d, 29),  // VK_LCONTROL LCTL
    (0x01e, 30),  // VK_A AC01
    (0x01f, 31),  // VK_S AC02
    (0x020, 32),  // VK_D AC03
    (0x021, 33),  // VK_F AC04
    (0x022, 34),  // VK_G AC05
    (0x023, 35),  // VK_H AC06
    (0x024, 36),  // VK_J AC07
    (0x025, 37),  // VK_K AC08
    (0x026, 38),  // VK_L AC09
    (0x027, 39),  // VK_OEM_1 AC10
    (0x028, 40),  // VK_OEM_7 AC11
    (0x029, 41),  // VK_OEM_3 TLDE
    (0x02a, 42),  // VK_LSHIFT LFSH
    (0x02b, 43),  // VK_OEM_5 BKSL
    (0x02c, 44),  // VK_Z AB01
    (0x02d, 45),  // VK_X AB02
    (0x02e, 46),  // VK_C AB03
    (0x02f, 47),  // VK_V AB04
    (0x030, 48),  // VK_B AB05
    (0x031, 49),  // VK_N AB06
    (0x032, 50),  // VK_M AB07
    (0x033, 51),  // VK_OEM_COMMA AB08
    (0x034, 52),  // VK_OEM_PERIOD AB09
    (0x035, 53),  // VK_OEM_2 AB10
    (0x036, 54),  // VK_RSHIFT RTSH
    (0x037, 55),  // VK_MULTIPLY KPMU
    (0x038, 56),  // VK_LMENU LALT
    (0x039, 57),  // VK_SPACE SPCE
    (0x03a, 58),  // VK_CAPITAL CAPS
    (0x03b, 59),  // VK_F1 FK01
    (0x03c, 60),  // VK_F2 FK02
    (0x03d, 61),  // VK_F3 FK03
    (0x03e, 62),  // VK_F4 FK04
    (0x03f, 63),  // VK_F5 FK05
    (0x040, 64),  // VK_F6 FK06
    (0x041, 65),  // VK_F7 FK07
    (0x042, 66),  // VK_F8 FK08
    (0x043, 67),  // VK_F9 FK09
    (0x044, 68),  // VK_F10 FK10
    (0x045, 69),  // VK_NUMLOCK NMLK
    (0x046, 70),  // VK_SCROLL SCLK
    (0x047, 71),  // VK_HOME KP7
    (0x048, 72),  // VK_UP KP8
    (0x049, 73),  // VK_PRIOR KP9
    (0x04a, 74),  // VK_SUBTRACT KPSU
    (0x04b, 75),  // VK_LEFT KP4
    (0x04c, 76),  // VK_CLEAR KP5
    (0x04d, 77),  // VK_RIGHT KP6
    (0x04e, 78),  // VK_ADD KPAD
    (0x04f, 79),  // VK_END KP1
    (0x050, 80),  // VK_DOWN KP2
    (0x051, 81),  // VK_NEXT KP3
    (0x052, 82),  // VK_INSERT KP0
    (0x053, 83),  // VK_DELETE KPDL
    (0x056, 86),  // VK_OEM_102 LSGT
    (0x057, 87),  // VK_F11 FK11
    (0x058, 88),  // VK_F12 FK12
    (0x070, 93),  // HKTG
    (0x073, 89),  // VK_ABNT_C1 AB11
    (0x079, 92),  // HENK
    (0x07b, 94),  // VK_OEM_PA1 MUHE
    (0x07d, 124), // AE13
    (0x07e, 121), // VK_ABNT_C2 KPPT (ABNT2 brasiliana)
    (0x110, 165), // VK_MEDIA_PREV_TRACK KEY_PREVIOUSSONG
    (0x119, 163), // VK_MEDIA_NEXT_TRACK KEY_NEXTSONG
    (0x11c, 96),  // VK_RETURN KPEN
    (0x11d, 97),  // VK_RCONTROL RCTL
    (0x120, 113), // VK_VOLUME_MUTE MUTE
    (0x121, 140), // VK_LAUNCH_APP2 KEY_CALC
    (0x122, 164), // VK_PLAY_PAUSE KEY_PLAYPAUSE
    (0x124, 166), // VK_MEDIA_STOP KEY_STOPCD
    (0x12e, 114), // VK_VOLUME_DOWN VOL-
    (0x130, 115), // VK_VOLUME_UP VOL+
    (0x132, 172), // VK_BROWSER_HOME KEY_HOMEPAGE
    (0x135, 98),  // VK_DIVIDE KPDV
    (0x137, 99),  // VK_SNAPSHOT PRSC
    (0x138, 100), // VK_RMENU RALT
    (0x147, 102), // VK_HOME HOME
    (0x148, 103), // VK_UP UP
    (0x149, 104), // VK_PRIOR PGUP
    (0x14b, 105), // VK_LEFT LEFT
    (0x14d, 106), // VK_RIGHT RGHT
    (0x14f, 107), // VK_END END
    (0x150, 108), // VK_DOWN DOWN
    (0x151, 109), // VK_NEXT PGDN
    (0x152, 110), // VK_INSERT INS
    (0x153, 111), // VK_DELETE DELE
    (0x15b, 125), // VK_LWIN LWIN
    (0x15c, 126), // VK_RWIN RWIN
    (0x15d, 127), // VK_APPS COMP
    (0x165, 217), // VK_BROWSER_SEARCH KEY_SEARCH
    (0x166, 156), // VK_BROWSER_FAVORITES KEY_BOOKMARKS
    (0x16b, 157), // VK_LAUNCH_APP1 KEY_COMPUTER
    (0x16c, 155), // VK_LAUNCH_MAIL KEY_MAIL
];

/// Codici evdev dei tasti a scatto, per la sincronizzazione all'aggancio.
pub const EVDEV_BLOC_MAIUSC: u16 = 58;
pub const EVDEV_BLOC_NUM: u16 = 69;
pub const EVDEV_BLOC_SCORR: u16 = 70;

/// Traduce uno scancode RDP nel codice evdev della stessa posizione fisica.
///
/// Restituisce `None` per le posizioni che la tabella non conosce: si preferisce
/// non premere nulla piuttosto che premere il tasto sbagliato.
pub fn evdev_da_scancode(codice: u8, esteso: bool) -> Option<u16> {
    let chiave = if esteso {
        0x100 | u16::from(codice)
    } else {
        u16::from(codice)
    };
    SCANCODE_A_EVDEV
        .binary_search_by_key(&chiave, |(scancode, _)| *scancode)
        .ok()
        .map(|posizione| SCANCODE_A_EVDEV[posizione].1)
}

/// Traduce un carattere Unicode nel keysym di X che lo produce.
///
/// Serve agli eventi Unicode di RDP, che alcuni client mandano al posto dello
/// scancode quando il carattere non sta su nessun tasto della loro
/// disposizione. La regola e' quella di X: i caratteri di Latin-1 hanno il
/// keysym uguale al proprio codice, tutti gli altri si ottengono sommando
/// `0x0100_0000`.
///
/// Restituisce `None` per le meta' di coppia surrogata di UTF-16: prese da sole
/// non sono un carattere, e RDP le consegna una per volta senza modo di
/// riunirle.
pub fn keysym_da_unicode(unita: u16) -> Option<u32> {
    if (0xd800..=0xdfff).contains(&unita) {
        return None;
    }
    let codice = u32::from(unita);
    // I caratteri di controllo non hanno keysym proprio: si lasciano allo
    // scancode, che il client manda comunque.
    if codice < 0x20 || (0x7f..0xa0).contains(&codice) {
        return None;
    }
    if codice <= 0xff {
        Some(codice)
    } else {
        Some(0x0100_0000 | codice)
    }
}

#[cfg(test)]
mod prove {
    use super::*;

    #[test]
    fn la_tabella_e_ordinata_e_senza_doppioni() {
        // La ricerca e' binaria: se l'ordine si rompe, la traduzione restituisce
        // silenziosamente il tasto sbagliato invece di fallire.
        for coppia in SCANCODE_A_EVDEV.windows(2) {
            assert!(
                coppia[0].0 < coppia[1].0,
                "tabella fuori ordine fra {:#05x} e {:#05x}",
                coppia[0].0,
                coppia[1].0
            );
        }
    }

    #[test]
    fn le_posizioni_di_riferimento() {
        assert_eq!(evdev_da_scancode(0x01, false), Some(1)); // Esc
        assert_eq!(evdev_da_scancode(0x1e, false), Some(30)); // A
        assert_eq!(evdev_da_scancode(0x1d, false), Some(29)); // Ctrl sinistro
        assert_eq!(evdev_da_scancode(0x1d, true), Some(97)); // Ctrl destro
        assert_eq!(evdev_da_scancode(0x1c, false), Some(28)); // Invio
        assert_eq!(evdev_da_scancode(0x1c, true), Some(96)); // Invio del tastierino
        assert_eq!(evdev_da_scancode(0x53, true), Some(111)); // Canc
        assert_eq!(evdev_da_scancode(0x53, false), Some(83)); // Canc del tastierino
        assert_eq!(evdev_da_scancode(0x5b, true), Some(125)); // tasto Windows
    }

    #[test]
    fn le_posizioni_sconosciute_non_premono_nulla() {
        assert_eq!(evdev_da_scancode(0x54, false), None);
        assert_eq!(evdev_da_scancode(0x00, false), None);
        assert_eq!(evdev_da_scancode(0x01, true), None);
    }

    #[test]
    fn i_keysym() {
        assert_eq!(keysym_da_unicode(u16::from(b'a')), Some(0x61));
        assert_eq!(keysym_da_unicode(0x00e8), Some(0x00e8)); // e' accentata
        assert_eq!(keysym_da_unicode(0x20ac), Some(0x0100_20ac)); // euro
        assert_eq!(keysym_da_unicode(0x000d), None); // invio
        assert_eq!(keysym_da_unicode(0xd83d), None); // meta' di surrogata
    }
}
