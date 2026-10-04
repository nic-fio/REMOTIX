#!/usr/bin/env python3
# 11-pam-root-negato.py — dentro una scatola, da root: la catena PAM «remotix» del prodotto (D3) deve
# respingere root PER L ELENCO (/etc/remotix/utenti-negati, nel registro «pam_listfile … Refused user root»)
# e far entrare nictest con la sua parola.  [M] 3 ott 2026: 4/4 scatole.
import ctypes, ctypes.util, sys
pam = ctypes.CDLL(ctypes.util.find_library("pam"))
class Msg(ctypes.Structure): _fields_=[("style",ctypes.c_int),("msg",ctypes.c_char_p)]
class Resp(ctypes.Structure): _fields_=[("resp",ctypes.c_char_p),("code",ctypes.c_int)]
CONV=ctypes.CFUNCTYPE(ctypes.c_int,ctypes.c_int,ctypes.POINTER(ctypes.POINTER(Msg)),ctypes.POINTER(ctypes.POINTER(Resp)),ctypes.c_void_p)
class Conv(ctypes.Structure): _fields_=[("conv",CONV),("data",ctypes.c_void_p)]
libc=ctypes.CDLL(ctypes.util.find_library("c")); libc.calloc.restype=ctypes.c_void_p; libc.strdup.restype=ctypes.c_void_p
def prova(utente, parola):
    def conv(n,msgs,resp,d):
        a=libc.calloc(n,ctypes.sizeof(Resp)); r=ctypes.cast(a,ctypes.POINTER(Resp))
        for i in range(n): r[i].resp=ctypes.cast(libc.strdup(parola.encode()),ctypes.c_char_p); r[i].code=0
        resp[0]=r; return 0
    c=CONV(conv); h=ctypes.c_void_p()
    pam.pam_start(b"remotix",utente.encode(),ctypes.byref(Conv(c,None)),ctypes.byref(h))
    rc=pam.pam_authenticate(h,0); pam.pam_strerror.restype=ctypes.c_char_p
    s=pam.pam_strerror(h,rc).decode(); pam.pam_end(h,rc); return rc,s
for u,p in [("root","qualsiasi"),("nictest","nictest")]:
    rc,s=prova(u,p); print(u, rc, s)
