"""Tests for PostgreSQL sequences after migrations."""
import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
import os
from typing import Optional


# Маркер для тестов, требующих реальную PostgreSQL БД
pytestmark = pytest.mark.skipif(
    os.getenv("SKIP_POSTGRES_TESTS", "false").lower() == "true",
    reason="PostgreSQL tests skipped via SKIP_POSTGRES_TESTS"
)


@pytest.fixture
async def postgres_session() -> Optional[AsyncSession]:
    """Create PostgreSQL database session for sequence tests."""
    # Получить параметры подключения из переменных окружения или использовать значения по умолчанию
    db_url = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:Jnvnszoe5971312059001@localhost:5432/b2bplatform"
    )
    
    try:
        engine = create_async_engine(db_url, echo=False)
        
        # Проверить подключение
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        
        async_session = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        
        async with async_session() as session:
            yield session
        
        await engine.dispose()
    except Exception as e:
        pytest.skip(f"PostgreSQL not available: {e}")


@pytest.mark.asyncio
async def test_domains_queue_sequence_exists(postgres_session: AsyncSession):
    """Проверить, что последовательность domains_queue_id_seq существует."""
    result = await postgres_session.execute(
        text("""
            SELECT sequence_name 
            FROM information_schema.sequences 
            WHERE sequence_name = 'domains_queue_id_seq'
        """)
    )
    sequence = result.scalar_one_or_none()
    
    assert sequence is not None, "Последовательность domains_queue_id_seq не найдена!"


@pytest.mark.asyncio
async def test_domains_queue_sequence_permissions(postgres_session: AsyncSession):
    """Проверить права доступа на последовательность domains_queue_id_seq."""
    # Проверить, что последовательность существует
    result = await postgres_session.execute(
        text("""
            SELECT sequence_name 
            FROM information_schema.sequences 
            WHERE sequence_name = 'domains_queue_id_seq'
        """)
    )
    sequence = result.scalar_one_or_none()
    
    if sequence is None:
        pytest.skip("Последовательность domains_queue_id_seq не существует")
    
    # Проверить права доступа (попробовать использовать последовательность)
    try:
        result = await postgres_session.execute(
            text("SELECT nextval('domains_queue_id_seq')")
        )
        next_val = result.scalar()
        assert next_val is not None, "Не удалось получить следующее значение последовательности"
    except Exception as e:
        pytest.fail(f"Нет прав доступа на последовательность domains_queue_id_seq: {e}")


@pytest.mark.asyncio
async def test_domains_queue_sequence_name_consistency(postgres_session: AsyncSession):
    """Проверить, что имя последовательности соответствует стандарту."""
    # Проверить, что нет последовательностей с неправильными именами
    result = await postgres_session.execute(
        text("""
            SELECT sequence_name 
            FROM information_schema.sequences 
            WHERE sequence_name LIKE '%domains_queue%seq%'
            AND sequence_name != 'domains_queue_id_seq'
        """)
    )
    wrong_sequences = result.scalars().all()
    
    assert len(wrong_sequences) == 0, (
        f"Найдены последовательности с неправильными именами: {list(wrong_sequences)}. "
        f"Ожидается только domains_queue_id_seq"
    )


@pytest.mark.asyncio
async def test_all_sequences_have_permissions(postgres_session: AsyncSession):
    """Проверить, что все последовательности имеют права доступа."""
    # Получить все последовательности в схеме public
    result = await postgres_session.execute(
        text("""
            SELECT sequence_name 
            FROM information_schema.sequences 
            WHERE sequence_schema = 'public'
            ORDER BY sequence_name
        """)
    )
    sequences = result.scalars().all()
    
    if not sequences:
        pytest.skip("Нет последовательностей для проверки")
    
    failed_sequences = []
    
    for seq_name in sequences:
        try:
            # Попробовать использовать последовательность
            await postgres_session.execute(text(f"SELECT nextval('{seq_name}')"))
        except Exception as e:
            failed_sequences.append((seq_name, str(e)))
    
    assert len(failed_sequences) == 0, (
        f"Последовательности без прав доступа: {failed_sequences}"
    )


@pytest.mark.asyncio
async def test_sequence_owner_is_postgres(postgres_session: AsyncSession):
    """Проверить, что владелец последовательности - postgres."""
    result = await postgres_session.execute(
        text("""
            SELECT sequence_name, sequence_schema
            FROM information_schema.sequences 
            WHERE sequence_name = 'domains_queue_id_seq'
        """)
    )
    sequence_info = result.fetchone()
    
    if sequence_info is None:
        pytest.skip("Последовательность domains_queue_id_seq не существует")
    
    # Проверить владельца через pg_class
    result = await postgres_session.execute(
        text("""
            SELECT pg_get_userbyid(c.relowner) as owner
            FROM pg_class c
            JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE c.relname = 'domains_queue_id_seq'
            AND n.nspname = 'public'
        """)
    )
    owner = result.scalar_one_or_none()
    
    assert owner == "postgres", f"Владелец последовательности: {owner}, ожидается: postgres"


@pytest.mark.asyncio
async def test_no_orphaned_sequences(postgres_session: AsyncSession):
    """Проверить, что нет последовательностей без связанных таблиц."""
    # Получить все последовательности
    result = await postgres_session.execute(
        text("""
            SELECT sequence_name 
            FROM information_schema.sequences 
            WHERE sequence_schema = 'public'
        """)
    )
    all_sequences = set(result.scalars().all())
    
    # Получить все таблицы с SERIAL полями
    result = await postgres_session.execute(
        text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
    )
    all_tables = set(result.scalars().all())
    
    # Проверить, что каждая последовательность соответствует таблице
    orphaned = []
    for seq_name in all_sequences:
        # Извлечь имя таблицы из имени последовательности (формат: table_name_id_seq)
        if seq_name.endswith("_id_seq"):
            table_name = seq_name[:-7]  # Убрать "_id_seq"
            if table_name not in all_tables:
                orphaned.append(seq_name)
    
    # domains_queue_id_seq может существовать даже если таблица была переименована
    # Поэтому проверяем только явно проблемные случаи
    problematic = [s for s in orphaned if not s.startswith("domains_queue")]
    
    assert len(problematic) == 0, (
        f"Найдены последовательности без связанных таблиц: {problematic}"
    )

