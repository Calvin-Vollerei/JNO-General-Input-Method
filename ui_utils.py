"""UI 辅助：圆角、字体注册"""

import os
import sys
import tkinter as tk


def apply_round_corners(root: tk.Tk):
    """Windows 11 DWM 窗口圆角"""
    if sys.platform != "win32":
        return
    try:
        import ctypes
        hwnd = root.winfo_id()
        corner_pref = ctypes.c_int(2)  # DWMWCP_ROUND
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            ctypes.wintypes.HWND(hwnd), 33,
            ctypes.byref(corner_pref), ctypes.sizeof(corner_pref))
    except Exception:
        pass


def register_ui_font(root: tk.Tk, font_path: str) -> str:
    """
    注册 HarmonyOS Sans SC Bold 为 tk 可用字体。
    成功返回 "JNOSans"，失败返回 "TkDefaultFont"。
    """
    if not font_path or not os.path.exists(font_path):
        return "TkDefaultFont"
    try:
        from PIL import ImageFont as _IF
        _IF.truetype(font_path, 12)
        root.tk.call("font", "create", "JNOSans",
                     "-family", "HarmonyOS Sans SC",
                     "-size", 10, "-weight", "bold")
        return "JNOSans"
    except Exception:
        return "TkDefaultFont"
