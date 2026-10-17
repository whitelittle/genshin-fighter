"""Local anonymous comment store, bounded public API collector and dashboard."""
import argparse
import hashlib
import json
import os
import re
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

BASE = Path(__file__).resolve().parent
STATE = BASE / 'data' / 'state.json'
LOCK = threading.RLock()
INTERVAL = 3600
URLS = {
    'bilibili': 'https://www.bilibili.com/video/BV1tgpz6EEZV/',
    'miyoushe': 'https://act.miyoushe.com/ys/ugc_community/mx/#/pages/level-detail/index?id=24196780849&region=cn_gf01',
}
TOPICS = [
    ('开始阻断', r'无法开始|不能开始|没办法开始|进不去|任意键'),
    ('卡顿与低帧', r'卡顿|有点卡|卡的|卡得|帧|不流畅'),
    ('大招受理', r'吞.*大招|大招.*[吞吃]|被吃|被吞'),
    ('动作辨识', r'出招|动作.*[少僵]|轻重|前.*摇|后.*摇'),
    ('闪避与冲刺', r'闪避|冲刺|前冲|后撤'),
    ('强度平衡', r'超模|强度|平衡'),
    ('打击反馈', r'打击感|受击|硬直'),
    ('音效', r'音效|声音|金属|铁器|语音'),
    ('比例与美术', r'比例|头.*大|背景|街道|观众'),
    ('界面', r'UI|ui|界面|按键说明'),
    ('延迟与联机', r'延迟|网络|瞬移|服务器'),
    ('玩法建议', r'援护|协力|元素反应|换人|拳皇|火影|街霸|闯关|国际服|街机|MUGEN|mugen'),
]

def now():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')

def anonymize(text):
    text = str(text or '')
    text = re.sub(r'(?<!\d)1[3-9]\d{9}(?!\d)|[a-zA-Z0-9_.+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', '[联系方式已隐藏]', text)
    text = re.sub(r'回复\s*[@＠][^：:\n]{1,100}[:：]\s*', '回复匿名玩家：', text)
    text = re.sub(r'[@＠][\w\-\u4e00-\u9fff]+', '匿名玩家', text)
    text = re.sub(r'https?://\S+', '[链接已省略]', text)
    text = re.sub(r'(?i)(?:uid|账号|用户id|QQ|微信|联系方式)\s*[:：=]?\s*[\w-]+', '[账号/联系方式已隐藏]', text)
    text = re.sub(r'[A-Za-z]:[\\/]+Users[\\/]+[^\\/\s]+', '%USERPROFILE%', text, flags=re.I)
    return re.sub(r'\s+', ' ', text).strip()[:12000]

def fingerprint(text):
    return hashlib.sha256(re.sub(r'[\s\W_]+', '', text.lower()).encode()).hexdigest()[:24]

def initial_state():
    state = {'version': 1, 'updated_at': now(), 'interval_seconds': INTERVAL,
             'sources': {}, 'comments': []}
    for source, url in URLS.items():
        state['sources'][source] = {'url': url, 'status': 'pending', 'last_success': None,
                                    'last_attempt': None, 'coverage': '等待采集', 'error': ''}
    # Previous anonymous summaries are labelled historical; never masquerade as live text.
    doc = BASE.parent.parent / 'docs/current/公开评论反馈去重记录_20261014.md'
    if doc.exists():
        for line in doc.read_text(encoding='utf-8').splitlines():
            cells = [x.strip() for x in line.split('|')[1:-1]]
            if not cells or not re.fullmatch(r'[MB]\d{2}', cells[0]):
                continue
            source = 'miyoushe' if cells[0][0] == 'M' else 'bilibili'
            text = anonymize(cells[2] if source == 'miyoushe' else cells[1])
            state['comments'].append({'key': source + ':summary:' + cells[0], 'source': source,
                'text': text, 'kind': '历史整理摘要', 'published': '', 'first_seen': now(),
                'last_seen': now(), 'fingerprint': fingerprint(text), 'summary': True})
    return state

def read_state():
    with LOCK:
        return json.loads(STATE.read_text(encoding='utf-8')) if STATE.exists() else initial_state()

def write_state(state):
    with LOCK:
        STATE.parent.mkdir(parents=True, exist_ok=True)
        tmp = STATE.with_suffix('.tmp')
        tmp.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding='utf-8')
        os.replace(tmp, STATE)

def ingest(source, records, coverage, advertised=None):
    if source not in URLS:
        raise ValueError('未知来源')
    if not isinstance(records, list) or not records:
        raise ValueError('空采集结果未覆盖已有记录；请核对登录、加载及页面变化')
    stamp = now()
    with LOCK:
        state = read_state()
        known = {c['key']: c for c in state['comments']}
        added = 0
        valid = 0
        for raw in records:
            text = anonymize(raw.get('text', ''))
            if not text:
                continue
            valid += 1
            fp = fingerprint(text)
            # No account or comment-author IDs are persisted. Content dedup cannot count players.
            key = source + ':text:' + fp
            old = known.get(key)
            if old:
                old['last_seen'] = stamp
            else:
                item = {'key': key, 'source': source, 'text': text,
                        'kind': str(raw.get('kind', '页面评论'))[:40],
                        'published': anonymize(raw.get('time', ''))[:80],
                        'first_seen': stamp, 'last_seen': stamp,
                        'fingerprint': fp, 'summary': False}
                state['comments'].append(item)
                known[key] = item
                added += 1
        if not valid:
            raise ValueError('未采到有效正文，保留旧数据')
        state['sources'][source].update(status='ok', last_attempt=stamp, last_success=stamp,
            coverage=str(coverage)[:200], advertised=str(advertised or '')[:60], error='',
            captured_count=len(records), new_count=added)
        state['updated_at'] = stamp
        write_state(state)
    return added

def mark_error(source, message):
    with LOCK:
        state = read_state()
        state['sources'][source].update(status='error', last_attempt=now(), error=anonymize(message))
        state['updated_at'] = now()
        write_state(state)

def request_json(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0',
        'Referer': URLS['bilibili'], 'Accept': 'application/json'})
    with urllib.request.urlopen(req, timeout=15) as response:
        data = json.load(response)
    if data.get('code') != 0:
        raise ValueError('站点返回限制或错误，代码 ' + str(data.get('code')))
    return data.get('data') or {}

def collect_bilibili():
    # Legacy public endpoint; empty or partial data is treated as incomplete, not success.
    aid = '117434421878626'
    records, roots = [], {}
    total = None
    for page in range(1, 21):
        url = 'https://api.bilibili.com/x/v2/reply?' + urllib.parse.urlencode(
            {'type': 1, 'oid': aid, 'pn': page, 'ps': 20, 'sort': 0})
        data = request_json(url)
        total = data.get('page', {}).get('count', total)
        replies = list(data.get('replies') or [])
        for field in ('top', 'upper'):
            obj = data.get(field) or {}
            if field == 'upper':
                obj = obj.get('top') or {}
            if isinstance(obj, dict):
                if obj.get('rpid'):
                    replies.append(obj)
                else:
                    replies.extend(x for x in obj.values() if isinstance(x, dict) and x.get('rpid'))
        for item in replies:
            roots[str(item['rpid'])] = item
        if not data.get('replies') or len(roots) >= (total or 10**9):
            break
        time.sleep(0.5)
    if not roots:
        raise ValueError('公开接口返回空列表，与已知评论不符；需已登录浏览器采集')
    for rpid, item in roots.items():
        records.append({'text': item.get('content', {}).get('message'), 'kind': '主评论',
                        'time': str(item.get('ctime', ''))})
        reply_count = item.get('rcount', 0)
        if reply_count:
            for page in range(1, min(20, (reply_count + 19) // 20) + 1):
                url = 'https://api.bilibili.com/x/v2/reply/reply?' + urllib.parse.urlencode(
                    {'type': 1, 'oid': aid, 'root': rpid, 'pn': page, 'ps': 20})
                data = request_json(url)
                for reply in data.get('replies') or []:
                    records.append({'text': reply.get('content', {}).get('message'),
                                    'kind': '回复', 'time': str(reply.get('ctime', ''))})
                time.sleep(0.5)
    return records, '公开接口分页（最多20页；不保证平台全部可见内容）', total

def refresh():
    try:
        records, coverage, total = collect_bilibili()
        ingest('bilibili', records, coverage, total)
    except Exception as exc:
        mark_error('bilibili', str(exc))
    mark_error('miyoushe', '此动态页面需浏览器采集；小时任务会读取公开评价页面并导入')

def dashboard():
    state = read_state()
    groups = {}
    for item in state['comments']:
        fp = item['fingerprint']
        group = groups.setdefault(fp, {'id': fp, 'text': item['text'], 'entries': [], 'topics': []})
        group['entries'].append({k: item[k] for k in ('source', 'kind', 'published', 'first_seen', 'last_seen', 'summary')})
        group['topics'] = [name for name, pattern in TOPICS if re.search(pattern, item['text'])] or ['其他反馈']
    state['groups'] = sorted(groups.values(), key=lambda g: max(e['last_seen'] for e in g['entries']), reverse=True)
    state['comments'] = []
    return state

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass

    def send(self, status, body, content_type='application/json; charset=utf-8'):
        if isinstance(body, (dict, list)):
            body = json.dumps(body, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Content-Security-Policy', "default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self'; connect-src 'self'; frame-ancestors 'none'")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == '/api/state':
            return self.send(200, dashboard())
        if self.path in ('/', '/index.html'):
            return self.send(200, (BASE / 'index.html').read_bytes(), 'text/html; charset=utf-8')
        if self.path == '/app.js':
            return self.send(200, (BASE / 'app.js').read_bytes(), 'text/javascript; charset=utf-8')
        self.send(404, {'error': '页面不存在'})

    def do_POST(self):
        # Local-only server. No cross-origin writes, arbitrary file access or cookie endpoint.
        if self.headers.get('Origin') not in (None, f'http://127.0.0.1:{self.server.server_port}',
                                              f'http://localhost:{self.server.server_port}'):
            return self.send(403, {'error': '不接受跨站操作'})
        if self.path != '/api/request-refresh':
            return self.send(404, {'error': '接口不存在'})
        with LOCK:
            state = read_state()
            state['refresh_requested'] = now()
            write_state(state)
        self.send(202, {'message': '已登记更新请求，小时采集任务将处理；本页刷新不向原站发送请求'})

def serve(port):
    if not STATE.exists():
        write_state(initial_state())
    ThreadingHTTPServer(('127.0.0.1', port), Handler).serve_forever()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--serve', action='store_true')
    parser.add_argument('--port', type=int, default=8807)
    parser.add_argument('--refresh', action='store_true')
    parser.add_argument('--ingest', choices=list(URLS))
    parser.add_argument('--input', type=Path)
    parser.add_argument('--status', action='store_true')
    args = parser.parse_args()
    if args.serve:
        serve(args.port)
    elif args.ingest:
        import sys
        payload = json.loads(args.input.read_text(encoding='utf-8')) if args.input else json.load(sys.stdin)
        added = ingest(args.ingest, payload['records'], payload.get('coverage', '已加载页面正文，非全量保证'), payload.get('advertised'))
        print(json.dumps({'source': args.ingest, 'added': added}, ensure_ascii=False))
    elif args.refresh:
        refresh()
        print(json.dumps({k: {'status': v['status'], 'error': v['error']} for k,v in read_state()['sources'].items()}, ensure_ascii=False))
    elif args.status:
        print(json.dumps({k: {'status': v['status'], 'count': v.get('captured_count')} for k,v in read_state()['sources'].items()}, ensure_ascii=False))
    else:
        write_state(read_state())
        print('已初始化匿名历史摘要；使用 --serve 启动查看页')

if __name__ == '__main__':
    main()
