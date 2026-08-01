"""JNO通用输入法 UI 构建"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import webbrowser

from config import (
    VERSION, THEMES,
    AUTHOR_GITHUB, AUTHOR_BILIBILI,
    BYTE_VALUES, BYTE_WARN_THRESHOLD,
)
from settings import SettingsDialog


# ═══════════════════════════════════════════════════════════════
#  菜单栏
# ═══════════════════════════════════════════════════════════════

def build_menubar(app):
    mb = tk.Menu(app.root)

    m1 = tk.Menu(mb, tearoff=0)
    m1.add_command(label=app.t("settings"),
                   command=lambda: SettingsDialog(app.root, app))
    m1.add_command(label=app.t("font_manager"),
                   command=app._open_fm)
    mb.add_cascade(label=app.t("settings"), menu=m1)

    m2 = tk.Menu(mb, tearoff=0)
    m2.add_command(label=app.t("github"),
                   command=lambda: webbrowser.open(AUTHOR_GITHUB))
    m2.add_command(label=app.t("bilibili"),
                   command=lambda: webbrowser.open(AUTHOR_BILIBILI))
    m2.add_separator()
    m2.add_command(label=app.t("about_title"),
                   command=lambda: messagebox.showinfo(
                       app.t("about_title"),
                       app.t("about_text").format(version=VERSION)))
    mb.add_cascade(label=app.t("about"), menu=m2)

    mb.add_command(label=app.t("help"),
                   command=lambda: messagebox.showinfo(
                       app.t("help_title"), app.t("help_text")))

    mb.add_command(label=app.t("history"),
                   command=app._open_history)

    mb.add_command(label=app.t("update"),
                   command=app._check_update)

    app.root.config(menu=mb)


# ═══════════════════════════════════════════════════════════════
#  主界面
# ═══════════════════════════════════════════════════════════════

def build_ui(app):
    main = ttk.Frame(app.root, padding=10)
    main.pack(fill=tk.BOTH, expand=True)

    # ── 输入文本 ──
    ttk.Label(main, text=app.t("input_label"),
              font=("", 11)).pack(anchor=tk.W)

    app.text_entry = tk.Text(main, height=2, font=("", 13), wrap=tk.WORD)
    app.text_entry.pack(fill=tk.X, pady=(3, 2))
    app.text_entry.bind("<Control-Return>", lambda e: app._generate())
    app.text_entry.bind("<Return>", app._handle_return)

    ttk.Label(main, text=app.t("newline_hint"),
              foreground="gray", font=("", 8)).pack(
        anchor=tk.W, pady=(0, 5))

    # ── 第一行 ──
    c1 = ttk.Frame(main)
    c1.pack(fill=tk.X, pady=(0, 3))

    _build_font_row(app, c1)
    _build_color_swatch(app, c1)
    _build_style_row(app, c1)

    # ── 第二行 ──
    c2 = ttk.Frame(main)
    c2.pack(fill=tk.X, pady=(0, 5))

    app.vertical_var = tk.BooleanVar()
    ttk.Checkbutton(c2, text=app.t("vertical"),
                    variable=app.vertical_var).pack(side=tk.LEFT)

    _build_byte_limit(app, c2)

    app.gen_btn = ttk.Button(c2, text=app.t("generate"),
                             command=app._generate)
    app.gen_btn.pack(side=tk.RIGHT, padx=5)

    # ── 状态栏 ──
    app.status_var = tk.StringVar(value=app.t("ready"))
    sl = tk.Label(main, textvariable=app.status_var,
                  relief=tk.SUNKEN, anchor=tk.W, padx=4, pady=2)
    sl.pack(fill=tk.X, pady=(0, 5))
    app.status_label = sl

    # ── 结果框 ──
    app.result_text = scrolledtext.ScrolledText(
        main, wrap=tk.CHAR, font=("Consolas", 10))
    app.result_text.pack(fill=tk.BOTH, expand=True)

    # ── 底部按钮 ──
    btm = ttk.Frame(main)
    btm.pack(fill=tk.X, pady=(5, 0))
    ttk.Button(btm, text=app.t("copy"),
               command=app._copy).pack(side=tk.LEFT, padx=2)
    ttk.Button(btm, text=app.t("save"),
               command=app._save).pack(side=tk.LEFT, padx=2)
    ttk.Button(btm, text=app.t("clear"),
               command=app._clear).pack(side=tk.LEFT, padx=2)

    # ── 版权 ──
    cf = ttk.Frame(app.root)
    cf.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=(0, 3))
    ttk.Label(cf, text=app.t("copyright"),
              font=("", 7)).pack(side=tk.RIGHT)


# ── 字体 ──

def _build_font_row(app, parent):
    ttk.Label(parent, text=app.t("font_label")).pack(
        side=tk.LEFT, padx=(0, 3))

    app._font_filter_var = tk.StringVar()
    app._font_search_entry = ttk.Entry(
        parent, textvariable=app._font_filter_var,
        font=("", 10), width=16)
    app._font_search_entry.pack(side=tk.LEFT)
    app._font_filter_placeholder = app.t("font_search")
    app._font_filter_var.set(app._font_filter_placeholder)
    app._font_search_entry.bind("<FocusIn>", app._on_filter_focus_in)
    app._font_search_entry.bind("<FocusOut>", app._on_filter_focus_out)
    app._font_search_entry.bind(
        "<Return>", lambda e: app._do_search_and_popup())

    app._search_btn = ttk.Button(
        parent, text=app.t("search_btn"),
        command=app._do_search_and_popup, width=6)
    app._search_btn.pack(side=tk.LEFT, padx=(3, 8))

    fc = app._build_font_choices("")
    app.font_var = tk.StringVar(value=fc[0] if fc else "")
    app.font_combo = ttk.Combobox(
        parent, textvariable=app.font_var, values=fc,
        width=24, state="readonly")
    app.font_combo.pack(side=tk.LEFT)
    app.font_combo.bind(
        "<<ComboboxSelected>>",
        lambda e: app._add_recent(app.font_var.get())
        if app.font_var.get() not in (
            app.t("font_auto"), app.t("font_recent"),
            app.t("font_all"))
        else None)


# ── 色块 ──

def _build_color_swatch(app, parent):
    ttk.Label(parent, text=app.t("color_label")).pack(
        side=tk.LEFT, padx=(15, 0))

    f = tk.Frame(parent, width=36, height=26,
                 relief=tk.SOLID, borderwidth=1,
                 cursor="hand2")
    f.pack(side=tk.LEFT, padx=(2, 5))
    f.pack_propagate(False)
    f.bind("<Button-1>", lambda e: app._open_color_picker())
    app._color_swatch = f


# ── 样式 ──

def _build_style_row(app, parent):
    ttk.Label(parent, text=app.t("style") + ":").pack(
        side=tk.LEFT, padx=(15, 0))
    app.style_var = tk.StringVar(value=app.t("style_normal"))
    sc = [app.t("style_normal"), app.t("style_bold"),
          app.t("style_italic"), app.t("style_bold_italic")]
    app.style_combo = ttk.Combobox(
        parent, textvariable=app.style_var, values=sc,
        width=8, state="readonly")
    app.style_combo.pack(side=tk.LEFT, padx=5)


# ── 字节上限（Combobox 可编辑）──

def _build_byte_limit(app, parent):
    ttk.Label(parent, text=app.t("byte_limit")).pack(
        side=tk.LEFT, padx=(15, 0))

    str_vals = [str(v) for v in BYTE_VALUES]
    app.bytes_var = tk.StringVar(value=str(30000))

    app.bytes_combo = ttk.Combobox(
        parent, textvariable=app.bytes_var,
        values=str_vals, width=7)
    app.bytes_combo.pack(side=tk.LEFT, padx=5)
    app.bytes_combo.bind("<<ComboboxSelected>>", app._on_byte_change)
    app.bytes_combo.bind("<KeyRelease>", app._on_byte_change)
    app.bytes_combo.bind("<FocusOut>", app._on_byte_change)

    app._byte_warn_label = tk.Label(
        parent, text="", font=("", 8), fg="#CC6600")
    app._byte_warn_label.pack(side=tk.LEFT, padx=(5, 0))


