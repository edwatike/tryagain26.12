import requests
import time
import os

# Получаем parsing run
r = requests.get('http://127.0.0.1:8000/parsing/runs?limit=1&sort=created_at&order=desc')
run = r.json()['runs'][0]
run_id = run['runId']

print(f'Testing with run: {run_id}')
print(f'Keyword: {run["keyword"]}')

# Получаем домены
d = requests.get(f'http://127.0.0.1:8000/domains/queue?parsingRunId={run_id}&limit=10')
domains = [e['domain'] for e in d.json()['entries'][:2]]

print(f'Selected domains: {domains}')

# Запускаем Domain Parser
print('\n=== Starting Domain Parser ===')
p = requests.post('http://127.0.0.1:8000/domain-parser/extract-batch', json={'runId': run_id, 'domains': domains})
parser_run_id = p.json()['parserRunId']
print(f'Parser started: {parser_run_id}')

# Ждем завершения Domain Parser
print('\nWaiting for Domain Parser to complete...')
for i in range(30):
    time.sleep(2)
    s = requests.get(f'http://127.0.0.1:8000/domain-parser/status/{parser_run_id}')
    status = s.json()
    if status['status'] == 'completed':
        print(f'\n✅ Domain Parser completed!')
        print(f'Results: {len(status["results"])} domains')
        for r in status['results']:
            inn = r.get('inn', 'Not found')
            emails = r.get('emails', [])
            email = emails[0] if emails else 'Not found'
            print(f'  - {r["domain"]}: INN={inn}, Email={email}')
        break
    print(f'  Status: {status["status"]} - {status["processed"]}/{status["total"]}', end='\r')

# Проверяем логи на AUTO-TRIGGER
print('\n\n=== Checking for AUTO-TRIGGER in logs ===')
time.sleep(3)
log_file = max([f for f in os.listdir('logs') if f.startswith('Backend-')], key=lambda x: os.path.getmtime(os.path.join('logs', x)))
with open(f'logs/{log_file}', 'r', encoding='utf-8') as f:
    lines = f.readlines()
    auto_trigger_lines = [l for l in lines[-50:] if 'AUTO-TRIGGER' in l]
    if auto_trigger_lines:
        print('✅ Found AUTO-TRIGGER logs:')
        for line in auto_trigger_lines:
            print(f'  {line.strip()}')
    else:
        print('⚠️ No AUTO-TRIGGER logs found')

print(f'\n📋 Open Frontend to see results: http://localhost:3000/parsing-runs/{run_id}')
