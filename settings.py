"""设置弹窗"""

import tkinter as tk
from tkinter import ttk
from config import THEME_NAMES


class SettingsDialog(tk.Toplevel):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.t = app.t
        self.title(self.t("settings"))
        self.geometry("320x160")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        self._build()
        self._center(parent)

    def _build(self):
        f = ttk.Frame(self, padding=15)
        f.pack(fill=tk.BOTH, expand=True)

        # ── 语言 ──
        ttk.Label(f, text=self.t("language") + ":").grid(
            row=0, column=0, sticky=tk.W, pady=5)
        lv = tk.StringVar(value=self.app.lang)
        lc = ttk.Combobox(f, textvariable=lv, values=["zh", "en"],
                          state="readonly", width=8)
        lc.grid(row=0, column=1, sticky=tk.W, pady=5, padx=5)
        lc.bind("<<ComboboxSelected>>",
                lambda e: setattr(self.app, 'lang', lv.get()))

        # ── 主题 ──
        ttk.Label(f, text=self.t("theme") + ":").grid(
            row=1, column=0, sticky=tk.W, pady=5)

        from config import THEME_NAMES_EN
        if self.app.lang == "en":
            theme_list = THEME_NAMES_EN
        else:
            theme_list = THEME_NAMES

        # 当前主题名映射到显示语言
        current_idx = 0
        for i, cn in enumerate(THEME_NAMES):
            if cn == self.app.theme_name:
                current_idx = i
                break
        display_name = theme_list[current_idx]

        tv = tk.StringVar(value=display_name)
        tc = ttk.Combobox(f, textvariable=tv, values=theme_list,
                          state="readonly", width=8)
        tc.grid(row=1, column=1, sticky=tk.W, pady=5, padx=5)

        def _apply():
            # 把显示名转回内部中文名
            sel = tv.get()
            idx = theme_list.index(sel) if sel in theme_list else 0
            self.app.theme_name = THEME_NAMES[idx]
            self.app.save_settings()
            self.app.apply_theme()
            self.destroy()

        ttk.Button(f, text=self.t("apply"), command=_apply).grid(
            row=2, column=0, columnspan=2, pady=12)

    def _center(self, p):
        self.update_idletasks()
        x = p.winfo_rootx() + (p.winfo_width() - self.winfo_width()) // 2
        y = p.winfo_rooty() + (p.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")
