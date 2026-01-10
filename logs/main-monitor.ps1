$Host.UI.RawUI.WindowTitle = 'Main Monitor - All Services'
Set-Location 'D:\tryagain'
& powershell.exe -ExecutionPolicy Bypass -File 'D:\tryagain\scripts\monitor-services.ps1' -ProjectRoot 'D:\tryagain'
