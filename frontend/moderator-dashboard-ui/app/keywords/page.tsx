"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Checkbox } from "@/components/ui/checkbox"
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion"
import { Navigation } from "@/components/navigation"
import { getKeywords, createKeyword, deleteKeyword, getDomainsQueue, getSuppliers, getBlacklist } from "@/lib/api"
import { extractRootDomain } from "@/lib/utils-domain"
import { getCachedSuppliers, setCachedSuppliers, getCachedBlacklist, setCachedBlacklist } from "@/lib/cache"
import { toast } from "sonner"
import { Plus, Trash2, ExternalLink, RefreshCw } from "lucide-react"
import type { KeywordDTO, DomainQueueEntryDTO } from "@/lib/types"

interface DomainGroup {
  rootDomain: string
  urls: DomainQueueEntryDTO[]
  supplierType?: "supplier" | "reseller" | null
  isBlacklisted: boolean
}

interface KeywordWithDomains extends KeywordDTO {
  domains: DomainGroup[]
  totalUrls: number
}

export default function KeywordsPage() {
  const [keywords, setKeywords] = useState<KeywordWithDomains[]>([])
  const [loading, setLoading] = useState(true)
  const [newKeyword, setNewKeyword] = useState("")
  const [addingKeyword, setAddingKeyword] = useState(false)
  const [expandedKeywords, setExpandedKeywords] = useState<Set<number>>(new Set())
  const [loadedUrls, setLoadedUrls] = useState<Map<number, DomainGroup[]>>(new Map())
  const [selectedKeywords, setSelectedKeywords] = useState<Set<number>>(new Set())

  useEffect(() => {
    loadKeywords()
    
    // Автоматическое обновление каждые 30 секунд
    const interval = setInterval(() => {
      loadKeywords()
    }, 30000)
    
    return () => clearInterval(interval)
  }, [])

  async function loadKeywords() {
    setLoading(true)
    try {
      // Всегда загружаем свежие данные blacklist (кэш может быть устаревшим после добавления)
      // Поставщики можно использовать из кэша
      let suppliersData: { suppliers: any[]; total: number; limit: number; offset: number }
      let blacklistData: { entries: any[]; total: number; limit: number; offset: number }
      
      const cachedSuppliers = getCachedSuppliers()
      
      if (cachedSuppliers) {
        // Используем кэш для поставщиков
        suppliersData = {
          suppliers: cachedSuppliers,
          total: cachedSuppliers.length,
          limit: 1000,
          offset: 0,
        }
      } else {
        // Загружаем поставщиков и кэшируем
        const suppliersResult = await getSuppliers({ limit: 1000 })
        suppliersData = suppliersResult
        setCachedSuppliers(suppliersData.suppliers)
      }
      
      // Всегда загружаем свежие данные blacklist (чтобы видеть актуальный список после добавления)
      const blacklistResult = await getBlacklist({ limit: 1000 })
      blacklistData = blacklistResult
      // Обновляем кэш blacklist свежими данными
      setCachedBlacklist(blacklistData.entries)
      
      const keywordsData = await getKeywords()

      // Создать Map для быстрого поиска поставщиков и blacklist по домену
      const suppliersMap = new Map<string, "supplier" | "reseller">()
      suppliersData.suppliers.forEach((supplier) => {
        if (supplier.domain) {
          const rootDomain = extractRootDomain(supplier.domain).toLowerCase()
          suppliersMap.set(rootDomain, supplier.type)
        }
      })

      const blacklistedDomains = new Set(
        blacklistData.entries.map((e) => extractRootDomain(e.domain).toLowerCase())
      )

      // Загружаем только базовую информацию о ключах (без URL)
      // URL будут загружаться лениво при раскрытии accordion
      const keywordsWithDomains = keywordsData.keywords.map((keyword) => ({
        ...keyword,
        domains: [],
        totalUrls: 0,
      }))

      setKeywords(keywordsWithDomains)
      
      // Очищаем кэш загруженных URL, чтобы перезагрузить их с учетом нового blacklist
      setLoadedUrls(new Map())
      
      // Перезагружаем URL для всех раскрытых ключей с учетом нового blacklist
      const expandedKeywordsList = Array.from(expandedKeywords)
      for (const keywordId of expandedKeywordsList) {
        const keyword = keywordsWithDomains.find(k => k.id === keywordId)
        if (keyword) {
          // Принудительно перезагружаем URL с учетом нового blacklist
          loadUrlsForKeyword(keywordId, keyword.keyword, true).catch(err => {
            console.error(`Error reloading URLs for keyword ${keyword.keyword}:`, err)
          })
        }
      }
    } catch (error) {
      toast.error("Ошибка загрузки ключевых слов")
      console.error("Error loading keywords:", error)
    } finally {
      setLoading(false)
    }
  }

  // Показываем все ключи без пагинации
  const paginatedKeywords = keywords

  async function handleAdd() {
    if (!newKeyword.trim()) {
      toast.error("Введите ключевое слово")
      return
    }

    setAddingKeyword(true)
    try {
      await createKeyword(newKeyword.trim())
      toast.success(`Ключевое слово "${newKeyword}" добавлено`)
      setNewKeyword("")
      loadKeywords()
    } catch (error) {
      toast.error("Ошибка добавления ключевого слова")
      console.error("Error adding keyword:", error)
    } finally {
      setAddingKeyword(false)
    }
  }

  async function handleDelete(id: number, keyword: string) {
    if (!confirm(`Удалить ключевое слово "${keyword}"?`)) return

    try {
      await deleteKeyword(id)
      toast.success(`Ключевое слово "${keyword}" удалено`)
      loadKeywords()
    } catch (error) {
      toast.error("Ошибка удаления ключевого слова")
      console.error("Error deleting keyword:", error)
    }
  }

  async function loadUrlsForKeyword(keywordId: number, keywordText: string, forceReload: boolean = false) {
    // Проверяем, не загружены ли уже URL для этого ключа (если не принудительная перезагрузка)
    if (!forceReload && loadedUrls.has(keywordId)) {
      return
    }

    try {
      const domainsData = await getDomainsQueue({ keyword: keywordText, limit: 1000 })

      // Получаем актуальные данные поставщиков и blacklist
      // ВАЖНО: Всегда загружаем свежий blacklist, чтобы видеть актуальный список после добавления
      const cachedSuppliers = getCachedSuppliers()

      const suppliersMap = new Map<string, "supplier" | "reseller">()
      if (cachedSuppliers) {
        cachedSuppliers.forEach((supplier) => {
          if (supplier.domain) {
            const rootDomain = extractRootDomain(supplier.domain).toLowerCase()
            suppliersMap.set(rootDomain, supplier.type)
          }
        })
      }

      // Всегда загружаем свежий blacklist (не из кэша) для актуальности
      const blacklistResult = await getBlacklist({ limit: 1000 })
      setCachedBlacklist(blacklistResult.entries) // Обновляем кэш свежими данными
      
      const blacklistedDomains = new Set<string>()
      blacklistResult.entries.forEach((e) => {
        blacklistedDomains.add(extractRootDomain(e.domain).toLowerCase())
      })

      // ФИЛЬТРАЦИЯ BLACKLIST: Исключаем домены из blacklist из результатов
      const filteredEntries = domainsData.entries.filter((urlEntry) => {
        const rootDomain = extractRootDomain(urlEntry.domain).toLowerCase()
        return !blacklistedDomains.has(rootDomain)
      })

      // Группируем URL по root domain (только не blacklisted)
      const domainGroupsMap = new Map<string, DomainGroup>()
      filteredEntries.forEach((urlEntry) => {
        const rootDomain = extractRootDomain(urlEntry.domain).toLowerCase()
        if (!domainGroupsMap.has(rootDomain)) {
          domainGroupsMap.set(rootDomain, {
            rootDomain,
            urls: [],
            supplierType: suppliersMap.get(rootDomain) || null,
            isBlacklisted: false, // Уже отфильтрованы, поэтому всегда false
          })
        }
        domainGroupsMap.get(rootDomain)!.urls.push(urlEntry)
      })

      const domains = Array.from(domainGroupsMap.values())
      const totalUrls = domains.reduce((sum, d) => sum + d.urls.length, 0)

      // Сохраняем загруженные URL
      setLoadedUrls((prev) => new Map(prev).set(keywordId, domains))

      // Обновляем ключ в списке
      setKeywords((prev) =>
        prev.map((k) =>
          k.id === keywordId
            ? {
                ...k,
                domains,
                totalUrls,
              }
            : k
        )
      )
    } catch (error) {
      console.error(`Error loading URLs for keyword ${keywordText}:`, error)
      toast.error(`Ошибка загрузки URL для ключа "${keywordText}"`)
    }
  }

  function handleAccordionChange(keywordId: number, keywordText: string, isOpen: boolean) {
    if (isOpen) {
      setExpandedKeywords((prev) => new Set(prev).add(keywordId))
      // Загружаем URL при раскрытии
      loadUrlsForKeyword(keywordId, keywordText)
    } else {
      setExpandedKeywords((prev) => {
        const newSet = new Set(prev)
        newSet.delete(keywordId)
        return newSet
      })
    }
  }

  function toggleSelectKeyword(keywordId: number) {
    const newSelected = new Set(selectedKeywords)
    if (newSelected.has(keywordId)) {
      newSelected.delete(keywordId)
    } else {
      newSelected.add(keywordId)
    }
    setSelectedKeywords(newSelected)
  }

  function toggleSelectAll() {
    if (selectedKeywords.size === paginatedKeywords.length) {
      setSelectedKeywords(new Set())
    } else {
      const allKeywordIds = paginatedKeywords.map((k) => k.id)
      setSelectedKeywords(new Set(allKeywordIds))
    }
  }

  async function handleBulkDelete() {
    if (selectedKeywords.size === 0) return
    if (!confirm(`Удалить ${selectedKeywords.size} ключевых слов?`)) return

    try {
      const keywordIds = Array.from(selectedKeywords)
      for (const keywordId of keywordIds) {
        await deleteKeyword(keywordId)
      }
      toast.success(`Удалено ${keywordIds.length} ключевых слов`)
      setSelectedKeywords(new Set())
      loadKeywords()
    } catch (error) {
      toast.error("Ошибка массового удаления")
      console.error("Error bulk deleting keywords:", error)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-background">
        <Navigation />
        <main className="container mx-auto px-6 py-6">
          <div className="text-center text-muted-foreground">Загрузка...</div>
        </main>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-background">
      <Navigation />

      <main className="container mx-auto px-6 py-6 max-w-7xl">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <h1 className="text-4xl font-bold">Ключи</h1>
            {keywords.length > 0 && (
              <Badge variant="outline" className="text-sm">
                Всего: {keywords.length}
              </Badge>
            )}
          </div>
          <Button variant="outline" onClick={loadKeywords} disabled={loading}>
            <RefreshCw className={`mr-2 h-4 w-4 ${loading ? "animate-spin" : ""}`} />
            Обновить
          </Button>
        </div>

        {/* Добавление нового ключа */}
        <Card className="mb-4">
          <CardHeader>
            <CardTitle>Добавить ключевое слово</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex gap-2">
              <Input
                placeholder="Введите ключевое слово..."
                value={newKeyword}
                onChange={(e) => setNewKeyword(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleAdd()}
                className="flex-1"
              />
              <Button onClick={handleAdd} disabled={addingKeyword}>
                <Plus className="mr-2 h-4 w-4" />
                Добавить
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Список ключей с доменами */}
        {keywords.length === 0 ? (
          <Card>
            <CardContent className="py-12 text-center text-muted-foreground">
              Ключевые слова не найдены
            </CardContent>
          </Card>
        ) : (
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>
                  Все ключи ({keywords.length})
                </CardTitle>
                <div className="flex items-center gap-2">
                  <Checkbox
                    checked={selectedKeywords.size === paginatedKeywords.length && paginatedKeywords.length > 0}
                    onCheckedChange={toggleSelectAll}
                  />
                  <span className="text-sm text-muted-foreground">Выделить все</span>
                </div>
              </div>
              {selectedKeywords.size > 0 && (
                <div className="mt-1 flex items-center justify-between bg-muted/50 p-1 rounded-md">
                  <span className="text-sm text-muted-foreground">
                    Выбрано: {selectedKeywords.size}
                  </span>
                  <Button variant="destructive" size="sm" onClick={handleBulkDelete}>
                    <Trash2 className="mr-2 h-4 w-4" />
                    Удалить выбранные
                  </Button>
                </div>
              )}
            </CardHeader>
            <CardContent>
              <Accordion
                type="multiple"
                className="w-full"
                onValueChange={(values) => {
                  paginatedKeywords.forEach((keyword) => {
                    const isOpen = values.includes(`keyword-${keyword.id}`)
                    handleAccordionChange(keyword.id, keyword.keyword, isOpen)
                  })
                }}
              >
                {paginatedKeywords.map((keyword) => {
                  const isSelected = selectedKeywords.has(keyword.id)
                  return (
                    <AccordionItem key={keyword.id} value={`keyword-${keyword.id}`}>
                      <div className="flex items-center">
                        <div className="flex items-center gap-1 px-1 flex-shrink-0" onClick={(e) => e.stopPropagation()}>
                          <Checkbox
                            checked={isSelected}
                            onCheckedChange={() => toggleSelectKeyword(keyword.id)}
                            onClick={(e) => e.stopPropagation()}
                          />
                        </div>
                        <AccordionTrigger className="hover:no-underline flex-1 py-1">
                          <div className="flex items-center gap-1 flex-1">
                            <span className="font-semibold text-base">{keyword.keyword}</span>
                            <Badge variant="outline" className="text-xs">{keyword.totalUrls} URL</Badge>
                            <Badge variant="outline" className="text-xs">{keyword.domains.length} доменов</Badge>
                            <span className="text-xs text-muted-foreground ml-auto">
                              {new Date(keyword.createdAt).toLocaleDateString("ru-RU")}
                            </span>
                          </div>
                        </AccordionTrigger>
                      </div>
                      <AccordionContent className="pb-1 pt-0">
                        <div>
                          {keyword.domains.length === 0 ? (
                            <div className="text-sm text-muted-foreground py-1">
                              Домены не найдены для этого ключа
                            </div>
                          ) : (
                            <Accordion type="multiple" className="w-full">
                              {keyword.domains.map((domainGroup) => (
                                <AccordionItem
                                  key={domainGroup.rootDomain}
                                  value={`domain-${keyword.id}-${domainGroup.rootDomain}`}
                                >
                                  <AccordionTrigger className="hover:no-underline py-1">
                                    <div className="flex items-center gap-1 flex-1">
                                      <span className="font-mono font-semibold text-sm">
                                        {domainGroup.rootDomain}
                                      </span>
                                      <Badge variant="outline" className="text-xs">{domainGroup.urls.length} URL</Badge>
                                      {domainGroup.supplierType === "supplier" && (
                                        <Badge className="bg-green-600 hover:bg-green-700 text-white text-xs">
                                          Поставщик
                                        </Badge>
                                      )}
                                      {domainGroup.supplierType === "reseller" && (
                                        <Badge className="bg-purple-600 hover:bg-purple-700 text-white text-xs">
                                          Реселлер
                                        </Badge>
                                      )}
                                    </div>
                                  </AccordionTrigger>
                                  <AccordionContent className="pb-1 pt-0">
                                    <div className="max-h-60 overflow-y-auto">
                                      {domainGroup.urls.map((urlEntry, idx) => (
                                        <div
                                          key={idx}
                                          className="text-sm flex items-center gap-1 hover:bg-accent/50 p-1 rounded"
                                        >
                                          <a
                                            href={urlEntry.url}
                                            target="_blank"
                                            rel="noopener noreferrer"
                                            className="text-blue-600 hover:underline flex-1 flex items-center gap-1"
                                          >
                                            <span className="font-mono text-xs">{urlEntry.domain}</span>
                                            <span className="text-muted-foreground">→</span>
                                            <span className="truncate">{urlEntry.url}</span>
                                            <ExternalLink className="h-3 w-3 flex-shrink-0" />
                                          </a>
                                          {urlEntry.parsingRunId && (
                                            <Badge variant="outline" className="text-xs">
                                              Run: {urlEntry.parsingRunId.slice(0, 8)}
                                            </Badge>
                                          )}
                                        </div>
                                      ))}
                                    </div>
                                  </AccordionContent>
                                </AccordionItem>
                              ))}
                            </Accordion>
                          )}

                          {/* Действия */}
                          <div className="flex gap-1 pt-1 border-t mt-1">
                            <Button
                              variant="destructive"
                              size="sm"
                              className="h-7 text-xs"
                              onClick={() => handleDelete(keyword.id, keyword.keyword)}
                            >
                              <Trash2 className="mr-2 h-3 w-3" />
                              Удалить ключ
                            </Button>
                          </div>
                        </div>
                      </AccordionContent>
                    </AccordionItem>
                  )
                })}
              </Accordion>
            </CardContent>
          </Card>
        )}
      </main>
    </div>
  )
}
