"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"

interface CheckoInfoDialogProps {
  inn: string
  onDataLoaded: (data: any) => void
}

// Кэш для данных Checko (24 часа)
const CHECKO_CACHE_TTL = 24 * 60 * 60 * 1000

function getCachedData(inn: string): any | null {
  if (typeof window === 'undefined') return null
  
  try {
    const cacheKey = `checko_${inn}`
    const cached = localStorage.getItem(cacheKey)
    if (cached) {
      const data = JSON.parse(cached)
      // Проверка, что кэш не старше TTL
      if (Date.now() - data.timestamp < CHECKO_CACHE_TTL) {
        return data.updates
      } else {
        localStorage.removeItem(cacheKey)
      }
    }
  } catch (e) {
    console.warn("Failed to read Checko cache", e)
  }
  return null
}

function setCachedData(inn: string, updates: any) {
  if (typeof window === 'undefined') return
  
  try {
    const cacheKey = `checko_${inn}`
    localStorage.setItem(cacheKey, JSON.stringify({
      timestamp: Date.now(),
      updates
    }))
  } catch (e) {
    console.warn("Failed to save Checko cache", e)
  }
}

export function CheckoInfoDialog({ inn, onDataLoaded }: CheckoInfoDialogProps) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [open, setOpen] = useState(false)
  const [progress, setProgress] = useState(0)

  async function loadCheckoData() {
    if (!inn || inn.length < 10) {
      setError("Введите корректный ИНН (10 или 12 цифр)")
      return
    }

    // Проверяем кэш
    const cached = getCachedData(inn)
    if (cached) {
      onDataLoaded(cached)
      setOpen(false)
      return
    }

    const apiKey = process.env.NEXT_PUBLIC_CHECKO_API_KEY
    if (!apiKey) {
      setError("API ключ Checko не настроен")
      return
    }

    try {
      setLoading(true)
      setError(null)
      setProgress(0)

      // Загружаем данные из всех endpoints Checko API
      // Используем Promise.allSettled для обработки ошибок каждого запроса отдельно
      const endpoints = [
        `https://api.checko.ru/v2/company?key=${apiKey}&inn=${inn}`,
        `https://api.checko.ru/v2/finances?key=${apiKey}&inn=${inn}`,
        `https://api.checko.ru/v2/legal-cases?key=${apiKey}&inn=${inn}`,
        `https://api.checko.ru/v2/inspections?key=${apiKey}&inn=${inn}`,
        `https://api.checko.ru/v2/enforcements?key=${apiKey}&inn=${inn}`,
      ]

      // Загружаем с отслеживанием прогресса
      const fetchWithProgress = async (url: string, index: number) => {
        const response = await fetch(url)
        setProgress(((index + 1) / endpoints.length) * 100)
        return response
      }

      const fetchPromises = endpoints.map((url, index) => fetchWithProgress(url, index))
      const results = await Promise.allSettled(fetchPromises)

      // Проверяем основной запрос (company) - он обязателен
      if (results[0].status === 'rejected') {
        throw new Error(`Ошибка подключения к Checko API: ${results[0].reason?.message || 'Неизвестная ошибка'}`)
      }

      const company = results[0].value
      if (!company.ok) {
        if (company.status === 403) {
          throw new Error("API ключ Checko недействителен или истек")
        }
        if (company.status === 404) {
          throw new Error("Компания с таким ИНН не найдена в Checko")
        }
        const errorText = await company.text().catch(() => company.statusText)
        throw new Error(`Ошибка загрузки данных из Checko: ${company.status} ${errorText}`)
      }

      // Парсим успешные ответы, игнорируем ошибки в дополнительных запросах
      const companyData = await company.json()
      
      let financesData = { data: null }
      let legalData = { data: null }
      let inspectionsData = { data: null }
      let enforcementsData = { data: null }

      // Обрабатываем дополнительные данные (не критичны, если не загрузились)
      if (results[1].status === 'fulfilled' && results[1].value.ok) {
        try {
          financesData = await results[1].value.json()
        } catch (e) {
          console.warn("Failed to parse finances data", e)
        }
      }

      if (results[2].status === 'fulfilled' && results[2].value.ok) {
        try {
          legalData = await results[2].value.json()
        } catch (e) {
          console.warn("Failed to parse legal cases data", e)
        }
      }

      if (results[3].status === 'fulfilled' && results[3].value.ok) {
        try {
          inspectionsData = await results[3].value.json()
        } catch (e) {
          console.warn("Failed to parse inspections data", e)
        }
      }

      if (results[4].status === 'fulfilled' && results[4].value.ok) {
        try {
          enforcementsData = await results[4].value.json()
        } catch (e) {
          console.warn("Failed to parse enforcements data", e)
        }
      }

      // Формируем полные данные для сохранения
      const fullCheckoData = {
        ...companyData.data,
        _finances: financesData.data || {},
        _legal: legalData.data || {},
        _inspections: inspectionsData.data || {},
        _enforcements: enforcementsData.data || {},
      }

      // Извлекаем поля для формы
      const updates: any = {
        // Автозаполнение названия компании из Checko
        name: companyData.data?.["НаимПолн"] || companyData.data?.["НаимСокр"] || companyData.data?.["Наим"] || null,
        ogrn: companyData.data?.["ОГРН"] || null,
        kpp: companyData.data?.["КПП"] || null,
        okpo: companyData.data?.["ОКПО"] || null,
        companyStatus: companyData.data?.["Статус"]?.["Наим"] || null,
        registrationDate: companyData.data?.["ДатаРег"] || null,
        legalAddress: companyData.data?.["ЮрАдрес"] || null,
        phone: companyData.data?.["Контакты"]?.["Телефон"] || null,
        website: companyData.data?.["Контакты"]?.["ВебСайт"] || null,
        vk: companyData.data?.["Контакты"]?.["ВК"] || null,
        telegram: companyData.data?.["Контакты"]?.["Телеграм"] || null,
        authorizedCapital: companyData.data?.["УстКап"]?.["Сумма"] || null,
        checkoData: JSON.stringify(fullCheckoData),
      }

      // Сохраняем в кэш
      setCachedData(inn, updates)

      // Финансы (последний год)
      if (financesData.data) {
        const years = Object.keys(financesData.data).sort().reverse()
        if (years.length > 0) {
          const lastYear = years[0]
          const lastYearData = financesData.data[lastYear]
          updates.revenue = lastYearData?.["2110"] ? Math.round(lastYearData["2110"]) : null
          updates.profit = lastYearData?.["2400"] ? Math.round(lastYearData["2400"]) : null
          updates.financeYear = parseInt(lastYear) || null
        }
      }

      // Судебные дела
      if (legalData.data) {
        updates.legalCasesCount = legalData.data["ЗапВсего"] || null
        updates.legalCasesSum = legalData.data["ОбщСуммИск"] ? Math.round(legalData.data["ОбщСуммИск"]) : null
        updates.legalCasesAsPlaintiff = legalData.data["Истец"] || null
        updates.legalCasesAsDefendant = legalData.data["Ответчик"] || null
      }

      onDataLoaded(updates)
      setProgress(100)
      setOpen(false)
    } catch (err: any) {
      const errorMessage = err?.message || "Ошибка загрузки данных из Checko"
      setError(typeof errorMessage === 'string' ? errorMessage : JSON.stringify(errorMessage))
      console.error("Checko API error:", err)
      setProgress(0)
    } finally {
      setLoading(false)
    }
  }

  // Сбрасываем ошибку при открытии диалога
  const handleOpenChange = (newOpen: boolean) => {
    setOpen(newOpen)
    if (newOpen) {
      setError(null)
    }
  }

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogTrigger asChild>
        <Button variant="outline">
          Загрузить из Checko
        </Button>
      </DialogTrigger>
      <DialogContent className="resizable-dialog">
        <DialogHeader>
          <DialogTitle>Загрузка данных из Checko</DialogTitle>
          <DialogDescription>
            Загрузка данных о компании по ИНН: {inn || "не указан"}
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-4">
          {error && (
            <div className="text-red-500 text-sm p-2 bg-red-50 rounded border border-red-200">
              {error}
            </div>
          )}
          {!inn || inn.length < 10 ? (
            <div className="text-yellow-600 text-sm p-2 bg-yellow-50 rounded border border-yellow-200">
              ⚠️ Введите корректный ИНН (10 или 12 цифр) в поле выше для загрузки данных
            </div>
          ) : (
            <div className="text-green-600 text-sm p-2 bg-green-50 rounded border border-green-200">
              ✓ ИНН введен корректно. Нажмите "Загрузить данные" для получения информации из Checko.
            </div>
          )}
          
          {/* Прогресс-бар загрузки */}
          {loading && (
            <div className="w-full">
              <div className="flex justify-between text-xs text-muted-foreground mb-1">
                <span>Загрузка данных...</span>
                <span>{Math.round(progress)}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div 
                  className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${progress}%` }}
                />
              </div>
            </div>
          )}
          
          <Button
            onClick={loadCheckoData}
            disabled={loading || !inn || inn.length < 10}
            className="w-full"
          >
            {loading ? "Загрузка..." : "Загрузить данные"}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  )
}

