r"""重建客户端目录里的用户脚本和说明（客户端更新会把这些文件清掉）。

用法：python helpers.py --app-dir "D:\其他\DeepSeekHarness"
"""

import argparse
import os
import sys

try:
    sys.stdout.reconfigure(encoding="cp936", errors="replace")
except Exception:
    pass

WORK = os.path.dirname(os.path.abspath(__file__))

RESTORE_TMPL = r'''@echo off
setlocal
title {title}

set "APP_DIR=%~dp0"
set "PY=%APP_DIR%resources\runtime\primary-runtime\dependencies\python\python.exe"
set "SCRIPT=%WORK%\restore.py"

echo ==========================================
echo   {banner}
echo ==========================================
echo.

tasklist /fi "imagename eq DeepSeek Harness.exe" 2>nul | find /i "DeepSeek Harness.exe" >nul
if not errorlevel 1 (
  echo [!] 客户端还在运行。请先在托盘图标上右键 - 退出，再运行本脚本。
  echo.
  pause
  exit /b 1
)

if not exist "%SCRIPT%" (
  echo [!] 找不到脚本：%SCRIPT%
  echo     请直接找 AI 助手处理。
  echo.
  pause
  exit /b 1
)

"%PY%" "%SCRIPT%" --app-dir "%APP_DIR%" --mode {mode}
set "CODE=%ERRORLEVEL%"
echo.
if "%CODE%"=="0" (
  echo [OK] 已完成，现在可以打开客户端了。
) else (
  echo [!] 没有切换（退出码 %CODE%），按上面提示处理。
)
echo.
pause
'''

REAPPLY = r'''@echo off
setlocal
title 更新后重新应用半透明外观

set "APP_DIR=%~dp0"
set "PY=%APP_DIR%resources\runtime\primary-runtime\dependencies\python\python.exe"
set "SCRIPT=%WORK%\repatch.py"

echo ==========================================
echo   DeepSeek Harness - 重新应用半透明外观
echo ==========================================
echo.

tasklist /fi "imagename eq DeepSeek Harness.exe" 2>nul | find /i "DeepSeek Harness.exe" >nul
if not errorlevel 1 (
  echo [!] 客户端还在运行。请先在托盘图标上右键 - 退出，再运行本脚本。
  echo.
  pause
  exit /b 1
)

if not exist "%PY%" (
  echo [!] 找不到客户端自带的 Python：%PY%
  echo     新版可能改了目录结构，请直接找 AI 助手处理。
  echo.
  pause
  exit /b 1
)

if not exist "%SCRIPT%" (
  echo [!] 找不到脚本：%SCRIPT%
  echo     请直接找 AI 助手处理。
  echo.
  pause
  exit /b 1
)

"%PY%" "%SCRIPT%" --app-dir "%APP_DIR%"
set "CODE=%ERRORLEVEL%"
echo.
if "%CODE%"=="0" (
  echo [OK] 已经重新打好了，现在可以打开客户端。
  echo      客户端目录里的切换脚本/说明会在下次整理时重建。
) else (
  echo [!] 没有改动客户端（退出码 %CODE%）。
  echo     如果提示“已经是改过的版本”，说明现在就是半透明状态；
  echo     如果提示结构变了，请把上面的文字发给 AI 助手。
)
echo.
pause
'''

DESKTOP = r'''@echo off
setlocal
title 恢复 DeepSeek Harness 原生外观

set "APP_DIR=D:\其他\DeepSeekHarness"
set "PY=%APP_DIR%\resources\runtime\primary-runtime\dependencies\python\python.exe"
set "SCRIPT=%WORK%\restore.py"

echo ==================================================
echo   把 DeepSeek Harness 恢复成原来的外观
echo ==================================================
echo.

tasklist /fi "imagename eq DeepSeek Harness.exe" 2>nul | find /i "DeepSeek Harness.exe" >nul
if not errorlevel 1 (
  echo [!] 客户端还在运行。请先在系统托盘图标上右键 - 退出，再运行一次本脚本。
  echo.
  pause
  exit /b 1
)

if exist "%PY%" if exist "%SCRIPT%" (
  "%PY%" "%SCRIPT%" --app-dir "%APP_DIR%" --mode orig --force
  set "CODE=%ERRORLEVEL%"
  echo.
  if "%CODE%"=="0" ( echo [OK] 已恢复原生外观。 ) else ( echo [!] 恢复失败，退出码 %CODE% )
  echo.
  pause
  exit /b %CODE%
)

if not exist "%APP_DIR%\resources\app.asar.glass-orig" (
  echo [!] 找不到备份 app.asar.glass-orig。
  echo.
  pause
  exit /b 1
)
copy /y "%APP_DIR%\resources\app.asar.glass-orig" "%APP_DIR%\resources\app.asar" >nul
if errorlevel 1 (
  echo [!] 复制失败，请确认客户端已完全退出。
) else (
  echo [OK] 已恢复原生外观，可以打开客户端了。
)
echo.
pause
'''

NOTE = r'''DeepSeek Harness 半透明外观 —— 说明
=====================================

现在是什么效果
--------------
客户端界面底色半透明，能看到背后的桌面；文字和图标保持清晰，不算进透明里。
透明程度可以在客户端里直接调，调好会记住，重启也保持。
由客户端弹出来的面板（设置、菜单、移动访问等）保持纯白不透明，避免文字叠在一起。

日常怎么用
----------
1. 窗口右下角有个水滴小按钮，点开是外观面板（Ctrl+Alt+G 也能开关）：
   - 「不透明度」滑块：最左=完全透明（看得到桌面）；往右白纱变厚；
     最右=客户端本来样子（原生配色、方角、不加任何效果）。设置会自动记住。
   - 背景是真实的桌面（动态壁纸、背后的窗口都实时显示）。
   - 说明：真正的"毛玻璃模糊"在 Windows 上对这类客户端窗口不生效（系统接口在本机
     要么被忽略、要么只给一层纯色），所以没有做模糊，只做真透明。
2. 不透明度越低，文字会自动变深，保证看得清。

客户端更新（装新版本）之后
--------------------------
装新版本会把这次改动覆盖掉：半透明会消失，客户端一切正常，不会坏。
想恢复半透明：
  1. 完全退出客户端（右下角托盘图标 → 右键 → 退出）。
  2. 双击本目录里的「更新后重新应用半透明.cmd」。
  3. 重新打开客户端就恢复了。
如果脚本报“结构变了/找不到锚点”，说明新版本代码改了，把窗口里的文字
发给 AI 助手，让它适配一下（一般十几分钟）。

不想要了
--------
完全退出客户端 → 双击「恢复原生外观.cmd」→ 再打开。桌面上的
「DSH打不开就双击这个-恢复原生外观.cmd」是同一件事的应急入口。

文件说明（都在客户端目录下）
----------------------------
resources\app.asar               当前生效的客户端文件（改过的）
resources\app.asar.glass         半透明版本的副本
resources\app.asar.glass-orig    原始版本的备份
更新后重新应用半透明.cmd          版本更新后用它重新打回去
恢复原生外观.cmd                  回到最初的样子
切换到半透明外观.cmd              半透明版和原版之间切换

注意
----
- 透明窗口没有系统阴影，四角弧度是样式画出来的（超椭圆，类似小米 logo）。
- 客户端里的网页面板（比如内嵌网页）是另一个页面，不受这个外观控制。
'''


def write(path, text):
    with open(path, "wb") as f:
        f.write(text.encode("cp936"))
    print("written", path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--app-dir", default=r"D:\其他\DeepSeekHarness")
    args = ap.parse_args()
    app = args.app_dir
    write(os.path.join(app, "更新后重新应用半透明.cmd"), REAPPLY.replace("%WORK%", WORK))
    write(os.path.join(app, "恢复原生外观.cmd"),
          RESTORE_TMPL.format(title="恢复原生外观", banner="DeepSeek Harness - 恢复原生外观", mode="orig").replace("%WORK%", WORK))
    write(os.path.join(app, "切换到半透明外观.cmd"),
          RESTORE_TMPL.format(title="切换到半透明外观", banner="DeepSeek Harness - 切换到半透明外观", mode="glass").replace("%WORK%", WORK))
    write(os.path.join(app, "窗口半透明-说明.txt"), NOTE)
    desktop = os.path.join(os.path.expanduser("~"), "Desktop", "DSH打不开就双击这个-恢复原生外观.cmd")
    if os.path.isdir(os.path.dirname(desktop)):
        write(desktop, DESKTOP.replace("%WORK%", WORK))
    print("done")


if __name__ == "__main__":
    main()
