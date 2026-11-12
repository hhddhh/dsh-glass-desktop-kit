# dsh-glass-desktop-kit

DeepSeek Harness 桌面版（Windows）的**圆润半透明外观 + 桌面小组件**套件。非官方，只做外观，不改 DSH 的功能。

## 效果

**外观**
- 窗口真透明：能看到桌面和动态壁纸（不是贴图，也不是 Windows 的奶白材质）
- 不透明度滑块 0–100：0 = 完全透明，100 = 撤掉所有注入样式，回到客户端原样
- 34px 圆角（超椭圆 squircle），四角更圆润
- 右上角最小化 / 最大化 / 关闭是**自绘圆角按钮**，悬停是圆角底色（关闭键红色），和窗口圆角统一；顶部中间可拖动窗口
- 半透明时文字自动加深，保证对比度；弹窗/菜单保持不透明，不和正文糊在一起

**桌面小组件（可选）**
- 桌面上部中间一行浮层：鲸鱼图标 + 「开始和大肥鱼对话」，无背景，直接浮在壁纸上
- 点一下：把 DSH 唤到前台；DSH 已关掉就启动它（不新建第二个实例）
- 按住拖动：挪位置，松手记住；Shift + 点击：退出组件
- 单实例、无控制台窗口、可由计划任务开机自启

## 环境

- Windows 11（在 24H2 / build 26100 上验证），175% 缩放
- DeepSeek Harness 桌面版 **0.2.2-rc.2**
- 不需要额外安装 Python / Node：脚本用客户端自带的运行时跑

> ⚠️ 只适配上述版本的归档结构。其他版本（尤其大版本更新）里 `lib/main.js` 的锚点会变，
> 脚本会**安全报错并拒绝写入**，不会把客户端改坏；需要按新版本代码调整 `client/repatch.py` 的锚点。

## 安装外观

1. **完全退出** DSH（托盘图标右键 → 退出；任务管理器确认没有 `DeepSeek Harness` 进程）
2. 用客户端自带 Python 跑补丁：

```bat
"D:\你的路径\DeepSeekHarness\resources\runtime\primary-runtime\dependencies\python\python.exe" ^
  client\repatch.py --app-dir "D:\你的路径\DeepSeekHarness"
```

3. 重新打开 DSH。
   补丁会：备份原版 `app.asar`、只改 `lib/main.js` 一个文件（长度不变）、把样式复制到
   `%APPDATA%\@deepseek-ai\dsh-desktop\dsh-glass`，并做语法/哈希校验。

想换样式文件位置：加 `--runtime-dir "D:\某处"`，同时给客户端设置同名环境变量 `DSH_GLASS_DIR`。

## 回滚

```bat
python client\restore.py --app-dir "D:\你的路径\DeepSeekHarness" --mode orig
```

（`restore.py` 会核对版本号，防止把旧备份盖到新版本上；加 `--force` 可强制。）

## 客户端升级之后

升级会把 `app.asar` 整个换掉，外观会消失（客户端本身正常）。重新跑一次 `client\repatch.py` 即可；
如果脚本提示"结构变了"，说明锚点需要适配，不要强行写入。

## 桌面小组件

1. 复制 `widget\config.example.json` 为 `widget\config.json`，改成你的路径：

```json
{
  "exe": "D:\\其他\\DeepSeekHarness\\DeepSeek Harness.exe",
  "runtimeDir": "C:\\Users\\<你>\\AppData\\Roaming\\@deepseek-ai\\dsh-desktop\\dsh-glass"
}
```

2. 双击 `widget\start-widget.vbs`（无窗口启动），或把 `start-widget.cmd` 放到启动文件夹/计划任务
3. 点组件唤回 DSH；Shift + 点击退出；`stop-widget.cmd` 也能关

组件依赖外观补丁里的 `wake.txt` 通道：它只是"写一个文件"，由客户端主进程自己恢复窗口，
**不会启动第二个实例**（第二个实例会闪黑框并让主窗口卡死）。

## 已知限制

- 不是 macOS 那种毛玻璃：Windows 上不存在能用于第三方窗口的实时模糊接口。
  - DWM 丙烯酸（Acrylic）：奶白、不透，观感差
  - `SetWindowCompositionAttribute`：在新版 Windows 上不生效或只输出纯色
  - 因此本套件只做**真透明 + 圆角 + 文字对比**，不做模糊
- 透明窗口在"最小化/隐藏→显示"时会闪一帧，套件里用"隐藏时不透明度归零 + 分步淡入"绕开
- 最大化后圆角由系统接管（Windows 行为）

## 目录

```
client/
  repatch.py       打补丁（锚点、注释压缩、长度不变、哈希校验、复制样式）
  restore.py       切回原版 / 半透明版（版本校验）
  helpers.py       生成客户端目录里的中文入口脚本（可选）
  asar_extract.py / asar_tool.py   归档读写小工具
  runtime/
    glass.css      外观样式（圆角、透明、文字对比、自绘按钮样式）
    glass.js       外观面板（不透明度滑块）+ 自绘窗口按钮
widget/
  widget.ps1       桌面组件本体（PowerShell + WPF）
  config.example.json
  start-widget.vbs / start-widget.cmd / stop-widget.cmd
```

## 免责声明

- 非官方项目，与 DeepSeek 无隶属或背书关系。
- 只修改 `app.asar` 里的 `lib/main.js` 一个文件（就地补丁、长度不变）；其余文件逐字节保持官方原样。
- 安装前会自动备份；回滚脚本可用。**仍建议先自行备份整个 `DeepSeekHarness` 目录。**
- 使用风险自负。

## License

MIT，见 `LICENSE`。
