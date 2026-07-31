"""设置弹窗 — v1.7：语言/主题/关闭行为即时生效"""

import tkinter as tk
from tkinter import ttk
from config import THEME_NAMES, THEMES


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

        th = THEMES.get(self.app.theme_name, THEMES["高雅灰"])
        self.configure(bg=th["bg"])

        # 记录原始值，用于判断是否变化
        self._orig_lang = app.lang
        self._orig_theme = app.theme_name
        self._orig_close_minimize = app.close_minimize

        self._build()
        self._center(parent)

    def _build(self):
        th = THEMES.get(self.app.theme_name, THEMES["高雅灰"])

        f = ttk.Frame(self, padding=15)
        f.pack(fill=tk.BOTH, expand=True)

        row = 0

        ttk.Label(f, text=self.t("language") + ":").grid(
            row=row, column=0, sticky=tk.W, pady=5)
        lv = tk.StringVar(value=self.app.lang)
        lc = ttk.Combobox(f, textvariable=lv, values=["zh", "en"],
                          state="readonly", width=8)
        lc.grid(row=row, column=1, sticky=tk.W, pady=5, padx=5)
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
            new_lang = lv.get()
            new_theme = tv.get()
            new_cm = close_var.get() == self.t("close_minimize")

            lang_changed = new_lang != self._orig_lang
            theme_changed = new_theme != self._orig_theme

            self.app.lang = new_lang
            self.app.theme_name = new_theme
            self.app.close_minimize = new_cm
            self.app.save_settings()

            if lang_changed:
                # 语言变了必须重建 UI（所有文字刷新）
                self.app.rebuild()
            elif theme_changed:
                # 主题变了只需重新应用样式
                self.app.apply_theme()

            self.destroy()

        ttk.Button(f, text=self.t("apply"), command=_apply).grid(
            row=row, column=0, columnspan=2, pady=12)

    def _center(self, p):
        self.update_idletasks()
        x = p.winfo_rootx() + (p.winfo_width() - self.winfo_width()) // 2
        y = p.winfo_rooty() + (p.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")
