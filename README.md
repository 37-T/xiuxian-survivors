# 修仙幸存者

一个用 Python 和 pygame-ce 制作的修仙题材像素风生存游戏 Demo。pygame-ce 与游戏代码使用的 `pygame` 模块接口兼容，无需下载图片或音效素材。

## 启动

需要 Python 3.10 或更高版本。Windows 可在项目目录运行：

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python main.py
```

如果 `py` 不可用，请先从 [python.org](https://www.python.org/downloads/) 安装 Python，并启用安装器中的 PATH 选项。首次启动时需要联网安装 Pygame。

## 操作

- `W A S D` / 方向键：移动
- `P` / `Esc`：暂停或继续
- 切换到其他窗口时自动暂停
- 升级时按 `1`、`2`、`3` 选择突破，或用鼠标点击
- 菜单和结算界面可按 `Enter` 开始或重新开始
- `F11`：切换全屏

游戏默认以 1280×720 窗口显示，可拖动窗口调整大小。画面按 16:9 比例适配窗口，并使用最近邻缩放保持像素边缘清晰；窗口比例不同时会在两侧或上下留出背景边框。

一局约 8 分钟。秘境会从山门古道转入荒野山谷，最终进入毒沼灵窟。乌鸦妖会保持距离发射羽刃，妖狼持续追猎并近身撕咬；敌人轮廓与敌方攻击以亮红色突出显示。灵剑会自动追踪附近妖兽。收集灵气升级后，在三种随机功法中选择一种。八分钟后毒沼蛙君登场，会喷吐毒泡并留下毒池。

开始前可在菜单中选择男性修士云归或女性修士洛璃，方向键也可切换。云归以高速灵剑追击单个目标；洛璃以较慢的火球攻击并造成范围爆燃。角色和妖兽像素图均基于项目所有者提供的参考图生成；素材说明见 [`assets/third_party/CREDITS.md`](assets/third_party/CREDITS.md)。
