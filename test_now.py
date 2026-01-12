import requests
import time
import subprocess

# Запускаем Domain Parser с реальными доменами
print('=== Starting Domain Parser ===')
response = requests.post(
    'http://127.0.0.1:8000/domain-parser/extract-batch',
    json={'runId': '35e40edd-7182-4d45-a39f-55333c0d152b', 'domains': ['owen.ru', 'elektro.ru']}
)

if response.status_code == 200:
    parser_run_id = response.json()['parserRunId']
    print(f'Parser started: {parser_run_id}')
    print('Waiting for completion...\n')
    
    # Ждем завершения
    for i in range(30):
        time.sleep(2)
        status_resp = requests.get(f'http://127.0.0.1:8000/domain-parser/status/{parser_run_id}')
        status = status_resp.json()
        stat = status['status']
        proc = status['processed']
        total = status['total']
        print(f'  {stat} - {proc}/{total}', end='\r')
        
        if stat == 'completed':
            print(f'\n\nDomain Parser COMPLETED!')
            print(f'Results: {len(status["results"])} domains')
            for r in status['results']:
                inn = r.get('inn', 'Not found')
                emails = r.get('emails', [])
                email = emails[0] if emails else 'Not found'
                print(f'  - {r["domain"]}: INN={inn}, Email={email}')
            break
    
    # Ждем немного для автотриггера
    print('\n\nWaiting for AUTO-TRIGGER...')
    time.sleep(5)
    
    # Проверяем логи
    print('\n=== Checking Backend logs for AUTO-TRIGGER ===')
    result = subprocess.run(
        ['powershell', '-Command', 'Get-Content logs\\Backend-*.log -Tail 50 | Select-String -Pattern AUTO-TRIGGER'],
        capture_output=True,
        text=True,
        cwd='D:\\tryagain'
    )
    
    if result.stdout.strip():
        print('AUTO-TRIGGER FOUND:')
        for line in result.stdout.strip().split('\n'):
            print(f'  {line}')
    else:
        print('No AUTO-TRIGGER logs yet')
        
else:
    print(f'Error: {response.status_code}')
    print(response.text)
