import fs from 'node:fs';
let p='work/build-original-text-training-v5.mjs',s=fs.readFileSync(p,'utf8');
s=s.replaceAll('原图文字训练室V5_头像框','原图文字训练室V5_头像框修订').replace('or(i==1 and -588 or 608),selecting and 160 or 325','or(i==1 and -608 or 608),selecting and 160 or 285').replace("local inset=menuMode=='battle'and string.match(parent.name,'^Portrait%d$')and 4 or 0",'local inset=0').replace('位置比原版右移10、上移40；框内头像右上偏移4','位置对应血条两端，左侧比原版左移10、右侧右移10；头像居中');fs.writeFileSync(p,s);
p='work/start-v4-visual-simulator.mjs';s=fs.readFileSync(p,'utf8').replace("local inset=menuMode=='battle'and string.match(parent.name,'^Portrait%d$')and 4 or 0",'local inset=0');fs.writeFileSync(p,s);
