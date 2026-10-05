"""Run the bundled client script offline in a mock 7.1 client (lupa, Lua 5.3).

    from harness import Client
    c = Client()                 # builds game/dist/genshin_fighter.lua first
    c.run(2.0)                   # 2 seconds at 60 fps
    c.press('J'); c.run(0.2)
    c.render('out.png')

Not the real client: the bootstrap sandbox is approximated (no load/require/coroutine,
string.rep / table.concat limited), controls follow the community 7.1 definitions, and the
renderer is a sketch of UGUI. Passing here is not client acceptance.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from lupa.lua53 import LuaRuntime

HERE = Path(__file__).resolve().parent
GAME = HERE.parent
sys.path.insert(0, str(GAME / 'tools'))
import bundle  # noqa: E402

SPEC = json.loads((HERE / 'data' / 'api_spec.json').read_text(encoding='utf-8'))

# pool sizes = what game/native puts into the map (keep in sync with gf_main.lua POOLS)
POOLS = {'img': 10000, 'txt': 160, 'btn': 24}

# keyboard names -> 7.1 key event base names
KEYS = {
    'W': 'KeyboardMoveForwardKey', 'S': 'KeyboardMoveBackwardKey', 'A': 'KeyboardMoveLeftKey',
    'D': 'KeyboardMoveRightKey', 'SPACE': 'KeyboardJumpKey', 'F': 'KeyboardInteractKey', 'E': 'KeyboardCharacterSkill1Key',
    'Q': 'KeyboardCharacterSkill2Key', 'R': 'KeyboardCharacterSkill3Key', 'T': 'KeyboardCharacterSkill4Key',
    'LMB': 'KeyboardNormalAttackKey', 'RMB': 'KeyboardSprintKey', 'X': 'KeyboardDropKey', 'TAB': 'KeyboardOpenShortcutWheelKey',
    'LCTRL': 'KeyboardSwitchToWalkOrRunKey',
}
_CRAFT = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0', 'U', 'Z', 'Y', 'G', 'H', 'I', 'O', 'P', 'J', 'K', 'L', 'V',
          'F5', 'F6', 'F7', 'F8', 'F9', 'F10', '`', '-', '=', '[', ',', '.', '/', 'UP', 'DOWN', 'LEFT', 'RIGHT',
          'RCTRL', 'RSHIFT', 'BACKSPACE', 'CAPS']
for i, k in enumerate(_CRAFT, 1):
    KEYS[k] = f'KeyboardCraftspersonKey{i}'
PAD = {'PAD_A': 'ControllerJumpKey', 'PAD_X': 'ControllerNormalAttackKey', 'PAD_B': 'ControllerSprintKey',
       'PAD_E': 'ControllerCharacterSkill1Key', 'PAD_Q': 'ControllerCharacterSkill2Key',
       'PAD_Y': 'ControllerInteractKey', 'PAD_OK': 'ControllerMenuConfirmKey', 'PAD_BACK': 'ControllerMenuBackKey'}
KEYS.update(PAD)

SANDBOX = r'''
local H, code, chunkname, REP_MAX, CONCAT_MAX = ...
local env = {}
for _, k in ipairs({'assert', 'error', 'ipairs', 'next', 'pairs', 'pcall', 'xpcall', 'select', 'tonumber', 'tostring',
                    'type', 'rawequal', 'rawget', 'rawset', 'rawlen', 'setmetatable', 'getmetatable', 'utf8'}) do env[k] = _G[k] end
env.math = setmetatable({}, {__index = math})
env.math.isinf = function(x) return x == math.huge or x == -math.huge end
env.math.isnan = function(x) return x ~= x end
env.string = setmetatable({}, {__index = string})
env.string.rep = function(s, n, sep)
    local r = string.rep(s, n, sep)
    if #r > REP_MAX then error('string.rep result too large', 2) end
    return r
end
env.table = setmetatable({}, {__index = table})
env.table.concat = function(t, sep, i, j)
    local r = table.concat(t, sep, i, j)
    if #r > CONCAT_MAX then error('table.concat result too large', 2) end
    return r
end
env.os = {time = os.time, clock = os.clock}
env.game, env.Enum, env.Color = H.game, H.Enum, H.Color
env.print = function(...) local t = {} for i = 1, select('#', ...) do t[#t + 1] = tostring((select(i, ...))) end H.log[#H.log + 1] = table.concat(t, ' ') end
env.printerr = function(...) local t = {} for i = 1, select('#', ...) do t[#t + 1] = tostring((select(i, ...))) end H.err[#H.err + 1] = table.concat(t, ' ') end
env.typeof = function(v) if getmetatable(v) == H.MT then return v._cls end return type(v) end
env._G = env
H.env = env
local fn, err = load(code, chunkname, 't', env)
if not fn then error(err) end
return fn
'''

METER = r'''
local H, fn, a, BUDGET = ...
H.instr = 0
debug.sethook(function() H.instr = H.instr + 100 end, '', 100)
local ok, err = pcall(fn, a)
debug.sethook()
return ok, err, H.instr
'''


class Client:
    def __init__(self, canvas=(1600, 900), device='KeyboardAndMouse', script=None, build=True, pools=None):
        if build:
            bundle.build()
        script = Path(script or bundle.OUT)
        self.rt = LuaRuntime(unpack_returned_tuples=True)
        spec = self.rt.eval('function(j) return j end')(self._to_lua(SPEC))
        host_src = (HERE / 'mock_host.lua').read_text(encoding='utf-8')
        self.H = self.rt.execute(host_src, spec)
        self.H.W, self.H.H = float(canvas[0]), float(canvas[1])
        self.H.device = device
        self.H.log = self.rt.table()
        self.H.err = self.rt.table()
        self.pools = dict(POOLS, **(pools or {}))
        self._build_tree()
        self.t = 0.0
        self.frame = 0
        self.heavy = []        # (frame, instructions) above 1.0 M
        self.calls = []        # native calls per frame
        self.max_instr = 0
        sandbox = self.rt.execute(SANDBOX, self.H, script.read_text(encoding='utf-8'), '@genshin_fighter.lua',
                                  1 << 20, 64 * 1024)
        self.meter = self.rt.eval('function(...) ' + METER + ' end')
        self.env = self.H.env
        self.env.script = self.script
        self.H.phase = 'load'
        self._call(sandbox, None, 'load')
        for phase in ('OnInit', 'OnEnable', 'OnStart'):
            self.H.phase = phase
            f = self.env[phase]
            if f:
                self._call(f, None, phase)
        self.H.phase = 'update'

    # ------------------------------------------------------------ setup
    def _to_lua(self, v):
        if isinstance(v, dict):
            return self.rt.table_from({k: self._to_lua(x) for k, x in v.items()})
        if isinstance(v, list):
            return self.rt.table_from([self._to_lua(x) for x in v])
        return v

    def _build_tree(self):
        new = self.H.newControl
        props = self.rt.table_from({'anchorMinX': 0, 'anchorMinY': 0, 'anchorMaxX': 1, 'anchorMaxY': 1,
                                    'sizeDeltaX': 0, 'sizeDeltaY': 0})
        self.root = new('container', 'GF_ROOT', None, props)
        self.host = new('text', 'GF_HOST', self.root, None)
        for i in range(1, self.pools['img'] + 1):
            new('image', f'GF_IMG_{i:04d}', self.root, None)
        for i in range(1, self.pools['txt'] + 1):
            new('text', f'GF_TXT_{i:03d}', self.root, None)
        for i in range(1, self.pools['btn'] + 1):
            new('button', f'GF_BTN_{i:02d}', self.root, None)
        self.H.roots = self.rt.table_from([self.root])
        self.update_enabled = False
        client = self

        script = self.rt.table()
        script.object = self.host
        script.id = 1

        def enable(_self, on):
            client.update_enabled = bool(on)
        script.EnableUpdate = enable
        script.RegisterServerSignalHandler = lambda *a: None
        script.UnregisterServerSignalHandler = lambda *a: None
        script.RegisterCustomVariableChangedHandler = lambda *a: None
        script.GetParam = lambda *a: None
        self.script = script

    def _call(self, fn, arg, label):
        ok, err, n = self.meter(self.H, fn, arg, 0)
        if n > self.max_instr:
            self.max_instr = n
        if n > 1_000_000:
            try:
                where = self.lua("GF_APP and GF_APP() and (GF_APP().sceneName .. (GF_APP().trans and '+trans' or '')) or 'boot'")
            except Exception:
                where = '?'
            self.heavy.append((self.frame, label, n, where))
        if not ok:
            raise RuntimeError(f'Lua error in {label}: {err}')
        return n

    # ------------------------------------------------------------ running
    def step(self, dt=1 / 60):
        self.H.count = 0
        f = self.env.OnUpdate
        if f and self.update_enabled:
            self._call(f, dt, f'OnUpdate#{self.frame}')
        self.H.advanceTweens(dt)
        self.calls.append(self.H.count)
        self.t += dt
        self.frame += 1
        errs = list(self.H.err.values())
        if errs:
            self.H.err = self.rt.table()
            raise RuntimeError('printerr: ' + ' | '.join(errs[:5]))

    def run(self, seconds, dt=1 / 60, every=None):
        n = int(round(seconds / dt))
        for i in range(n):
            self.step(dt)
            if every:
                every(self)

    def key(self, name, down=True):
        base = KEYS[name]
        return self.H.fireKey(self.root, base + ('Down' if down else 'Up'))

    def press(self, name, frames=2):
        self.key(name, True)
        for _ in range(frames):
            self.step()
        self.key(name, False)

    def touch(self, kind, x, y, tid=0):
        """kind: down / drag / up; canvas coordinates (origin bottom-left)."""
        return self.H.cursor(self.root, kind, x, y, tid)

    def lua(self, code):
        """Evaluate an expression inside the game's environment (tests)."""
        f = self.rt.execute('local env, src = ... return load("return " .. src, "probe", "t", env)', self.env, code)
        return f()

    def logs(self):
        return list(self.H.log.values())

    def stats(self):
        s = self.H.stats(self.root)
        return {k: s[k] for k in ('controls', 'active', 'visibleImages', 'visibleTexts', 'glyphs')}

    def snapshot(self):
        return self.H.snapshot(self.root)

    def render(self, path=None, scale=1.0):
        from render import render
        im = render(self.snapshot(), (int(self.H.W), int(self.H.H)), scale)
        if path:
            im.save(path)
        return im
