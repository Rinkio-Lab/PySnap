import { i18n } from "./i18n.js";

let editor = null;

/* ===========================
   初始化 Monaco
=========================== */
require(['vs/editor/editor.main'], () => {
    editor = monaco.editor.create(document.getElementById('editor'), {
        value: "# 欢迎使用 PySnap v0.3\nprint('Hello from PySnap')\n",
        language: 'python',
        theme: "vs-dark",
        fontSize: 14,
        minimap: { enabled: false },
        automaticLayout: true
    });
});

/* ===========================
   初始化 i18n
=========================== */
i18n.init();
const langSelect = document.getElementById("langSelect");
langSelect.value = i18n.current;
langSelect.onchange = e => i18n.set(e.target.value);

/* ===========================
   全局提示
=========================== */
function showMsg(text, type = "normal") {
    const box = document.getElementById("msg");
    box.textContent = text;
    box.style.borderColor = (type === "error") ? "rgba(255,120,120,0.5)" : "var(--glass-border)";
    box.classList.remove("hidden");
    setTimeout(() => box.classList.add("hidden"), 2500);
}

/* ===========================
   运行 Python 代码
=========================== */
async function runCode() {
    const code = editor.getValue();
    const timeout = Number(document.getElementById('timeout').value) || 5;
    const timeoutEnabled = document.getElementById('timeoutToggle').checked;

    document.getElementById('stdout').textContent = i18n.t("no_output");
    document.getElementById('stderr').textContent = '';

    try {
        const resp = await fetch('/run', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ code, timeout, timeout_enabled: timeoutEnabled })
        });
        const data = await resp.json();

        if (!data.ok) {
            document.getElementById('stdout').textContent = '';
            document.getElementById('stderr').textContent = data.error;
            showMsg(i18n.t("msg_error"), "error");
            return;
        }

        document.getElementById('stdout').textContent = data.result.stdout || i18n.t("no_output");
        document.getElementById('stderr').textContent = data.result.stderr || data.result.traceback || i18n.t("no_error");

        const imports = data.imports || [];
        const missing = data.missing || [];
        const modDiv = document.getElementById('modules');
        modDiv.innerHTML = imports.length
            ? imports.map(m =>
                missing.includes(m)
                    ? `<div class="missing">❌ ${m}</div>`
                    : `<div class="found">✔ ${m}</div>`
            ).join("")
            : i18n.t("no_import");

        loadTempFiles();
        showMsg(i18n.t("msg_done"));

    } catch (e) {
        document.getElementById('stderr').textContent = `请求失败：${e}`;
        showMsg(i18n.t("msg_network"), "error");
    }
}

/* ===========================
   加载临时文件
=========================== */
async function loadTempFiles() {
    try {
        const resp = await fetch('/files');
        const data = await resp.json();
        const area = document.getElementById('files');

        if (!data.ok) return;
        area.innerHTML = '';

        if (data.files.length === 0) {
            area.textContent = i18n.t("file_none");
            return;
        }

        data.files.forEach(f => {
            const div = document.createElement('div');
            div.style.marginBottom = "10px";

            div.innerHTML = `
        <div><strong>${f.name}</strong> (${Math.round(f.size)} bytes)</div>
        <div style="margin-top:6px; display:flex; gap:8px">
          <button class="glass-btn" onclick="viewFile('${f.name}')"><span class="material-icons">visibility</span>${i18n.t("run")}</button>
          <button class="glass-btn" onclick="downloadFile('${f.name}')"><span class="material-icons">download</span>${i18n.t("temp")}</button>
        </div>
      `;
            area.appendChild(div);
        });

    } catch (e) { console.error(e); }
}

async function viewFile(name) {
    const resp = await fetch(`/file/${encodeURIComponent(name)}`);
    const data = await resp.json();
    if (!data.ok) return showMsg(i18n.t("msg_error"), "error");

    editor.setValue(data.content);
    showMsg(i18n.t("file_loaded"));
}

function downloadFile(name) {
    location.href = `/download/${encodeURIComponent(name)}`;
}

/* ===========================
   清空临时目录
=========================== */
async function clearTemp() {
    const resp = await fetch('/clear', { method: 'DELETE' });
    const data = await resp.json();

    showMsg(`${i18n.t("clear")} ${data.deleted || 0} 个文件`);
    loadTempFiles();
}

/* ===========================
   历史记录
=========================== */
async function loadHistory() {
    const resp = await fetch('/history');
    const data = await resp.json();
    const area = document.getElementById("files");

    if (!data.ok) return showMsg(i18n.t("msg_error"), "error");

    area.innerHTML = `<pre class="glass-sub">${JSON.stringify(data.data, null, 2)}</pre>`;
    showMsg(i18n.t("history") + " ✔");
}

/* ===========================
   弹窗：设置 & 关于
=========================== */
const settingsModal = document.getElementById("settingsModal");
const aboutModal = document.getElementById("aboutModal");

document.getElementById("settingsBtn").onclick = () => settingsModal.classList.remove("hidden");
document.getElementById("aboutBtn").onclick = () => aboutModal.classList.remove("hidden");

document.getElementById("closeSettings").onclick = () => settingsModal.classList.add("hidden");
document.getElementById("closeAbout").onclick = () => aboutModal.classList.add("hidden");

/* ===========================
   设置：主题切换
=========================== */
document.querySelectorAll(".theme-btn").forEach(btn => {
    btn.onclick = () => {
        const t = btn.dataset.theme;
        document.body.dataset.theme = t;
        localStorage.setItem("theme", t);
        showMsg(`${i18n.t("theme_" + t)}`);
    };
});

// 从 localStorage 恢复
const saved = localStorage.getItem("theme");
if (saved) document.body.dataset.theme = saved;

/* ===========================
   设置：超时同步
=========================== */
document.getElementById("settingsBtn").onclick = () => {
    settingsModal.classList.remove("hidden");

    document.getElementById("timeoutToggle2").checked =
        document.getElementById("timeoutToggle").checked;

    document.getElementById("timeout2").value =
        document.getElementById("timeout").value;
};

document.getElementById("closeSettings").onclick = () => {
    document.getElementById("timeoutToggle").checked =
        document.getElementById("timeoutToggle2").checked;

    document.getElementById("timeout").value =
        document.getElementById("timeout2").value;

    settingsModal.classList.add("hidden");
    showMsg(i18n.t("save_done"));
};

/* ===========================
   绑定事件
=========================== */
document.getElementById('run').onclick = runCode;
document.getElementById('filesBtn').onclick = loadTempFiles;
document.getElementById('clearBtn').onclick = clearTemp;
document.getElementById('historyBtn').onclick = loadHistory;

// 自动加载临时文件
setTimeout(loadTempFiles, 600);
