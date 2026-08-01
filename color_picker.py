"""JNO 颜色槽位弹窗 — 5×5 槽位色盘 + hex 输入 + 应用"""

import re
import tkinter as tk
from tkinter import ttk, messagebox
from config import THEMES, COLOR_SLOTS


_HEX_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")


class ColorPickerDialog(tk.Toplevel):
    """5×5 颜色槽位选择盘：点击选槽位，hex 输入染色，应用生效"""

    CELL_SIZE = 36
    GRID_COLS = 5
    GAP = 4

    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.t = app.t

        self._slots = list(app.color_slots)
        self._active = app.active_slot

        self.title(self.t("color_slot_title"))
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        th = THEMES.get(self.app.theme_name, THEMES["高雅灰"])
        self.configure(bg=th["bg"])
        self._th = th

        self._build()
        self._sync_all()
        self._center(parent)

    # ── 构建 ──

    def _build(self):
        pad = 10
        canvas_w = (self.GRID_COLS * self.CELL_SIZE
                    + (self.GRID_COLS + 1) * self.GAP)
        canvas_h = 5 * self.CELL_SIZE + 6 * self.GAP

        # ── 5×5 槽位色盘 ──
        self._grid_canvas = tk.Canvas(
            self,
            width=canvas_w,
            height=canvas_h,
            highlightthickness=0,
            bg=self._th["bg"],
        )
        self._grid_canvas.pack(padx=pad, pady=(pad, 0))

        self._sel_rect = self._grid_canvas.create_rectangle(
            0, 0, 0, 0,
            outline=self._th["select_bg"],
            width=3,
        )
        self._cell_rects = {}
        self._cell_labels = {}

        for i in range(COLOR_SLOTS):
            row, col = divmod(i, self.GRID_COLS)
            x1 = self.GAP + col * (self.CELL_SIZE + self.GAP)
            y1 = self.GAP + row * (self.CELL_SIZE + self.GAP)
            x2 = x1 + self.CELL_SIZE
            y2 = y1 + self.CELL_SIZE

            color = self._slots[i]
            rid = self._grid_canvas.create_rectangle(
                x1, y1, x2, y2,
                fill=color,
                outline="#555555" if self._is_dark() else "#cccccc",
                width=1,
                tags=("cell",),
            )
            self._cell_rects[i] = rid

            tid = self._grid_canvas.create_text(
                (x1 + x2) // 2, (y1 + y2) // 2,
                text=str(i + 1),
                fill=self._label_fg(color),
                font=("", 8, "bold"),
            )
            self._cell_labels[i] = tid

            self._grid_canvas.tag_bind(
                rid, "<Button-1>", lambda e, idx=i: self._on_slot_click(idx))
            self._grid_canvas.tag_bind(
                tid, "<Button-1>", lambda e, idx=i: self._on_slot_click(idx))

        # ── hex 输入行 ──
        hf = ttk.Frame(self, padding=(pad, 6, pad, 0))
        hf.pack(fill=tk.X)

        ttk.Label(hf, text=self.t("color_value")).pack(side=tk.LEFT)

        self._hex_var = tk.StringVar()
        self._hex_entry = ttk.Entry(
            hf, textvariable=self._hex_var,
            font=("Consolas", 11), width=10)
        self._hex_entry.pack(side=tk.LEFT, padx=5)
        self._hex_entry.bind("<Return>", lambda e: self._on_hex_enter())

        # ── 按钮 ──
        bf = ttk.Frame(self, padding=pad)
        bf.pack(fill=tk.X)

        ttk.Button(bf, text=self.t("color_reset"),
                   command=self._reset).pack(side=tk.LEFT, padx=2)

        ttk.Button(bf, text=self.t("color_apply"),
                   command=self._apply).pack(side=tk.RIGHT, padx=2)
        ttk.Button(bf, text=self.t("close"),
                   command=self._close).pack(side=tk.RIGHT, padx=2)

    # ── 同步 ──

    def _sync_all(self):
        self._sync_cells()
        self._sync_hex()
        self._sync_selection()

    def _sync_cells(self):
        for i in range(COLOR_SLOTS):
            c = self._slots[i]
            self._grid_canvas.itemconfig(self._cell_rects[i], fill=c)
            self._grid_canvas.itemconfig(self._cell_labels[i],
                                         fill=self._label_fg(c))

    def _sync_hex(self):
        self._hex_var.set(self._slots[self._active])

    def _sync_selection(self):
        i = self._active
        row, col = divmod(i, self.GRID_COLS)
        x1 = self.GAP + col * (self.CELL_SIZE + self.GAP)
        y1 = self.GAP + row * (self.CELL_SIZE + self.GAP)
        x2 = x1 + self.CELL_SIZE
        y2 = y1 + self.CELL_SIZE
        self._grid_canvas.coords(self._sel_rect,
                                 x1 - 2, y1 - 2, x2 + 2, y2 + 2)

    # ── 事件 ──

    def _on_slot_click(self, idx: int):
        self._active = idx
        self._sync_all()

    def _on_hex_enter(self):
        raw = self._hex_var.get().strip()
        if _HEX_RE.match(raw):
            self._slots[self._active] = raw.upper()
        elif raw == "":
            self._slots[self._active] = "#000000"
        else:
            messagebox.showwarning(
                self.t("color_slot_title"),
                self.t("color_invalid"),
                parent=self,
            )
        self._sync_all()

    def _reset(self):
        self._slots[self._active] = "#000000"
        self._sync_all()

    def _apply(self):
        self.app.color_slots = list(self._slots)
        self.app.active_slot = self._active
        self.app._on_color_changed()
        self.app.save_settings()
        self.destroy()

    def _close(self):
        self.destroy()

    # ── 辅助 ──

    def _label_fg(self, hex_color: str) -> str:
        r = int(hex_color[1:3], 16)
        g = int(hex_color[3:5], 16)
        b = int(hex_color[5:7], 16)
        luminance = 0.299 * r + 0.587 * g + 0.114 * b
        return "#FFFFFF" if luminance < 128 else "#000000"

    def _is_dark(self) -> bool:
        return self.app.theme_name in (
            "典雅黑", "希儿紫", "天依蓝", "初音绿")

    def _center(self, parent):
        self.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width()
                                    - self.winfo_width()) // 2
        y = parent.winfo_rooty() + (parent.winfo_height()
                                    - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")



