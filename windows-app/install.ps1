# Publishes the app to a fixed per-user folder and adds a Start menu shortcut, so Windows Search finds it
# and rebuilding the project no longer touches the running copy. Run again after a code change to update.
$ErrorActionPreference = 'Stop'
$dir = Join-Path $env:LOCALAPPDATA 'Programs\G435MediaGesture'
$exe = Join-Path $dir 'G435MediaGesture.exe'

Get-Process G435MediaGesture -ErrorAction SilentlyContinue | Stop-Process -Force
dotnet publish $PSScriptRoot -c Release -o $dir
if ($LASTEXITCODE -ne 0) { throw 'dotnet publish failed' }

$shell = New-Object -ComObject WScript.Shell
$link = $shell.CreateShortcut((Join-Path ([Environment]::GetFolderPath('Programs')) 'G435 미디어 제스처.lnk'))
$link.TargetPath = $exe
$link.WorkingDirectory = $dir
$link.Save()

# "Windows 시작 시 실행" stores the exe path; point an existing entry at the installed copy.
$run = 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Run'
if (Get-ItemProperty $run -Name G435MediaGesture -ErrorAction SilentlyContinue) {
    Set-ItemProperty $run -Name G435MediaGesture -Value "`"$exe`" --background"
}

Start-Process $exe
Write-Host "설치됨: $exe"
