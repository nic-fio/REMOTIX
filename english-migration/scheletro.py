import re,subprocess,sys
def sk_c(t, js=False):
    out=[];i=0;n=len(t)
    while i<n:
        c=t[i]
        if t.startswith('//',i):
            j=t.find('\n',i); i=n if j<0 else j; continue
        if t.startswith('/*',i):
            j=t.find('*/',i+2); i=n if j<0 else j+2; out.append(' '); continue
        if c in '"\'' or (js and c=='`'):
            q=c;j=i+1
            while j<n and t[j]!=q:
                if t[j]=='\\': j+=1
                elif q!='`' and t[j]=='\n': break
                j+=1
            out.append(q+q); i=j+1; continue
        out.append(c); i+=1
    s=''.join(out)
    s=re.sub(r'""(\s*"")+','""',s)   # stringhe spezzate
    return re.findall(r'\w+|[^\w\s]',s)
def sk_sh(t):
    lines=[]
    for l in t.split('\n'):
        l=re.sub(r'"(\\.|[^"\\])*"','""',l); l=re.sub(r"'[^']*'","''",l)
        l=re.sub(r'(^|\s)#.*','',l)
        lines.append(l)
    return re.findall(r'\w+|[^\w\s]','\n'.join(lines))
files=subprocess.check_output(['git','diff','--name-only','HEAD']).decode().split()
bad=0
for f in files:
    try: new=open(f).read()
    except: continue
    old=subprocess.run(['git','show','HEAD:'+f],capture_output=True,text=True).stdout
    if f.endswith(('.c','.h','.go','.mjs','.comp')): a,b=sk_c(old,f.endswith('.mjs')),sk_c(new,f.endswith('.mjs'))
    elif f.endswith('.html'):
        a,b=sk_c(old,True),sk_c(new,True)
    elif f.endswith(('.sh','.py')) or '/' in f and '.' not in f.rsplit('/',1)[1]: a,b=sk_sh(old),sk_sh(new)
    else: continue
    if a!=b:
        bad+=1
        import difflib
        d=[x for x in difflib.ndiff(a,b) if x[0] in '+-']
        print(f"DIVERSO {f}: {len(d)} gettoni, es. {d[:12]}")
print("file con codice diverso:",bad,"su",len(files))
