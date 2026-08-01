"""PIL 渲染核心：点阵生成 + 后处理 — v2.2

v2.2 改动：
  - 裁剪阈值恢复为 > 0（原始行为）
  - 二值化阈值恢复为 >= 128（原始行为）
  - 移除 v2.1 的腐蚀，避免误删笔画细线
  - 保留 v2.0 单趟流式 + 颜色标签
"""

import os
from config import BASE_ROWS, SCALE_MAX, SCALE_MIN, SCALE_STEP
from font_utils import render_text_mask
from PIL import Image


# ── JNO Label 25 槽位标识符（与 JS 版 colorIdList 完全一致）──

COLOR_ID_LIST = [
    '#000000', '#010101', '#020202', '#030303', '#040404',
    '#050505', '#060606', '#070707', '#080808', '#090909',
    '#0A0A0A', '#0B0B0B', '#0C0C0C', '#0D0D0D', '#0E0E0E',
    '#0F0F0F', '#101010', '#111111', '#121212', '#131313',
    '#141414', '#151515', '#161616', '#171717', '#181818',
]

SPACE_RLE_THRESHOLD = 8


# ═══════════════════════════════════════════════════════════════
#  核心：单趟 mask → JNO 字符串
# ═══════════════════════════════════════════════════════════════

def _mask_to_string(mask: Image.Image, color_hex: str | None = None) -> str:
    """单趟流式：像素遍历 + 行边界 + 空格游程编码 + 颜色标签。"""
    px = mask.load()
    w, h = mask.width, mask.height
    buf = []
    space_run = 0
    color_emitted = color_hex is None

    for y in range(h):
        for x in range(w):
            is_dot = px[x, y] >= 128
            if is_dot:
                if not color_emitted:
                    buf.append(f"<{color_hex}>")
                    color_emitted = True
                if space_run >= SPACE_RLE_THRESHOLD:
                    v = space_run * 0.2
                    s = f"{v:.1f}"
                    buf.append(
                        f"<space={s[:-2] if s.endswith('.0') else s}>"
                    )
                elif space_run > 0:
                    buf.append(" " * space_run)
                space_run = 0
                buf.append(".")
            else:
                space_run += 1
        space_run = 0
        buf.append("<br>")

    return "".join(buf).rstrip()


# ═══════════════════════════════════════════════════════════════
#  横排
# ═══════════════════════════════════════════════════════════════

def _render_horizontal(text: str, scale: float, font_path: str,
                       style: int, color_hex: str | None) -> str:
    hires_h = BASE_ROWS * 4
    hires_w = hires_h * 2

    mask = render_text_mask(text, font_path, style, hires_h, hires_w)
    px = mask.load()

    # 裁剪：使用 > 0（与原始版本一致）
    top = next((r for r in range(hires_h)
                if any(px[c, r] > 0 for c in range(hires_w))), 0)
    bot = next((r for r in range(hires_h - 1, -1, -1)
                if any(px[c, r] > 0 for c in range(hires_w))), hires_h - 1)
    left = next((c for c in range(hires_w)
                 if any(px[c, r] > 0 for r in range(hires_h))), 0)
    right = next((c for c in range(hires_w - 1, -1, -1)
                  if any(px[c, r] > 0 for r in range(hires_h))), hires_w - 1)

    if bot <= top or right <= left:
        return ""

    crop = mask.crop((left, top, right + 1, bot + 1))
    char_h = bot - top + 1
    char_w = right - left + 1

    tr = max(int(BASE_ROWS * scale), 5)
    tc = max(int(tr * char_w / char_h), 5)

    return _mask_to_string(crop.resize((tc, tr), Image.NEAREST), color_hex)


# ═══════════════════════════════════════════════════════════════
#  竖排
# ═══════════════════════════════════════════════════════════════

def _render_vertical(text: str, scale: float, font_path: str,
                     style: int, color_hex: str | None) -> str:
    chars = list(text.replace("\n", ""))
    if not chars:
        return ""

    base_rc = BASE_ROWS // max(len(chars), 1)
    blocks = []
    max_w = 0

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
        ch_h = bot - top + 1
        ch_w = right - left + 1
        th_v = max(int(base_rc * scale), 3)
        tw_v = max(int(th_v * ch_w / ch_h), 3)
        blocks.append(crop.resize((tw_v, th_v), Image.NEAREST))
        if tw_v > max_w:
            max_w = tw_v

    if not blocks or all(b is None for b in blocks):
        return ""

    total_h = sum(b.height for b in blocks if b is not None)
    combined = Image.new("L", (max_w, total_h), 0)

    y_off = 0
    for block in blocks:
        if block is None:
            continue
        x_off = (max_w - block.width) // 2
        combined.paste(block, (x_off, y_off))
        y_off += block.height

    return _mask_to_string(combined, color_hex)


# ═══════════════════════════════════════════════════════════════
#  统一入口
# ═══════════════════════════════════════════════════════════════

def _render_one(text: str, scale: float, font_path: str,
                vertical: bool, style: int, color_hex: str | None) -> str:
    if vertical:
        return _render_vertical(text, scale, font_path, style, color_hex)
    return _render_horizontal(text, scale, font_path, style, color_hex)


# ═══════════════════════════════════════════════════════════════
#  二分查找
# ═══════════════════════════════════════════════════════════════

def find_scale(text: str, font_path: str, max_bytes: int,
               vertical: bool, style: int,
               color_hex: str | None = None,
               callback=None) -> float:

    def _size(s: float) -> int:
        return len(_render_one(
            text, s, font_path, vertical, style, color_hex
        ).encode("utf-8"))

    b = _size(SCALE_MAX)
    if callback:
        callback(f"scale=1.00 → {b}B")
    if b <= max_bytes:
        return SCALE_MAX

    b = _size(SCALE_MIN)
    if callback:
        callback(f"scale={SCALE_MIN:.2f} → {b}B")
    if b > max_bytes:
        return SCALE_MIN

    lo, hi, best = SCALE_MIN, SCALE_MAX, SCALE_MIN
    for _ in range(12):
        if hi - lo < SCALE_STEP:
            break
        mid = (lo + hi) / 2
        b = _size(mid)
        if callback:
            callback(f"scale={mid:.3f} → {b}B")
        if b <= max_bytes:
            best = mid
            lo = mid
        else:
            hi = mid
    return best


# ═══════════════════════════════════════════════════════════════
#  主入口
# ═══════════════════════════════════════════════════════════════

def generate(text: str, font_choice: str, max_bytes: int,
             vertical: bool, style: int = 0,
             color_hex: str | None = None,
             callback=None) -> str:
    from font_utils import scan_fonts, pick_font

    if len(text) > 80:
        text = text[:80]
    if not text:
        return ""

    all_f = scan_fonts()
    fp = pick_font(font_choice if font_choice else None, all_f)
    if callback:
        callback(f"字体: {os.path.basename(fp)}")

    scale = find_scale(text, fp, max_bytes, vertical, style,
                       color_hex, callback)
    body = _render_one(text, scale, fp, vertical, style, color_hex)

    prefix = "<mspace=0.2><line-height=0.2><size=0.65>"
    result = prefix + body

    if len(result.encode("utf-8")) > max_bytes:
        result_bytes = result.encode("utf-8")[:max_bytes]
        while True:
            try:
                result = result_bytes.decode("utf-8")
                break
            except UnicodeDecodeError:
                result_bytes = result_bytes[:-1]
        lb = result.rfind("<br>")
        if lb > 0:
            result = result[:lb + 4]

    return result

