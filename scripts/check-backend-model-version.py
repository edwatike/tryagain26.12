"""Скрипт для проверки версии модели ParsingRunModel."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

def check_model_version():
    """Проверяет, содержит ли модель ParsingRunModel поле results_count."""
    try:
        from app.adapters.db.models import ParsingRunModel
        
        print("Проверка модели ParsingRunModel...")
        print("=" * 50)
        
        # Проверка 1: hasattr на классе
        has_attr = hasattr(ParsingRunModel, 'results_count')
        print(f"1. hasattr(ParsingRunModel, 'results_count'): {has_attr}")
        
        # Проверка 2: в __table__.columns
        in_columns = 'results_count' in [c.name for c in ParsingRunModel.__table__.columns]
        print(f"2. 'results_count' in table columns: {in_columns}")
        
        # Проверка 3: в dir()
        in_dir = 'results_count' in dir(ParsingRunModel())
        print(f"3. 'results_count' in dir(instance): {in_dir}")
        
        print("=" * 50)
        
        if has_attr and in_columns:
            print("✅ Модель содержит поле results_count")
            return True
        else:
            print("❌ Модель НЕ содержит поле results_count")
            print("   Необходимо перезапустить Backend после изменений модели")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка при проверке модели: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = check_model_version()
    sys.exit(0 if success else 1)




