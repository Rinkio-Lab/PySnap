# app.py
# FastAPI 后端：提供 / , /run, /history, /file/{name}, /clear 等接口
import time
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from pathlib import Path
import uvicorn
from utils import runner

app = FastAPI(title="PySnap - 临时代码执行器 v0.2")

# 挂载静态文件夹
app.mount("/static", StaticFiles(directory="static"), name="static")


class CodeInput(BaseModel):
    code: str
    timeout: float = 5.0
    timeout_enabled: bool = True


@app.get("/", response_class=HTMLResponse)
async def index():
    index_path = Path("static") / "index.html"
    if not index_path.exists():
        return HTMLResponse("<h1>index.html not found</h1>", status_code=404)
    return FileResponse(index_path)


@app.post("/run")
async def run_code(payload: CodeInput):
    code = payload.code
    timeout = payload.timeout
    timeout_enabled = payload.timeout_enabled

    # 1) AST 安全检查
    is_safe, msg = runner._ast_safety_check(code)
    if not is_safe:
        return JSONResponse(
            {"ok": False, "error": f"安全检查失败：{msg}"}, status_code=400
        )

    # 2) 扫描 imports & 检查本地安装情况
    imports = runner.scan_imports(code)
    found, missing = runner.analyze_imports_against_env(imports)

    # 3) 保存临时文件
    path = runner.save_code_to_temp(code)

    # 4) 执行（子进程）
    res = runner.execute_file(path, timeout=timeout, timeout_enabled=timeout_enabled)

    # 5) 写历史（包含 meta 信息）
    entry = {
        "timestamp": int(time.time() * 1000),
        "filename": path.name,
        "execution": {
            "stdout": res.get("stdout"),
            "stderr": res.get("stderr"),
            "returncode": res.get("returncode"),
            "timeout": res.get("timeout"),
        },
        "meta": {
            "imports": imports,
            "found_imports": found,
            "missing_imports": missing,
            "timeout_sec": timeout,
            "timeout_enabled": bool(timeout_enabled),
            "safe_check": True,
        },
    }
    try:
        runner.save_run_history(entry)
    except Exception:
        pass  # 历史写失败不影响主流程

    return {
        "ok": True,
        "file": path.name,
        "imports": imports,
        "found": found,
        "missing": missing,
        "result": res,
    }


@app.get("/history")
async def history(date: str = None):
    # date 格式 YYYYMMDD，可选
    return runner.list_history(date_str=date)


@app.get("/files")
async def files_list(limit: int = 100):
    return {"ok": True, "files": runner.list_temp_files(limit=limit)}


@app.get("/file/{name}")
async def get_file(name: str):
    try:
        content = runner.read_temp_file(name)
        return {"ok": True, "name": name, "content": content}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found")


@app.get("/download/{name}")
async def download_file(name: str):
    p = runner.BASE_TEMP_DIR / name
    if not p.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(p, filename=name, media_type="text/x-python")


@app.delete("/clear")
async def clear():
    n = runner.clear_temp_files()
    return {"ok": True, "deleted": n}


@app.get("/{name}")
async def get_static(name: str):
    # 如果以ja/css等结尾，则返回静态文件
    if name.endswith((".js", ".css", ".html", ".ico")):
        p = Path(__file__).parent / "static" / name
        if not p.exists():
            raise HTTPException(status_code=404, detail="File not found")
        return FileResponse(p, filename=name)
    # 否则返回 404
    raise HTTPException(status_code=404, detail="Not found")


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)
