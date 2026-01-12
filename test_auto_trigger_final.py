import requests
import time
import subprocess

print('=== ФИНАЛЬНЫЙ ТЕСТ АВТОТРИГГЕРА ===\n')

# Запускаю Domain Parser
print('Запускаю Domain Parser с доменами: armaturka.ru, kc27.ru')
r = requests.post(
    'http://127.0.0.1:8000/domain-parser/extract-batch',
    json={'runId': '35e40edd-7182-4d45-a39f-55333c0d152b', 'domains': ['armaturka.ru', 'kc27.ru']}
)

if r.status_code == 200:
    data = r.json()
    parser_id = data['parserRunId']
    print(f'✅ Parser запущен: {parser_id}\n')
    
    # Ждем завершения
    print('Ожидаю завершения Domain Parser...\n')
    for i in range(60):
        time.sleep(2)
        s = requests.get(f'http://127.0.0.1:8000/domain-parser/status/{parser_id}')
        if s.status_code == 200:
            st = s.json()
            status = st['status']
            proc = st['processed']
            total = st['total']
            
            if status == 'completed':
                print(f'\n✅ Domain Parser ЗАВЕРШЕН!\n')
                print('Результаты:')
                for res in st['results']:
                    domain = res['domain']
                    inn = res.get('inn', 'Not found')
                    emails = res.get('emails', [])
                    email = emails[0] if emails else 'Not found'
                    print(f'  {domain}: INN={inn}, Email={email}')
                break
            print(f'  {status} - {proc}/{total}', end='\r')
    
    print('\n\n=== Жду 15 секунд для автотриггера Comet ===')
    time.sleep(15)
    
    print('\n=== Проверяю логи Backend на AUTO-TRIGGER ===')
    result = subprocess.run(
        ['powershell', '-Command', 
         f'Get-Content logs\\Backend-20260112-143820.log | Select-String -Pattern "{parser_id}|AUTO-TRIGGER|PROCESSING DOMAIN PARSER" | Select-Object -Last 50'],
        capture_output=True,
        text=True,
        cwd='D:\\tryagain'
    )
    
    if result.stdout.strip():
        print('✅ НАЙДЕНЫ ЛОГИ:')
        lines = result.stdout.strip().split('\n')
        for line in lines:
            print(f'  {line}')
    else:
        print('⚠️ Логи не найдены - проверяю вручную...')
        
        # Проверяем последние 100 строк лога
        result2 = subprocess.run(
            ['powershell', '-Command', 'Get-Content logs\\Backend-20260112-143820.log -Tail 100'],
            capture_output=True,
            text=True,
            cwd='D:\\tryagain'
        )
        print('\nПоследние 100 строк лога:')
        print(result2.stdout[-2000:])  # Последние 2000 символов
        
else:
    print(f'❌ Error: {r.status_code}')
    print(r.text)
