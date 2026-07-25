"""
JNO通用输入法
打包: pyinstaller --onefile --windowed --name "JNO通用输入法" --hidden-import PIL --hidden-import PIL.Image --hidden-import PIL.ImageDraw --hidden-import PIL.ImageFont dotart_gui.py
"""

from __future__ import annotations

import glob
import os
import re
import sys
import threading
import webbrowser
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from typing import Dict, List, Tuple

try:
    from PIL import Image, ImageDraw, ImageFont

    HAS_PIL = True
except ImportError:
    HAS_PIL = False

# ═══════════════════════ 国际化 ═══════════════════════

TEXTS = {
    "zh": {
        "title": "JNO通用输入法",
        "input_label": "输入文本:",
        "font_label": "字体:",
        "font_auto": "（自动选择）",
        "vertical": "竖排",
        "byte_limit": "字节上限:",
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
        "about": "关于",
        "about_title": "关于 JNO通用输入法",
        "about_text": (
            "JNO通用输入法 vFinal\n\n"
            "基于 PIL 渲染 + 最近邻降采样\n\n"
            "作者: Calvin Vollerei"
        ),
        "github": "GitHub",
        "bilibili": "B站主页",
        "copyright": "Calvin Vollerei Studio 2022-2026 All Rights Reserved.",
        "done": "完成 — {}行, {}B",
        "font_scan": "字体: {}",
        "scale_info": "scale={:.3f} → {}B",
    },
    "en": {
        "title": "JNO Input Method",
        "input_label": "Input Text:",
        "font_label": "Font:",
        "font_auto": "(Auto Select)",
        "vertical": "Vertical",
        "byte_limit": "Byte Limit:",
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
        "about": "About",
        "about_title": "About JNO Input Method",
        "about_text": (
            "JNO Input Method vFinal\n\n"
            "Convert text to QQ/WeChat dot-art\n"
            "Based on PIL + nearest-neighbor downsampling\n\n"
            "Author: Calvin Vollerei"
        ),
        "github": "GitHub",
        "bilibili": "Bilibili",
        "copyright": "Calvin Vollerei Studio 2022-2026 All Rights Reserved.",
        "done": "Done — {} lines, {}B",
        "font_scan": "Font: {}",
        "scale_info": "scale={:.3f} → {}B",
    },
}

# ═══════════════════════ 配置 ═══════════════════════

MAX_BYTES = 30000
BASE_ROWS = 240
SCALE_MAX = 1.0
SCALE_MIN = 0.10
SCALE_STEP = 0.02
MAX_CHARS_IN = 50

CN_FONT_MAP: Dict[str, str] = {
    "华文中宋": "STZHONGS", "华文宋体": "STSONG", "华文楷体": "STKAITI",
    "华文仿宋": "STFANGSO", "华文细黑": "STXIHEI",
    "宋体": "simsun", "黑体": "simhei", "楷体": "simkai", "仿宋": "simfang",
    "微软雅黑": "msyh", "等线": "Deng",
}

AUTHOR_GITHUB = "https://github.com/Calvin-Vollerei"
AUTHOR_BILIBILI = "https://space.bilibili.com/400975747"

# ═══════════════════════ 主题 ═══════════════════════

LIGHT_THEME = {
    "bg": "#f0f0f0", "fg": "#333333",
    "result_bg": "#ffffff", "result_fg": "#333333",
    "entry_bg": "#ffffff", "entry_fg": "#000000",
    "status_bg": "#e0e0e0", "status_fg": "#555555",
    "btn_bg": "#e0e0e0", "btn_fg": "#000000",
}

DARK_THEME = {
    "bg": "#1e1e1e", "fg": "#cccccc",
    "result_bg": "#252525", "result_fg": "#dddddd",
    "entry_bg": "#2d2d2d", "entry_fg": "#ffffff",
    "status_bg": "#333333", "status_fg": "#aaaaaa",
    "btn_bg": "#3a3a3a", "btn_fg": "#dddddd",
}


# ═══════════════════════ 渲染核心 ═══════════════════════

def _scan_fonts() -> List[Tuple[str, str]]:
    fonts = []
    if sys.platform == "win32":
        fd = os.environ.get("WINDIR", "C:/Windows") + "/Fonts"
    elif sys.platform == "darwin":
        fd = "/System/Library/Fonts"
    else:
        fd = "/usr/share/fonts"
    if os.path.isdir(fd):
        for pat in ("*.ttf", "*.ttc", "*.otf", "*.TTF", "*.TTC", "*.OTF"):
            for fp in glob.glob(os.path.join(fd, "**", pat), recursive=True):
                fonts.append((os.path.splitext(os.path.basename(fp))[0], fp))
    kw = list(CN_FONT_MAP.values()) + [
        "sim", "msyh", "Deng", "FZ", "ST",
        "arial", "times", "cour", "consol", "segoe", "calibri", "cambria",
    ]
    fonts.sort(key=lambda x: (not any(k.lower() in x[0].lower() for k in kw), x[0]))
    return fonts


def _pick_font(pref: str | None, all_f: List[Tuple[str, str]]) -> str:
    if not all_f:
        raise RuntimeError("未找到任何字体")
    if pref is None:
        return all_f[0][1]
    if os.path.exists(pref):
        return pref
    if pref in CN_FONT_MAP:
        m = CN_FONT_MAP[pref].lower()
        for n, p in all_f:
            if m in n.lower():
                return p
    pl = pref.lower()
    for n, p in all_f:
        if pl in n.lower():
            return p
    for n, p in all_f:
        if pl in p.lower():
            return p
    return all_f[0][1]


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


def _render_horizontal(text: str, scale: float, font_path: str) -> bytes:
    hires_h = BASE_ROWS * 4
    hires_w = hires_h * 2
    mask = Image.new("L", (hires_w, hires_h), 0)
    draw = ImageDraw.Draw(mask)
    font = ImageFont.truetype(font_path, int(hires_h * 0.85))
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(((hires_w - tw) // 2 - bbox[0],
               (hires_h - th) // 2 - bbox[1]), text, fill=255, font=font)
    px = mask.load()
    top = next((r for r in range(hires_h) if any(px[c, r] > 0 for c in range(hires_w))), 0)
    bot = next((r for r in range(hires_h - 1, -1, -1)
                if any(px[c, r] > 0 for c in range(hires_w))), hires_h - 1)
    left = next((c for c in range(hires_w) if any(px[c, r] > 0 for r in range(hires_h))), 0)
    right = next((c for c in range(hires_w - 1, -1, -1)
                  if any(px[c, r] > 0 for r in range(hires_h))), hires_w - 1)
    if bot <= top or right <= left:
        return b""
    char_h, char_w = bot - top + 1, right - left + 1
    crop = mask.crop((left, top, right + 1, bot + 1))
    tr = max(int(BASE_ROWS * scale), 5)
    tc = max(int(tr * char_w / char_h), 5)
    return _scan_to_bytes(crop.resize((tc, tr), Image.NEAREST))


def _render_vertical(text: str, scale: float, font_path: str) -> bytes:
    chars = list(text)
    if not chars:
        return b""
    base_rc = BASE_ROWS // max(len(chars), 1)
    blocks, max_w = [], 0
    for ch in chars:
        hires = base_rc * 6
        mask = Image.new("L", (hires, hires), 0)
        draw = ImageDraw.Draw(mask)
        font = ImageFont.truetype(font_path, int(hires * 0.85))
        bbox = draw.textbbox((0, 0), ch, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        draw.text(((hires - tw) // 2 - bbox[0],
                   (hires - th) // 2 - bbox[1]), ch, fill=255, font=font)
        px = mask.load()
        top = next((r for r in range(hires) if any(px[c, r] > 0 for c in range(hires))), 0)
        bot = next((r for r in range(hires - 1, -1, -1)
                    if any(px[c, r] > 0 for c in range(hires))), hires - 1)
        left = next((c for c in range(hires) if any(px[c, r] > 0 for r in range(hires))), 0)
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


def _render(text: str, scale: float, font_path: str, vertical: bool) -> bytes:
    return _render_vertical(text, scale, font_path) if vertical else \
        _render_horizontal(text, scale, font_path)


def _find_scale(text: str, font_path: str, max_bytes: int,
                vertical: bool, callback=None) -> float:
    b = len(_render(text, SCALE_MAX, font_path, vertical))
    if callback:
        callback("scale=1.00 → {}B".format(b))
    if b <= max_bytes:
        return SCALE_MAX
    b = len(_render(text, SCALE_MIN, font_path, vertical))
    if callback:
        callback("scale={:.2f} → {}B".format(SCALE_MIN, b))
    if b > max_bytes:
        return SCALE_MIN
    lo, hi, best = SCALE_MIN, SCALE_MAX, SCALE_MIN
    for _ in range(12):
        if hi - lo < SCALE_STEP:
            break
        mid = (lo + hi) / 2
        b = len(_render(text, mid, font_path, vertical))
        if callback:
            callback("scale={:.3f} → {}B".format(mid, b))
        if b <= max_bytes:
            best, lo = mid, mid
        else:
            hi = mid
    return best


def generate(text: str, font_choice: str, max_bytes: int,
             vertical: bool, callback=None) -> str:
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
    scale = _find_scale(text, fp, max_bytes, vertical, callback)
    body = _render(text, scale, fp, vertical)
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

class SettingsDialog(tk.Toplevel):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.t = app.t
        self.title(self.t("settings"))
        self.geometry("300x160")
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
            row=2, column=0, columnspan=2, pady=15)

    def _change_lang(self, lang: str):
        self.app.lang = lang
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
        self.fonts = _scan_fonts() if HAS_PIL else []

        self._current_theme_name = "light"

        self.root.title("JNO通用输入法")
        self.root.geometry("850x730")
        self.root.minsize(600, 500)

        self.rebuild()

    def t(self, key: str, *args) -> str:
        s = TEXTS[self.lang].get(key, key)
        if args:
            s = s.format(*args)
        return s

    # ── 全量重建 UI（语言/主题切换用） ──

    def rebuild(self):
        for w in self.root.winfo_children():
            w.destroy()

        self._build_menubar()
        self._build_ui()
        self.apply_theme()

    def _build_menubar(self):
        menubar = tk.Menu(self.root)

        # 菜单 → 设置
        m1 = tk.Menu(menubar, tearoff=0)
        m1.add_command(label=self.t("settings"), command=self._open_settings)
        menubar.add_cascade(label=self.t("settings"), menu=m1)

        # 菜单 → 关于
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

        # 输入标签
        ttk.Label(main, text=self.t("input_label"),
                  font=("", 11)).pack(anchor=tk.W)

        # 输入框（tk.Entry 支持 insertbackground）
        self.text_var = tk.StringVar()
        self.text_entry = tk.Entry(main, textvariable=self.text_var,
                                   font=("", 15))
        self.text_entry.pack(fill=tk.X, pady=(3, 8))
        self.text_entry.bind("<Return>", lambda e: self._generate())

        # 控制行
        ctrl = ttk.Frame(main)
        ctrl.pack(fill=tk.X, pady=(0, 5))

        ttk.Label(ctrl, text=self.t("font_label")).pack(side=tk.LEFT)

        font_choices = [self.t("font_auto")]
        for name, path in self.fonts:
            cn = next((k for k, v in CN_FONT_MAP.items()
                       if v.lower() == name.lower()), "")
            font_choices.append("{} [{}]".format(name, cn) if cn else name)

        self.font_var = tk.StringVar(value=font_choices[0] if font_choices else "")
        self.font_combo = ttk.Combobox(ctrl, textvariable=self.font_var,
                                       values=font_choices, width=35,
                                       state="readonly")
        self.font_combo.pack(side=tk.LEFT, padx=5)

        self.vertical_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(ctrl, text=self.t("vertical"),
                        variable=self.vertical_var).pack(side=tk.LEFT, padx=10)

        ttk.Label(ctrl, text=self.t("byte_limit")).pack(
            side=tk.LEFT, padx=(15, 0))
        self.bytes_var = tk.IntVar(value=MAX_BYTES)
        ttk.Spinbox(ctrl, textvariable=self.bytes_var, from_=5000,
                    to=200000, increment=5000, width=8).pack(
            side=tk.LEFT, padx=5)

        self.gen_btn = ttk.Button(ctrl, text=self.t("generate"),
                                  command=self._generate)
        self.gen_btn.pack(side=tk.RIGHT, padx=5)

        # 状态栏
        self.status_var = tk.StringVar(value=self.t("ready"))
        status_label = tk.Label(main, textvariable=self.status_var,
                                relief=tk.SUNKEN, anchor=tk.W, padx=4, pady=2)
        status_label.pack(fill=tk.X, pady=(0, 5))
        self.status_label = status_label

        # 结果区域
        self.result_text = scrolledtext.ScrolledText(
            main, wrap=tk.NONE, font=("Consolas", 10))
        self.result_text.pack(fill=tk.BOTH, expand=True)

        # 底部按钮
        bottom = ttk.Frame(main)
        bottom.pack(fill=tk.X, pady=(5, 0))

        ttk.Button(bottom, text=self.t("copy"),
                   command=self._copy).pack(side=tk.LEFT, padx=2)
        ttk.Button(bottom, text=self.t("save"),
                   command=self._save).pack(side=tk.LEFT, padx=2)
        ttk.Button(bottom, text=self.t("clear"),
                   command=self._clear).pack(side=tk.LEFT, padx=2)

        # 右下角版权
        cf = ttk.Frame(self.root)
        cf.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=(0, 3))
        ttk.Label(cf, text=self.t("copyright"),
                  font=("", 7)).pack(side=tk.RIGHT)

    # ── 主题 ──

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

    # ── 对话框 ──

    def _open_settings(self):
        SettingsDialog(self.root, self)

    def _open_about(self):
        messagebox.showinfo(self.t("about_title"), self.t("about_text"))

    # ── 生成 ──

    def _generate(self):
        text = self.text_var.get().strip()
        if not text:
            messagebox.showwarning(self.t("title"), self.t("input_warning"))
            return

        font_sel = self.font_var.get()
        if font_sel and font_sel != self.t("font_auto"):
            font_choice = font_sel.split(" [")[0] if " [" in font_sel else font_sel
        else:
            font_choice = ""

        vertical = self.vertical_var.get()
        max_bytes = self.bytes_var.get()

        self.gen_btn.config(state=tk.DISABLED, text=self.t("generating"))
        self.status_var.set(self.t("generating") + "...")

        def _log(msg):
            self.root.after(0, lambda: self.status_var.set(msg))

        def _run():
            try:
                result = generate(
                    text, font_choice, max_bytes, vertical, callback=_log)
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

    def _on_error(self, msg: str):
        messagebox.showerror(self.t("error"), msg)
        self.status_var.set("{}: {}".format(self.t("error"), msg))
        self.gen_btn.config(state=tk.NORMAL, text=self.t("generate"))

    # ── 操作 ──

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

