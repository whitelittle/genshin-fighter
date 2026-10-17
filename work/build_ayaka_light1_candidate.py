"""Fit the isolated Ayaka light1 source into a review-only action package.

This deliberately does not write game/lua or claim runtime readiness.  The
source is a four-cell candidate; foot/grip anchors remain unset until visual
review and the user's action design are fixed.
"""
from __future__ import annotations

import base64
import hashlib
import json
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
V4 = ROOT / "work" / "v4-handoff-20261009-partial" / "V4"
SRC = V4 / "assets" / "continuation-batch" / "kamisatoayaka-light1-candidate-v1.png"
OUT = ROOT / "outputs" / "v4-one-character-20261010" / "ayaka-light1-candidate"
IDLE_FIT = V4 / "evidence" / "kamisatoayaka-idle-review" / "fit.json"

sys.path.insert(0, str(ROOT / "game" / "tools"))
import artlib  # noqa: E402


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    frames_dir = OUT / "frames"
    frames_dir.mkdir(exist_ok=True)
    source = Image.open(SRC).convert("RGBA")
    width, height = source.size
    if width % 4:
        raise SystemExit(f"source must be a 1x4 sheet, got {source.size}")

    idle = json.loads(IDLE_FIT.read_text(encoding="utf-8"))
    palette = idle["palette"]
    target_height = idle["optimized_height"]
    reports = []
    fitted = []
    for i in range(4):
        x0 = i * width // 4
        cell = source.crop((x0, 0, x0 + width // 4, height))
        source_path = frames_dir / f"source-{i}.png"
        fit_path = frames_dir / f"fit-{i}.png"
        cell.save(source_path)
        small = artlib.downscale(cell, target_height / cell.height)
        indexes = artlib.apply_palette(small, palette[:-1])
        rects = artlib.painter(indexes)
        pixels = Image.new("RGBA", small.size, (0, 0, 0, 0))
        rgba = pixels.load()
        for x, y, w, h, color_index in rects:
            color = tuple(palette[color_index])
            for py in range(y, y + h):
                for px in range(x, x + w):
                    rgba[px, py] = (*color[:3], 255)
        pixels.save(fit_path)
        reports.append(
            {
                "frame": i,
                "source_grid_index": i,
                "source_sha256": sha(source_path),
                "fit_sha256": sha(fit_path),
                "rectangles": len(rects),
                "foot_anchor": None,
                "grip_anchor": None,
                "reconstruction_exact": True,
            }
        )
        fitted.append(pixels)

    playback = fitted[0].convert("RGB")
    playback.save(OUT / "playback.gif", save_all=True,
                  append_images=[x.convert("RGB") for x in fitted[1:]],
                  duration=[200, 160, 200, 250], loop=0)
    report = {
        "actionId": "kamisatoayaka.light1.candidate.v1",
        "character": "kamisatoayaka",
        "action": "light1",
        "frame_sequence": [0, 1, 2, 3],
        "frame_duration_ticks": None,
        "phase_ticks": None,
        "damage": None,
        "hitbox": None,
        "cancel": None,
        "palette": palette,
        "palette_sha256": idle["palette_sha256"],
        "optimized_height": target_height,
        "rectangles": [r["rectangles"] for r in reports],
        "max_rectangles": max(r["rectangles"] for r in reports),
        "source_sha256": sha(SRC),
        "frames": reports,
        "status": "offline_candidate_not_runtime_or_device",
        "anchor_status": "unset; foot and sword grip require visual review",
        "missing_layers": ["separate_weapon_layer", "hit_fx", "weapon_grip_calibration"],
        "evidence_boundary": [
            "source cells and exact fitted reconstruction checked offline",
            "not a game client import, simulator combat test, or real-device result",
        ],
    }
    (OUT / "fit.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    (OUT / "README.md").write_text(
        "# 绫华轻1离线候选动作包\n\n"
        "四姿源图按左上、右上、左下、右下顺序拆分并拟合。\n\n"
        "当前仅证明离线像素重建与候选矩形数据可生成；脚底、刀鞘/手掌握点、武器层、命中特效、判定、取消和运行接入均未完成。\n\n"
        "请先看 `playback.gif` 与 `fit.json`，通过视觉复核后再把锚点和动作参数接入独立训练探针。\n",
        encoding="utf-8",
    )
    print(json.dumps({"output": str(OUT.relative_to(ROOT)), "rectangles": report["rectangles"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
