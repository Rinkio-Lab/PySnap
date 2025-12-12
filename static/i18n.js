// i18n.js
export const i18n = {
    current: "zh",

    dict: {
        zh: {
            run: "运行",
            history: "历史",
            temp: "Temp",
            clear: "清空",
            timeout_enable: "启用超时保护",
            timeout: "超时(s)",
            modules: "模块解析",
            stdout: "stdout",
            stderr: "stderr",
            files: "操作/历史",
            no_output: "无输出",
            no_error: "无错误",
            click_load: "（点击历史或 TempFiles）",
            msg_done: "执行完成 ✔",
            msg_error: "执行失败",
            msg_network: "网络错误",
            settings: "设置",
            about: "关于",
            theme_light: "亮色",
            theme_dark: "暗色",
            theme_auto: "跟随系统",
            language: "语言",
            save_done: "设置已保存 ✔",
            no_import: "未检测到 import",
            file_none: "暂无临时文件",
            file_loaded: "已加载到编辑器",
            sidebar_collapse: "折叠",
            sidebar_expand: "展开"
        },
        en: {
            run: "Run",
            history: "History",
            temp: "Temp",
            clear: "Clear",
            timeout_enable: "Enable Timeout",
            timeout: "Timeout(s)",
            modules: "Modules",
            stdout: "stdout",
            stderr: "stderr",
            files: "Files/History",
            no_output: "No Output",
            no_error: "No Error",
            click_load: "(Click History or TempFiles)",
            msg_done: "Execution Done ✔",
            msg_error: "Execution Failed",
            msg_network: "Network Error",
            settings: "Settings",
            about: "About",
            theme_light: "Light",
            theme_dark: "Dark",
            theme_auto: "Auto",
            language: "Language",
            save_done: "Settings Saved ✔",
            no_import: "No imports detected",
            file_none: "No temporary files",
            file_loaded: "Loaded to editor",
            sidebar_collapse: "Collapse",
            sidebar_expand: "Expand"
        },
        jp: {
            run: "実行",
            history: "履歴",
            temp: "Temp",
            clear: "クリア",
            timeout_enable: "タイムアウト有効",
            timeout: "タイムアウト(s)",
            modules: "モジュール解析",
            stdout: "stdout",
            stderr: "stderr",
            files: "操作/履歴",
            no_output: "出力なし",
            no_error: "エラーなし",
            click_load: "（履歴または TempFiles をクリック）",
            msg_done: "実行完了 ✔",
            msg_error: "実行失敗",
            msg_network: "ネットワークエラー",
            settings: "設定",
            about: "情報",
            theme_light: "ライト",
            theme_dark: "ダーク",
            theme_auto: "システムに合わせる",
            language: "言語",
            save_done: "設定を保存 ✔",
            no_import: "import は検出されません",
            file_none: "一時ファイルなし",
            file_loaded: "エディタに読み込みました",
            sidebar_collapse: "折りたたむ",
            sidebar_expand: "展開"
        }
    },

    init() {
        const lang = navigator.language.toLowerCase();
        if (lang.startsWith("zh")) this.current = "zh";
        else if (lang.startsWith("ja")) this.current = "jp";
        else this.current = "en";
        this.apply();
    },

    set(lang) {
        if (this.dict[lang]) {
            this.current = lang;
            this.apply();
        }
    },

    t(key) {
        return this.dict[this.current][key] || key;
    },

    apply() {
        document.querySelectorAll("[data-i18n]").forEach(el => {
            const key = el.getAttribute("data-i18n");
            el.textContent = this.t(key);
        });
    }
};
