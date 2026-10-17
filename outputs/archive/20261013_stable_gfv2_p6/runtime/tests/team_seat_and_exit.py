"""Real touch draft with no seat; late-seat preservation; quit/close signal flow."""
from pathlib import Path
import sys,argparse,json
sys.path.insert(0,str(Path(__file__).resolve().parent))
from mock_flow import RuntimeClient,wait
from team_select import card,button
ap=argparse.ArgumentParser();ap.add_argument('--source',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);ap.add_argument('--bindings',type=Path);a=ap.parse_args();RuntimeClient.source=a.source
bindings=json.loads(a.bindings.read_text(encoding='utf-8')) if a.bindings else {}
logical={actual:name for name,actual in bindings.items()}
nativeSent=[]
def native(name):return bindings.get(name,name)
def client(scene,args=None):
    c=RuntimeClient(device='Mobile',canvas=(1950,900));c.env.GF_FIRST_SCENE=scene
    if args:c.env.GF_FIRST_ARGS=c._to_lua(args)
    handlers={};sent=[];gate={'seat':False};settled=[0]
    c.script.RegisterServerSignalHandler=lambda _s,n,fn:handlers.__setitem__(n,fn)
    def signal(name):
        values=[]
        def send(_s):
            nativeSent.append(name)
            if bindings:assert name in logical,name
            meaning=logical.get(name,name)
            sent.append((meaning,values[:]))
            if meaning=='GF3Hello' and gate['seat']:handlers[native('GF3Seat')](None,c._to_lua([2,1]))
            if meaning=='GF3Quit':
                if settled[0]==0:settled[0]+=1
                handlers[native('GF3Close')](None,c._to_lua([]))
        return c._to_lua({'AddInt':lambda _s,v:values.append(int(v)),'SendSignal':send})
    c.H.game.ServerSignal=signal
    return c,handlers,sent,gate,settled
c,handlers,sent,gate,_=client('select',{'teamPreview':True,'teamOnline':True})
wait(c,"GF_APP() and GF_APP().sceneName=='select' and GF_APP().scene.initialized and GF_APP().scene.built==6 and not GF_APP().poolNext")
for idx in (5,6,3):card(c,idx,(1950,900));card(c,idx,(1950,900))
assert c.lua('#GF_APP().scene.teams[1]==3 and not GF_APP().scene.teamIO.slot')
button(c,'teamConfirm',(1950,900));assert c.lua('GF_APP().scene.ready[1] and GF_APP().scene.teamIO.ready')
c.render(a.out/'online-draft-without-seat.png')
gate['seat']=True;c.run(.7)
assert c.lua('GF_APP().scene.teamIO.slot==2 and #GF_APP().scene.teams[1]==3 and GF_APP().scene.teams[1][1]==5 and GF_APP().scene.ready[1]')
rev=c.lua('GF_APP().scene.teamIO.revision')
handlers[native('GF3Progress')](None,c._to_lua([1,1,3,1,0]));handlers[native('GF3Reveal')](None,c._to_lua([1,0,rev,1,2,4,5,6,3]))
wait(c,"GF_APP().sceneName=='gf_scene_team_vs' and not GF_APP().trans")
assert any(n=='GF3Team' and v[0]==2 and v[3:6]==[5,6,3] and v[-1]==1 for n,v in sent)
c,handlers,sent,gate,settled=client('menu')
wait(c,"GF_APP() and GF_APP().sceneName=='menu' and not GF_APP().poolNext")
c.lua("(function()GF_APP().scene:pick('quit');return true end)()");c.step()
assert c.lua('GF_APP().closed') and not c.update_enabled and settled[0]==1
assert any(n=='GF3Quit' for n,v in sent)
# Repeated close delivery is safe; never return to title as a fake settlement.
handlers[native('GF3Close')](None,c._to_lua([]));assert c.lua('GF_APP().closed')
assert c.lua("""(function()
 local names=GF_REQUIRE('gf_signal_names');local handlers={};local emitted={}
 local game={ServerSignal=function(name)
  local values={};return {AddInt=function(_,v)values[#values+1]=v end,AddString=function(_,v)values[#values+1]=v end,SendSignal=function()emitted[#emitted+1]={name,values}end}
 end}
 local script={RegisterServerSignalHandler=function(_,name,cb)handlers[name]=cb end}
 local t=GF_REQUIRE('gf_transport').new(game,script,function()return 0 end,{family='GF3Battle',epoch=1})
 t.start();t.pump();assert(emitted[1][1]==names.resolve('GF3BattleHello'))
 handlers[names.resolve('GF3BattleSeat')](nil,{1})
 local packet={};for i=1,24 do packet[i]=i end;packet[1]=-7201
 t.send(packet);assert(emitted[2][1]==names.resolve('GF3BattleFrames'))
 assert(emitted[2][2][4]:sub(1,10)=='GF3Battle:' and emitted[2][2][5]==1)
 assert(handlers[names.resolve('GF3BattleFramesOut')])
 assert(names.resolve('GFV2Hello')=='GFV2Hello' and names.resolve('GFV2FramesOut')=='GFV2FramesOut')
 return true
end)()""")
result={'localDraftWithoutNativeSeat':True,'lateSeatPreservesThreeReadyRoles':True,'revealAfterAcknowledgment':True,'quitSignalCloseRootAndStopUpdate':True,'mockOnly':True}
result['nativeSignalNames']=sorted(set(nativeSent));result['actualNameBindingsUsed']=bool(bindings);result['battleTransportBindingsAndGFV2Isolation']=True
(a.out/'team-seat-exit.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(result)
