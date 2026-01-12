import requests
import time

print("🚀 ФИНАЛЬНЫЙ ТЕСТ: Domain Parser → Comet → Learning")
print("="*60)

# Запускаем Domain Parser
print("\n1️⃣ Запускаю Domain Parser для elektro.ru...")
response = requests.post(
    'http://127.0.0.1:8000/domain-parser/extract-batch',
    json={'runId': '35e40edd-7182-4d45-a39f-55333c0d152b', 'domains': ['elektro.ru']}
)
print(f"   Status: {response.status_code}")
parser_run_id = response.json().get('parserRunId')
print(f"   Parser Run ID: {parser_run_id}")

# Ждем завершения Domain Parser
print("\n2️⃣ Жду завершения Domain Parser (60 секунд)...")
time.sleep(60)

# Проверяем статус Domain Parser
status_response = requests.get(f'http://127.0.0.1:8000/domain-parser/status/{parser_run_id}')
status_data = status_response.json()
print(f"   Domain Parser статус: {status_data.get('status')}")
print(f"   Обработано: {status_data.get('processed')}/{status_data.get('total')}")

# Ждем Comet (если запустился автоматически)
print("\n3️⃣ Жду автозапуск Comet и его завершение (180 секунд)...")
time.sleep(180)

print("\n✅ ТЕСТ ЗАВЕРШЕН!")
print("\n📋 Проверь логи Backend для деталей:")
print("   - Ищи 'Waiting for sidecar UI' - должно появиться")
print("   - Ищи 'Interactive elements detected' - должно появиться")
print("   - Ищи 'Assistant panel not opened' - НЕ должно появиться")
print("   - Ищи 'AUTO-LEARNING' - должно появиться если Comet нашел данные")
