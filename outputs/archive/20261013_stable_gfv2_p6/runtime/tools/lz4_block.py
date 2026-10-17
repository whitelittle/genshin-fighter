"""Small offline greedy LZ4 block encoder, matching the published block format."""
def compress(raw):
    out=bytearray();seen={};i=anchor=0;n=len(raw)
    def length(extra):
        while extra>=255:out.append(255);extra-=255
        out.append(extra)
    def sequence(start,end,offset,match):
        lit=end-start;ml=max(0,match-4)
        out.append((min(lit,15)<<4)|min(ml,15))
        if lit>=15:length(lit-15)
        out.extend(raw[start:end])
        if offset:
            out.extend((offset&255,offset>>8))
            if ml>=15:length(ml-15)
    while i<=n-12:
        key=raw[i:i+4];prev=seen.get(key);seen[key]=i
        if prev is None or i-prev>65535:i+=1;continue
        match=4
        while i+match<n-5 and raw[prev+match]==raw[i+match]:match+=1
        sequence(anchor,i,i-prev,match)
        end=i+match
        for j in range(i+1,end):seen[raw[j:j+4]]=j
        i=anchor=end
    sequence(anchor,n,0,0)
    return bytes(out)

def decompress(data):
    out=bytearray();i=0
    def length(value):
        nonlocal i
        if value==15:
            while True:
                b=data[i];i+=1;value+=b
                if b!=255:break
        return value
    while i<len(data):
        token=data[i];i+=1;lit=length(token>>4)
        out.extend(data[i:i+lit]);i+=lit
        if i==len(data):break
        offset=data[i]+256*data[i+1];i+=2
        assert 0<offset<=len(out)
        match=length(token&15)+4
        for _ in range(match):out.append(out[-offset])
    return bytes(out)
