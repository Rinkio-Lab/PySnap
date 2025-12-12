# PySnap — 临时 Python 代码执行器

一个 *轻量・现代・安全* 的本地 Python 代码执行 WebUI
让你随时写点 Python、小实验、小片段、调库、测语法——像 VS Code 一样爽！🎉

> ✔ 无需启动完整 IDE
> ✔ 自动保存临时代码
> ✔ 提供执行历史
> ✔ 支持 import 检测 & 缺失模块提示
> ✔ 支持超时保护
> ✔ 内置 Monaco Editor（VS Code 的编辑器内核）

---

## ✨ 核心特性

### 🌈 1. VS Code 级编辑体验（Monaco Editor）

* 语法高亮
* 自动补全
* 支持 Tab 缩进
* 类似 VS Code 的深色主题

让「写小段 Python」从未如此舒服。

---

### ⚙ 2. 自动生成临时代码文件

执行代码前，会将你的代码写入：

```
%TEMP%/cn.linko.PySnap/TempCodes/{timestamp}.py
```

你可以随时查看、下载、保存这些临时文件。

---

### 📜 3. 每日执行历史（JSON）

每天自动生成：

```
%TEMP%/cn.linko.PySnap/History/{YYYYMMDD}.json
```

记录包括：

* 执行代码文件名
* stdout / stderr
* return code
* 超时信息
* 导入模块列表
* 缺失模块
* 执行时间戳

非常适合调试记录、学习归档。

---

### 🧩 4. 自动扫描 import 并检测缺失模块

通过 AST 自动解析：

```python
import xxx
from yyy import z
```

并对比本地 Python 环境，给出：

* ✔ 已安装模块（绿色）
* ✘ 缺失模块（红色，提醒你是否要 pip install）

特别适合快速测试第三方库。

---

### ⏱ 5. 可选的超时执行保护

开启后，代码执行超过设定秒数将被终止，防止：

* 死循环
* 网络等待
* 无限递归

你可以自由启用 / 禁用超时。

---

### 🧼 6. 一键清空临时代码

临时目录满了？点一下即可清空所有 `.py`。

---

## 🖼 项目结构

```
PySnap/
├─ app.py                 # FastAPI 后端
├─ utils/
│   └─ runner.py          # 代码执行逻辑
└─ static/
   ├─ index.html          # 前端页面
   ├─ style.css           # 前端样式
   ├─ app.js              # 前端逻辑
   └─ i18n.js             # 前端多语言支持
```

---

## 🚀 启动方式

### 1. 克隆项目

```bash
git clone https://github.com/Rinkio-Lab/PySnap
cd PySnap
```

### 2. 安装依赖（使用 uv）

```bash
uv sync
```

### 3. 运行

```bash
uv run uvicorn app:app --reload --host 127.0.0.1 --port 8000
```

然后访问：

```
http://127.0.0.1:8000
```

---

## 🐍 安全提示（重要）

PySnap 不是沙盒，它只是做了基础安全限制：

* 禁止 import 高危险模块（os、subprocess 等）
* 禁止使用 eval、exec、**import**
* 子进程执行隔离

⚠ **不要用于：**

* 执行不可信来源代码
* 运行恶意脚本
* 提供公网访问

这是一个 *本地开发工具*。

---

## ❤️ 作者

**Linko** - 2025 LimeBow Studios

### 提示

* 本项目仅供学习和研究使用，请勿用于非法用途
* 本项目不包含任何恶意代码，请放心使用
* 如有疑问，请随时联系作者

---

## 📝 许可证

本项目遵循 [MIT 许可证](LICENSE)。