"""Serve the preserved V3 action pages with their original /actions routes."""
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent / 'github-review-20261009' / 'V3' / 'assets' / 'action-reference'
PROJECT = Path(__file__).resolve().parents[1]
if (PROJECT / 'outputs/dual-character-reference-20261011').is_dir():
    ROOT = PROJECT / 'outputs/dual-character-reference-20261011'
PACKAGES = {'furina': PROJECT / 'outputs/furina-design-20261010',
            'ayaka': PROJECT / 'outputs/v4-one-character-20261010/ayaka-armed-v2'}

class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def do_GET(self):
        for name, folder in PACKAGES.items():
            prefix = '/actions/' + name + '/'
            if self.path.startswith(prefix):
                self.directory = str(folder)
                self.path = '/' + self.path[len(prefix):]
                return super().do_GET()
        if self.path.startswith('/actions/'):
            self.path = self.path[len('/actions'):]
        super().do_GET()

if __name__ == '__main__':
    ThreadingHTTPServer(('127.0.0.1', 8767), Handler).serve_forever()
