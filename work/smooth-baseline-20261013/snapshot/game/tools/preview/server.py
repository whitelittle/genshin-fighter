"""Live browser preview of the game: runs the real client bundle in the offline mock client
(game/tests/harness.py) at 60 Hz and streams draw lists to a canvas renderer.

  python -X utf8 game/tools/preview/server.py [--port 8765] [--scene intro] [--canvas 1600x900]
  then open http://127.0.0.1:8765/

Keyboard in the page is forwarded as 7.1 key events (WASD, J K L I U O, Space, arrows,
, . / RShift RCtrl, P / Tab pause, F9 debug). Click / touch go to pooled buttons.
Local development tool only: the mock is not the Genshin client.
"""
from __future__ import annotations

import argparse
import json
import sys
import threading
import time
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

sys.stdout.reconfigure(encoding='utf-8')
HERE = Path(__file__).resolve().parent
GAME = HERE.parent.parent
sys.path.insert(0, str(GAME / 'tests'))
sys.path.insert(0, str(GAME / 'tools'))
from harness import Client  # noqa: E402


class Runner:
    def __init__(self, scene, args, canvas, device):
        self.lock = threading.Lock()
        self.scene, self.args, self.canvas, self.device = scene, args, canvas, device
        self.frame_text = ''
        self.frame_id = 0
        self.events = []
        self.error = None
        self.stats = {}
        self.restart_flag = False
        self.paused = False
        self.speed = 1.0
        self.start()

    def start(self):
        self.client = Client(canvas=self.canvas, device=self.device)
        c = self.client
        if self.scene:
            c.env.GF_FIRST_SCENE = self.scene
        if self.args:
            c.env.GF_FIRST_ARGS = self.to_lua(self.args)
        if getattr(self, 'settings', None):
            c.env.GF_SETTINGS = self.to_lua(self.settings)
        self.error = None

    def to_lua(self, v):
        rt = self.client.rt
        if isinstance(v, dict):
            return rt.table_from({k: self.to_lua(x) for k, x in v.items()})
        if isinstance(v, list):
            return rt.table_from([self.to_lua(x) for x in v])
        return v

    def loop(self):
        dt = 1 / 60
        nxt = time.perf_counter()
        while True:
            if self.restart_flag:
                with self.lock:
                    self.restart_flag = False
                    try:
                        self.start()
                    except Exception:
                        self.error = traceback.format_exc()
            now = time.perf_counter()
            if now < nxt:
                time.sleep(min(nxt - now, 0.01))
                continue
            nxt += dt / self.speed
            if now - nxt > 0.25:
                nxt = now
            with self.lock:
                evs, self.events = self.events, []
                c = self.client
                try:
                    for ev in evs:
                        if ev['t'] == 'key':
                            c.key(ev['k'], ev['down'])
                        elif ev['t'] == 'touch':
                            c.touch(ev['kind'], ev['x'], ev['y'], ev.get('id', 0))
                        elif ev['t'] == 'cursor':
                            c.H.cursorPos[1], c.H.cursorPos[2] = ev['x'], ev['y']
                    if not self.paused and not self.error:
                        t0 = time.perf_counter()
                        c.step(dt)
                        lua_ms = (time.perf_counter() - t0) * 1000
                        if c.frame % 2 == 0:
                            self.frame_text = c.H.snapshotText(c.root)
                            self.frame_id = c.frame
                        if c.frame % 30 == 0:
                            st = c.stats()
                            st.update({'frame': c.frame, 'calls': c.calls[-1], 'instr': c.max_instr, 'luaMs': round(lua_ms, 2)})
                            self.stats = st
                except Exception:
                    self.error = traceback.format_exc()
                    print(self.error)


RUNNER: Runner | None = None


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def send(self, code, body, ctype='text/plain; charset=utf-8'):
        data = body.encode('utf-8') if isinstance(body, str) else body
        self.send_response(code)
        self.send_header('Content-Type', ctype)
        self.send_header('Content-Length', str(len(data)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        u = urlparse(self.path)
        if u.path == '/logo':
            return self.send(200, (GAME / 'tools' / 'logo' / 'logo.html').read_text(encoding='utf-8'), 'text/html; charset=utf-8')
        if u.path in ('/', '/index.html'):
            return self.send(200, (HERE / 'index.html').read_text(encoding='utf-8'), 'text/html; charset=utf-8')
        if u.path == '/frame':
            r = RUNNER
            since = int(parse_qs(u.query).get('since', ['-1'])[0])
            if r.error:
                return self.send(200, 'E\n' + r.error)
            if r.frame_id == since:
                return self.send(204, b'')
            return self.send(200, f'F{r.frame_id} {r.canvas[0]}x{r.canvas[1]}\n' + r.frame_text)
        if u.path == '/stats':
            return self.send(200, json.dumps(RUNNER.stats), 'application/json')
        if u.path == '/restart':
            q = parse_qs(u.query)
            if 'scene' in q:
                RUNNER.scene = q['scene'][0]
            if 'args' in q:
                RUNNER.args = json.loads(q['args'][0])
            if 'device' in q:
                RUNNER.device = q['device'][0]
            if 'canvas' in q:
                RUNNER.canvas = tuple(int(v) for v in q['canvas'][0].split('x'))
            if 'settings' in q:
                RUNNER.settings = json.loads(q['settings'][0])
            RUNNER.restart_flag = True
            return self.send(200, 'ok')
        if u.path == '/pause':
            RUNNER.paused = not RUNNER.paused
            return self.send(200, str(RUNNER.paused))
        if u.path == '/speed':
            RUNNER.speed = float(parse_qs(u.query).get('v', ['1'])[0])
            return self.send(200, 'ok')
        self.send(404, 'not found')

    def do_POST(self):
        n = int(self.headers.get('Content-Length', 0))
        body = json.loads(self.rfile.read(n) or b'{}')
        if self.path == '/save':
            # design pages (tools/logo) export their canvas here; baked later by tools/build_logo.py
            import base64
            out = GAME / 'tools' / 'logo' / (Path(body['name']).name + '.png')
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_bytes(base64.b64decode(body['png'].split(',', 1)[1]))
            return self.send(200, str(out))
        if self.path == '/shot':
            import base64
            out = GAME / 'build' / 'shots' / 'live.png'
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_bytes(base64.b64decode(body['png'].split(',', 1)[1]))
            return self.send(200, str(out))
        if self.path == '/input':
            with RUNNER.lock:
                RUNNER.events.extend(body if isinstance(body, list) else [body])
            return self.send(200, 'ok')
        self.send(404, 'not found')


def main():
    global RUNNER
    ap = argparse.ArgumentParser()
    ap.add_argument('--port', type=int, default=8765)
    ap.add_argument('--scene', default=None)
    ap.add_argument('--args', default=None, help='JSON args for the first scene')
    ap.add_argument('--canvas', default='1600x900')
    ap.add_argument('--device', default='KeyboardAndMouse')
    a = ap.parse_args()
    w, h = (int(v) for v in a.canvas.split('x'))
    RUNNER = Runner(a.scene, json.loads(a.args) if a.args else None, (w, h), a.device)
    threading.Thread(target=RUNNER.loop, daemon=True).start()
    srv = ThreadingHTTPServer(('127.0.0.1', a.port), Handler)
    print(f'preview on http://127.0.0.1:{a.port}/')
    srv.serve_forever()


if __name__ == '__main__':
    main()
