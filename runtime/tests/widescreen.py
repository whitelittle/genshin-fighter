"""Page-by-page wide screen and inset UI canvas reproduction, never native proof."""
from pathlib import Path
import json,sys,argparse,hashlib
from PIL import Image,ImageDraw
sys.path.insert(0,str(Path(__file__).resolve().parent))
from mock_flow import RuntimeClient,wait,ROOT
from performance import BenchClient

class WideClient(BenchClient):
    def __init__(self,source,safe):
        self.safe=safe
        super().__init__(source)
        self.H.W,self.H.H=2832,1280
        # Native GIA has GF_ROOT under the full-screen server container. The
        # ordinary mock has no parent and ignores its transform; model it here.
        self.rt.execute("""local H,safe,root=...;local canvas=H.newControl('container','canvas',nil,nil)
root.parent=canvas;root:SetAnchorMin(0,0);root:SetAnchorMax(1,1);root:SetSizeDelta(0,0)
H.game.GetUICanvasSize=function()return safe,1280 end""",self.H,safe,self.root)

def pages(source,safe,label):
    c=WideClient(source,safe);shots=[];counts=[]
    out=ROOT/'verification/widescreen'/label;out.mkdir(parents=True,exist_ok=True)
    def shot(name):
        path=out/(name+'.png');c.render(path)
        app=c.lua('GF_APP()');a,b,cc,d,e,f,w,h=c.H.frame(app.canvasBacking.c)
        bounds=[e-w*a/2,f-h*d/2,e+w*a/2,f+h*d/2]
        counts.append({'page':name,'backingBounds':list(bounds),'coversPhysicalScreen':bounds[0]<=0 and bounds[1]<=0 and bounds[2]>=2832 and bounds[3]>=1280,'pool':c.lua('GF_SECOND_POOL_STATUS().total')})
        shots.append(path)
    def go(name,args='{}',settle=.8):
        c.lua(f"(function()GF_APP():go('{name}',{args});return true end)()")
        wait(c,f"GF_APP().sceneName=='{name}' and not GF_APP().poolNext")
        c.run(settle)
    wait(c,'GF_APP() and GF_APP().poolNext and GF_SECOND_POOL_STATUS().total>400')
    shot('01-loading')
    wait(c,"GF_APP().sceneName=='intro' and not GF_APP().poolNext");c.run(.2);shot('02-intro')
    wait(c,"GF_APP().sceneName=='title' and not GF_APP().trans and not GF_APP().poolNext and GF_APP().scene.logoT and GF_APP().scene.logoT>1")
    shot('03-title')
    for name in ['menu','options','howto']:
        go(name);shot('04-'+name)
    for page in [2,3]:
        c.lua(f"(function()GF_APP().scene.page={page};return true end)()");c.run(.2);shot(f'05-howto-{page}')
    go('select');wait(c,'GF_APP().scene.built==4');shot('06-select')
    c.lua("(function()local s=GF_APP().scene;s.cur={3,4};s:confirm(1);s:confirm(2);return true end)()")
    c.run(.3);shot('07-select-transition-loading')
    args="{chars={'furina','kamisatoayaka'},mode='training',cpu={false,false},infinite=true,rounds=2,time=99}"
    go('vs',args,.6);shot('08-vs')
    wait(c,"GF_APP().sceneName=='fight' and GF_APP().scene.state=='load' and not GF_APP().poolNext");shot('09-fight-loading')
    wait(c,"GF_APP().scene.state=='run' and not GF_APP().trans");c.run(2);shot('10-fight')
    if label.startswith('before'):
        return {'label':label,'physicalScreen':[2832,1280],'uiCanvas':[safe,1280],'pages':counts,'note':'baseline comparison stops before known 96-text training pause exhaustion'}
    c.lua("(function()GF_APP().scene:openPause();return true end)()");c.run(.4);shot('11-pause')
    c.lua("(function()GF_APP().scene.showMoves=true;return true end)()");c.run(.2);shot('11-command-list')
    c.lua("(function()GF_APP().scene:closePause();return true end)()");c.run(.2)
    for seat,key in [(1,'furina'),(2,'kamisatoayaka')]:
        c.lua(f"""(function()local s=GF_APP().scene;s.banners={{}};s.sim.phase='fight';s.sim.freeze=1000
for i,p in ipairs(s.sim.f)do p.state='idle';p.x=i==1 and -20000 or 18000;p.y=0;p.hitstop=0;p.t=0;p.frozen=0;p.coat=0;p.cinematicConfirmed=false end
local p=s.sim.f[{seat}];p.state='burst';p.t=24;p.cinematicConfirmed=true;p.move=p.kit.burst;return true end)()""")
        c.run(.2);shot('12-Q-'+key)
    c.lua("(function()local s=GF_APP().scene;s.winner=1;s:finish();return true end)()")
    wait(c,"GF_APP().sceneName=='result' and not GF_APP().trans and not GF_APP().poolNext");c.run(1);shot('13-result')
    for name in ['online','gallery']:
        go(name);shot('14-'+name)
    # Resize already built title/selection controls without recreating the page.
    go('title');c.run(2);c.H.W,c.H.H=3200,1440;c.rt.execute('local H=...;H.game.GetUICanvasSize=function()return 3200,1440 end',c.H)
    c.lua('(function()GF_APP():fit(false);return true end)()');c.run(.2)
    if not label.startswith('before'):assert c.lua('GF_APP().scene.area.node.w==GF_APP().W')
    go('select');wait(c,'GF_APP().scene.built==4');c.H.W,c.H.H=2560,1440
    c.rt.execute('local H=...;H.game.GetUICanvasSize=function()return 2560,1440 end',c.H)
    c.lua('(function()GF_APP():fit(false);return true end)()');c.run(.6)
    assert c.lua("(function()local s=GF_APP().scene;for i,b in pairs(s.cardAreas)do local x,y=s:cardPos(i);assert(b.node.x==x and b.node.y==y)end;return true end)()")
    assert all(r['coversPhysicalScreen'] for r in counts) or label.startswith('before'),counts
    if not label.startswith('before'):
        # Black loading cover must itself cover the screen, not just the backing.
        im=Image.open(shots[0]).convert('RGB');assert im.getpixel((0,640))==(0,0,0) and im.getpixel((2831,640))==(0,0,0)
    montage=Image.new('RGB',(1200,((len(shots)+2)//3)*230),(17,19,31));draw=ImageDraw.Draw(montage)
    for i,p in enumerate(shots):
        im=Image.open(p);im.thumbnail((400,205));x=(i%3)*400;y=(i//3)*230;montage.paste(im,(x,y));draw.text((x+4,y+205),p.stem,fill='white')
    montage.save(out/'all-pages.png')
    print(json.dumps({'label':label,'screens':len(shots),'allBackingCovers':all(r['coversPhysicalScreen'] for r in counts)}),flush=True)
    return {'label':label,'physicalScreen':[2832,1280],'uiCanvas':[safe,1280],'pages':counts,'contactSheet':(out/'all-pages.png').relative_to(ROOT).as_posix()}
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--before',action='store_true');a=ap.parse_args()
    source=ROOT.parent/'outputs/four-character-pool-fix-20261012_012454/gpt_20261012_012454_原神格斗_16000三段加载性能版.lua' if a.before else ROOT/'dist/genshin_fighter.lua'
    results=[pages(source,safe,('before' if a.before else 'after')+label) for safe,label in [(2832,'-full'),(2648,'-safe-inset')]]
    (ROOT/'verification'/('widescreen-before.json' if a.before else 'widescreen-after.json')).write_text(json.dumps({'mockOnly':True,'safeInsetIsReproductionHypothesis':True,'sourceSha256':hashlib.sha256(source.read_bytes()).hexdigest(),'results':results},indent=2),encoding='utf-8')
