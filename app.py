"""JNO通用输入法 主 GUI — v1.5"""

import json
import os
import sys
import threading
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import urllib.request
import webbrowser
from typing import List, Set

from config import (
    VERSION, MAX_BYTES, MAX_RECENT_FONTS, THEMES, THEME_NAMES,
    T, load_config, save_config,
    AUTHOR_GITHUB, AUTHOR_BILIBILI,
)
from font_utils import scan_fonts, find_ui_font
from renderer import generate
from font_manager import FontManagerDialog
from settings import SettingsDialog
from ui_utils import apply_round_corners, register_ui_font


def _ver_gt(v1: str, v2: str) -> bool:
    """Return True if v1 > v2, using semantic version comparison."""
    try:
        p1 = [int(x) for x in v1.split(".")]
        p2 = [int(x) for x in v2.split(".")]
        return p1 > p2
    except Exception:
        return v1 > v2  # fallback to string compare


class App:
    def __init__(self):
        self.root = tk.Tk()
        self.lang = "zh"
        self.theme_name = "高雅灰"
        self.close_minimize = False
        self.all_fonts = scan_fonts()

        cfg = load_config()
        self.lang = cfg.get("lang", "zh")
        self.theme_name = cfg.get("theme_name", "高雅灰")
        self.close_minimize = cfg.get("close_minimize", False)
        self.recent_fonts: List[str] = cfg.get("recent_fonts", [])
        self.disabled_fonts: Set[str] = set(cfg.get("disabled_fonts", []))

        apply_round_corners(self.root)
        self._ui_font_path = find_ui_font()
        if not self._ui_font_path:
            print(self.t("no_font"), file=sys.stderr)
        self._ui_font_name = register_ui_font(self.root, self._ui_font_path)

        self.root.title("JNO通用输入法")
        self.root.geometry("900x760")
        self.root.minsize(650, 520)
        self.rebuild()

    def save_settings(self):
        save_config({
            "lang": self.lang,
            "theme_name": self.theme_name,
            "close_minimize": self.close_minimize,
            "recent_fonts": self.recent_fonts,
            "disabled_fonts": list(self.disabled_fonts),
        })

    def t(self, key: str, *args) -> str:
        s = T[self.lang].get(key, key)
        if args:
            s = s.format(*args)
        return s

    def _get_enabled(self):
        return [(n, p) for n, p in self.all_fonts
                if n not in self.disabled_fonts]

    def _get_recent(self):
        en = {n for n, _ in self._get_enabled()}
        return [r for r in self.recent_fonts if r in en]

    def _add_recent(self, n):
        if n in self.recent_fonts:
            self.recent_fonts.remove(n)
        self.recent_fonts.insert(0, n)
        self.recent_fonts = self.recent_fonts[:MAX_RECENT_FONTS]
        self.save_settings()

    def rebuild(self):
        for w in self.root.winfo_children():
            w.destroy()
        self._build_menubar()
        self._build_ui()
        self.apply_theme()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_menubar(self):
        mb = tk.Menu(self.root)

        # ── 通用 ──
        m1 = tk.Menu(mb, tearoff=0)
        m1.add_command(label=self.t("settings"),
                       command=lambda: SettingsDialog(self.root, self))
        m1.add_command(label=self.t("font_manager"),
                       command=self._open_fm)
        mb.add_cascade(label=self.t("settings"), menu=m1)

        # ── 关于 ──
        m2 = tk.Menu(mb, tearoff=0)
        m2.add_command(label=self.t("github"),
                       command=lambda: webbrowser.open(AUTHOR_GITHUB))
        m2.add_command(label=self.t("bilibili"),
                       command=lambda: webbrowser.open(AUTHOR_BILIBILI))
        m2.add_separator()
        m2.add_command(label=self.t("about_title"),
                       command=lambda: messagebox.showinfo(
                           self.t("about_title"), self.t("about_text")))
        mb.add_cascade(label=self.t("about"), menu=m2)

        # ── 帮助 ──
        mb.add_command(label=self.t("help"),
                       command=lambda: messagebox.showinfo(
                           self.t("help_title"), self.t("help_text")))

        # ── 检查更新 ──
        mb.add_command(label=self.t("update"),
                       command=self._check_update)

        self.root.config(menu=mb)

    def _build_ui(self):
        main = ttk.Frame(self.root, padding=10)
        main.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main, text=self.t("input_label"),
                  font=("", 11)).pack(anchor=tk.W)

        self.text_entry = tk.Text(main, height=2, font=("", 13), wrap=tk.WORD)
        self.text_entry.pack(fill=tk.X, pady=(3, 2))
        self.text_entry.bind("<Control-Return>", lambda e: self._generate())
        self.text_entry.bind(
            "<Return>",
            lambda e: (self.text_entry.insert(tk.INSERT, "\n"), "break"))

        ttk.Label(main, text=self.t("newline_hint"),
                  foreground="gray", font=("", 8)).pack(
            anchor=tk.W, pady=(0, 5))

        c1 = ttk.Frame(main)
        c1.pack(fill=tk.X, pady=(0, 3))

        ttk.Label(c1, text=self.t("font_label")).pack(
            side=tk.LEFT, padx=(0, 3))

        self._font_filter_var = tk.StringVar()
        self._font_search_entry = ttk.Entry(
            c1, textvariable=self._font_filter_var,
            font=("", 10), width=16)
        self._font_search_entry.pack(side=tk.LEFT)
        self._font_filter_placeholder = self.t("font_search")
        self._font_filter_var.set(self._font_filter_placeholder)
        self._font_search_entry.config(foreground="gray")
        self._font_search_entry.bind("<FocusIn>", self._on_filter_focus_in)
        self._font_search_entry.bind("<FocusOut>", self._on_filter_focus_out)
        self._font_search_entry.bind(
            "<Return>", lambda e: self._do_search_and_popup())

        self._search_btn = ttk.Button(
            c1, text=self.t("search_btn"),
            command=self._do_search_and_popup, width=6)
        self._search_btn.pack(side=tk.LEFT, padx=(3, 8))

        fc = self._build_font_choices("")
        self.font_var = tk.StringVar(value=fc[0] if fc else "")
        self.font_combo = ttk.Combobox(
            c1, textvariable=self.font_var, values=fc,
            width=24, state="readonly")
        self.font_combo.pack(side=tk.LEFT)
        self.font_combo.bind(
            "<<ComboboxSelected>>",
            lambda e: self._add_recent(self.font_var.get())
            if self.font_var.get() not in (
                self.t("font_auto"), self.t("font_recent"),
                self.t("font_all"))
            else None)

        ttk.Label(c1, text=self.t("style") + ":").pack(
            side=tk.LEFT, padx=(15, 0))
        self.style_var = tk.StringVar(value=self.t("style_normal"))
        sc = [self.t("style_normal"), self.t("style_bold"),
              self.t("style_italic"), self.t("style_bold_italic")]
        self.style_combo = ttk.Combobox(
            c1, textvariable=self.style_var, values=sc,
            width=8, state="readonly")
        self.style_combo.pack(side=tk.LEFT, padx=5)

        c2 = ttk.Frame(main)
        c2.pack(fill=tk.X, pady=(0, 5))

        self.vertical_var = tk.BooleanVar()
        ttk.Checkbutton(c2, text=self.t("vertical"),
                        variable=self.vertical_var).pack(side=tk.LEFT)

        ttk.Label(c2, text=self.t("byte_limit")).pack(
            side=tk.LEFT, padx=(15, 0))
        self.bytes_var = tk.IntVar(value=MAX_BYTES)
        ttk.Spinbox(c2, textvariable=self.bytes_var, from_=5000,
                    to=200000, increment=5000, width=8).pack(
            side=tk.LEFT, padx=5)

        self.gen_btn = ttk.Button(c2, text=self.t("generate"),
                                  command=self._generate)
        self.gen_btn.pack(side=tk.RIGHT, padx=5)

        self.status_var = tk.StringVar(value=self.t("ready"))
        sl = tk.Label(main, textvariable=self.status_var,
                      relief=tk.SUNKEN, anchor=tk.W, padx=4, pady=2)
        sl.pack(fill=tk.X, pady=(0, 5))
        self.status_label = sl

        self.result_text = scrolledtext.ScrolledText(
            main, wrap=tk.NONE, font=("Consolas", 10))
        self.result_text.pack(fill=tk.BOTH, expand=True)

        btm = ttk.Frame(main)
        btm.pack(fill=tk.X, pady=(5, 0))
        ttk.Button(btm, text=self.t("copy"),
                   command=self._copy).pack(side=tk.LEFT, padx=2)
        ttk.Button(btm, text=self.t("save"),
                   command=self._save).pack(side=tk.LEFT, padx=2)
        ttk.Button(btm, text=self.t("clear"),
                   command=self._clear).pack(side=tk.LEFT, padx=2)
        ttk.Label(btm, text=self.t("fonts_total", len(self._get_enabled())),
                  foreground="gray", font=("", 8)).pack(side=tk.RIGHT)

        cf = ttk.Frame(self.root)
        cf.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=(0, 3))
        ttk.Label(cf, text=self.t("copyright"),
                  font=("", 7)).pack(side=tk.RIGHT)

    # ═══════════════ 字体搜索 ═══════════════

    def _build_font_choices(self, q: str) -> list:
        auto = self.t("font_auto")
        rt = self.t("font_recent")
        at = self.t("font_all")
        rec = self._get_recent()
        en = [n for n, _ in self._get_enabled()]
        if not q:
            c = [auto]
            if rec:
                c += [rt] + rec + [at]
            c += en
            return c
        ql = q.lower()
        c = [auto]
        mr = [r for r in rec if ql in r.lower()]
        ma = [n for n in en if ql in n.lower()]
        if mr:
            c += [rt] + mr
        if ma:
            c += [at] + ma
        return c if len(c) > 1 else c + ["（无匹配）"]

    def _on_filter_focus_in(self, e):
        if self._font_filter_var.get() == self._font_filter_placeholder:
            self._font_filter_var.set("")
            e.widget.config(foreground="black")

    def _on_filter_focus_out(self, e):
        if not self._font_filter_var.get().strip():
            self._font_filter_var.set(self._font_filter_placeholder)
            e.widget.config(foreground="gray")

    def _get_filter_text(self) -> str:
        t = self._font_filter_var.get().strip()
        if t == self._font_filter_placeholder:
            return ""
        return t

    def _do_search_and_popup(self):
        q = self._get_filter_text()
        choices = self._build_font_choices(q)
        self.font_combo["values"] = choices
        if choices:
            self.font_var.set(choices[0])
        self.font_combo.config(state="normal")
        self.font_combo.focus_set()
        self.font_combo.event_generate("<Down>")
        self.root.after(100,
                        lambda: self.font_combo.config(state="readonly"))

    def _refresh_font_combo(self):
        q = self._get_filter_text()
        choices = self._build_font_choices(q)
        self.font_combo["values"] = choices
        cur = self.font_var.get()
        if cur not in choices:
            self.font_var.set(choices[0] if choices else self.t("font_auto"))

    # ═══════════════ 主题 ═══════════════

    def apply_theme(self):
        th = THEMES.get(self.theme_name, THEMES["高雅灰"])
        self.root.configure(bg=th["bg"])

        fn = self._ui_font_name

        st = ttk.Style()
        st.theme_use("clam")
        st.configure(".", background=th["bg"], foreground=th["fg"],
                     font=fn)
        st.configure("TFrame", background=th["bg"], font=fn)
        st.configure("TLabel", background=th["bg"], foreground=th["fg"],
                     font=fn)
        st.configure("TCheckbutton", background=th["bg"],
                     foreground=th["fg"], font=fn)
        st.configure("TButton", background=th["btn_bg"],
                     foreground=th["btn_fg"], font=fn,
                     borderwidth=0, relief="flat", padding=(12, 4))
        st.map("TButton",
               background=[("active", th["btn_bg"]),
                           ("disabled", th["status_bg"])])
        st.configure("TCombobox",
                     fieldbackground=th["entry_bg"],
                     background=th["entry_bg"],
                     foreground=th["entry_fg"],
                     font=fn,
                     selectbackground=th["select_bg"],
                     selectforeground=th["select_fg"],
                     borderwidth=0)
        st.configure("TSpinbox",
                     fieldbackground=th["entry_bg"],
                     background=th["entry_bg"],
                     foreground=th["entry_fg"],
                     font=fn,
                     selectbackground=th["select_bg"],
                     selectforeground=th["select_fg"],
                     borderwidth=0)
        st.configure("TEntry",
                     fieldbackground=th["entry_bg"],
                     foreground=th["entry_fg"],
                     font=fn,
                     selectbackground=th["select_bg"],
                     selectforeground=th["select_fg"],
                     borderwidth=0)

        self.status_label.configure(bg=th["status_bg"],
                                    fg=th["status_fg"],
                                    font=fn)
        self.text_entry.configure(bg=th["entry_bg"],
                                  fg=th["entry_fg"],
                                  insertbackground=th["entry_fg"],
                                  font=fn)
        self.result_text.configure(bg=th["result_bg"],
                                   fg=th["result_fg"],
                                   insertbackground=th["result_fg"])

    # ═══════════════ 生成 ═══════════════

    def _get_style(self):
        s = self.style_var.get()
        if s == self.t("style_bold"):
            return 1
        if s == self.t("style_italic"):
            return 2
        if s == self.t("style_bold_italic"):
            return 3
        return 0

    def _generate(self):
        text = self.text_entry.get("1.0", tk.END).rstrip("\n").rstrip()
        if not text:
            messagebox.showwarning(self.t("title"),
                                   self.t("input_warning"))
            return

        fs = self.font_var.get()
        if fs and fs != self.t("font_auto") and \
           fs not in (self.t("font_recent"), self.t("font_all"),
                      self.t("font_search")):
            fc = fs
            self._add_recent(fs)
        else:
            fc = ""

        v = self.vertical_var.get()
        mb = self.bytes_var.get()
        stl = self._get_style()

        self.gen_btn.config(state=tk.DISABLED,
                            text=self.t("generating"))
        self.status_var.set(self.t("generating") + "...")

        def _log(m):
            self.root.after(0, lambda: self.status_var.set(m))

        def _run():
            try:
                r = generate(text, fc, mb, v, stl, callback=_log)
            except Exception as exc:
                msg = str(exc)
                self.root.after(0, lambda m=msg: self._on_err(m))
                return
            self.root.after(0, lambda res=r: self._on_done(res))

        threading.Thread(target=_run, daemon=True).start()

    def _on_done(self, r):
        self.result_text.delete("1.0", tk.END)
        self.result_text.insert("1.0", r)
        self.status_var.set(
            self.t("done", r.count("<br>"), len(r.encode("utf-8"))))
        self.gen_btn.config(state=tk.NORMAL, text=self.t("generate"))
        self._refresh_font_combo()

    def _on_err(self, m):
        messagebox.showerror(self.t("error"), m)
        self.status_var.set(f"{self.t('error')}: {m}")
        self.gen_btn.config(state=tk.NORMAL, text=self.t("generate"))

    # ═══════════════ 操作 ═══════════════

    def _copy(self):
        c = self.result_text.get("1.0", tk.END).rstrip()
        if c:
            self.root.clipboard_clear()
            self.root.clipboard_append(c)
            self.status_var.set(self.t("copied"))
        else:
            messagebox.showinfo(self.t("title"),
                                self.t("no_content", self.t("copy")))

    def _save(self):
        c = self.result_text.get("1.0", tk.END).rstrip()
        if not c:
            messagebox.showinfo(self.t("title"),
                                self.t("no_content", self.t("save")))
            return
        from tkinter import filedialog
        p = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")])
        if p:
            with open(p, "w", encoding="utf-8") as f:
                f.write(c)
            self.status_var.set(self.t("saved", os.path.basename(p)))

    def _clear(self):
        self.result_text.delete("1.0", tk.END)
        self.status_var.set(self.t("cleared"))

    def _open_fm(self):
        d = FontManagerDialog(self.root, self)
        self.root.wait_window(d)
        self.rebuild()

    # ═══════════════ 更新检查 ═══════════════

    def _check_update(self):
        """异步检查 GitHub 最新版本（仅当更高时才提示更新）"""
        self.status_var.set(self.t("update_checking"))

        def _run():
            try:
                req = urllib.request.Request(
                    "https://api.github.com/repos/Calvin-Vollerei/"
                    "JNO-Input-General-Method/releases/latest",
                    headers={"Accept": "application/json",
                             "User-Agent": "JNO-Input-Method"})
                with urllib.request.urlopen(req, timeout=10) as resp:
                    data = json.loads(resp.read())
                latest = data.get("tag_name", "").lstrip("v")

                def _done():
                    if latest and _ver_gt(latest, VERSION):
                        if messagebox.askyesno(
                            self.t("update"),
                            self.t("update_available", latest, VERSION)):
                            webbrowser.open(
                                "https://github.com/Calvin-Vollerei/"
                                "JNO-Input-General-Method/releases/latest")
                    else:
                        messagebox.showinfo(
                            self.t("update"),
                            self.t("update_latest", VERSION))
                    self.status_var.set(self.t("ready"))

                self.root.after(0, _done)
            except Exception as e:
                def _err():
                    messagebox.showwarning(
                        self.t("update"),
                        self.t("update_error", str(e)))
                    self.status_var.set(self.t("ready"))
                self.root.after(0, _err)

        threading.Thread(target=_run, daemon=True).start()

    # ═══════════════ 关闭行为 ═══════════════

    def _on_close(self):
        if self.close_minimize:
            self.root.iconify()
        else:
            self.save_settings()
            self.root.destroy()

    def run(self):
        self.root.mainloop()
