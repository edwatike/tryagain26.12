@echo off
echo === ФИНАЛЬНЫЙ ТЕСТ ===
echo.
echo 1. Создание parsing run...
curl -X POST http://127.0.0.1:8000/parsing/start -H "Content-Type: application/json" -d "{\"keyword\":\"фланец\",\"depth\":1,\"source\":\"google\"}" > temp\test-response.json
python -c "import json; d=json.load(open('temp/test-response.json')); print('   Создан:', d['runId']); open('temp/test-runid.txt', 'w').write(d['runId'])"
set /p RUN_ID=<temp\test-runid.txt
echo.
echo 2. Ожидание завершения (60 сек)...
timeout /t 60 /nobreak >nul
echo.
echo 3. Проверка доменов...
curl "http://127.0.0.1:8000/domains/queue?parsingRunId=%RUN_ID%&limit=100" > temp\test-domains.json
python -c "import json; d=json.load(open('temp/test-domains.json')); print('   Доменов:', len(d.get('entries', []))); print('   Total:', d.get('total', 0)); [print(f'   {i+1}. {e.get(\"domain\")}') for i, e in enumerate(d.get('entries', [])[:5])]"
echo.
echo Откройте: http://localhost:3000/parsing-runs/%RUN_ID%















