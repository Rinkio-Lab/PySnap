# utils/runner.py
# 负责：保存临时文件、执行临时文件、AST 安全检查、导入扫描、历史存储
import tempfile
from pathlib import Path
import time
import subprocess
import sys
import ast
import traceback
import json
from datetime import datetime
from typing import Tuple, Dict, List, Any

# ---------- 根路径 ----------
BASE_TEMP_DIR = Path(tempfile.gettempdir()) / "cn.linko.PySnap" / "TempCodes"
HISTORY_DIR = Path(tempfile.gettempdir()) / "cn.linko.PySnap" / "History"
BASE_TEMP_DIR.mkdir(parents=True, exist_ok=True)
HISTORY_DIR.mkdir(parents=True, exist_ok=True)

# ---------- 黑名单（初版静态检查） ----------
BLACKLISTED_MODULES = {
    "os",
    "subprocess",
    "socket",
    "shutil",
    "psutil",
    "multiprocessing",
}
BLACKLISTED_NAMES = {"__import__", "exec", "eval"}  # open 可按需放行


# ---------- 文件名生成 ----------
def _timestamp_name() -> str:
    return f"{int(time.time() * 1000)}.py"


def save_code_to_temp(code: str) -> Path:
    """保存代码为临时文件并返回 Path"""
    path = BASE_TEMP_DIR / _timestamp_name()
    path.write_text(code, encoding="utf-8")
    return path


def list_temp_files(limit: int = 100) -> List[Dict[str, Any]]:
    """列出临时文件（按时间倒序）"""
    files = sorted(
        BASE_TEMP_DIR.glob("*.py"), key=lambda p: p.stat().st_mtime, reverse=True
    )
    result = []
    for p in files[:limit]:
        result.append(
            {
                "name": p.name,
                "path": str(p),
                "size": p.stat().st_size,
                "mtime": p.stat().st_mtime,
            }
        )
    return result


def read_temp_file(name: str) -> str:
    p = BASE_TEMP_DIR / name
    if not p.exists() or not p.is_file():
        raise FileNotFoundError("文件不存在")
    return p.read_text(encoding="utf-8")


def clear_temp_files() -> int:
    count = 0
    for p in BASE_TEMP_DIR.glob("*.py"):
        try:
            p.unlink()
            count += 1
        except Exception:
            pass
    return count


# ---------- AST 安全检查 ----------
def _ast_safety_check(code: str) -> Tuple[bool, str]:
    """
    简单 AST 静态检查：
    - 禁止导入 BLACKLISTED_MODULES
    - 禁止使用 BLACKLISTED_NAMES（如 exec/eval/__import__）
    注：仅为第一道防线，非完全沙盒。
    """
    try:
        tree = ast.parse(code)
    except Exception as e:
        return False, f"无法解析代码：{e}"

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for n in node.names:
                if n.name.split(".")[0] in BLACKLISTED_MODULES:
                    return False, f"禁止导入模块：{n.name}"
        if isinstance(node, ast.ImportFrom):
            if (node.module or "").split(".")[0] in BLACKLISTED_MODULES:
                return False, f"禁止从模块导入：{node.module}"
        if isinstance(node, ast.Name):
            if node.id in BLACKLISTED_NAMES:
                return False, f"禁止使用危险内建名：{node.id}"
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name) and func.id in BLACKLISTED_NAMES:
                return False, f"禁止调用危险函数：{func.id}"

    return True, "通过安全检查"


# ---------- 导入扫描 ----------
def scan_imports(code: str) -> List[str]:
    """用 AST 提取顶层导入的模块名（简单拆分到顶级包名）"""
    mods = set()
    try:
        tree = ast.parse(code)
    except Exception:
        return []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for n in node.names:
                mods.add(n.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                mods.add(node.module.split(".")[0])
    return sorted(mods)


# ---------- 本地已安装包检测 ----------
def get_installed_packages() -> set:
    """
    获取当前环境下已安装包的关键字集合（小写）。
    使用 importlib.metadata（py3.8+）或 pkg_resources 回退。
    """
    try:
        # Python 3.8+
        from importlib import metadata as importlib_metadata

        pkgs = {
            dist.metadata["Name"].lower() for dist in importlib_metadata.distributions()
        }
        # 以上在某些平台 metadata['Name'] 可能抛 KeyError，下面再回退到 simpler approach
        if not pkgs:
            raise Exception()
        return pkgs
    except Exception:
        try:
            import pkg_resources

            return {pkg.key for pkg in pkg_resources.working_set}
        except Exception:
            # 最后回退：只有 stdlib，返回空集合（会被判为 missing）
            return set()


def analyze_imports_against_env(
    imported_modules: List[str],
) -> Tuple[List[str], List[str]]:
    """
    返回 (found, missing)
    - found: 在已安装包列表中发现的模块名（尽量小写比对）
    - missing: 未发现的模块（供前端显示）
    """
    installed = get_installed_packages()
    found = []
    missing = []
    for m in imported_modules:
        if not m:
            continue
        if m.lower() in installed:
            found.append(m)
        else:
            # 额外判断内置模块（简单 check）: 如果能 import 成功则认为存在（可避免某些 stdlib 被误判）
            try:
                __import__(m)
                found.append(m)
            except Exception:
                missing.append(m)
    return found, missing


# ---------- 执行临时文件（子进程） ----------
def execute_file(
    path: Path, timeout: float = 5.0, timeout_enabled: bool = True
) -> Dict:
    """
    使用子进程执行临时文件，捕获 stdout/stderr。
    - timeout_enabled: False 则不传 timeout（或使用非常大的值）
    返回 dict：stdout, stderr, returncode, timeout(bool), traceback
    """
    result = {
        "stdout": "",
        "stderr": "",
        "returncode": None,
        "timeout": False,
        "traceback": None,
    }

    python_exec = sys.executable
    cmd = [python_exec, str(path)]

    try:
        proc = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        if timeout_enabled:
            out, err = proc.communicate(timeout=timeout)
        else:
            out, err = proc.communicate()
        result["stdout"] = out
        result["stderr"] = err
        result["returncode"] = proc.returncode
    except subprocess.TimeoutExpired:
        try:
            proc.kill()
        except Exception:
            pass
        result["timeout"] = True
        result["stderr"] = (
            result["stderr"] or ""
        ) + f"\n执行超时（>{timeout}s），已被终止。"
    except Exception as e:
        result["traceback"] = traceback.format_exc()
        result["stderr"] = str(e)

    return result


# ---------- 历史保存 ----------
def _today_filename() -> str:
    return datetime.now().strftime("%Y%m%d") + ".json"


def save_run_history(entry: Dict) -> None:
    """
    将单次运行信息追加到当日历史文件中。
    entry 格式建议：
    {
      "timestamp": 123456789,
      "filename": "....py",
      "execution": { ... },
      "meta": { "imports": [...], "missing": [...], "timeout_sec": 5.0, "safe_check": True }
    }
    """
    file = HISTORY_DIR / _today_filename()
    if file.exists():
        try:
            data = json.loads(file.read_text(encoding="utf-8"))
        except Exception:
            data = {"history": []}
    else:
        data = {"history": []}
    data.setdefault("history", []).append(entry)
    file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def list_history(date_str: str = None) -> Dict:
    """
    如果 date_str 提供（格式 YYYYMMDD）则返回该文件内容，否则返回当日历史或列出所有历史文件。
    返回 {"ok": True, "data": ...}
    """
    if date_str:
        file = HISTORY_DIR / f"{date_str}.json"
        if not file.exists():
            return {"ok": False, "error": "No history for date"}
        return {"ok": True, "data": json.loads(file.read_text(encoding="utf-8"))}
    # 默认返回今天
    file = HISTORY_DIR / _today_filename()
    if not file.exists():
        return {"ok": True, "data": {"history": []}}
    return {"ok": True, "data": json.loads(file.read_text(encoding="utf-8"))}
