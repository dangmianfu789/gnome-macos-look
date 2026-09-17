# GNOME macOS Look

**把 Ubuntu / GNOME Shell 桌面改造成接近 macOS 的观感与操作习惯。**

*Turn your GNOME desktop into something that feels like macOS — menu bar, Dock, traffic-light buttons, Spotlight, Sonoma-style lock screen — all in userspace, no sudo, fully reversible.*

在 **Ubuntu 26.04 + GNOME Shell 50** 上实测通过。

> 全套配置 **100% 在用户态完成**：不安装系统包、不修改任何 `/usr` 下的文件、配置前先自动备份，随时一条命令还原。
> 单台机器上实测装了 **19 个 GNOME 扩展 + 5 类用户态资源**，全程无需 root。

---

## 效果

```
菜单栏   [ 苹果标 ] [ 应用名 ] [ 文件 编辑 显示 前往 窗口 帮助 ] ……  [ 状态图标 ] [ 时钟 ]
          └Logo Menu  └WinTitle   └ Global Menu                              └ 最右端
────────────────────────────────────────────────────────────────────────────────────
                                                                    半透明毛玻璃
底部 Dock  [启动台] [文件] [浏览器] [邮件] [应用商店] …… [垃圾桶]
               └ 悬停时图标向上放大，左右邻图标依次递减（macOS 波浪手感）
```

| 模块 | 具体效果 |
|---|---|
| **顶部菜单栏** | 左上角苹果 logo（可点出系统菜单）、当前应用名、应用菜单（文件/编辑/显示/窗口/帮助）搬进顶栏；时钟排到最右端；面板压到 26px；毛玻璃半透明 |
| **Dock** | 移到屏幕底部居中、常驻显示、48px 图标、运行中应用下小圆点、右侧垃圾桶与挂载磁盘；**鼠标悬停时图标向上放大成波浪** |
| **窗口** | 左上角红黄绿三色按钮（平时不显符号、悬停淡入、失焦变灰）；12px 圆角；最小化"精灵效果"（窗口被吸进 Dock） |
| **启动器** | Spotlight 式搜索（`Super+空格`），支持应用、文件、计算器、系统动作 |
| **系统细节** | 左上角触发角 = Mission Control；摇动鼠标高亮光标位置（macOS 同款）；通知弹在右上角；日落/日出自动切换深浅色；Sonoma 风格锁屏 |
| **外观** | macOS 图标主题 + 光标主题 + Inter 界面字体 + JetBrains Mono 终端字体 + Monterey 壁纸（浅色/深色随系统模式自动切换，共 8 张注册进「设置→外观」） |
| **键盘** | 一整套 `Super`（= ⌘）快捷键映射，原绑定全部保留不被夺 |

---

## 系统要求

- **GNOME Shell 45 或更高**（在 GNOME 50 上完整实测；45 以下扩展 API 不兼容）
- 任意 Linux 发行版（在 **Ubuntu 26.04** 上实测，Debian 系最省事）
- **Wayland 或 X11 均可**（Wayland 下新扩展需注销重登才能加载）
- 需要能访问 GitHub 与 `extensions.gnome.org`（下载扩展与资源）
- 磁盘约 **300MB**（扩展 + 字体 20M + 图标主题 63M + 壁纸 5M）

---

## 快速开始

```bash
git clone https://github.com/<your-name>/gnome-macos-look.git
cd gnome-macos-look
./install.sh
```

脚本会依次：**检查依赖 → 部署脚本 → 备份原始设置 → 下载资源 → 安装 19 个扩展 → 应用配置**。

装完还剩两步收尾（脚本结束时会再提示一遍）：

1. **注销并重新登录**（Wayland 无法热加载新装的扩展），登录后执行：
   ```bash
   python3 ~/.config/macos-look/macos-look.py enable-ext
   ```
2. 可选，补齐两个推荐包：
   ```bash
   sudo apt install -y gnome-sushi gnome-tweaks
   ```

---

## 依赖一览

脚本会自动解决绝大部分依赖，这里是完整清单。

### 必需（脚本会检查，缺失时提示）

| 依赖 | 用途 | 获取方式 |
|---|---|---|
| GNOME Shell 45+ | 运行环境 | 发行版自带 |
| `python3` | 运行配置脚本 | 发行版自带 |
| `curl` | 下载扩展与资源 | `sudo apt install curl` |
| `unzip` | 解压扩展与字体包 | `sudo apt install unzip` |
| `git` | 拉取图标/光标/壁纸主题仓库 | `sudo apt install git` |
| `glib-compile-schemas` | 编译扩展的 gsettings 参数表 | `sudo apt install libglib2.0-bin` |

### 可选（增强体验，缺了不影响主功能）

| 依赖 | 用途 | 获取方式 |
|---|---|---|
| `gnome-sushi` | 文件管理器按空格快速预览 = macOS Quick Look | `sudo apt install gnome-sushi` |
| `gnome-tweaks` | 图形化调参面板，免记命令 | `sudo apt install gnome-tweaks` |

### 自动下载的 GNOME 扩展（19 个，来自 extensions.gnome.org）

`install.sh` 会按 UUID 自动下载、解压到 `~/.local/share/gnome-shell/extensions/` 并编译各自 schema。

| 效果 | 扩展 | 扩展 ID |
|---|---|---|
| Dock 图标悬停放大波浪 | Magnific Launcher | 9529 |
| 顶栏/总览毛玻璃 | Blur my Shell | 3193 |
| 顶栏精调（隐藏活动、时钟右置、通知右上、面板高度） | Just Perfection | 3843 |
| 左上角苹果菜单 | Logo Menu | 4451 |
| 应用菜单搬进顶栏 | Global Menu for GNOME | 10288 |
| 顶栏显示当前应用名 | Window Title Pro Topbar | 10319 |
| 顶栏元素排序 | Top Bar Organizer | 4356 |
| Spotlight 启动器 | Spotlight | 10666 |
| 窗口圆角 | Rounded Window Corners Reborn | 7048 |
| 最小化精灵动画 | Compiz alike magic lamp effect | 3740 |
| Sonoma 风格锁屏 | WACK - Sonoma Lockscreen | 9713 |
| 日落自动切深浅色 | Night Theme Switcher | 2236 |

> 另有 7 个 Ubuntu 自带的系统扩展（Dock、托盘图标、平铺助手等）保持启用，不在替换范围内。

### 自动下载的用户态资源

| 资源 | 来源 | 安装位置 |
|---|---|---|
| Inter 字体（界面） | [rsms/inter](https://github.com/rsms/inter) Release | `~/.local/share/fonts/inter/` |
| JetBrains Mono（终端） | [JetBrains/JetBrainsMono](https://github.com/JetBrains/JetBrainsMono) Release | `~/.local/share/fonts/jetbrains-mono/` |
| WhiteSur 图标主题 | [vinceliuice/WhiteSur-icon-theme](https://github.com/vinceliuice/WhiteSur-icon-theme) | `~/.local/share/icons/WhiteSur*` |
| WhiteSur 光标主题 | [vinceliuice/WhiteSur-cursors](https://github.com/vinceliuice/WhiteSur-cursors) | `~/.local/share/icons/WhiteSur-cursors` |
| macOS 风格壁纸 | [vinceliuice/WhiteSur-wallpapers](https://github.com/vinceliuice/WhiteSur-wallpapers) | `~/.local/share/backgrounds/macos/` |
| 苹果 logo | [simple-icons](https://github.com/simple-icons/simple-icons) | `~/.local/share/icons/apple-logo-symbolic.svg` |

---

## 它到底改了什么

全部改动集中在四个地方，**没有一处动到系统文件**：

| 位置 | 内容 |
|---|---|
| `gsettings` / `dconf` | 桌面主题、Dock 位置、窗口按钮布局、快捷键、字体、通知位置等约 60 项键值 |
| `~/.local/share/gnome-shell/extensions/` | 19 个用户态扩展 |
| `~/.local/share/{fonts,icons,backgrounds,glib-2.0/schemas,gnome-background-properties}/` | 字体、主题、壁纸、扩展参数表 |
| `~/.config/gtk-{3,4}.0/gtk.css` | 三色窗口按钮的着色（删掉即还原） |

配置脚本 `~/.config/macos-look/macos-look.py` 提供以下子命令：

| 命令 | 作用 |
|---|---|
| `deps` | 检查系统与依赖 |
| `assets` | 下载字体 / 图标 / 光标 / 壁纸 / 苹果 logo |
| `install-ext` | 下载安装全部 GNOME 扩展（已装的跳过） |
| `apply` | 应用 macOS 风格设置（幂等） |
| `prepare` | 注册扩展参数表 + 写入扩展配置 + 更新自启动清单 |
| `enable-ext` | 登录后重新启用全部扩展 |
| `backup` | 备份当前设置（**首次安装时自动执行，勿重复覆盖**） |
| `status` | 查看当前各项设置值 |
| `revert` | **一键还原**到安装前的状态 |

---

## 快捷键对照

| macOS | 本配置 | 说明 |
|---|---|---|
| ⌘Space | `Super+空格` | Spotlight |
| ⌘W | `Super+W` | 关闭窗口 |
| ⌘M | `Super+M` | 最小化 |
| ⌘\` | `Super+\`` | 切换同一应用的窗口 |
| ⌘⇧3 / ⌘⇧4 | `Super+⇧3` / `Super+⇧4` | 全屏截图 / 区域截图 |
| ⌃⌘F | `Super+Ctrl+F` | 全屏切换 |
| ⌘Tab | `Super+Tab` | 应用切换器 |
| 摇鼠标找指针 | 摇鼠标 | 高亮光标位置 |
| 鼠标撞左上角 | 同 | Mission Control |

> 原绑定（`Alt+Tab`、`Alt+F4` 等）全部保留，没有被夺走。

---

## 已知限制（架构层面，不是配置问题）

1. **全局菜单只在部分应用出现** —— GTK4 / libadwaita 应用（文件管理器、设置等）不向系统导出菜单，这是 GNOME 的架构决定。Firefox、LibreOffice 这类应用可能有效。
2. **Dock 放大是模拟的** —— 靠像素缩放实现，没有 macOS 原生那条弹性曲线，凑近看能看出差别。且实测它只响应**真实鼠标**，脚本注入的虚拟指针触发不了。
3. **三指拖拽做不了** —— 上游手势扩展不支持 GNOME 50。
4. **窗口毛玻璃材质（vibrancy）做不了** —— Linux 应用不实现这种材质。
5. **字体渲染引擎不同** —— Inter 只是字形接近 SF Pro。
6. **无原生应用生态** —— Safari / Preview / QuickTime / Keynote 没有对应物。

**结论：界面和交互能到八成到九成，最后那一成需要换硬件。**

---

## 还原

```bash
python3 ~/.config/macos-look/macos-look.py revert
```

会用安装前自动生成的 `~/.config/macos-look/backup.json` 把 gsettings 逐项还原，并把扩展参数重置为默认。

想只退掉某一项，直接关掉对应扩展即可：

```bash
gnome-extensions list                                  # 查看 uuid
gnome-extensions disable rounded-window-corners@fxgn   # 例如关掉窗口圆角
```

删除这两个文件即可还原三色窗口按钮：`~/.config/gtk-4.0/gtk.css`、`~/.config/gtk-3.0/gtk.css`。

---

## 故障排查

```bash
python3 ~/.config/macos-look/macos-look.py deps        # 依赖检查
gnome-extensions list --enabled                        # 已启用扩展
gnome-extensions info <uuid>                           # 单个扩展状态
journalctl --user -b -o cat | grep -iE "error" | tail -30   # Shell 报错
```

几个实测踩过的坑：

- **`!important` 在 GTK CSS 里不被支持**：写了不会报错，但整条声明被静默丢弃。改用提高选择器特异性。
- **扩展装上了但没生效**：Wayland 下必须先注销重登，新扩展才会被扫描到。
- **扩展变成 ERROR 后可能救不回来**：`disable`/`enable` 无反应，`ReloadExtension` 在 GNOME 50 未实现，只能注销重登。
- **日志里的 `Can't update stage views actor … needs an allocation`** 是 Blur my Shell 给 Dock 插 actor 造成的正常刷屏，**不影响功能**。
- **Top Bar Organizer 有个崩溃点**：动态出现的托盘图标（屏幕共享、U 盘、更新提示）会让它抛 `TypeError` 整体进 ERROR。仓库里已带本地补丁（见 `patches/`）。

---

## 致谢

本项目的观感完全建立在这些作品之上：

- [WhiteSur 系列主题](https://github.com/vinceliuice)（图标 / 光标 / 壁纸）by vinceliuice
- [Inter](https://github.com/rsms/inter) by Rasmus Andersson · [JetBrains Mono](https://github.com/JetBrains/JetBrainsMono)
- 以及上游那 19 个 GNOME 扩展的各位作者

## 许可证

[MIT](LICENSE)
