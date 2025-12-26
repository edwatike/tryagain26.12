#!/usr/bin/env python3
"""
Скрипт для проверки отсутствующих импортов date/datetime в роутерах и usecases.

Использование:
    python temp/backend/check_imports.py
"""

import os
import re
import sys
from pathlib import Path

# Пути для проверки
ROUTERS_DIR = Path("backend/app/transport/routers")
USECASES_DIR = Path("backend/app/usecases")

# Паттерны для поиска использования date/datetime
PATTERNS = [
    (r"isinstance\([^,]+,\s*date\)", "date"),
    (r"isinstance\([^,]+,\s*datetime\)", "datetime"),
    (r":\s*date\s*[=:]", "date"),  # type hints
    (r":\s*datetime\s*[=:]", "datetime"),  # type hints
]

def check_file(file_path: Path) -> list:
    """Проверить файл на отсутствующие импорты."""
    errors = []
    
    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception as e:
        return [f"Ошибка чтения файла {file_path}: {e}"]
    
    # Проверить наличие импортов
    has_date_import = bool(re.search(r"from datetime import.*date|import datetime", content))
    has_datetime_import = bool(re.search(r"from datetime import.*datetime|import datetime", content))
    
    # Проверить использование
    uses_date = False
    uses_datetime = False
    
    for pattern, type_name in PATTERNS:
        if re.search(pattern, content):
            if type_name == "date":
                uses_date = True
            elif type_name == "datetime":
                uses_datetime = True
    
    # Проверить ошибки
    if uses_date and not has_date_import:
        errors.append(f"  ERROR: Uses 'date' but missing import 'from datetime import date'")
    
    if uses_datetime and not has_datetime_import:
        errors.append(f"  ERROR: Uses 'datetime' but missing import 'from datetime import datetime'")
    
    return errors

def main():
    """Основная функция."""
    print("Checking date/datetime imports in routers and usecases...\n")
    
    all_errors = []
    
    # Проверить роутеры
    if ROUTERS_DIR.exists():
        print(f"Checking routers: {ROUTERS_DIR}")
        for py_file in ROUTERS_DIR.glob("*.py"):
            if py_file.name == "__init__.py":
                continue
            errors = check_file(py_file)
            if errors:
                print(f"\n  File: {py_file.name}:")
                for error in errors:
                    print(error)
                all_errors.extend([(py_file, e) for e in errors])
    
    # Проверить usecases
    if USECASES_DIR.exists():
        print(f"\nChecking usecases: {USECASES_DIR}")
        for py_file in USECASES_DIR.glob("*.py"):
            if py_file.name == "__init__.py":
                continue
            errors = check_file(py_file)
            if errors:
                print(f"\n  File: {py_file.name}:")
                for error in errors:
                    print(error)
                all_errors.extend([(py_file, e) for e in errors])
    
    # Итог
    print("\n" + "="*60)
    if all_errors:
        print(f"ERROR: Found {len(all_errors)} import problems!")
        print("\nFix missing imports before committing.")
        sys.exit(1)
    else:
        print("OK: All imports are in place!")
        sys.exit(0)

if __name__ == "__main__":
    main()

