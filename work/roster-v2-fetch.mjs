import{mkdirSync,writeFileSync,existsSync,readFileSync}from'node:fs';
const dir='assets/roster-v2';mkdirSync(dir,{recursive:true});
export const roster=[['keqing','刻晴'],['diluc','迪卢克'],['kaeya','凯亚'],['jean','琴'],['klee','可莉'],['lisa','丽莎'],['ganyu','甘雨'],['yanfei','烟绯'],['xiao','魈'],['hutao','胡桃'],['lawachurl','岩盔丘丘王'],['yaemiko','八重神子'],['kirara','绮良良'],['kamisatoayaka','神里绫华'],['kamisatoayato','神里绫人'],['aratakiitto','荒泷一斗'],['sangonomiyakokomi','珊瑚宫心海'],['tighnari','提纳里'],['cyno','赛诺'],['wanderer','散兵'],['nilou','妮露'],['faruzan','珐露珊'],['layla','莱依拉'],['neuvillette','那维莱特'],['wriothesley','莱欧斯利'],['clorinde','克洛琳德'],['navia','娜维娅'],['mualani','玛拉妮'],['kinich','基尼奇'],['kachina','卡齐娜'],['ineffa','伊涅芙'],['skirk','丝柯克'],['flins','菲林斯'],['varka','法尔加'],['nicole','尼可'],['venti','温迪'],['zhongli','钟离'],['furina','芙宁娜'],['nahida','纳西妲'],['mavuika','玛薇卡'],['raidenshogun','雷电将军'],['columbina','少女'],['tartaglia','达达利亚'],['sandrone','桑多涅'],['arlecchino','仆人'],['ronova','若娜瓦']];
async function fetchRetry(url,json=false){for(let i=0;i<5;i++)try{const r=await fetch(url,{signal:AbortSignal.timeout(18000)});if(!r.ok)throw Error(r.status+' '+url);return json?await r.json():Buffer.from(await r.arrayBuffer());}catch(e){if(i===4)throw e;}}
const cache=dir+'/character-images.json';const images=existsSync(cache)?JSON.parse(readFileSync(cache)):await fetchRetry('https://raw.githubusercontent.com/theBowja/genshin-db/main/src/data/image/characters.json',true);writeFileSync(cache,JSON.stringify(images));
console.log('DATASET_KEYS',Object.keys(images).slice(-25));
const records=[];
for(let offset=0;offset<roster.length;offset+=5)await Promise.all(roster.slice(offset,offset+5).map(async([key,name])=>{
 const item=images[key];let rec={key,name,source:'genshin-db extracted asset index',indexURL:'https://github.com/theBowja/genshin-db',images:[],errors:[]};
 if(item){for(const field of ['hoyolab-avatar','portrait']){let url=item[field];if(!url)continue;const path=dir+'/'+key+'-'+(field==='portrait'?'body':'head')+'.png';try{if(!existsSync(path))writeFileSync(path,await fetchRetry(url));rec.images.push({field,url,path});}catch(e){rec.errors.push(String(e));}}}
 else rec.errors.push('No indexed official artwork. Requires separate reference / concept art.');
 records.push(rec);console.log(key,rec.images.length,rec.errors.length);
}));
writeFileSync(dir+'/source-records.json',JSON.stringify(records,null,2));writeFileSync(dir+'/roster.json',JSON.stringify(roster,null,2));
