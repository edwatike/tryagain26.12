"""Скрипт для удаления дубликатов поставщиков из базы данных.

Удаляет дубликаты по домену, оставляя самую новую запись.

ЗАПУСК: python remove_duplicates.py (из корня проекта d:/tryagain/)
"""
import asyncio
import sys
import os
from collections import defaultdict

# Добавляем путь к backend
backend_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend')
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

try:
    from app.adapters.db.models import ModeratorSupplierModel
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    print(f"Текущая директория: {os.getcwd()}")
    print(f"Backend path: {backend_path}")
    print(f"sys.path: {sys.path[:3]}")
    sys.exit(1)

# Database URL
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/moderator_db")

print("="*70)
print("🗑️  УДАЛЕНИЕ ДУБЛИКАТОВ ПОСТАВЩИКОВ")
print("="*70)


async def remove_duplicates():
    """Удалить дубликаты поставщиков, оставив самую новую запись."""
    
    # Создаем engine и session
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        print("\n1️⃣ Поиск дубликатов...")
        
        # Получаем всех поставщиков
        result = await session.execute(
            select(ModeratorSupplierModel)
            .order_by(ModeratorSupplierModel.domain, ModeratorSupplierModel.created_at.desc())
        )
        suppliers = result.scalars().all()
        
        print(f"   Всего поставщиков: {len(suppliers)}")
        
        # Группируем по домену
        by_domain = defaultdict(list)
        for supplier in suppliers:
            if supplier.domain:
                by_domain[supplier.domain.lower()].append(supplier)
        
        # Находим дубликаты
        duplicates_info = []
        total_duplicates = 0
        
        for domain, domain_suppliers in by_domain.items():
            if len(domain_suppliers) > 1:
                duplicates_info.append({
                    'domain': domain,
                    'count': len(domain_suppliers),
                    'suppliers': domain_suppliers
                })
                total_duplicates += len(domain_suppliers) - 1
        
        print(f"   Найдено доменов с дубликатами: {len(duplicates_info)}")
        print(f"   Всего дубликатов для удаления: {total_duplicates}")
        
        if not duplicates_info:
            print("\n✅ Дубликатов не найдено!")
            return
        
        # Показываем топ-10 доменов с наибольшим количеством дубликатов
        print("\n2️⃣ Топ-10 доменов с дубликатами:")
        sorted_duplicates = sorted(duplicates_info, key=lambda x: x['count'], reverse=True)
        for i, dup in enumerate(sorted_duplicates[:10], 1):
            print(f"   {i}. {dup['domain']}: {dup['count']} записей")
        
        # Спрашиваем подтверждение
        print(f"\n⚠️  ВНИМАНИЕ: Будет удалено {total_duplicates} дубликатов!")
        print("   Будут оставлены самые новые записи для каждого домена.")
        
        response = input("\nПродолжить? (yes/no): ")
        if response.lower() not in ['yes', 'y', 'да']:
            print("❌ Отменено пользователем")
            return
        
        print("\n3️⃣ Удаление дубликатов...")
        deleted_count = 0
        
        for dup_info in duplicates_info:
            domain = dup_info['domain']
            domain_suppliers = dup_info['suppliers']
            
            # Оставляем первую запись (самую новую), удаляем остальные
            keep = domain_suppliers[0]
            to_delete = domain_suppliers[1:]
            
            print(f"\n   Домен: {domain}")
            print(f"   Оставляем: ID={keep.id}, Название={keep.name}, Создан={keep.created_at}")
            
            for supplier in to_delete:
                print(f"   Удаляем:   ID={supplier.id}, Название={supplier.name}, Создан={supplier.created_at}")
                await session.delete(supplier)
                deleted_count += 1
        
        # Сохраняем изменения
        await session.commit()
        
        print("\n" + "="*70)
        print(f"✅ УСПЕШНО УДАЛЕНО: {deleted_count} дубликатов")
        print("="*70)
        
        # Показываем итоговую статистику
        result = await session.execute(select(func.count()).select_from(ModeratorSupplierModel))
        total_after = result.scalar()
        print(f"\nОсталось поставщиков в базе: {total_after}")
    
    await engine.dispose()


async def show_statistics():
    """Показать статистику по дубликатам без удаления."""
    
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        print("\n📊 СТАТИСТИКА ДУБЛИКАТОВ")
        print("="*70)
        
        # Получаем всех поставщиков
        result = await session.execute(
            select(ModeratorSupplierModel)
            .order_by(ModeratorSupplierModel.domain, ModeratorSupplierModel.created_at.desc())
        )
        suppliers = result.scalars().all()
        
        print(f"Всего поставщиков: {len(suppliers)}")
        
        # Группируем по домену
        by_domain = defaultdict(list)
        for supplier in suppliers:
            if supplier.domain:
                by_domain[supplier.domain.lower()].append(supplier)
        
        # Находим дубликаты
        duplicates_info = []
        total_duplicates = 0
        
        for domain, domain_suppliers in by_domain.items():
            if len(domain_suppliers) > 1:
                duplicates_info.append({
                    'domain': domain,
                    'count': len(domain_suppliers),
                    'suppliers': domain_suppliers
                })
                total_duplicates += len(domain_suppliers) - 1
        
        print(f"Доменов с дубликатами: {len(duplicates_info)}")
        print(f"Всего дубликатов: {total_duplicates}")
        
        if duplicates_info:
            print("\nВсе домены с дубликатами:")
            sorted_duplicates = sorted(duplicates_info, key=lambda x: x['count'], reverse=True)
            for i, dup in enumerate(sorted_duplicates, 1):
                print(f"{i}. {dup['domain']}: {dup['count']} записей")
                for supplier in dup['suppliers']:
                    print(f"   - ID={supplier.id}, {supplier.name}, Создан={supplier.created_at}")
        else:
            print("\n✅ Дубликатов не найдено!")
    
    await engine.dispose()


if __name__ == "__main__":
    print("\nВыберите действие:")
    print("1. Показать статистику дубликатов")
    print("2. Удалить дубликаты")
    
    choice = input("\nВаш выбор (1/2): ")
    
    if choice == "1":
        asyncio.run(show_statistics())
    elif choice == "2":
        asyncio.run(remove_duplicates())
    else:
        print("❌ Неверный выбор")
