import requests
import time

print('=== ЗАПУСКАЮ DOMAIN PARSER ===')
r = requests.post(
    'http://127.0.0.1:8000/domain-parser/extract-batch',
    json={'runId': '35e40edd-7182-4d45-a39f-55333c0d152b', 'domains': ['owen.ru', 'elektro.ru']}
)

print(f'Status: {r.status_code}')
if r.status_code == 200:
    data = r.json()
    parser_id = data['parserRunId']
    print(f'Parser ID: {parser_id}')
    print('\nОжидаю завершения...\n')
    
    for i in range(40):
        time.sleep(2)
        s = requests.get(f'http://127.0.0.1:8000/domain-parser/status/{parser_id}')
        if s.status_code == 200:
            st = s.json()
            status = st['status']
            proc = st['processed']
            total = st['total']
            print(f'{status} - {proc}/{total}', end='\r')
            
            if status == 'completed':
                print(f'\n\n✅ DOMAIN PARSER ЗАВЕРШЕН!')
                print(f'Результаты:')
                for res in st['results']:
                    domain = res['domain']
                    inn = res.get('inn', 'Not found')
                    emails = res.get('emails', [])
                    email = emails[0] if emails else 'Not found'
                    print(f'  {domain}: INN={inn}, Email={email}')
                break
        else:
            print(f'Error getting status: {s.status_code}')
            break
    
    print('\n\n=== Проверяю AUTO-TRIGGER в логах ===')
    time.sleep(5)
    
    import subprocess
    result = subprocess.run(
        ['powershell', '-Command', 
         'Get-Content logs\\Backend-*.log -Tail 100 | Select-String -Pattern "AUTO-TRIGGER|Domain parser batch completed" | Select-Object -Last 10'],
        capture_output=True,
        text=True,
        cwd='D:\\tryagain'
    )
    
    if result.stdout.strip():
        print('✅ НАЙДЕНЫ ЛОГИ AUTO-TRIGGER:')
        print(result.stdout)
    else:
        print('⚠️ AUTO-TRIGGER логи не найдены')
        
else:
    print(f'Error: {r.status_code}')
    print(r.text)
