# Balatro Terminal · V15

**Unofficial fan-made Balatro terminal adaptation for macOS and Windows.**

这是**非官方**的 Python 终端扑克 Roguelike 改编游戏，兼容 macOS 和 Windows，保留 18 种语言选择、可选的五首场景音乐支持和 JSON 存档格式。V15 主要修复幻灵牌、Boss 失效／翻面、牌型计分提示，以及部分语言界面。代码只有一套，无需为两个系统下载不同版本。

> **Fan-made / 非官方声明：** 本项目是爱好者制作的非官方终端改编作品，与 Balatro 的开发者 **LocalThunk**、发行商 **Playstack** 没有隶属、合作、赞助或官方授权关系。Balatro 名称及相关原作知识产权归其各自权利人所有。本仓库不提供原作音乐文件，也不主张拥有其版权。部分复杂 Joker、封印和 Boss 效果仍为简化实现；18 种语言尚未全部完成完整人工校对。非商业用途本身并不意味着已获得公开分发授权。

## V15 修复重点

- **Sigil／Ouija**：整手统一花色／点数的修改写回永久牌组；Ouija 永久减少 1 格手牌容量。
- **其余幻灵牌**：使魔／死神使者／咒语生成的牌立即加入当前手牌和牌组；隐秘复制立即加入两张；安卡、妖术保留永恒 Joker；灵质每次使用递增手牌惩罚；不符合使用条件时不会消耗牌。
- **Boss 失效**：梅花、黑桃、方块、红心对应失效牌画红叉；万能牌与涂抹小丑联动；受禁用影响的牌仍用于牌型构成，但本身不计分／不触发卡牌加成。眼睛、嘴巴、心灵感应的违规出牌会消耗一次出牌，但该手得 0 分，牌型提示红色划线。
- **翻面／强制牌**：房屋、车轮、印记（The Mark）、鱼儿逐次重抽的隐藏状态生效；猩红之心在出牌前标记失效 Joker；琥珀橡实把小丑牌翻面；蔚蓝铃铛强制选牌并防止取消。
- **巨蛇**：出牌或弃牌后强制抽 3 张，允许超过通常手牌容量。**手牌数量**在侧栏显示 `当前张数 / 通常容量`。
- **初始牌组／下注**：焦点只改边框颜色和样式，不再改底色。
- **多语言**：将静态菜单、主要牌名、牌效摘要、复杂牌详情和动态事件补上非中文回退；支持的 18 种语言并未声称每种都有完整的人工译本。

## 系统要求

- Python **3.10 或以上**，不需安装第三方 Python 软件包。
- **macOS**：Terminal 或 iTerm2。音频使用系统自带 `afplay`。
- **Windows 10 / 11**：推荐 **Windows Terminal**（PowerShell 标签页），音频使用系统自带 Windows PowerShell + .NET `PresentationCore`，不需额外 Python 音频依赖。若系统缺少相关多媒体组件，可用 `--no-music` 启动。
- 终端至少约 **120 列 × 50 行**，建议 **160 列 × 60 行**；请使用支持中文、扑克牌符号的等宽字体。游戏会尝试请求改变窗口大小，但并非所有终端支持，必要时请手动放大。

## macOS 启动

解压 ZIP 后进入项目文件夹，在 Terminal 运行：

```bash
cd ~/Downloads/Balatro_V15
python3 play.py
```

也可运行 `bash run.command`。macOS 游戏输入、音频和图形显示功能仍按此前版本运行。

## Windows 启动

1. 安装 Python 3.10+（安装时勾选「Add Python to PATH」，或者通过 `py` 启动器使用已安装的 Python）。
2. 使用 Windows 的“全部解压缩”把 ZIP 解压到本地文件夹，不要在 ZIP 预览窗口里运行脚本。
3. 双击游戏目录里的 **`run.bat`**，它会自动尝试 `py -3`，否则使用 `python`。
4. 或者打开 Windows Terminal 的 PowerShell，切换到游戏所在文件夹：

```powershell
cd "$HOME\Downloads\Balatro_V15"
py -3 play.py
```

如果 `py` 不存在，但 `python` 可用，就改成 `python play.py`。

如果窗口无法自动放大，可先手动调整 Windows Terminal 的窗口和字体尺寸。如果只是音频播放遇到问题，运行：

```powershell
py -3 play.py --no-music
```

完全跳过自动调整窗口与音乐：

```powershell
py -3 play.py --no-resize --no-music
```

### Windows 实现说明

- 控制器通过 Windows `msvcrt` 读取单键输入、WASD、方向键和 Enter，**不改变任何键位**。
- 使用 Windows 控制台 `ENABLE_VIRTUAL_TERMINAL_PROCESSING` 输出 ANSI 24 位彩色、备用屏幕和精确光标定位；游戏退出后恢复原控制台模式。
- 用户自行添加的 MP3（如已具备合法使用权限）在 Windows 上由 Windows PowerShell 的 WPF `MediaPlayer` 播放。曲目和场景与 Mac 完全一致；按 `C` 开关音乐。
- 两端共用 JSON 存档结构；操作系统各自在其用户主目录中保留游戏存档 `~/.terminal_arcana_v10_save.json` 和语言设置 `~/.balatro_terminal_settings.json`。复制存档文件至另一平台的用户主目录，即可在另一系统按 `L` 读档。
- 实际 Windows Terminal 的音乐输出、个别字体的双宽字符和自动调整窗口行为必须在 Windows 实机验证；开发环境完成的是跨平台代码路径与模拟测试，未声称已经在真实 Windows 设备上全部测试。

## 可选音乐：自行添加（仓库不包含音频）

**本仓库不提供 Balatro 原声音乐或其他受版权保护的 MP3。** 游戏支持可选背景音乐；不添加音乐也可以通过 `--no-music` 启动。请只使用通过合法渠道取得、且使用方式符合相关许可或授权的音频文件。拥有音乐的收听权限不一定意味着拥有再分发权限；不要把音频文件提交到公开仓库。

### 本地安装步骤

1. 从具有适当授权的来源取得兼容的 **MP3** 文件。
2. 打开游戏项目根目录中的 `assets/` 文件夹（如果没有则新建）。
3. 将五首音频文件放入 `assets/`，并使用下表中的**精确文件名**；区分大小写，注意下划线和扩展名。
4. 启动游戏，使用 `C` 开关音乐。若音乐无法播放，请先确认文件是实际 MP3 格式、文件名与音频模块配置一致；单纯重命名扩展名不能转换格式。

| 页面 / 场景 | 音乐 | 本地文件名 |
|---|---|---|
| 封面、难度选择、普通战斗、标准包、小丑包 | LouisF — Main Theme | `LouisF_main.mp3` |
| 商店 | LouisF — Shop Theme | `LouisF_shop.mp3` |
| Boss 准备 / Boss 战 | LouisF — Boss Theme | `LouisF_boss.mp3` |
| 奥秘包 / 幻灵包 | LouisF — Arcana Theme | `LouisF_arcana.mp3` |
| 天体包 | LouisF — Celestial Theme | `LouisF_celestial.mp3` |

> **文件名提示：** 上表采用项目先前使用的 `LouisF_*.mp3` 命名约定；发布前请以你本地 `arcana` 音频模块实际引用的路径和文件名核对。如代码使用不同名称，请相应调整表格，不要仅凭此表重命名音频。

预期目录结构：

```text
balatro-terminal/
├── play.py
├── README.md
├── .gitignore
├── arcana/
├── tests/
└── assets/
    ├── LouisF_main.mp3        # 本地添加，不上传 GitHub
    ├── LouisF_shop.mp3        # 本地添加，不上传 GitHub
    ├── LouisF_boss.mp3        # 本地添加，不上传 GitHub
    ├── LouisF_arcana.mp3      # 本地添加，不上传 GitHub
    └── LouisF_celestial.mp3   # 本地添加，不上传 GitHub
```

**无音乐启动：**

macOS：`python3 play.py --no-music`  
Windows：`py -3 play.py --no-music`

## 操作：沿用此前界面操作

| 按键 | 功能 |
|---|---|
| WASD / 方向键 | 导航；**只有初始牌组/难度页**使用 WASD 选牌组、方向键选难度 |
| Enter | 确认、战斗选牌、商店买卖、开包领取、使用 `I` 里的效果牌 |
| `P` / `O` | 出牌 / 弃牌；效果目标选择时 `P` 确认 |
| `I` | 持有 Joker、效果牌、整副牌组 |
| `E` | 查看当前焦点详情，再按 `E` 关闭；盲注准备页可在符合条件时更换 Boss |
| `X` | 所有牌型与等级 |
| `V` | 语言选择（18 种语言） |
| `H` / `F` / `G` | 帮助 / 效果图鉴 / Joker 图鉴 |
| `M` | 在 `I` 中调整 Joker 顺序 |
| Backspace | 在 `I` 页聚焦已持有 Joker 后出售（即使处于 Boss 战也可出售；永恒 Joker 无法出售）。可用于解除「翠绿叶片」的全牌失效。 |
| `T` / `N` / `R` / `Z` | 跳过盲注 / 下一关 / 商店刷新 / 放弃剩余开包选择 |
| `K` / `L` | 保存 / 读档 |
| `C` / `Q` / Esc | 开关音乐 / 保存退出 / 返回或取消 |

**语言**：简体中文、繁體中文、English、日本語、한국어、Français、Español、Deutsch、Italiano、Português (Brasil)、Русский、Nederlands、Türkçe、Polski、العربية、हिन्दी、Bahasa Indonesia、Tiếng Việt。主要导航和部分牌组/Boss 词条具备翻译或回退；复杂 Joker／塔罗／幻灵牌说明：非中文语言优先使用英文准确机制说明作为回退；动态的未知事件也用英文中性提示代替未翻译中文。**本版本并非 18 种语言的完整母语卡牌译本**；部分简体／繁体及特殊语言排版仍未完成逐字母人工校对。

**优惠券**：已购买优惠券不再从商店抽到；高级券依赖基础券；同一 Ante 未购买优惠券会保持，Boss 后才刷新。与 V13 相同。

## 自动化测试

```bash
python3 -m unittest discover -s tests -q
```

测试覆盖 18 张幻灵牌的效果、永久牌组更改、隐藏牌重抽、红叉及红色划线、Boss 零分但消耗手数、28 Boss 定义、翠绿叶片战斗中出售 Joker、蔚蓝铃铛自动选择、巨蛇超容量抽牌、非中文计分提示，以及此前 Windows 键盘扫描码映射、Win32 彩色模式与退出恢复、音乐命令、启动脚本等回归测试。Windows 平台专项测试使用 Win32 模拟对象，不能替代实机检查。

## 版权与项目性质 / Fan Project Disclaimer

This is an **unofficial, fan-made** terminal adaptation of *Balatro*. It is **not affiliated with, endorsed by, sponsored by, or officially associated with LocalThunk or Playstack**. Balatro and the original game's intellectual property belong to their respective owners. This repository does **not** include the original soundtrack. Users must supply any optional audio themselves and comply with applicable rights and licenses. No claim of ownership or official authorization is made.

欢迎反馈 Bug 和提出改进建议，但请不要向本仓库提交未经授权的原作音乐、图片或其他专有素材。
