⚠️ **АРХИВ. Актуальная версия: см. `docs/MASTER_INSTRUCTION.md`**

# Полный промпт для V0 - B2B Platform Moderator Dashboard

## ⚠️ ВАЖНО: ВСЯ ИНФОРМАЦИЯ ПЕРЕДАНА ОДИН РАЗ

Этот промпт содержит ВСЮ необходимую информацию для генерации UI. Не задавай дополнительные вопросы - используй эту информацию.

---

## 1. ОТВЕТЫ НА СТАНДАРТНЫЕ ВОПРОСЫ V0

### Какие страницы нужно создать?
**Ответ:** Все страницы сразу (Dashboard, Parsing Runs, Suppliers, Blacklist, Manual Parsing)

### Нужна ли интеграция с базой данных?
**Ответ:** Нет, только API. Все данные получаются через REST API endpoints.

### Какой формат API?
**Ответ:** REST API с JSON, camelCase в запросах/ответах, базовый URL: `http://127.0.0.1:8000`

---

## 2. АРХИТЕКТУРА И ТЕХНОЛОГИИ

### Frontend Stack
- **Framework:** Next.js 14+ (App Router)
- **Language:** TypeScript
- **Styling:** Tailwind CSS
- **UI Components:** Shadcn UI (Card, Badge, Table, Button, Input, Separator, Accordion, Dialog, AlertDialog)
- **Icons:** Lucide React
- **Notifications:** Sonner (toast)

### Backend API
- **Base URL:** `http://127.0.0.1:8000`
- **Format:** REST API, JSON
- **CORS:** Enabled for `http://localhost:3000`
- **Error Format:** `{ detail: string }`

### API Client
- Все запросы идут через `lib/api.ts`
- Используется `apiFetch<T>()` функция
- Обработка ошибок через `APIError` класс

---

## 3. API ENDPOINTS И ТИПЫ ДАННЫХ

### 3.1 Parsing Runs

#### `GET /parsing/runs`
Список запусков парсинга.

**Query параметры:**
- `limit` (int, default=100, min=1, max=1000)
- `offset` (int, default=0, min=0)
- `status` (string, optional): "running" | "completed" | "failed"
- `keyword` (string, optional)
- `sort` (string, default="created_at")
- `order` (string, default="desc"): "asc" | "desc"

**Response:**
```typescript
{
  runs: ParsingRunDTO[]
  total: number
  limit: number
  offset: number
}
```

#### `GET /parsing/runs/{runId}`
Детали запуска парсинга.

**Response:** `ParsingRunDTO`

#### `POST /parsing/start`
Запуск нового парсинга.

**Request:**
```typescript
{
  keyword: string
  depth: number  // 1-10
  source: "google" | "yandex" | "both"
}
```

**Response:** `ParsingRunDTO`

#### `DELETE /parsing/runs/{runId}`
Удаление запуска парсинга.

**Response:** `204 No Content`

### 3.2 Domains Queue (Результаты парсинга)

#### `GET /domains/queue`
Список доменов из очереди (результаты парсинга).

**Query параметры:**
- `limit` (int, default=100, min=1, max=1000)
- `offset` (int, default=0, min=0)
- `status` (string, optional): "pending" | "processing"
- `keyword` (string, optional)
- `parsingRunId` (string, optional) - **КРИТИЧЕСКИ ВАЖНО:** фильтрует результаты по runId

**Response:**
```typescript
{
  entries: DomainQueueEntryDTO[]
  total: number
  limit: number
  offset: number
}
```

**⚠️ КРИТИЧЕСКИ ВАЖНО: Backend Requirements:**
- `GET /domains/queue?parsingRunId={runId}` **ДОЛЖЕН** фильтровать blacklisted домены на сервере
- Blacklist проверка: нормализация к root-domain (например, spb.example.com -> example.com)
- Blacklisted домены (и все поддомены) **НЕ ДОЛЖНЫ** появляться в ответе
- Фильтрация происходит на сервере перед возвратом результатов

**Типы:**
```typescript
interface DomainQueueEntryDTO {
  domain: string
  keyword: string
  url: string
  parsingRunId: string | null
  status: string
  createdAt: string
}
```

### 3.3 Blacklist

#### `GET /moderator/blacklist`
Список доменов в blacklist.

**Query параметры:**
- `limit` (int, default=100, min=1, max=1000)
- `offset` (int, default=0, min=0)

**Response:**
```typescript
{
  entries: BlacklistEntryDTO[]
  total: number
  limit: number
  offset: number
}
```

#### `POST /moderator/blacklist`
Добавить домен в blacklist.

**Request:**
```typescript
{
  domain: string  // root-domain, без http://, без www.
  reason?: string | null
  addedBy?: string | null
  parsingRunId?: string | null
}
```

**Response:** `BlacklistEntryDTO` (status 201)

#### `DELETE /moderator/blacklist/{domain}`
Удалить домен из blacklist.

**Response:** `204 No Content`

**Типы:**
```typescript
interface BlacklistEntryDTO {
  domain: string
  reason: string | null
  addedBy: string | null
  addedAt: string | null
  parsingRunId: string | null
}
```

### 3.4 Suppliers

#### `GET /moderator/suppliers`
Список поставщиков.

**Query параметры:**
- `limit` (int, default=100, min=1, max=1000)
- `offset` (int, default=0, min=0)
- `type` (string, optional): "supplier" | "reseller"

**Response:**
```typescript
{
  suppliers: SupplierDTO[]
  total: number
  limit: number
  offset: number
}
```

#### `POST /moderator/suppliers`
Создать поставщика/реселлера.

**Request:**
```typescript
{
  name: string  // ОБЯЗАТЕЛЬНО
  inn?: string | null
  email?: string | null
  domain?: string | null
  address?: string | null
  type: "supplier" | "reseller"  // default: "supplier"
}
```

**Response:** `SupplierDTO` (status 201)

**Типы:**
```typescript
interface SupplierDTO {
  id: number
  name: string
  inn: string | null
  email: string | null
  domain: string | null
  address: string | null
  type: "supplier" | "reseller"
  // ... другие поля Checko (опциональные)
  createdAt: string
  updatedAt: string
}
```

### 3.5 Parsing Run Status

#### `GET /parsing/status/{runId}`
Статус запуска парсинга.

**Response:**
```typescript
{
  runId: string
  keyword: string
  status: "running" | "completed" | "failed"
  startedAt: string | null
  finishedAt: string | null
  errorMessage: string | null
  resultsCount: number | null
}
```

**Типы:**
```typescript
interface ParsingRunDTO {
  runId: string
  keyword: string
  status: string
  startedAt: string | null
  finishedAt: string | null
  error: string | null
  resultsCount: number | null
  createdAt: string
}
```

---

## 4. СТРАНИЦЫ И UI КОМПОНЕНТЫ

### 4.1 Dashboard (Главная страница) - `/`

**Текущая реализация:** Linear/Notion стиль dashboard

**Компоненты:**
1. **Новый парсинг (верхняя секция, 1/3 экрана):**
   - Input поле для ключевого слова
   - Кнопка "🚀 НОВЫЙ ПАРСИНГ" (▶️)
   - Примеры: [кирпич] [цемент] [труба]

2. **Метрики (2x2 grid, огромные жирные цифры):**
   - 315 ДОМЕНОВ | в обработке
   - 3 НОВЫХ | поставщиков | Today
   - АКТИВНЫХ: 0
   - BLACKLIST: 2

3. **Recent Runs (горизонтальный скролл, карточки):**
   - [кирпич ✅ 28 дек 31]
   - [тест ✅ 28 дек 13]
   - ──→

4. **CTA кнопки (снизу):**
   - [➤ Обработать очередь]
   - [➤ Проверить новых]
   - [📊 Аналитика]

**API вызовы:**
- `getSuppliers({ limit: 1 })` - для счетчика новых поставщиков
- `getParsingRuns({ status: "running", limit: 1 })` - для активных парсингов
- `getDomainsQueue({ limit: 1 })` - для счетчика в очереди
- `getBlacklist({ limit: 1 })` - для счетчика blacklist
- `getParsingRuns({ limit: 10, sort: "created_at", order: "desc" })` - для recent runs

### 4.2 Parsing Runs List - `/parsing-runs`

**Компоненты:**
1. **Заголовок:** "Запуски парсинга"
2. **Фильтры:**
   - Статус: Все | Выполняется | Завершен | Ошибка
   - Поиск по ключевому слову
3. **Таблица:**
   - Ключевое слово
   - Статус (badge)
   - Дата создания
   - Количество результатов
   - Действия: [Открыть] [Удалить]

**API:** `GET /parsing/runs` с фильтрами

### 4.3 Parsing Run Details - `/parsing-runs/[runId]` ⚠️ КРИТИЧЕСКИ ВАЖНО

**⚠️ ЭТА СТРАНИЦА ТРЕБУЕТ ACCORDION UI ДЛЯ РЕЗУЛЬТАТОВ ПАРСИНГА**

#### Компоненты:

1. **Run Summary Card:**
   - Keyword (title, большой шрифт)
   - Status badge (Выполняется | Завершен | Ошибка)
   - Started/Finished dates
   - Results count
   - Duration (если завершен)

2. **Parsing Results Accordion (КРИТИЧЕСКИ ВАЖНО):**
   - **ИСПОЛЬЗУЙ Shadcn UI Accordion компонент**
   - **Группировка по доменам:** один домен = один accordion item
   - **Каждый accordion item:**
     - **Header:** Domain name + Badge с количеством URL
     - **Content:** Список всех URL для этого домена
   - **Дедупликация:** каждый домен появляется только один раз
   - **Blacklisted домены:** НЕ показываются (фильтруются на backend или frontend)
   - **Empty state:** "No results found" или "All domains are blacklisted"

3. **Domain Actions (для каждого домена в accordion):**
   - **"Add to Blacklist" button** (black/destructive, size="sm")
     - При клике: `POST /moderator/blacklist { domain, parsingRunId }`
     - После успеха: домен исчезает из accordion (refetch results)
   - **"Create Supplier" button** (green, size="sm")
     - Открывает modal с формой: name (required), inn, email, domain (pre-filled), address
     - При submit: `POST /moderator/suppliers { name, inn?, email?, domain, address?, type: "supplier" }`
   - **"Create Reseller" button** (purple, size="sm")
     - То же самое, что Create Supplier, но `type: "reseller"`

#### Логика группировки (Frontend):

1. Получить плоский список: `GET /domains/queue?parsingRunId={runId}`
2. Если backend не фильтрует blacklist, фильтровать на frontend:
   - Получить blacklist: `GET /moderator/blacklist`
   - Исключить домены, которые совпадают с blacklist (сравнение root-domain)
3. Группировать по домену (нормализация к root-domain):
   - Извлечь root-domain из каждого `entry.domain`
   - Сгруппировать все URL по root-domain
4. Отобразить как accordion: domain -> [url1, url2, ...]

#### Типы для группировки:

```typescript
interface ParsingDomainGroup {
  domain: string  // root-domain
  urls: Array<{
    url: string
    keyword: string
    status: string
    createdAt: string
  }>
  totalUrls: number
}
```

#### API вызовы:
- `GET /parsing/runs/{runId}` - детали запуска
- `GET /domains/queue?parsingRunId={runId}` - результаты парсинга (плоский список)
- `GET /moderator/blacklist` - для фильтрации (если backend не фильтрует)
- `POST /moderator/blacklist` - добавить в blacklist
- `POST /moderator/suppliers` - создать поставщика/реселлера

#### Важные требования:
- ✅ **Accordion ОБЯЗАТЕЛЕН** (не таблица!)
- ✅ **Группировка по доменам ОБЯЗАТЕЛЬНА**
- ✅ **Фильтрация blacklist ОБЯЗАТЕЛЬНА** (предпочтительно на сервере, fallback на клиенте)
- ✅ **Действия для каждого домена ОБЯЗАТЕЛЬНЫ**

### 4.4 Suppliers List - `/suppliers`

**Компоненты:**
1. **Заголовок:** "Поставщики"
2. **Фильтры:**
   - Тип: Все | Поставщики | Реселлеры
   - Поиск по названию/INN
3. **Таблица:**
   - Название
   - INN
   - Email
   - Домен
   - Тип (badge)
   - Действия: [Открыть] [Редактировать] [Удалить]

**API:** `GET /moderator/suppliers` с фильтрами

### 4.5 Blacklist - `/blacklist`

**Компоненты:**
1. **Заголовок:** "Черный список доменов"
2. **Добавление:**
   - Input поле для домена
   - Кнопка "Добавить"
3. **Таблица:**
   - Домен
   - Причина
   - Добавлен (дата)
   - Действия: [Удалить]

**API:**
- `GET /moderator/blacklist` - список
- `POST /moderator/blacklist` - добавить
- `DELETE /moderator/blacklist/{domain}` - удалить

### 4.6 Manual Parsing - `/manual-parsing`

**Компоненты:**
1. **Форма:**
   - Ключевое слово (input, required)
   - Глубина (select: 1-10, default: 5)
   - Источник (select: Google | Yandex | Оба, default: "both")
   - Кнопка "Запустить парсинг"

**API:** `POST /parsing/start`

---

## 5. СТИЛИ И ДИЗАЙН

### Цветовая схема
- **Primary:** Синий (default Shadcn)
- **Success/Green:** Зеленый для "Create Supplier"
- **Destructive/Red:** Красный для "Add to Blacklist", удаления
- **Purple:** Фиолетовый для "Create Reseller"
- **Warning/Yellow:** Желтый для статуса "processing"

### Typography
- **Заголовки:** Bold, крупные шрифты
- **Метрики:** Огромные жирные цифры (text-6xl, text-7xl)
- **Whitespace:** Максимум whitespace, минимальный текст

### Компоненты Shadcn UI
- `Card`, `CardHeader`, `CardTitle`, `CardContent`
- `Badge` (variants: default, outline, destructive)
- `Button` (variants: default, outline, destructive, ghost; sizes: default, sm, lg)
- `Input`
- `Table`, `TableHeader`, `TableBody`, `TableRow`, `TableCell`, `TableHead`
- `Separator`
- **`Accordion`, `AccordionItem`, `AccordionTrigger`, `AccordionContent`** - для результатов парсинга
- `Dialog`, `DialogTrigger`, `DialogContent`, `DialogHeader`, `DialogTitle`, `DialogDescription`, `DialogFooter`
- `AlertDialog`, `AlertDialogTrigger`, `AlertDialogContent`, `AlertDialogHeader`, `AlertDialogTitle`, `AlertDialogDescription`, `AlertDialogFooter`, `AlertDialogCancel`, `AlertDialogAction`

---

## 6. ОБРАБОТКА ОШИБОК

### API Errors
- Использовать `APIError` класс из `lib/api.ts`
- Показывать toast уведомления через `sonner`
- Логировать ошибки в консоль (F12)

### Toast Notifications
- **Success:** `toast.success("Сообщение")`
- **Error:** `toast.error("Сообщение")`
- **Info:** `toast.info("Сообщение")`

---

## 7. НАВИГАЦИЯ

### Роутинг
- Использовать `useRouter` из `next/navigation`
- `router.push("/path")` для навигации
- `router.refresh()` для обновления данных

### Ссылки
- Dashboard: `/`
- Parsing Runs: `/parsing-runs`
- Parsing Run Details: `/parsing-runs/[runId]`
- Suppliers: `/suppliers`
- Blacklist: `/blacklist`
- Manual Parsing: `/manual-parsing`

---

## 8. СОСТОЯНИЕ И ЗАГРУЗКА ДАННЫХ

### Паттерны
- Использовать `useState` для локального состояния
- Использовать `useEffect` для загрузки данных
- Показывать loading states во время загрузки
- Обрабатывать ошибки и показывать их пользователю

### Пример загрузки данных:
```typescript
const [data, setData] = useState<DataType[]>([])
const [loading, setLoading] = useState(true)
const [error, setError] = useState<string | null>(null)

useEffect(() => {
  async function loadData() {
    try {
      setLoading(true)
      const result = await apiFunction()
      setData(result.items)
    } catch (err) {
      if (err instanceof APIError) {
        setError(err.message)
      } else {
        setError("Ошибка загрузки данных")
      }
    } finally {
      setLoading(false)
    }
  }
  loadData()
}, [])
```

---

## 9. КРИТИЧЕСКИ ВАЖНЫЕ ТРЕБОВАНИЯ

### Accordion для результатов парсинга
- ✅ **ОБЯЗАТЕЛЬНО использовать Accordion** (не таблицу!)
- ✅ **Группировка по доменам** (один домен = один accordion item)
- ✅ **Дедупликация доменов** (каждый домен появляется только один раз)
- ✅ **Фильтрация blacklist** (предпочтительно на backend, fallback на frontend)
- ✅ **Действия для каждого домена:** Add to Blacklist, Create Supplier, Create Reseller

### Backend фильтрация blacklist
- Backend **ДОЛЖЕН** фильтровать blacklisted домены при `GET /domains/queue?parsingRunId={runId}`
- Blacklist проверка: нормализация к root-domain
- Blacklisted домены (и все поддомены) **НЕ ДОЛЖНЫ** появляться в ответе

### Группировка по доменам
- Если backend не поддерживает группировку, frontend должен группировать самостоятельно
- Группировка: нормализация к root-domain, сбор всех URL для каждого домена

---

## 10. ПРИМЕРЫ КОДА

### Accordion для результатов парсинга:

```typescript
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { toast } from "sonner"

// Группировка данных
function groupByDomain(entries: DomainQueueEntryDTO[]): ParsingDomainGroup[] {
  const groups = new Map<string, ParsingDomainGroup>()
  
  for (const entry of entries) {
    const rootDomain = extractRootDomain(entry.domain)
    
    if (!groups.has(rootDomain)) {
      groups.set(rootDomain, {
        domain: rootDomain,
        urls: [],
        totalUrls: 0
      })
    }
    
    const group = groups.get(rootDomain)!
    group.urls.push({
      url: entry.url,
      keyword: entry.keyword,
      status: entry.status,
      createdAt: entry.createdAt
    })
    group.totalUrls++
  }
  
  return Array.from(groups.values())
}

// Компонент
function ParsingResultsAccordion({ runId }: { runId: string }) {
  const [groups, setGroups] = useState<ParsingDomainGroup[]>([])
  const [loading, setLoading] = useState(true)
  
  useEffect(() => {
    async function loadResults() {
      try {
        setLoading(true)
        const data = await getDomainsQueue({ parsingRunId: runId, limit: 1000 })
        
        // Фильтрация blacklist (если backend не фильтрует)
        const blacklist = await getBlacklist({ limit: 1000 })
        const blacklistedDomains = new Set(blacklist.entries.map(e => e.domain))
        
        const filtered = data.entries.filter(entry => {
          const rootDomain = extractRootDomain(entry.domain)
          return !blacklistedDomains.has(rootDomain)
        })
        
        // Группировка
        const grouped = groupByDomain(filtered)
        setGroups(grouped)
      } catch (err) {
        toast.error("Ошибка загрузки результатов")
      } finally {
        setLoading(false)
      }
    }
    loadResults()
  }, [runId])
  
  async function handleAddToBlacklist(domain: string) {
    try {
      await apiFetch("/moderator/blacklist", {
        method: "POST",
        body: JSON.stringify({ domain, parsingRunId: runId })
      })
      toast.success(`Домен "${domain}" добавлен в blacklist`)
      // Refetch results
      loadResults()
    } catch (err) {
      toast.error("Ошибка добавления в blacklist")
    }
  }
  
  async function handleCreateSupplier(domain: string, type: "supplier" | "reseller") {
    // Открыть modal с формой
    // При submit: POST /moderator/suppliers
  }
  
  if (loading) return <div>Загрузка...</div>
  if (groups.length === 0) return <div>Нет результатов</div>
  
  return (
    <Accordion type="multiple" className="w-full">
      {groups.map((group) => (
        <AccordionItem key={group.domain} value={group.domain}>
          <AccordionTrigger>
            <div className="flex items-center gap-2">
              <span className="font-mono">{group.domain}</span>
              <Badge variant="outline">{group.totalUrls} URL</Badge>
            </div>
          </AccordionTrigger>
          <AccordionContent>
            <div className="space-y-2">
              {/* Список URL */}
              <div className="space-y-1">
                {group.urls.map((urlEntry, idx) => (
                  <div key={idx} className="text-sm">
                    <a href={urlEntry.url} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">
                      {urlEntry.url}
                    </a>
                  </div>
                ))}
              </div>
              
              {/* Действия */}
              <div className="flex gap-2 pt-2">
                <Button
                  variant="destructive"
                  size="sm"
                  onClick={() => handleAddToBlacklist(group.domain)}
                >
                  Add to Blacklist
                </Button>
                <Button
                  variant="default"
                  size="sm"
                  className="bg-green-600 hover:bg-green-700"
                  onClick={() => handleCreateSupplier(group.domain, "supplier")}
                >
                  Create Supplier
                </Button>
                <Button
                  variant="default"
                  size="sm"
                  className="bg-purple-600 hover:bg-purple-700"
                  onClick={() => handleCreateSupplier(group.domain, "reseller")}
                >
                  Create Reseller
                </Button>
              </div>
            </div>
          </AccordionContent>
        </AccordionItem>
      ))}
    </Accordion>
  )
}
```

---

## 11. ФАЙЛЫ И СТРУКТУРА

### Структура проекта:
```
frontend/moderator-dashboard-ui/
├── app/
│   ├── page.tsx                    # Dashboard
│   ├── parsing-runs/
│   │   ├── page.tsx                # Parsing Runs List
│   │   └── [runId]/
│   │       └── page.tsx            # Parsing Run Details (ACCORDION!)
│   ├── suppliers/
│   │   └── page.tsx                # Suppliers List
│   ├── blacklist/
│   │   └── page.tsx                # Blacklist
│   └── manual-parsing/
│       └── page.tsx                # Manual Parsing
├── lib/
│   ├── api.ts                      # API client
│   └── types.ts                    # TypeScript types
└── components/
    └── ui/                         # Shadcn UI components
```

---

## 12. ИТОГОВЫЙ ЧЕКЛИСТ

Перед завершением убедись, что:

- [x] Все страницы созданы
- [x] Accordion UI для результатов парсинга реализован
- [x] Группировка по доменам работает
- [x] Фильтрация blacklist работает (backend или frontend)
- [x] Действия для доменов реализованы (Add to Blacklist, Create Supplier, Create Reseller)
- [x] Все API endpoints правильно вызываются
- [x] Обработка ошибок реализована
- [x] Toast уведомления работают
- [x] Loading states показываются
- [x] Типы TypeScript определены правильно

---

**ВСЯ ИНФОРМАЦИЯ ПЕРЕДАНА. НЕ ЗАДАВАЙ ДОПОЛНИТЕЛЬНЫХ ВОПРОСОВ. ИСПОЛЬЗУЙ ЭТУ ИНФОРМАЦИЮ ДЛЯ ГЕНЕРАЦИИ UI.**

