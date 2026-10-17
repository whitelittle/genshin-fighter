import assert from'node:assert/strict';
export function compress(raw){
 const out=[],dict=new Map();let p=0,literals=[],tokens=0;
 const flush=()=>{if(literals.length){out.push(literals.length-1,...literals);literals=[];tokens++;}};
 const remember=i=>{if(i+2>=raw.length)return;const k=raw[i]*65536+raw[i+1]*256+raw[i+2];const list=dict.get(k)||[];list.push(i);while(list.length>12||i-list[0]>65535)list.shift();dict.set(k,list);};
 while(p<raw.length){let best=0,offset=0;if(p+2<raw.length){const k=raw[p]*65536+raw[p+1]*256+raw[p+2];for(const pos of dict.get(k)||[]){const dist=p-pos;if(dist>65535)continue;let n=0;while(n<130&&p+n<raw.length&&raw[pos+n]===raw[p+n])n++;if(n>best){best=n;offset=dist;}}}
  if(best>=4){flush();out.push(128+best-3,Math.floor(offset/256),offset%256);tokens++;for(let n=0;n<best;n++)remember(p+n);p+=best;}
  else{literals.push(raw[p]);remember(p++);if(literals.length===128)flush();}
 }flush();return{bytes:Buffer.from(out),tokens};
}
export function decompress(z){const out=[];for(let p=0;p<z.length;){let token=z[p++];if(token<128){const len=token+1;for(let n=0;n<len;n++)out.push(z[p++]);}else{const len=token-128+3,dist=z[p++]*256+z[p++];for(let n=0;n<len;n++)out.push(out[out.length-dist]);}}return Buffer.from(out);}
export function expandCompact(bytes){const raw=[];let x=0,y=0;for(let at=0;at<bytes.length;){const header=bytes[at++],flag=Math.floor(header/64),index=header%64+1;let w,h;if(flag===0){const coord=bytes[at++],dx=Math.floor(coord/16),dy=coord%16;const unzig=n=>n%2===0?n/2:-(n+1)/2;x+=unzig(dx);y+=unzig(dy);const size=bytes[at++];w=Math.floor(size/16)+1;h=size%16+1;}else if(flag===1){x=bytes[at++];y=bytes[at++];const size=bytes[at++];w=Math.floor(size/16)+1;h=size%16+1;}else{x=bytes[at++];y=bytes[at++];w=bytes[at++];h=bytes[at++];}raw.push(x,y,w,h,index);}return Buffer.from(raw);}
export function packFrame(f){const palette=[],index=new Map(),raw=[],compact=[];let oldX=0,oldY=0;const zig=n=>n>=0?n*2:-n*2-1;
 for(const r of f.rows){let[x,y,w,h,red,g,b,a]=r;let color=r.length===5?r[4]:((a<<24)|(red<<16)|(g<<8)|b)>>>0;if(!index.has(color)){palette.push(color);index.set(color,palette.length);}const pal=index.get(color);assert.ok(pal<=64,'palette header requires <=64 colors');for(const n of[x,y,w,h,pal]){assert.ok(n>=0&&n<=255&&Number.isInteger(n),'coordinate / palette overflow');raw.push(n);}
  const dx=zig(x-oldX),dy=zig(y-oldY);if(w<=16&&h<=16){if(dx<16&&dy<16)compact.push(pal-1,dx*16+dy,(w-1)*16+h-1);else compact.push(64+pal-1,x,y,(w-1)*16+h-1);}else compact.push(128+pal-1,x,y,w,h);oldX=x;oldY=y;
 }
 const bytes=Buffer.from(raw),stream=Buffer.from(compact),z=compress(stream);assert.deepEqual(expandCompact(decompress(z.bytes)),bytes);return{scale:f.scale,anchor:f.anchor,palette,data:z.bytes.toString('base64'),count:f.rows.length,tokens:z.tokens,rawBytes:bytes.length,compactBytes:stream.length,compressedBytes:z.bytes.length};}
export function luaFrame(f){return`{scale=${f.scale},anchor={${f.anchor}},palette={${f.palette}},data='${f.data}',count=${f.count},tokens=${f.tokens}}`;}
