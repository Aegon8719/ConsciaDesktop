# ConsciaDesktop

Conscia 的独立安装与发布工程，面向 EndeavourOS / Arch Linux x86_64。
这个仓库仅保存安装逻辑、版本锁、Arch 构建规则和默认配置。
niri 和 DankMaterialShell 源码从两个 GitHub Fork 按完整提交 SHA 获取，不复制进本仓库。

```text
ConsciaDesktop/
├── install.sh
├── update.sh
├── rollback.sh
├── uninstall.sh
├── versions.lock
├── config/                 # niri、DMS、会话偏好及登录配置
├── packages/arch/          # PKGBUILD、会话入口
├── scripts/                # 获取源码、构建、配置部署、生命周期、安装包生成
└── .github/workflows/      # Arch 构建、Artifacts 和标签 Release
```

## 默认桌面与交互

- 使用 Conscia 主区域与小窗列布局，支持 Dwindle 分屏、内侧加入、组内图标行、连续滚动吸附和向外关闭动画。
- 单应用工作区不允许最小化到小窗列或最大化；最大化保留焦点高亮、圆角和边框留白。
- `Super+F`／`Super+M` 最大化当前应用；`Super+Ctrl+F` 展开／恢复整个分屏组并保留组内分割；`Super+Shift+F` 全屏。
- 触屏、触控板三指上下滑动切换工作区，三指张开／捏合展开／恢复整个分屏组，四指捏合／张开显示／退出桌面；`Super+D` 切换桌面。
- 小窗左键提升、右键关闭、Super+左键加入分屏。触屏单指滚动小窗列，触控板使用二指。
- DMS 使用 island，中央顺序为搜索、通知、剪贴板、时钟、媒体；圆形和胶囊形组件统一边距，CPU／内存合并显示。
- 时间格式为 `yyyy/MM/dd HH:mm:ss`，使用性能数字同款字体和固定宽度。日历和媒体直接显示内容，外部空白点击关闭，弹窗主色描边关闭。
- 状态栏空白区域仅鼠标滚轮切换工作区；触屏向内扫动仅展开左右两侧组件，工作区部件打开概览。中央组件只响应触屏点击，中央空白点击不打开弹窗。

完整 Touch、TouchPad、KeyBoard Shortcuts、Mouse Click 交互见 [niri 项目说明](https://github.com/Aegon8719/niri)，面板实现见 [DMS 项目说明](https://github.com/Aegon8719/DankMaterialShell)。默认配置用于首次安装；已有用户配置由更新流程保留。

## 全新安装

支持从没有桌面环境的 Arch Linux／EndeavourOS x86_64 基础系统安装。
系统需已能启动并联网，具有 systemd、pacman 和有 sudo 权限的普通用户；
在本机 TTY 登录该用户后运行。安装器不负责分区、基础系统安装或引导器配置，
目前不支持将同一安装脚本用于 Fedora、Debian 等其他发行版。

在已安装并联网的系统中，以有 sudo 权限的普通用户运行：

```bash
git clone https://github.com/Aegon8719/ConsciaDesktop.git
cd ConsciaDesktop
bash install.sh
```

也可直接复制当前 ConsciaDesktop 文件夹到新电脑，执行 `bash install.sh`。
安装器执行完整的 pacman 系统更新，安装依赖，从 GitHub 获取锁定源码并编译。
Rust、Go 和构建工具由依赖安装流程提供；Go 可自动获取源码要求的工具链。
小窗应用图标所需的 GdkPixbuf 和 SVG 解码支持由 `gdk-pixbuf2`、`librsvg` 软件包提供。
不运行测试套件或桌面配置验证，不自动注销或重启。

安装后自行重启，在登录界面选择 **Conscia**。
没有登录管理器时会自动安装并启用 **greetd + DMS Greeter**，无需预装 KDE、GNOME 或 SDDM。
安装器优先使用软件仓库中的 `dms-greeter`；仓库没有该包时，通过普通用户的
`makepkg --nocheck` 从 AUR `greetd-dms-greeter-bin` 构建并安装二进制发行包，不需要 yay／paru。
`--package` 安装同样包含登录界面的配置步骤。已有登录管理器则保留，更新不会替换它。
登录界面使用独立的 `greeter` 系统账户和系统 niri，不依赖用户家目录中的编译产物；
登录后选择 **Conscia**，进入项目版本的 niri 与 DMS 桌面。
桌面内 `Super+L` 默认调用 DMS 锁屏。因此从无桌面系统首次安装后，登录和锁屏均使用 DMS。
安装时自动以安装用户执行 `dms-greeter sync --yes`，使用 DMS 自带的同步机制，
让登录界面跟随该用户的桌面壁纸与主题设置；所需账户组和文件读取权限由 DMS Greeter 配置。
ConsciaDesktop 不指定默认壁纸图片，也不携带自定义壁纸或动态配色缓存，首次启动采用 DMS 自身默认设置。
之后在 DMS 中更换壁纸，登录界面通过同步的用户配置跟随，不固定到某个图片路径。
配置只启用下次启动服务，不立即启动登录管理器或打断 TTY 会话。
也可以在 TTY 运行 `conscia-session`。NVIDIA 驱动交由 EndeavourOS 自身管理。
维护已有 niri/DMS 桌面时，先注销，再从本机 TTY 运行这些脚本。

发布版可避免本地编译，使用与项目版本配套的 Arch 软件包：

```bash
bash install.sh --package /path/to/conscia-desktop-*.pkg.tar.zst
```

软件包由 pacman 安装；不要另外直接安装该软件包后再运行首次安装流程，
否则会缺少本用户的配置基线和回退记录。脚本拒绝接管这种无记录安装。

## 更新与回退

先更新本安装仓库到需要的发布版本，再运行：

```bash
git pull --ff-only
bash update.sh
# 或使用发布的软件包：
bash update.sh --package /path/to/conscia-desktop-*.pkg.tar.zst

# 回到上一次安装的软件包版本：
bash rollback.sh
```

更新只替换程序，保留当前用户配置；不会每次覆盖成仓库默认设置。
`update.sh` 使用当前 checkout 的版本锁，不擅自追踪两个 Fork 的主分支。
回退恢复成对构建的 niri/DMS 及该版本的配套脚本，不覆盖用户配置，
不回退 pacman 更新的其他系统依赖。因此历史版本还需与当前系统库兼容。

生命周期操作保留事务快照。正常报错时自动尝试恢复；断电等中断后运行：

```bash
bash rollback.sh --recover
```

源码下载或构建阶段失败不会替换已安装的 Conscia，但系统依赖可能已更新。

## 卸载

```bash
bash uninstall.sh
```

卸载 `conscia-desktop` 软件包，恢复首次安装前的个人配置和服务覆盖文件。
卸载前的最新配置也会另存一份。自动启用的 DMS Greeter 会在仍由 greetd 管理登录时取消启用，
恢复配置前的 greetd 配置、启用状态和默认启动目标；中断事务恢复也包含这些状态。
如果之后自行切换了登录管理器，卸载不会替换它。依赖软件包和 greeter 系统账户不自动删除，避免影响其他桌面。
不要在多个用户下分别管理同一套系统安装；脚本会记录并检查安装用户。

## 文件与缓存

| 内容 | 位置 |
| --- | --- |
| 当前程序及配套脚本 | `/usr/lib/conscia/`，由 pacman 管理 |
| 登录入口 | `/usr/bin/conscia-session` |
| 用户配置 | `$XDG_CONFIG_HOME/niri/`、`$XDG_CONFIG_HOME/DankMaterialShell/` |
| 壁纸设置 | 由 DMS 管理；安装包不携带壁纸图片 |
| 安装记录、旧软件包、配置快照 | `$XDG_STATE_HOME/conscia-desktop/` |
| 下载的源码、编译中间文件 | `$XDG_CACHE_HOME/conscia-desktop/` |

没有设置 XDG 变量时，分别使用 `~/.config`、`~/.local/share`、`~/.local/state`、`~/.cache`。
构建完成后可以删除构建缓存；不要删除状态目录中的旧软件包和基线，回退、卸载需要它们。
安装目录独立于 Git checkout，可将本仓库放在任意位置。

## 维护版本锁与配置

1. 先把源码改动提交并推送到对应 Fork。
2. 将两个兼容提交的完整 40 位 SHA 写入 `versions.lock`。
3. 修改程序、脚本或默认配置准备发布时，提高 `version`。
4. 提交本工程，并用 `v<version>` 标签发布。

锁定版本为：

- [niri de6270f](https://github.com/Aegon8719/niri/commit/de6270f1a2b2bb764b4cf71db6d6ea00f86408c2)
- [DankMaterialShell 4624295](https://github.com/Aegon8719/DankMaterialShell/commit/462429571323cffd6d7f030ca305abb35f6509c6)

将当前电脑的桌面偏好重新保存为默认配置：

```bash
python3 scripts/capture-config.py
```

捕获布局、面板、快捷键、字体、光标、动态配色和壁纸路径，并打包所引用的图片。
用户名和图片路径在目标电脑部署时重写。
不捕获浏览器账号、Wi-Fi 凭据、剪贴板和启动器查询历史。
显示器相关偏好保持原值，新机器必要时可自行调整。

## 构建与发布

在 Arch / EndeavourOS 上构建原生软件包：

```bash
sudo pacman -Syu --needed base-devel git python
bash scripts/build-package.sh
```

在当前开发电脑生成不含 Fork 源码的单文件在线安装器：

```bash
python3 scripts/package-installer.py
# 输出 dist/ConsciaDesktop-EndeavourOS.run
```

将 `.run` 复制到新电脑后执行 `bash ConsciaDesktop-EndeavourOS.run`。
它只携带本工程，真正安装时才从 GitHub 下载锁定源码，所以必须联网。

GitHub Actions 在手动触发时构建并上传 Artifacts；推送 `v*` 标签时，
在构建成功后将 Arch 软件包和 `.run` 安装器发布到 GitHub Release。
工作流构建 Arch 软件包及在线安装器，不运行测试。
