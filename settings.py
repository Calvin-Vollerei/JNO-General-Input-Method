"""设置弹窗"""

import tkinter as tk
from tkinter import ttk


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
        f = ttk.Frame(self, padding=15)
        f.pack(fill=tk.BOTH, expand=True)

        ttk.Label(f, text=self.t("language") + ":").grid(
            row=0, column=0, sticky=tk.W, pady=5)
        lv = tk.StringVar(value=self.app.lang)
        lc = ttk.Combobox(f, textvariable=lv, values=["zh", "en"],
                          state="readonly", width=6)
        lc.grid(row=0, column=1, sticky=tk.W, pady=5, padx=5)
        lc.bind("<<ComboboxSelected>>",
                lambda e: setattr(self.app, 'lang', lv.get()))

        ttk.Label(f, text=self.t("theme") + ":").grid(
            row=1, column=0, sticky=tk.W, pady=5)
        tv = tk.StringVar(value="dark" if self.app.dark_theme else "light")
        tc = ttk.Combobox(f, textvariable=tv, values=["light", "dark"],
                          state="readonly", width=6)
        tc.grid(row=1, column=1, sticky=tk.W, pady=5, padx=5)

        def _apply():
            self.app.set_theme(tv.get() == "dark")
            self.app.apply_theme()
            self.destroy()

        ttk.Button(f, text="应用", command=_apply).grid(
            row=2, column=0, columnspan=2, pady=10)

    def _center(self, p):
        self.update_idletasks()
        x = p.winfo_rootx() + (p.winfo_width() - self.winfo_width()) // 2
        y = p.winfo_rooty() + (p.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")
