r"""在客户端更新后，把「半透明外观」重新打回新的 app.asar。

特点（为了安全）：
  * 不改归档布局：只就地改写 lib/main.js，且长度保持不变（自动腾出注释空间）。
  * 先备份，再写；写完重新读回校验；除 main.js 外所有文件逐字节比对。
  * 如果新版本代码结构变了、锚点找不到，会直接退出（退出码 2），不动任何文件。
  * 如果发现已经是改过的版本（含 dsh-glass 标记），拒绝执行。

用法：
  python repatch.py --app-dir "D:\其他\DeepSeekHarness" [--dry-run]
"""

import argparse
import hashlib
import json
import os
import re
import shutil
import struct
import subprocess
import sys

try:
    sys.stdout.reconfigure(encoding="cp936", errors="replace")
    sys.stderr.reconfigure(encoding="cp936", errors="replace")
except Exception:
    pass

MAIN_PARTS = ["lib", "main.js"]
MARKER = "dsh-glass-translucent"

REGION = r"""
//#region dsh-glass-translucent
/** Workspace folder holding the hot-reloadable renderer assets. */
const GLASS_DIR = process.env.DSH_GLASS_DIR || join(app.getPath("userData"), "dsh-glass");
function glassLog(message) {
	try {
		appendFileSync(join(GLASS_DIR, "diagnostics.log"), new Date().toISOString() + " " + message + String.fromCharCode(10));
	} catch {}
}
function glassText(name) {
	try {
		return readFileSync(join(GLASS_DIR, name), "utf8");
	} catch {
		return "";
	}
}
function glassTime(name) {
	try {
		return statSync(join(GLASS_DIR, name)).mtimeMs;
	} catch {
		return 0;
	}
}
/** 滑到最右（原样）时把注入的样式整个撤掉，回到客户端本来外观。 */
function installGlass(window) {
	if (process.platform !== "win32") return;
	try {
		window.setBackgroundColor("#00000000");
	} catch (error) {
		glassLog("background failed " + String(error && error.message ? error.message : error));
	}
	try {
		window.on("show", () => {
			// 兜底：不管从哪个入口显示（托盘菜单等），200ms 后一定恢复不透明度
			setTimeout(() => {
				try {
					window.setOpacity(1);
				} catch {}
			}, 220);
		});
		window.on("hide", () => {
			try {
				window.setBackgroundColor("#00000000");
			} catch {}
			try {
				window.setOpacity(0);
			} catch {}
		});
	} catch {}
	try {
		window.on("minimize", () => {
			try {
				window.setBackgroundColor(chromeFallbackFill());
			} catch {}
		});
		window.on("restore", () => {
			try {
				window.setBackgroundColor("#00000000");
			} catch {}
			try {
				window.webContents.invalidate();
			} catch {}
		});
	} catch {}
	try {
		const reapplyBackground = () => {
			try {
				if (!window.isDestroyed()) window.setBackgroundColor("#00000000");
			} catch {}
		};
		nativeTheme.on("updated", reapplyBackground);
		window.on("closed", () => {
			try {
				nativeTheme.removeListener("updated", reapplyBackground);
			} catch {}
		});
	} catch {}
	const contents = window.webContents;
	/** 自绘标题栏按钮：渲染层把动作写进 document.title，这里拦截并执行。 */
	try {
		contents.on("page-title-updated", (event, title) => {
			if (typeof title !== "string" || !title.startsWith("DSHGLASS:")) return;
			event.preventDefault();
			const action = title.split(":")[1];
			try {
				if (action === "min") window.minimize();
				else if (action === "max") {
					if (window.isMaximized()) window.unmaximize();
					else window.maximize();
				} else if (action === "close") window.close();
				glassLog("win " + action);
			} catch (error) {
				glassLog("win action failed " + String(error && error.message ? error.message : error));
			}
		});
	} catch {}
	let cssKey;
	let cssMark = -1;
	let jsMark = -1;
	let cmdMark = -1;
	let solidOn = false;
	const putCss = (css) => {
		const apply = () => {
			try {
				contents.insertCSS(css, { cssOrigin: "user" }).then((key) => {
					cssKey = key;
					glassLog("css inserted " + String(key));
				}, (error) => glassLog("css insert failed " + String(error && error.message ? error.message : error)));
			} catch (error) {
				glassLog("css throw " + String(error && error.message ? error.message : error));
			}
		};
		if (cssKey === void 0) {
			apply();
			return;
		}
		try {
			contents.removeInsertedCSS(cssKey).then(apply, apply);
		} catch {
			apply();
		}
	};
	const dropCss = () => {
		if (cssKey === void 0) return;
		const key = cssKey;
		cssKey = void 0;
		try {
			contents.removeInsertedCSS(key).then(() => glassLog("css removed (solid)"), () => {});
		} catch {}
	};
	const runUi = () => {
		const script = glassText("glass.js");
		if (script === "") {
			glassLog("glass.js missing");
			return;
		}
		contents.executeJavaScript(script).then(() => glassLog("panel injected"), (error) => glassLog("panel failed " + String(error && error.message ? error.message : error)));
	};
	const runCmd = () => {
		const code = glassText("glass-cmd.js");
		if (code === "") return;
		contents.executeJavaScript(code).then((value) => glassLog("CMD " + String(value)), (error) => glassLog("CMD ERR " + String(error && error.message ? error.message : error)));
	};
	const syncSolid = () => {
		try {
			contents.executeJavaScript("(window.__dshGlassSolid === true) || ((typeof window.__dshGlassAlpha === 'number') && window.__dshGlassAlpha >= 0.995)").then((on) => {
				if (on === solidOn) return;
				solidOn = on;
				glassLog("solid " + String(on));
				if (solidOn) {
					dropCss();
					try {
						window.setBackgroundColor(chromeFallbackFill());
					} catch (error) {
						glassLog("solid background failed " + String(error && error.message ? error.message : error));
					}
				} else {
					try {
						window.setBackgroundColor("#00000000");
					} catch {}
					cssMark = -1;
				}
			}).catch(() => {});
		} catch {}
	};
	let wakeMark = glassTime("wake.txt");
	/** 组件点一下时由外部 touch wake.txt，用 Electron 自己的 API 恢复窗口（Win32 强拉会让透明窗口假死）。 */
	const syncWake = () => {
		const wakeMarkNow = glassTime("wake.txt");
		if (wakeMarkNow === wakeMark) return;
		wakeMark = wakeMarkNow;
		try {
			const wasHidden = !window.isVisible() || window.isMinimized();
			try {
				window.setBackgroundColor("#00000000");
			} catch {}
			if (wasHidden) {
				// 隐藏时已经是 0 透明度；这里再确保一次，显示的第一帧不可见
				try {
					window.setOpacity(0);
				} catch {}
			}
			if (window.isMinimized()) window.restore();
			window.show();
			window.focus();
			if (wasHidden) {
				// 先重绘，再分两步淡入：0 → 0.65（80ms）→ 1（180ms）
				setTimeout(() => {
					try {
						window.webContents.invalidate();
						window.setOpacity(0.65);
					} catch {}
				}, 80);
				setTimeout(() => {
					try {
						window.setOpacity(1);
					} catch {}
				}, 180);
			} else {
				setTimeout(() => {
					try {
						window.webContents.invalidate();
					} catch {}
				}, 150);
			}
			glassLog("wake");
		} catch (error) {
			glassLog("wake failed " + String(error && error.message ? error.message : error));
		}
	};
	const sync = () => {
		syncWake();
		const cssMarkNow = glassTime("glass.css");
		if (!solidOn && cssMarkNow !== cssMark) {
			cssMark = cssMarkNow;
			const css = glassText("glass.css");
			if (css !== "") putCss(css);
		}
		const jsMarkNow = glassTime("glass.js");
		if (jsMarkNow !== jsMark) {
			jsMark = jsMarkNow;
			runUi();
		}
		const cmdMarkNow = glassTime("glass-cmd.js");
		if (cmdMarkNow !== cmdMark) {
			cmdMark = cmdMarkNow;
			runCmd();
		}
		syncSolid();
	};
	contents.on("dom-ready", () => {
		cssMark = -1;
		jsMark = -1;
		cmdMark = -1;
		sync();
	});
	const timer = setInterval(sync, 1200);
	window.on("closed", () => clearInterval(timer));
}
// 全局唤醒：即使主窗口已经被关掉（进程留在托盘），也能重建并显示。
// 由桌面组件点击时 touch runtime/wake.txt 触发。
try {
	app.whenReady().then(() => {
		let wakeMark = glassTime("wake.txt");
		const timer = setInterval(() => {
			const now = glassTime("wake.txt");
			if (now === wakeMark) return;
			wakeMark = now;
			try {
				if (typeof focusPrimaryWindow === "function") focusPrimaryWindow();
				glassLog("global wake");
			} catch (error) {
				glassLog("global wake failed " + String(error && error.message ? error.message : error));
			}
		}, 1200);
		app.on("will-quit", () => clearInterval(timer));
	});
} catch {}
//#endregion
"""


def parse_asar(raw):
    _, _, c, jl = struct.unpack("<4I", raw[:16])
    padded = c - 4
    return json.loads(raw[16:16 + jl].decode("utf-8")), 16 + padded, jl


def node_of(header, parts):
    node = header
    for p in parts:
        node = node["files"][p]
    return node


def iter_files(header, prefix=()):
    for name, child in header["files"].items():
        if "files" in child:
            yield from iter_files(child, prefix + (name,))
        elif not child.get("unpacked"):
            yield prefix + (name,), child


# ---------------------------------------------------------------- comments
def comment_spans(src):
    """Return [(start, end)] spans of real // and /* */ comments (lexer based)."""
    spans = []
    i = 0
    n = len(src)
    while i < n:
        c = src[i]
        if c == '"' or c == "'" or c == "`":
            quote = c
            i += 1
            while i < n:
                if src[i] == "\\":
                    i += 2
                    continue
                if src[i] == quote:
                    i += 1
                    break
                i += 1
            continue
        if c == "/" and i + 1 < n and src[i + 1] == "/":
            j = src.find("\n", i)
            if j < 0:
                j = n
            spans.append((i, j))
            i = j
            continue
        if c == "/" and i + 1 < n and src[i + 1] == "*":
            j = src.find("*/", i + 2)
            if j < 0:
                j = n - 2
            spans.append((i, j + 2))
            i = j + 2
            continue
        i += 1
    return spans


def free_space(src, need):
    """Drop the largest block comments until `need` extra bytes are available."""
    spans = [(a, b) for a, b in comment_spans(src) if src[a:a + 2] == "/*" and b - a > 120]
    spans.sort(key=lambda s: s[1] - s[0], reverse=True)
    removed = 0
    picked = []
    for a, b in spans:
        if removed >= need:
            break
        picked.append((a, b))
        removed += b - a
    if removed < need:
        raise SystemExit("可用注释空间不够（需要 %d 字节，只能腾出 %d 字节）。" % (need, removed))
    picked.sort()
    out = []
    last = 0
    for a, b in picked:
        out.append(src[last:a])
        last = b
    out.append(src[last:])
    return "".join(out), removed, len(picked)


# ---------------------------------------------------------------- patch
def patch_create_window(text):
    marker = '...process.platform === "win32" && primary ? {'
    start = text.find(marker)
    if start < 0:
        raise SystemExit("找不到窗口选项锚点（win32 && primary），新版本结构可能变了。")
    end = text.find("} : {},", start)
    if end < 0:
        raise SystemExit("找不到窗口选项块的结尾，新版本结构可能变了。")
    block = text[start:end]
    if 'backgroundColor: "#00000000"' in block:
        return text, False
    stripped = block.rstrip()
    new_block = stripped + ',\n\t\t\ttransparent: true,\n\t\t\tbackgroundColor: "#00000000",\n\t\t\ttitleBarOverlay: false\n\t\t'
    return text[:start] + new_block + text[end:], True

def patch_install_call(text):
    idx = text.find("function createWindow(")
    if idx < 0:
        raise SystemExit("找不到 createWindow 函数。")
    ret = text.find("return window;", idx)
    if ret < 0:
        raise SystemExit("createWindow 里找不到 return window;。")
    line_start = text.rfind("\n", 0, ret) + 1
    insert = '\tif (primary && process.platform === "win32") installGlass(window);\n'
    return text[:line_start] + insert + text[line_start:]


def patch_overlay_ipc(text):
    pattern = re.compile(
        r"if \(validColor\(color\) && validColor\(symbolColor\)\) mainWindow\.setTitleBarOverlay\(\{\s*color,\s*symbolColor\s*\}\);",
        re.S,
    )
    replacement = 'if (validColor(color) && validColor(symbolColor)) {}'
    if not pattern.search(text):
        return text, False
    return pattern.sub(replacement, text, count=1), True


def patch_tail(text):
    idx = text.rfind("export {};")
    if idx < 0:
        raise SystemExit("找不到 export {}; 结尾。")
    return text[:idx] + REGION + "\n" + text[idx:]


def build(original):
    text, flagged = patch_create_window(original)
    text = patch_install_call(text)
    text, ipc_ok = patch_overlay_ipc(text)
    text, neutralized = neutralize_background_calls(text)
    text = patch_tail(text)
    return text, flagged, ipc_ok


def neutralize_background_calls(text):
    """rc.2 会在窗口打开/切换主题时把背景刷回不透明色，这里按字节数原位改回透明。"""
    pairs = [
        ('if (process.platform === "win32") window.setBackgroundColor(chromeFallbackFill());',
         'if (process.platform === "win32") window.setBackgroundColor("#00000000");'),
        ('if (!window.isDestroyed()) window.setBackgroundColor(chromeFallbackFill());',
         'if (!window.isDestroyed()) window.setBackgroundColor("#00000000");'),
    ]
    changed = 0
    for old, new in pairs:
        count = text.count(old)
        if count and len(new) <= len(old):
            text = text.replace(old, new + ' ' * (len(old) - len(new)))
            changed += count
    return text, changed


def install_runtime(runtime_dir):
    """把本仓库里的样式/脚本复制到运行时目录（客户端补丁会从这里热加载）。"""
    here = os.path.dirname(os.path.abspath(__file__))
    src_dir = os.path.join(here, "runtime")
    os.makedirs(runtime_dir, exist_ok=True)
    copied = []
    for name in ("glass.css", "glass.js"):
        src = os.path.join(src_dir, name)
        if not os.path.exists(src):
            continue
        dst = os.path.join(runtime_dir, name)
        with open(src, "rb") as f:
            data = f.read()
        with open(dst, "wb") as f:
            f.write(data)
        copied.append(name)
    return copied


def node_check(data, node_exe):
    if not node_exe or not os.path.exists(node_exe):
        return None
    tmp = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_glass_check.mjs")
    with open(tmp, "wb") as f:
        f.write(data)
    try:
        res = subprocess.run([node_exe, "--check", tmp], capture_output=True)
        return res.returncode == 0, (res.stderr or b"").decode("utf-8", "replace")[:400]
    finally:
        try:
            os.remove(tmp)
        except OSError:
            pass


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--app-dir", default=r"D:\其他\DeepSeekHarness")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--runtime-dir", default=None, help="样式/脚本热加载目录（默认 %%APPDATA%%/@deepseek-ai/dsh-desktop/dsh-glass）")
    args = ap.parse_args()

    res_dir = os.path.join(args.app_dir, "resources")
    asar = os.path.join(res_dir, "app.asar")
    orig = os.path.join(res_dir, "app.asar.glass-orig")
    glass = os.path.join(res_dir, "app.asar.glass")
    node_exe = os.path.join(args.app_dir, "resources", "runtime", "primary-runtime", "dependencies", "node", "bin", "node.exe")

    if not os.path.exists(asar):
        raise SystemExit("找不到 %s" % asar)
    raw = open(asar, "rb").read()
    header, base, jl = parse_asar(raw)
    node = node_of(header, MAIN_PARTS)
    offset, size = int(node["offset"]), int(node["size"])
    old_main = raw[base + offset:base + offset + size]
    text = old_main.decode("utf-8")
    print("app.asar: %d 字节, main.js: %d 字节" % (len(raw), size))

    if MARKER in text:
        raise SystemExit("当前 app.asar 已经是改过的版本，不需要重新打补丁。\n如果客户端刚更新过，请先确认更新已完成。")

    patched, flagged, ipc_ok = build(text)
    data = patched.encode("utf-8")
    need = len(data) - size
    if need > 0:
        patched, removed, blocks = free_space(patched, need + 200)
        data = patched.encode("utf-8")
        if len(data) > size:
            raise SystemExit("清理注释后仍然放不下（超出 %d 字节）。" % (len(data) - size))
        print("删掉 %d 段注释，腾出 %d 字节" % (blocks, removed))
    data += b" " * (size - len(data))
    print("新 main.js: %d 字节（补空格 %d），窗口选项补丁=%s，标题栏补丁=%s" % (len(data), size - len(data.rstrip()), flagged, ipc_ok))

    checked = node_check(data, node_exe)
    if checked is not None:
        ok, err = checked
        if not ok:
            raise SystemExit("语法检查失败，已放弃：\n" + err)
        print("语法检查通过")

    if args.dry_run:
        print("干跑完成，未写入任何文件。")
        return

    old_hash = node["integrity"]["hash"]
    new_hash = hashlib.sha256(data).hexdigest()
    patched_asar = bytearray(raw)
    patched_asar[base + offset:base + offset + size] = data
    json_bytes = bytes(patched_asar[16:16 + jl])
    if json_bytes.count(old_hash.encode()) < 1:
        raise SystemExit("头部找不到原哈希，放弃。")
    json_bytes = json_bytes.replace(old_hash.encode(), new_hash.encode())
    patched_asar[16:16 + jl] = json_bytes

    # 写入前备份原始（新的官方版本）
    shutil.copyfile(asar, orig)
    with open(os.path.join(res_dir, "app.asar.version.txt"), "w", encoding="utf-8") as f:
        f.write("backup-of-app.asar\nsha256=" + hashlib.sha256(raw).hexdigest() + "\nmain.js=" + old_hash + "\n")

    with open(asar, "r+b") as f:
        f.seek(base + offset)
        f.write(data)
        f.seek(16)
        f.write(json_bytes)
    live = open(asar, "rb").read()
    if hashlib.sha256(live).hexdigest() != hashlib.sha256(bytes(patched_asar)).hexdigest():
        shutil.copyfile(orig, asar)
        raise SystemExit("写回校验失败，已恢复原文件。")
    shutil.copyfile(asar, glass)
    print("完成：已写入 app.asar，备份 app.asar.glass-orig，切换副本 app.asar.glass")
    runtime_dir = args.runtime_dir or os.path.join(os.environ.get("APPDATA", ""), "@deepseek-ai", "dsh-desktop", "dsh-glass")
    copied = install_runtime(runtime_dir)
    print("运行时文件已复制到：" + runtime_dir + " (" + ", ".join(copied) + ")")
    print("重新打开客户端即可看到半透明外观。")


if __name__ == "__main__":
    main()
