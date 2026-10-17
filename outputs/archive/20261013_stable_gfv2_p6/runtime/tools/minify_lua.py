"""Whitespace/comments only. Preserve every Lua token, literal and identifier."""
from pathlib import Path
import argparse,hashlib,json,re
IDENT=re.compile(r'[A-Za-z_][A-Za-z_0-9]*')
NUMBER=re.compile(r'(?:0[xX](?:[0-9a-fA-F]+(?:\.[0-9a-fA-F]*)?|\.[0-9a-fA-F]+)(?:[pP][+-]?\d+)?|(?:\d+\.\d*|\.\d+|\d+)(?:[eE][+-]?\d+)?)')
LONG=re.compile(r'\[(=*)\[')
SYMBOLS=('...','//','<<','>>','==','~=','<=','>=','..','::')

def tokens(source):
    i=0;n=len(source)
    def long_end(start,m):
        close=']'+m.group(1)+']';end=source.find(close,m.end())
        assert end>=0,('unterminated long literal',start)
        return end+len(close)
    while i<n:
        c=source[i]
        if c.isspace():i+=1;continue
        if source.startswith('--',i):
            m=LONG.match(source,i+2)
            if m:i=long_end(i,m)
            else:
                end=source.find('\n',i);i=n if end<0 else end+1
            continue
        start=i
        if c in ('"',"'"):
            i+=1
            while i<n:
                if source[i]=='\\':i+=2
                elif source[i]==c:i+=1;break
                else:i+=1
            else:raise AssertionError('unterminated quoted literal')
        else:
            m=LONG.match(source,i)
            if m:i=long_end(i,m)
            elif (m:=IDENT.match(source,i)):i=m.end()
            elif (m:=NUMBER.match(source,i)):i=m.end()
            else:
                symbol=next((s for s in SYMBOLS if source.startswith(s,i)),c);i+=len(symbol)
        yield source[start:i]

def minify(source):
    out=[];previous=None;cache={}
    for token in tokens(source):
        if previous is not None:
            pair=(previous,token)
            needs=cache.get(pair)
            if needs is None:
                needs=(previous[-1].isalnum() or previous[-1]=='_') and (token[0].isalnum() or token[0]=='_')
                if not needs:
                    try:needs=list(tokens(previous+token))!=[previous,token]
                    except AssertionError:needs=True
                cache[pair]=needs
            if needs:out.append(' ')
        out.append(token);previous=token
    result=''.join(out)+'\n'
    # Full stream comparison also catches ambiguous boundaries over >2 tokens.
    assert list(tokens(source))==list(tokens(result)),'Lua token stream changed'
    return result

def export(source,out):
    original=Path(source).read_bytes();text=original.decode('utf-8');raw=minify(text).encode()
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    (out/'genshin_fighter.lua').write_bytes(raw)
    manifest={'profile':'comments-whitespace-only','minified':True,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'baseBytes':len(original),'baseSha256':hashlib.sha256(original).hexdigest(),'tokenStreamIdentical':True,'nativeDeviceTested':False}
    (out/'build.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    print(json.dumps(manifest));return manifest
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--source',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();export(a.source,a.out)
