"""PIL 渲染核心：点阵生成 + 后处理"""

import os
import re
from config import BASE_ROWS, SCALE_MAX, SCALE_MIN, SCALE_STEP
from font_utils import render_text_mask
from PIL import Image


def _post_process(raw: str) -> bytes:
    def _repl(m):
        v = len(m.group()) * 0.2
        s = f"{v:.1f}"
        return f"<space={s[:-2] if s.endswith('.0') else s}>"
    raw = re.sub(r' {12,}', _repl, raw)
    raw = re.sub(r'\s*<br>', '<br>', raw)
    return raw.rstrip().encode("utf-8")


def _mask_to_bytes(mask: Image.Image) -> bytes:
    px = mask.load()
    w, h = mask.width, mask.height
    parts = []
    for y in range(h):
        line = bytearray()
        for x in range(w):
            line.append(ord(".") if px[x, y] >= 128 else ord(" "))
        stripped = bytes(line).rstrip(b" ")
        parts.append(stripped + b"<br>" if stripped else b"<br>")
    return _post_process(b"".join(parts).decode("ascii", errors="replace"))


def _render_one(text: str, scale: float, font_path: str,
                vertical: bool, style: int) -> bytes:
    hires_h = BASE_ROWS * 4
    hires_w = hires_h * 2 if not vertical else hires_h
    if vertical:
        return _render_vertical(text, scale, font_path, style)

    mask = render_text_mask(text, font_path, style, hires_h, hires_w)
    px = mask.load()
    top = next((r for r in range(hires_h)
                if any(px[c, r] > 0 for c in range(hires_w))), 0)
    bot = next((r for r in range(hires_h - 1, -1, -1)
                if any(px[c, r] > 0 for c in range(hires_w))), hires_h - 1)
    left = next((c for c in range(hires_w)
                 if any(px[c, r] > 0 for r in range(hires_h))), 0)
    right = next((c for c in range(hires_w - 1, -1, -1)
                  if any(px[c, r] > 0 for r in range(hires_h))), hires_w - 1)
    if bot <= top or right <= left:
        return b""
    char_h, char_w = bot - top + 1, right - left + 1
    crop = mask.crop((left, top, right + 1, bot + 1))
    tr = max(int(BASE_ROWS * scale), 5)
    tc = max(int(tr * char_w / char_h), 5)
    return _mask_to_bytes(crop.resize((tc, tr), Image.NEAREST))


def _render_vertical(text: str, scale: float, font_path: str, style: int) -> bytes:
    chars = list(text.replace("\n", ""))
    if not chars:
        return b""
    base_rc = BASE_ROWS // max(len(chars), 1)
    blocks, max_w = [], 0
    for ch in chars:
        hires = base_rc * 6
        mask = render_text_mask(ch, font_path, style, hires, hires)
        px = mask.load()
        top = next((r for r in range(hires)
                    if any(px[c, r] > 0 for c in range(hires))), 0)
        bot = next((r for r in range(hires - 1, -1, -1)
                    if any(px[c, r] > 0 for c in range(hires))), hires - 1)
        left = next((c for c in range(hires)
                     if any(px[c, r] > 0 for r in range(hires))), 0)
        right = next((c for c in range(hires - 1, -1, -1)
                      if any(px[c, r] > 0 for r in range(hires))), hires - 1)
        if bot <= top or right <= left:
            blocks.append(None)
            continue
        crop = mask.crop((left, top, right + 1, bot + 1))
        ch_h, ch_w = bot - top + 1, right - left + 1
        th_v = max(int(base_rc * scale), 3)
        tw_v = max(int(th_v * ch_w / ch_h), 3)
        blocks.append(crop.resize((tw_v, th_v), Image.NEAREST))
        if tw_v > max_w:
            max_w = tw_v
    if not blocks or all(b is None for b in blocks):
        return b""
    parts = []
    for block in blocks:
        if block is None:
            continue
        px = block.load()
        bw, bh = block.width, block.height
        lp = (max_w - bw) // 2
        rp = max_w - bw - lp
        for y in range(bh):
            line = bytearray(b" " * lp)
            for x in range(bw):
                line.append(ord(".") if px[x, y] >= 128 else ord(" "))
            line.extend(b" " * rp)
            stripped = bytes(line).rstrip(b" ")
            parts.append(stripped + b"<br>" if stripped else b"<br>")
    return _post_process(b"".join(parts).decode("ascii", errors="replace"))


def find_scale(text: str, font_path: str, max_bytes: int,
               vertical: bool, style: int, callback=None) -> float:
    b = len(_render_one(text, SCALE_MAX, font_path, vertical, style))
    if callback:
        callback(f"scale=1.00 → {b}B")
    if b <= max_bytes:
        return SCALE_MAX
    b = len(_render_one(text, SCALE_MIN, font_path, vertical, style))
    if callback:
        callback(f"scale={SCALE_MIN:.2f} → {b}B")
    if b > max_bytes:
        return SCALE_MIN
    lo, hi, best = SCALE_MIN, SCALE_MAX, SCALE_MIN
    for _ in range(12):
        if hi - lo < SCALE_STEP:
            break
        mid = (lo + hi) / 2
        b = len(_render_one(text, mid, font_path, vertical, style))
        if callback:
            callback(f"scale={mid:.3f} → {b}B")
        if b <= max_bytes:
            best, lo = mid, mid
        else:
            hi = mid
    return best


def generate(text: str, font_choice: str, max_bytes: int,
             vertical: bool, style: int = 0, callback=None) -> str:
    from font_utils import scan_fonts, pick_font
    if len(text) > 80:
        text = text[:80]
    if not text:
        return ""
    all_f = scan_fonts()
    fp = pick_font(font_choice if font_choice else None, all_f)
    if callback:
        callback(f"字体: {os.path.basename(fp)}")
    scale = find_scale(text, fp, max_bytes, vertical, style, callback)
    body = _render_one(text, scale, fp, vertical, style)
    result = b"<mspace=0.2><line-height=0.2><size=0.65>" + body
    if len(result) > max_bytes:
        result = result[:max_bytes]
        while True:
            try:
                result.decode("utf-8")
                break
            except UnicodeDecodeError:
                result = result[:-1]
        s = result.decode("utf-8")
        lb = s.rfind("<br>")
        if lb > 0:
            s = s[:lb + 4]
        return s
    return result.decode("utf-8")
