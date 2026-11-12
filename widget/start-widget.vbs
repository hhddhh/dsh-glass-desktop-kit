Set sh = CreateObject("WScript.Shell")
p = WScript.ScriptFullName
p = Left(p, InStrRev(p, ".") - 1) & ".ps1"
sh.Run "powershell -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File """ & p & """", 0, False
