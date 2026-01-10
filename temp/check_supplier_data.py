"""Проверка структуры данных поставщика"""
import requests
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

r = requests.get('http://127.0.0.1:8000/moderator/suppliers/16')
data = r.json()
checko = json.loads(data.get('checkoData', '{}'))

print("=== Проверка структуры данных ===")
print(f"\nВсе ключи в checkoData: {list(checko.keys())[:30]}")

# Проверка ОКВЭД
okved_key = None
for key in ['ОКВЭД', 'ОКВЭДы', 'okved', 'OKVED']:
    if key in checko:
        okved_key = key
        break

if okved_key:
    okved_data = checko[okved_key]
    print(f"\n✅ ОКВЭД найден (ключ: {okved_key})")
    print(f"   Тип: {type(okved_data)}")
    if isinstance(okved_data, list):
        print(f"   Количество: {len(okved_data)}")
        if len(okved_data) > 0:
            print(f"   Первый элемент: {okved_data[0]}")
    else:
        print(f"   Значение: {okved_data}")
else:
    print("\n❌ ОКВЭД не найден")

# Проверка Учредителей
uchred_key = None
for key in ['Учред', 'Учредители', 'founders', 'Founders']:
    if key in checko:
        uchred_key = key
        break

if uchred_key:
    uchred_data = checko[uchred_key]
    print(f"\n✅ Учредители найдены (ключ: {uchred_key})")
    print(f"   Тип: {type(uchred_data)}")
    if isinstance(uchred_data, list):
        print(f"   Количество: {len(uchred_data)}")
        if len(uchred_data) > 0:
            print(f"   Первый элемент: {uchred_data[0]}")
    else:
        print(f"   Значение: {uchred_data}")
else:
    print("\n❌ Учредители не найдены")

# Проверка рейтинга
rating_keys = ['rating', 'Рейтинг', 'Rating', 'Оценка']
for key in rating_keys:
    if key in checko:
        print(f"\n✅ Рейтинг найден (ключ: {key}): {checko[key]}")
        break
else:
    print("\n❌ Рейтинг не найден")







