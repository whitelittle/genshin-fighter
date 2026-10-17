import assert from 'node:assert/strict';

// Shared by the runtime generator and delivery builder; original artwork stays intact.
export function progressOnlyRuntime(source) {
  let code = source;
  const replace = (from, to) => {
    assert(code.includes(from), 'Progress-only loader missing: ' + from.slice(0, 80));
    code = code.replace(from, () => to);
  };
  replace('local loadingRoot,loadingOverlay,loadingBar,loadingLabel,loadingMascot,loadingSeed',
    'local loadingRoot,loadingOverlay,loadingBar,loadingLabel,loadingTrack,loadingSeed');
  replace("local loadingState,loadingClock,loadingPose='wait',0,0",
    "local loadingState='wait'\nlocal loadingCanvasW,loadingCanvasH,loadingBarWidth\nlocal loadingDisplayClock=0");
  const start = code.indexOf('local function loadingDraw(dt)');
  const end = code.indexOf('local function loadingRequest(', start);
  assert(start >= 0 && end > start);
  code = code.slice(0, start) + `local function loadingDraw(dt)
 loadingDisplayClock=loadingDisplayClock+dt
 local cw,ch=game.GetUICanvasSize()
 local resized=cw~=loadingCanvasW or ch~=loadingCanvasH
 if not resized and loadingDisplayClock<.1 then return end
 loadingDisplayClock=0
 local width=math.min(760,cw*.7);local y=-ch/2+135
 if resized then
  loadingCanvasW=cw;loadingCanvasH=ch;loadingBarWidth=nil
  loadingTrack:SetAnchoredPosition(0,y);loadingTrack:SetSizeDelta(width,8)
  loadingLabel:SetAnchoredPosition(0,y-35);loadingLabel:SetSizeDelta(cw*.9,56)
 end
 local ratio=loadingTotal>0 and math.min(1,loadingDone/loadingTotal)or 1
 local filled=math.max(1,math.floor(width*ratio+.5))
 if filled~=loadingBarWidth then
  loadingBarWidth=filled
  loadingBar:SetSizeDelta(filled,8);loadingBar:SetAnchoredPosition(-width/2+filled/2,y)
 end
end
` + code.slice(end);
  replace("loadingLabel=loadingOverlay:FindChild('LoadingText');loadingMascot=loadingOverlay:FindChild('LoadingPaimon');",
    "loadingLabel=loadingOverlay:FindChild('LoadingText');loadingLabel:SetVisible(false);loadingTrack=loadingOverlay:FindChild('LoadingTrack');");
  replace("loadingOverlay:SetVisible(true);loadingOverlay:FindChild('LoadingBlack')",
    "loadingDisplayClock=.1;loadingBarWidth=nil;loadingLabel:SetVisible(false);loadingOverlay:SetVisible(true);loadingOverlay:FindChild('LoadingBlack')");
  replace("loadingState='error';loadingLabel.text=", "loadingState='error';loadingLabel:SetVisible(true);loadingLabel.text=");
  // Full Lua has one standalone declaration; runtime-only source has none.
  code = code.replace(/^local loadingPaimonFrames=.*\r?\n/m, '');
  assert(!/loadingPaimonFrames|loadingMascot|loadingClock|loadingPose|LoadingPaimon/.test(code));
  return code;
}

export function progressOnlyControls(root) {
  let removed = 0;
  const count = node => 1 + (node.children || []).reduce((sum, child) => sum + count(child), 0);
  function visit(node) {
    if (node.name === 'LoadingScreen') {
      node.children = (node.children || []).filter(child => {
        if (child.name !== 'LoadingPaimon') return true;
        removed += count(child);return false;
      });
      const label = node.children.find(child => child.name === 'LoadingText');
      assert(label);label.visible = false;label.text = '';
    }
    for (const child of node.children || []) visit(child);
  }
  visit(root);
  return removed;
}
