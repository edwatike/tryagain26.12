import requests
import time

print("🚀 Запускаю Domain Parser для elektro.ru...")
response = requests.post(
    'http://127.0.0.1:8000/domain-parser/extract-batch',
    json={'runId': '35e40edd-7182-4d45-a39f-55333c0d152b', 'domains': ['elektro.ru']}
)
print(f"Status: {response.status_code}")
data = response.json()
print(f"Parser Run ID: {data.get('parserRunId')}")

parser_run_id = data.get('parserRunId')

# Ждем завершения Domain Parser
print("\n⏳ Жду завершения Domain Parser (60 секунд)...")
time.sleep(60)

# Проверяем статус
status_response = requests.get(f'http://127.0.0.1:8000/domain-parser/status/{parser_run_id}')
status_data = status_response.json()
print(f"\n📊 Domain Parser статус: {status_data.get('status')}")
print(f"   Обработано: {status_data.get('processed')}/{status_data.get('total')}")

# Ждем Comet (если запустился)
print("\n⏳ Жду Comet (120 секунд)...")
time.sleep(120)

print("\n✅ Готово! Проверяй логи Backend для деталей.")
