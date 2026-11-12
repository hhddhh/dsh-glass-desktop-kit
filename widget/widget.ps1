# DSH 桌面小组件：无背景文字浮层，点击打开 DSH；可以拖动，位置自动记住
param([switch]$Preview)
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName PresentationFramework, PresentationCore, WindowsBase

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$cfgPath = Join-Path (Split-Path -Parent $MyInvocation.MyCommand.Path) 'config.json'
$cfg = $null
if (Test-Path -LiteralPath $cfgPath) { try { $cfg = Get-Content -LiteralPath $cfgPath -Raw | ConvertFrom-Json } catch {} }
$exe = if ($cfg -and $cfg.exe) { [string]$cfg.exe } else { 'C:\Program Files\DeepSeek Harness\DeepSeek Harness.exe' }
$title = if ($cfg -and $cfg.title) { [string]$cfg.title } else { '开始和 DeepSeek Harness 对话' }
$subtitle = if ($cfg -and $cfg.subtitle) { [string]$cfg.subtitle } else { '点一下进入对话' }
$iconPath = Join-Path $scriptDir 'dsh_icon_256.png'
$pidFile = Join-Path $scriptDir 'widget.pid'
$logFile = Join-Path $scriptDir 'widget.log'
$posFile = Join-Path $scriptDir 'widget_pos.json'
$runtimeDir = if ($cfg -and $cfg.runtimeDir) { [string]$cfg.runtimeDir } else { Join-Path $env:APPDATA '@deepseek-ai\dsh-desktop\dsh-glass' }
$wakeFile = Join-Path $runtimeDir 'wake.txt'

if (-not $Preview) {
    # 命名互斥量：比 pid 文件可靠，保证全局只有一个组件实例
    $script:mutex = New-Object System.Threading.Mutex($false, 'Global\DshDesktopWidget')
    $gotIt = $false
    try { $gotIt = $script:mutex.WaitOne(0) } catch { $gotIt = $false }
    if (-not $gotIt) { return }
}

Add-Type -TypeDefinition @"
using System;
using System.Text;
using System.Runtime.InteropServices;
public class W {
    [DllImport("user32.dll")] public static extern IntPtr SetWindowPos(IntPtr h, IntPtr after, int x, int y, int cx, int cy, uint flags);
    [DllImport("user32.dll")] public static extern int GetWindowLong(IntPtr h, int index);
    [DllImport("user32.dll")] public static extern int SetWindowLong(IntPtr h, int index, int value);
    [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr h, int cmd);
    [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
    [DllImport("user32.dll")] public static extern bool IsIconic(IntPtr h);
    [DllImport("user32.dll")] public static extern bool BringWindowToTop(IntPtr h);
    public delegate bool EnumProc(IntPtr h, IntPtr l);
    [DllImport("user32.dll")] public static extern bool EnumWindows(EnumProc cb, IntPtr l);
    [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr h, out uint pid);
    [DllImport("user32.dll")] public static extern bool IsWindowVisible(IntPtr h);
    [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr h, out RECT r);
    [StructLayout(LayoutKind.Sequential)] public struct RECT { public int Left, Top, Right, Bottom; }
    [DllImport("user32.dll")] public static extern bool GetCursorPos(out POINT p);
    [StructLayout(LayoutKind.Sequential)] public struct POINT { public int X, Y; }
    public static IntPtr FindDshWindow() {
        IntPtr found = IntPtr.Zero;
        foreach (var p in System.Diagnostics.Process.GetProcessesByName("DeepSeek Harness")) {
            uint want = (uint)p.Id;
            EnumWindows((h, l) => {
                uint pid; GetWindowThreadProcessId(h, out pid);
                if (pid != want) return true;
                RECT r; GetWindowRect(h, out r);
                if ((r.Right - r.Left) > 500 && (r.Bottom - r.Top) > 300) { found = h; return false; }
                return true;
            }, IntPtr.Zero);
            if (found != IntPtr.Zero) break;
        }
        return found;
    }
    public static bool Activate(IntPtr h) {
        if (h == IntPtr.Zero) return false;
        if (IsIconic(h)) ShowWindow(h, 9);   // SW_RESTORE
        ShowWindow(h, 5);                     // SW_SHOW
        BringWindowToTop(h);
        SetForegroundWindow(h);
        return true;
    }
}
"@ -Language CSharp

$xaml = @"
<Window xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
        xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
        WindowStyle="None" AllowsTransparency="True" Background="Transparent"
        ShowInTaskbar="False" ResizeMode="NoResize" Topmost="False"
        Width="322" Height="64" WindowStartupLocation="Manual">
  <Grid x:Name="Root" Background="Transparent" Cursor="Hand">
    <Grid.ColumnDefinitions>
      <ColumnDefinition Width="Auto"/>
      <ColumnDefinition Width="*"/>
    </Grid.ColumnDefinitions>
    <Viewbox Grid.Column="0" Width="40" Height="40" VerticalAlignment="Center">
      <Canvas Width="50" Height="50">
        <Path Data="M48.8354 10.0479C48.3232 9.79199 48.1025 10.2798 47.8032 10.5278C47.7007 10.6079 47.6143 10.7119 47.5273 10.8076C46.7793 11.624 45.9048 12.1597 44.7622 12.0957C43.0923 12 41.666 12.5356 40.4058 13.8398C40.1377 12.2319 39.2476 11.272 37.8926 10.6558C37.1836 10.3359 36.4668 10.0156 35.9702 9.31982C35.6235 8.82373 35.5293 8.27197 35.356 7.72754C35.2456 7.3999 35.1353 7.06396 34.7651 7.00781C34.3633 6.94385 34.2056 7.2876 34.0479 7.57568C33.418 8.75195 33.1733 10.0479 33.1973 11.3599C33.2524 14.312 34.4736 16.6641 36.8999 18.3359C37.1758 18.5278 37.2466 18.7197 37.1597 19C36.9946 19.5757 36.7974 20.1357 36.624 20.7119C36.5137 21.0801 36.3486 21.1597 35.9624 21C34.6309 20.4321 33.481 19.5918 32.4644 18.5757C30.7393 16.8721 29.1792 14.9917 27.2334 13.52C26.7764 13.1758 26.3193 12.856 25.8467 12.5518C23.8618 10.584 26.1069 8.96777 26.627 8.77588C27.1704 8.57568 26.8159 7.8877 25.0591 7.896C23.3022 7.90381 21.6953 8.50391 19.647 9.30371C19.3477 9.42383 19.0322 9.51172 18.7095 9.58398C16.8501 9.22363 14.9199 9.14355 12.9033 9.37598C9.10596 9.80762 6.07275 11.6396 3.84326 14.7681C1.16455 18.5278 0.53418 22.7998 1.30664 27.2559C2.11768 31.9521 4.46582 35.8398 8.07373 38.8799C11.8159 42.0322 16.1255 43.5762 21.041 43.2803C24.0269 43.104 27.3516 42.6963 31.1016 39.4561C32.0469 39.936 33.0396 40.1279 34.686 40.272C35.9546 40.3921 37.1758 40.208 38.1211 40.0078C39.6021 39.688 39.4995 38.2881 38.9639 38.0322C34.623 35.9678 35.5762 36.8081 34.71 36.1279C36.9155 33.4639 40.2402 30.6958 41.54 21.728C41.6426 21.0161 41.5557 20.5679 41.54 19.9917C41.5322 19.6396 41.6108 19.5039 42.0049 19.4639C43.0923 19.3359 44.1479 19.0317 45.1167 18.4878C47.9292 16.9199 49.064 14.3438 49.3315 11.2559C49.3711 10.7837 49.3237 10.2959 48.8354 10.0479ZM24.3262 37.8398C20.1196 34.4639 18.0791 33.3521 17.2358 33.3999C16.4482 33.4482 16.5898 34.3682 16.7632 34.9678C16.9443 35.5601 17.1812 35.9683 17.5117 36.4878C17.7402 36.832 17.8979 37.3442 17.2832 37.728C15.9282 38.584 13.5728 37.4399 13.4624 37.3838C10.7207 35.7358 8.42822 33.5601 6.81348 30.584C5.25342 27.7197 4.34766 24.6479 4.19775 21.3677C4.1582 20.5757 4.38672 20.2959 5.15869 20.1519C6.17529 19.96 7.22314 19.9199 8.23926 20.0718C12.5327 20.7119 16.1885 22.6719 19.2529 25.7759C21.002 27.5439 22.3252 29.6558 23.6885 31.7202C25.1377 33.9121 26.6978 36 28.6831 37.7119C29.3843 38.312 29.9434 38.7681 30.479 39.104C28.8643 39.2881 26.1699 39.3281 24.3262 37.8398ZM26.3433 24.6001C26.3433 24.248 26.6191 23.9678 26.9658 23.9678C27.0444 23.9678 27.1152 23.9839 27.1782 24.0078C27.2651 24.04 27.3438 24.0879 27.4067 24.1602C27.5171 24.272 27.5801 24.4321 27.5801 24.6001C27.5801 24.9521 27.3042 25.2319 26.9575 25.2319C26.6108 25.2319 26.3433 24.9521 26.3433 24.6001ZM32.6064 27.8799C32.2046 28.0479 31.8027 28.1919 31.4165 28.208C30.8179 28.2397 30.1641 27.9922 29.8096 27.688C29.2583 27.2158 28.8643 26.9521 28.6987 26.1279C28.6279 25.7759 28.6675 25.2319 28.7305 24.9199C28.8721 24.248 28.7144 23.8159 28.2495 23.4238C27.8716 23.104 27.3911 23.0161 26.8633 23.0161C26.666 23.0161 26.4849 22.9277 26.3511 22.856C26.1304 22.7441 25.9492 22.4639 26.1226 22.1201C26.1777 22.0078 26.4458 21.7358 26.5088 21.688C27.2256 21.272 28.0527 21.4077 28.8169 21.7197C29.5259 22.0161 30.0615 22.5601 30.834 23.3281C31.6216 24.2559 31.7632 24.5117 32.2124 25.208C32.5669 25.752 32.8901 26.312 33.1104 26.9521C33.2446 27.3521 33.0713 27.6802 32.6064 27.8799Z" Fill="#FFFFFF">
          <Path.Effect>
            <DropShadowEffect Color="#000000" BlurRadius="7" ShadowDepth="1" Opacity="0.6"/>
          </Path.Effect>
        </Path>
      </Canvas>
    </Viewbox>
    <StackPanel Grid.Column="1" VerticalAlignment="Center" Margin="11,0,14,0">
      <TextBlock x:Name="Title" FontFamily="Microsoft YaHei UI, Segoe UI" FontSize="15.5" FontWeight="SemiBold"
                 Foreground="#FFFFFF" Text="__TITLE__">
        <TextBlock.Effect>
          <DropShadowEffect Color="#000000" BlurRadius="10" ShadowDepth="2" Opacity="0.6"/>
        </TextBlock.Effect>
      </TextBlock>
      <TextBlock x:Name="Sub" FontFamily="Microsoft YaHei UI, Segoe UI" FontSize="10.5"
                 Foreground="#F0FFFFFF" Margin="0,5,0,0" Text="__SUBTITLE__">
        <TextBlock.Effect>
          <DropShadowEffect Color="#000000" BlurRadius="9" ShadowDepth="1" Opacity="0.6"/>
        </TextBlock.Effect>
      </TextBlock>
    </StackPanel>
  </Grid>
</Window>
"@

$xaml = $xaml.Replace('__TITLE__', $title).Replace('__SUBTITLE__', $subtitle)
$reader = New-Object System.Xml.XmlNodeReader ([xml]$xaml)
$window = [Windows.Markup.XamlReader]::Load($reader)
$root = $window.FindName('Root')

# 位置：优先用上次拖到的位置，否则桌面中上部
$work = [System.Windows.SystemParameters]::WorkArea
$window.Left = $work.Left + ($work.Width - $window.Width) / 2
$window.Top = $work.Top + [Math]::Round($work.Height * 0.20)
$savedPos = $null
if (Test-Path -LiteralPath $posFile) {
    try {
        $pos = Get-Content -LiteralPath $posFile -Raw | ConvertFrom-Json
        if ($null -ne $pos.x -and $null -ne $pos.y) { $savedPos = @{ x = [int]$pos.x; y = [int]$pos.y } }
    } catch {}
}

$root.Opacity = 0.92
$root.Add_MouseEnter({ try { $root.Opacity = 1.0 } catch {} })

# 拖动：按下记录起点，移动超过阈值就挪窗口，松开保存
$drag = @{ on = $false; cx = 0; cy = 0; rx = 0; ry = 0; moved = $false }
$root.Add_MouseLeftButtonDown({
    try {
        $pt = New-Object W+POINT
        [void][W]::GetCursorPos([ref]$pt)
        $r = New-Object W+RECT
        [void][W]::GetWindowRect((New-Object System.Windows.Interop.WindowInteropHelper $window).Handle, [ref]$r)
        $drag.on = $true; $drag.moved = $false
        $drag.cx = $pt.X; $drag.cy = $pt.Y
        $drag.rx = $r.Left; $drag.ry = $r.Top
        [void]$root.CaptureMouse()
    } catch {}
})
$root.Add_MouseMove({
    try {
        if (-not $drag.on) { return }
        $pt = New-Object W+POINT
        [void][W]::GetCursorPos([ref]$pt)
        $dx = $pt.X - $drag.cx; $dy = $pt.Y - $drag.cy
        if ([Math]::Abs($dx) -gt 3 -or [Math]::Abs($dy) -gt 3) { $drag.moved = $true }
        if ($drag.moved) {
            $wh = (New-Object System.Windows.Interop.WindowInteropHelper $window).Handle
            [void][W]::SetWindowPos($wh, [IntPtr]::Zero, $drag.rx + $dx, $drag.ry + $dy, 0, 0, 0x0015)  # NOSIZE|NOZORDER|NOACTIVATE
        }
    } catch {}
})
$root.Add_MouseLeftButtonUp({
    try {
        if ($drag.on) {
            $drag.on = $false
            [void]$root.ReleaseMouseCapture()
            if ($drag.moved) {
                $r = New-Object W+RECT
                [void][W]::GetWindowRect((New-Object System.Windows.Interop.WindowInteropHelper $window).Handle, [ref]$r)
                $obj = @{ x = $r.Left; y = $r.Top }
                try { ($obj | ConvertTo-Json -Compress) | Set-Content -LiteralPath $posFile -Encoding UTF8 } catch {}
            } else {
                if (([System.Windows.Input.Keyboard]::Modifiers -band [System.Windows.Input.ModifierKeys]::Shift) -ne 0) {
                    $window.Close()
                    return
                }
                # 没拖动 = 点击：让客户端自己恢复窗口（touch wake.txt，不抢 Win32 强拉）
                $h = [W]::FindDshWindow()
                $procs = @(Get-Process 'DeepSeek Harness' -ErrorAction SilentlyContinue).Count
                try { Add-Content -LiteralPath $logFile -Value ((Get-Date).ToString('s') + ' click: hwnd=0x' + $h.ToString('X') + ' procs=' + $procs) } catch {}
                if ($procs -gt 0) {
                    # 客户端自己恢复（restore+show+focus），不启动第二个实例
                    try {
                        if (-not (Test-Path -LiteralPath $wakeFile)) { Set-Content -LiteralPath $wakeFile -Value 'wake' -Encoding ASCII }
                        (Get-Item -LiteralPath $wakeFile).LastWriteTime = Get-Date
                        try { Add-Content -LiteralPath $logFile -Value ((Get-Date).ToString('s') + ' touched wake') } catch {}
                    } catch {}
                } else {
                    try {
                        Start-Process -FilePath $exe -WorkingDirectory (Split-Path -Parent $exe) -ErrorAction Stop
                        try { Add-Content -LiteralPath $logFile -Value ((Get-Date).ToString('s') + ' launched exe') } catch {}
                    } catch {
                        try { Add-Content -LiteralPath $logFile -Value ((Get-Date).ToString('s') + ' launch failed: ' + $_.Exception.Message) } catch {}
                    }
                }
                if (-not $Preview) {
                    $wh = (New-Object System.Windows.Interop.WindowInteropHelper $window).Handle
                    [void][W]::SetWindowPos($wh, [IntPtr]::new(1), 0, 0, 0, 0, 0x0013)
                }
            }
        }
    } catch {}
})
$root.Add_MouseLeave({
    try {
        if (-not $drag.on) { $root.Opacity = 0.92 }
    } catch {}
})

$window.Add_SourceInitialized({
    $h = (New-Object System.Windows.Interop.WindowInteropHelper $window).Handle
    $ex = [W]::GetWindowLong($h, -20)
    $ex = ($ex -bor 0x08000000) -bor 0x00000080   # NOACTIVATE | TOOLWINDOW
    [void][W]::SetWindowLong($h, -20, $ex)
})
$window.Add_Closed({
    if (-not $Preview) {
        if (Test-Path -LiteralPath $pidFile) { Remove-Item -LiteralPath $pidFile -Force -ErrorAction SilentlyContinue }
    }
    [System.Windows.Application]::Current.Shutdown()
})

$app = New-Object System.Windows.Application
$app.ShutdownMode = 'OnMainWindowClose'
$window.Show()
$window.Activate() | Out-Null
$h = (New-Object System.Windows.Interop.WindowInteropHelper $window).Handle
if ($null -ne $savedPos) {
    [void][W]::SetWindowPos($h, [IntPtr]::Zero, $savedPos.x, $savedPos.y, 0, 0, 0x0015)  # NOSIZE|NOZORDER|NOACTIVATE
}
if ($Preview) {
    $window.Topmost = $true
    $window.Activate() | Out-Null
} else {
    [void][W]::SetWindowPos($h, [IntPtr]::new(1), 0, 0, 0, 0, 0x0013)
    Set-Content -LiteralPath $pidFile -Value $PID -Encoding ASCII
}
[void]$app.Run()
