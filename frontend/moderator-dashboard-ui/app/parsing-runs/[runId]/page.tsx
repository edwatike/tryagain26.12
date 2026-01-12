"use client"

import { useState, useEffect, use, useRef } from "react"
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
import { Textarea } from "@/components/ui/textarea"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Navigation } from "@/components/navigation"
import { CheckoInfoDialog } from "@/components/checko-info-dialog"
import { getParsingRun, getDomainsQueue, getBlacklist, addToBlacklist, createSupplier, updateSupplier, getSuppliers, getParsingLogs, extractINNBatch, startCometExtractBatch, getCometStatus, getCheckoData, startDomainParserBatch, getDomainParserStatus, APIError } from "@/lib/api"
import { groupByDomain, extractRootDomain, collectDomainSources, normalizeUrl } from "@/lib/utils-domain"
import { getCachedSuppliers, setCachedSuppliers, getCachedBlacklist, setCachedBlacklist, invalidateSuppliersCache, invalidateBlacklistCache } from "@/lib/cache"
import { toast } from "sonner"
import { ExternalLink, Copy, FileSearch } from "lucide-react"
import { Checkbox } from "@/components/ui/checkbox"
import type { ParsingDomainGroup, ParsingRunDTO, INNExtractionResult, CometExtractionResult, CometStatusResponse, SupplierDTO, DomainParserResult, DomainParserStatusResponse } from "@/lib/types"

export default function ParsingRunDetailsPage({ params }: { params: Promise<{ runId: string }> }) {
  const router = useRouter()
  const resolvedParams = use(params)
  const runId = resolvedParams.runId
  const [run, setRun] = useState<ParsingRunDTO | null>(null)
  const [groups, setGroups] = useState<ParsingDomainGroup[]>([])
  const [loading, setLoading] = useState(true)
  const [refreshKey, setRefreshKey] = useState(0) // Ключ для принудительного обновления
  const [supplierDialogOpen, setSupplierDialogOpen] = useState(false)
  const [blacklistDialogOpen, setBlacklistDialogOpen] = useState(false)
  const [blacklistDomain, setBlacklistDomain] = useState("")
  const [blacklistReason, setBlacklistReason] = useState("")
  const [addingToBlacklist, setAddingToBlacklist] = useState(false)
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
  const [selectedDomains, setSelectedDomains] = useState<Set<string>>(new Set()) // Выбранные домены для извлечения ИНН
  const [innExtractionDialogOpen, setInnExtractionDialogOpen] = useState(false) // Модальное окно извлечения ИНН
  const [innExtractionResults, setInnExtractionResults] = useState<INNExtractionResult[]>([]) // Результаты извлечения ИНН
  const [innExtractionLoading, setInnExtractionLoading] = useState(false) // Загрузка извлечения ИНН
  const [innExtractionProgress, setInnExtractionProgress] = useState({ processed: 0, total: 0 }) // Прогресс извлечения
  const [innResultsMap, setInnResultsMap] = useState<Map<string, INNExtractionResult>>(new Map()) // Кэш результатов извлечения ИНН по домену
  const [extractingDomains, setExtractingDomains] = useState<Set<string>>(new Set()) // Домены, для которых идет извлечение

  const [cometRunId, setCometRunId] = useState<string | null>(null)
  const [cometStatus, setCometStatus] = useState<CometStatusResponse | null>(null)
  const [cometLoading, setCometLoading] = useState(false)
  const [cometResultsMap, setCometResultsMap] = useState<Map<string, CometExtractionResult>>(new Map())

  const [parserRunId, setParserRunId] = useState<string | null>(null)
  const [parserStatus, setParserStatus] = useState<DomainParserStatusResponse | null>(null)
  const [parserLoading, setParserLoading] = useState(false)
  const [parserResultsMap, setParserResultsMap] = useState<Map<string, DomainParserResult>>(new Map())

  const suppliersByDomainRef = useRef<Map<string, SupplierDTO>>(new Map())
  const cometAutofillDoneRef = useRef<Set<string>>(new Set())
  const cometAutofillLockRef = useRef<Set<string>>(new Set())
  const parserAutofillDoneRef = useRef<Set<string>>(new Set())
  const parserAutoSaveProcessedRef = useRef<boolean>(false)
  
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

  // Восстанавливаем кэш результатов ИНН из localStorage при загрузке
  useEffect(() => {
    if (!runId) return
    try {
      const cached = localStorage.getItem(`inn-results-${runId}`)
      if (cached) {
        const cachedMap = new Map<string, INNExtractionResult>(JSON.parse(cached))
        setInnResultsMap(cachedMap)
      }
    } catch (error) {
      // Игнорируем ошибки парсинга кэша
    }
  }, [runId])

  useEffect(() => {
    if (!runId || !cometRunId) return
    try {
      const key = `comet-autofill-done-${runId}-${cometRunId}`
      const raw = localStorage.getItem(key)
      if (!raw) return
      const parsed = JSON.parse(raw)
      if (Array.isArray(parsed)) {
        for (const d of parsed) {
          if (typeof d === "string" && d) {
            cometAutofillDoneRef.current.add(d)
          }
        }
      }
    } catch {
      // ignore
    }
  }, [runId, cometRunId])

  useEffect(() => {
    if (!runId) return
    try {
      const cached = localStorage.getItem(`comet-results-${runId}`)
      if (cached) {
        const cachedMap = new Map<string, CometExtractionResult>(JSON.parse(cached))
        setCometResultsMap(cachedMap)
      }
      const cachedRunId = localStorage.getItem(`comet-run-${runId}`)
      if (cachedRunId) {
        setCometRunId(cachedRunId)
      }
    } catch (error) {
      // ignore
    }
  }, [runId])

  // Сохраняем кэш результатов ИНН в localStorage при изменении
  useEffect(() => {
    if (!runId || innResultsMap.size === 0) return
    try {
      const serialized = JSON.stringify(Array.from(innResultsMap.entries()))
      localStorage.setItem(`inn-results-${runId}`, serialized)
    } catch (error) {
      // Игнорируем ошибки сохранения кэша
    }
  }, [innResultsMap, runId])

  useEffect(() => {
    if (!runId || cometResultsMap.size === 0) return
    try {
      const serialized = JSON.stringify(Array.from(cometResultsMap.entries()))
      localStorage.setItem(`comet-results-${runId}`, serialized)
    } catch (error) {
      // ignore
    }
  }, [cometResultsMap, runId])

  useEffect(() => {
    if (!runId || !cometRunId) return
    try {
      localStorage.setItem(`comet-run-${runId}`, cometRunId)
    } catch (error) {
      // ignore
    }
  }, [cometRunId, runId])

  useEffect(() => {
    if (!runId || !cometRunId) return

    const poll = async () => {
      try {
        const status = await getCometStatus(runId, cometRunId)
        setCometStatus(status)
        if (status.results && status.results.length > 0) {
          setCometResultsMap((prev) => {
            const next = new Map(prev)
            for (const r of status.results) {
              next.set(r.domain, r)
            }
            return next
          })
        }
      } catch (e) {
        // silent
      }
    }

    poll()
    const t = setInterval(poll, 2000)
    return () => clearInterval(t)
  }, [runId, cometRunId])

  useEffect(() => {
    if (!runId || !cometRunId) return
    if (!cometResultsMap || cometResultsMap.size === 0) return

    const isValidInn = (inn: string | null | undefined) => {
      const v = String(inn || "").trim()
      return /^\d{10}$/.test(v) || /^\d{12}$/.test(v)
    }

    const markDone = (domain: string) => {
      cometAutofillDoneRef.current.add(domain)
      try {
        const key = `comet-autofill-done-${runId}-${cometRunId}`
        const arr = Array.from(cometAutofillDoneRef.current)
        localStorage.setItem(key, JSON.stringify(arr))
      } catch {
        // ignore
      }
    }

    const autoUpsert = async (domain: string, res: CometExtractionResult) => {
      const lockKey = `${runId}|${cometRunId}|${domain}`
      if (cometAutofillDoneRef.current.has(domain)) return
      if (cometAutofillLockRef.current.has(lockKey)) return

      console.log(`[Comet AutoUpsert] Processing ${domain}:`, res)
      console.log(`[Comet AutoUpsert] res.status:`, res.status)
      console.log(`[Comet AutoUpsert] res.inn:`, res.inn)
      console.log(`[Comet AutoUpsert] res.email:`, res.email)
      
      if (res.status !== "success") {
        console.log(`[Comet AutoUpsert] Skipping ${domain}: status is ${res.status}`)
        return
      }
      if (!isValidInn(res.inn) && !res.email) {
        console.log(`[Comet AutoUpsert] Skipping ${domain}: no valid INN or email`)
        console.log(`[Comet AutoUpsert] isValidInn check:`, isValidInn(res.inn))
        return
      }

      console.log(`[Comet AutoUpsert] Creating/updating supplier for ${domain}`)
      cometAutofillLockRef.current.add(lockKey)
      try {
        const rootDomain = extractRootDomain(domain).toLowerCase()
        const existing = suppliersByDomainRef.current.get(rootDomain)
        
        // Parse INN: convert to string, trim, and set to null if empty
        const innRaw = res.inn ? String(res.inn).trim() : ""
        const inn = innRaw && /^\d{10,12}$/.test(innRaw) ? innRaw : null
        
        const email = res.email ? String(res.email).trim() : null
        
        console.log(`[Comet AutoUpsert] Parsed data - INN: ${inn}, Email: ${email}`)

        let checko: any = null
        if (inn) {
          console.log(`[Comet AutoUpsert] Fetching Checko data for INN: ${inn}`)
          try {
            checko = await getCheckoData(inn, false)
            console.log(`[Comet AutoUpsert] Checko data received:`, checko ? 'success' : 'null')
          } catch (e) {
            console.error(`[Comet AutoUpsert] Failed to fetch Checko data:`, e)
            checko = null
          }
        } else {
          console.log(`[Comet AutoUpsert] No valid INN, skipping Checko`)
        }

        const baseName = (checko?.name && String(checko.name).trim()) || rootDomain
        const supplierType: "supplier" | "reseller" = existing?.type || "supplier"

        let saved: SupplierDTO
        if (existing?.id) {
          console.log(`[Comet AutoUpsert] Updating existing supplier ID ${existing.id}`)
          console.log(`[Comet AutoUpsert] Data to send:`, { name: baseName, inn, email, domain: rootDomain, type: supplierType })
          saved = await updateSupplier(existing.id, {
            name: baseName,
            inn,
            email,
            domain: rootDomain,
            type: supplierType,
          })
          console.log(`[Comet AutoUpsert] Updated supplier:`, saved)
        } else {
          console.log(`[Comet AutoUpsert] Creating new supplier`)
          console.log(`[Comet AutoUpsert] Data to send:`, { name: baseName, inn, email, domain: rootDomain, address: null, type: supplierType })
          saved = await createSupplier({
            name: baseName,
            inn,
            email,
            domain: rootDomain,
            address: null,
            type: supplierType,
          })
          console.log(`[Comet AutoUpsert] Created supplier:`, saved)
        }

        if (checko) {
          saved = await updateSupplier(saved.id, {
            name: checko.name || saved.name,
            inn,
            email,
            domain: rootDomain,
            type: supplierType,
            ogrn: checko.ogrn || null,
            kpp: checko.kpp || null,
            okpo: checko.okpo || null,
            companyStatus: checko.companyStatus || null,
            registrationDate: checko.registrationDate || null,
            legalAddress: checko.legalAddress || null,
            phone: checko.phone || null,
            website: checko.website || null,
            vk: checko.vk || null,
            telegram: checko.telegram || null,
            authorizedCapital: checko.authorizedCapital ?? null,
            revenue: checko.revenue ?? null,
            profit: checko.profit ?? null,
            financeYear: checko.financeYear ?? null,
            legalCasesCount: checko.legalCasesCount ?? null,
            legalCasesSum: checko.legalCasesSum ?? null,
            legalCasesAsPlaintiff: checko.legalCasesAsPlaintiff ?? null,
            legalCasesAsDefendant: checko.legalCasesAsDefendant ?? null,
            checkoData: checko.checkoData || null,
          })
        }

        suppliersByDomainRef.current.set(rootDomain, saved)
        invalidateSuppliersCache()
        setRefreshKey((k) => k + 1)
        markDone(domain)
        toast.success(`Comet: создан/обновлён поставщик для ${rootDomain}`)
      } catch (e) {
        // silent, to avoid noisy UI; user can retry via manual edit
      } finally {
        cometAutofillLockRef.current.delete(lockKey)
      }
    }

    for (const [domain, res] of cometResultsMap.entries()) {
      void autoUpsert(domain, res)
    }
  }, [runId, cometRunId, cometResultsMap])

  // Polling для Domain Parser статуса
  useEffect(() => {
    if (!parserRunId) return

    const poll = async () => {
      try {
        const status = await getDomainParserStatus(parserRunId)
        setParserStatus(status)
        if (status.results && status.results.length > 0) {
          setParserResultsMap((prev) => {
            const next = new Map(prev)
            for (const r of status.results) {
              next.set(r.domain, r)
            }
            return next
          })
        }
      } catch (e) {
        // silent
      }
    }

    poll()
    const t = setInterval(poll, 2000)
    return () => clearInterval(t)
  }, [runId, parserRunId])

  // Автоматическое сохранение доменов с ИНН+email после Domain Parser
  // С ЗАЩИТОЙ ОТ ДУБЛИКАТОВ через проверку существования по домену
  useEffect(() => {
    if (!runId || !parserRunId || !parserStatus) return
    if (parserStatus.status !== 'completed') return
    if (!parserResultsMap || parserResultsMap.size === 0) return
    
    // Проверяем, не обработали ли мы уже этот parserRunId
    if (parserAutoSaveProcessedRef.current) {
      console.log('[Domain Parser AutoSave] Already processed, skipping')
      return
    }

    // Автоматически сохраняем домены с ИНН и Email
    const autoSaveDomains = async () => {
      // Устанавливаем флаг сразу, чтобы предотвратить повторные запуски
      parserAutoSaveProcessedRef.current = true
      
      console.log('[Domain Parser AutoSave] Starting auto-save for domains with INN+Email')
      
      // КРИТИЧНО: Загружаем актуальный список поставщиков из БД перед началом
      let currentSuppliers: Map<string, SupplierDTO>
      try {
        const { suppliers } = await getSuppliers()
        currentSuppliers = new Map()
        for (const s of suppliers) {
          if (s.domain) {
            currentSuppliers.set(s.domain.toLowerCase(), s)
          }
        }
        console.log(`[Domain Parser AutoSave] Loaded ${currentSuppliers.size} existing suppliers from DB`)
      } catch (e) {
        console.error('[Domain Parser AutoSave] Failed to load suppliers, aborting:', e)
        toast.error('Ошибка загрузки списка поставщиков')
        return
      }
      
      let savedCount = 0
      let skippedCount = 0
      
      for (const [domain, result] of parserResultsMap.entries()) {
        // Пропускаем домены с ошибками или без данных
        if (result.error || (!result.inn && !result.emails?.length)) {
          console.log(`[Domain Parser AutoSave] Skipping ${domain}: no INN or email`)
          skippedCount++
          continue
        }
        
        // Сохраняем только если есть ИНН И Email
        if (!result.inn || !result.emails || result.emails.length === 0) {
          console.log(`[Domain Parser AutoSave] Skipping ${domain}: missing INN or email`)
          skippedCount++
          continue
        }
        
        const rootDomain = extractRootDomain(domain).toLowerCase()
        
        // КРИТИЧНО: Проверяем существование в актуальном списке из БД
        const existing = currentSuppliers.get(rootDomain)
        
        if (existing) {
          console.log(`[Domain Parser AutoSave] Skipping ${domain}: already exists as supplier (ID: ${existing.id})`)
          skippedCount++
          continue
        }
        
        const inn = result.inn
        const email = result.emails[0]
        
        console.log(`[Domain Parser AutoSave] Auto-saving ${domain}: INN=${inn}, Email=${email}`)
        
        try {
          // ОБЯЗАТЕЛЬНО загружаем данные из Checko
          let checko: any = null
          try {
            console.log(`[Domain Parser AutoSave] Fetching Checko data for INN: ${inn}`)
            checko = await getCheckoData(inn, false)
            console.log(`[Domain Parser AutoSave] Checko data received:`, checko ? 'success' : 'null')
          } catch (e) {
            console.error(`[Domain Parser AutoSave] Failed to fetch Checko data:`, e)
            // Продолжаем без Checko данных
          }
          
          const baseName = (checko?.name && String(checko.name).trim()) || rootDomain
          
          // Создаем поставщика сразу со всеми данными из Checko
          const supplierData: any = {
            name: baseName,
            inn,
            email,
            domain: rootDomain,
            type: "supplier",
          }
          
          // Добавляем данные из Checko если есть
          if (checko) {
            supplierData.ogrn = checko.ogrn || null
            supplierData.kpp = checko.kpp || null
            supplierData.okpo = checko.okpo || null
            // Обрезаем до лимитов БД
            supplierData.companyStatus = checko.companyStatus ? checko.companyStatus.substring(0, 50) : null
            supplierData.registrationDate = checko.registrationDate || null
            supplierData.legalAddress = checko.legalAddress || null
            supplierData.address = checko.legalAddress || null
            supplierData.phone = checko.phone ? checko.phone.substring(0, 50) : null
            supplierData.website = checko.website || null
            supplierData.vk = checko.vk || null
            supplierData.telegram = checko.telegram || null
            // Числовые поля:确保传递 number | null
            supplierData.authorizedCapital = (checko.authorizedCapital !== undefined && checko.authorizedCapital !== null) ? Number(checko.authorizedCapital) : null
            supplierData.revenue = (checko.revenue !== undefined && checko.revenue !== null) ? Number(checko.revenue) : null
            supplierData.profit = (checko.profit !== undefined && checko.profit !== null) ? Number(checko.profit) : null
            supplierData.financeYear = (checko.financeYear !== undefined && checko.financeYear !== null) ? Number(checko.financeYear) : null
            supplierData.legalCasesCount = (checko.legalCasesCount !== undefined && checko.legalCasesCount !== null) ? Number(checko.legalCasesCount) : null
            supplierData.legalCasesSum = (checko.legalCasesSum !== undefined && checko.legalCasesSum !== null) ? Number(checko.legalCasesSum) : null
            supplierData.legalCasesAsPlaintiff = (checko.legalCasesAsPlaintiff !== undefined && checko.legalCasesAsPlaintiff !== null) ? Number(checko.legalCasesAsPlaintiff) : null
            supplierData.legalCasesAsDefendant = (checko.legalCasesAsDefendant !== undefined && checko.legalCasesAsDefendant !== null) ? Number(checko.legalCasesAsDefendant) : null
            supplierData.checkoData = checko.checkoData || null
          }
          
          const saved = await createSupplier(supplierData)
          
          console.log(`[Domain Parser AutoSave] Created supplier with Checko data:`, saved)
          
          // Добавляем в локальный список чтобы избежать повторного создания
          currentSuppliers.set(rootDomain, saved)
          
          toast.success(`✅ ${domain}: сохранен как поставщик`)
          savedCount++
          
          // Небольшая пауза между сохранениями
          await new Promise(resolve => setTimeout(resolve, 500))
          
        } catch (error) {
          console.error(`[Domain Parser AutoSave] Error saving ${domain}:`, error)
          toast.error(`Ошибка сохранения ${domain}`)
        }
      }
      
      console.log(`[Domain Parser AutoSave] Completed: saved=${savedCount}, skipped=${skippedCount}`)
      
      // Перезагружаем список поставщиков
      if (savedCount > 0) {
        try {
          const { suppliers } = await getSuppliers()
          const newMap = new Map<string, SupplierDTO>()
          for (const s of suppliers) {
            if (s.domain) {
              newMap.set(s.domain.toLowerCase(), s)
            }
          }
          suppliersByDomainRef.current = newMap
          invalidateSuppliersCache()
          console.log('[Domain Parser AutoSave] Suppliers list refreshed')
          toast.success(`Автосохранение завершено: ${savedCount} новых поставщиков`)
        } catch (e) {
          console.error('[Domain Parser AutoSave] Failed to refresh suppliers:', e)
        }
      }
    }
    
    autoSaveDomains()
  }, [runId, parserRunId, parserStatus, parserResultsMap])

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

      try {
        const nextMap = new Map<string, SupplierDTO>()
        for (const s of suppliersData.suppliers) {
          if ((s as any)?.domain) {
            const root = extractRootDomain(String((s as any).domain)).toLowerCase()
            nextMap.set(root, s as SupplierDTO)
          }
        }
        suppliersByDomainRef.current = nextMap
      } catch {
        // ignore
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

      // Fallback restore Comet state from DB process_log if localStorage is empty
      // (after refresh/new device) so user still sees results.
      try {
        const hasLocalCometRun = !!localStorage.getItem(`comet-run-${runId}`)
        const hasLocalCometResults = !!localStorage.getItem(`comet-results-${runId}`)
        const pl: any = (runData as any)?.processLog ?? (runData as any)?.process_log
        const runs: any = pl?.comet?.runs
        if ((!hasLocalCometRun || !hasLocalCometResults) && runs && typeof runs === "object") {
          const ids = Object.keys(runs).sort()
          const latestId = ids[ids.length - 1]
          const latest = latestId ? runs[latestId] : null
          if (latestId && latest) {
            if (!hasLocalCometRun) {
              setCometRunId(latestId)
            }
            if (!hasLocalCometResults && Array.isArray(latest.results)) {
              const map = new Map<string, CometExtractionResult>()
              for (const r of latest.results) {
                if (r?.domain) {
                  map.set(String(r.domain), r as CometExtractionResult)
                }
              }
              setCometResultsMap(map)
              setCometStatus({
                runId,
                cometRunId: latestId,
                status: (latest.status || "running") as any,
                processed: Number(latest.processed || 0),
                total: Number(latest.total || map.size),
                results: Array.from(map.values()),
              })
            }
          }
        }
      } catch (e) {
        // ignore restore errors
      }
      
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

  function openBlacklistDialog(domain: string) {
    setBlacklistDomain(domain)
    setBlacklistReason("")
    setBlacklistDialogOpen(true)
  }

  async function handleAddToBlacklist() {
    if (!blacklistDomain.trim()) {
      toast.error("Домен не указан")
      return
    }

    setAddingToBlacklist(true)
    try {
      // НОРМАЛИЗАЦИЯ: Используем extractRootDomain для нормализации домена
      // Это гарантирует, что домен будет добавлен в том же формате, что используется при фильтрации
      const normalizedDomain = extractRootDomain(blacklistDomain)
      await addToBlacklist({ 
        domain: normalizedDomain, 
        parsingRunId: runId || undefined,
        reason: blacklistReason.trim() || null
      })
      // Инвалидируем кэш blacklist ПЕРЕД перезагрузкой данных
      invalidateBlacklistCache()
      toast.success(`Домен "${normalizedDomain}" добавлен в blacklist`)
      // Закрываем модальное окно
      setBlacklistDialogOpen(false)
      setBlacklistDomain("")
      setBlacklistReason("")
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
    } finally {
      setAddingToBlacklist(false)
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
      // Для нового поставщика проверяем данные из Domain Parser
      const rootDomain = extractRootDomain(domain).toLowerCase()
      const parserResult = parserResultsMap.get(rootDomain) || parserResultsMap.get(domain)
      
      let prefillInn = ""
      let prefillEmail = ""
      
      if (parserResult && !parserResult.error) {
        prefillInn = parserResult.inn || ""
        prefillEmail = parserResult.emails && parserResult.emails.length > 0 ? parserResult.emails[0] : ""
        
        if (prefillInn || prefillEmail) {
          console.log(`[Domain Parser] Предзаполнение для ${domain}: INN=${prefillInn}, Email=${prefillEmail}`)
        }
      }
      
      setSupplierForm({
        name: "",
        inn: prefillInn,
        email: prefillEmail,
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
          // Обрезаем до лимитов БД
          companyStatus: supplierForm.companyStatus ? supplierForm.companyStatus.substring(0, 50) : null,
          registrationDate: supplierForm.registrationDate || null,
          legalAddress: supplierForm.legalAddress || null,
          phone: supplierForm.phone ? supplierForm.phone.substring(0, 50) : null,
          website: supplierForm.website || null,
          vk: supplierForm.vk || null,
          telegram: supplierForm.telegram || null,
          // Числовые поля:确保传递 number | null
          authorizedCapital: supplierForm.authorizedCapital !== undefined ? supplierForm.authorizedCapital : null,
          revenue: supplierForm.revenue !== undefined ? supplierForm.revenue : null,
          profit: supplierForm.profit !== undefined ? supplierForm.profit : null,
          financeYear: supplierForm.financeYear !== undefined ? supplierForm.financeYear : null,
          legalCasesCount: supplierForm.legalCasesCount !== undefined ? supplierForm.legalCasesCount : null,
          legalCasesSum: supplierForm.legalCasesSum !== undefined ? supplierForm.legalCasesSum : null,
          legalCasesAsPlaintiff: supplierForm.legalCasesAsPlaintiff !== undefined ? supplierForm.legalCasesAsPlaintiff : null,
          legalCasesAsDefendant: supplierForm.legalCasesAsDefendant !== undefined ? supplierForm.legalCasesAsDefendant : null,
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
          // Обрезаем до лимитов БД
          companyStatus: supplierForm.companyStatus ? supplierForm.companyStatus.substring(0, 50) : null,
          registrationDate: supplierForm.registrationDate || null,
          legalAddress: supplierForm.legalAddress || null,
          phone: supplierForm.phone ? supplierForm.phone.substring(0, 50) : null,
          website: supplierForm.website || null,
          vk: supplierForm.vk || null,
          telegram: supplierForm.telegram || null,
          // Числовые поля:确保传递 number | null
          authorizedCapital: supplierForm.authorizedCapital !== undefined ? supplierForm.authorizedCapital : null,
          revenue: supplierForm.revenue !== undefined ? supplierForm.revenue : null,
          profit: supplierForm.profit !== undefined ? supplierForm.profit : null,
          financeYear: supplierForm.financeYear !== undefined ? supplierForm.financeYear : null,
          legalCasesCount: supplierForm.legalCasesCount !== undefined ? supplierForm.legalCasesCount : null,
          legalCasesSum: supplierForm.legalCasesSum !== undefined ? supplierForm.legalCasesSum : null,
          legalCasesAsPlaintiff: supplierForm.legalCasesAsPlaintiff !== undefined ? supplierForm.legalCasesAsPlaintiff : null,
          legalCasesAsDefendant: supplierForm.legalCasesAsDefendant !== undefined ? supplierForm.legalCasesAsDefendant : null,
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

  // Функции для работы с выбранными доменами
  const toggleDomainSelection = async (domain: string) => {
    setSelectedDomains((prev) => {
      const newSet = new Set(prev)
      if (newSet.has(domain)) {
        newSet.delete(domain)
        // Удаляем результат из кэша при снятии выбора (опционально)
        // setInnResultsMap((prevMap) => {
        //   const newMap = new Map(prevMap)
        //   newMap.delete(domain)
        //   return newMap
        // })
      } else {
        newSet.add(domain)
        // Автоматически запускаем извлечение ИНН для выбранного домена
        if (!innResultsMap.has(domain) && !extractingDomains.has(domain)) {
          extractINNForDomain(domain)
        }
      }
      return newSet
    })
  }

  // Функция для извлечения ИНН для одного домена
  const extractINNForDomain = async (domain: string) => {
    // Проверяем кэш
    if (innResultsMap.has(domain)) {
      return
    }

    // Помечаем домен как обрабатываемый
    setExtractingDomains((prev) => new Set(prev).add(domain))

    try {
      const response = await extractINNBatch([domain])
      if (response.results && response.results.length > 0) {
        const result = response.results[0]
        // Сохраняем только если ИНН найден
        if (result.inn) {
          setInnResultsMap((prev) => {
            const newMap = new Map(prev)
            newMap.set(domain, result)
            return newMap
          })
        }
      }
    } catch (error) {
      // Обрабатываем разные типы ошибок
      if (error instanceof APIError) {
        if (error.status === 404) {
          // Endpoint не найден - возможно Backend не запущен
          console.warn(`[INN Extraction] Endpoint not found for ${domain}. Backend may not be running.`)
          // Не показываем toast для 404 - это техническая ошибка
        } else if (error.status === 503) {
          // Сервер недоступен
          toast.error(`Сервер недоступен. Проверьте, что Backend запущен.`)
        } else {
          // Другие ошибки
          toast.error(`Ошибка при извлечении ИНН для ${domain}: ${error.message}`)
        }
      } else {
        // Неожиданная ошибка
        console.error(`[INN Extraction] Unexpected error for ${domain}:`, error)
        toast.error(`Неожиданная ошибка при извлечении ИНН для ${domain}`)
      }
    } finally {
      // Убираем домен из списка обрабатываемых
      setExtractingDomains((prev) => {
        const newSet = new Set(prev)
        newSet.delete(domain)
        return newSet
      })
    }
  }

  const selectAllDomains = () => {
    const allDomains = groups.map((g) => g.domain)
    setSelectedDomains(new Set(allDomains))
  }

  const deselectAllDomains = () => {
    setSelectedDomains(new Set())
  }

  const copySelectedDomains = () => {
    const domainsArray = Array.from(selectedDomains)
    if (domainsArray.length === 0) {
      toast.error("Нет выбранных доменов")
      return
    }
    navigator.clipboard.writeText(domainsArray.join("\n"))
    toast.success(`Скопировано ${domainsArray.length} доменов`)
  }

  // Функция для запуска Domain Parser (получение данных)
  const handleDomainParser = async () => {
    if (selectedDomains.size === 0) {
      toast.error("Выберите хотя бы один домен")
      return
    }
    if (!runId) {
      toast.error("runId не найден")
      return
    }

    // Фильтруем домены: только те, которые НЕ являются поставщиками
    const domainsArray = Array.from(selectedDomains)
    const domainsWithoutSuppliers = domainsArray.filter(domain => {
      const rootDomain = extractRootDomain(domain).toLowerCase()
      const supplier = suppliersByDomainRef.current.get(rootDomain)
      return !supplier // Только домены без поставщиков
    })

    if (domainsWithoutSuppliers.length === 0) {
      toast.info("Все выбранные домены уже являются поставщиками")
      return
    }

    console.log('[Domain Parser] Starting for domains:', domainsWithoutSuppliers)
    setParserLoading(true)
    
    try {
      const resp = await startDomainParserBatch(runId, domainsWithoutSuppliers)
      setParserRunId(resp.parserRunId)
      toast.success(`Парсер запущен для ${domainsWithoutSuppliers.length} доменов`)
      
      if (domainsArray.length > domainsWithoutSuppliers.length) {
        const skipped = domainsArray.length - domainsWithoutSuppliers.length
        toast.info(`Пропущено ${skipped} доменов (уже поставщики)`)
      }
    } catch (error) {
      console.error('[Domain Parser] Error:', error)
      if (error instanceof APIError) {
        toast.error(`Ошибка парсера: ${error.message}`)
      } else {
        toast.error(error instanceof Error ? error.message : "Ошибка запуска парсера")
      }
    } finally {
      setParserLoading(false)
    }
  }

  const handleCometExtract = async () => {
    console.log('[Comet] Button clicked')
    console.log('[Comet] selectedDomains:', selectedDomains)
    console.log('[Comet] selectedDomains.size:', selectedDomains.size)
    
    if (selectedDomains.size === 0) {
      console.log('[Comet] No domains selected, showing error')
      toast.error("Выберите хотя бы один домен")
      return
    }
    if (!runId) {
      console.log('[Comet] No runId, showing error')
      toast.error("runId не найден")
      return
    }

    console.log('[Comet] Starting extraction...')
    setCometLoading(true)
    try {
      const domainsArray = Array.from(selectedDomains)
      console.log('[Comet] Domains array:', domainsArray)
      console.log('[Comet] Calling startCometExtractBatch...')
      const resp = await startCometExtractBatch(runId, domainsArray)
      console.log('[Comet] Response:', resp)
      setCometRunId(resp.cometRunId)
      toast.success(`Comet запущен для ${domainsArray.length} доменов`)
    } catch (error) {
      console.error('[Comet] Error:', error)
      if (error instanceof APIError) {
        toast.error(`Ошибка Comet: ${error.message}`)
      } else {
        toast.error(error instanceof Error ? error.message : "Ошибка запуска Comet")
      }
    } finally {
      setCometLoading(false)
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
              {/* Кнопки для работы с выбранными доменами */}
              {selectedDomains.size > 0 && (
                <div className="flex gap-2">
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={copySelectedDomains}
                    className="h-8 text-xs"
                  >
                    <Copy className="h-3 w-3 mr-1" />
                    Копировать ({selectedDomains.size})
                  </Button>
                  <Button
                    size="sm"
                    onClick={handleDomainParser}
                    disabled={parserLoading}
                    className="h-8 text-xs bg-blue-600 hover:bg-blue-700"
                  >
                    <FileSearch className="h-3 w-3 mr-1" />
                    Получить данные ({selectedDomains.size})
                  </Button>
                  <Button
                    size="sm"
                    onClick={handleCometExtract}
                    disabled={cometLoading}
                    className="h-8 text-xs bg-black hover:bg-black/90 text-white"
                  >
                    Comet ({selectedDomains.size})
                  </Button>
                </div>
              )}
            </div>
            {cometRunId && cometStatus && (
              <div className="text-xs text-muted-foreground mb-2">
                Comet: {cometStatus.status} — {cometStatus.processed}/{cometStatus.total}
              </div>
            )}
            {parserRunId && parserStatus && (
              <div className="text-xs mb-2">
                <div className="flex items-center gap-2">
                  <span className={`font-medium ${
                    parserStatus.status === 'running' ? 'text-blue-600' : 
                    parserStatus.status === 'completed' ? 'text-green-600' : 
                    'text-red-600'
                  }`}>
                    {parserStatus.status === 'running' ? '🔄 Получение данных...' : 
                     parserStatus.status === 'completed' ? '✅ Данные получены' : 
                     '❌ Ошибка'}
                  </span>
                  <span className="text-muted-foreground">
                    {parserStatus.processed}/{parserStatus.total} доменов
                  </span>
                </div>
                {parserStatus.status === 'running' && (
                  <div className="mt-1 w-full bg-gray-200 rounded-full h-2">
                    <div 
                      className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                      style={{ width: `${(parserStatus.processed / parserStatus.total) * 100}%` }}
                    />
                  </div>
                )}
              </div>
            )}
            {/* Кнопки выбора всех/снятия выбора */}
            <div className="flex items-center gap-2 mb-2">
              <Button
                size="sm"
                variant="ghost"
                onClick={selectAllDomains}
                className="h-7 text-xs"
              >
                Выбрать все
              </Button>
              <Button
                size="sm"
                variant="ghost"
                onClick={deselectAllDomains}
                className="h-7 text-xs"
              >
                Снять выбор
              </Button>
              {selectedDomains.size > 0 && (
                <span className="text-xs text-muted-foreground">
                  Выбрано: {selectedDomains.size}
                </span>
              )}
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
                        <div className="flex items-center gap-2 flex-1">
                          <Checkbox
                            checked={selectedDomains.has(group.domain)}
                            onCheckedChange={() => toggleDomainSelection(group.domain)}
                            onClick={(e) => e.stopPropagation()}
                          />
                          <AccordionTrigger className="hover:no-underline flex-1 py-1">
                            <div className="flex items-center gap-2 flex-1">
                              <span className="font-mono font-semibold text-sm">{group.domain}</span>
                            <Badge variant="outline" className="text-xs">{group.totalUrls} URL</Badge>
                            {/* Индикаторы Domain Parser результатов */}
                            {(() => {
                              const parserResult = parserResultsMap.get(group.domain)
                              if (!parserResult || parserResult.error) return null
                              return (
                                <>
                                  {parserResult.inn && (
                                    <span 
                                      className="ml-1 px-1.5 py-0.5 bg-blue-100 text-blue-700 rounded text-xs font-bold"
                                      title={`ИНН получен: ${parserResult.inn}`}
                                    >
                                      I
                                    </span>
                                  )}
                                  {parserResult.emails && parserResult.emails.length > 0 && (
                                    <span 
                                      className="ml-1 px-1.5 py-0.5 bg-green-100 text-green-700 rounded text-xs font-bold"
                                      title={`Email получен: ${parserResult.emails.join(', ')}`}
                                    >
                                      @
                                    </span>
                                  )}
                                </>
                              )
                            })()}
                            {/* Автоматически найденный ИНН - отображается желтым с ссылкой на пруф */}
                            {innResultsMap.get(group.domain)?.inn && (
                              <a
                                href={innResultsMap.get(group.domain)?.proof?.url || "#"}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="ml-1 px-2 py-0.5 bg-yellow-200 hover:bg-yellow-300 text-yellow-900 rounded text-xs font-semibold underline transition-colors"
                                title={`ИНН найден: ${innResultsMap.get(group.domain)?.inn}. Контекст: ${innResultsMap.get(group.domain)?.proof?.context || "нет"}`}
                                onClick={(e) => e.stopPropagation()}
                              >
                                ИНН: {innResultsMap.get(group.domain)?.inn}
                                <ExternalLink className="h-3 w-3 inline ml-1" />
                              </a>
                            )}
                            {/* Индикатор загрузки для домена, у которого идет извлечение */}
                            {extractingDomains.has(group.domain) && (
                              <span className="ml-1 text-xs text-muted-foreground animate-pulse">
                                Извлечение...
                              </span>
                            )}

                            {(() => {
                              const comet = cometResultsMap.get(group.domain)
                              if (!comet) return null
                              return (
                                <>
                                  {(comet.status === "running" || comet.status === "pending") && (
                                    <span className="ml-1 text-xs text-muted-foreground animate-pulse">Comet...</span>
                                  )}
                                  {comet.inn && (
                                    <span className="ml-1 px-2 py-0.5 bg-emerald-200 text-emerald-900 rounded text-xs font-semibold">
                                      Comet ИНН: {comet.inn}
                                    </span>
                                  )}
                                  {comet.email && (
                                    <span className="ml-1 px-2 py-0.5 bg-emerald-200 text-emerald-900 rounded text-xs font-semibold">
                                      Comet email: {comet.email}
                                    </span>
                                  )}
                                  {comet.sourceUrls && comet.sourceUrls.length > 0 && (
                                    <a
                                      href={comet.sourceUrls[0]}
                                      target="_blank"
                                      rel="noopener noreferrer"
                                      className="ml-1 px-2 py-0.5 bg-emerald-100 text-emerald-900 rounded text-xs font-semibold underline"
                                      onClick={(e) => e.stopPropagation()}
                                    >
                                      Источник <ExternalLink className="h-3 w-3 inline ml-1" />
                                    </a>
                                  )}
                                </>
                              )
                            })()}
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
                        </div>
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
                                onClick={() => openBlacklistDialog(group.domain)}
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

        {/* Логи извлечения данных (Domain Parser) */}
        {parserStatus && parserStatus.results && parserStatus.results.length > 0 && (
          <Card className="mt-6 border-2 border-green-500">
            <CardHeader>
              <CardTitle>Результаты извлечения данных (ИНН + Email)</CardTitle>
            </CardHeader>
            <CardContent>
              <Accordion type="multiple" className="w-full">
                {parserStatus.results.map((result, idx) => {
                  const hasData = result.inn || (result.emails && result.emails.length > 0)
                  const hasError = !!result.error
                  
                  return (
                    <AccordionItem key={`parser-${idx}`} value={`parser-${idx}`} className="border-b">
                      <AccordionTrigger className="hover:no-underline">
                        <div className="flex items-center gap-2 flex-1">
                          <span className={`w-3 h-3 rounded-full ${hasError ? 'bg-red-500' : hasData ? 'bg-green-500' : 'bg-gray-400'}`}></span>
                          <span className="font-mono font-semibold">{result.domain}</span>
                          {result.inn && (
                            <Badge className="bg-blue-600 text-white">
                              ИНН: {result.inn}
                            </Badge>
                          )}
                          {result.emails && result.emails.length > 0 && (
                            <Badge className="bg-green-600 text-white">
                              Email: {result.emails[0]}
                            </Badge>
                          )}
                          {hasError && (
                            <Badge variant="destructive">
                              Ошибка
                            </Badge>
                          )}
                          {!hasData && !hasError && (
                            <Badge variant="outline">
                              Не найдено
                            </Badge>
                          )}
                        </div>
                      </AccordionTrigger>
                      <AccordionContent>
                        <div className="pt-2 space-y-3">
                          {result.inn && (
                            <div className="text-sm">
                              <p className="font-semibold text-blue-700 mb-1">ИНН найден:</p>
                              <div className="p-2 bg-blue-50 rounded border border-blue-200">
                                <span className="font-mono text-lg">{result.inn}</span>
                              </div>
                            </div>
                          )}
                          
                          {result.emails && result.emails.length > 0 && (
                            <div className="text-sm">
                              <p className="font-semibold text-green-700 mb-1">Email найден:</p>
                              <div className="space-y-1">
                                {result.emails.map((email, emailIdx) => (
                                  <div key={emailIdx} className="p-2 bg-green-50 rounded border border-green-200">
                                    <a href={`mailto:${email}`} className="text-green-700 hover:underline">
                                      {email}
                                    </a>
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}
                          
                          {result.sourceUrls && result.sourceUrls.length > 0 && (
                            <div className="text-sm">
                              <p className="font-semibold text-muted-foreground mb-1">Источники ({result.sourceUrls.length}):</p>
                              <div className="space-y-1">
                                {result.sourceUrls.map((url, urlIdx) => (
                                  <div key={urlIdx} className="text-xs">
                                    <a
                                      href={url}
                                      target="_blank"
                                      rel="noopener noreferrer"
                                      className="text-blue-600 hover:underline flex items-center gap-1"
                                    >
                                      <span className="truncate">{url}</span>
                                      <ExternalLink className="h-3 w-3 flex-shrink-0" />
                                    </a>
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}
                          
                          {result.error && (
                            <div className="p-3 bg-red-50 border border-red-200 rounded-md">
                              <p className="text-sm text-red-800 font-semibold mb-1">Ошибка:</p>
                              <p className="text-sm text-red-700">{result.error}</p>
                            </div>
                          )}
                          
                          {!result.inn && !result.emails?.length && !result.error && (
                            <div className="p-3 bg-gray-50 border border-gray-200 rounded-md">
                              <p className="text-sm text-gray-700">
                                ℹ️ Данные не найдены на сайте. Возможно, сайт не содержит контактную информацию или она находится в защищенных разделах.
                              </p>
                            </div>
                          )}
                        </div>
                      </AccordionContent>
                    </AccordionItem>
                  )
                })}
              </Accordion>
              
              <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-md">
                <p className="text-sm text-blue-800">
                  <strong>Статистика:</strong> Обработано {parserStatus.processed} из {parserStatus.total} доменов
                  {parserStatus.results.filter(r => r.inn).length > 0 && (
                    <span> • ИНН найден: {parserStatus.results.filter(r => r.inn).length}</span>
                  )}
                  {parserStatus.results.filter(r => r.emails && r.emails.length > 0).length > 0 && (
                    <span> • Email найден: {parserStatus.results.filter(r => r.emails && r.emails.length > 0).length}</span>
                  )}
                </p>
              </div>
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
                <div className="pt-7 flex gap-2">
                  <CheckoInfoDialog
                    inn={supplierForm.inn}
                    onDataLoaded={(data) => {
                      setSupplierForm({ ...supplierForm, ...data })
                    }}
                  />
                  {supplierForm.inn && supplierForm.inn.length >= 10 && (
                    <Button
                      variant="outline"
                      size="default"
                      onClick={() => window.open(`https://checko.ru/search?query=${supplierForm.inn}`, '_blank')}
                      className="flex items-center gap-1"
                      title="Открыть на Checko.ru"
                    >
                      <ExternalLink className="h-4 w-4" />
                      Checko
                    </Button>
                  )}
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

      {/* Blacklist Dialog */}
      <Dialog open={blacklistDialogOpen} onOpenChange={setBlacklistDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Добавить домен в черный список</DialogTitle>
            <DialogDescription>
              Добавить "{blacklistDomain}" в blacklist?
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4">
            <div>
              <Label htmlFor="blacklist-reason">Причина добавления в черный список (необязательно)</Label>
              <Textarea
                id="blacklist-reason"
                placeholder="Укажите причину добавления домена в черный список..."
                value={blacklistReason}
                onChange={(e) => setBlacklistReason(e.target.value)}
                rows={4}
                className="mt-1"
              />
            </div>
          </div>

          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => {
                setBlacklistDialogOpen(false)
                setBlacklistDomain("")
                setBlacklistReason("")
              }}
            >
              Отмена
            </Button>
            <Button
              onClick={handleAddToBlacklist}
              disabled={addingToBlacklist}
              variant="destructive"
            >
              {addingToBlacklist ? "Добавление..." : "Добавить"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* INN Extraction Results Dialog */}
      <Dialog open={innExtractionDialogOpen} onOpenChange={setInnExtractionDialogOpen}>
        <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Результаты извлечения ИНН</DialogTitle>
            <DialogDescription>
              {innExtractionLoading
                ? `Обработка: ${innExtractionProgress.processed} из ${innExtractionProgress.total} доменов`
                : `Обработано: ${innExtractionProgress.processed} из ${innExtractionProgress.total} доменов`}
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4">
            {innExtractionLoading && (
              <div className="text-center py-4">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto"></div>
                <p className="mt-2 text-sm text-muted-foreground">Извлечение ИНН...</p>
              </div>
            )}

            {!innExtractionLoading && innExtractionResults.length > 0 && (
              <div className="space-y-2">
                <div className="grid grid-cols-1 gap-2">
                  {innExtractionResults.map((result, index) => (
                    <Card key={index} className="p-3">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-2">
                            <span className="font-mono font-semibold text-sm">{result.domain}</span>
                            {result.status === "success" && result.inn && (
                              <Badge className="bg-green-600">ИНН: {result.inn}</Badge>
                            )}
                            {result.status === "not_found" && (
                              <Badge variant="outline">ИНН не найден</Badge>
                            )}
                            {result.status === "error" && (
                              <Badge variant="destructive">Ошибка</Badge>
                            )}
                          </div>

                          {result.proof && (
                            <div className="mt-2 p-2 bg-muted rounded text-xs space-y-1">
                              <div>
                                <span className="font-semibold">URL:</span>{" "}
                                <a
                                  href={result.proof.url}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="text-blue-600 hover:underline"
                                >
                                  {result.proof.url}
                                  <ExternalLink className="h-3 w-3 inline ml-1" />
                                </a>
                              </div>
                              <div>
                                <span className="font-semibold">Метод:</span> {result.proof.method}
                                {result.proof.confidence && (
                                  <span className="ml-1">
                                    ({result.proof.confidence === "high" ? "высокая" : result.proof.confidence === "medium" ? "средняя" : "низкая"} уверенность)
                                  </span>
                                )}
                              </div>
                              <div>
                                <span className="font-semibold">Контекст:</span>
                                <div className="mt-1 p-2 bg-background rounded border">
                                  {result.proof.context}
                                </div>
                              </div>
                            </div>
                          )}

                          {result.error && (
                            <div className="mt-2 text-xs text-destructive">
                              Ошибка: {result.error}
                            </div>
                          )}

                          {result.processingTime && (
                            <div className="mt-1 text-xs text-muted-foreground">
                              Время обработки: {result.processingTime} мс
                            </div>
                          )}
                        </div>
                      </div>
                    </Card>
                  ))}
                </div>
              </div>
            )}

            {!innExtractionLoading && innExtractionResults.length === 0 && (
              <div className="text-center py-4 text-muted-foreground">
                Нет результатов для отображения
              </div>
            )}
          </div>

          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => {
                setInnExtractionDialogOpen(false)
                setInnExtractionResults([])
              }}
            >
              Закрыть
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}