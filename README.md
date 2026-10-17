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
系统需已能启动，具有 systemd、pacman 和有 sudo 权限的普通用户；
在本机 TTY 登录该用户后运行。安装器不负责分区、基础系统安装或引导器配置，
目前不支持将同一安装脚本用于 Fedora、Debian 等其他发行版。

联网安装直接下载 GitHub Release 中的完整安装包，不在目标机器编译：

```bash
curl -fLO https://github.com/Aegon8719/ConsciaDesktop/releases/latest/download/ConsciaDesktop-EndeavourOS.run
bash ConsciaDesktop-EndeavourOS.run
```

也可克隆本仓库后运行 `bash install.sh`，下载 `versions.lock` 对应标签的 Release。
下载入口需要系统已有 curl、tar、zstd 和 sha256sum。完整包包含程序、依赖、登录界面
和默认配置；联网与离线入口最终执行同一个安装流程。不自动注销或重启。
小窗图标所需的 GdkPixbuf 和 SVG 解码支持包含在依赖中。

开发者如需在目标系统联网获取源码并编译，显式执行 `bash install.sh --build`。
该模式会先完整更新 pacman 系统并安装构建工具，仍不运行测试套件。

安装后自行重启，在登录界面选择 **Conscia**。
没有登录管理器时会自动安装并启用 **greetd + DMS Greeter**，无需预装 KDE、GNOME 或 SDDM。
Release 已携带 DMS Greeter；仅源码构建或单独 `--package` 安装时，才从仓库或
AUR `greetd-dms-greeter-bin` 获取，不需要 yay／paru。
`--package` 安装同样包含登录界面的配置步骤。已有登录管理器则保留，更新不会替换它。
登录界面使用独立的 `greeter` 系统账户和本包安装的 fork niri，不依赖用户家目录中的编译产物；
登录后选择 **Conscia**，进入项目版本的 niri 与 DMS 桌面。
桌面内 `Super+L` 默认调用 DMS 锁屏。因此从无桌面系统首次安装后，登录和锁屏均使用 DMS。
安装时自动以安装用户执行 `dms-greeter sync --yes`，使用 DMS 自带的同步机制，
让登录界面跟随该用户的桌面壁纸与主题设置；所需账户组和文件读取权限由 DMS Greeter 配置。
ConsciaDesktop 不指定默认壁纸图片，也不携带自定义壁纸或动态配色缓存，首次启动采用 DMS 自身默认设置。
之后在 DMS 中更换壁纸，登录界面通过同步的用户配置跟随，不固定到某个图片路径。
配置只启用下次启动服务，不立即启动登录管理器或打断 TTY 会话。
也可以在 TTY 运行 `conscia-session`。NVIDIA 驱动交由 EndeavourOS 自身管理。
维护已有 niri/DMS 桌面时，先注销，再从本机 TTY 运行这些脚本。

开发者也可安装自行构建的 Arch 软件包（此模式仍需联网安装系统依赖）：

```bash
bash install.sh --package /path/to/conscia-desktop-*.pkg.tar.zst
```

软件包由 pacman 安装；不要另外直接安装该软件包后再运行首次安装流程，
否则会缺少本用户的配置基线和回退记录。脚本拒绝接管这种无记录安装。

### 完整离线安装包

`ConsciaDesktop-<版本>-EndeavourOS-x86_64-offline.tar.zst` 面向制作时已更新的
EndeavourOS / Arch x86_64 基础系统：已有 systemd、pacman、有 sudo 权限的普通用户，
无需预装桌面，也无需在目标机器上联网或编译。

发布包以英文界面为支持范围，DMS 默认语言为英语。界面字体使用 Noto Sans，
等宽数字使用 Noto Sans Mono；保留表情字体，不包含中日韩字体包。
联网入口下载同一份发布包，因此使用相同默认设置。

默认安装以保留 fork niri 和 DMS 的桌面功能为范围：保留 Alacritty 终端、
图形登录与锁屏、网络、声音、剪贴板、媒体波形、XWayland 和桌面门户依赖。
不预装浏览器、文件管理器或完整 Breeze 主题；DMS 管理配色，使用 Adwaita
基础图标和 Breeze 光标。图形库及其 LLVM 运行依赖仍由包管理器解析并携带。
只打包这些功能和安装入口的递归依赖，不额外携带整个 `base` 元包的依赖。

本包直接安装 fork 的 niri、DMS、会话服务、门户配置和 DMS 应用入口，
提供 `niri`、`dms-shell` 包能力，不再依赖发行版的两套程序。
若系统已安装发行版 niri 或 dms-shell，pacman 会在安装本包时要求确认替换；
请从 TTY 操作。既有安装的个人配置和其它应用不会因精简自动删除。

```bash
tar --zstd -xf ConsciaDesktop-*-EndeavourOS-x86_64-offline.tar.zst
cd ConsciaDesktop-*-EndeavourOS-x86_64-offline
bash install-offline.sh
# 更新既有安装：bash install-offline.sh update
```

包内含锁定版本的 Conscia 原生软件包、DMS Greeter、Alacritty 终端及桌面功能的递归依赖、
本地 pacman 软件仓库、配置和安装脚本。`packages.txt` 记录精确包版本，
`built-at.txt` 记录打包时间，`SHA256SUMS` 用于文件完整性检查。
官方依赖保留软件包签名；自行构建的软件包随离线包提供。
安装入口仅使用本地仓库，复用在线安装的配置、登录界面及回退记录流程，
启用 NetworkManager 供下次启动使用，不自动注销或重启。

浏览器和文件管理器不预装。联网后可按需安装，例如：

```bash
sudo pacman -Syu firefox dolphin
```

这是已有基础系统上的桌面安装包，不是启动 ISO，不包含分区、引导器安装或
专有显卡驱动。基础系统应与包内依赖快照一致；不能保证任意旧版或另行修改的
系统可直接安装。NVIDIA 驱动需随目标 EndeavourOS 的内核另行准备。

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
`update.sh` 下载当前 checkout 版本锁对应的 Release；`bash update.sh --build` 才在本机构建。
也可下载新版 `.run` 后执行 `bash ConsciaDesktop-EndeavourOS.run update`。
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

- [niri 3fbf0ad](https://github.com/Aegon8719/niri/commit/3fbf0add9939520b8559800038054c4d86867939)
- [DankMaterialShell 017fa9a](https://github.com/Aegon8719/DankMaterialShell/commit/017fa9a1c543b79f25af454f702f4ff15b79a812)

将当前电脑的桌面偏好重新保存为默认配置：

```bash
python3 scripts/capture-config.py
```

捕获布局、面板、快捷键、字体、光标和主题偏好；不捕获壁纸路径、图片或动态配色缓存。
首次安装使用 DMS 自身默认壁纸设置，之后由用户设置并同步。
不捕获浏览器账号、Wi-Fi 凭据、剪贴板和启动器查询历史。
显示器相关偏好保持原值，新机器必要时可自行调整。

## 构建与发布

在 Arch / EndeavourOS 上构建原生软件包：

```bash
sudo pacman -Syu --needed base-devel git python
bash scripts/build-package.sh
```

生成绑定当前版本的轻量 Release 下载入口：

```bash
python3 scripts/package-installer.py
# 输出 dist/ConsciaDesktop-EndeavourOS.run
```

将 `.run` 复制到新电脑后执行 `bash ConsciaDesktop-EndeavourOS.run`。
它下载同一 Release 的完整离线包和校验文件，然后执行包内安装入口；需要先发布对应 Release。

GitHub Actions 在手动触发时构建并上传 Artifacts；推送 `v*` 标签时，
在构建成功后将完整 `.tar.zst` 包、SHA-256 校验文件和 `.run` 下载入口发布到 GitHub Release。
所有入口共用同一份构建产物，工作流不运行测试。

在联网的 Arch x86_64 环境中生成完整离线包：

```bash
sudo pacman -Syu --needed base-devel git python sudo
bash scripts/build-offline.sh
```

也可使用 Arch 容器构建。构建需要联网获取锁定源码、编译工具和完整依赖，
输出位于 `dist/`；不运行测试。离线包体积较大，不提交到 Git 源码仓库。
