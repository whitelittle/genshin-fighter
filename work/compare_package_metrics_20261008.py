from pathlib import Path
import re, json, hashlib, statistics
BASE=Path(__file__).resolve().parent/'package-review-20261008'
paths={
 'early_online': BASE/'GF_Online_BackgroundPool_20261007/modules/genshin_fighter_online_1073742224',
 'r31': BASE/'dual-character-r31/modules/genshin_fighter_dual_pool',
 'r33': BASE/'GF_FORMAL_r33/modules/genshin_fighter',
}
report={'identity':{}, 'art':{}}
for mod in ['gf_net','gf_online','gf_fview','gf_gfx','gf_sim','gf_transport']:
    report['identity'][mod]={k:hashlib.sha256((p/(mod+'.lua')).read_bytes()).hexdigest() for k,p in paths.items()}
for name in ['gf_animation_data','gf_inbetween_data','gf_animation_effects','gf_aranara_data','gf_viewfinder_data']:
    s=(paths['r33']/(name+'.lua')).read_text(encoding='utf-8')
    values=[int(n) for n in re.findall(r'\["n"\]\s*=\s*(\d+)',s)]
    report['art'][name]={'entries':len(values),'min':min(values) if values else None,'max':max(values) if values else None,'mean':round(statistics.mean(values),1) if values else None,'over1600':sum(n>1600 for n in values)}
for char in ['raidenshogun','nahida']:
    s=(paths['early_online']/('gf_art_'+char+'.lua')).read_text(encoding='utf-8')
    for tier, section in [('lo',s.split('lo={',1)[1].split('sil={',1)[0]), ('sil',s.split('sil={',1)[1].split('face={',1)[0])]:
        values=[int(n) for n in re.findall(r'\bn=(\d+)',section)]
        report['art'][char+'_'+tier]={'entries':len(values),'min':min(values),'max':max(values),'mean':round(statistics.mean(values),1)}
(BASE/'comparison-metrics.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
