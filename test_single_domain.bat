@echo off
curl -X POST "http://localhost:8000/domain-parser/extract-batch" -H "Content-Type: application/json" -d "{\"runId\":\"a0097613-61ab-4831-8d48-ef9c8cbfac8b\",\"domains\":[\"kranikoff.ru\"]}"
pause
