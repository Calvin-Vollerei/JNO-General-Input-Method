"""配置、国际化、6套主题"""

import json
import os

# ── 常量 ──

VERSION = "1.8"
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


# ── 字节上限分段档位 ──

def build_byte_values():
    vals = []
    for v in range(100, 1000 + 1, 100):
        vals.append(v)
    for v in range(2000, 10000 + 1, 1000):
        vals.append(v)
    for v in range(15000, 30000 + 1, 5000):
        vals.append(v)
    return vals


BYTE_VALUES = build_byte_values()
BYTE_WARN_THRESHOLD = 15000
COLOR_SLOTS = 25


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
            "将文字渲染为 ASCII 点阵，输出格式兼容\n"
            "JNO Label 插件（Jpixel 格式）。\n"
            "基于 PIL 高分辨率渲染 + 最近邻降采样，\n"
            "支持全 Windows 系统字体库。\n\n"
            "特性：\n"
            "  • 横排 / 竖排\n"
            "  • 常规 / 加粗 / 斜体 / 粗斜体\n"
            "  • 6 套界面主题\n"
            "  • 中英双语界面\n"
            "  • 25 色墨水槽位（对应 JNO Label 色板）\n"
            "  • 历史记录与收藏\n"
            "  • 字节上限自适应缩放\n\n"
            "Calvin Vollerei Studio（2022-2026）"
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
            "  Enter              —  输入框中换行\n"
            "  Ctrl+Enter         —  生成点阵\n"
            "  搜索框回车          —  搜索字体并弹出下拉\n\n"
            "【文本输入】\n"
            "  支持任意语言文字（中日韩、拉丁等）。\n"
            "  单次最多 80 字符，超出自动截断。\n"
            "  Enter 换行，Ctrl+Enter 生成。\n\n"
            "【字体】\n"
            "  搜索框输入关键字 → 点击「搜索」或回车。\n"
            "  下拉列表按「最近使用 / 全部字体」分组。\n"
            "  通过 通用 → 字体管理 可启用/禁用字体。\n\n"
            "【样式】\n"
            "  常规 / 加粗 / 斜体 / 粗斜体。\n"
            "  优先使用字体内置变体文件，无变体则代码模拟。\n\n"
            "【排版方向】\n"
            "  横排：从左到右逐行输出。\n"
            "  竖排：从上到下逐字排列。\n\n"
            "【颜色】\n"
            "  点击色块打开 5×5 颜色槽位面板。\n"
            "  25 个槽位对应 JNO Label 预定义墨水槽。\n"
            "  点击槽位选中，输入 #RRGGBB 染色（仅可视化）。\n"
            "  输出中使用 JNO 槽位标识符 <#000000> ~ <#181818>。\n"
            "  点击「应用」生效，「重置」将当前槽位恢复黑色。\n\n"
            "【字节上限】\n"
            "  控制输出总大小，程序自动缩放适配。\n"
            "  下拉提供分段建议值（100~30000），也可双击自行输入。\n"
            "  超过 15000 字节将弹出性能警告。\n\n"
            "【输出格式】\n"
            "  输出为 Jpixel 格式，可直接粘贴到 JNO Label。\n"
            "  长空格自动合并为 <space=N> 标签以节约字节。\n"
            "  也可保存为 .txt 文件。\n\n"
            "【主题】\n"
            "  通用 中选择：高雅灰 / 典雅黑 / 简洁白 /\n"
            "  希儿紫 / 天依蓝 / 初音绿。即时生效。"
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
        "color_label": "颜色:",
        "color_slot_title": "颜色槽位",
        "color_value": "颜色值:",
        "color_apply": "应用",
        "color_reset": "重置",
        "color_none": "（默认黑）",
        "color_invalid": "无效的颜色格式（需 #RRGGBB）",
        "byte_warn": "⚠ 输出较大，可能影响性能",
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
            "Converts text to ASCII dot art compatible with\n"
            "JNO Label plugin (Jpixel format).\n"
            "Uses PIL high-res rendering + nearest-neighbor\n"
            "downscaling. Supports all Windows system fonts.\n\n"
            "Features:\n"
            "  • Horizontal / Vertical layout\n"
            "  • Normal / Bold / Italic / Bold Italic styles\n"
            "  • 6 UI themes\n"
            "  • Chinese / English UI\n"
            "  • 25 ink slots (JNO Label palette)\n"
            "  • History & Favorites\n"
            "  • Byte limit with auto-scaling\n\n"
            "Calvin Vollerei Studio (2022-2026)"
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
            "  Enter              —  New line in input box\n"
            "  Ctrl+Enter         —  Generate dot art\n"
            "  Enter in search    —  Search fonts & show list\n\n"
            "[Text Input]\n"
            "  Supports all languages (CJK, Latin, etc.).\n"
            "  Max 80 chars per generation (auto-truncated).\n"
            "  Enter for newline, Ctrl+Enter to generate.\n\n"
            "[Fonts]\n"
            "  Type keyword in search box → click Search or Enter.\n"
            "  Dropdown grouped by Recent / All Fonts.\n"
            "  Enable/disable fonts via General → Font Manager.\n\n"
            "[Style]\n"
            "  Normal / Bold / Italic / Bold Italic.\n"
            "  Uses native font variants if available,\n"
            "  falls back to software simulation.\n\n"
            "[Layout]\n"
            "  Horizontal: left-to-right line by line.\n"
            "  Vertical: top-to-bottom character by character.\n\n"
            "[Color]\n"
            "  Click the color swatch to open 5×5 slot panel.\n"
            "  25 slots mapped to JNO Label predefined ink slots.\n"
            "  Click a slot to select, enter #RRGGBB to colorize\n"
            "  (visual preview only, output uses slot ID).\n"
            "  Output format: <#000000> ~ <#181818>.\n"
            "  Click Apply to confirm, Reset to clear current slot.\n\n"
            "[Byte Limit]\n"
            "  Controls max output size — auto-scales to fit.\n"
            "  Dropdown provides suggested values (100~30000).\n"
            "  You may also double click to type a custom value.\n"
            "  Warning shown above 15000 bytes.\n\n"
            "[Output Format]\n"
            "  Output is Jpixel format, paste directly into JNO Label.\n"
            "  Long spaces auto-merged to <space=N> to save bytes.\n"
            "  Can also be saved as .txt file.\n\n"
            "[Themes]\n"
            "  General → choose from: Gray / Dark / White /\n"
            "  Seele / Tianyi / Miku. Instant apply."
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
        "color_label": "Color:",
        "color_slot_title": "Color Slots",
        "color_value": "Color Value:",
        "color_apply": "Apply",
        "color_reset": "Reset",
        "color_none": "(Default Black)",
        "color_invalid": "Invalid color format (use #RRGGBB)",
        "byte_warn": "⚠ Large output, may affect performance",
    },
}


