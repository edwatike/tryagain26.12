import requests
import time

print('=== Проверяю статус Comet ===\n')

# Ждем завершения Comet
comet_id = 'comet_20260112_144004_4887b0ae'

for i in range(30):
    time.sleep(2)
    try:
        r = requests.get(f'http://127.0.0.1:8000/comet/status/{comet_id}')
        if r.status_code == 200:
            data = r.json()
            status = data['status']
            proc = data['processed']
            total = data['total']
            
            print(f'Comet: {status} - {proc}/{total}', end='\r')
            
            if status == 'completed':
                print(f'\n\n✅ COMET ЗАВЕРШЕН!\n')
                print(f'Результаты:')
                for res in data.get('results', []):
                    domain = res['domain']
                    inn = res.get('inn', 'Not found')
                    emails = res.get('emails', [])
                    email = emails[0] if emails else 'Not found'
                    print(f'  {domain}: INN={inn}, Email={email}')
                break
        else:
            print(f'Error: {r.status_code}')
            break
    except Exception as e:
        print(f'Error: {e}')
        break

print('\n\n=== Проверяю логи на AUTO-LEARNING ===')
import subprocess
result = subprocess.run(
    ['powershell', '-Command', 
     'Get-Content logs\\Backend-20260112-143820.log | Select-String -Pattern "AUTO-LEARNING|AUTO-TRIGGER" | Select-Object -Last 20'],
    capture_output=True,
    text=True,
    cwd='D:\\tryagain'
)

if result.stdout.strip():
    print('✅ НАЙДЕНЫ ЛОГИ AUTO-LEARNING:')
    for line in result.stdout.strip().split('\n'):
        print(f'  {line}')
else:
    print('⚠️ Логи не найдены')
