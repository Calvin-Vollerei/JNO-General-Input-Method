"""配置、国际化、主题色"""

import json
import os

MAX_BYTES          = 30000
BASE_ROWS          = 240
SCALE_MAX          = 1.0
SCALE_MIN          = 0.10
SCALE_STEP         = 0.02
MAX_CHARS_IN       = 80
MAX_RECENT_FONTS   = 10

AUTHOR_GITHUB   = "https://github.com/Calvin-Vollerei"
AUTHOR_BILIBILI = "https://space.bilibili.com/400975747"

def _config_dir():
    d = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")),
                     "JNO-Input-Method")
    os.makedirs(d, exist_ok=True)
    return d

def load_config():
    path = os.path.join(_config_dir(), "settings.json")
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def save_config(cfg: dict):
    path = os.path.join(_config_dir(), "settings.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)

T = {
    "zh": {
        "title":              "JNO通用输入法",
        "input_label":        "输入文本:",
        "font_label":         "字体:",
        "font_auto":          "（自动选择）",
        "font_recent":        "── 最近使用 ──",
        "font_all":           "── 全部字体 ──",
        "font_search":        "搜索字体...",
        "vertical":           "竖排",
        "byte_limit":         "字节上限:",
        "style":              "样式:",
        "style_normal":       "常规",
        "style_bold":         "加粗",
        "style_italic":       "斜体",
        "style_bold_italic":  "粗斜体",
        "newline_hint":       "（Enter 换行，Ctrl+Enter 生成）",
        "generate":           "生成",
        "generating":         "生成中...",
        "ready":              "就绪",
        "copy":               "复制到剪贴板",
        "save":               "保存到文件",
        "clear":              "清空",
        "copied":             "已复制",
        "saved":              "已保存: {}",
        "cleared":            "已清空",
        "no_content":         "没有内容可{}",
        "input_warning":      "请输入文本",
        "error":              "错误",
        "missing_pillow":     "请先安装 pillow:\npip install pillow",
        "settings":           "设置",
        "language":           "语言",
        "theme":              "主题",
        "theme_light":        "浅色",
        "theme_dark":         "深色",
        "font_manager":       "字体管理",
        "font_manager_title": "字体管理",
        "font_enable_all":    "全选",
        "font_disable_all":   "全不选",
        "font_filter":        "搜索字体...",
        "font_count":         "已启用 {}/{} 个字体",
        "font_applied":       "修改已应用",
        "font_unsaved":       "有未保存的修改。\n\n是否放弃修改并关闭？",
        "about":              "关于",
        "about_title":        "关于 JNO通用输入法",
        "about_text":         "JNO通用输入法 v1.3\n\n将文字转换为适用于JNO Lable的形式\n基于 PIL 渲染 + 最近邻降采样\n支持全 Windows 字体库\n\nCalvin Vollerei Studio All rights Reserved（2022-2026）",
        "github":             "GitHub",
        "bilibili":           "B站主页",
        "copyright":          "Calvin Vollerei Studio 2022-2026 All Rights Reserved.",
        "done":               "完成 — {}行, {}B",
        "fonts_total":        "共 {} 个字体",
    },
    "en": {
        "title":              "JNO Input Method",
        "input_label":        "Input Text:",
        "font_label":         "Font:",
        "font_auto":          "(Auto Select)",
        "font_recent":        "── Recent ──",
        "font_all":           "── All Fonts ──",
        "font_search":        "Search fonts...",
        "vertical":           "Vertical",
        "byte_limit":         "Byte Limit:",
        "style":              "Style:",
        "style_normal":       "Normal",
        "style_bold":         "Bold",
        "style_italic":       "Italic",
        "style_bold_italic":  "Bold Italic",
        "newline_hint":       "(Enter for newline, Ctrl+Enter to generate)",
        "generate":           "Generate",
        "generating":         "Generating...",
        "ready":              "Ready",
        "copy":               "Copy",
        "save":               "Save",
        "clear":              "Clear",
        "copied":             "Copied",
        "saved":              "Saved: {}",
        "cleared":            "Cleared",
        "no_content":         "No content to {}",
        "input_warning":      "Please enter text",
        "error":              "Error",
        "missing_pillow":     "Please install pillow:\npip install pillow",
        "settings":           "Settings",
        "language":           "Language",
        "theme":              "Theme",
        "theme_light":        "Light",
        "theme_dark":         "Dark",
        "font_manager":       "Font Manager",
        "font_manager_title": "Font Manager",
        "font_enable_all":    "Select All",
        "font_disable_all":   "Deselect All",
        "font_filter":        "Search...",
        "font_count":         "Enabled {}/{} fonts",
        "font_applied":       "Changes applied",
        "font_unsaved":       "Unsaved changes.\n\nDiscard and close?",
        "about":              "About",
        "about_title":        "About JNO Input Method",
        "about_text":      (             
            "JNO Input Method v1.3\n\n"
            "Convert text to JNO Label format.\n"
            "Based on PIL + nearest-neighbor,\n"
            "Full Windows font library.\n\n"
            "Calvin Vollerei Studio\n"
            "All rights Reserved (2022-2026)"
        ),
        "github":             "GitHub",
        "bilibili":           "Bilibili",
        "copyright":          "Calvin Vollerei Studio 2022-2026 All Rights Reserved.",
        "done":               "Done — {} lines, {}B",
        "fonts_total":        "Total {} fonts",
    },
}

LIGHT_THEME = {
    "bg":        "#f0f0f0", "fg": "#333333",
    "result_bg": "#ffffff", "result_fg": "#333333",
    "entry_bg":  "#ffffff", "entry_fg": "#000000",
    "status_bg": "#e0e0e0", "status_fg": "#555555",
    "btn_bg":    "#e0e0e0", "btn_fg": "#000000",
    "list_bg":   "#ffffff", "list_fg": "#000000",
}

DARK_THEME = {
    "bg":        "#1e1e1e", "fg": "#cccccc",
    "result_bg": "#252525", "result_fg": "#dddddd",
    "entry_bg":  "#2d2d2d", "entry_fg": "#ffffff",
    "status_bg": "#333333", "status_fg": "#aaaaaa",
    "btn_bg":    "#3a3a3a", "btn_fg": "#dddddd",
    "list_bg":   "#2d2d2d", "list_fg": "#dddddd",
}
