#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
把 Ubuntu 26.04 / GNOME 50 桌面调成 macOS 风格。
可随时一键还原。

用法：
  python3 macos-look.py deps        # 检查系统与依赖
  python3 macos-look.py assets      # 下载字体/图标/光标/壁纸/苹果 logo
  python3 macos-look.py install-ext # 下载安装全部 GNOME 扩展
  python3 macos-look.py patch-ext   # 给有已知缺陷的上游扩展打本地补丁
  python3 macos-look.py apply       # 应用 macOS 风格设置(幂等)
  python3 macos-look.py prepare     # 注册扩展参数表 + 写扩展配置 + 更新自启动清单
  python3 macos-look.py enable-ext  # 注销重登后启用全部扩展
  python3 macos-look.py backup      # 备份当前设置(装前自动执行，勿重复覆盖)
  python3 macos-look.py status      # 查看当前各项设置
  python3 macos-look.py revert      # 一键还原到安装前状态

首次安装直接跑 install.sh 即可，它会按正确顺序调用上面的命令。
"""
import json
import os
import shlex
import subprocess
import sys
import urllib.request

HOME = os.path.expanduser("~")
BACKUP = os.path.join(HOME, ".config/macos-look/backup.json")
EXT_DIR = os.path.join(HOME, ".local/share/gnome-shell/extensions")
UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64)"}

SCHEMAS = [
    "org.gnome.shell.extensions.dash-to-dock",
    "org.gnome.desktop.wm.preferences",
    "org.gnome.desktop.wm.keybindings",
    "org.gnome.desktop.interface",
    "org.gnome.desktop.background",
    "org.gnome.desktop.peripherals.touchpad",
    "org.gnome.shell.keybindings",
    "org.gnome.nautilus.preferences",
    "org.gnome.shell",
]

BG_DIR = os.path.join(HOME, ".local/share/backgrounds")

# 扩展清单: (pk, uuid, 名字, 是否启用)
# 注: 原版 Dash to Dock 与系统自带的 Ubuntu Dock 同源同版本(105)，
#     GNOME 45+ 上游已删除"图标悬停放大"，故不再替换系统 Dock。
EXTS = [
    (3193, "blur-my-shell@aunetx",                    "Blur my Shell(毛玻璃顶栏)",   True),
    (3843, "just-perfection-desktop@just-perfection", "Just Perfection(顶栏精调)",   True),
    (4451, "logomenu@aryan_k",                        "Logo Menu(左上角苹果菜单)",   True),
    (9529, "magnific-launcher@gilsonf",               "Magnific Launcher(Dock 悬停放大)", True),
    (7048, "rounded-window-corners@fxgn",             "Rounded Window Corners(窗口圆角)", True),
    (3740, "compiz-alike-magic-lamp-effect@hermes83.github.com", "魔法灯最小化动画", True),
    # 第三轮：向 macOS 菜单栏 / Spotlight / 锁屏 / 自动深浅色 靠
    (10288, "globalmenu@ShiroOSL.github.io",            "Global Menu(macOS 式全局菜单栏)", True),
    (10319, "window-title-pro@eprahemi.github.io",      "Window Title Pro(顶栏显示当前应用名)", True),
    (4356, "top-bar-organizer@julian.gse.jsts.xyz",     "Top Bar Organizer(顶栏元素排序)", True),
    (10666, "spotlight@nin",                            "Spotlight(Spotlight 式启动器)", True),
    (9713, "wack-lockscreen-clock@rinzler69-wastaken.github.com", "WACK Sonoma(锁屏)", True),
    (2236, "nightthemeswitcher@romainvigier.fr",        "Night Theme Switcher(日落自动切深浅色)", True),
]

# Just Perfection 的 macOS 化配置
JP_SCHEMA = "org.gnome.shell.extensions.just-perfection"
JP_APPLY = {
    "activities-button": False,   # 隐藏左上角"活动"文字，位置让给苹果 logo
    "workspace": False,           # 隐藏顶栏工作区指示圆点
    "window-picker-icon": False,  # 隐藏顶栏"窗口"指示器
    "clock-menu-position": 1,     # 时钟移到最右端(0=中 1=右 2=左)
    "type-to-search": True,       # 打开总览即可直接输入搜索 = Spotlight
}

# Logo Menu：左上角换成苹果 logo
LOGO_SCHEMA = "org.gnome.shell.extensions.logo-menu"
LOGO_ICON = os.path.join(HOME, ".local/share/icons/apple-logo-symbolic.svg")
LOGO_APPLY = {
    "use-custom-icon": True,
    "custom-icon-path": LOGO_ICON,
    "symbolic-icon": True,          # 图标跟随顶栏颜色
    "show-activities-button": False,  # 不显示"活动"文字
    "menu-button-icon-size": 22,
    # 苹果菜单里必须有电源与锁屏项 —— 否则"注销/重启/关机"在菜单里找不到
    # （这是 macOS 苹果菜单的标准内容，也是本机唯一顺手的注销入口）
    "show-power-options": True,
    "show-lockscreen": True,
}

# 第三轮：macOS 菜单栏 / Spotlight / 通知位置 / 自动深浅色
ROUND3 = {
    "org.gnome.shell.extensions.just-perfection": {
        "notification-banner-position": 2,   # 通知弹到右上角(0顶左 1顶中 2顶右)
        "panel-size": 26,                     # 顶栏压到 26px（默认约 32，macOS 约 24）
    },
    "org.gnome.shell.extensions.spotlight": {
        "toggle-shortcut": ["<Super>space"],  # 同 macOS 的 Cmd+Space
    },
    "org.gnome.shell.extensions.window-title-pro": {
        "font-size": 13,                      # macOS 菜单栏字号
        "show-app": True,
        "show-title": False,                  # 只显示应用名，不显示窗口标题
        "toggle-shortcut": [],                # 别占 Super+Y
    },
    "org.gnome.shell.extensions.globalmenu": {
        "show-logo-menu": False,              # 苹果 logo 交给 Logo Menu，避免两个 logo
        "hide-overview-button": True,         # 隐藏"活动"按钮
        "terminal-command": "ptyxis",
        "system-monitor-command": "resources",
        "software-center-command": "snap-store",
        "show-force-quit": True,
        "show-lock-screen": True,
    },
    "org.gnome.shell.extensions.nightthemeswitcher.time": {
        "location": "(121.47, 31.23)",        # 按系统时区 Asia/Shanghai 取上海
    },
    "org.gnome.shell.extensions.top-bar-organizer": {
        # GNOME 默认顺序把时钟排在右上角各种图标之前，macOS 是时钟在最右
        "right-box-order": ["a11y", "keyboard", "quickSettings", "dateMenu"],
    },
    "org.gnome.desktop.wm.keybindings": {
        "switch-input-source": [],            # 让出 Super+Space 给 Spotlight
        "toggle-fullscreen": ["<Super><Control>f"],   # 同 macOS 的 ⌃⌘F
    },
    "org.gnome.desktop.interface": {
        "monospace-font-name": "JetBrains Mono 11",
    },
}

# macOS 风格设置: schema -> {key: value}
APPLY = {
    "org.gnome.shell.extensions.dash-to-dock": {
        "dock-position": "BOTTOM",        # Dock 到底部
        "dock-fixed": True,               # 常驻显示(与 macOS 默认一致)
        "autohide": False,
        "intellihide": False,
        "extend-height": False,           # 底部 Dock 不拉通整屏
        "always-center-icons": True,      # 图标居中
        "dash-max-icon-size": 48,
        "icon-size-fixed": True,
        "custom-theme-shrink": True,
        "transparency-mode": "DYNAMIC",
        "background-opacity": 0.75,
        "min-alpha": 0.2,
        "max-alpha": 0.9,
        "running-indicator-style": "DOTS",  # 运行中应用下面的小圆点
        "show-show-apps-button": True,      # 启动台按钮
        "show-apps-at-top": False,          # 启动台放末尾
        "show-trash": True,                 # 垃圾桶
        "show-mounts": True,                # 挂载的磁盘/U盘
        "click-action": "focus-or-appspread",
        "middle-click-action": "launch",
        "scroll-action": "switch-workspace",
        "animation-time": 0.15,
        "autohide-in-fullscreen": False,
        "require-pressure-to-show": False,
        "show-delay": 0.05,
        "hide-delay": 0.2,
        "preview-size-scale": 0.35,
    },
    "org.gnome.desktop.wm.preferences": {
        "button-layout": "close,minimize,maximize:",  # 红黄绿灯挪到左上角
    },
    "org.gnome.desktop.background": {
        "picture-options": "zoom",
        "picture-uri": "file://" + os.path.join(BG_DIR, "Monterey-light.jpg"),
        "picture-uri-dark": "file://" + os.path.join(BG_DIR, "Monterey-dark.jpg"),
    },
    "org.gnome.desktop.wm.keybindings": {
        # 把 macOS 的 Cmd 组合键映射到 Super 键（原绑定保留，不夺）
        "close": ["<Alt>F4", "<Super>w"],                          # Cmd+W 关窗口
        "minimize": ["<Super>h", "<Super>m"],                      # Cmd+M 最小化
        "switch-windows": ["<Alt>Tab", "<Super>grave"],            # Cmd+` 切同应用窗口
        "switch-windows-backward": ["<Shift><Alt>Tab", "<Super>asciitilde"],
    },
    "org.gnome.desktop.interface": {
        "show-battery-percentage": True,
        "clock-show-weekday": True,
        "enable-hot-corners": True,   # 左上角触发角 = macOS 的 Mission Control
        "locate-pointer": True,       # 摇鼠标高亮光标 = macOS 的"晃动查找指针"
        "font-name": "Inter 11",
        "document-font-name": "Inter 11",
        "font-antialiasing": "rgba",
        "font-hinting": "slight",
        "icon-theme": "WhiteSur",              # macOS 风格图标
        "cursor-theme": "WhiteSur-cursors",    # macOS 风格指针
        "cursor-size": 24,
    },
    "org.gnome.nautilus.preferences": {
        "always-use-location-entry": True,  # 常显路径栏，像 Finder
    },
    "org.gnome.shell.keybindings": {
        "show-screenshot-ui": ["Print", "<Super><Shift>4"],        # 类 Cmd+Shift+4 区域截图
        "screenshot": ["<Shift>Print", "<Super><Shift>3"],         # 类 Cmd+Shift+3 全屏截图
    },
}


def sh(args, check=False):
    r = subprocess.run(args, capture_output=True, text=True)
    if check and r.returncode != 0:
        raise RuntimeError(" ".join(args) + "\n" + r.stderr)
    return r


def gset(schema, key, value):
    if isinstance(value, bool):
        v = "true" if value else "false"
    elif isinstance(value, (int, float)):
        v = str(value)
    elif isinstance(value, list):
        v = json.dumps(value)
    else:
        v = str(value)
    r = sh(["gsettings", "set", schema, key, v])
    if r.returncode != 0:
        print("  ✗ %s %s = %s  (%s)" % (schema.split(".")[-1], key, v, r.stderr.strip()))
        return False
    print("  ✓ %s.%s = %s" % (schema.split(".")[-1], key, v))
    return True


def cmd_backup():
    data = {}
    for s in SCHEMAS:
        data[s] = sh(["gsettings", "list-recursively", s]).stdout
    os.makedirs(os.path.dirname(BACKUP), exist_ok=True)
    with open(BACKUP, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print("已备份当前桌面设置 ->", BACKUP)


def cmd_revert():
    if not os.path.exists(BACKUP):
        print("找不到备份文件:", BACKUP)
        return 1
    with open(BACKUP, encoding="utf-8") as f:
        data = json.load(f)
    n = 0
    bad = 0
    for schema, text in data.items():
        for line in text.splitlines():
            try:
                parts = shlex.split(line)
            except ValueError:
                continue
            if len(parts) < 3:
                continue
            s, k = parts[0], parts[1]
            raw = line.split(" ", 2)[2].strip()
            if raw.startswith("@as"):
                raw = raw[3:].strip() or "[]"
            r = sh(["gsettings", "set", s, k, raw])
            if r.returncode == 0:
                n += 1
            else:
                bad += 1
    print("已还原 %d 项设置%s" % (n, "" if bad == 0 else "(有 %d 项跳过)" % bad))
    # 扩展自身的参数重置为出厂默认
    for extra in (JP_SCHEMA, LOGO_SCHEMA, "org.gnome.shell.extensions.blur-my-shell"):
        if sh(["gsettings", "list-keys", extra]).returncode == 0:
            sh(["gsettings", "reset-recursively", extra])
            print("  已重置 %s 为默认" % extra)
    print("扩展本身如需停用： gnome-extensions disable <uuid>（uuid 见 gnome-extensions list）")
    return 0


def cmd_apply():
    print("== 应用 macOS 风格设置 ==")
    for schema, kv in APPLY.items():
        print("[%s]" % schema)
        for k, v in kv.items():
            gset(schema, k, v)
    # 清理收藏栏里的"安装 Ubuntu"图标
    fav = sh(["gsettings", "get", "org.gnome.shell", "favorite-apps"]).stdout.strip()
    try:
        apps = json.loads(fav.replace("@as", "").replace("'", '"'))
    except Exception:
        apps = None
    if apps:
        cleaned = [a for a in apps if "ubuntu-desktop-bootstrap" not in a and "org.gnome.Yelp" not in a]
        if cleaned != apps:
            gset("org.gnome.shell", "favorite-apps", cleaned)
    print("\n完成。窗口按钮已是左上角红黄绿，Dock 已移到底部居中。")
    return 0


def fetch_info(pk):
    url = "https://extensions.gnome.org/extension-info/?pk=%d&shell_version=50" % pk
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as r:
        return json.load(r)


def cmd_install_ext():
    os.makedirs(EXT_DIR, exist_ok=True)
    ok = []
    for pk, uuid, name, _ in EXTS:
        print("== %s ==" % name)
        try:
            info = fetch_info(pk)
        except Exception as e:
            print("  查询失败:", e)
            continue
        svm = info.get("shell_version_map", {})
        if "50" not in svm:
            print("  跳过: 不支持 GNOME 50")
            continue
        url = "https://extensions.gnome.org" + info["download_url"]
        tmp = "/tmp/%s.zip" % uuid
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=90) as r, open(tmp, "wb") as f:
                f.write(r.read())
        except Exception as e:
            print("  下载失败:", e)
            continue
        target = os.path.join(EXT_DIR, uuid)
        if os.path.exists(os.path.join(target, "metadata.json")):
            print("  已装过，跳过")
            ok.append(uuid)
            continue
        os.makedirs(target, exist_ok=True)
        r = sh(["unzip", "-o", "-q", tmp, "-d", target])
        if r.returncode != 0:
            print("  解压失败:", r.stderr.strip())
            continue
        # 元数据校验
        meta_path = os.path.join(target, "metadata.json")
        if not os.path.exists(meta_path):
            print("  解压后没有 metadata.json，跳过")
            continue
        with open(meta_path, encoding="utf-8") as f:
            meta = json.load(f)
        sv = meta.get("shell-version", [])
        # 编译扩展自带的 gsettings schema
        sch = os.path.join(target, "schemas")
        if os.path.isdir(sch) and sh(["bash", "-c", "command -v glib-compile-schemas"]).returncode == 0:
            sh(["glib-compile-schemas", sch])
        print("  已安装 v%s  声明支持: %s" % (info.get("version"), ",".join(sv)))
        ok.append(uuid)
    print("\n已就位 %d 个扩展 (目录 %s)" % (len(ok), EXT_DIR))
    print("下一步：注销并重新登录一次，然后说一声，我来启用它们。")
    return 0


def install_schemas():
    """把扩展自带的 gsettings schema 装到用户目录，这样命令行也能直接调参数"""
    src_root = os.path.join(HOME, ".local/share/glib-2.0/schemas")
    os.makedirs(src_root, exist_ok=True)
    n = 0
    for pk, uuid, name, on in EXTS:
        sch = os.path.join(EXT_DIR, uuid, "schemas")
        if not os.path.isdir(sch):
            continue
        for f in os.listdir(sch):
            if f.endswith(".gschema.xml"):
                sh(["cp", "-f", os.path.join(sch, f), os.path.join(src_root, f)])
                n += 1
    if n:
        sh(["glib-compile-schemas", src_root])
    print("  已注册 %d 个扩展参数表 -> %s" % (n, src_root))
    return n


def cmd_prepare():
    """注销前准备：注册参数表、写好 macOS 化参数、清理重复的 Dock 扩展"""
    print("== 注销前的准备 ==")
    # 1. 清理与系统 Dock 重复的原版 Dash to Dock
    dup = os.path.join(EXT_DIR, "dash-to-dock@micxgx.gmail.com")
    if os.path.isdir(dup):
        sh(["rm", "-rf", dup])
        print("  已移除重复的 Dash to Dock(系统自带 Ubuntu Dock 已够用)")
    # 2. 注册扩展参数表
    install_schemas()
    # 3. 写入 macOS 化参数
    print("[%s]" % JP_SCHEMA)
    for k, v in JP_APPLY.items():
        gset(JP_SCHEMA, k, v)
    if os.path.exists(LOGO_ICON):
        print("[%s]" % LOGO_SCHEMA)
        for k, v in LOGO_APPLY.items():
            gset(LOGO_SCHEMA, k, v)
    else:
        print("  (跳过苹果 logo：找不到 %s)" % LOGO_ICON)
    # 3.5 收尾微调：放大强度、圆角半径、苹果菜单里的命令指向
    print("[收尾微调]")
    gset("org.gnome.shell.extensions.magnific-launcher", "zoom-pixels", 20)  # mac 式放大 ~1.4 倍
    corner = ("{'padding': <{'left': <uint32 1>, 'right': <uint32 1>, 'top': <uint32 1>, "
              "'bottom': <uint32 1>}>, 'keepRoundedCorners': <{'maximized': <false>, "
              "'fullscreen': <false>}>, 'borderRadius': <uint32 12>, 'smoothing': <0>, "
              "'borderColor': <[0.5, 0.5, 0.5, 1.0]>, 'enabled': <true>}")
    gset("org.gnome.shell.extensions.rounded-window-corners-reborn",
         "global-rounded-corner-settings", corner)
    for key, cmd in (("menu-button-terminal", "ptyxis"),
                     ("menu-button-software-center", "snap-store"),
                     ("menu-button-system-monitor", "resources")):
        if sh(["bash", "-c", "command -v %s" % cmd]).returncode == 0:
            gset(LOGO_SCHEMA, key, cmd)
        else:
            print("  (跳过 %s：命令 %s 不存在)" % (key, cmd))
    # 3.8 第三轮：菜单栏 / Spotlight / 锁屏 / 自动深浅色
    print("[第三轮：菜单栏与 Spotlight]")
    for schema, kv in ROUND3.items():
        print("  [%s]" % schema.split(".")[-1])
        for k, v in kv.items():
            gset(schema, k, v)
    # 4. 让新扩展在下次登录时自动启用
    cur = sh(["gnome-extensions", "list", "--enabled"]).stdout.split()
    enabled = [u for u in cur]
    for pk, uuid, name, on in EXTS:
        if on and uuid not in enabled:
            enabled.append(uuid)
    gset("org.gnome.shell", "enabled-extensions", enabled)
    print("\n准备完毕。现在注销并重新登录一次即生效。")
    return 0


def cmd_enable_ext():
    print("== 启用扩展 ==")
    for pk, uuid, name, on in EXTS:
        if not on:
            continue
        sh(["gnome-extensions", "enable", uuid])
        info = sh(["gnome-extensions", "info", uuid]).stdout
        state = "未加载"
        for line in info.splitlines():
            if "状态" in line or "State" in line:
                state = line.split(":", 1)[-1].strip()
        print("  %s %s -> %s" % ("✓" if state == "ACTIVE" else "✗", name, state))
    print("\n== 扩展加载状态 ===")
    for pk, uuid, name, on in EXTS:
        info = sh(["gnome-extensions", "info", uuid]).stdout
        err = [l for l in info.splitlines() if "错误" in l or "Error" in l]
        if err:
            print("  %s: %s" % (name, " / ".join(e.strip() for e in err)))
    return 0


def cmd_status():
    print("== 当前状态 ==")
    for s in SCHEMAS:
        print("\n[%s]" % s)
        print(sh(["gsettings", "list-recursively", s]).stdout.strip()[:1200])
    return 0


# ─────────────────────────── 依赖与资源 ───────────────────────────

ASSETS = {
    "inter_font": "https://github.com/rsms/inter/releases/download/v4.1/Inter-4.1.zip",
    "mono_font": "https://github.com/JetBrains/JetBrainsMono/releases/download/v2.304/JetBrainsMono-2.304.zip",
    "icon_theme": "https://github.com/vinceliuice/WhiteSur-icon-theme.git",
    "cursors": "https://github.com/vinceliuice/WhiteSur-cursors.git",
    "wallpapers": "https://github.com/vinceliuice/WhiteSur-wallpapers.git",
    "apple_logo": "https://raw.githubusercontent.com/simple-icons/simple-icons/develop/icons/apple.svg",
}


def cmd_deps():
    """检查系统与依赖是否齐备"""
    import re

    print("== 系统 ==")
    ver = sh(["gnome-shell", "--version"]).stdout.strip()
    print("  %s" % (ver or "未检测到 gnome-shell"))
    m = re.search(r"(\d+)\.", ver)
    if m and int(m.group(1)) < 45:
        print("  ⚠ 本脚本面向 GNOME 45+（扩展 API 自 45 起大改），当前版本扩展可能装不上")
    print("  会话类型: %s" % os.environ.get("XDG_SESSION_TYPE", "未知"))

    print("\n== 必需命令 ==")
    ok = True
    for c, why in [("python3", "运行本脚本"),
                   ("curl", "下载扩展与资源"),
                   ("unzip", "解压扩展与字体"),
                   ("git", "拉取图标/光标/壁纸主题"),
                   ("glib-compile-schemas", "编译扩展参数表")]:
        if sh(["bash", "-c", "command -v %s" % c]).returncode == 0:
            print("  ✓ %-22s %s" % (c, why))
        else:
            print("  ✗ %-22s 缺失 —— %s" % (c, why))
            ok = False

    print("\n== 可选（缺了不影响主功能）==")
    for c, why in [("gnome-sushi", "文件管理器空格预览 = macOS Quick Look"),
                   ("gnome-tweaks", "图形化调参面板"),
                   ("notify-send", "桌面通知测试"),
                   ("fc-cache", "刷新字体缓存")]:
        hit = sh(["bash", "-c", "command -v %s" % c]).returncode == 0
        print("  %s %-22s %s" % ("✓" if hit else "○", c, why))
    print("\n  推荐补齐: sudo apt install -y gnome-sushi gnome-tweaks")
    return 0 if ok else 1


def _screen_size():
    """尽力探测主显示器分辨率，用于挑合适档位的壁纸"""
    import glob as _glob
    for m in sorted(_glob.glob("/sys/class/drm/card*/card*-*/modes")):
        try:
            with open(m) as f:
                line = f.readline().strip()
            if "x" in line:
                w, h = line.split("x")[:2]
                return int(w), int(h)
        except Exception:
            continue
    return 1920, 1080


def cmd_assets():
    """下载并安装全部用户态资源：字体、图标主题、光标主题、壁纸、苹果 logo"""
    import shutil
    import tempfile

    tmp = tempfile.mkdtemp(prefix="macos-look-")
    fonts_root = os.path.join(HOME, ".local/share/fonts")
    icons_root = os.path.join(HOME, ".local/share/icons")
    bg_root = os.path.join(BG_DIR, "macos")
    for d in (fonts_root, icons_root, bg_root):
        os.makedirs(d, exist_ok=True)

    def fetch(url, dest):
        print("    下载 %s" % url.split("/")[-1])
        r = sh(["curl", "-fsSL", "--max-time", "600", "-o", dest, url])
        return r.returncode == 0

    # 1) 西文字体：Inter（界面）与 JetBrains Mono（终端）
    for key, sub, label in [("inter_font", "inter", "Inter"),
                            ("mono_font", "jetbrains-mono", "JetBrains Mono")]:
        target = os.path.join(fonts_root, sub)
        if os.path.isdir(target) and os.listdir(target):
            print("  ✓ %s 已存在，跳过" % label)
            continue
        print("  → 安装 %s" % label)
        zp = os.path.join(tmp, key + ".zip")
        if not fetch(ASSETS[key], zp):
            print("    ✗ 下载失败，跳过")
            continue
        ex = os.path.join(tmp, key)
        os.makedirs(ex, exist_ok=True)
        if sh(["unzip", "-oq", zp, "-d", ex]).returncode != 0:
            print("    ✗ 解压失败，跳过")
            continue
        os.makedirs(target, exist_ok=True)
        n = 0
        for root, _dirs, files in os.walk(ex):
            for f in files:
                if f.lower().endswith((".ttf", ".otf")):
                    shutil.copy(os.path.join(root, f), target)
                    n += 1
        if n == 0:
            # 有些字体包把可变字体放在根目录
            print("    ⚠ 未找到字体文件，检查包结构")
        else:
            print("    ✓ %d 个字体文件 → %s" % (n, target))

    # 2) 主题类：图标主题 / 光标主题（脚本自带用户态安装逻辑）
    for key, label in [("icon_theme", "WhiteSur 图标主题"), ("cursors", "WhiteSur 光标主题")]:
        if key == "icon_theme" and os.path.isdir(os.path.join(icons_root, "WhiteSur")):
            print("  ✓ %s 已存在，跳过" % label)
            continue
        if key == "cursors" and os.path.isdir(os.path.join(icons_root, "WhiteSur-cursors")):
            print("  ✓ %s 已存在，跳过" % label)
            continue
        print("  → 安装 %s" % label)
        d = os.path.join(tmp, key)
        if sh(["git", "clone", "--depth", "1", "-q", ASSETS[key], d]).returncode != 0:
            print("    ✗ 拉取失败，跳过")
            continue
        r = sh(["bash", os.path.join(d, "install.sh")])
        print("    %s %s" % ("✓" if r.returncode == 0 else "✗", label))

    # 3) 壁纸：按屏幕分辨率选档
    w, h = _screen_size()
    tier = "4k" if w > 2560 else ("2k" if w > 1920 else "1080p")
    print("  → 安装壁纸（屏幕 %dx%d，选 %s 档）" % (w, h, tier))
    d = os.path.join(tmp, "wallpapers")
    if sh(["git", "clone", "--depth", "1", "-q", ASSETS["wallpapers"], d]).returncode != 0:
        print("    ✗ 拉取失败，跳过")
    else:
        src = os.path.join(d, tier)
        if not os.path.isdir(src):
            src = os.path.join(d, "1080p")
        n = 0
        for f in sorted(os.listdir(src)):
            if f.lower().endswith((".jpg", ".png")):
                shutil.copy(os.path.join(src, f), bg_root)
                n += 1
        print("    ✓ %d 张壁纸 → %s" % (n, bg_root))
        write_background_properties(bg_root)

    # 4) 苹果 logo（Logo Menu 自带的是各发行版 logo，没有苹果）
    logo = LOGO_ICON
    if os.path.exists(logo):
        print("  ✓ 苹果 logo 已存在，跳过")
    else:
        print("  → 生成苹果 logo")
        raw = os.path.join(tmp, "apple.svg")
        if fetch(ASSETS["apple_logo"], raw):
            import re as _re
            svg = open(raw, encoding="utf-8").read()
            svg = _re.sub(r"<title>.*?</title>", "", svg, flags=_re.S)
            if "fill=" not in svg:
                svg = svg.replace("<path ", '<path fill="#ffffff" ')
            os.makedirs(os.path.dirname(logo), exist_ok=True)
            with open(logo, "w", encoding="utf-8") as f:
                f.write(svg)
            print("    ✓ %s" % logo)
        else:
            print("    ✗ 下载失败，跳过")

    sh(["fc-cache", "-f", fonts_root])
    shutil.rmtree(tmp, ignore_errors=True)
    print("\n资源安装完毕。")
    return 0


def write_background_properties(bg_root):
    """把壁纸注册进「设置 → 外观」面板（纯用户态）"""
    out_dir = os.path.join(HOME, ".local/share/gnome-background-properties")
    os.makedirs(out_dir, exist_ok=True)
    names = {
        "Monterey-light": "macOS Monterey 浅色", "Monterey-dark": "macOS Monterey 深色",
        "Monterey-morning": "macOS Monterey 清晨", "Monterey": "macOS Monterey",
        "WhiteSur-light": "macOS WhiteSur 浅色", "WhiteSur-dark": "macOS WhiteSur 深色",
        "WhiteSur-morning": "macOS WhiteSur 清晨", "WhiteSur": "macOS WhiteSur",
    }
    entries = []
    for f in sorted(os.listdir(bg_root)):
        stem = os.path.splitext(f)[0]
        if not f.lower().endswith((".jpg", ".png")):
            continue
        entries.append(
            '  <wallpaper deleted="false">\n'
            "    <name>%s</name>\n"
            "    <filename>%s</filename>\n"
            "    <options>zoom</options>\n"
            "    <shade_type>solid</shade_type>\n"
            "    <pcolor>#1a1a2e</pcolor>\n"
            "    <scolor>#1a1a2e</scolor>\n"
            "  </wallpaper>" % (names.get(stem, stem), os.path.join(bg_root, f)))
    if not entries:
        return
    with open(os.path.join(out_dir, "macos.xml"), "w", encoding="utf-8") as fh:
        fh.write('<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<!DOCTYPE wallpapers SYSTEM "gnome-wp-list.dtd">\n<wallpapers>\n'
                 + "\n".join(entries) + "\n</wallpapers>\n")
    print("    ✓ 已注册进「设置 → 外观」")


# ─────────────────────── 上游扩展的本地补丁 ───────────────────────
# 格式: (扩展 uuid, 相对路径, 原始片段, 替换片段, 已打补丁的判定标记)
EXT_PATCHES = [
    (
        "top-bar-organizer@julian.gse.jsts.xyz",
        "extensionModules/BoxOrderManager.js",
        "        const appIndicator = indicatorContainer.get_child()._indicator;\n"
        "        let application = appIndicator.id;",
        "        // 本地补丁：某些 indicator 容器的 _indicator 尚未就绪或结构不同\n"
        "        // （屏幕共享、U 盘、更新提示等动态出现的托盘项），原代码直接读 .id\n"
        "        // 会抛 TypeError 使整个扩展进入 ERROR，顶栏排序集体失效。\n"
        "        const appIndicator = indicatorContainer.get_child()?._indicator;\n"
        "        if (!appIndicator)\n"
        "            return `appindicator-unknown-${role}`;\n"
        "        let application = appIndicator.id;",
        "indicatorContainer.get_child()?._indicator",
    ),
]


def cmd_patch_ext():
    """给有已知缺陷的上游扩展打本地补丁（幂等，可重复执行）"""
    print("== 给扩展打本地补丁 ==")
    applied = 0
    for uuid, rel, old, new, marker in EXT_PATCHES:
        path = os.path.join(EXT_DIR, uuid, rel)
        if not os.path.exists(path):
            print("  ○ %s 未安装，跳过" % uuid)
            continue
        with open(path, encoding="utf-8") as f:
            src = f.read()
        if marker in src:
            print("  ✓ %s 已是打过补丁的状态" % uuid)
            continue
        if old not in src:
            print("  ⚠ %s 没找到补丁锚点（上游可能已修复或改版），跳过" % uuid)
            continue
        with open(path, "w", encoding="utf-8") as f:
            f.write(src.replace(old, new, 1))
        print("  ✓ %s 补丁已应用" % uuid)
        applied += 1
    if applied:
        print("\n  补丁写在上游扩展代码里，扩展被更新后需要重新执行本命令。")
    return 0


if __name__ == "__main__":
    cmds = {
        "backup": cmd_backup,
        "apply": cmd_apply,
        "revert": cmd_revert,
        "install-ext": cmd_install_ext,
        "prepare": cmd_prepare,
        "enable-ext": cmd_enable_ext,
        "status": cmd_status,
        "deps": cmd_deps,
        "assets": cmd_assets,
        "patch-ext": cmd_patch_ext,
    }
    if len(sys.argv) < 2 or sys.argv[1] not in cmds:
        print(__doc__)
        sys.exit(1)
    sys.exit(cmds[sys.argv[1]]() or 0)
