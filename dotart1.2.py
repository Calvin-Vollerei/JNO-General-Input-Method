"""
JNO通用输入法 v1.2
- 修复: 字体管理弹窗滚轮报错 (invalid command name)
- 修复: ttk.Frame 不支持 -bg cget 报错
- 修复: 勾选标记确保显示 √
- 修复: 弹窗关闭时清理事件绑定
打包: pyinstaller --onefile --windowed --name "JNO通用输入法" --hidden-import PIL --hidden-import PIL.Image --hidden-import PIL.ImageDraw --hidden-import PIL.ImageFont dotart_gui.py
"""

from __future__ import annotations

import glob
import json
import os
import re
import sys
import threading
import webbrowser
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from typing import Dict, List, Tuple, Set

try:
    from PIL import Image, ImageDraw, ImageFont
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

# ═══════════════════════ 配置持久化 ═══════════════════════

def _config_dir() -> str:
    d = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")),
                     "JNO-Input-Method")
    os.makedirs(d, exist_ok=True)
    return d

def _config_path() -> str:
    return os.path.join(_config_dir(), "settings.json")

def _load_config() -> dict:
    path = _config_path()
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def _save_config(cfg: dict):
    with open(_config_path(), "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)

# ═══════════════════════ 国际化 ═══════════════════════

TEXTS = {
    "zh": {
        "title": "JNO通用输入法",
        "input_label": "输入文本:",
        "font_label": "字体:",
        "font_auto": "（自动选择）",
        "font_recent": "── 最近使用 ──",
        "font_all": "── 全部字体 ──",
        "vertical": "竖排",
        "byte_limit": "字节上限:",
        "style": "样式:",
        "style_normal": "常规",
        "style_bold": "加粗",
        "style_italic": "斜体",
        "style_bold_italic": "粗斜体",
        "newline_hint": "（Enter 换行，Ctrl+Enter 生成）",
        "generate": "生成",
        "generating": "生成中...",
        "ready": "就绪",
        "copy": "复制到剪贴板",
        "save": "保存到文件",
        "clear": "清空",
        "copied": "已复制到剪贴板",
        "saved": "已保存: {}",
        "cleared": "已清空",
        "no_content": "没有内容可{}",
        "input_warning": "请输入文本",
        "error": "错误",
        "missing_pillow": "请先安装 pillow:\npip install pillow",
        "settings": "设置",
        "language": "语言",
        "theme": "主题",
        "theme_light": "浅色",
        "theme_dark": "深色",
        "font_manager": "字体管理",
        "font_manager_title": "字体管理",
        "font_enable_all": "全选",
        "font_disable_all": "全不选",
        "font_filter": "搜索字体...",
        "font_count": "已启用 {}/{} 个字体",
        "font_applied": "修改已应用",
        "font_unsaved": "有未保存的修改。\n\n是否放弃修改并关闭？",
        "about": "关于",
        "about_title": "关于 JNO通用输入法",
        "about_text": (
            "JNO通用输入法 v1.2\n\n"
            "将文字转换为适用于JNO Lable的形式\n基于 PIL 渲染 + 最近邻降采样\n支持全 Windows 字体库\n\nCalvin Vollerei Studio All rights Reserved（2022-2026）\n"
        ),
        "github": "GitHub",
        "bilibili": "B站主页",
        "copyright": "Calvin Vollerei Studio 2022-2026 All Rights Reserved.",
        "done": "完成 — {}行, {}B",
        "fonts_total": "共 {} 个字体",
    },
    "en": {
        "title": "JNO Input Method",
        "input_label": "Input Text:",
        "font_label": "Font:",
        "font_auto": "(Auto Select)",
        "font_recent": "── Recent ──",
        "font_all": "── All Fonts ──",
        "vertical": "Vertical",
        "byte_limit": "Byte Limit:",
        "style": "Style:",
        "style_normal": "Normal",
        "style_bold": "Bold",
        "style_italic": "Italic",
        "style_bold_italic": "Bold Italic",
        "newline_hint": "(Enter for newline, Ctrl+Enter to generate)",
        "generate": "Generate",
        "generating": "Generating...",
        "ready": "Ready",
        "copy": "Copy to Clipboard",
        "save": "Save to File",
        "clear": "Clear",
        "copied": "Copied to clipboard",
        "saved": "Saved: {}",
        "cleared": "Cleared",
        "no_content": "No content to {}",
        "input_warning": "Please enter text",
        "error": "Error",
        "missing_pillow": "Please install pillow:\npip install pillow",
        "settings": "Settings",
        "language": "Language",
        "theme": "Theme",
        "theme_light": "Light",
        "theme_dark": "Dark",
        "font_manager": "Font Manager",
        "font_manager_title": "Font Manager",
        "font_enable_all": "Select All",
        "font_disable_all": "Deselect All",
        "font_filter": "Search fonts...",
        "font_count": "Enabled {}/{} fonts",
        "font_applied": "Changes applied",
        "font_unsaved": "Unsaved changes.\n\nDiscard and close?",
        "about": "About",
        "about_title": "About JNO Input Method",
        "about_text": (
            "JNO Input Method v1.2\n\n"
            "Convert text to JNO Label format.\n"
            "Based on PIL + nearest-neighbor,\n"
            "Full Windows font library.\n\n"
            "Calvin Vollerei Studio\n"
            "All rights Reserved (2022-2026)"
        ),
        "github": "GitHub",
        "bilibili": "Bilibili",
        "copyright": "Calvin Vollerei Studio 2022-2026 All Rights Reserved.",
        "done": "Done — {} lines, {}B",
        "fonts_total": "Total {} fonts",
    },
}

# ═══════════════════════ 配置 ═══════════════════════

MAX_BYTES = 30000
BASE_ROWS = 240
SCALE_MAX = 1.0
SCALE_MIN = 0.10
SCALE_STEP = 0.02
MAX_CHARS_IN = 80
MAX_RECENT_FONTS = 10

AUTHOR_GITHUB = "https://github.com/Calvin-Vollerei"
AUTHOR_BILIBILI = "https://space.bilibili.com/400975747"

# ═══════════════════════ 主题 ═══════════════════════

LIGHT_THEME = {
    "bg": "#f0f0f0", "fg": "#333333",
    "result_bg": "#ffffff", "result_fg": "#333333",
    "entry_bg": "#ffffff", "entry_fg": "#000000",
    "status_bg": "#e0e0e0", "status_fg": "#555555",
    "btn_bg": "#e0e0e0", "btn_fg": "#000000",
    "list_bg": "#ffffff", "list_fg": "#000000",
    "sep_fg": "#aaaaaa",
}

DARK_THEME = {
    "bg": "#1e1e1e", "fg": "#cccccc",
    "result_bg": "#252525", "result_fg": "#dddddd",
    "entry_bg": "#2d2d2d", "entry_fg": "#ffffff",
    "status_bg": "#333333", "status_fg": "#aaaaaa",
    "btn_bg": "#3a3a3a", "btn_fg": "#dddddd",
    "list_bg": "#2d2d2d", "list_fg": "#dddddd",
    "sep_fg": "#666666",
}

# ═══════════════════════ 字体扫描 ═══════════════════════

def _get_font_dirs() -> List[str]:
    dirs = []
    if sys.platform == "win32":
        windir = os.environ.get("WINDIR", "C:/Windows")
        dirs.append(os.path.join(windir, "Fonts"))
        la = os.environ.get("LOCALAPPDATA", "")
        if la:
            dirs.append(os.path.join(la, "Microsoft", "Windows", "Fonts"))
        for pf in [os.environ.get("PROGRAMFILES", "C:/Program Files"),
                   os.environ.get("PROGRAMFILES(X86)", "C:/Program Files (x86)")]:
            if pf:
                dirs.append(os.path.join(pf, "Common Files", "Fonts"))
    elif sys.platform == "darwin":
        dirs.extend(["/System/Library/Fonts", "/Library/Fonts",
                     os.path.expanduser("~/Library/Fonts")])
    else:
        dirs.extend(["/usr/share/fonts", "/usr/local/share/fonts",
                     os.path.expanduser("~/.fonts")])
    return [d for d in dirs if os.path.isdir(d)]


def _scan_fonts() -> List[Tuple[str, str]]:
    fonts = []
    seen = set()
    for fd in _get_font_dirs():
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
    return fonts


def _pick_font(pref: str | None, all_f: List[Tuple[str, str]]) -> str:
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


# ═══════════════════════ 样式增强 ═══════════════════════

def _apply_italic(mask: Image.Image) -> Image.Image:
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


def _render_text_mask(text: str, font_path: str, style: int,
                       hires_h: int, hires_w: int) -> Image.Image:
    if style == 1:
        bf = _detect_variant(font_path, ["b", "bd", "bold", "B", "Bd", "Bold"])
        if bf:
            font_path, style = bf, 0
    elif style == 2:
        it = _detect_variant(font_path, ["i", "it", "italic", "I", "It", "Italic"])
        if it:
            font_path, style = it, 0
    elif style == 3:
        bi = _detect_variant(font_path, ["bi", "z", "BoldItalic", "bolditalic"])
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
        mask = _apply_italic(mask)
    return mask


# ═══════════════════════ 后处理 ═══════════════════════

def _post_process(raw: str) -> bytes:
    def _repl(m):
        v = len(m.group()) * 0.2
        s = f"{v:.1f}"
        return f"<space={s[:-2] if s.endswith('.0') else s}>"
    raw = re.sub(r' {12,}', _repl, raw)
    raw = re.sub(r'\s*<br>', '<br>', raw)
    return raw.rstrip().encode("utf-8")


def _scan_to_bytes(mask: Image.Image) -> bytes:
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


# ═══════════════════════ 渲染 ═══════════════════════

def _render_horizontal(text: str, scale: float, font_path: str,
                        style: int) -> bytes:
    hires_h = BASE_ROWS * 4
    hires_w = hires_h * 2
    mask = _render_text_mask(text, font_path, style, hires_h, hires_w)
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
    return _scan_to_bytes(crop.resize((tc, tr), Image.NEAREST))


def _render_vertical(text: str, scale: float, font_path: str,
                      style: int) -> bytes:
    chars = list(text.replace("\n", ""))
    if not chars:
        return b""
    base_rc = BASE_ROWS // max(len(chars), 1)
    blocks, max_w = [], 0
    for ch in chars:
        hires = base_rc * 6
        mask = _render_text_mask(ch, font_path, style, hires, hires)
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


def _render(text: str, scale: float, font_path: str, vertical: bool,
            style: int) -> bytes:
    return _render_vertical(text, scale, font_path, style) if vertical else \
           _render_horizontal(text, scale, font_path, style)


def _find_scale(text: str, font_path: str, max_bytes: int,
                vertical: bool, style: int, callback=None) -> float:
    b = len(_render(text, SCALE_MAX, font_path, vertical, style))
    if callback:
        callback("scale=1.00 → {}B".format(b))
    if b <= max_bytes:
        return SCALE_MAX
    b = len(_render(text, SCALE_MIN, font_path, vertical, style))
    if callback:
        callback("scale={:.2f} → {}B".format(SCALE_MIN, b))
    if b > max_bytes:
        return SCALE_MIN
    lo, hi, best = SCALE_MIN, SCALE_MAX, SCALE_MIN
    for _ in range(12):
        if hi - lo < SCALE_STEP:
            break
        mid = (lo + hi) / 2
        b = len(_render(text, mid, font_path, vertical, style))
        if callback:
            callback("scale={:.3f} → {}B".format(mid, b))
        if b <= max_bytes:
            best, lo = mid, mid
        else:
            hi = mid
    return best


def generate(text: str, font_choice: str, max_bytes: int,
             vertical: bool, style: int = 0, callback=None) -> str:
    if not HAS_PIL:
        raise RuntimeError("请安装 pillow")
    if len(text) > MAX_CHARS_IN:
        text = text[:MAX_CHARS_IN]
    if not text:
        return ""
    all_f = _scan_fonts()
    fp = _pick_font(font_choice if font_choice else None, all_f)
    if callback:
        callback("字体: {}".format(os.path.basename(fp)))
    scale = _find_scale(text, fp, max_bytes, vertical, style, callback)
    body = _render(text, scale, fp, vertical, style)
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


# ═══════════════════════ GUI ═══════════════════════

class FontManagerDialog(tk.Toplevel):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.t = app.t
        self.title(self.t("font_manager_title"))
        self.geometry("480x540")
        self.resizable(True, True)
        self.transient(parent)
        self.grab_set()

        self._all_fonts = app.all_fonts
        self._disabled = app.disabled_fonts
        self._original_disabled = set(app.disabled_fonts)
        self._check_vars: Dict[str, tk.BooleanVar] = {}
        self._canvas = None
        self._mw_self_bind = None
        self._mw_canvas_bind = None

        self._build()
        self._center(parent)
        self.protocol("WM_DELETE_WINDOW", self._on_window_close)

    def _bg_color(self) -> str:
        """获取列表背景色"""
        theme = DARK_THEME if self.app.dark_theme else LIGHT_THEME
        return theme["list_bg"]

    def _fg_color(self) -> str:
        theme = DARK_THEME if self.app.dark_theme else LIGHT_THEME
        return theme["list_fg"]

    def _build(self):
        top = ttk.Frame(self, padding=8)
        top.pack(fill=tk.X)

        self._filter_var = tk.StringVar()
        filter_entry = ttk.Entry(top, textvariable=self._filter_var, font=("", 10))
        filter_entry.pack(fill=tk.X, side=tk.LEFT, expand=True, padx=(0, 5))
        filter_entry.bind("<KeyRelease>", lambda e: self._apply_filter())
        self._filter_placeholder = self.t("font_filter")
        self._filter_var.set(self._filter_placeholder)
        filter_entry.config(foreground="gray")
        filter_entry.bind("<FocusIn>", self._on_filter_focus_in)
        filter_entry.bind("<FocusOut>", self._on_filter_focus_out)

        ttk.Button(top, text=self.t("font_enable_all"),
                   command=self._select_all).pack(side=tk.LEFT, padx=2)
        ttk.Button(top, text=self.t("font_disable_all"),
                   command=self._deselect_all).pack(side=tk.LEFT, padx=2)

        self._count_label = ttk.Label(self, text="", font=("", 9))
        self._count_label.pack(anchor=tk.W, padx=10, pady=(0, 3))
        self._update_count()

        # 列表容器
        list_container = ttk.Frame(self)
        list_container.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 8))

        self._canvas = tk.Canvas(list_container, highlightthickness=0,
                                 bg=self._bg_color())
        scrollbar = ttk.Scrollbar(list_container, orient=tk.VERTICAL,
                                  command=self._canvas.yview)
        self._scroll_frame = ttk.Frame(self._canvas)

        self._scroll_frame.bind("<Configure>",
            lambda e: self._canvas.configure(
                scrollregion=self._canvas.bbox("all")))
        canvas_win = self._canvas.create_window((0, 0),
            window=self._scroll_frame, anchor=tk.NW)

        # 让内容宽度跟随 canvas 宽度
        def _on_canvas_configure(event):
            self._canvas.itemconfig(canvas_win, width=event.width)
        self._canvas.bind("<Configure>", _on_canvas_configure)

        self._canvas.configure(yscrollcommand=scrollbar.set)
        self._canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 滚轮 — 只在鼠标位于弹窗内时响应，且检查 canvas 是否存活
        def _on_mw(event):
            if self._canvas and self._canvas.winfo_exists():
                self._canvas.yview_scroll(
                    int(-1 * (event.delta / 120)), "units")

        self._mw_self_bind = self.bind("<MouseWheel>", _on_mw, add="+")
        self._mw_canvas_bind = self._canvas.bind("<MouseWheel>", _on_mw, add="+")

        self._populate_list()

        # 底部按钮
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill=tk.X, padx=8, pady=5)

        def _apply():
            self.app.disabled_fonts = set()
            for name in self._check_vars:
                if not self._check_vars[name].get():
                    self.app.disabled_fonts.add(name)
            self._original_disabled = set(self.app.disabled_fonts)
            self.app.save_settings()
            self.app._refresh_font_combo()
            self._update_count()
            messagebox.showinfo(self.t("font_manager_title"),
                                self.t("font_applied"), parent=self)

        def _close():
            if self._has_changes():
                if not messagebox.askyesno(
                    self.t("font_manager_title"),
                    self.t("font_unsaved"), parent=self):
                    return
            self.close()

        ttk.Button(btn_frame, text="应用", command=_apply).pack(
            side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="关闭", command=_close).pack(
            side=tk.LEFT, padx=2)

    def close(self):
        """安全关闭，清除事件绑定"""
        try:
            if self._mw_self_bind:
                self.unbind("<MouseWheel>", self._mw_self_bind)
        except Exception:
            pass
        try:
            if self._mw_canvas_bind and self._canvas and self._canvas.winfo_exists():
                self._canvas.unbind("<MouseWheel>", self._mw_canvas_bind)
        except Exception:
            pass
        self._mw_self_bind = None
        self._mw_canvas_bind = None
        self._canvas = None
        self.destroy()

    def _on_window_close(self):
        """窗口关闭按钮"""
        if self._has_changes():
            if not messagebox.askyesno(
                self.t("font_manager_title"),
                self.t("font_unsaved"), parent=self):
                return
        self.close()

    def _has_changes(self) -> bool:
        current_disabled = set()
        for name in self._check_vars:
            if not self._check_vars[name].get():
                current_disabled.add(name)
        return current_disabled != self._original_disabled

    def _on_filter_focus_in(self, event):
        if self._filter_var.get() == self._filter_placeholder:
            self._filter_var.set("")
            event.widget.config(foreground=self._fg_color())

    def _on_filter_focus_out(self, event):
        if not self._filter_var.get().strip():
            self._filter_var.set(self._filter_placeholder)
            event.widget.config(foreground="gray")

    def _get_filter_text(self) -> str:
        t = self._filter_var.get().strip()
        if t == self._filter_placeholder:
            return ""
        return t

    def _populate_list(self):
        for w in self._scroll_frame.winfo_children():
            w.destroy()
        self._check_vars.clear()

        ft = self._get_filter_text().lower()
        filtered = [(n, p) for n, p in self._all_fonts
                    if ft in n.lower()] if ft else self._all_fonts

        bg = self._bg_color()
        fg = self._fg_color()

        for name, _path in filtered:
            var = tk.BooleanVar(value=name not in self._original_disabled)
            self._check_vars[name] = var
            # 使用 tk.Checkbutton (原生) 确保显示 √
            cb = tk.Checkbutton(
                self._scroll_frame, text=name, variable=var,
                bg=bg, fg=fg, selectcolor=bg,
                activebackground=bg, activeforeground=fg,
                anchor=tk.W, padx=2,
            )
            cb.pack(anchor=tk.W, fill=tk.X, padx=5, pady=1)

        self._update_count()

    def _apply_filter(self):
        self._populate_list()

    def _select_all(self):
        for v in self._check_vars.values():
            v.set(True)
        self._update_count()

    def _deselect_all(self):
        for v in self._check_vars.values():
            v.set(False)
        self._update_count()

    def _update_count(self):
        total = len(self._all_fonts)
        enabled = total - len(self._original_disabled)
        text = self.t("font_count", enabled, total)
        if self._has_changes():
            text += "  *"
        self._count_label.config(text=text)

    def _center(self, parent):
        self.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() - self.winfo_width()) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry("+{}+{}".format(x, y))


class SettingsDialog(tk.Toplevel):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.t = app.t
        self.title(self.t("settings"))
        self.geometry("300x140")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        self._build()
        self._center(parent)

    def _build(self):
        frame = ttk.Frame(self, padding=15)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text=self.t("language") + ":").grid(
            row=0, column=0, sticky=tk.W, pady=5)
        lang_var = tk.StringVar(value=self.app.lang)
        lang_combo = ttk.Combobox(frame, textvariable=lang_var,
                                  values=["zh", "en"], state="readonly", width=6)
        lang_combo.grid(row=0, column=1, sticky=tk.W, pady=5, padx=5)
        lang_combo.bind("<<ComboboxSelected>>",
                        lambda e: self._change_lang(lang_var.get()))

        ttk.Label(frame, text=self.t("theme") + ":").grid(
            row=1, column=0, sticky=tk.W, pady=5)
        theme_var = tk.StringVar(
            value="dark" if self.app.dark_theme else "light")
        theme_combo = ttk.Combobox(frame, textvariable=theme_var,
                                   values=["light", "dark"],
                                   state="readonly", width=6)
        theme_combo.grid(row=1, column=1, sticky=tk.W, pady=5, padx=5)

        def _apply_theme(e=None):
            self.app.set_theme(theme_var.get() == "dark")
            self.app.apply_theme()
            self.destroy()

        ttk.Button(frame, text="应用", command=_apply_theme).grid(
            row=2, column=0, columnspan=2, pady=10)

    def _change_lang(self, lang: str):
        self.app.lang = lang
        self.app.save_settings()
        self.app.rebuild()

    def _center(self, parent):
        self.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() - self.winfo_width()) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry("+{}+{}".format(x, y))


class App:
    def __init__(self):
        self.root = tk.Tk()
        self.lang = "zh"
        self.dark_theme = False
        self.all_fonts = _scan_fonts() if HAS_PIL else []

        cfg = _load_config()
        self.lang = cfg.get("lang", "zh")
        self.dark_theme = cfg.get("dark_theme", False)
        self.recent_fonts: List[str] = cfg.get("recent_fonts", [])
        self.disabled_fonts: Set[str] = set(cfg.get("disabled_fonts", []))

        self.root.title("JNO通用输入法")
        self.root.geometry("900x760")
        self.root.minsize(650, 520)
        self.rebuild()

    def save_settings(self):
        cfg = {
            "lang": self.lang,
            "dark_theme": self.dark_theme,
            "recent_fonts": self.recent_fonts,
            "disabled_fonts": list(self.disabled_fonts),
        }
        _save_config(cfg)

    def _add_recent(self, font_name: str):
        if font_name in self.recent_fonts:
            self.recent_fonts.remove(font_name)
        self.recent_fonts.insert(0, font_name)
        self.recent_fonts = self.recent_fonts[:MAX_RECENT_FONTS]
        self.save_settings()

    def t(self, key: str, *args) -> str:
        s = TEXTS[self.lang].get(key, key)
        if args:
            s = s.format(*args)
        return s

    def _get_enabled_fonts(self) -> List[Tuple[str, str]]:
        return [(n, p) for n, p in self.all_fonts
                if n not in self.disabled_fonts]

    def _get_recent_fonts(self) -> List[str]:
        enabled_names = {n for n, _ in self._get_enabled_fonts()}
        return [r for r in self.recent_fonts if r in enabled_names]

    def rebuild(self):
        for w in self.root.winfo_children():
            w.destroy()
        self._build_menubar()
        self._build_ui()
        self.apply_theme()

    def _build_menubar(self):
        menubar = tk.Menu(self.root)

        m1 = tk.Menu(menubar, tearoff=0)
        m1.add_command(label=self.t("settings"), command=self._open_settings)
        m1.add_command(label=self.t("font_manager"),
                       command=self._open_font_manager)
        menubar.add_cascade(label=self.t("settings"), menu=m1)

        m2 = tk.Menu(menubar, tearoff=0)
        m2.add_command(label=self.t("github"),
                       command=lambda: webbrowser.open(AUTHOR_GITHUB))
        m2.add_command(label=self.t("bilibili"),
                       command=lambda: webbrowser.open(AUTHOR_BILIBILI))
        m2.add_separator()
        m2.add_command(label=self.t("about_title"),
                       command=self._open_about)
        menubar.add_cascade(label=self.t("about"), menu=m2)
        self.root.config(menu=menubar)

    def _build_ui(self):
        main = ttk.Frame(self.root, padding=10)
        main.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main, text=self.t("input_label"),
                  font=("", 11)).pack(anchor=tk.W)

        self.text_entry = tk.Text(main, height=2, font=("", 13), wrap=tk.WORD)
        self.text_entry.pack(fill=tk.X, pady=(3, 2))
        self.text_entry.bind("<Control-Return>", lambda e: self._generate())
        self.text_entry.bind("<Return>", self._handle_return)

        ttk.Label(main, text=self.t("newline_hint"),
                  foreground="gray", font=("", 8)).pack(anchor=tk.W, pady=(0, 5))

        ctrl1 = ttk.Frame(main)
        ctrl1.pack(fill=tk.X, pady=(0, 3))

        ttk.Label(ctrl1, text=self.t("font_label")).pack(side=tk.LEFT)

        font_choices = self._build_font_choices()
        self.font_var = tk.StringVar(value=font_choices[0] if font_choices else "")
        self.font_combo = ttk.Combobox(ctrl1, textvariable=self.font_var,
                                       values=font_choices, width=30,
                                       state="readonly")
        self.font_combo.pack(side=tk.LEFT, padx=5)

        ttk.Label(ctrl1, text=self.t("style") + ":").pack(
            side=tk.LEFT, padx=(15, 0))
        self.style_var = tk.StringVar(value=self.t("style_normal"))
        style_choices = [self.t("style_normal"), self.t("style_bold"),
                         self.t("style_italic"), self.t("style_bold_italic")]
        self.style_combo = ttk.Combobox(ctrl1, textvariable=self.style_var,
                                        values=style_choices, width=8,
                                        state="readonly")
        self.style_combo.pack(side=tk.LEFT, padx=5)

        ctrl2 = ttk.Frame(main)
        ctrl2.pack(fill=tk.X, pady=(0, 5))

        self.vertical_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(ctrl2, text=self.t("vertical"),
                        variable=self.vertical_var).pack(side=tk.LEFT)

        ttk.Label(ctrl2, text=self.t("byte_limit")).pack(
            side=tk.LEFT, padx=(15, 0))
        self.bytes_var = tk.IntVar(value=MAX_BYTES)
        ttk.Spinbox(ctrl2, textvariable=self.bytes_var, from_=5000,
                    to=200000, increment=5000, width=8).pack(
            side=tk.LEFT, padx=5)

        self.gen_btn = ttk.Button(ctrl2, text=self.t("generate"),
                                  command=self._generate)
        self.gen_btn.pack(side=tk.RIGHT, padx=5)

        self.status_var = tk.StringVar(value=self.t("ready"))
        status_label = tk.Label(main, textvariable=self.status_var,
                                relief=tk.SUNKEN, anchor=tk.W, padx=4, pady=2)
        status_label.pack(fill=tk.X, pady=(0, 5))
        self.status_label = status_label

        self.result_text = scrolledtext.ScrolledText(
            main, wrap=tk.NONE, font=("Consolas", 10))
        self.result_text.pack(fill=tk.BOTH, expand=True)

        bottom = ttk.Frame(main)
        bottom.pack(fill=tk.X, pady=(5, 0))

        ttk.Button(bottom, text=self.t("copy"),
                   command=self._copy).pack(side=tk.LEFT, padx=2)
        ttk.Button(bottom, text=self.t("save"),
                   command=self._save).pack(side=tk.LEFT, padx=2)
        ttk.Button(bottom, text=self.t("clear"),
                   command=self._clear).pack(side=tk.LEFT, padx=2)

        enabled_count = len(self._get_enabled_fonts())
        ttk.Label(bottom, text=self.t("fonts_total", enabled_count),
                  foreground="gray", font=("", 8)).pack(side=tk.RIGHT)

        cf = ttk.Frame(self.root)
        cf.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=(0, 3))
        ttk.Label(cf, text=self.t("copyright"),
                  font=("", 7)).pack(side=tk.RIGHT)

    def _build_font_choices(self) -> List[str]:
        choices = [self.t("font_auto")]
        recents = self._get_recent_fonts()
        enabled_names = [n for n, _ in self._get_enabled_fonts()]
        if recents:
            choices.append(self.t("font_recent"))
            choices.extend(recents)
            choices.append(self.t("font_all"))
            choices.extend(enabled_names)
        else:
            choices.extend(enabled_names)
        return choices

    def _refresh_font_combo(self):
        choices = self._build_font_choices()
        current = self.font_var.get()
        self.font_combo["values"] = choices
        if current not in choices:
            self.font_var.set(choices[0] if choices else "")

    def _handle_return(self, event):
        self.text_entry.insert(tk.INSERT, "\n")
        return "break"

    def apply_theme(self):
        theme = DARK_THEME if self.dark_theme else LIGHT_THEME
        self.root.configure(bg=theme["bg"])

        st = ttk.Style()
        st.theme_use("clam")
        st.configure(".", background=theme["bg"], foreground=theme["fg"])
        st.configure("TFrame", background=theme["bg"])
        st.configure("TLabel", background=theme["bg"], foreground=theme["fg"])
        st.configure("TCheckbutton", background=theme["bg"],
                     foreground=theme["fg"])
        st.configure("TButton", background=theme["btn_bg"],
                     foreground=theme["btn_fg"])
        st.map("TButton",
               background=[("active", theme["btn_bg"]),
                           ("disabled", theme["status_bg"])])
        st.configure("TCombobox",
                     fieldbackground=theme["entry_bg"],
                     background=theme["entry_bg"],
                     foreground=theme["entry_fg"])
        st.configure("TSpinbox",
                     fieldbackground=theme["entry_bg"],
                     background=theme["entry_bg"],
                     foreground=theme["entry_fg"])

        self.status_label.configure(
            bg=theme["status_bg"], fg=theme["status_fg"])
        self.text_entry.configure(
            bg=theme["entry_bg"], fg=theme["entry_fg"],
            insertbackground=theme["entry_fg"])
        self.result_text.configure(
            bg=theme["result_bg"], fg=theme["result_fg"],
            insertbackground=theme["result_fg"])

    def set_theme(self, dark: bool):
        self.dark_theme = dark
        self.save_settings()

    def _open_settings(self):
        SettingsDialog(self.root, self)

    def _open_font_manager(self):
        dlg = FontManagerDialog(self.root, self)
        self.root.wait_window(dlg)
        self.rebuild()

    def _open_about(self):
        messagebox.showinfo(self.t("about_title"), self.t("about_text"))

    def _get_style_index(self) -> int:
        s = self.style_var.get()
        if s == self.t("style_bold"):
            return 1
        elif s == self.t("style_italic"):
            return 2
        elif s == self.t("style_bold_italic"):
            return 3
        return 0

    def _generate(self):
        text = self.text_entry.get("1.0", tk.END).rstrip("\n").rstrip()
        if not text:
            messagebox.showwarning(self.t("title"), self.t("input_warning"))
            return

        font_sel = self.font_var.get()
        if font_sel and font_sel != self.t("font_auto") and \
           font_sel not in (self.t("font_recent"), self.t("font_all")):
            font_choice = font_sel
            self._add_recent(font_sel)
        else:
            font_choice = ""

        vertical = self.vertical_var.get()
        max_bytes = self.bytes_var.get()
        style = self._get_style_index()

        self.gen_btn.config(state=tk.DISABLED, text=self.t("generating"))
        self.status_var.set(self.t("generating") + "...")

        def _log(msg):
            self.root.after(0, lambda: self.status_var.set(msg))

        def _run():
            try:
                result = generate(text, font_choice, max_bytes,
                                  vertical, style, callback=_log)
            except Exception as e:
                self.root.after(0, lambda: self._on_error(str(e)))
                return
            self.root.after(0, lambda: self._on_done(result))

        threading.Thread(target=_run, daemon=True).start()

    def _on_done(self, result: str):
        self.result_text.delete("1.0", tk.END)
        self.result_text.insert("1.0", result)
        size = len(result.encode("utf-8"))
        lines = result.count("<br>")
        self.status_var.set(self.t("done", lines, size))
        self.gen_btn.config(state=tk.NORMAL, text=self.t("generate"))
        self._refresh_font_combo()

    def _on_error(self, msg: str):
        messagebox.showerror(self.t("error"), msg)
        self.status_var.set("{}: {}".format(self.t("error"), msg))
        self.gen_btn.config(state=tk.NORMAL, text=self.t("generate"))

    def _copy(self):
        content = self.result_text.get("1.0", tk.END).rstrip()
        if content:
            self.root.clipboard_clear()
            self.root.clipboard_append(content)
            self.status_var.set(self.t("copied"))
        else:
            messagebox.showinfo(self.t("title"),
                                self.t("no_content", self.t("copy")))

    def _save(self):
        content = self.result_text.get("1.0", tk.END).rstrip()
        if not content:
            messagebox.showinfo(self.t("title"),
                                self.t("no_content", self.t("save")))
            return
        from tkinter import filedialog
        path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")])
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            self.status_var.set(self.t("saved", os.path.basename(path)))

    def _clear(self):
        self.result_text.delete("1.0", tk.END)
        self.status_var.set(self.t("cleared"))

    def _on_close(self):
        self.save_settings()
        self.root.destroy()

    def run(self):
        if not HAS_PIL:
            messagebox.showerror(self.t("error"), self.t("missing_pillow"))
            return
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self.root.mainloop()


def main():
    App().run()


if __name__ == "__main__":
    main()
