"""字体扫描、选择、样式增强、UI 字体查找"""

import glob
import os
import sys
from typing import List, Tuple

try:
    from PIL import Image, ImageDraw, ImageFont
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


def get_font_dirs() -> List[str]:
    dirs = []
    if sys.platform == "win32":
        windir = os.environ.get("WINDIR", "C:/Windows")
        dirs.append(os.path.join(windir, "Fonts"))
        la = os.environ.get("LOCALAPPDATA", "")
        if la:
            dirs.append(os.path.join(la, "Microsoft", "Windows", "Fonts"))
        for pf in [os.environ.get("PROGRAMFILES", "C:/Program Files"),
                   os.environ.get("PROGRAMFILES(X86)",
                                  "C:/Program Files (x86)")]:
            if pf:
                dirs.append(os.path.join(pf, "Common Files", "Fonts"))
    elif sys.platform == "darwin":
        dirs.extend(["/System/Library/Fonts", "/Library/Fonts",
                     os.path.expanduser("~/Library/Fonts")])
    else:
        dirs.extend(["/usr/share/fonts", "/usr/local/share/fonts",
                     os.path.expanduser("~/.fonts")])
    return [d for d in dirs if os.path.isdir(d)]


_font_cache: List[Tuple[str, str]] | None = None


def scan_fonts() -> List[Tuple[str, str]]:
    global _font_cache
    if _font_cache is not None:
        return _font_cache
    fonts = []
    seen = set()
    for fd in get_font_dirs():
        for pat in ("*.ttf", "*.ttc", "*.otf", "*.TTF", "*.TTC", "*.OTF"):
            for fp in glob.glob(os.path.join(fd, "**", pat), recursive=True):
                name = os.path.splitext(os.path.basename(fp))[0]
                if name.lower() not in seen:
                    seen.add(name.lower())
                    fonts.append((name, fp))
    cn_kw = ["song", "hei", "kai", "ming", "fang", "yuan", "sim", "msyh",
             "deng", "fz", "st", "harmony", "hany", "noto"]
    fonts.sort(key=lambda x: (
        not any(k in x[0].lower() for k in cn_kw),
        x[0].lower(),
    ))
    _font_cache = fonts
    return fonts


def find_ui_font() -> str:
    """查找 HarmonyOS Sans SC Bold 用于界面控件，找不到返回第一个可用字体"""
    from config import DEFAULT_UI_FONT, DEFAULT_UI_FONT_FALLBACKS
    all_f = scan_fonts()
    for target in [DEFAULT_UI_FONT] + DEFAULT_UI_FONT_FALLBACKS:
        tl = target.lower()
        for name, path in all_f:
            if tl == name.lower():
                return path
        for name, path in all_f:
            if tl in name.lower():
                return path
    if all_f:
        return all_f[0][1]
    return ""


def pick_font(pref: str | None, all_f: List[Tuple[str, str]]) -> str:
    if not all_f:
        raise RuntimeError("未找到任何字体")
    if pref is None:
        return all_f[0][1]
    if os.path.exists(pref):
        return pref
    pl = pref.lower()
    for n, p in all_f:
        if pl == n.lower():
            return p
    for n, p in all_f:
        if pl in n.lower():
            return p
    for n, p in all_f:
        if any(kw in n.lower() for kw in pl.split()):
            return p
    return all_f[0][1]


# ── 粗/斜体变体检测 ──

def _detect_variant(font_path: str, suffixes: List[str]) -> str | None:
    base = os.path.splitext(font_path)[0]
    for sfx in suffixes:
        for c in [base + sfx + ".ttf", base + sfx + ".otf",
                  base + sfx + ".TTF", base + sfx + ".OTF",
                  base.replace("Regular", sfx) + ".ttf",
                  base.replace("-Regular", "-" + sfx) + ".ttf"]:
            if os.path.exists(c):
                return c
    return None


def apply_italic(mask: Image.Image) -> Image.Image:
    w, h = mask.size
    shear = 0.25
    new_w = int(w + h * shear)
    result = Image.new("L", (new_w, h), 0)
    px_src = mask.load()
    px_dst = result.load()
    for y in range(h):
        offset = int(y * shear)
        for x in range(w):
            if px_src[x, y] > 0:
                dst_x = x + offset
                if 0 <= dst_x < new_w:
                    px_dst[dst_x, y] = px_src[x, y]
    return result


def render_text_mask(text: str, font_path: str, style: int,
                     hires_h: int, hires_w: int) -> Image.Image:
    """style: 0=normal, 1=bold, 2=italic, 3=bold+italic"""
    if style == 1:
        bf = _detect_variant(font_path,
                             ["b", "bd", "bold", "B", "Bd", "Bold"])
        if bf:
            font_path, style = bf, 0
    elif style == 2:
        it = _detect_variant(font_path,
                             ["i", "it", "italic", "I", "It", "Italic"])
        if it:
            font_path, style = it, 0
    elif style == 3:
        bi = _detect_variant(
            font_path, ["bi", "z", "BoldItalic", "bolditalic"])
        if bi:
            font_path, style = bi, 0

    mask = Image.new("L", (hires_w, hires_h), 0)
    draw = ImageDraw.Draw(mask)
    font = ImageFont.truetype(font_path, int(hires_h * 0.85))

    lines = text.split("\n")
    total_h = len(lines) * int(hires_h * 0.95)
    for li, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        tw = bbox[2] - bbox[0]
        y_off = li * int(hires_h * 0.95) + (hires_h - total_h) // 2
        draw.text(((hires_w - tw) // 2 - bbox[0], y_off),
                  line, fill=255, font=font)

    if style == 1 or style == 3:
        mask2 = Image.new("L", (hires_w, hires_h), 0)
        draw2 = ImageDraw.Draw(mask2)
        for li, line in enumerate(lines):
            bbox = draw2.textbbox((0, 0), line, font=font)
            tw = bbox[2] - bbox[0]
            y_off = li * int(hires_h * 0.95) + (hires_h - total_h) // 2
            for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                draw2.text(((hires_w - tw) // 2 - bbox[0] + dx,
                            y_off + dy), line, fill=255, font=font)
        px1, px2 = mask.load(), mask2.load()
        for y in range(hires_h):
            for x in range(hires_w):
                if px2[x, y] > 0:
                    px1[x, y] = 255

    if style == 2 or style == 3:
        mask = apply_italic(mask)

    return mask
