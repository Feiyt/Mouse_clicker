# 鼠标连点器 (Mouse Clicker)

一个基于 Python tkinter 的简单鼠标连点器工具。

## 安装依赖

本项目推荐使用 [uv](https://github.com/astral-sh/uv) 进行依赖管理。

### 使用 uv (推荐)

如果你安装了 `uv`，可以直接同步环境：

```bash
uv sync
```

或者直接运行程序（会自动安装依赖）：

```bash
uv run main.py
```

### 使用 pip (传统方式)

如果不使用 uv，也可以通过 pip 安装依赖：

```bash
pip install -r requirements.txt
```

主要依赖库：
- `pyautogui`
- `pynput`

## 使用说明

1. **运行程序**：参考上述启动命令。
2. **设定目标**：
   - 点击 **"选择位置"** 按钮。
   - 移动十字光标至目标位置，点击 **左键** 确认锁定。
   - *（在此过程中按 `ESC` 或鼠标右键可取消）*
3. **自动运行**：位置锁定后，自动开始连续点击。
4. **快捷控制**：
   - `Ctrl + ,` : 暂停 / 继续
   - `Ctrl + .` : 退出程序
