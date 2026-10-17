"""Touch controls in the mock client (phone device, wide canvas).

  python -X utf8 game/tests/test_touch.py

Checks: the on-screen controls appear only on touch devices, the stick walks player 1, the 轻
button attacks while the stick is held (two touch ids at once), the pause button opens the pause
menu, and resuming brings the controls back.
"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from harness import Client  # noqa: E402

ARGS = "{chars = {'raidenshogun', 'furina'}, mode = 'versus', stage = 'mondstadt', cpu = {false, false}}"


def boot(device, canvas=(1950, 900), build=True):
    c = Client(canvas=canvas, device=device, build=build)
    c.env.GF_FIRST_SCENE = 'fight'
    c.env.GF_FIRST_ARGS = c.lua(ARGS)
    for _ in range(60 * 20):
        c.step()
        if c.lua("GF_APP() ~= nil and GF_APP().scene ~= nil and GF_APP().scene.state == 'run'"):
            break
    else:
        raise SystemExit('fight never started')
    # skip the round intro
    for _ in range(60 * 4):
        c.step()
        if c.lua("GF_APP().scene.sim.phase == 'fight'"):
            return c
    raise SystemExit('round never started')


def to_canvas(c, x, y):
    """design coordinates (centre origin) -> canvas pixels (bottom-left origin)"""
    s, cw, ch = c.lua('GF_APP().s'), c.lua('GF_APP().cw'), c.lua('GF_APP().ch')
    return cw / 2 + x * s, ch / 2 + y * s


def button(c, bid):
    for i in range(1, 7):
        if c.lua(f"GF_APP().scene.touch.buttons[{i}].id") == bid:
            return c.lua(f"GF_APP().scene.touch.buttons[{i}].x"), c.lua(f"GF_APP().scene.touch.buttons[{i}].y")
    raise KeyError(bid)


def main():
    fails = []

    def check(name, ok):
        print(('PASS ' if ok else 'FAIL ') + name)
        if not ok:
            fails.append(name)

    pc = boot('KeyboardAndMouse')
    check('no touch controls on PC', pc.lua('GF_APP().scene.touch == nil'))

    c = boot('Mobile', build=False)
    check('touch controls on phone', c.lua('GF_APP().scene.touch ~= nil'))
    check('hud compact on phone', c.lua('GF_APP().scene.hud.compact == true'))

    # stick: press in the lower-left, drag right, hold
    x0 = c.lua('GF_APP().scene.sim.f[1].x')
    sx, sy = to_canvas(c, -c.lua('GF_APP().W') / 2 + 260, -c.lua('GF_APP().H') / 2 + 200)
    c.touch('down', sx, sy, 1)
    c.touch('drag', sx + 90, sy, 1)
    c.run(0.6)
    x1 = c.lua('GF_APP().scene.sim.f[1].x')
    check(f'stick walks forward ({x0} -> {x1})', x1 > x0 + 1000)

    # light attack with the stick still held (second finger)
    lx, ly = to_canvas(c, *button(c, 'LP'))
    c.touch('down', lx, ly, 2)
    c.step(); c.step()
    st = c.lua('GF_APP().scene.sim.f[1].state')
    mv = c.lua("(GF_APP().scene.sim.f[1].move or {}).name or ''")
    c.touch('up', lx, ly, 2)
    check(f'轻 attacks while stick held (state={st} move={mv})', st == 'attack')
    c.touch('up', sx + 90, sy, 1)
    c.run(0.5)

    # pause button
    px, py = to_canvas(c, 0, c.lua('GF_APP().H') / 2 - 222)
    c.touch('down', px, py, 3)
    c.touch('up', px, py, 3)
    c.step()
    check('pause button opens pause', c.lua('GF_APP().scene.paused == true'))
    c.lua('(function() GF_APP().scene:closePause() end)()')
    c.step()
    check('touch areas back after resume', c.lua('#GF_APP().input.buttons') >= 8)
    lx, ly = to_canvas(c, *button(c, 'LP'))
    c.run(0.4)
    c.touch('down', lx, ly, 4)
    c.step(); c.step()
    check('轻 works after resume', c.lua('GF_APP().scene.sim.f[1].state') == 'attack')
    c.touch('up', lx, ly, 4)
    errs = list(c.H.err.values()) if c.H.err else []
    check(f'no Lua errors ({len(errs)})', not errs)
    print('max instr', c.max_instr)

    # menus by touch only: title -> menu -> back hint -> title -> menu -> arcade -> random x1
    # -> stage arrows -> confirm -> VS
    m = Client(canvas=(1950, 900), device='Mobile', build=False)

    def scene():
        return m.lua('GF_APP() and GF_APP().sceneName')

    def wait(name, limit=10):
        for _ in range(int(limit * 60)):
            m.step()
            if scene() == name and not m.lua('GF_APP().trans ~= nil'):
                m.run(0.7)
                return True
        return False

    def tap(x, y):
        px, py = to_canvas(m, x, y)
        m.touch('down', px, py, 9)
        m.touch('up', px, py, 9)
        m.step(); m.step()

    def tapArea(name):
        # the scene's own tap area (UI.tap / UI.prompt), so layout changes do not break the test
        x = m.lua(f"GF_APP().scene.L.taps['{name}'].x")
        y = m.lua(f"GF_APP().scene.L.taps['{name}'].y")
        tap(x, y)
    check('title reached', wait('title', 15))
    tap(0, 0)
    check('tap title -> menu', wait('menu'))
    tapArea('promptK')                              # K 返回 hint
    check('back hint -> title', wait('title'))
    tap(0, 0)
    wait('menu')
    m.lua('(function() GF_APP().scene.menu.sel = 2 end)()')
    tapArea('promptJ')                              # J 确认 hint -> versus submenu
    m.run(0.4)
    tapArea('promptJ')                              # -> vs CPU
    check('confirm hint -> select', wait('select'))
    tapArea('promptL')                              # L 随机 (P1)
    m.run(0.3)
    tapArea('promptL')                              # L 随机 (opponent)
    m.run(0.3)
    check('random hint picks a character', m.lua("GF_APP().scene.phase") == 'stage')
    s0 = m.lua('GF_APP().scene.stageI')
    tapArea('stageR')
    check('stage arrow by tap', m.lua('GF_APP().scene.stageI') != s0)
    tapArea('stageOk')
    check('stage confirm by tap -> VS', wait('vs'))
    errs = list(m.H.err.values()) if m.H.err else []
    check(f'no Lua errors in menus ({len(errs)})', not errs)
    if fails:
        raise SystemExit(f'{len(fails)} failed')


if __name__ == '__main__':
    main()
