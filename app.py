"""JNO通用输入法 主 GUI"""

import os
import threading
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import webbrowser
from typing import List, Set

from config import (MAX_BYTES, MAX_RECENT_FONTS,
                    LIGHT_THEME, DARK_THEME, T, load_config, save_config,
                    AUTHOR_GITHUB, AUTHOR_BILIBILI)
from font_utils import scan_fonts
from renderer import generate
from font_manager import FontManagerDialog
from settings import SettingsDialog


class App:
    def __init__(self):
        self.root = tk.Tk()
        self.lang = "zh"
        self.dark_theme = False
        self.all_fonts = scan_fonts()

        cfg = load_config()
        self.lang          = cfg.get("lang", "zh")
        self.dark_theme    = cfg.get("dark_theme", False)
        self.recent_fonts: List[str] = cfg.get("recent_fonts", [])
        self.disabled_fonts: Set[str] = set(cfg.get("disabled_fonts", []))

        self.root.title("JNO通用输入法")
        self.root.geometry("900x760")
        self.root.minsize(650, 520)
        self.rebuild()

    def save_settings(self):
        save_config({
            "lang": self.lang, "dark_theme": self.dark_theme,
            "recent_fonts": self.recent_fonts,
            "disabled_fonts": list(self.disabled_fonts),
        })

    def t(self, key: str, *args) -> str:
        s = T[self.lang].get(key, key)
        if args: s = s.format(*args)
        return s

    def _get_enabled(self):
        return [(n, p) for n, p in self.all_fonts if n not in self.disabled_fonts]

    def _get_recent(self):
        en = {n for n, _ in self._get_enabled()}
        return [r for r in self.recent_fonts if r in en]

    def _add_recent(self, n):
        if n in self.recent_fonts: self.recent_fonts.remove(n)
        self.recent_fonts.insert(0, n)
        self.recent_fonts = self.recent_fonts[:MAX_RECENT_FONTS]
        self.save_settings()

    def rebuild(self):
        for w in self.root.winfo_children(): w.destroy()
        self._build_menubar()
        self._build_ui()
        self.apply_theme()

    def _build_menubar(self):
        mb = tk.Menu(self.root)
        m1 = tk.Menu(mb, tearoff=0)
        m1.add_command(label=self.t("settings"),
                       command=lambda: SettingsDialog(self.root, self))
        m1.add_command(label=self.t("font_manager"),
                       command=lambda: self._open_fm())
        mb.add_cascade(label=self.t("settings"), menu=m1)
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
        self.root.config(menu=mb)

    def _build_ui(self):
        main = ttk.Frame(self.root, padding=10)
        main.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main, text=self.t("input_label"), font=("", 11)).pack(anchor=tk.W)
        self.text_entry = tk.Text(main, height=2, font=("", 13), wrap=tk.WORD)
        self.text_entry.pack(fill=tk.X, pady=(3, 2))
        self.text_entry.bind("<Control-Return>", lambda e: self._generate())
        self.text_entry.bind("<Return>",
            lambda e: (self.text_entry.insert(tk.INSERT, "\n"), "break"))
        ttk.Label(main, text=self.t("newline_hint"),
                  foreground="gray", font=("", 8)).pack(anchor=tk.W, pady=(0, 5))

        c1 = ttk.Frame(main); c1.pack(fill=tk.X, pady=(0, 3))
        ttk.Label(c1, text=self.t("font_label")).pack(side=tk.LEFT)
        fc = self._build_font_choices("")
        self.font_var = tk.StringVar(value=fc[0] if fc else "")
        self.font_combo = ttk.Combobox(c1, textvariable=self.font_var, values=fc, width=30)
        self.font_combo.pack(side=tk.LEFT, padx=5)
        self.font_combo.bind("<KeyRelease>", self._on_font_search)
        self.font_combo.bind("<<ComboboxSelected>>", lambda e: self._on_font_selected())
        self._focused = False
        self.font_combo.bind("<FocusIn>", lambda e: self._on_font_focus(True))
        self.font_combo.bind("<FocusOut>", lambda e: self._on_font_focus(False))
        self._ph = self.t("font_search")

        ttk.Label(c1, text=self.t("style") + ":").pack(side=tk.LEFT, padx=(15, 0))
        self.style_var = tk.StringVar(value=self.t("style_normal"))
        sc = [self.t("style_normal"), self.t("style_bold"),
              self.t("style_italic"), self.t("style_bold_italic")]
        self.style_combo = ttk.Combobox(c1, textvariable=self.style_var,
                                        values=sc, width=8, state="readonly")
        self.style_combo.pack(side=tk.LEFT, padx=5)

        c2 = ttk.Frame(main); c2.pack(fill=tk.X, pady=(0, 5))
        self.vertical_var = tk.BooleanVar()
        ttk.Checkbutton(c2, text=self.t("vertical"),
                        variable=self.vertical_var).pack(side=tk.LEFT)
        ttk.Label(c2, text=self.t("byte_limit")).pack(side=tk.LEFT, padx=(15, 0))
        self.bytes_var = tk.IntVar(value=MAX_BYTES)
        ttk.Spinbox(c2, textvariable=self.bytes_var, from_=5000,
                    to=200000, increment=5000, width=8).pack(side=tk.LEFT, padx=5)
        self.gen_btn = ttk.Button(c2, text=self.t("generate"), command=self._generate)
        self.gen_btn.pack(side=tk.RIGHT, padx=5)

        self.status_var = tk.StringVar(value=self.t("ready"))
        sl = tk.Label(main, textvariable=self.status_var,
                      relief=tk.SUNKEN, anchor=tk.W, padx=4, pady=2)
        sl.pack(fill=tk.X, pady=(0, 5)); self.status_label = sl

        self.result_text = scrolledtext.ScrolledText(
            main, wrap=tk.NONE, font=("Consolas", 10))
        self.result_text.pack(fill=tk.BOTH, expand=True)

        btm = ttk.Frame(main); btm.pack(fill=tk.X, pady=(5, 0))
        ttk.Button(btm, text=self.t("copy"), command=self._copy).pack(side=tk.LEFT, padx=2)
        ttk.Button(btm, text=self.t("save"), command=self._save).pack(side=tk.LEFT, padx=2)
        ttk.Button(btm, text=self.t("clear"), command=self._clear).pack(side=tk.LEFT, padx=2)
        ttk.Label(btm, text=self.t("fonts_total", len(self._get_enabled())),
                  foreground="gray", font=("", 8)).pack(side=tk.RIGHT)

        cf = ttk.Frame(self.root); cf.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=(0, 3))
        ttk.Label(cf, text=self.t("copyright"), font=("", 7)).pack(side=tk.RIGHT)

    # ── 字体搜索 ──
    def _build_font_choices(self, q):
        auto = self.t("font_auto"); rt = self.t("font_recent"); at = self.t("font_all")
        rec = self._get_recent(); en = [n for n, _ in self._get_enabled()]
        if not q:
            c = [auto]
            if rec: c += [rt] + rec + [at]
            c += en; return c
        ql = q.lower()
        c = [auto]
        mr = [r for r in rec if ql in r.lower()]
        ma = [n for n in en if ql in n.lower()]
        if mr: c += [rt] + mr
        if ma: c += [at] + ma
        return c if len(c) > 1 else c + ["（无匹配）"]

    def _on_font_search(self, e):
        if not self._focused or e.keysym in (
            "Up","Down","Left","Right","Return","Tab","Escape",
            "Control_L","Control_R","Shift_L","Shift_R","Alt_L","Alt_R"): return
        q = self.font_var.get() if self.font_var.get() != self._ph else ""
        self.font_combo["values"] = self._build_font_choices(q)
        self.root.after_idle(lambda: self.font_combo.event_generate("<Down>"))

    def _on_font_selected(self): self._focused = False

    def _on_font_focus(self, f):
        self._focused = f
        if f:
            if self.font_var.get() == self._ph:
                self.font_var.set(""); self.font_combo.config(foreground="black")
            self.font_combo["values"] = self._build_font_choices("")
        else:
            self.root.after(200, self._reset_font_display)

    def _reset_font_display(self):
        if self._focused: return
        cur = self.font_var.get().strip()
        fc = self._build_font_choices("")
        self.font_combo["values"] = fc
        if not cur or cur == self._ph: self.font_var.set(fc[0] if fc else "")

    def _refresh_font_combo(self):
        self.font_combo["values"] = self._build_font_choices("")
        cur = self.font_var.get()
        if cur not in self.font_combo["values"]: self.font_var.set(self.t("font_auto"))

    # ── 主题 ──
    def apply_theme(self):
        th = DARK_THEME if self.dark_theme else LIGHT_THEME
        self.root.configure(bg=th["bg"])
        st = ttk.Style(); st.theme_use("clam")
        st.configure(".", background=th["bg"], foreground=th["fg"])
        st.configure("TFrame", background=th["bg"])
        st.configure("TLabel", background=th["bg"], foreground=th["fg"])
        st.configure("TCheckbutton", background=th["bg"], foreground=th["fg"])
        st.configure("TButton", background=th["btn_bg"], foreground=th["btn_fg"])
        st.map("TButton", background=[("active", th["btn_bg"]),
               ("disabled", th["status_bg"])])
        st.configure("TCombobox", fieldbackground=th["entry_bg"],
                     background=th["entry_bg"], foreground=th["entry_fg"])
        st.configure("TSpinbox", fieldbackground=th["entry_bg"],
                     background=th["entry_bg"], foreground=th["entry_fg"])
        self.status_label.configure(bg=th["status_bg"], fg=th["status_fg"])
        self.text_entry.configure(bg=th["entry_bg"], fg=th["entry_fg"],
                                  insertbackground=th["entry_fg"])
        self.result_text.configure(bg=th["result_bg"], fg=th["result_fg"],
                                   insertbackground=th["result_fg"])

    def set_theme(self, dark):
        self.dark_theme = dark; self.save_settings()

    # ── 生成 ──
    def _get_style(self):
        s = self.style_var.get()
        if s == self.t("style_bold"): return 1
        if s == self.t("style_italic"): return 2
        if s == self.t("style_bold_italic"): return 3
        return 0

    def _generate(self):
        text = self.text_entry.get("1.0", tk.END).rstrip("\n").rstrip()
        if not text:
            messagebox.showwarning(self.t("title"), self.t("input_warning")); return
        fs = self.font_var.get()
        if fs and fs != self.t("font_auto") and fs != self._ph and \
           fs not in (self.t("font_recent"), self.t("font_all")):
            fc = fs; self._add_recent(fs)
        else:
            fc = ""
        v = self.vertical_var.get(); mb = self.bytes_var.get()
        stl = self._get_style()
        self.gen_btn.config(state=tk.DISABLED, text=self.t("generating"))
        self.status_var.set(self.t("generating") + "...")

        def _log(m): self.root.after(0, lambda: self.status_var.set(m))
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
        self.status_var.set(self.t("done", r.count("<br>"), len(r.encode("utf-8"))))
        self.gen_btn.config(state=tk.NORMAL, text=self.t("generate"))
        self._refresh_font_combo()

    def _on_err(self, m):
        messagebox.showerror(self.t("error"), m)
        self.status_var.set(f"{self.t('error')}: {m}")
        self.gen_btn.config(state=tk.NORMAL, text=self.t("generate"))

    def _copy(self):
        c = self.result_text.get("1.0", tk.END).rstrip()
        if c:
            self.root.clipboard_clear(); self.root.clipboard_append(c)
            self.status_var.set(self.t("copied"))
        else:
            messagebox.showinfo(self.t("title"), self.t("no_content", self.t("copy")))

    def _save(self):
        c = self.result_text.get("1.0", tk.END).rstrip()
        if not c:
            messagebox.showinfo(self.t("title"), self.t("no_content", self.t("save"))); return
        from tkinter import filedialog
        p = filedialog.asksaveasfilename(defaultextension=".txt",
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")])
        if p:
            with open(p, "w", encoding="utf-8") as f: f.write(c)
            self.status_var.set(self.t("saved", os.path.basename(p)))

    def _clear(self):
        self.result_text.delete("1.0", tk.END)
        self.status_var.set(self.t("cleared"))

    def _open_fm(self):
        d = FontManagerDialog(self.root, self)
        self.root.wait_window(d); self.rebuild()

    def run(self):
        self.root.protocol("WM_DELETE_WINDOW",
                           lambda: (self.save_settings(), self.root.destroy()))
        self.root.mainloop()
