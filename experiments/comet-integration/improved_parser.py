"""
УЛУЧШЕННЫЙ ПАРСЕР ОТВЕТОВ
"""
import re

def parse_comet_response(response_text: str, domain: str) -> dict:
    """Распарсить ответ ассистента."""
    result = {
        'domain': domain,
        'inn': '',
        'email': '',
        'phone': '',
        'address': '',
        'company': '',
        'success': False,
        'raw_response': response_text
    }
    
    # Ищем ИНН разными способами
    inn_patterns = [
        r'ИНН[:\s]*(\d{10,12})',
        r'ИНН\s*[:\-]?\s*(\d{10,12})',
        r'инн[:\s]*(\d{10,12})',
        r'(\b\d{10}\b)',  # 10 цифр
        r'(\b\d{12}\b)',  # 12 цифр
    ]
    
    for pattern in inn_patterns:
        matches = re.findall(pattern, response_text, re.IGNORECASE)
        if matches:
            inn = matches[0] if isinstance(matches[0], str) else matches[0][0]
            inn = re.sub(r'[^\d]', '', str(inn))
            if len(inn) in [10, 12]:
                result['inn'] = inn
                break
    
    # Ищем email
    email_patterns = [
        r'\b([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\b',
        r'email[:\s]*([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
        r'E-mail[:\s]*([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
    ]
    
    for pattern in email_patterns:
        matches = re.findall(pattern, response_text, re.IGNORECASE)
        if matches:
            result['email'] = matches[0]
            break
    
    # Ищем телефон
    phone_patterns = [
        r'\+?\s*7\s*[\(\s]*(\d{3})[\)\s]*(\d{3})[\s-]*(\d{2})[\s-]*(\d{2})',
        r'8\s*[\(\s]*(\d{3})[\)\s]*(\d{3})[\s-]*(\d{2})[\s-]*(\d{2})',
        r'\+?\d{1,3}[\s-]?\d{3}[\s-]?\d{3}[\s-]?\d{2}[\s-]?\d{2}',
    ]
    
    for pattern in phone_patterns:
        matches = re.findall(pattern, response_text)
        if matches:
            if isinstance(matches[0], tuple):
                phone = ''.join(matches[0])
            else:
                phone = matches[0]
            result['phone'] = phone
            break
    
    # Ищем адрес
    address_patterns = [
        r'(г\.\s*[А-Яа-я\s]+\s*[А-Яа-я\s]+\d+[\s,к\.]*)',
        r'(г\.\s*[А-Яа-я\s]+,\s*ул\.\s*[А-Яа-я\s]+[\d\s,к\.]*)',
        r'([А-Яа-я]+\s*[А-Яа-я]*\s*\d+[\s,к\.]*)',
    ]
    
    for pattern in address_patterns:
        matches = re.findall(pattern, response_text)
        if matches:
            result['address'] = matches[0].strip()
            break
    
    # Ищем название компании
    company_patterns = [
        r'([А-Яа-я\s]+[«""][А-Яа-я\s]+[»""])',
        r'(ООО\s+[«""][А-Яа-я\s]+[»""])',
        r'([А-Яа-я\s]+[«""][А-Яа-я\s]+[»""])',
    ]
    
    for pattern in company_patterns:
        matches = re.findall(pattern, response_text)
        if matches:
            result['company'] = matches[0].strip()
            break
    
    # Определяем успех
    result['success'] = bool(result['inn'] or result['email'])
    
    return result

# Тест парсера
if __name__ == "__main__":
    test_response = """
    » Попробуйте изменить формулировку, воспользуйтесь каталогом, или свяжитесь с нами
    На главную
    Контакты
    +7 (831) 414-XX-XX Показать номер
    nn@metsnab.pro
    г. Нижний Новгород, ш. Московское, 52, к. 1
    Время работы: пн-пт 8:00-18:00, сб, вс выходной
    Все контакты
    © МЕТАЛЛСНАБ Нижний Новгород, 2018—2026
    """
    
    result = parse_comet_response(test_response, "metallsnab-nn.ru")
    
    print("📊 РЕЗУЛЬТАТ ПАРСИНГА:")
    print(f"   Домен: {result['domain']}")
    print(f"   ИНН: {result['inn']}")
    print(f"   Email: {result['email']}")
    print(f"   Телефон: {result['phone']}")
    print(f"   Адрес: {result['address']}")
    print(f"   Компания: {result['company']}")
    print(f"   Успех: {result['success']}")
