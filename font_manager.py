"""字体管理弹窗"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Set
from config import THEMES


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

        self._build()
        self._center(parent)
        self.protocol("WM_DELETE_WINDOW", self._on_window_close)

    def _th(self):
        return THEMES.get(self.app.theme_name, THEMES["高雅灰"])

    def _bg(self):
        return self._th()["list_bg"]

    def _fg(self):
        return self._th()["list_fg"]

    def _build(self):
        # ── 顶部搜索栏 ──
        top = ttk.Frame(self, padding=8)
        top.pack(fill=tk.X)

        self._filter_var = tk.StringVar()
        fe = ttk.Entry(top, textvariable=self._filter_var, font=("", 10))
        fe.pack(fill=tk.X, side=tk.LEFT, expand=True, padx=(0, 5))
        fe.bind("<KeyRelease>", lambda e: self._populate())
        ph = self.t("font_filter")
        self._filter_var.set(ph)
        fe.config(foreground="gray")

        def _fi(e):
            if self._filter_var.get() == ph:
                self._filter_var.set("")
                e.widget.config(foreground=self._fg())

        def _fo(e):
            if not self._filter_var.get().strip():
                self._filter_var.set(ph)
                e.widget.config(foreground="gray")

        fe.bind("<FocusIn>", _fi)
        fe.bind("<FocusOut>", _fo)

        ttk.Button(top, text=self.t("font_enable_all"),
                   command=self._sel_all).pack(side=tk.LEFT, padx=2)
        ttk.Button(top, text=self.t("font_disable_all"),
                   command=self._sel_none).pack(side=tk.LEFT, padx=2)

        # ── 计数标签 ──
        self._cnt = ttk.Label(self, text="", font=("", 9))
        self._cnt.pack(anchor=tk.W, padx=10, pady=(0, 3))
        self._upd_cnt()

        # ── 可滚动列表 ──
        lc = ttk.Frame(self)
        lc.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 8))
        self._canvas = tk.Canvas(lc, highlightthickness=0, bg=self._bg())
        sb = ttk.Scrollbar(lc, orient=tk.VERTICAL,
                           command=self._canvas.yview)
        self._sf = ttk.Frame(self._canvas)
        self._sf.bind("<Configure>",
                      lambda e: self._canvas.configure(
                          scrollregion=self._canvas.bbox("all")))
        cw = self._canvas.create_window((0, 0), window=self._sf,
                                        anchor=tk.NW)
        self._canvas.bind("<Configure>",
                          lambda e: self._canvas.itemconfig(cw, width=e.width))
        self._canvas.configure(yscrollcommand=sb.set)
        self._canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

        def _mw(e):
            if self._canvas and self._canvas.winfo_exists():
                self._canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")

        self._mwb = self.bind("<MouseWheel>", _mw, add="+")
        self._canvas.bind("<MouseWheel>", _mw, add="+")

        self._populate()

        # ── 底部按钮 ──
        bf = ttk.Frame(self)
        bf.pack(fill=tk.X, padx=8, pady=5)
        ttk.Button(bf, text=self.t("apply"), command=self._apply).pack(
            side=tk.LEFT, padx=2)
        ttk.Button(bf, text=self.t("close"), command=self._close).pack(
            side=tk.LEFT, padx=2)

    def _populate(self):
        for w in self._sf.winfo_children():
            w.destroy()
        self._check_vars.clear()
        q = self._filter_var.get().strip()
        if q == self.t("font_filter"):
            q = ""
        fq = [x for x in self._all_fonts
              if q.lower() in x[0].lower()] if q else self._all_fonts
        bg, fg = self._bg(), self._fg()
        for name, _ in fq:
            v = tk.BooleanVar(value=name not in self._original_disabled)
            self._check_vars[name] = v
            tk.Checkbutton(
                self._sf, text=name, variable=v,
                bg=bg, fg=fg, selectcolor=bg,
                activebackground=bg, activeforeground=fg,
                anchor=tk.W, padx=2,
            ).pack(anchor=tk.W, fill=tk.X, padx=5, pady=1)
        self._upd_cnt()

    def _has_changes(self):
        cur = {n for n, v in self._check_vars.items() if not v.get()}
        return cur != self._original_disabled

    def _upd_cnt(self):
        t = len(self._all_fonts)
        e = t - len(self._original_disabled)
        s = self.t("font_count", e, t)
        if self._has_changes():
            s += "  *"
        self._cnt.config(text=s)

    def _sel_all(self):
        for v in self._check_vars.values():
            v.set(True)
        self._upd_cnt()

    def _sel_none(self):
        for v in self._check_vars.values():
            v.set(False)
        self._upd_cnt()

    def _apply(self):
        self.app.disabled_fonts = {
            n for n, v in self._check_vars.items() if not v.get()
        }
        self._original_disabled = set(self.app.disabled_fonts)
        self.app.save_settings()
        self.app._refresh_font_combo()
        self._upd_cnt()
        messagebox.showinfo(self.t("font_manager_title"),
                            self.t("font_applied"), parent=self)

    def _close(self):
        if self._has_changes():
            if not messagebox.askyesno(
                self.t("font_manager_title"),
                self.t("font_unsaved"), parent=self,
            ):
                return
        self._cleanup()
        self.destroy()

    def _on_window_close(self):
        if self._has_changes():
            if not messagebox.askyesno(
                self.t("font_manager_title"),
                self.t("font_unsaved"), parent=self,
            ):
                return
        self._cleanup()
        self.destroy()

    def _cleanup(self):
        try:
            if hasattr(self, '_mwb'):
                self.unbind("<MouseWheel>", self._mwb)
        except Exception:
            pass
        self._canvas = None

    def _center(self, p):
        self.update_idletasks()
        x = p.winfo_rootx() + (p.winfo_width() - self.winfo_width()) // 2
        y = p.winfo_rooty() + (p.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")
