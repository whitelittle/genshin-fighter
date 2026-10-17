"""Read-only SWF/ABC inspection. Emits bytecode; never executes SWF scripts."""
import hashlib, json, pathlib, struct, sys, zlib, lzma

class Reader:
    def __init__(self, data): self.data,self.pos=data,0
    def u8(self): v=self.data[self.pos];self.pos+=1;return v
    def u30(self):
        v=0
        for i in range(5):
            b=self.u8();v|=(b&127)<<(i*7)
            if b<128: return v
        return v
    def take(self,n): v=self.data[self.pos:self.pos+n];self.pos+=n;return v
    def s24(self):
        v=int.from_bytes(self.take(3),'little');return v-(1<<24) if v&(1<<23) else v

OPS={}
def op(code,name,args=''): OPS[code]=(name,args)
for c,n in {0x02:'nop',0x03:'throw',0x09:'label',0x1c:'pushwith',0x1d:'popscope',0x20:'pushnull',0x21:'pushundefined',0x23:'nextvalue',0x26:'pushtrue',0x27:'pushfalse',0x28:'pushnan',0x29:'pop',0x2a:'dup',0x2b:'swap',0x30:'pushscope',0x47:'returnvoid',0x48:'returnvalue',0x57:'newactivation',0x64:'getglobalscope',0x70:'convert_s',0x73:'convert_i',0x74:'convert_u',0x75:'convert_d',0x76:'convert_b',0x77:'convert_o',0x78:'checkfilter',0x82:'coerce_a',0x85:'coerce_s',0x87:'astypelate',0x90:'negate',0x91:'increment',0x93:'decrement',0x95:'typeof',0x96:'not',0x97:'bitnot',0xa0:'add',0xa1:'subtract',0xa2:'multiply',0xa3:'divide',0xa4:'modulo',0xa5:'lshift',0xa6:'rshift',0xa7:'urshift',0xa8:'bitand',0xa9:'bitor',0xaa:'bitxor',0xab:'equals',0xac:'strictequals',0xad:'lessthan',0xae:'lessequals',0xaf:'greaterthan',0xb0:'greaterequals',0xb1:'instanceof',0xb3:'istypelate',0xb4:'in',0xc0:'increment_i',0xc1:'decrement_i',0xc4:'negate_i',0xc5:'add_i',0xc6:'subtract_i',0xc7:'multiply_i'}.items():op(c,n)
for c,n in {0x04:'getsuper',0x05:'setsuper',0x45:'callsuper',0x46:'callproperty',0x4a:'constructprop',0x4c:'callproplex',0x4e:'callsupervoid',0x4f:'callpropvoid',0x59:'getdescendants',0x5d:'findpropstrict',0x5e:'findproperty',0x5f:'finddef',0x60:'getlex',0x61:'setproperty',0x66:'getproperty',0x68:'initproperty',0x6a:'deleteproperty',0x80:'coerce',0x86:'astype',0xb2:'istype'}.items():op(c,n,'mu' if c in(0x45,0x46,0x4a,0x4c,0x4e,0x4f) else 'm')
for c,n in {0x06:'dxns',0x08:'kill',0x25:'pushshort',0x2c:'pushstring',0x2d:'pushint',0x2e:'pushuint',0x2f:'pushdouble',0x31:'pushnamespace',0x40:'newfunction',0x41:'call',0x42:'construct',0x49:'constructsuper',0x53:'applytype',0x55:'newobject',0x56:'newarray',0x58:'newclass',0x5a:'newcatch',0x62:'getlocal',0x63:'setlocal',0x67:'getouterscope',0x6c:'getslot',0x6d:'setslot',0x6e:'getglobalslot',0x6f:'setglobalslot',0x92:'inclocal',0x94:'declocal',0xc2:'inclocal_i',0xc3:'declocal_i',0xf0:'debugline',0xf1:'debugfile'}.items():op(c,n,'u')
for c in range(0x0c,0x1b):op(c,{0x0c:'ifnlt',0x0d:'ifnle',0x0e:'ifngt',0x0f:'ifnge',0x10:'jump',0x11:'iftrue',0x12:'iffalse',0x13:'ifeq',0x14:'ifne',0x15:'iflt',0x16:'ifle',0x17:'ifgt',0x18:'ifge',0x19:'ifstricteq',0x1a:'ifstrictne'}[c],'j')
op(0x24,'pushbyte','b');op(0x65,'getscopeobject','b');op(0x32,'hasnext2','uu');op(0x43,'callmethod','uu');op(0x44,'callstatic','uu');op(0xef,'debug','bubu')
for c in range(0xd0,0xd4):op(c,f'getlocal_{c-0xd0}')
for c in range(0xd4,0xd8):op(c,f'setlocal_{c-0xd4}')

def parse_abc(data):
    r=Reader(data); version=struct.unpack('<HH',r.take(4))
    def pool(fn): return [None]+[fn() for _ in range(max(0,r.u30()-1))]
    ints=pool(r.u30);ints=[0]+[x-(1<<32) if x&(1<<31) else x for x in ints[1:]]
    uints=pool(r.u30); doubles=pool(lambda:struct.unpack('<d',r.take(8))[0]); strings=['']+[r.take(r.u30()).decode('utf-8',errors='replace') for _ in range(max(0,r.u30()-1))]
    namespaces=pool(lambda:(r.u8(),r.u30())); nssets=pool(lambda:[r.u30() for _ in range(r.u30())])
    multinames=[None]
    for _ in range(max(0,r.u30()-1)):
        kind=r.u8()
        if kind in(7,13): item=[r.u30(),r.u30()]
        elif kind in(15,16,27,28): item=[r.u30()]
        elif kind in(17,18): item=[]
        elif kind in(9,14): item=[r.u30(),r.u30()]
        elif kind==29: item=[r.u30(),[r.u30() for _ in range(r.u30())]]
        else: raise ValueError(('multiname',kind))
        multinames.append((kind,item))
    def mn(i):
        if i==0:return '*'
        kind,item=multinames[i]
        if kind in(7,13):
            ns=strings[namespaces[item[0]][1]];return (ns+'::' if ns else '')+strings[item[1]]
        if kind in(15,16,9,14):return strings[item[0]]
        return f'multiname_{i}'
    methods=[]
    for _ in range(r.u30()):
        count=r.u30();ret=r.u30();params=[r.u30() for _ in range(count)];name=r.u30();flags=r.u8()
        if flags&8:
            for _ in range(r.u30()):r.u30();r.u8()
        if flags&128:
            for _ in range(count):r.u30()
        methods.append({'name':strings[name],'return':mn(ret),'params':[mn(x) for x in params]})
    for _ in range(r.u30()):
        r.u30();count=r.u30()
        for _ in range(count*2):r.u30()
    def traits(owner):
        out=[]
        for _ in range(r.u30()):
            name=mn(r.u30());kindattr=r.u8();kind=kindattr&15
            if kind in(0,6):
                r.u30();r.u30();val=r.u30()
                if val:r.u8()
            elif kind in(1,2,3,5):
                r.u30();mid=r.u30();methods[mid]['name']=owner+'::'+name;out.append(mid)
            elif kind==4:r.u30();r.u30()
            else:raise ValueError(('trait',kind))
            if kindattr&64:
                for _ in range(r.u30()):r.u30()
        return out
    count=r.u30();classes=[]
    for _ in range(count):
        name=mn(r.u30());r.u30();flags=r.u8()
        if flags&8:r.u30()
        for _ in range(r.u30()):r.u30()
        mid=r.u30();methods[mid]['name']=name+'::$init';t=traits(name);classes.append({'name':name,'init':mid,'methods':t})
    for cls in classes:
        mid=r.u30();methods[mid]['name']=cls['name']+'::$cinit';traits(cls['name'])
    for _ in range(r.u30()):r.u30();traits('script')
    bodies=[]
    for _ in range(r.u30()):
        mid=r.u30();limits=[r.u30() for _ in range(4)];code=r.take(r.u30());cr=Reader(code);instructions=[]
        while cr.pos<len(code):
            at=cr.pos;opcode=cr.u8()
            if opcode==0x1b:
                args=[cr.s24()];n=cr.u30();args+=[cr.s24() for _ in range(n+1)];name='lookupswitch'
            else:
                if opcode not in OPS:raise ValueError(('unknown_opcode',hex(opcode),mid,at))
                name,fmt=OPS[opcode];args=[]
                for f in fmt:
                    if f=='j':v=cr.s24();args.append(cr.pos+v)
                    elif f=='b':args.append(cr.u8())
                    else:
                        v=cr.u30();args.append(mn(v) if f=='m' else v)
                if name in('pushstring','debugfile'):args[0]=strings[args[0]]
                elif name=='pushint':args[0]=ints[args[0]]
                elif name=='pushuint':args[0]=uints[args[0]]
                elif name=='pushdouble':args[0]=doubles[args[0]]
                elif name=='pushshort' and args[0]&0x8000:args[0]-=0x10000
                elif name=='pushbyte' and args[0]&128:args[0]-=256
            instructions.append({'offset':at,'op':name,'args':args})
        for _ in range(r.u30()):
            for _ in range(5):r.u30()
        traits('body')
        bodies.append({'method':mid,'name':methods[mid]['name'],'limits':limits,'instructions':instructions})
    assert r.pos==len(data),(r.pos,len(data))
    return {'version':version,'methods':methods,'classes':classes,'bodies':bodies}

def read_swf(path):
    packed=path.read_bytes();assert packed[:3] in(b'CWS',b'FWS',b'ZWS')
    if packed[:3]==b'ZWS':
        prop=packed[12]
        filt={'id':lzma.FILTER_LZMA1,'dict_size':struct.unpack('<I',packed[13:17])[0],
              'lc':prop%9,'lp':(prop//9)%5,'pb':prop//45}
        dec=lzma.LZMADecompressor(format=lzma.FORMAT_RAW,filters=[filt])
        data=dec.decompress(packed[17:])
    else:data=zlib.decompress(packed[8:]) if packed[:3]==b'CWS' else packed[8:]
    assert len(data)+8==struct.unpack('<I',packed[4:8])[0]
    nbits=data[0]>>3;off=(5+4*nbits+7)//8
    framerate,frames=struct.unpack_from('<HH',data,off);off+=4
    result={'swf_sha256':hashlib.sha256(packed).hexdigest(),'framerate':framerate/256,'frames':frames,'abc':[]}
    while off<len(data):
        h=struct.unpack_from('<H',data,off)[0];off+=2;tag=h>>6;length=h&63
        if length==63:length=struct.unpack_from('<I',data,off)[0];off+=4
        payload=data[off:off+length];off+=length
        if tag==82:
            start=payload.index(b'\0',4)+1;result['abc'].append(parse_abc(payload[start:]))
        if tag==0:break
    out=path.with_suffix('.abc.json');out.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    lines=[]
    for abc in result['abc']:
        for body in abc['bodies']:
            lines.append(f"\nMETHOD {body['method']} {body['name']}")
            for ins in body['instructions']:
                lines.append(f"{ins['offset']:04x}: {ins['op']} "+', '.join(str(x) for x in ins['args']))
    path.with_suffix('.pcode.txt').write_text('\n'.join(lines),encoding='utf-8')
    print(json.dumps({'file':path.name,'abc':len(result['abc']),'methods':sum(len(a['bodies']) for a in result['abc']),'framerate':result['framerate']},ensure_ascii=False))

for arg in sys.argv[1:]:read_swf(pathlib.Path(arg))
