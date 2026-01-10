-- Скрипт для удаления дубликатов поставщиков
-- Оставляет самую новую запись для каждого домена

-- 1. Показать статистику дубликатов
SELECT 
    domain,
    COUNT(*) as count,
    STRING_AGG(id::text, ', ' ORDER BY created_at DESC) as ids
FROM moderator_suppliers
WHERE domain IS NOT NULL
GROUP BY domain
HAVING COUNT(*) > 1
ORDER BY count DESC;

-- 2. Удалить дубликаты (оставить самую новую запись)
-- ВНИМАНИЕ: Раскомментируйте следующий блок для выполнения удаления

/*
DELETE FROM moderator_suppliers
WHERE id IN (
    SELECT id
    FROM (
        SELECT 
            id,
            ROW_NUMBER() OVER (PARTITION BY domain ORDER BY created_at DESC) as rn
        FROM moderator_suppliers
        WHERE domain IS NOT NULL
    ) t
    WHERE rn > 1
);
*/

-- 3. Добавить UNIQUE constraint на domain (после удаления дубликатов)
-- ВНИМАНИЕ: Раскомментируйте следующую строку после удаления дубликатов

-- ALTER TABLE moderator_suppliers ADD CONSTRAINT unique_domain UNIQUE (domain);

-- 4. Проверить результат
-- SELECT domain, COUNT(*) FROM moderator_suppliers GROUP BY domain HAVING COUNT(*) > 1;
