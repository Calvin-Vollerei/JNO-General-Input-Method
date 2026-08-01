"""JNO通用输入法 主 GUI — v1.8"""

import json
import os
import sys
import threading
import time
import tkinter as tk
from tkinter import ttk, messagebox
import urllib.request
import webbrowser
from typing import List, Set, Dict

from config import (
    VERSION, MAX_BYTES, MAX_RECENT_FONTS, THEMES, COLOR_SLOTS,
    T, load_config, save_config,
    BYTE_WARN_THRESHOLD,
)
from font_utils import scan_fonts, find_ui_font
from renderer import generate, COLOR_ID_LIST
from font_manager import FontManagerDialog
from history_dialog import HistoryDialog
from color_picker import ColorPickerDialog
from ui_utils import apply_round_corners, register_ui_font
from app_ui import build_menubar, build_ui


def _ver_gt(v1: str, v2: str) -> bool:
    try:
        p1 = [int(x) for x in v1.split(".")]
        p2 = [int(x) for x in v2.split(".")]
        return p1 > p2
    except Exception:
        return v1 > v2


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
        self.favorites: List[Dict] = cfg.get("favorites", [])

        saved_slots = cfg.get("color_slots", None)
        if saved_slots and isinstance(saved_slots, list) and len(saved_slots) == COLOR_SLOTS:
            self.color_slots: List[str] = saved_slots
        else:
            self.color_slots = ["#000000"] * COLOR_SLOTS
        self.active_slot: int = cfg.get("active_slot", 0)

        self.history: List[Dict] = []
        self._last_result = ""

        apply_round_corners(self.root)
        self._ui_font_path = find_ui_font()
        if not self._ui_font_path:
            print(self.t("no_font"), file=sys.stderr)
        self._ui_font_name = register_ui_font(self.root, self._ui_font_path)

        self.root.title("JNO通用输入法")
        self.root.geometry("900x760")
        self.root.minsize(650, 520)
        self.rebuild()

    # ═══════════════ 基础 ═══════════════

    @property
    def selected_color(self) -> str | None:
        """返回当前活动槽位的 JNO Label 标识符（#000000~#181818）。
        对应 Minecraft JNO Label 中预定义的 25 个墨水槽位。
        """
        return COLOR_ID_LIST[self.active_slot]

    def save_settings(self):
        save_config({
            "lang": self.lang,
            "theme_name": self.theme_name,
            "close_minimize": self.close_minimize,
            "recent_fonts": self.recent_fonts,
            "disabled_fonts": list(self.disabled_fonts),
            "favorites": self.favorites,
            "color_slots": self.color_slots,
            "active_slot": self.active_slot,
        })

    def t(self, key: str, *args) -> str:
        s = T[self.lang].get(key, key)
        if args:
            s = s.format(*args)
        return s

    def rebuild(self):
        for w in self.root.winfo_children():
            w.destroy()
        build_menubar(self)
        build_ui(self)
        self.apply_theme()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    # ═══════════════ 字体 ═══════════════

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
            th = THEMES.get(self.theme_name, THEMES["高雅灰"])
            e.widget.config(foreground=th["entry_fg"])

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

    # ═══════════════ 颜色 ═══════════════

    def _open_color_picker(self):
        ColorPickerDialog(self.root, self)

    def _on_color_changed(self):
        self._update_color_swatch()

    def _update_color_swatch(self):
        c = self.color_slots[self.active_slot]
        if c != "#000000":
            self._color_swatch.config(bg=c)
        else:
            th = THEMES.get(self.theme_name, THEMES["高雅灰"])
            self._color_swatch.config(bg=th["bg"])

    # ═══════════════ 字节上限 ═══════════════

    def _on_byte_change(self, event=None):
        self._update_byte_warn()

    def _update_byte_warn(self):
        try:
            v = int(self.bytes_var.get())
        except ValueError:
            self._byte_warn_label.config(text="")
            return
        if v > BYTE_WARN_THRESHOLD:
            self._byte_warn_label.config(text=self.t("byte_warn"))
        else:
            self._byte_warn_label.config(text="")

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
        st.map("TCombobox",
               fieldbackground=[("readonly", th["entry_bg"])])
        st.configure("TEntry",
                     fieldbackground=th["entry_bg"],
                     foreground=th["entry_fg"],
                     font=fn,
                     selectbackground=th["select_bg"],
                     selectforeground=th["select_fg"],
                     borderwidth=0)
        st.configure("TNotebook", background=th["bg"], borderwidth=0)
        st.configure("TNotebook.Tab", background=th["tab_bg"],
                     foreground=th["tab_fg"], font=fn, padding=(12, 4))
        st.map("TNotebook.Tab",
               background=[("selected", th["tab_active_bg"])])

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

        if self._font_filter_var.get() != self._font_filter_placeholder:
            self._font_search_entry.config(foreground=th["entry_fg"])

        for cb in [self.font_combo, self.style_combo]:
            try:
                cb.config(state="normal")
                cb.config(state="readonly")
            except Exception:
                pass

        self._update_color_swatch()
        self._update_byte_warn()

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

    def _handle_return(self, event):
        self.text_entry.insert(tk.INSERT, "\n")
        return "break"

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
        try:
            mb = int(self.bytes_var.get())
        except ValueError:
            mb = MAX_BYTES

        if mb > BYTE_WARN_THRESHOLD:
            if not messagebox.askyesno(
                self.t("title"),
                self.t("byte_warn") + "\n\n" + self.t("generate") + "?",
            ):
                return

        stl = self._get_style()
        style_name = self.style_var.get()

        self.gen_btn.config(state=tk.DISABLED,
                            text=self.t("generating"))
        self.status_var.set(self.t("generating") + "...")

        color_for_render = self.selected_color

        def _log(m):
            self.root.after(0, lambda: self.status_var.set(m))

        def _run():
            try:
                r = generate(text, fc, mb, v, stl,
                             color_hex=color_for_render,
                             callback=_log)
            except Exception as exc:
                msg = str(exc)
                self.root.after(0, lambda m=msg: self._on_err(m))
                return
            entry = {
                "text": text,
                "font": fs if fs else "自动",
                "style": stl,
                "style_name": style_name,
                "vertical": v,
                "result": r,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            }
            self.root.after(0, lambda: self._on_done(r, entry))

        threading.Thread(target=_run, daemon=True).start()

    def _on_done(self, r: str, entry: dict = None):
        self._last_result = r

        current = self.result_text.get("1.0", tk.END).rstrip()
        if current:
            self.result_text.insert(tk.END, "\n" + r)
        else:
            self.result_text.delete("1.0", tk.END)
            self.result_text.insert("1.0", r)

        if entry:
            self.history.append(entry)

        size = len(r.encode("utf-8"))
        lines = r.count("<br>")
        self.status_var.set(self.t("done", lines, size))
        self.gen_btn.config(state=tk.NORMAL, text=self.t("generate"))
        self._refresh_font_combo()

    def _on_err(self, m):
        messagebox.showerror(self.t("error"), m)
        self.status_var.set(f"{self.t('error')}: {m}")
        self.gen_btn.config(state=tk.NORMAL, text=self.t("generate"))

    # ═══════════════ 操作 ═══════════════

    def _copy(self):
        if self._last_result:
            self.root.clipboard_clear()
            self.root.clipboard_append(self._last_result)
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
        self._last_result = ""
        self.status_var.set(self.t("cleared"))

    def _open_fm(self):
        d = FontManagerDialog(self.root, self)
        self.root.wait_window(d)
        self.rebuild()

    def _open_history(self):
        HistoryDialog(self.root, self)

    # ═══════════════ 更新检查 ═══════════════

    def _check_update(self):
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

    # ═══════════════ 关闭 ═══════════════

    def _on_close(self):
        if self.close_minimize:
            self.root.iconify()
        else:
            self.save_settings()
            self.root.destroy()

    def run(self):
        self.root.mainloop()


