export default function HomePage() {
  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold">B2B Platform</h1>
        <p className="text-muted-foreground mt-2">
          Система модерации и парсинга поставщиков
        </p>
      </div>
      
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <div className="rounded-lg border p-6">
          <h3 className="font-semibold">Поставщики</h3>
          <p className="text-sm text-muted-foreground mt-2">
            Управление карточками поставщиков
          </p>
        </div>
        <div className="rounded-lg border p-6">
          <h3 className="font-semibold">Ключевые слова</h3>
          <p className="text-sm text-muted-foreground mt-2">
            Управление ключевыми словами для парсинга
          </p>
        </div>
        <div className="rounded-lg border p-6">
          <h3 className="font-semibold">Парсинг</h3>
          <p className="text-sm text-muted-foreground mt-2">
            Запуск и мониторинг парсинга
          </p>
        </div>
        <div className="rounded-lg border p-6">
          <h3 className="font-semibold">Черный список</h3>
          <p className="text-sm text-muted-foreground mt-2">
            Управление черным списком доменов
          </p>
        </div>
      </div>
    </div>
  )
}

