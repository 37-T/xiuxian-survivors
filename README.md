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
- 升级时按 `1`、`2`、`3` 选择突破，或用鼠标点击
- 菜单和结算界面可按 `Enter` 开始或重新开始
- `F11`：切换全屏

一局约 8 分钟。灵剑会自动追踪附近妖兽；收集灵气升级后，在三种随机功法中选择一种。最后阶段会出现秘境精英。

开始前可在菜单中选择男性修士云归或女性修士洛璃，方向键也可切换；选择只影响外观。人物与妖兽使用随项目附带的 CC0 像素素材，来源与作者列于 [`assets/third_party/CREDITS.md`](assets/third_party/CREDITS.md)。
