import requests
import time
import subprocess

print('=== ФИНАЛЬНЫЙ ТЕСТ С ИСПРАВЛЕННЫМИ ЗАВИСИМОСТЯМИ ===\n')

# Запускаю Domain Parser для нового домена
print('Запускаю Domain Parser для домена: elektro.ru')
r = requests.post(
    'http://127.0.0.1:8000/domain-parser/extract-batch',
    json={'runId': '35e40edd-7182-4d45-a39f-55333c0d152b', 'domains': ['elektro.ru']}
)

if r.status_code == 200:
    data = r.json()
    parser_id = data['parserRunId']
    print(f'✅ Parser запущен: {parser_id}\n')
    
    # Ждем завершения
    print('Ожидаю завершения Domain Parser...')
    for i in range(60):
        time.sleep(2)
        s = requests.get(f'http://127.0.0.1:8000/domain-parser/status/{parser_id}')
        if s.status_code == 200:
            st = s.json()
            if st['status'] == 'completed':
                print(f'\n✅ Domain Parser завершен!\n')
                for res in st['results']:
                    domain = res['domain']
                    inn = res.get('inn', 'Not found')
                    emails = res.get('emails', [])
                    email = emails[0] if emails else 'Not found'
                    print(f'  {domain}: INN={inn}, Email={email}')
                break
            print(f"  {st['status']} - {st['processed']}/{st['total']}", end='\r')
    
    print('\n\n=== Жду 20 секунд для Comet ===')
    time.sleep(20)
    
    print('\n=== Проверяю логи Backend ===')
    result = subprocess.run(
        ['powershell', '-Command', 
         f'Get-Content logs\\Backend-20260112-143820.log -Tail 200 | Select-String -Pattern "AUTO-TRIGGER|Comet.*started|ModuleNotFoundError|elektro" | Select-Object -Last 30'],
        capture_output=True,
        text=True,
        cwd='D:\\tryagain'
    )
    
    if result.stdout.strip():
        print('✅ ЛОГИ НАЙДЕНЫ:')
        for line in result.stdout.strip().split('\n'):
            print(f'  {line}')
    else:
        print('⚠️ Логи не найдены')
        
        # Показываем последние 50 строк
        result2 = subprocess.run(
            ['powershell', '-Command', 'Get-Content logs\\Backend-20260112-143820.log -Tail 50'],
            capture_output=True,
            text=True,
            cwd='D:\\tryagain'
        )
        print('\nПоследние 50 строк лога:')
        print(result2.stdout[-3000:])
else:
    print(f'❌ Error: {r.status_code}')
    print(r.text)
