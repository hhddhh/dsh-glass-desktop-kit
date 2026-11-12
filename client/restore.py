r"""在「原生 / 半透明」两份 app.asar 之间切换，带版本校验，避免用旧版本覆盖新版本。

用法：
  python restore.py --app-dir "D:\其他\DeepSeekHarness" --mode orig   # 恢复原生
  python restore.py --app-dir "D:\其他\DeepSeekHarness" --mode glass  # 切到半透明
  加 --force 可跳过版本一致性检查（应急用）。
"""

import argparse
import hashlib
import json
import os
import shutil
import struct
import sys

try:
    sys.stdout.reconfigure(encoding="cp936", errors="replace")
except Exception:
    pass


def asar_version(path):
    with open(path, "rb") as f:
        head = f.read(16)
        _, _, c, jl = struct.unpack("<4I", head)
        padded = c - 4
        js = f.read(jl).decode("utf-8", "replace")
    header = json.loads(js)
    pkg = header["files"].get("package.json", {})
    if "files" in pkg or "size" not in pkg:
        return None, None
    with open(path, "rb") as f:
        _, _, c, jl = struct.unpack("<4I", f.read(16))
        f.seek(16 + (c - 4) + int(pkg["offset"]))
        data = f.read(int(pkg["size"]))
    try:
        return json.loads(data.decode("utf-8")) .get("version"), None
    except Exception as exc:
        return None, str(exc)


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--app-dir", default=r"D:\其他\DeepSeekHarness")
    ap.add_argument("--mode", choices=["orig", "glass"], required=True)
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    res = os.path.join(args.app_dir, "resources")
    live = os.path.join(res, "app.asar")
    src = os.path.join(res, "app.asar.glass-orig" if args.mode == "orig" else "app.asar.glass")
    if not os.path.exists(live):
        raise SystemExit("找不到 %s" % live)
    if not os.path.exists(src):
        raise SystemExit("找不到目标文件 %s" % src)

    lv, lerr = asar_version(live)
    sv, serr = asar_version(src)
    print("当前 app.asar 版本: %s" % (lv or ("无法读取" + ("(" + lerr + ")" if lerr else ""))))
    print("要换成的版本: %s (%s)" % (sv or "无法读取", os.path.basename(src)))
    if lv and sv and lv != sv and not args.force:
        raise SystemExit(
            "版本不一致：当前 %s，目标 %s。\n"
            "这通常说明客户端刚更新过，用旧备份覆盖会让版本对不上。\n"
            "请改用「更新后重新应用半透明.cmd」重新打补丁。" % (lv, sv)
        )
    if args.dry_run:
        print("检查通过（干跑，未写入）。")
        return
    shutil.copyfile(src, live)
    print("已写入。当前 app.asar sha256 = %s" % sha256(live))
    print("重新打开客户端生效。")


if __name__ == "__main__":
    main()
