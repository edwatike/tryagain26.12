"use client"

import { useState, useEffect, use } from "react"
import { useRouter } from "next/navigation"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Navigation } from "@/components/navigation"
import { CheckoInfoDialog } from "@/components/checko-info-dialog"
import { getParsingRun, getDomainsQueue, getBlacklist, addToBlacklist, createSupplier, updateSupplier, getSuppliers, getParsingLogs, APIError } from "@/lib/api"
import { groupByDomain, extractRootDomain, collectDomainSources, normalizeUrl } from "@/lib/utils-domain"
import { getCachedSuppliers, setCachedSuppliers, getCachedBlacklist, setCachedBlacklist, invalidateSuppliersCache, invalidateBlacklistCache } from "@/lib/cache"
import { toast } from "sonner"
import { ExternalLink } from "lucide-react"
import type { ParsingDomainGroup, ParsingRunDTO } from "@/lib/types"

export default function ParsingRunDetailsPage({ params }: { params: Promise<{ runId: string }> }) {
  const router = useRouter()
  const resolvedParams = use(params)
  const runId = resolvedParams.runId
  const [run, setRun] = useState<ParsingRunDTO | null>(null)
  const [groups, setGroups] = useState<ParsingDomainGroup[]>([])
  const [loading, setLoading] = useState(true)
  const [refreshKey, setRefreshKey] = useState(0) // Ключ для принудительного обновления
  const [supplierDialogOpen, setSupplierDialogOpen] = useState(false)
  const [selectedDomain, setSelectedDomain] = useState("")
  const [editingSupplierId, setEditingSupplierId] = useState<number | null>(null) // ID существующего поставщика для редактирования
  const [supplierForm, setSupplierForm] = useState({
    name: "",
    inn: "",
    email: "",
    domain: "",
    address: "",
    type: "supplier" as "supplier" | "reseller",
    // Checko fields
    ogrn: "",
    kpp: "",
    okpo: "",
    companyStatus: "",
    registrationDate: "",
    legalAddress: "",
    phone: "",
    website: "",
    vk: "",
    telegram: "",
    authorizedCapital: null as number | null,
    revenue: null as number | null,
    profit: null as number | null,
    financeYear: null as number | null,
    legalCasesCount: null as number | null,
    legalCasesSum: null as number | null,
    legalCasesAsPlaintiff: null as number | null,
    legalCasesAsDefendant: null as number | null,
    checkoData: null as string | null,
  })
  const [searchQuery, setSearchQuery] = useState("")
  const [sortBy, setSortBy] = useState<"domain" | "urls">("urls")
  const [filterStatus, setFilterStatus] = useState<"all" | "supplier" | "reseller" | "new">("all")
  const [parsingLogs, setParsingLogs] = useState<{
    google?: { total_links: number; pages_processed: number; last_links: string[]; links_by_page?: Record<number, number> }
    yandex?: { total_links: number; pages_processed: number; last_links: string[]; links_by_page?: Record<number, number> }
  } | null>(null)
  const [accordionValue, setAccordionValue] = useState<string[]>([]) // Состояние аккордеона для логов парсинга
  
  // Функция для определения источников URL на основе parsing_logs и source из БД
  // Используем parsing_logs как основной источник, но fallback на source из БД
  const getUrlSources = (url: string, urlSource?: string | null): string[] => {
    const normalizedUrl = normalizeUrl(url)
    const sources: string[] = []
    
    // Используем parsing_logs как основной источник информации
    if (parsingLogs) {
      // Проверяем Google
      if (parsingLogs.google?.last_links) {
        const foundInGoogle = parsingLogs.google.last_links.some(link => 
          normalizeUrl(link) === normalizedUrl
        )
        if (foundInGoogle) {
          sources.push("google")
        }
      }
      
      // Проверяем Yandex
      if (parsingLogs.yandex?.last_links) {
        const foundInYandex = parsingLogs.yandex.last_links.some(link => 
          normalizeUrl(link) === normalizedUrl
        )
        if (foundInYandex) {
          sources.push("yandex")
        }
      }
    }
    
    // Fallback: если не нашли в parsing_logs, используем source из domains_queue
    // Это важно, так как parsing_logs может содержать не все URL
    if (sources.length === 0 && urlSource) {
      if (urlSource === "both") {
        sources.push("google", "yandex")
      } else if (urlSource === "google") {
        sources.push("google")
      } else if (urlSource === "yandex") {
        sources.push("yandex")
      }
    }
    
    return sources
  }

  useEffect(() => {
    if (runId) {
      loadData()
    }
  }, [runId, refreshKey]) // Добавляем refreshKey для принудительной перезагрузки

  // Загрузка логов парсера (один раз при загрузке run, даже если парсинг завершен)
  useEffect(() => {
    if (!runId || !run) return

    const fetchLogs = async () => {
      try {
        const logsData = await getParsingLogs(runId)
        if (logsData.parsing_logs && Object.keys(logsData.parsing_logs).length > 0) {
          setParsingLogs(logsData.parsing_logs)
        } else {
          // Если логов нет, очищаем состояние (на случай, если они были удалены)
          setParsingLogs(null)
        }
      } catch (error: unknown) {
        // Игнорируем ошибки 404, если run еще не создан в БД или логов еще нет
        // Это нормальная ситуация сразу после запуска парсинга
        if (error instanceof APIError && error.status === 404) {
          // Run не найден - это может быть временная ситуация, не показываем ошибку
          // Просто возвращаемся, не логируя ошибку
          return
        }
        // Для других ошибок используем debug, чтобы не засорять консоль
        // Но не показываем их как ошибки, так как это может быть временная ситуация
        console.debug("Could not fetch parsing logs:", error)
      }
    }

    // Загружаем логи один раз при загрузке run (для завершенных парсингов)
    // И при изменении статуса (когда парсинг завершается)
    fetchLogs()
  }, [runId, run?.status]) // Загружаем при изменении статуса

  // Polling для получения логов парсера в реальном времени (только во время парсинга)
  useEffect(() => {
    if (!runId) return
    
    // Не пытаемся получать логи, пока run не загружен
    if (!run) {
      return
    }
    
    // Если парсинг завершен, не нужно polling
    if (run.status === "completed" || run.status === "failed") {
      return
    }

    const fetchLogs = async () => {
      try {
        const logsData = await getParsingLogs(runId)
        if (logsData.parsing_logs && Object.keys(logsData.parsing_logs).length > 0) {
          setParsingLogs(logsData.parsing_logs)
        }
      } catch (error: unknown) {
        // Игнорируем ошибки 404, если run еще не создан в БД или логов еще нет
        // Это нормальная ситуация сразу после запуска парсинга
        if (error instanceof APIError && error.status === 404) {
          // Run не найден - это может быть временная ситуация, не показываем ошибку
          // Просто возвращаемся, не логируя ошибку
          return
        }
        // Для других ошибок используем debug, чтобы не засорять консоль
        // Но не показываем их как ошибки, так как это может быть временная ситуация
        console.debug("Could not fetch parsing logs:", error)
      }
    }

    // Загружаем логи сразу, если run существует и выполняется
    if (run.status === "running") {
      fetchLogs()
    }

    // Polling каждые 2 секунды, если парсинг выполняется
    const intervalId = setInterval(() => {
      if (run.status === "running") {
        fetchLogs()
      }
    }, 2000)

    return () => clearInterval(intervalId)
  }, [runId, run])

  // УБРАНО: Сортировка теперь применяется в loadData() после фильтрации
  // Это предотвращает конфликты с обновлением данных после добавления в blacklist

  async function loadData() {
    if (!runId) return
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
      
      const [runData, domainsData, logsData] = await Promise.all([
        getParsingRun(runId),
        getDomainsQueue({ parsingRunId: runId, limit: 1000 }),
        getParsingLogs(runId).catch(() => ({ parsing_logs: {} })), // Загружаем логи вместе с данными
      ])

      setRun(runData)
      
      // Загружаем логи сразу при загрузке данных (даже если парсинг завершен)
      if (logsData.parsing_logs && Object.keys(logsData.parsing_logs).length > 0) {
        setParsingLogs(logsData.parsing_logs)
      }

      // Фильтрация blacklist - нормализуем домены для сравнения
      const blacklistedDomains = new Set(
        blacklistData.entries.map((e) => extractRootDomain(e.domain).toLowerCase())
      )
      const filtered = domainsData.entries.filter((entry) => {
        const rootDomain = extractRootDomain(entry.domain).toLowerCase()
        return !blacklistedDomains.has(rootDomain)
      })

      // Создать Map для быстрого поиска поставщиков по домену
      // ВАЖНО: Используем toLowerCase для обоих доменов для корректного сопоставления
      const suppliersMap = new Map<string, { type: "supplier" | "reseller"; id: number }>()
      suppliersData.suppliers.forEach((supplier) => {
        if (supplier.domain) {
          const rootDomain = extractRootDomain(supplier.domain).toLowerCase()
          suppliersMap.set(rootDomain, { type: supplier.type, id: supplier.id })
        }
      })

      // Группировка с добавлением информации о поставщиках и источниках
      // Используем parsing_logs для точного определения источников каждого домена
      const parsingLogsForSources = logsData.parsing_logs && Object.keys(logsData.parsing_logs).length > 0 
        ? logsData.parsing_logs 
        : null
      
      let grouped = groupByDomain(filtered).map((group) => {
        const groupDomainLower = group.domain.toLowerCase()
        const supplierInfo = suppliersMap.get(groupDomainLower)
        
        // Вычисляем источники для домена на основе всех его URL используя parsing_logs
        const sources = collectDomainSources(group.urls, parsingLogsForSources)
        
        return {
          ...group,
          supplierType: supplierInfo?.type || null,
          supplierId: supplierInfo?.id || null, // ID поставщика для редактирования
          sources: sources, // Источники, которые нашли этот домен
        }
      })

      // Сортировка
      grouped = grouped.sort((a, b) => {
        if (sortBy === "urls") {
          return b.totalUrls - a.totalUrls // По убыванию количества URL
        } else {
          return a.domain.localeCompare(b.domain) // По алфавиту
        }
      })

      setGroups(grouped)
    } catch (error) {
      toast.error("Ошибка загрузки данных")
      console.error("Error loading data:", error)
    } finally {
      setLoading(false)
    }
  }

  async function handleAddToBlacklist(domain: string) {
    if (!confirm(`Добавить "${domain}" в blacklist?`)) return

    try {
      // НОРМАЛИЗАЦИЯ: Используем extractRootDomain для нормализации домена
      // Это гарантирует, что домен будет добавлен в том же формате, что используется при фильтрации
      const normalizedDomain = extractRootDomain(domain)
      await addToBlacklist({ domain: normalizedDomain, parsingRunId: runId || undefined })
      // Инвалидируем кэш blacklist ПЕРЕД перезагрузкой данных
      invalidateBlacklistCache()
      toast.success(`Домен "${normalizedDomain}" добавлен в blacklist`)
      // Увеличиваем задержку, чтобы backend успел закоммитить изменения
      await new Promise(resolve => setTimeout(resolve, 500))
      // Принудительно перезагружаем данные (await чтобы дождаться завершения)
      // Устанавливаем loading в true, чтобы показать индикатор загрузки
      setLoading(true)
      // Принудительно обновляем ключ для перезагрузки
      setRefreshKey(prev => prev + 1)
      await loadData()
    } catch (error) {
      toast.error("Ошибка добавления в blacklist")
      console.error("Error adding to blacklist:", error)
      setLoading(false)
    }
  }

  function openSupplierDialog(domain: string, type: "supplier" | "reseller", supplierId?: number | null) {
    setSelectedDomain(domain)
    setEditingSupplierId(supplierId || null)
    
    // Если редактируем существующего поставщика, загружаем его данные
    if (supplierId) {
      // Находим поставщика в кэше
      const cachedSuppliers = getCachedSuppliers()
      const supplier = cachedSuppliers?.find(s => s.id === supplierId)
      if (supplier) {
        setSupplierForm({
          name: supplier.name || "",
          inn: supplier.inn || "",
          email: supplier.email || "",
          domain: supplier.domain || domain,
          address: supplier.address || "",
          type: supplier.type || type,
          // Checko fields
          ogrn: supplier.ogrn || "",
          kpp: supplier.kpp || "",
          okpo: supplier.okpo || "",
          companyStatus: supplier.companyStatus || "",
          registrationDate: supplier.registrationDate || "",
          legalAddress: supplier.legalAddress || "",
          phone: supplier.phone || "",
          website: supplier.website || "",
          vk: supplier.vk || "",
          telegram: supplier.telegram || "",
          authorizedCapital: supplier.authorizedCapital ?? null,
          revenue: supplier.revenue ?? null,
          profit: supplier.profit ?? null,
          financeYear: supplier.financeYear ?? null,
          legalCasesCount: supplier.legalCasesCount ?? null,
          legalCasesSum: supplier.legalCasesSum ?? null,
          legalCasesAsPlaintiff: supplier.legalCasesAsPlaintiff ?? null,
          legalCasesAsDefendant: supplier.legalCasesAsDefendant ?? null,
          checkoData: supplier.checkoData ?? null,
        })
      } else {
        setSupplierForm({
          name: "",
          inn: "",
          email: "",
          domain: domain,
          address: "",
          type: type,
          // Checko fields
          ogrn: "",
          kpp: "",
          okpo: "",
          companyStatus: "",
          registrationDate: "",
          legalAddress: "",
          phone: "",
          website: "",
          vk: "",
          telegram: "",
          authorizedCapital: null,
          revenue: null,
          profit: null,
          financeYear: null,
          legalCasesCount: null,
          legalCasesSum: null,
          legalCasesAsPlaintiff: null,
          legalCasesAsDefendant: null,
          checkoData: null,
        })
      }
    } else {
      setSupplierForm({
        name: "",
        inn: "",
        email: "",
        domain: domain,
        address: "",
        type: type,
        // Checko fields
        ogrn: "",
        kpp: "",
        okpo: "",
        companyStatus: "",
        registrationDate: "",
        legalAddress: "",
        phone: "",
        website: "",
        vk: "",
        telegram: "",
        authorizedCapital: null,
        revenue: null,
        profit: null,
        financeYear: null,
        legalCasesCount: null,
        legalCasesSum: null,
        legalCasesAsPlaintiff: null,
        legalCasesAsDefendant: null,
        checkoData: null,
      })
    }
    setSupplierDialogOpen(true)
  }

  function openEditSupplierDialog(domain: string, supplierId: number, currentType: "supplier" | "reseller") {
    openSupplierDialog(domain, currentType, supplierId)
  }

  async function handleCreateSupplier() {
    if (!supplierForm.name.trim()) {
      toast.error("Укажите название")
      return
    }

    try {
      if (editingSupplierId) {
        // Обновляем существующего поставщика
        await updateSupplier(editingSupplierId, {
          name: supplierForm.name,
          inn: supplierForm.inn || null,
          email: supplierForm.email || null,
          domain: supplierForm.domain || null,
          address: supplierForm.address || null,
          type: supplierForm.type,
          // Checko fields
          ogrn: supplierForm.ogrn || null,
          kpp: supplierForm.kpp || null,
          okpo: supplierForm.okpo || null,
          companyStatus: supplierForm.companyStatus || null,
          registrationDate: supplierForm.registrationDate || null,
          legalAddress: supplierForm.legalAddress || null,
          phone: supplierForm.phone || null,
          website: supplierForm.website || null,
          vk: supplierForm.vk || null,
          telegram: supplierForm.telegram || null,
          authorizedCapital: supplierForm.authorizedCapital,
          revenue: supplierForm.revenue,
          profit: supplierForm.profit,
          financeYear: supplierForm.financeYear,
          legalCasesCount: supplierForm.legalCasesCount,
          legalCasesSum: supplierForm.legalCasesSum,
          legalCasesAsPlaintiff: supplierForm.legalCasesAsPlaintiff,
          legalCasesAsDefendant: supplierForm.legalCasesAsDefendant,
          checkoData: supplierForm.checkoData,
        })
        toast.success(`${supplierForm.type === "supplier" ? "Поставщик" : "Реселлер"} обновлен`)
      } else {
        // Создаем нового поставщика
        await createSupplier({
          name: supplierForm.name,
          inn: supplierForm.inn || null,
          email: supplierForm.email || null,
          domain: supplierForm.domain || null,
          address: supplierForm.address || null,
          type: supplierForm.type,
          // Checko fields
          ogrn: supplierForm.ogrn || null,
          kpp: supplierForm.kpp || null,
          okpo: supplierForm.okpo || null,
          companyStatus: supplierForm.companyStatus || null,
          registrationDate: supplierForm.registrationDate || null,
          legalAddress: supplierForm.legalAddress || null,
          phone: supplierForm.phone || null,
          website: supplierForm.website || null,
          vk: supplierForm.vk || null,
          telegram: supplierForm.telegram || null,
          authorizedCapital: supplierForm.authorizedCapital,
          revenue: supplierForm.revenue,
          profit: supplierForm.profit,
          financeYear: supplierForm.financeYear,
          legalCasesCount: supplierForm.legalCasesCount,
          legalCasesSum: supplierForm.legalCasesSum,
          legalCasesAsPlaintiff: supplierForm.legalCasesAsPlaintiff,
          legalCasesAsDefendant: supplierForm.legalCasesAsDefendant,
          checkoData: supplierForm.checkoData,
        })
        toast.success(`${supplierForm.type === "supplier" ? "Поставщик" : "Реселлер"} создан`)
      }
      // Инвалидируем кэш поставщиков
      invalidateSuppliersCache()
      setSupplierDialogOpen(false)
      setEditingSupplierId(null)
      // Обновить данные, чтобы сразу показать бейдж
      loadData()
    } catch (error) {
      toast.error(editingSupplierId ? "Ошибка обновления" : "Ошибка создания")
      console.error("Error saving supplier:", error)
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

  if (!run) {
    return (
      <div className="min-h-screen bg-background">
        <Navigation />
        <main className="container mx-auto px-6 py-6">
          <div className="text-center text-muted-foreground">Запуск не найден</div>
        </main>
      </div>
    )
  }

  function getStatusBadge(status: string) {
    if (status === "completed")
      return (
        <Badge variant="default" className="text-lg px-4 py-1">
          Завершен
        </Badge>
      )
    if (status === "running")
      return (
        <Badge variant="outline" className="text-lg px-4 py-1">
          Выполняется
        </Badge>
      )
    return (
      <Badge variant="destructive" className="text-lg px-4 py-1">
        Ошибка
      </Badge>
    )
  }

  const displayRunId = run.runId || run.run_id || runId
  const keyword = run.keyword || "Unknown"
  const depth = run.depth || null
  const createdAt = run.createdAt || run.created_at || ""
  const finishedAt = run.finishedAt || run.finished_at

  // Функция для форматирования дат
  const formatDate = (dateString: string | null | undefined) => {
    if (!dateString) return "—"
    try {
      const date = new Date(dateString)
      // Используем UTC для правильного отображения
      return date.toLocaleString("ru-RU", {
        timeZone: "UTC",
        year: "numeric",
        month: "2-digit",
        day: "2-digit",
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
      })
    } catch (e) {
      return dateString
    }
  }

  return (
    <div className="min-h-screen bg-background">
      <Navigation />

      <main className="container mx-auto px-6 py-6 max-w-7xl">
        {/* Summary */}
        <Card className="mb-4">
          <CardHeader className="p-3">
            <div className="flex items-start justify-between">
              <div>
                <CardTitle className="text-lg mb-1">{keyword}</CardTitle>
                <div className="flex items-center gap-2 text-xs text-muted-foreground flex-wrap">
                  <span>Создан: {formatDate(createdAt)}</span>
                  {finishedAt && <span>Завершен: {formatDate(finishedAt)}</span>}
                  {depth !== null && depth !== undefined && <span>Глубина: {depth}</span>}
                </div>
              </div>
              {getStatusBadge(run.status)}
            </div>
          </CardHeader>
          {run.resultsCount !== null && run.resultsCount !== undefined && (
            <CardContent className="p-3 pt-0">
              <div className="text-xl font-bold">{run.resultsCount}</div>
              <div className="text-xs text-muted-foreground">результатов найдено</div>
            </CardContent>
          )}
        </Card>

        {/* Results Accordion */}
        <Card className="border-2 border-primary/20 shadow-lg">
          <CardHeader className="border-b">
            <div className="flex items-center justify-between mb-2">
              <CardTitle>Результаты парсинга</CardTitle>
            </div>
            {/* Фильтры и поиск */}
            <div className="flex gap-2 flex-wrap">
              <Input
                placeholder="Поиск по домену..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="flex-1 min-w-[200px]"
              />
              <Select value={sortBy} onValueChange={(value: "domain" | "urls") => setSortBy(value)}>
                <SelectTrigger className="w-[180px]">
                  <SelectValue placeholder="Сортировка" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="urls">По количеству URL</SelectItem>
                  <SelectItem value="domain">По алфавиту</SelectItem>
                </SelectContent>
              </Select>
              <Select value={filterStatus} onValueChange={(value: "all" | "supplier" | "reseller" | "new") => setFilterStatus(value)}>
                <SelectTrigger className="w-[180px]">
                  <SelectValue placeholder="Фильтр" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Все домены</SelectItem>
                  <SelectItem value="supplier">Только поставщики</SelectItem>
                  <SelectItem value="reseller">Только реселлеры</SelectItem>
                  <SelectItem value="new">Только новые</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </CardHeader>
          <CardContent>
            {(() => {
              // Применяем фильтры
              const filteredGroups = groups.filter((group) => {
                // Фильтр по поисковому запросу
                if (searchQuery && !group.domain.toLowerCase().includes(searchQuery.toLowerCase())) {
                  return false
                }
                // Фильтр по статусу
                if (filterStatus === "supplier" && group.supplierType !== "supplier") {
                  return false
                }
                if (filterStatus === "reseller" && group.supplierType !== "reseller") {
                  return false
                }
                if (filterStatus === "new" && group.supplierType !== null) {
                  return false
                }
                return true
              })

              if (filteredGroups.length === 0) {
                return (
                  <div className="text-center py-12 text-muted-foreground">
                    Результаты не найдены или все домены в blacklist
                  </div>
                )
              }

              return (
                <Accordion type="multiple" className="w-full">
                  {filteredGroups.map((group) => (
                    <AccordionItem key={group.domain} value={group.domain} className="border-b border-border/50 last:border-b-0">
                      <div className="flex items-center justify-between py-0.5">
                        <AccordionTrigger className="hover:no-underline flex-1 py-1">
                          <div className="flex items-center gap-1 flex-1">
                            <span className="font-mono font-semibold text-sm">{group.domain}</span>
                            <Badge variant="outline" className="text-xs">{group.totalUrls} URL</Badge>
                            {/* Источники, которые нашли этот домен */}
                            {group.sources && group.sources.includes("google") && (
                              <Badge variant="outline" className="bg-blue-100 text-blue-700 border-blue-300 text-xs">
                                Google
                              </Badge>
                            )}
                            {group.sources && group.sources.includes("yandex") && (
                              <Badge variant="outline" className="bg-yellow-100 text-yellow-700 border-yellow-300 text-xs">
                                Яндекс
                              </Badge>
                            )}
                            {group.supplierType === "supplier" && (
                              <Badge className="bg-green-600 hover:bg-green-700 text-white text-xs">Поставщик</Badge>
                            )}
                            {group.supplierType === "reseller" && (
                              <Badge className="bg-purple-600 hover:bg-purple-700 text-white text-xs">Реселлер</Badge>
                            )}
                          </div>
                        </AccordionTrigger>
                        {/* Действия на уровне домена (вынесены из AccordionTrigger для исправления hydration error) */}
                        <div className="flex gap-1 px-1" onClick={(e) => e.stopPropagation()}>
                          {group.supplierType ? (
                            // Если домен уже поставщик/реселлер - показываем кнопку "Изменить"
                            <Button
                              size="sm"
                              variant="outline"
                              className="h-7 text-xs"
                              onClick={() => openEditSupplierDialog(group.domain, group.supplierId!, group.supplierType!)}
                            >
                              Изменить
                            </Button>
                          ) : (
                            // Если домен не поставщик/реселлер - показываем все кнопки
                            <>
                              <Button 
                                variant="destructive" 
                                size="sm" 
                                onClick={() => handleAddToBlacklist(group.domain)}
                                className="h-7 text-xs"
                              >
                                В Blacklist
                              </Button>
                              <Button
                                size="sm"
                                className="bg-green-600 hover:bg-green-700 text-white h-7 text-xs"
                                onClick={() => openSupplierDialog(group.domain, "supplier")}
                              >
                                Поставщик
                              </Button>
                              <Button
                                size="sm"
                                className="bg-purple-600 hover:bg-purple-700 text-white h-7 text-xs"
                                onClick={() => openSupplierDialog(group.domain, "reseller")}
                              >
                                Реселлер
                              </Button>
                            </>
                          )}
                        </div>
                      </div>
                      <AccordionContent className="pb-1 pt-0">
                        <div className="max-h-60 overflow-y-auto">
                          {/* Список URL */}
                          {group.urls.map((urlEntry, idx) => {
                            // Определяем источники для этого URL на основе parsing_logs и source из domains_queue
                            const urlSources = getUrlSources(urlEntry.url, urlEntry.source)
                            
                            return (
                              <div key={idx} className="text-xs flex items-center gap-1 hover:bg-accent/50 p-0.5 rounded">
                                <a
                                  href={urlEntry.url}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="text-blue-600 hover:underline flex-1 flex items-center gap-1 truncate"
                                >
                                  <span className="truncate">{urlEntry.url}</span>
                                  <ExternalLink className="h-3 w-3 flex-shrink-0" />
                                </a>
                                {/* Бейджи источников для каждого URL */}
                                <div className="flex items-center gap-0.5 flex-shrink-0">
                                  {urlSources.includes("google") && (
                                    <Badge variant="outline" className="bg-blue-100 text-blue-700 border-blue-300 text-xs px-1 py-0">
                                      G
                                    </Badge>
                                  )}
                                  {urlSources.includes("yandex") && (
                                    <Badge variant="outline" className="bg-yellow-100 text-yellow-700 border-yellow-300 text-xs px-1 py-0">
                                      Y
                                    </Badge>
                                  )}
                                </div>
                              </div>
                            )
                          })}
                        </div>
                      </AccordionContent>
                    </AccordionItem>
                  ))}
                </Accordion>
              )
            })()}
          </CardContent>
        </Card>

        {/* Логи парсера в реальном времени */}
        {(run?.status === "running" || parsingLogs) && (
          <Card className="mt-6 border-2 border-blue-500">
            <CardHeader>
              <CardTitle>Состояние парсинга</CardTitle>
            </CardHeader>
            <CardContent>
              {parsingLogs ? (
                <>
                  {parsingLogs.google || parsingLogs.yandex ? (
                    <Accordion 
                      type="multiple" 
                      value={accordionValue} 
                      onValueChange={setAccordionValue}
                      className="w-full"
                    >
                      {parsingLogs.google && (
                        <AccordionItem value="google" className="border-b">
                          <AccordionTrigger className="hover:no-underline">
                            <div className="flex items-center gap-2 flex-1">
                              <span className="w-3 h-3 rounded-full bg-blue-500"></span>
                              <span className="font-semibold">Google</span>
                              <Badge variant="outline" className="ml-2">
                                {parsingLogs.google.total_links} ссылок
                              </Badge>
                              {parsingLogs.google.pages_processed > 0 && (
                                <Badge variant="outline" className="ml-1">
                                  {parsingLogs.google.pages_processed} стр.
                                </Badge>
                              )}
                            </div>
                          </AccordionTrigger>
                          <AccordionContent>
                            <div className="pt-2 space-y-3">
                              <div className="text-sm space-y-1">
                                <p className="text-muted-foreground">
                                  Найдено ссылок: <span className="font-medium text-blue-600">{parsingLogs.google.total_links}</span>
                                </p>
                                {parsingLogs.google.pages_processed > 0 && (
                                  <p className="text-muted-foreground">
                                    Обработано страниц: <span className="font-medium">{parsingLogs.google.pages_processed}</span>
                                  </p>
                                )}
                                {parsingLogs.google.links_by_page && Object.keys(parsingLogs.google.links_by_page).length > 0 && (
                                  <div className="mt-2">
                                    <p className="text-xs font-medium text-muted-foreground mb-1">Ссылок по страницам:</p>
                                    <div className="flex flex-wrap gap-2">
                                      {Object.entries(parsingLogs.google.links_by_page)
                                        .sort(([a], [b]) => Number(a) - Number(b))
                                        .map(([page, count]) => (
                                          <Badge key={`google-page-${page}`} variant="outline" className="text-xs">
                                            Страница {page}: {count}
                                          </Badge>
                                        ))}
                                    </div>
                                  </div>
                                )}
                              </div>
                              {parsingLogs.google.last_links && parsingLogs.google.last_links.length > 0 && (
                                <div className="mt-3">
                                  <p className="text-xs font-medium text-muted-foreground mb-2">
                                    Найденные ссылки ({parsingLogs.google.last_links.length}):
                                  </p>
                                  <div className="space-y-1 max-h-96 overflow-y-auto border rounded-md p-2 bg-muted/30">
                                    {parsingLogs.google.last_links.map((link, idx) => (
                                      <div key={`google-${idx}`} className="text-xs text-muted-foreground flex items-start gap-2 py-1">
                                        <span className="text-muted-foreground/50 min-w-[2rem]">{idx + 1}.</span>
                                        <a 
                                          href={link} 
                                          target="_blank" 
                                          rel="noopener noreferrer"
                                          className="text-blue-600 hover:text-blue-800 hover:underline break-all flex-1"
                                        >
                                          {link}
                                        </a>
                                        <ExternalLink className="w-3 h-3 text-muted-foreground/50 flex-shrink-0 mt-0.5" />
                                      </div>
                                    ))}
                                  </div>
                                </div>
                              )}
                            </div>
                          </AccordionContent>
                        </AccordionItem>
                      )}
                      {parsingLogs.yandex && (
                        <AccordionItem value="yandex" className="border-b">
                          <AccordionTrigger className="hover:no-underline">
                            <div className="flex items-center gap-2 flex-1">
                              <span className="w-3 h-3 rounded-full bg-red-500"></span>
                              <span className="font-semibold">Яндекс</span>
                              <Badge variant="outline" className="ml-2">
                                {parsingLogs.yandex.total_links} ссылок
                              </Badge>
                              {parsingLogs.yandex.pages_processed > 0 && (
                                <Badge variant="outline" className="ml-1">
                                  {parsingLogs.yandex.pages_processed} стр.
                                </Badge>
                              )}
                            </div>
                          </AccordionTrigger>
                          <AccordionContent>
                            <div className="pt-2 space-y-3">
                              <div className="text-sm space-y-1">
                                <p className="text-muted-foreground">
                                  Найдено ссылок: <span className="font-medium text-red-600">{parsingLogs.yandex.total_links}</span>
                                </p>
                                {parsingLogs.yandex.pages_processed > 0 && (
                                  <p className="text-muted-foreground">
                                    Обработано страниц: <span className="font-medium">{parsingLogs.yandex.pages_processed}</span>
                                  </p>
                                )}
                                {parsingLogs.yandex.links_by_page && Object.keys(parsingLogs.yandex.links_by_page).length > 0 && (
                                  <div className="mt-2">
                                    <p className="text-xs font-medium text-muted-foreground mb-1">Ссылок по страницам:</p>
                                    <div className="flex flex-wrap gap-2">
                                      {Object.entries(parsingLogs.yandex.links_by_page)
                                        .sort(([a], [b]) => Number(a) - Number(b))
                                        .map(([page, count]) => (
                                          <Badge key={`yandex-page-${page}`} variant="outline" className="text-xs">
                                            Страница {page}: {count}
                                          </Badge>
                                        ))}
                                    </div>
                                  </div>
                                )}
                              </div>
                              {parsingLogs.yandex.last_links && parsingLogs.yandex.last_links.length > 0 && (
                                <div className="mt-3">
                                  <p className="text-xs font-medium text-muted-foreground mb-2">
                                    Найденные ссылки ({parsingLogs.yandex.last_links.length}):
                                  </p>
                                  <div className="space-y-1 max-h-96 overflow-y-auto border rounded-md p-2 bg-muted/30">
                                    {parsingLogs.yandex.last_links.map((link, idx) => (
                                      <div key={`yandex-${idx}`} className="text-xs text-muted-foreground flex items-start gap-2 py-1">
                                        <span className="text-muted-foreground/50 min-w-[2rem]">{idx + 1}.</span>
                                        <a 
                                          href={link} 
                                          target="_blank" 
                                          rel="noopener noreferrer"
                                          className="text-red-600 hover:text-red-800 hover:underline break-all flex-1"
                                        >
                                          {link}
                                        </a>
                                        <ExternalLink className="w-3 h-3 text-muted-foreground/50 flex-shrink-0 mt-0.5" />
                                      </div>
                                    ))}
                                  </div>
                                </div>
                              )}
                            </div>
                          </AccordionContent>
                        </AccordionItem>
                      )}
                    </Accordion>
                  ) : (
                    <p className="text-sm text-muted-foreground">Логи парсинга пока недоступны...</p>
                  )}
                </>
              ) : (
                <p className="text-sm text-muted-foreground animate-pulse">Загрузка логов парсинга...</p>
              )}
            </CardContent>
          </Card>
        )}

        {/* История парсинга */}
        {(run?.processLog || run?.process_log) && (
          <Card className="mt-6">
            <CardHeader>
              <CardTitle>История парсинга</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {(() => {
                  const processLog = run.processLog || run.process_log
                  if (!processLog) return null
                  
                  return (
                    <>
                      {processLog.source_statistics && (
                        <div>
                          <h4 className="font-semibold mb-2">Статистика по источникам:</h4>
                          <div className="flex gap-4 text-sm">
                            <span className="flex items-center gap-1">
                              <span className="w-2 h-2 rounded-full bg-blue-500"></span>
                              Google: {processLog.source_statistics.google}
                            </span>
                            <span className="flex items-center gap-1">
                              <span className="w-2 h-2 rounded-full bg-red-500"></span>
                              Yandex: {processLog.source_statistics.yandex}
                            </span>
                            <span className="flex items-center gap-1">
                              <span className="w-2 h-2 rounded-full bg-purple-500"></span>
                              Оба: {processLog.source_statistics.both}
                            </span>
                          </div>
                        </div>
                      )}
                      {processLog.total_domains !== undefined && (
                        <div>
                          <h4 className="font-semibold mb-2">Общее количество доменов:</h4>
                          <p className="text-sm">{processLog.total_domains}</p>
                        </div>
                      )}
                      {processLog.duration_seconds !== undefined && (
                        <div>
                          <h4 className="font-semibold mb-2">Время выполнения:</h4>
                          <p className="text-sm">
                            {Math.floor(processLog.duration_seconds / 60)} мин {Math.floor(processLog.duration_seconds % 60)} сек
                          </p>
                        </div>
                      )}
                      {processLog.captcha_detected && (
                        <div className="p-3 bg-orange-50 border border-orange-200 rounded-md">
                          <p className="text-sm text-orange-800">⚠️ Обнаружена CAPTCHA во время парсинга</p>
                        </div>
                      )}
                      {processLog.error && (
                        <div className="p-3 bg-red-50 border border-red-200 rounded-md">
                          <h4 className="font-semibold mb-2 text-red-800">Ошибка:</h4>
                          <p className="text-sm text-red-700">{processLog.error}</p>
                        </div>
                      )}
                      {processLog.started_at && (
                        <div>
                          <h4 className="font-semibold mb-2">Время начала:</h4>
                          <p className="text-sm">{new Date(processLog.started_at).toLocaleString('ru-RU')}</p>
                        </div>
                      )}
                      {processLog.finished_at && (
                        <div>
                          <h4 className="font-semibold mb-2">Время завершения:</h4>
                          <p className="text-sm">{new Date(processLog.finished_at).toLocaleString('ru-RU')}</p>
                        </div>
                      )}
                    </>
                  )
                })()}
              </div>
            </CardContent>
          </Card>
        )}
      </main>

      {/* Supplier Dialog */}
      <Dialog open={supplierDialogOpen} onOpenChange={setSupplierDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              {editingSupplierId 
                ? `Изменить ${supplierForm.type === "supplier" ? "поставщика" : "реселлера"}` 
                : supplierForm.type === "supplier" ? "Создать поставщика" : "Создать реселлера"}
            </DialogTitle>
            <DialogDescription>Заполните информацию о компании</DialogDescription>
          </DialogHeader>

          <div className="space-y-4">
            <div>
              <Label htmlFor="name">Название *</Label>
              <Input
                id="name"
                value={supplierForm.name}
                onChange={(e) => setSupplierForm({ ...supplierForm, name: e.target.value })}
                placeholder="ООО Компания"
              />
            </div>
            <div>
              <div className="flex items-start gap-2">
                <div className="flex-1">
                  <Label htmlFor="inn">ИНН</Label>
                  <Input
                    id="inn"
                    value={supplierForm.inn}
                    onChange={(e) => setSupplierForm({ ...supplierForm, inn: e.target.value.replace(/\D/g, '') })}
                    placeholder="1234567890"
                  />
                </div>
                <div className="pt-7">
                  <CheckoInfoDialog
                    inn={supplierForm.inn}
                    onDataLoaded={(data) => {
                      setSupplierForm({ ...supplierForm, ...data })
                    }}
                  />
                </div>
              </div>
            </div>
            <div>
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                value={supplierForm.email}
                onChange={(e) => setSupplierForm({ ...supplierForm, email: e.target.value })}
                placeholder="info@example.com"
              />
            </div>
            <div>
              <Label htmlFor="domain">Домен</Label>
              <Input
                id="domain"
                value={supplierForm.domain}
                onChange={(e) => setSupplierForm({ ...supplierForm, domain: e.target.value })}
                placeholder="example.com"
              />
            </div>
            <div>
              <Label htmlFor="address">Адрес</Label>
              <Input
                id="address"
                value={supplierForm.address}
                onChange={(e) => setSupplierForm({ ...supplierForm, address: e.target.value })}
                placeholder="г. Москва, ул. Ленина, д. 1"
              />
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => {
              setSupplierDialogOpen(false)
              setEditingSupplierId(null)
            }}>
              Отмена
            </Button>
            <Button onClick={handleCreateSupplier}>
              {editingSupplierId ? "Сохранить" : "Создать"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
