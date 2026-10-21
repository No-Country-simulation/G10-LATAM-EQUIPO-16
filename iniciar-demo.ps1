Set-Location -LiteralPath $PSScriptRoot
$env:COMMUNITYLAB_DEMO = '1'
& "$PSScriptRoot/.venv/Scripts/python.exe" -m streamlit run frontend/app.py --server.address 127.0.0.1 --server.port 8502 --server.headless true --browser.gatherUsageStats false
