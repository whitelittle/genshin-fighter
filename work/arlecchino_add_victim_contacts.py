from pathlib import Path
p=Path('work/arlecchino_pairing_profiles.py');s=p.read_text(encoding='utf-8');needle="(p/'pairing-profiles.json').write_text"
if "profiles['victim']" not in s:
 at=s.index(needle);s=s[:at]+"profiles['victim']={}\nfor model,bases in [('raiden',[[45,12],[36,15]]),('nahida',[[44,21],[44,22]])]:\n pr={}\n for i,h in enumerate([(490,150),(885,210)]):\n  key='throw_'+str(i);v=match(d['victim']['sourceFrames'][i],h,models[model][key],bases[i]);v['targetKey']=key;v['kind']='victim forearm';pr[str(i)]=v\n profiles['victim'][model]=pr\n"+s[at:]
p.write_text(s,encoding='utf-8')
