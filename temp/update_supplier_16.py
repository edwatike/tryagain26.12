"""
Скрипт для обновления данных поставщика ID 16 и проверки соответствия с Checko.ru
"""
import sys
import json
import requests
from datetime import datetime

# Настройка кодировки для Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

API_BASE_URL = "http://127.0.0.1:8000"

def get_supplier(supplier_id: int):
    """Получить данные поставщика"""
    response = requests.get(f"{API_BASE_URL}/moderator/suppliers/{supplier_id}")
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Ошибка получения поставщика: {response.status_code}")
        print(response.text)
        return None

def get_checko_data(inn: str, force_refresh: bool = False):
    """Получить данные Checko"""
    url = f"{API_BASE_URL}/moderator/checko/{inn}"
    if force_refresh:
        url += "?force_refresh=true"
    
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Ошибка получения данных Checko: {response.status_code}")
        print(response.text)
        return None

def update_supplier(supplier_id: int, data: dict):
    """Обновить данные поставщика"""
    response = requests.put(
        f"{API_BASE_URL}/moderator/suppliers/{supplier_id}",
        json=data,
        headers={"Content-Type": "application/json; charset=utf-8"}
    )
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Ошибка обновления поставщика: {response.status_code}")
        print(response.text)
        return None

def main():
    print("=" * 80)
    print("Обновление данных поставщика ID 16")
    print("=" * 80)
    
    # 1. Получаем данные поставщика
    print("\n1. Получение данных поставщика ID 16...")
    supplier = get_supplier(16)
    if not supplier:
        print("❌ Не удалось получить данные поставщика")
        return
    
    print(f"✅ Поставщик найден: {supplier.get('name', 'N/A')}")
    print(f"   ИНН: {supplier.get('inn', 'N/A')}")
    print(f"   ОГРН: {supplier.get('ogrn', 'N/A')}")
    print(f"   КПП: {supplier.get('kpp', 'N/A')}")
    
    # 2. Проверяем наличие ИНН
    inn = supplier.get('inn')
    if not inn or len(inn) < 10:
        print("❌ ИНН не указан или некорректен")
        return
    
    # 3. Проверяем данные Checko
    checko_data_str = supplier.get('checkoData')
    has_checko_data = checko_data_str and len(checko_data_str) > 0
    
    if has_checko_data:
        try:
            checko_data = json.loads(checko_data_str)
            timestamp = checko_data.get('timestamp', 0)
            age_hours = (datetime.now().timestamp() - timestamp) / 3600 if timestamp else 999
            print(f"\n2. Данные Checko найдены (возраст: {age_hours:.1f} часов)")
            
            if age_hours < 24:
                print("✅ Данные Checko актуальны (менее 24 часов)")
                should_refresh = False
            else:
                print("⚠️ Данные Checko устарели (более 24 часов)")
                should_refresh = True
        except json.JSONDecodeError:
            print("⚠️ Данные Checko повреждены, требуется обновление")
            should_refresh = True
    else:
        print("\n2. Данные Checko отсутствуют")
        should_refresh = True
    
    # 4. Загружаем данные Checko если нужно
    if should_refresh:
        print(f"\n3. Загрузка данных Checko для ИНН {inn}...")
        checko_response = get_checko_data(inn, force_refresh=True)
        if not checko_response:
            print("❌ Не удалось загрузить данные Checko")
            return
        
        print("✅ Данные Checko загружены")
        print(f"   Название: {checko_response.get('name', 'N/A')}")
        print(f"   ОГРН: {checko_response.get('ogrn', 'N/A')}")
        print(f"   КПП: {checko_response.get('kpp', 'N/A')}")
        print(f"   Статус: {checko_response.get('companyStatus', 'N/A')}")
        print(f"   Выручка: {checko_response.get('revenue', 'N/A')}")
        print(f"   Прибыль: {checko_response.get('profit', 'N/A')}")
        
        # 5. Обновляем поставщика
        print(f"\n4. Обновление данных поставщика...")
        update_data = {
            "name": checko_response.get('name') or supplier.get('name'),
            "inn": inn,
            "email": supplier.get('email'),
            "domain": supplier.get('domain'),
            "address": supplier.get('address'),
            "type": supplier.get('type'),
            "ogrn": checko_response.get('ogrn'),
            "kpp": checko_response.get('kpp'),
            "okpo": checko_response.get('okpo'),
            "companyStatus": checko_response.get('companyStatus'),
            "registrationDate": checko_response.get('registrationDate'),
            "legalAddress": checko_response.get('legalAddress'),
            "phone": checko_response.get('phone'),
            "website": checko_response.get('website'),
            "vk": checko_response.get('vk'),
            "telegram": checko_response.get('telegram'),
            "authorizedCapital": checko_response.get('authorizedCapital'),
            "revenue": checko_response.get('revenue'),
            "profit": checko_response.get('profit'),
            "financeYear": checko_response.get('financeYear'),
            "legalCasesCount": checko_response.get('legalCasesCount'),
            "legalCasesSum": checko_response.get('legalCasesSum'),
            "legalCasesAsPlaintiff": checko_response.get('legalCasesAsPlaintiff'),
            "legalCasesAsDefendant": checko_response.get('legalCasesAsDefendant'),
            "checkoData": checko_response.get('checkoData'),
        }
        
        updated_supplier = update_supplier(16, update_data)
        if updated_supplier:
            print("✅ Поставщик успешно обновлен")
        else:
            print("❌ Ошибка обновления поставщика")
            return
    else:
        print("\n3. Обновление не требуется")
        updated_supplier = supplier
    
    # 6. Проверяем соответствие с Checko.ru
    print("\n" + "=" * 80)
    print("Проверка соответствия с Checko.ru")
    print("=" * 80)
    print("\nОжидаемые данные (из Checko.ru):")
    print("  Название: ООО \"СТРОЙТОРГОВЛЯ\"")
    print("  ИНН: 4703148343")
    print("  ОГРН: 1174704000767")
    print("  КПП: 470301001")
    print("  Дата регистрации: 26 января 2017 года")
    print("  Адрес: 188643, Ленинградская область, Всеволожский район, г. Всеволожск, Колтушское шоссе, д. 298, офис 17")
    print("  Выручка 2024: 12,9 млрд руб.")
    print("  Прибыль 2024: 420,2 млн руб.")
    
    print("\nФактические данные (из нашей БД):")
    print(f"  Название: {updated_supplier.get('name', 'N/A')}")
    print(f"  ИНН: {updated_supplier.get('inn', 'N/A')}")
    print(f"  ОГРН: {updated_supplier.get('ogrn', 'N/A')}")
    print(f"  КПП: {updated_supplier.get('kpp', 'N/A')}")
    print(f"  Дата регистрации: {updated_supplier.get('registrationDate', 'N/A')}")
    print(f"  Адрес: {updated_supplier.get('legalAddress', 'N/A')}")
    print(f"  Выручка: {updated_supplier.get('revenue', 'N/A')}")
    print(f"  Прибыль: {updated_supplier.get('profit', 'N/A')}")
    print(f"  Год финансов: {updated_supplier.get('financeYear', 'N/A')}")
    
    # Проверяем checkoData
    checko_data_str = updated_supplier.get('checkoData')
    if checko_data_str:
        try:
            checko_data = json.loads(checko_data_str)
            finances = checko_data.get('_finances', {})
            print(f"\n  Финансовые данные в checkoData:")
            for year in sorted(finances.keys()):
                year_data = finances[year]
                revenue = year_data.get('2110', 0)
                profit = year_data.get('2400', 0)
                print(f"    {year}: Выручка={revenue}, Прибыль={profit}")
        except json.JSONDecodeError:
            print("  ⚠️ checkoData не является валидным JSON")
    
    print("\n" + "=" * 80)
    print("✅ Проверка завершена")
    print("=" * 80)
    print("\nОткройте http://localhost:3000/suppliers/16 для просмотра обновленной карточки")

if __name__ == "__main__":
    main()

