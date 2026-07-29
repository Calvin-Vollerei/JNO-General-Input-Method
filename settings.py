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
        self.geometry("340x220")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        self._build()
        self._center(parent)

    def _build(self):
        f = ttk.Frame(self, padding=15)
        f.pack(fill=tk.BOTH, expand=True)

        row = 0

        ttk.Label(f, text=self.t("language") + ":").grid(
            row=row, column=0, sticky=tk.W, pady=5)
        lv = tk.StringVar(value=self.app.lang)
        lc = ttk.Combobox(f, textvariable=lv, values=["zh", "en"],
                          state="readonly", width=8)
        lc.grid(row=row, column=1, sticky=tk.W, pady=5, padx=5)
        lc.bind("<<ComboboxSelected>>",
                lambda e: setattr(self.app, 'lang', lv.get()))
        row += 1

        ttk.Label(f, text=self.t("theme") + ":").grid(
            row=row, column=0, sticky=tk.W, pady=5)

        from config import THEME_NAMES_EN
        names = THEME_NAMES_EN if self.app.lang == "en" else THEME_NAMES
        tv = tk.StringVar(value=self.app.theme_name)
        tc = ttk.Combobox(f, textvariable=tv, values=names,
                          state="readonly", width=8)
        tc.grid(row=row, column=1, sticky=tk.W, pady=5, padx=5)
        row += 1

        ttk.Label(f, text=self.t("close_action")).grid(
            row=row, column=0, sticky=tk.W, pady=5)
        close_var = tk.StringVar(
            value=self.t("close_minimize")
            if self.app.close_minimize
            else self.t("close_exit"))
        cc = ttk.Combobox(f, textvariable=close_var,
                          values=[self.t("close_exit"),
                                  self.t("close_minimize")],
                          state="readonly", width=12)
        cc.grid(row=row, column=1, sticky=tk.W, pady=5, padx=5)
        row += 1

        def _apply():
            self.app.lang = lv.get()
            self.app.theme_name = tv.get()
            self.app.close_minimize = (
                close_var.get() == self.t("close_minimize"))
            self.app.save_settings()
            self.app.apply_theme()
            self.app.rebuild()   # 语言/关闭行为可能需刷新
            self.destroy()

        ttk.Button(f, text=self.t("apply"), command=_apply).grid(
            row=row, column=0, columnspan=2, pady=12)

    def _center(self, p):
        self.update_idletasks()
        x = p.winfo_rootx() + (p.winfo_width() - self.winfo_width()) // 2
        y = p.winfo_rooty() + (p.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")
