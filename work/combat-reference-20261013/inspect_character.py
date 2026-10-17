import pathlib,json,struct,zlib,lzma,re
from read_abc import Reader

root=pathlib.Path(__file__).resolve().parent
def expr(s):return {'expr':s}
def fmt(v):return v['expr'] if isinstance(v,dict) and set(v)=={'expr'} else json.dumps(v,ensure_ascii=False)

def summarize(body):
    stack=[];locals={0:expr('this')};calls=[];sets=[];branches=[];unsupported=[]
    def pop():return stack.pop() if stack else expr('<unknown>')
    for i in body['instructions']:
        op,args=i['op'],i['args']
        if op.startswith('push') and op not in('pushscope','pushwith'):
            v={'pushnull':None,'pushundefined':expr('undefined'),'pushtrue':True,'pushfalse':False,'pushnan':expr('NaN')}.get(op,args[0] if args else expr(op));stack.append(v)
        elif op in('pushscope','pushwith','pop'):pop()
        elif op in('popscope','nop','label','returnvoid','debugline','debugfile','debug'):pass
        elif op.startswith('getlocal'):
            n=int(op[-1]) if op.startswith('getlocal_') else args[0];stack.append(locals.get(n,expr('local'+str(n))))
        elif op.startswith('setlocal'):
            n=int(op[-1]) if op.startswith('setlocal_') else args[0];locals[n]=pop()
        elif op in('getlex','findpropstrict','findproperty'):stack.append(expr(args[0]))
        elif op=='getproperty':stack.append(expr(fmt(pop())+'.'+args[0]))
        elif op in('setproperty','initproperty'):
            v=pop();obj=pop();sets.append({'offset':i['offset'],'target':fmt(obj)+'.'+args[0],'value':v})
        elif op=='dup':stack.append(stack[-1] if stack else expr('<unknown>'))
        elif op=='swap':a=pop();b=pop();stack.extend([a,b])
        elif op=='newobject':
            pairs=[]
            for _ in range(args[0]):v=pop();k=pop();pairs.append((fmt(k) if not isinstance(k,str) else k,v))
            stack.append(dict(reversed(pairs)))
        elif op=='newarray':stack.append(list(reversed([pop() for _ in range(args[0])])))
        elif op in('callproperty','callpropvoid','callproplex','callsuper','callsupervoid','constructprop'):
            params=list(reversed([pop() for _ in range(args[1])]));obj=pop();target=fmt(obj)+'.'+args[0]
            calls.append({'offset':i['offset'],'call':target,'args':params,'conditional_method':bool(branches)})
            if op not in('callpropvoid','callsupervoid'):stack.append(expr(target+'('+','.join(map(fmt,params))+')'))
        elif op=='constructsuper':
            for _ in range(args[0]+1):pop()
        elif op=='construct':
            params=list(reversed([pop() for _ in range(args[0])]));stack.append(expr('new '+fmt(pop())+'('+','.join(map(fmt,params))+')'))
        elif op=='newfunction':stack.append(expr('method_'+str(args[0])))
        elif op in('coerce','coerce_a','coerce_s','convert_s','convert_i','convert_u','convert_d','convert_b','convert_o'):pass
        elif op in('add','subtract','multiply','divide','equals','strictequals','lessthan','lessequals','greaterthan','greaterequals','bitand','bitor'):
            b=pop();a=pop();stack.append(expr('('+fmt(a)+' '+op+' '+fmt(b)+')'))
        elif op in('not','negate'):stack.append(expr(op+'('+fmt(pop())+')'))
        elif op in('increment','decrement'):stack.append(expr(op+'('+fmt(pop())+')'))
        elif op=='kill':locals.pop(args[0],None)
        elif op.startswith('if'):
            cond=[pop()]
            if op not in('iftrue','iffalse'):cond.insert(0,pop())
            branches.append({'offset':i['offset'],'op':op,'args':args,'conditions':cond})
        elif op=='jump':branches.append({'offset':i['offset'],'op':op,'args':args})
        elif op=='returnvalue':pop()
        else:unsupported.append(i)
    return {'method':body['method'],'name':body['name'],'calls':calls,'assignments':sets,'branches':branches,'unsupported':unsupported}

class Bits:
    def __init__(self,b,start):self.b=b;self.p=start*8
    def read(self,n,signed=False):
        v=0
        for _ in range(n):v=v*2+((self.b[self.p//8]>>(7-self.p%8))&1);self.p+=1
        return v-(1<<n) if signed and n and v&(1<<(n-1)) else v
    def end(self):return (self.p+7)//8
def matrix(b,off):
    r=Bits(b,off);sx=sy=1.;ra=rb=0.
    if r.read(1):n=r.read(5);sx=r.read(n,True)/65536;sy=r.read(n,True)/65536
    if r.read(1):n=r.read(5);ra=r.read(n,True)/65536;rb=r.read(n,True)/65536
    n=r.read(5);x=r.read(n,True)/20;y=r.read(n,True)/20
    return {'x':x,'y':y,'scaleX':sx,'scaleY':sy,'rotate0':ra,'rotate1':rb},r.end()
def cxform(b,off):
    r=Bits(b,off);add=r.read(1);mul=r.read(1);n=r.read(4)
    for _ in range(4*add+4*mul):r.read(n,True)
    return r.end()
def cstr(b,off):end=b.index(b'\0',off);return b[off:end].decode('utf-8',errors='replace'),end+1

def timelines(packed):
    if packed[:3]==b'CWS':data=zlib.decompress(packed[8:])
    elif packed[:3]==b'ZWS':
        prop=packed[12];f={'id':lzma.FILTER_LZMA1,'dict_size':struct.unpack('<I',packed[13:17])[0],'lc':prop%9,'lp':(prop//9)%5,'pb':prop//45}
        data=lzma.LZMADecompressor(format=lzma.FORMAT_RAW,filters=[f]).decompress(packed[17:])
    else:data=packed[8:]
    sprites={};symbols={};notes=[]
    def parse(b,off,sid,frames):
        labels=[];events=[];markers=[];depths={};frame=1
        while off<len(b):
            h=struct.unpack_from('<H',b,off)[0];off+=2;tag=h>>6;length=h&63
            if length==63:length=struct.unpack_from('<I',b,off)[0];off+=4
            v=b[off:off+length];off+=length
            if tag==0:break
            if tag==1:
                objs=[dict(d,depth=k) for k,d in depths.items() if d.get('name') and ('atm' in d['name'] or d['name'] in('body','b','a'))]
                if objs:markers.append({'frame':frame,'objects':objs})
                frame+=1
            elif tag==43:labels.append({'frame':frame,'label':cstr(v,0)[0]})
            elif tag==39:
                child,count=struct.unpack_from('<HH',v,0);parse(v,4,child,count)
            elif tag==76:
                count=struct.unpack_from('<H',v,0)[0];q=2
                for _ in range(count):char=struct.unpack_from('<H',v,q)[0];name,q=cstr(v,q+2);symbols[char]=name
            elif tag in(26,70):
                flags=v[0];flags2=v[1] if tag==70 else 0;head=2 if tag==70 else 1
                depth=struct.unpack_from('<H',v,head)[0];q=head+2;obj=dict(depths.get(depth,{})) if flags&1 else {}
                if flags2&8 or (flags2&16 and flags&2):obj['class_name'],q=cstr(v,q)
                if flags&2:obj['character']=struct.unpack_from('<H',v,q)[0];q+=2
                if flags&4:obj['matrix'],q=matrix(v,q)
                if flags&8:q=cxform(v,q)
                if flags&16:q+=2
                if flags&32:obj['name'],q=cstr(v,q)
                depths[depth]=obj
                if flags&32:events.append({'frame':frame,'event':'place','depth':depth,**obj})
            elif tag==28:
                depth=struct.unpack_from('<H',v,0)[0];obj=depths.pop(depth,{})
                if obj.get('name'):events.append({'frame':frame,'event':'remove','depth':depth,**obj})
        sprites[sid]={'id':sid,'frames':frames,'labels':labels,'named_events':events,'markers':markers}
    nbits=data[0]>>3;off=(5+4*nbits+7)//8;frames=struct.unpack_from('<H',data,off+2)[0]
    parse(data,off+4,0,frames)
    for sid,info in sprites.items():info['class']=symbols.get(sid)
    return {'sprites':list(sprites.values()),'symbols':symbols,'unparsed_placeobject3':notes}

for key in ('juggo','yoruichi'):
    abc=json.loads((root/f'{key}.abc.json').read_text(encoding='utf-8'))
    methods=[summarize(b) for a in abc['abc'] for b in a['bodies'] if '::frame' in b['name'] or b['name'].endswith('::$init')]
    tl=timelines((root/f'{key}.swf').read_bytes())
    result={'id':key,'swf_sha256':abc['swf_sha256'],'framerate':abc['framerate'],'method_summaries':methods,**tl}
    (root/f'{key}.inspection.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'id':key,'frame_methods':sum('::frame' in m['name'] for m in methods),'unsupported_in_frame_methods':sum(len(m['unsupported']) for m in methods if '::frame' in m['name']),'placeobject3':len(tl['unparsed_placeobject3']),'timelines_with_labels':[(s['class'],len(s['labels'])) for s in tl['sprites'] if s['labels']]},ensure_ascii=False))
