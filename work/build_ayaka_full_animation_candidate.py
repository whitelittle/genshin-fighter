"""Assemble an isolated, review-only Ayaka fitted-frame animation package."""
from __future__ import annotations

import json
import math
import sys
import base64
import shutil
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
V4 = ROOT / "work" / "v4-handoff-20261009-partial" / "V4"
OUT = ROOT / "outputs" / "v4-one-character-20261010" / "ayaka-full-animation-candidate"
FIT_ROOT = V4 / "evidence"
sys.path.insert(0, str(ROOT / "game" / "tools"))
import artlib  # noqa: E402

PALETTE = [(174, 224, 255, 255), (115, 175, 255, 220), (230, 250, 255, 255), (117, 145, 230, 210)]
PREVIEW_SCALE = 4
PREVIEW_SIZE = (720, 420)
PREVIEW_FOOT_Y = 370

SOURCES = {
    "idle": "kamisatoayaka-idle-review",
    "walk": "kamisatoayaka-walk-review",
    "backwalk": "codex-batch-20261009/kamisatoayaka-backwalk-body-v1",
    "crouch": "codex-batch-20261009/kamisatoayaka-crouch-body-v2",
    "crouchguard": "codex-batch-20261009/kamisatoayaka-crouchguard-body-v1",
    "jump": "codex-batch-20261009/kamisatoayaka-jump-body-v1",
    "guard": "codex-batch-20261009/kamisatoayaka-standguard-body-v1",
    "hurt_knockdown": "codex-batch-20261009/kamisatoayaka-hit_knockdown-body-v1",
    "wakeup": "codex-batch-20261009/kamisatoayaka-wakeup-body-v1",
    "forwarddash": "codex-batch-20261009/kamisatoayaka-forwarddash-body-v1",
    "backdash": "codex-batch-20261009/kamisatoayaka-backdash-body-v1",
    "light2": "actions-20261009/kamisatoayaka-light2-body-v1",
    "light3": "full-delivery-20261009/kamisatoayaka-light3-body-full-v1",
    "heavy": "full-delivery-20261009/kamisatoayaka-heavy-body-full-v1",
    "crouchlight": "full-delivery-20261009/kamisatoayaka-crouchlight-body-full-v1",
    "crouchheavy": "full-delivery-20261009/kamisatoayaka-crouchheavy-body-full-v1",
    "airlight": "full-delivery-20261009/kamisatoayaka-airlight-body-full-v1",
    "airheavy": "codex-batch-20261009/kamisatoayaka-airheavy-body-v1",
    "E": "kamisatoayaka-E-composite-review",
    "Q": "codex-batch-20261009/kamisatoayaka-Q-body-v1",
    "throw": "codex-batch-20261009/kamisatoayaka-throw-body-v2",
    "victim": "codex-batch-20261009/kamisatoayaka-victim-body-v2",
    "defeat": "codex-batch-20261009/kamisatoayaka-defeat-body-v1",
}


def load_optimized(rel: str) -> list[Image.Image]:
    d = FIT_ROOT / rel
    paths = list(d.glob("optimized-*.png")) or list(d.glob("fit-*.png"))
    return [Image.open(p).convert("RGBA") for p in sorted(paths, key=lambda p: int(p.stem.rsplit("-", 1)[1]))]


def fit_victory() -> list[Image.Image]:
    src = V4 / "assets" / "codex-batch-20261009" / "kamisatoayaka-victory-body-v1.png"
    idle_report = json.loads((FIT_ROOT / "kamisatoayaka-idle-review" / "fit.json").read_text(encoding="utf-8"))
    palette = idle_report["palette"]
    target_h = idle_report["optimized_height"]
    im = Image.open(src).convert("RGBA")
    out = []
    for i in range(4):
        cell = im.crop(((i % 2) * im.width // 2, (i // 2) * im.height // 2,
                        (i % 2 + 1) * im.width // 2, (i // 2 + 1) * im.height // 2))
        small = artlib.downscale(cell, target_h / cell.height)
        idx = artlib.apply_palette(small, palette[:-1])
        rects = artlib.painter(idx)
        rgba = Image.new("RGBA", small.size, (0, 0, 0, 0))
        px = rgba.load()
        for x, y, w, h, ci in rects:
            col = tuple(palette[ci])
            for yy in range(y, y + h):
                for xx in range(x, x + w):
                    px[xx, yy] = (*col[:3], 255)
        out.append(rgba)
    return out


def effect_layer(kind: str, size: tuple[int, int], frame: int, total: int) -> Image.Image:
    w, h = size
    e = Image.new("RGBA", size, (0, 0, 0, 0))
    d = ImageDraw.Draw(e)
    if kind == "slash":
        progress = frame / max(1, total - 1)
        box = (w * 0.28, h * 0.18, w * 0.90, h * 0.92)
        d.arc(box, 205 - int(progress * 35), 325 - int(progress * 35), fill=PALETTE[0], width=max(2, w // 36))
        d.arc((box[0] + 5, box[1] + 4, box[2] - 7, box[3] - 4), 205 - int(progress * 35), 325 - int(progress * 35), fill=PALETTE[2], width=max(1, w // 70))
        for n in range(3):
            x = int(w * (0.45 + 0.16 * n) - frame * 2)
            y = int(h * (0.28 + 0.14 * n))
            d.polygon([(x, y - 4), (x + 4, y), (x, y + 4), (x - 4, y)], fill=PALETTE[2])
    elif kind == "q":
        cx, cy = int(w * 0.58), int(h * 0.48)
        radius = int(min(w, h) * (0.22 + 0.08 * math.sin(frame / max(1, total - 1) * math.pi)))
        d.ellipse((cx - radius, cy - radius, cx + radius, cy + radius), outline=PALETTE[0], width=max(2, w // 42))
        for n in range(8):
            a = math.tau * n / 8 + frame * 0.16
            x, y = cx + int(math.cos(a) * radius * 1.45), cy + int(math.sin(a) * radius * 1.45)
            d.polygon([(x, y - 7), (x + 7, y), (x, y + 7), (x - 7, y)], fill=PALETTE[n % len(PALETTE)])
    return e


def alpha_bbox(im: Image.Image) -> tuple[int, int, int, int] | None:
    return im.getchannel("A").getbbox()


def compose(body: Image.Image, overlay: Image.Image | None, label: str, frame: int, total: int) -> Image.Image:
    canvas = Image.new("RGBA", PREVIEW_SIZE, (31, 38, 51, 255))
    # Fixed preview pixel scale: never rescale each frame by its own bbox.
    bbox = alpha_bbox(body)
    scale = PREVIEW_SCALE
    bw, bh = max(1, round(body.width * scale)), max(1, round(body.height * scale))
    b = body.resize((bw, bh), Image.Resampling.NEAREST)
    if bbox:
        bx0, by0, bx1, by1 = [v * scale for v in bbox]
        x = round((PREVIEW_SIZE[0] - (bx0 + bx1)) / 2)
        y = round(PREVIEW_FOOT_Y - by1)
    else:
        x, y = (PREVIEW_SIZE[0] - bw) // 2, PREVIEW_FOOT_Y - bh
    if overlay:
        ov = overlay.resize((bw, bh), Image.Resampling.NEAREST)
        canvas.alpha_composite(ov, (x, y))
    canvas.alpha_composite(b, (x, y))
    d = ImageDraw.Draw(canvas)
    d.text((14, 10), f"{label}  {frame + 1}/{total}", fill=(240, 245, 255, 255))
    d.line((30, PREVIEW_FOOT_Y + 1, PREVIEW_SIZE[0] - 30, PREVIEW_FOOT_Y + 1), fill=(98, 114, 141, 255), width=1)
    return canvas.convert("RGB")


def data_url(path: Path) -> str:
    return "data:image/png;base64," + base64.b64encode(path.read_bytes()).decode("ascii")


def write_viewer(action_manifest: dict) -> None:
    new_source = ROOT / 'outputs/v4-one-character-20261010/ayaka-armed-v2/standguard-source-v1.png'
    if new_source.exists():
        (OUT / 'new-assets').mkdir(exist_ok=True)
        shutil.copy2(new_source, OUT / 'new-assets/standguard-source-v1.png')
    actions = {}
    for name in action_manifest:
        actions[name] = [data_url(p) for p in sorted((OUT / "actions" / name).glob("frame-*.png"))]
    refs = {}
    for key, path in {
        "芙宁娜站姿·0": FIT_ROOT / "furina-idle-review" / "optimized-0.png",
        "芙宁娜站姿·1": FIT_ROOT / "furina-idle-review" / "optimized-1.png",
        "八重神子蹲姿·0": FIT_ROOT / "codex-batch-20261009" / "yaemiko-crouchheavy-body-v3" / "fit-0.png",
        "八重神子蹲姿·1": FIT_ROOT / "codex-batch-20261009" / "yaemiko-crouchheavy-body-v3" / "fit-1.png",
    }.items():
        if path.exists():
            cmp = compose(Image.open(path).convert("RGBA"), None, key, 0, 1)
            ref_path = OUT / "comparisons" / (key.replace("·", "-") + ".png")
            ref_path.parent.mkdir(exist_ok=True)
            cmp.save(ref_path)
            refs[key] = data_url(ref_path)
    payload = json.dumps({"actions": actions, "refs": refs}, ensure_ascii=False)
    html = """<!doctype html><meta charset='utf-8'><title>绫华全动作拟合帧动画预览</title>
<style>
body{margin:0;background:#111827;color:#e5edff;font-family:system-ui,"Microsoft YaHei",sans-serif}main{max-width:1180px;margin:auto;padding:22px}h1{font-size:22px;margin:0 0 8px}p{color:#aab8d4}.bar{display:flex;gap:10px;align-items:center;flex-wrap:wrap;background:#1d2638;padding:12px;border-radius:10px}.stage{margin-top:16px;background:#1f2633;border:1px solid #44516b;border-radius:12px;padding:12px;text-align:center}.stage img{width:min(960px,100%);image-rendering:pixelated;display:block;margin:auto}.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(360px,1fr));gap:12px;margin-top:16px}.card{background:#1d2638;padding:10px;border-radius:10px}.card img{width:100%;height:auto;object-fit:contain;background:#10151f;image-rendering:pixelated;display:block}.small{font-size:12px;color:#aab8d4}button,select,input{font:inherit}button{background:#6fa7ff;border:0;border-radius:6px;padding:6px 10px;color:#071326}label{font-size:13px}
</style><main><h1>绫华全动作拟合帧动画 · 固定像素倍率预览</h1><p>这是离线候选查看器，不代表运行时锚点、命中框或真机验收。所有帧共用固定4倍像素倍率、统一画布和脚底线；不再按每帧包围盒单独放大，原始拟合 PNG 未被改写。</p><div class='bar'><label>动作 <select id='action'></select></label><button id='play'>播放</button><button id='prev'>上一帧</button><button id='next'>下一帧</button><label>速度 <input id='speed' type='range' min='60' max='500' value='160'> ms</label><span id='info'></span></div><div class='stage'><img id='frame' alt='绫华帧'></div><div class='cards'><div class='card'><b>芙宁娜站姿交付</b><img id='furina0'><img id='furina1'><div class='small'>同一固定4倍像素倍率与统一画布预览。</div></div><div class='card'><b>八重神子蹲姿交付</b><img id='yae0'><img id='yae1'><div class='small'>同一固定4倍像素倍率与统一画布预览。</div></div></div></main><script>
const DATA=__PAYLOAD__;const sel=document.querySelector('#action'),img=document.querySelector('#frame'),info=document.querySelector('#info');let i=0,timer=null;for(const k of Object.keys(DATA.actions)){const o=document.createElement('option');o.value=k;o.textContent=k;sel.append(o)}function show(){const a=DATA.actions[sel.value];i=(i+a.length)%a.length;img.src=a[i];info.textContent=`${sel.value} · ${i+1}/${a.length}`}function restart(){if(timer)clearInterval(timer);timer=setInterval(()=>{i++;show()},+document.querySelector('#speed').value)}sel.onchange=()=>{i=0;show()};document.querySelector('#prev').onclick=()=>{i--;show()};document.querySelector('#next').onclick=()=>{i++;show()};document.querySelector('#play').onclick=()=>{if(timer){clearInterval(timer);timer=null;event.target.textContent='播放'}else{restart();event.target.textContent='暂停'}};document.querySelector('#speed').oninput=()=>{if(timer)restart()};for(const [id,k] of [['furina0','芙宁娜站姿·0'],['furina1','芙宁娜站姿·1'],['yae0','八重神子蹲姿·0'],['yae1','八重神子蹲姿·1']])document.querySelector('#'+id).src=DATA.refs[k]||'';show();
</script>""".replace("__PAYLOAD__", payload)
    html = html.replace('</style>', '''
    .delivery-layout{display:grid;grid-template-columns:270px minmax(0,1fr);gap:16px;align-items:start}
    #actionRows{display:flex;flex-wrap:wrap;gap:6px;background:#1d2638;padding:12px;border-radius:10px}
    #actionRows button{flex:1 1 112px;white-space:normal;text-align:left;font-size:13px;background:#29364c;color:#e5edff}
    #actionRows button[aria-pressed=true]{background:#674d91;color:#ffe2a0}
    #actionRows h2{width:100%;font-size:14px;margin:10px 0 4px;color:#aab8d4}
    @media(max-width:800px){.delivery-layout{grid-template-columns:1fr}#actionRows button{flex:1 1 130px}}
    </style>''')
    html = html.replace("<div class='bar'>", "<div class='delivery-layout'><aside id='actionRows' aria-label='选择动作'></aside><section><div class='bar'>", 1)
    html = html.replace("<div class='cards'>", "</section></div><section><h2>新制作：持械站防关键姿势</h2><p>进入格挡 → 保持 → 受力 → 恢复。身体、刀与刀鞘整体设计；当前为源图审查，切帧与拟合待完成。</p><a href='../ayaka-armed-v2/standguard-source-v1.png'>查看完整新格挡源图</a><img style='width:100%;height:auto' src='../ayaka-armed-v2/standguard-source-v1.png' alt='绫华持械格挡四姿候选'></section><div class='cards'>", 1)
    html = html.replace('../ayaka-armed-v2/standguard-source-v1.png', 'new-assets/standguard-source-v1.png')
    html = html.replace('</script>', '''
    const actionLabels={idle:'待机',walk:'前走',backwalk:'后退',crouch:'蹲下',crouchguard:'蹲防',jump:'跳跃',guard:'站立格挡',hurt_knockdown:'受击与倒地',wakeup:'起身',forwarddash:'前冲',backdash:'后撤',light1:'轻攻一',light2:'轻攻二',light3:'轻攻三',heavy:'站重',crouchlight:'蹲轻',crouchheavy:'蹲重',airlight:'空轻',airheavy:'空重',E:'E · 冰华',Q:'Q · 霜灭',throw:'投技',victim:'被投',defeat:'败北',victory:'胜利 · 待修'};
    const groups={'移动与防御':['idle','walk','backwalk','jump','forwarddash','backdash','crouch','guard','crouchguard'],'攻击':['light1','light2','light3','heavy','crouchlight','crouchheavy','airlight','airheavy'],'技能与投技':['E','Q','throw','victim'],'受击与结算':['hurt_knockdown','wakeup','defeat','victory']};
    const rows=document.querySelector('#actionRows');const choiceButtons=[];
    for(const [group,keys] of Object.entries(groups)){const h=document.createElement('h2');h.textContent=group;rows.append(h);for(const key of keys){if(!DATA.actions[key])continue;const b=document.createElement('button');b.textContent=actionLabels[key]||key;b.dataset.action=key;b.onclick=()=>{sel.value=key;sel.onchange();syncChoices()};choiceButtons.push(b);rows.append(b)}}
    function syncChoices(){for(const b of choiceButtons)b.setAttribute('aria-pressed',String(b.dataset.action===sel.value))}
    sel.closest('label').hidden=true;syncChoices();
    </script>''', 1)
    (OUT / "viewer.html").write_text(html, encoding="utf-8")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "actions").mkdir(exist_ok=True)
    actions: dict[str, list[Image.Image]] = {k: load_optimized(v) for k, v in SOURCES.items()}
    actions["light1"] = [Image.open(p).convert("RGBA") for p in sorted((ROOT / "outputs/v4-one-character-20261010/ayaka-light1-candidate/frames").glob("fit-*.png"), key=lambda p: int(p.stem.rsplit("-", 1)[1]))]
    actions["victory"] = fit_victory()

    # Existing fitted E effect is aligned as a separate layer; Q and normals use
    # clearly-labelled preview-only procedural ice effects.
    efx = load_optimized("kamisatoayaka-E-fx-review")
    action_manifest = {}
    all_frames: list[Image.Image] = []
    for name, frames in actions.items():
        ad = OUT / "actions" / name
        ad.mkdir(exist_ok=True)
        rendered = []
        for i, body in enumerate(frames):
            overlay = None
            effect = "none"
            if name == "E" and i < len(efx):
                overlay, effect = efx[i], "existing-ayaka-E-fx-candidate"
            elif name == "Q":
                overlay, effect = effect_layer("q", body.size, i, len(frames)), "preview-derived-ice-burst"
            elif name in {"light1", "light2", "light3", "heavy", "crouchlight", "crouchheavy", "airlight", "airheavy"}:
                overlay, effect = effect_layer("slash", body.size, i, len(frames)), "preview-derived-ice-slash"
            img = compose(body, overlay, name, i, len(frames))
            body.save(ad / f"body-{i:02d}.png")
            img.save(ad / f"frame-{i:02d}.png")
            rendered.append(img)
            all_frames.append(img)
        durations = [160] * len(rendered)
        (ad / "animation.json").write_text(json.dumps({
            "character": "kamisatoayaka", "actionId": f"kamisatoayaka.{name}.candidate.v1",
            "fps": 8, "loop": name in {"idle", "walk", "backwalk", "crouch", "guard", "jump"},
            "frames": [f"frame-{i:02d}.png" for i in range(len(rendered))],
            "durations_ms": durations, "world_anchor": None, "effect_layer": effect,
            "status": "preview_candidate_not_runtime_or_device",
        }, ensure_ascii=False, indent=2), encoding="utf-8")
        action_manifest[name] = {"frames": len(rendered), "effect": effect, "max_preview_size": [max(x.width for x in frames), max(x.height for x in frames)], "preview_normalization": "fixed_pixel_scale_4x_and_footline_y370"}

    # Overview: first/active/final representative for every action.
    names = list(actions)
    sheet = Image.new("RGB", (1440, math.ceil(len(names) / 3) * 360), (22, 27, 38))
    for n, name in enumerate(names):
        frames = [Image.open(p).convert("RGB") for p in sorted((OUT / "actions" / name).glob("frame-*.png"))]
        img = frames[min(len(frames) - 1, len(frames) // 2)]
        sheet.paste(img, ((n % 3) * 480, (n // 3) * 360))
    sheet.save(OUT / "overview.png")
    all_frames[0].save(OUT / "all-actions-preview.gif", save_all=True, append_images=all_frames[1:], duration=[120] * len(all_frames), loop=0)
    write_viewer(action_manifest)
    (OUT / "manifest.json").write_text(json.dumps({
        "character": "kamisatoayaka", "status": "complete_visual_candidate_review_only",
        "actions": action_manifest, "action_count": len(action_manifest), "frame_count": sum(x["frames"] for x in action_manifest.values()),
        "evidence_boundary": ["fitted PNG frame exports and CPU-side GIF/PNG assembly", "not simulator combat, game import, or real-device validation"],
        "open_items": ["world anchors", "weapon separation", "hitboxes/cancel timing", "Q effect user review", "real runtime integration"],
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    (OUT / "README.md").write_text("# 绫华全动作拟合帧动画候选\n\n已汇总现有身体候选并生成逐动作帧PNG、animation.json、总览图和播放GIF。E使用现有冰特效候选；普通斩击与Q为预览性冰效层。脚底/世界锚点、命中逻辑、取消窗口和真机兼容仍未验收。\n", encoding="utf-8")
    print(json.dumps({"output": str(OUT.relative_to(ROOT)), "actions": len(action_manifest), "frames": sum(x["frames"] for x in action_manifest.values())}, ensure_ascii=False))


if __name__ == "__main__":
    main()
