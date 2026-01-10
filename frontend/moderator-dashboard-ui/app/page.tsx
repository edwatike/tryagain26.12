"use client"

import { useState, useEffect, useRef } from "react"
import { useRouter } from "next/navigation"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Label } from "@/components/ui/label"
import { Progress } from "@/components/ui/progress"
import { Navigation } from "@/components/navigation"
import { getParsingRuns, getDomainsQueue, getBlacklist, getSuppliers, startParsing, getParsingRun, getParsingLogs } from "@/lib/api"
import { extractRootDomain } from "@/lib/utils-domain"
import { toast } from "sonner"
import { ArrowRight, Play, TrendingUp, AlertCircle, Ban } from "lucide-react"
import type { ParsingRunDTO } from "@/lib/types"

export default function DashboardPage() {
  const router = useRouter()
  const [keyword, setKeyword] = useState("")
  const [depth, setDepth] = useState(5)
  const [source, setSource] = useState<"google" | "yandex" | "both">("both")
  const [loading, setLoading] = useState(false)
  const [stats, setStats] = useState({
    domainsInQueue: 0,
    newSuppliers: 0,
    activeRuns: 0,
    blacklistCount: 0,
  })
  const [recentRuns, setRecentRuns] = useState<ParsingRunDTO[]>([])
  const [parsingProgress, setParsingProgress] = useState<{
    isRunning: boolean
    runId: string | null
    status: string
    resultsCount?: number | null
    source?: string | null
    sourceStats?: {
      google: number
      yandex: number
      both: number
    }
    sourceStatus?: {
      google: { completed: boolean; domains: number }
      yandex: { completed: boolean; domains: number }
    }
    captchaDetected?: boolean  // Флаг обнаружения CAPTCHA
    recentDomains?: Array<{
      domain: string
      source: string | null
      createdAt: string
    }>  // Последние полученные домены
    progressPercent?: number  // Процент выполнения (0-100)
    parsingLogs?: {
      google?: { total_links: number; pages_processed: number; last_links: string[] }
      yandex?: { total_links: number; pages_processed: number; last_links: string[] }
    } | null  // Логи парсера с информацией о найденных ссылках
  }>({ 
    isRunning: false, 
    runId: null, 
    status: "", 
    resultsCount: null, 
    source: null, 
    sourceStats: undefined,
    sourceStatus: undefined,
    captchaDetected: false,
    recentDomains: [],
    progressPercent: undefined,
    parsingLogs: null
  })
  
  // Для отслеживания динамики завершения источников (для определения когда источник завершился)
  const sourceHistoryRef = useRef<{
    google: number[]
    yandex: number[]
  }>({ google: [], yandex: [] })
  
  // Кэш для доменов (используем useRef для сохранения между рендерами)
  const domainsCacheRef = useRef<Array<{ domain: string; source: string | null; createdAt: string }>>([])
  
  // Фильтр для доменов по источнику
  const [domainSourceFilter, setDomainSourceFilter] = useState<"all" | "google" | "yandex" | "both">("all")

  useEffect(() => {
    loadDashboardData()
  }, [])

  // Polling для обновления статуса парсинга с адаптивным интервалом
  useEffect(() => {
    if (!parsingProgress.isRunning || !parsingProgress.runId) return

    // Адаптивный интервал: 2 сек для running, 5 сек для completed/failed
    const getPollingInterval = (status: string) => {
      if (status === "running") return 2000  // 2 секунды
      if (status === "completed" || status === "failed") return 5000  // 5 секунд для финальной проверки
      return 2000  // По умолчанию 2 секунды
    }

    let pollCount = 0  // Счетчик для остановки polling после завершения
    const maxPollAfterCompletion = 3  // Максимум 3 проверки после завершения
    let currentStatus = parsingProgress.status
    let currentInterval = getPollingInterval(currentStatus)
    let intervalId: NodeJS.Timeout | null = null

    const poll = async () => {
      try {
        const runId = parsingProgress.runId
        if (!runId) return
        
        const run = await getParsingRun(runId)
        
        // Проверяем, есть ли упоминание CAPTCHA в error_message или error
        const captchaDetected = (run.error_message?.toLowerCase().includes("captcha") || 
                                 run.error_message?.toLowerCase().includes("капча") ||
                                 run.error?.toLowerCase().includes("captcha") || 
                                 run.error?.toLowerCase().includes("капча") ||
                                 false)
        
        // Получаем статистику по источникам и последние домены
        let sourceStats: { google: number; yandex: number; both: number } | undefined = undefined
        let recentDomains: Array<{ domain: string; source: string | null; createdAt: string }> = []
        let parsingLogs: { google?: { total_links: number; pages_processed: number; last_links: string[] }; yandex?: { total_links: number; pages_processed: number; last_links: string[] } } | null = null
        
        try {
          const domainsData = await getDomainsQueue({ parsingRunId: runId, limit: 1000 })
          const googleCount = domainsData.entries.filter(e => e.source === "google").length
          const yandexCount = domainsData.entries.filter(e => e.source === "yandex").length
          const bothCount = domainsData.entries.filter(e => e.source === "both").length
          sourceStats = { google: googleCount, yandex: yandexCount, both: bothCount }
          
          // Получаем parsing logs для более точного расчета прогресса
          try {
            const logsData = await getParsingLogs(runId)
            parsingLogs = logsData.parsing_logs || null
          } catch (logsError) {
            console.debug("Could not fetch parsing logs:", logsError)
            // Не критично, продолжаем без логов
          }
          
          // Получаем последние 10 доменов, отсортированных по дате создания (новые первыми)
          const allDomains = domainsData.entries
            .sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime())
            .map(e => ({
              domain: e.domain,
              source: e.source || null,
              createdAt: e.createdAt
            }))
          
          // Кэширование: обновляем кэш только при появлении новых доменов
          const cachedDomains = domainsCacheRef.current
          const cachedDomainsSet = new Set(cachedDomains.map(d => `${d.domain}_${d.createdAt}`))
          const newDomains = allDomains.filter(d => !cachedDomainsSet.has(`${d.domain}_${d.createdAt}`))
          
          if (newDomains.length > 0 || cachedDomains.length === 0) {
            // Обновляем кэш: добавляем новые домены и обновляем список
            domainsCacheRef.current = allDomains.slice(0, 10)
            recentDomains = domainsCacheRef.current
          } else {
            // Используем кэш, если новых доменов нет
            recentDomains = cachedDomains
          }
        } catch (error) {
          console.error("Error getting source stats:", error)
          // При ошибке используем кэш, если он есть
          if (domainsCacheRef.current.length > 0) {
            recentDomains = domainsCacheRef.current
          }
        }
        
        // Вычисляем процент выполнения на основе реального количества полученных доменов
        // Если статус "running" - показываем реальный прогресс на основе полученных доменов
        // Если статус "completed" - 100%
        // Если статус "failed" - показываем ошибку
        let progressPercent: number | undefined = undefined
        let sourceStatus: { google: { completed: boolean; domains: number }; yandex: { completed: boolean; domains: number } } | undefined = undefined
        
        if (run.status === "completed") {
          progressPercent = 100
          // При завершении все источники завершены
          if (sourceStats) {
            sourceStatus = {
              google: { completed: true, domains: sourceStats.google },
              yandex: { completed: true, domains: sourceStats.yandex }
            }
          }
        } else if (run.status === "running") {
          const totalDomains = sourceStats ? sourceStats.google + sourceStats.yandex + sourceStats.both : 0
          const depth = run.depth || 10  // По умолчанию 10
          const sourceType = run.source || "google"
          
          // Извлекаем данные из parsing_logs для более точного расчета прогресса
          // Определяем переменные ДО всех условий, чтобы они были доступны везде
          const googleLinksFromLogs = parsingLogs?.google?.total_links || 0
          const googlePagesFromLogs = parsingLogs?.google?.pages_processed || 0
          const yandexLinksFromLogs = parsingLogs?.yandex?.total_links || 0
          const yandexPagesFromLogs = parsingLogs?.yandex?.pages_processed || 0
          
          // Реальный прогресс на основе полученных доменов
          // Учитываем, что домены могут сохраняться не сразу, поэтому используем более гибкий расчет
          if (sourceType === "both") {
            // Для "both" считаем прогресс каждого источника отдельно
            const expectedPerSource = depth * 10 // ~10 доменов на страницу
            const googleDomains = sourceStats?.google || 0
            const yandexDomains = sourceStats?.yandex || 0
            
            // Отслеживаем динамику для определения завершения источников
            if (sourceHistoryRef.current.google.length >= 3) {
              sourceHistoryRef.current.google.shift() // Удаляем старый
            }
            sourceHistoryRef.current.google.push(googleDomains)
            
            if (sourceHistoryRef.current.yandex.length >= 3) {
              sourceHistoryRef.current.yandex.shift() // Удаляем старый
            }
            sourceHistoryRef.current.yandex.push(yandexDomains)
            
            // Определяем завершение: если количество не меняется 3 проверки подряд
            const googleHistory = sourceHistoryRef.current.google
            const yandexHistory = sourceHistoryRef.current.yandex
            const googleCompleted = googleHistory.length >= 3 && googleHistory[0] === googleHistory[1] && googleHistory[1] === googleHistory[2] && googleDomains > 0
            const yandexCompleted = yandexHistory.length >= 3 && yandexHistory[0] === yandexHistory[1] && yandexHistory[1] === yandexHistory[2] && yandexDomains > 0
            
            sourceStatus = {
              google: { completed: googleCompleted, domains: googleDomains },
              yandex: { completed: yandexCompleted, domains: yandexDomains }
            }
            
            // Прогресс: каждый источник дает максимум 50%
            // Если доменов еще нет в БД, но парсинг идет - показываем прогресс на основе времени
            let googleProgress = 0
            let yandexProgress = 0
            
            // Используем parsing_logs для более точного расчета прогресса
            if (googleLinksFromLogs > 0 || googlePagesFromLogs > 0) {
              // Используем данные из логов: количество страниц или ссылок
              const pagesProcessed = googlePagesFromLogs > 0 ? googlePagesFromLogs : Math.ceil(googleLinksFromLogs / 10)
              googleProgress = Math.min((pagesProcessed / depth) * 50, 50)
            } else if (googleDomains > 0) {
              googleProgress = Math.min((googleDomains / expectedPerSource) * 100, 50)
            } else if (googleCompleted) {
              // Если завершен, но доменов нет - значит они еще не сохранены
              googleProgress = 50
            } else {
              // Если доменов нет и не завершен - оцениваем по времени
              const startedAt = run.startedAt ? new Date(run.startedAt).getTime() : null
              if (startedAt) {
                const elapsedSeconds = (Date.now() - startedAt) / 1000
                const estimatedPagesProcessed = Math.floor(elapsedSeconds / 12) // ~12 сек на страницу
                googleProgress = Math.min(Math.floor((estimatedPagesProcessed / depth) * 40), 40) // Максимум 40% для одного источника
              }
            }
            
            if (yandexLinksFromLogs > 0 || yandexPagesFromLogs > 0) {
              // Используем данные из логов: количество страниц или ссылок
              // Yandex может давать 10-20 ссылок на страницу, используем среднее 15
              const pagesProcessed = yandexPagesFromLogs > 0 ? yandexPagesFromLogs : Math.ceil(yandexLinksFromLogs / 15)
              yandexProgress = Math.min((pagesProcessed / depth) * 50, 50)
            } else if (yandexDomains > 0) {
              yandexProgress = Math.min((yandexDomains / expectedPerSource) * 100, 50)
            } else if (yandexCompleted) {
              // Если завершен, но доменов нет - значит они еще не сохранены
              yandexProgress = 50
            } else {
              // Если доменов нет и не завершен - оцениваем по времени
              const startedAt = run.startedAt ? new Date(run.startedAt).getTime() : null
              if (startedAt) {
                const elapsedSeconds = (Date.now() - startedAt) / 1000
                const estimatedPagesProcessed = Math.floor(elapsedSeconds / 12) // ~12 сек на страницу
                yandexProgress = Math.min(Math.floor((estimatedPagesProcessed / depth) * 40), 40) // Максимум 40% для одного источника
              }
            }
            
            // Если оба источника завершены, но доменов нет - показываем 95% (почти готово)
            if (googleCompleted && yandexCompleted && totalDomains === 0) {
              progressPercent = 95
            } else {
              progressPercent = Math.floor(googleProgress + yandexProgress)
            }
          } else {
            // Для одного источника
            const expectedTotal = depth * 10
            
            // Если доменов еще нет в БД, но парсинг идет - показываем прогресс на основе времени
            // Это временная оценка, пока домены не сохранятся в БД
            if (totalDomains === 0) {
              const startedAt = run.startedAt ? new Date(run.startedAt).getTime() : null
              const now = Date.now()
              const elapsedSeconds = startedAt ? (now - startedAt) / 1000 : 0
              
              // Используем parsing_logs для более точного расчета прогресса
              const linksFromLogs = (sourceType === "google" ? googleLinksFromLogs : yandexLinksFromLogs)
              const pagesFromLogs = (sourceType === "google" ? googlePagesFromLogs : yandexPagesFromLogs)
              
              if (linksFromLogs > 0 || pagesFromLogs > 0) {
                // Используем данные из логов: количество страниц или ссылок
                const linksPerPage = sourceType === "google" ? 10 : 15
                const pagesProcessed = pagesFromLogs > 0 ? pagesFromLogs : Math.ceil(linksFromLogs / linksPerPage)
                progressPercent = Math.min((pagesProcessed / depth) * 80, 80)
              } else if (startedAt && elapsedSeconds > 5) {
                // Оценка прогресса на основе времени
                // Предполагаем, что одна страница обрабатывается примерно за 10-15 секунд
                const estimatedPagesProcessed = Math.floor(elapsedSeconds / 12) // ~12 сек на страницу
                progressPercent = Math.min(Math.floor((estimatedPagesProcessed / depth) * 80), 80)
              } else {
                progressPercent = 0
              }
            } else {
              // Если домены есть - считаем нормально
              progressPercent = Math.min(Math.floor((totalDomains / expectedTotal) * 100), 95)
            }
            
            // Для одного источника статус простой
            if (sourceType === "google") {
              sourceStatus = {
                google: { completed: false, domains: totalDomains },
                yandex: { completed: true, domains: 0 }
              }
            } else if (sourceType === "yandex") {
              sourceStatus = {
                google: { completed: true, domains: 0 },
                yandex: { completed: false, domains: totalDomains }
              }
            }
          }
        }
        
        // Автоматический переход на вкладку с капчей при обнаружении
        if (captchaDetected && !parsingProgress.captchaDetected) {
          // Первое обнаружение капчи - показываем уведомление
          toast.warning("⚠️ Обнаружена CAPTCHA! Пожалуйста, откройте окно Chrome и решите капчу.", {
            duration: 10000,
          })
        }
        
        if (run.status === "completed" || run.status === "failed") {
          pollCount++
          const finalRunId = runId
          setParsingProgress((prev) => ({ 
            isRunning: pollCount < maxPollAfterCompletion,  // Продолжаем polling еще несколько раз после завершения
            runId: pollCount < maxPollAfterCompletion ? runId : null, 
            status: run.status, 
            resultsCount: run.resultsCount,
            source: run.source || prev.source,
            sourceStats: sourceStats,
            recentDomains: recentDomains,
            progressPercent: progressPercent,
            parsingLogs: parsingLogs || prev.parsingLogs  // Сохраняем логи парсера
          }))
          
          // Останавливаем polling после нескольких проверок
          if (pollCount >= maxPollAfterCompletion) {
            loadDashboardData()
            if (run.status === "completed") {
              toast.success(`Парсинг завершен. Найдено результатов: ${run.resultsCount || 0}`)
              // Автоматический переход на страницу результатов
              setTimeout(() => {
                router.push(`/parsing-runs/${finalRunId}`)
              }, 1000)
            } else {
              toast.error("Парсинг завершен с ошибкой")
            }
          }
        } else {
          pollCount = 0  // Сбрасываем счетчик, если статус снова running
          setParsingProgress((prev) => ({ 
            ...prev, 
            status: run.status,
            resultsCount: run.resultsCount ?? prev.resultsCount ?? 0,
            source: run.source || prev.source,
            sourceStats: sourceStats || prev.sourceStats,
            sourceStatus: sourceStatus || prev.sourceStatus,
            captchaDetected: captchaDetected || prev.captchaDetected,
            recentDomains: recentDomains.length > 0 ? recentDomains : prev.recentDomains,
            progressPercent: progressPercent,
            parsingLogs: parsingLogs || prev.parsingLogs  // Сохраняем логи парсера
          }))
        }
        
        // Обновляем интервал при изменении статуса
        if (run.status !== currentStatus) {
          currentStatus = run.status
          const newInterval = getPollingInterval(currentStatus)
          if (newInterval !== currentInterval && intervalId) {
            clearInterval(intervalId)
            currentInterval = newInterval
            intervalId = setInterval(poll, currentInterval)
          }
        }
      } catch (error) {
        console.error("Error checking parsing status:", error)
      }
    }

    // Начинаем polling с начальным интервалом
    intervalId = setInterval(poll, currentInterval)

    return () => {
      if (intervalId) clearInterval(intervalId)
    }
  }, [parsingProgress.isRunning, parsingProgress.runId, router])

  async function loadDashboardData() {
    try {
      // Загружаем данные порциями, так как backend ограничивает limit до 1000
      const [suppliersData, runsData, blacklistData] = await Promise.all([
        getSuppliers({ limit: 1000 }), // Загружаем всех поставщиков
        getParsingRuns({ status: "running", limit: 1 }),
        getBlacklist({ limit: 1000 }), // Загружаем весь blacklist
      ])

      const recentRunsData = await getParsingRuns({ limit: 10, sort: "created_at", order: "desc" })

      // Получаем все завершенные parsing runs для подсчета доменов из результатов парсинга
      // Ограничиваем последними 50 runs для оптимизации
      const completedRunsData = await getParsingRuns({ status: "completed", limit: 50, sort: "created_at", order: "desc" })
      
      // Загружаем домены только из завершенных parsing runs
      const uniqueDomains = new Set<string>()
      
      // Для каждого завершенного run загружаем его домены
      for (const run of completedRunsData.runs) {
        const runId = run.runId || run.run_id
        if (!runId) continue
        
        let offset = 0
        const limit = 1000
        let hasMore = true
        
        while (hasMore) {
          try {
            const domainsData = await getDomainsQueue({ parsingRunId: runId, limit, offset })
            domainsData.entries.forEach((entry) => {
              const rootDomain = extractRootDomain(entry.domain).toLowerCase()
              uniqueDomains.add(rootDomain)
            })
            
            if (domainsData.entries.length < limit || offset + limit >= domainsData.total) {
              hasMore = false
            } else {
              offset += limit
            }
          } catch (error) {
            console.error(`Error loading domains for run ${runId}:`, error)
            hasMore = false
          }
        }
      }

      // Получаем домены из blacklist
      const blacklistedDomains = new Set<string>()
      blacklistData.entries.forEach((entry) => {
        const rootDomain = extractRootDomain(entry.domain).toLowerCase()
        blacklistedDomains.add(rootDomain)
      })

      // Получаем домены из suppliers (поставщики и реселлеры)
      const processedDomains = new Set<string>()
      suppliersData.suppliers.forEach((supplier) => {
        if (supplier.domain) {
          const rootDomain = extractRootDomain(supplier.domain).toLowerCase()
          processedDomains.add(rootDomain)
        }
      })

      // Фильтруем: домены, которые НЕ в blacklist и НЕ в suppliers
      const unprocessedDomains = Array.from(uniqueDomains).filter(
        (domain) => !blacklistedDomains.has(domain) && !processedDomains.has(domain)
      )

      setStats({
        domainsInQueue: unprocessedDomains.length, // Количество уникальных необработанных доменов
        newSuppliers: suppliersData.total,
        activeRuns: runsData.total,
        blacklistCount: blacklistData.total,
      })
      setRecentRuns(recentRunsData.runs)
    } catch (error) {
      console.error("Error loading dashboard data:", error)
    }
  }

  async function handleStartParsing() {
    if (!keyword.trim()) {
      toast.error("Введите ключевое слово")
      return
    }

    if (depth < 1 || depth > 10) {
      toast.error("Глубина должна быть от 1 до 10")
      return
    }

    setLoading(true)
    try {
      const result = await startParsing({
        keyword: keyword.trim(),
        depth,
        source,
      })
      const runId = result.runId || result.run_id || ""
      toast.success(`Парсинг запущен: ${result.keyword}`)
      setKeyword("")
      setDepth(5)
      setSource("both")
      
      // Очищаем кэш доменов
      domainsCacheRef.current = []
      sourceHistoryRef.current = { google: [], yandex: [] }  // Очищаем историю источников
      
      // Сразу переходим на страницу деталей парсинга, где будут видны логи
      router.push(`/parsing-runs/${runId}`)
    } catch (error) {
      toast.error("Ошибка запуска парсинга")
      console.error("Error starting parsing:", error)
      setParsingProgress({ isRunning: false, runId: null, status: "" })
    } finally {
      setLoading(false)
    }
  }

  const exampleKeywords = ["кирпич", "цемент", "труба", "арматура"]

  return (
    <div className="min-h-screen bg-background">
      <Navigation />

      <main className="container mx-auto px-6 py-3 max-w-7xl">
        {/* Новый парсинг */}
        <div className="mb-4">
          <h1 className="text-3xl font-bold mb-2 text-balance">Запустить новый парсинг</h1>

          <Card className="border-2">
            <CardContent className="pt-4 space-y-3">
              <div className="grid gap-3">
                <div>
                  <Label htmlFor="keyword" className="text-sm mb-1 block">
                    Ключевое слово
                  </Label>
                  <Input
                    id="keyword"
                    placeholder="Введите ключевое слово..."
                    value={keyword}
                    onChange={(e) => setKeyword(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && handleStartParsing()}
                    className="text-base h-10"
                  />
                  <div className="flex gap-1 flex-wrap mt-1.5">
                    <span className="text-xs text-muted-foreground">Примеры:</span>
                    {exampleKeywords.map((word) => (
                      <Button key={word} variant="outline" size="sm" className="h-7 text-xs" onClick={() => setKeyword(word)}>
                        {word}
                      </Button>
                    ))}
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  <div>
                    <Label htmlFor="depth" className="text-sm mb-1 block">
                      Глубина парсинга
                    </Label>
                    <Input
                      id="depth"
                      type="number"
                      min={1}
                      value={depth}
                      onChange={(e) => setDepth(Number.parseInt(e.target.value) || 1)}
                      className="text-base h-10"
                    />
                    <p className="text-xs text-muted-foreground mt-1">Количество страниц результатов</p>
                  </div>

                  <div>
                    <Label className="text-sm mb-1 block">Источник</Label>
                    <div className="flex gap-1">
                      <Button
                        variant={source === "google" ? "default" : "outline"}
                        onClick={() => setSource("google")}
                        className="flex-1 h-10 text-sm"
                      >
                        Google
                      </Button>
                      <Button
                        variant={source === "yandex" ? "default" : "outline"}
                        onClick={() => setSource("yandex")}
                        className="flex-1 h-10 text-sm"
                      >
                        Яндекс
                      </Button>
                      <Button
                        variant={source === "both" ? "default" : "outline"}
                        onClick={() => setSource("both")}
                        className="flex-1 h-10 text-sm"
                      >
                        Оба
                      </Button>
                    </div>
                  </div>
                </div>
              </div>

              <Button onClick={handleStartParsing} disabled={loading || parsingProgress.isRunning} size="lg" className="w-full h-10 text-sm">
                <Play className="mr-2 h-4 w-4" />
                {parsingProgress.isRunning ? "Парсинг выполняется..." : "Запустить парсинг"}
              </Button>
            </CardContent>
          </Card>

          {/* Прогрессбар парсинга */}
          {parsingProgress.isRunning && (
            <Card className={`mt-2 border-2 ${parsingProgress.captchaDetected ? "border-orange-500" : "border-blue-500"}`}>
              <CardContent className="pt-3">
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <h3 className="font-semibold text-sm">Парсинг выполняется</h3>
                      <p className="text-xs text-muted-foreground">
                        Статус: {parsingProgress.status === "running" ? "Выполняется" : parsingProgress.status}
                      </p>
                      {parsingProgress.resultsCount !== null && parsingProgress.resultsCount !== undefined && (
                        <p className="text-xs font-medium text-blue-600 mt-0.5">
                          Найдено доменов: {parsingProgress.resultsCount}
                        </p>
                      )}
                      {parsingProgress.sourceStats && (
                        <div className="flex flex-col gap-2 mt-2 text-xs">
                          {parsingProgress.sourceStats.google > 0 && (
                            <div className="flex items-center gap-2">
                              <span className="w-2 h-2 rounded-full bg-blue-500"></span>
                              <span className="text-muted-foreground">
                                Google: {parsingProgress.sourceStats.google} доменов
                                {parsingProgress.sourceStatus?.google.completed && (
                                  <span className="text-green-600 ml-1">✓ завершен</span>
                                )}
                              </span>
                            </div>
                          )}
                          {parsingProgress.sourceStats.yandex > 0 && (
                            <div className="flex items-center gap-2">
                              <span className="w-2 h-2 rounded-full bg-red-500"></span>
                              <span className="text-muted-foreground">
                                Yandex: {parsingProgress.sourceStats.yandex} доменов
                                {parsingProgress.sourceStatus?.yandex.completed && (
                                  <span className="text-green-600 ml-1">✓ завершен</span>
                                )}
                              </span>
                            </div>
                          )}
                          {parsingProgress.sourceStats.both > 0 && (
                            <div className="flex items-center gap-2">
                              <span className="w-2 h-2 rounded-full bg-purple-500"></span>
                              <span className="text-muted-foreground">Оба: {parsingProgress.sourceStats.both}</span>
                            </div>
                          )}
                          {parsingProgress.sourceStatus && parsingProgress.source === "both" && (
                            <div className="text-xs text-muted-foreground mt-1">
                              {parsingProgress.sourceStatus.google.completed && !parsingProgress.sourceStatus.yandex.completed && (
                                <span>Google завершил сбор доменов, Yandex еще работает...</span>
                              )}
                              {!parsingProgress.sourceStatus.google.completed && parsingProgress.sourceStatus.yandex.completed && (
                                <span>Yandex завершил сбор доменов, Google еще работает...</span>
                              )}
                              {parsingProgress.sourceStatus.google.completed && parsingProgress.sourceStatus.yandex.completed && (
                                <span>Оба источника завершили сбор доменов</span>
                              )}
                            </div>
                          )}
                        </div>
                      )}
                      {parsingProgress.progressPercent !== undefined && (
                        <p className="text-xs text-muted-foreground mt-1">
                          Прогресс: {parsingProgress.progressPercent}%
                        </p>
                      )}
                      {/* Отображение логов парсера */}
                      {parsingProgress.parsingLogs && (
                        <div className="mt-3 space-y-2 text-xs border-t pt-2">
                          <div className="font-medium text-muted-foreground">Состояние парсинга:</div>
                          {parsingProgress.parsingLogs.google && (
                            <div className="flex items-center gap-2 pl-2">
                              <span className="w-2 h-2 rounded-full bg-blue-500"></span>
                              <span className="text-muted-foreground">
                                Google: {parsingProgress.parsingLogs.google.total_links} ссылок
                                {parsingProgress.parsingLogs.google.pages_processed > 0 && (
                                  <span className="ml-1">({parsingProgress.parsingLogs.google.pages_processed} стр.)</span>
                                )}
                              </span>
                            </div>
                          )}
                          {parsingProgress.parsingLogs.yandex && (
                            <div className="flex items-center gap-2 pl-2">
                              <span className="w-2 h-2 rounded-full bg-red-500"></span>
                              <span className="text-muted-foreground">
                                Яндекс: {parsingProgress.parsingLogs.yandex.total_links} ссылок
                                {parsingProgress.parsingLogs.yandex.pages_processed > 0 && (
                                  <span className="ml-1">({parsingProgress.parsingLogs.yandex.pages_processed} стр.)</span>
                                )}
                              </span>
                            </div>
                          )}
                          {/* Последние найденные ссылки */}
                          {((parsingProgress.parsingLogs.google?.last_links?.length ?? 0) > 0 || (parsingProgress.parsingLogs.yandex?.last_links?.length ?? 0) > 0) && (
                            <div className="mt-2">
                              <div className="font-medium text-muted-foreground mb-1">Последние найденные ссылки:</div>
                              <div className="space-y-1 max-h-24 overflow-y-auto pl-2">
                                {parsingProgress.parsingLogs.google?.last_links?.slice(-3).map((link, idx) => (
                                  <div key={`google-${idx}`} className="text-xs text-muted-foreground truncate">
                                    <span className="text-blue-600">G:</span> {link.length > 60 ? link.substring(0, 60) + '...' : link}
                                  </div>
                                ))}
                                {parsingProgress.parsingLogs.yandex?.last_links?.slice(-3).map((link, idx) => (
                                  <div key={`yandex-${idx}`} className="text-xs text-muted-foreground truncate">
                                    <span className="text-red-600">Y:</span> {link.length > 60 ? link.substring(0, 60) + '...' : link}
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                    {parsingProgress.runId && (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => router.push(`/parsing-runs/${parsingProgress.runId}`)}
                      >
                        Открыть детали
                      </Button>
                    )}
                  </div>
                  <Progress 
                    value={parsingProgress.progressPercent !== undefined ? parsingProgress.progressPercent : (parsingProgress.status === "running" ? undefined : 100)} 
                    className="h-2"
                  />
                  {parsingProgress.status === "running" && (
                    <div className="mt-2 space-y-2">
                      <div className="text-xs text-muted-foreground animate-pulse">
                        Парсинг выполняется...
                      </div>
                      {parsingProgress.captchaDetected && (
                        <div className="p-3 bg-orange-50 border border-orange-200 rounded-md">
                          <div className="text-sm font-medium text-orange-800 flex items-center gap-2 mb-2">
                            <AlertCircle className="h-4 w-4" />
                            Обнаружена CAPTCHA - требуется решение
                          </div>
                          <p className="text-xs text-orange-600 mb-2">
                            Пожалуйста, откройте окно Chrome и решите капчу. Парсинг будет продолжен автоматически после решения.
                          </p>
                          <Button
                            variant="outline"
                            size="sm"
                            className="w-full text-xs h-7 border-orange-300 text-orange-700 hover:bg-orange-100"
                            onClick={() => {
                              // Пытаемся открыть Chrome через системную команду (только для информации)
                              toast.info("Откройте окно Chrome вручную. Обычно оно запущено на порту 9222.", {
                                duration: 5000,
                              })
                              // Можно попробовать открыть через window.open, но это не сработает для локального Chrome CDP
                              // window.open("http://127.0.0.1:9222", "_blank")
                            }}
                          >
                            📋 Инструкция: Откройте Chrome
                          </Button>
                        </div>
                      )}
                      {parsingProgress.recentDomains && parsingProgress.recentDomains.length > 0 && (
                        <div className="mt-3">
                          <div className="flex items-center justify-between mb-2">
                            <p className="text-xs font-medium text-muted-foreground">
                              Последние полученные домены:
                            </p>
                            <div className="flex gap-1">
                              <Button
                                variant={domainSourceFilter === "all" ? "default" : "outline"}
                                size="sm"
                                className="h-6 text-xs px-2"
                                onClick={() => setDomainSourceFilter("all")}
                              >
                                Все
                              </Button>
                              <Button
                                variant={domainSourceFilter === "google" ? "default" : "outline"}
                                size="sm"
                                className="h-6 text-xs px-2"
                                onClick={() => setDomainSourceFilter("google")}
                              >
                                Google
                              </Button>
                              <Button
                                variant={domainSourceFilter === "yandex" ? "default" : "outline"}
                                size="sm"
                                className="h-6 text-xs px-2"
                                onClick={() => setDomainSourceFilter("yandex")}
                              >
                                Yandex
                              </Button>
                              <Button
                                variant={domainSourceFilter === "both" ? "default" : "outline"}
                                size="sm"
                                className="h-6 text-xs px-2"
                                onClick={() => setDomainSourceFilter("both")}
                              >
                                Оба
                              </Button>
                            </div>
                          </div>
                          <div className="space-y-1 max-h-32 overflow-y-auto">
                            {parsingProgress.recentDomains
                              .filter(domainEntry => {
                                if (domainSourceFilter === "all") return true
                                return domainEntry.source === domainSourceFilter
                              })
                              .map((domainEntry, index) => (
                                <div key={index} className="flex items-center justify-between text-xs bg-muted/50 p-2 rounded">
                                  <span className="font-mono text-xs truncate flex-1">{domainEntry.domain}</span>
                                  {domainEntry.source && (
                                    <Badge 
                                      variant="outline" 
                                      className={`ml-2 text-xs ${
                                        domainEntry.source === "google" ? "border-blue-500 text-blue-700" :
                                        domainEntry.source === "yandex" ? "border-red-500 text-red-700" :
                                        "border-purple-500 text-purple-700"
                                      }`}
                                    >
                                      {domainEntry.source === "google" ? "Google" :
                                       domainEntry.source === "yandex" ? "Yandex" :
                                       domainEntry.source}
                                    </Badge>
                                  )}
                                </div>
                              ))}
                            {parsingProgress.recentDomains.filter(d => {
                              if (domainSourceFilter === "all") return true
                              return d.source === domainSourceFilter
                            }).length === 0 && (
                              <div className="text-xs text-muted-foreground text-center py-2">
                                Нет доменов для выбранного источника
                              </div>
                            )}
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          )}
        </div>

        {/* Метрики */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3 mb-8">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                В очереди
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-0">
              <div className="text-4xl font-bold mb-1">{stats.domainsInQueue}</div>
              <div className="text-xs text-muted-foreground">доменов</div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Новые</CardTitle>
            </CardHeader>
            <CardContent className="pt-0">
              <div className="text-4xl font-bold mb-1 text-green-600">{stats.newSuppliers}</div>
              <div className="text-xs text-muted-foreground">поставщиков</div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                Активных
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-0">
              <div className="text-4xl font-bold mb-1 text-blue-600">{stats.activeRuns}</div>
              <div className="text-xs text-muted-foreground">парсингов</div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                Blacklist
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-0">
              <div className="text-4xl font-bold mb-1 text-red-600">{stats.blacklistCount}</div>
              <div className="text-xs text-muted-foreground">доменов</div>
            </CardContent>
          </Card>
        </div>

        {/* Последние запуски */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-xl font-bold">Последние запуски</h2>
            <Button variant="ghost" size="sm" className="h-8 text-xs" onClick={() => router.push("/parsing-runs")}>
              Все запуски
              <ArrowRight className="ml-2 h-3 w-3" />
            </Button>
          </div>

          {recentRuns.length === 0 ? (
            <Card>
              <CardContent className="py-6 text-center text-muted-foreground text-sm">Нет запусков парсинга</CardContent>
            </Card>
          ) : (
            <div className="flex gap-2 overflow-x-auto pb-2">
              {recentRuns.map((run) => {
                const runId = run.runId || run.run_id || ""
                const createdAt = run.createdAt || run.created_at || ""
                return (
                  <Card
                    key={runId}
                    className="min-w-[200px] cursor-pointer hover:border-primary transition-colors"
                    onClick={() => runId && router.push(`/parsing-runs/${runId}`)}
                  >
                    <CardContent className="pt-3">
                      <div className="flex items-start justify-between mb-1.5">
                        <div className="font-semibold text-sm">{run.keyword}</div>
                        <Badge
                          variant={
                            run.status === "completed" ? "default" : run.status === "running" ? "outline" : "destructive"
                          }
                          className={
                            run.status === "completed" 
                              ? "bg-green-600 hover:bg-green-700 text-white text-xs" 
                              : run.status === "failed" 
                              ? "bg-red-600 hover:bg-red-700 text-white text-xs"
                              : "text-xs"
                          }
                        >
                          {run.status === "completed" ? "✓" : run.status === "running" ? "⏳" : "✗"}
                        </Badge>
                      </div>
                      <div className="text-xs text-muted-foreground">
                        {createdAt
                          ? new Date(createdAt).toLocaleDateString("ru-RU", {
                              day: "numeric",
                              month: "short",
                            })
                          : "—"}
                      </div>
                      {run.resultsCount !== null && run.resultsCount !== undefined && (
                        <div className="text-xs font-medium mt-1">{run.resultsCount} результатов</div>
                      )}
                    </CardContent>
                  </Card>
                )
              })}
            </div>
          )}
        </div>

        {/* CTA кнопки */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          <Button
            variant="outline"
            size="lg"
            className="h-12 text-sm justify-start bg-transparent"
            onClick={() => router.push("/parsing-runs")}
          >
            <TrendingUp className="mr-2 h-4 w-4" />
            Обработать очередь
          </Button>

          <Button
            variant="outline"
            size="lg"
            className="h-12 text-sm justify-start bg-transparent"
            onClick={() => router.push("/suppliers")}
          >
            <AlertCircle className="mr-2 h-4 w-4" />
            Проверить новых
          </Button>

          <Button
            variant="outline"
            size="lg"
            className="h-12 text-sm justify-start bg-transparent"
            onClick={() => router.push("/blacklist")}
          >
            <Ban className="mr-2 h-4 w-4" />
            Управление Blacklist
          </Button>
        </div>
      </main>
    </div>
  )
}
