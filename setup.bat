@echo off
cd /d "%~dp0"
where py >nul 2>&1 || goto fail
py -m pip install -r requirements.txt || goto fail
powershell -NoProfile -Command "$w=New-Object -ComObject WScript.Shell; $s=$w.CreateShortcut((Join-Path ([Environment]::GetFolderPath('DesktopDirectory')) 'Vanijen AI.lnk')); $s.TargetPath=(Get-Command pyw.exe -ErrorAction Stop).Source; $s.Arguments='jarvis.py'; $s.WorkingDirectory=(Get-Location).Path; $ico=Join-Path $s.WorkingDirectory 'assets\vanijen-icon.ico'; if (Test-Path -LiteralPath $ico) { $s.IconLocation=$ico+',0' }; $s.Save()" || goto fail
echo Desktop shortcut created. Keep this folder in place.
pause
exit /b 0
:fail
echo Setup failed. Install Windows Python with its launcher, then retry.
pause
exit /b 1
