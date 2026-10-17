"""Fit each pose from an empty transparent canvas; then match native shapes."""
import sys,json,math,time,io
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont
sys.path.insert(0,str(Path('work/vector-research-deps').resolve()))
import resvg_py
from scipy.optimize import linear_sum_assignment
OUT=Path('outputs/nahida-independent-actions-20261015');OUT.mkdir(parents=True,exist_ok=True)
OLD=Path('outputs/nahida-two-actions-20261015')
W,H=384,512; yy,xx=np.mgrid[:H,:W].astype(np.float32);xx+=.5;yy+=.5
N=994
def svg(es):
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">'+''.join(f'<ellipse cx="{e["x"]}" cy="{e["y"]}" rx="{e["width"]/2}" ry="{e["height"]/2}" transform="rotate({-e["rotation"]} {e["x"]} {e["y"]})" fill="{e["color"]}"/>' for e in es)+'</svg>'
def metric(png,ref):
    p=np.array(Image.open(io.BytesIO(png)).convert('RGBA').resize((W,H),Image.Resampling.LANCZOS)).astype(float)/255
    ra=np.array(ref)[:,:,3]>0;t=np.array(ref)[:,:,:3].astype(float)/255;t[~ra]=1
    c=p[:,:,:3]*p[:,:,3,None]+1-p[:,:,3,None];a=p[:,:,3]>=.5
    return {'foregroundRGBMAE':round(float(np.abs(c-t)[ra].mean()*255),3),'silhouetteIoU':round(float(np.count_nonzero(a&ra)/np.count_nonzero(a|ra)),5)}
allactions=[];reports=[];started=time.time()
for action in ['idle','move']:
    frames=[]
    for index in range(4):
        directory=OUT/action/str(index);directory.mkdir(parents=True,exist_ok=True)
        ref=Image.open(OLD/action/str(index)/'reference.png').convert('RGBA');ref.save(directory/'reference.png')
        raw=np.array(ref);ta=(raw[:,:,3]>0).astype(np.float32);target=raw[:,:,:3].astype(np.float32)/255;target[ta==0]=1
        current=np.ones((H,W,3),np.float32);alpha=np.zeros((H,W),np.float32)
        lum=target.mean(axis=2);dy,dx=np.gradient(lum);wt=1+np.clip(np.hypot(dx,dy)*6,0,1.5)
        rng=np.random.default_rng(20261015+index+(100 if action=='move' else 0))
        es=[]
        for iteration in range(N):
            error=wt*(np.sum((current-target)**2,axis=2)+6*(alpha-ta)**2)
            mass=(error*ta).ravel().astype(np.float64)+1e-10
            centers=rng.choice(W*H,4,p=mass/mass.sum())
            best=None;bestgain=-1e9
            for location in centers:
                cy,cx=divmod(int(location),W)
                for trial in range(24):
                    if iteration<100:width=float(rng.uniform(7,75));height=float(rng.uniform(15,115))
                    elif iteration<350:width=float(rng.uniform(3,30));height=float(rng.uniform(8,55))
                    else:width=float(rng.uniform(1.3,13));height=float(rng.uniform(4,26))
                    angle=float(rng.uniform(-90,90));r=math.radians(-angle);c,s=math.cos(r),math.sin(r)
                    radius=math.hypot(width,height)*.5+2
                    x0=max(0,int(cx-radius));x1=min(W,int(cx+radius+1));y0=max(0,int(cy-radius));y1=min(H,int(cy+radius+1));sl=np.s_[y0:y1,x0:x1]
                    u=(xx[sl]-cx)*c+(yy[sl]-cy)*s;v=-(xx[sl]-cx)*s+(yy[sl]-cy)*c
                    a=np.clip((1-np.sqrt((u/(width*.5))**2+(v/(height*.5))**2))*min(width,height)*.5+.5,0,1)
                    if np.sum(a*ta[sl])/max(float(np.sum(a)),1e-7)<.985:continue
                    ww=wt[sl];old=current[sl];den=float(np.sum(ww*a*a))
                    if den<1e-6:continue
                    col=np.clip(np.sum(ww[:,:,None]*a[:,:,None]*(target[sl]-old*(1-a[:,:,None])),axis=(0,1))/den,0,1)
                    new=old*(1-a[:,:,None])+a[:,:,None]*col;na=alpha[sl]+(1-alpha[sl])*a
                    loss=ww*(np.sum((new-target[sl])**2,axis=2)+6*(na-ta[sl])**2)
                    gain=float(np.sum(error[sl]-loss))
                    if gain>bestgain:bestgain=gain;best=(cx,cy,width,height,angle,col,sl,a,new,na)
            if best is None:
                cy,cx=divmod(int(centers[0]),W);width=height=1.5;angle=0;col=target[cy,cx]
                sl=np.s_[cy:cy+1,cx:cx+1];a=np.ones((1,1),np.float32);new=target[sl];na=np.ones((1,1),np.float32)
                best=(cx,cy,width,height,angle,col,sl,a,new,na)
            cx,cy,width,height,angle,col,sl,a,new,na=best
            current[sl]=new;alpha[sl]=na
            es.append({'type':'ellipse','name':f'independent-{iteration}','part':'independent-pose','x':cx,'y':cy,'width':round(width,4),'height':round(height,4),'rotation':round(angle,4),'color':'#'+''.join(f'{round(float(v)*255):02x}' for v in col),'fill':1})
        mark=svg(es);(directory/'fitted.svg').write_text(mark,encoding='utf-8');png=resvg_py.svg_to_bytes(svg_string=mark,zoom=2,skip_system_fonts=True);(directory/'fitted.png').write_bytes(png)
        result=metric(png,ref);reports.append({'action':action,'frame':index,'images':len(es),'fitStartedFromEmpty':True,**result})
        frames.append({'index':index,'durationMs':500,'elements':es,'svg':f'{action}/{index}/fitted.svg','reference':f'{action}/{index}/reference.png'})
        print('INDEPENDENT_FRAME '+json.dumps(reports[-1]),flush=True)
    # One-to-one correspondence uses type, position, size and color, not
    # arbitrary original indices. Reorder whole shape/color tuples together.
    for j in range(1,4):
        left,right=frames[j-1]['elements'],frames[j]['elements']
        def features(items):
            return np.array([[e['x']/W,e['y']/H,math.log(e['width'])/8,math.log(e['height'])/8,*[int(e['color'][k:k+2],16)/255 for k in (1,3,5)]] for e in items],np.float32)
        a,b=features(left),features(right);difference=a[:,None,:]-b[None,:,:]
        cost=np.sum(difference[:,:,:2]**2,axis=2)*4+np.sum(difference[:,:,2:4]**2,axis=2)+np.sum(difference[:,:,4:]**2,axis=2)*2
        _,assignment=linear_sum_assignment(cost)
        frames[j]['poolOrder']=assignment.tolist()
        # Keep fitted paint order unchanged; poolOrder defines correspondence.
        for i,e in enumerate(left):e.setdefault('poolId',i)
        for i,k in enumerate(assignment):right[int(k)]['poolId']=left[i]['poolId']
    for f in frames:
        for i,e in enumerate(f['elements']):e.setdefault('poolId',i)
        p=OUT/action/str(f['index']);(p/'collage.json').write_text(json.dumps({'w':W,'h':H,'elements':f['elements']},ensure_ascii=False,separators=(',',':')),encoding='utf-8')
    allactions.append({'key':action,'name':'基础姿势组' if action=='idle' else '移动姿势组','loop':True,'frames':frames})
(OUT/'animation.json').write_text(json.dumps({'w':W,'h':H,'imagePoolSize':N,'background':'transparent','actions':allactions,'matching':'one-to-one minimum-cost assignment','transition':'replace geometry and paint order; no alpha crossfade','deviceVerified':False},ensure_ascii=False,separators=(',',':')),encoding='utf-8')
(OUT/'fit-report.json').write_text(json.dumps({'frames':reports,'seconds':round(time.time()-started,2),'eachFrameIndependent':True,'imageBudget':1000,'imagesPerFrame':N,'artApproved':False,'deviceVerified':False},ensure_ascii=False,indent=2),encoding='utf-8')
font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',18)
for action in ['idle','move']:
    panel=Image.new('RGB',(1200,300),'#eef2f5');d=ImageDraw.Draw(panel)
    for i in range(4):
        d.text((i*300+8,8),f'{action} {i+1}  原图 / 独立拟合',font=font,fill='#354139')
        for name,x in [('reference.png',i*300+3),('fitted.png',i*300+153)]:
            p=Image.open(OUT/action/str(i)/name).convert('RGBA').resize((144,192),Image.Resampling.LANCZOS);panel.paste(p,(x,47),p)
    panel.save(OUT/(action+'-contact.png'))
print('INDEPENDENT_ACTIONS_COMPLETE',flush=True)
