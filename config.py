"""配置、国际化、6套主题"""

import json
import os

# ── 常量 ──

VERSION = "1.7"
MAX_BYTES = 30000
BASE_ROWS = 240
SCALE_MAX = 1.0
SCALE_MIN = 0.10
SCALE_STEP = 0.02
MAX_CHARS_IN = 80
MAX_RECENT_FONTS = 10

AUTHOR_GITHUB = "https://github.com/Calvin-Vollerei"
AUTHOR_BILIBILI = "https://space.bilibili.com/400975747"

DEFAULT_UI_FONT = "HarmonyOS Sans SC Bold"
DEFAULT_UI_FONT_FALLBACKS = [
    "HarmonyOS Sans SC", "HarmonyOS_Sans_SC_Bold",
    "HarmonyOS_Sans_SC", "Microsoft YaHei UI Bold",
    "Microsoft YaHei UI", "Segoe UI Bold", "Segoe UI",
]

THEME_NAMES = ["高雅灰", "典雅黑", "简洁白", "希儿紫", "天依蓝", "初音绿"]
THEME_NAMES_EN = ["Gray", "Dark", "White", "Seele", "Tianyi", "Miku"]

THEMES = {
    "高雅灰": {
        "bg": "#f0f0f0", "fg": "#333333",
        "result_bg": "#ffffff", "result_fg": "#222222",
        "entry_bg": "#ffffff", "entry_fg": "#111111",
        "status_bg": "#e0e0e0", "status_fg": "#444444",
        "btn_bg": "#dcdcdc", "btn_fg": "#111111",
        "list_bg": "#ffffff", "list_fg": "#111111",
        "select_bg": "#0078d4", "select_fg": "#ffffff",
        "tab_bg": "#d8d8d8", "tab_fg": "#333333",
        "tab_active_bg": "#f0f0f0",
    },
    "典雅黑": {
        "bg": "#1e1e1e", "fg": "#dddddd",
        "result_bg": "#252525", "result_fg": "#e8e8e8",
        "entry_bg": "#2d2d2d", "entry_fg": "#f0f0f0",
        "status_bg": "#333333", "status_fg": "#bbbbbb",
        "btn_bg": "#3a3a3a", "btn_fg": "#eeeeee",
        "list_bg": "#2d2d2d", "list_fg": "#f0f0f0",
        "select_bg": "#0078d4", "select_fg": "#ffffff",
        "tab_bg": "#2a2a2a", "tab_fg": "#aaaaaa",
        "tab_active_bg": "#1e1e1e",
    },
    "简洁白": {
        "bg": "#ffffff", "fg": "#333333",
        "result_bg": "#f8f8f8", "result_fg": "#222222",
        "entry_bg": "#ffffff", "entry_fg": "#111111",
        "status_bg": "#f0f0f0", "status_fg": "#555555",
        "btn_bg": "#e8e8e8", "btn_fg": "#111111",
        "list_bg": "#ffffff", "list_fg": "#111111",
        "select_bg": "#0078d4", "select_fg": "#ffffff",
        "tab_bg": "#e0e0e0", "tab_fg": "#333333",
        "tab_active_bg": "#ffffff",
    },
    "希儿紫": {
        "bg": "#3d3a63", "fg": "#e0d8f0",
        "result_bg": "#252235", "result_fg": "#e0d8f0",
        "entry_bg": "#2d2a50", "entry_fg": "#f0e8ff",
        "status_bg": "#2a2740", "status_fg": "#c0b8e0",
        "btn_bg": "#4a4780", "btn_fg": "#f0e8ff",
        "list_bg": "#2d2a50", "list_fg": "#f0e8ff",
        "select_bg": "#8b7ec8", "select_fg": "#ffffff",
        "tab_bg": "#2d2a50", "tab_fg": "#c0b8e0",
        "tab_active_bg": "#3d3a63",
    },
    "天依蓝": {
        "bg": "#3a5a78", "fg": "#d8e8f8",
        "result_bg": "#1e2a38", "result_fg": "#d8e8f8",
        "entry_bg": "#243548", "entry_fg": "#f0f8ff",
        "status_bg": "#1e2e3c", "status_fg": "#b0c8e0",
        "btn_bg": "#4a7090", "btn_fg": "#f0f8ff",
        "list_bg": "#243548", "list_fg": "#f0f8ff",
        "select_bg": "#5b9bd5", "select_fg": "#ffffff",
        "tab_bg": "#243548", "tab_fg": "#b0c8e0",
        "tab_active_bg": "#3a5a78",
    },
    "初音绿": {
        "bg": "#2a7a72", "fg": "#d0f0ec",
        "result_bg": "#1a2a28", "result_fg": "#d0f0ec",
        "entry_bg": "#1e3532", "entry_fg": "#e8fff8",
        "status_bg": "#1a2e2a", "status_fg": "#a0d8d0",
        "btn_bg": "#3a9088", "btn_fg": "#e8fff8",
        "list_bg": "#1e3532", "list_fg": "#e8fff8",
        "select_bg": "#4db8ac", "select_fg": "#ffffff",
        "tab_bg": "#1e3532", "tab_fg": "#a0d8d0",
        "tab_active_bg": "#2a7a72",
    },
}


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
        "title": "JNO通用输入法",
        "input_label": "输入文本:",
        "font_label": "字体:",
        "font_auto": "（自动选择）",
        "font_recent": "── 最近使用 ──",
        "font_all": "── 全部字体 ──",
        "font_search": "搜索字体...",
        "search_btn": "搜索",
        "vertical": "竖排",
        "byte_limit": "字节上限:",
        "style": "样式",
        "style_normal": "常规",
        "style_bold": "加粗",
        "style_italic": "斜体",
        "style_bold_italic": "粗斜体",
        "newline_hint": "（Enter 换行，Ctrl+Enter 生成）",
        "generate": "生成",
        "generating": "生成中...",
        "ready": "就绪",
        "copy": "复制到剪贴板",
        "save": "保存到文件",
        "clear": "清空",
        "copied": "已复制",
        "saved": "已保存: {}",
        "cleared": "已清空",
        "no_content": "没有内容可{}",
        "input_warning": "请输入文本",
        "error": "错误",
        "missing_pillow": "请先安装 pillow:\npip install pillow",
        "settings": "通用",
        "language": "语言",
        "theme": "主题",
        "close_action": "关闭窗口时:",
        "close_exit": "退出程序",
        "close_minimize": "最小化到任务栏",
        "font_manager": "字体管理",
        "font_manager_title": "字体管理",
        "font_enable_all": "全选",
        "font_disable_all": "全不选",
        "font_filter": "搜索字体...",
        "font_count": "已启用 {}/{} 个字体",
        "font_applied": "修改已应用",
        "font_unsaved": "有未保存的修改。\n\n是否放弃修改并关闭？",
        "about": "关于",
        "about_title": "关于 JNO通用输入法",
        "about_text": (
            "JNO通用输入法 v{version}\n\n"
            "将文字转换为适用于JNO Label的形式。\n"
            "基于 PIL 渲染 + 最近邻降采样，\n"
            "支持全 Windows 字体库。\n\n"
            "Calvin Vollerei Studio\n"
            "All rights Reserved（2022-2026）"
        ),
        "github": "GitHub",
        "bilibili": "B站主页",
        "copyright": "Calvin Vollerei Studio All rights Reserved（2022-2026）",
        "done": "完成 — {}行, {}B",
        "fonts_total": "共 {} 个字体",
        "apply": "应用",
        "close": "关闭",
        "no_font": "未找到 HarmonyOS Sans SC Bold，使用备用字体",
        "help": "帮助",
        "help_title": "JNO通用输入法 — 帮助",
        "help_text": (
            "【快捷键】\n"
            "  Enter         —  输入框中换行\n"
            "  Ctrl+Enter    —  生成点阵\n"
            "  搜索框回车     —  搜索字体并弹出下拉\n\n"
            "【功能】\n"
            "  字体搜索  —  在搜索框输入关键字，点击搜索按钮\n"
            "  字体管理  —  通用 → 字体管理，勾选启用的字体\n"
            "  样式      —  常规 / 加粗 / 斜体 / 粗斜体\n"
            "  横排/竖排 —  勾选「竖排」切换排版方向\n"
            "  主题      —  通用中选择 6 套配色\n"
            "  字节上限  —  控制输出大小，自动缩放适配\n\n"
            "【输出】\n"
            "  输出结果可粘贴到JNO Label\n"
            "  也可保存为 .txt 文件"
        ),
        "update": "检查更新",
        "update_checking": "正在检查更新...",
        "update_latest": "当前已是最新版本 v{}",
        "update_available": "发现新版本 v{}\n当前版本 v{}\n\n是否前往下载？",
        "update_error": "检查更新失败：{}",
        "version": "版本",
        "history": "历史记录",
        "history_title": "历史记录与收藏",
        "history_tab_recent": "历史记录",
        "history_tab_favorites": "收藏",
        "history_empty": "暂无记录",
        "history_fav_empty": "暂无收藏",
        "history_copy": "复制",
        "history_fav": "收藏",
        "history_unfav": "取消收藏",
        "history_clear_all": "清空历史",
        "history_fav_added": "已加入收藏",
        "history_fav_removed": "已取消收藏",
        "history_cleared": "历史记录已清空",
    },
    "en": {
        "title": "JNO Input Method",
        "input_label": "Input Text:",
        "font_label": "Font:",
        "font_auto": "(Auto Select)",
        "font_recent": "── Recent ──",
        "font_all": "── All Fonts ──",
        "font_search": "Search fonts...",
        "search_btn": "Search",
        "vertical": "Vertical",
        "byte_limit": "Byte Limit:",
        "style": "Style",
        "style_normal": "Normal",
        "style_bold": "Bold",
        "style_italic": "Italic",
        "style_bold_italic": "Bold Italic",
        "newline_hint": "(Enter for newline, Ctrl+Enter to generate)",
        "generate": "Generate",
        "generating": "Generating...",
        "ready": "Ready",
        "copy": "Copy",
        "save": "Save",
        "clear": "Clear",
        "copied": "Copied",
        "saved": "Saved: {}",
        "cleared": "Cleared",
        "no_content": "No content to {}",
        "input_warning": "Please enter text",
        "error": "Error",
        "missing_pillow": "Please install pillow:\npip install pillow",
        "settings": "General",
        "language": "Language",
        "theme": "Theme",
        "close_action": "On window close:",
        "close_exit": "Exit",
        "close_minimize": "Minimize to taskbar",
        "font_manager": "Font Manager",
        "font_manager_title": "Font Manager",
        "font_enable_all": "Select All",
        "font_disable_all": "Deselect All",
        "font_filter": "Search...",
        "font_count": "Enabled {}/{} fonts",
        "font_applied": "Changes applied",
        "font_unsaved": "Unsaved changes.\n\nDiscard and close?",
        "about": "About",
        "about_title": "About JNO Input Method",
        "about_text": (
            "JNO Input Method v{version}\n\n"
            "Convert text to JNO Label format.\n"
            "Based on PIL + nearest-neighbor,\n"
            "Full Windows font library.\n\n"
            "Calvin Vollerei Studio\n"
            "All rights Reserved (2022-2026)"
        ),
        "github": "GitHub",
        "bilibili": "Bilibili",
        "copyright": "Calvin Vollerei Studio All rights Reserved (2022-2026)",
        "done": "Done — {} lines, {}B",
        "fonts_total": "Total {} fonts",
        "apply": "Apply",
        "close": "Close",
        "no_font": "HarmonyOS Sans SC Bold not found, using fallback",
        "help": "Help",
        "help_title": "JNO Input Method — Help",
        "help_text": (
            "[Shortcuts]\n"
            "  Enter          —  New line in input box\n"
            "  Ctrl+Enter     —  Generate dot art\n"
            "  Enter in search —  Search fonts & popup list\n\n"
            "[Features]\n"
            "  Font Search  —  Type keyword in search box, click Search\n"
            "  Font Manager —  General → Font Manager, check enabled fonts\n"
            "  Style        —  Normal / Bold / Italic / Bold Italic\n"
            "  Horizontal/Vertical — Check 「Vertical」to switch\n"
            "  Theme        —  Choose from 6 color schemes\n"
            "  Byte Limit   —  Auto-scale output to fit\n\n"
            "[Output]\n"
            "  Output can be pasted to JNO Label\n"
            "  Or saved as .txt file"
        ),
        "update": "Check Update",
        "update_checking": "Checking for updates...",
        "update_latest": "You are on the latest version v{}",
        "update_available": "New version v{} available\nCurrent version v{}\n\nGo to download?",
        "update_error": "Update check failed: {}",
        "version": "Version",
        "history": "History",
        "history_title": "History & Favorites",
        "history_tab_recent": "Recent",
        "history_tab_favorites": "Favorites",
        "history_empty": "No history",
        "history_fav_empty": "No favorites",
        "history_copy": "Copy",
        "history_fav": "Favorite",
        "history_unfav": "Unfavorite",
        "history_clear_all": "Clear History",
        "history_fav_added": "Added to favorites",
        "history_fav_removed": "Removed from favorites",
        "history_cleared": "History cleared",
    },
}
