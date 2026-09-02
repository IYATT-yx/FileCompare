$startTime = Get-Date

python -m venv venv
.\venv\Scripts\Activate.ps1
python.exe -m pip install --upgrade pip
pip install nuitka==4.2
pip install -r requirements.txt

python .\savebuildtime.py

$env:CL = "/utf-8"

nuitka --standalone `
--onefile `
--windows-console-mode=disable `
--lto=yes `
--no-deployment-flag=self-contained `
--enable-plugin=tk-inter `
--include-package-data=tkinterdnd2 `
--windows-company-name="IYATT-yx" `
--windows-product-name="文件一致性比对工具" `
--windows-file-description="文件一致性比对工具" `
--windows-product-version="1.0.0.0" `
--windows-file-version="1.0.0.0" `
--copyright="Copyright (C) 2026 IYATT-yx. All Rights Reserved." `
--windows-icon-from-ico=.\icon.ico `
--include-data-file=.\icon.ico=.\ `
--output-dir=dist `
--output-filename=FileCompare_win_amd64 `
.\FileCompare.py

$endTime = Get-Date
$elapsedTime = New-TimeSpan -Start $startTime -End $endTime
Write-Output "程序构建用时：$($elapsedTime.TotalSeconds) 秒"