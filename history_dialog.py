"""历史记录与收藏弹窗"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import List, Dict
from config import THEMES


class HistoryDialog(tk.Toplevel):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.t = app.t
        self.title(self.t("history_title"))
        self.geometry("700x500")
        self.resizable(True, True)
        self.transient(parent)

        th = THEMES.get(self.app.theme_name, THEMES["高雅灰"])
        self.configure(bg=th["bg"])

        self._notebook = ttk.Notebook(self)
        self._notebook = ttk.Notebook(self, style="TNotebook")
        self._notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self._recent_frame = ttk.Frame(self._notebook)
        self._notebook.add(self._recent_frame,
                           text=self.t("history_tab_recent"))
        self._build_list(self._recent_frame, "recent")

        self._fav_frame = ttk.Frame(self._notebook)
        self._notebook.add(self._fav_frame,
                           text=self.t("history_tab_favorites"))
        self._build_list(self._fav_frame, "favorites")

        self._center(parent)

    def _build_list(self, parent, kind: str):
        th = THEMES.get(self.app.theme_name, THEMES["高雅灰"])

        top = ttk.Frame(parent, padding=5)
        top.pack(fill=tk.X)

        if kind == "recent":
            ttk.Button(top, text=self.t("history_clear_all"),
                       command=self._clear_recent).pack(side=tk.LEFT)
        ttk.Label(top, text="", font=("", 1)).pack(
            side=tk.LEFT, fill=tk.X, expand=True)

        canvas = tk.Canvas(parent, highlightthickness=0,
                           bg=th["list_bg"])
        scrollbar = ttk.Scrollbar(parent, orient=tk.VERTICAL,
                                  command=canvas.yview)
        scroll_frame = ttk.Frame(canvas)

        scroll_frame.bind("<Configure>",
                          lambda e: canvas.configure(
                              scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor=tk.NW)
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        def _mw(e):
            canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")
        canvas.bind("<MouseWheel>", _mw)

        if kind == "recent":
            self._recent_scroll = scroll_frame
        else:
            self._fav_scroll = scroll_frame

        self._populate_list(kind)

    def _populate_list(self, kind: str):
        th = THEMES.get(self.app.theme_name, THEMES["高雅灰"])
        frame = self._recent_scroll if kind == "recent" else self._fav_scroll
        for w in frame.winfo_children():
            w.destroy()

        items = (self.app.history if kind == "recent"
                 else self.app.favorites)

        if not items:
            ttk.Label(frame, text=self.t(
                "history_empty" if kind == "recent" else "history_fav_empty"),
                font=("", 10)).pack(pady=20)
            return

        for idx, entry in enumerate(items if kind == "recent"
                                    else reversed(self.app.favorites)):
            self._add_item_row(frame, entry, kind, idx, th)

    def _add_item_row(self, parent, entry: dict, kind: str, idx: int,
                       th: dict):
        row = ttk.Frame(parent, padding=3)
        row.pack(fill=tk.X, pady=1, padx=5)

        ts = entry.get("timestamp", "")[:16] if kind == "recent" else ""
        if kind == "favorites":
            ts = entry.get("added", "")[:16]
        ttk.Label(row, text=ts, width=16, font=("", 8)).pack(
            side=tk.LEFT, padx=(0, 5))

        text_preview = entry.get("text", "")[:20].replace("\n", " ")
        font_name = entry.get("font", "自动")
        style_name = entry.get("style_name", "常规")
        info = f"{text_preview}  |  {font_name}  |  {style_name}"
        ttk.Label(row, text=info, font=("", 9)).pack(
            side=tk.LEFT, fill=tk.X, expand=True)

        ttk.Button(row, text=self.t("history_copy"),
                   command=lambda e=entry: self._do_copy(e),
                   width=4).pack(side=tk.RIGHT, padx=2)

        if kind == "recent":
            ttk.Button(row, text=self.t("history_fav"),
                       command=lambda e=entry: self._do_fav(e),
                       width=4).pack(side=tk.RIGHT, padx=2)
        else:
            ttk.Button(row, text=self.t("history_unfav"),
                       command=lambda e=entry: self._do_unfav(e),
                       width=6).pack(side=tk.RIGHT, padx=2)

    def _do_copy(self, entry: dict):
        result = entry.get("result", "")
        if result:
            self.app.root.clipboard_clear()
            self.app.root.clipboard_append(result)
            self.app.status_var.set(self.t("copied"))

    def _do_fav(self, entry: dict):
        import time
        entry_copy = dict(entry)
        entry_copy["added"] = time.strftime("%Y-%m-%d %H:%M")
        for f in self.app.favorites:
            if f.get("result") == entry_copy.get("result"):
                messagebox.showinfo(self.t("history_title"),
                                    "已存在相同收藏")
                return
        self.app.favorites.append(entry_copy)
        self.app.save_settings()
        self._populate_list("favorites")
        messagebox.showinfo(self.t("history_title"),
                            self.t("history_fav_added"))

    def _do_unfav(self, entry: dict):
        self.app.favorites = [
            f for f in self.app.favorites
            if f.get("result") != entry.get("result")
        ]
        self.app.save_settings()
        self._populate_list("favorites")
        messagebox.showinfo(self.t("history_title"),
                            self.t("history_fav_removed"))

    def _clear_recent(self):
        self.app.history.clear()
        self._populate_list("recent")
        self.app.status_var.set(self.t("history_cleared"))

    def _center(self, parent):
        self.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() - self.winfo_width()) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")
