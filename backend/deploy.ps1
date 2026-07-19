Start-Process -NoNewWindow -FilePath "python" -ArgumentList "-m uvicorn app.main:app --port 8001"
Write-Host "Starting public tunnel via localtunnel..."
npx localtunnel --port 8001
