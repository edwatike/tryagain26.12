"use client"

import { useState } from "react"
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

export function CheckoInfoDialog({ inn, onDataLoaded }: CheckoInfoDialogProps) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [open, setOpen] = useState(false)

  async function loadCheckoData() {
    if (!inn || inn.length < 10) {
      setError("Введите корректный ИНН (10 или 12 цифр)")
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

      // Загружаем данные из всех endpoints Checko API
      const [company, finances, legal, inspections, enforcements] = await Promise.all([
        fetch(`https://api.checko.ru/v2/company?key=${apiKey}&inn=${inn}`),
        fetch(`https://api.checko.ru/v2/finances?key=${apiKey}&inn=${inn}`),
        fetch(`https://api.checko.ru/v2/legal-cases?key=${apiKey}&inn=${inn}`),
        fetch(`https://api.checko.ru/v2/inspections?key=${apiKey}&inn=${inn}`),
        fetch(`https://api.checko.ru/v2/enforcements?key=${apiKey}&inn=${inn}`),
      ])

      if (!company.ok) {
        if (company.status === 403) {
          throw new Error("API ключ Checko недействителен или истек")
        }
        throw new Error(`Ошибка загрузки данных: ${company.statusText}`)
      }

      const companyData = await company.json()
      const financesData = await finances.json()
      const legalData = await legal.json()
      const inspectionsData = await inspections.json()
      const enforcementsData = await enforcements.json()

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
      setOpen(false)
    } catch (err: any) {
      setError(err.message || "Ошибка загрузки данных из Checko")
    } finally {
      setLoading(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button variant="outline" disabled={!inn || inn.length < 10}>
          Загрузить из Checko
        </Button>
      </DialogTrigger>
      <DialogContent className="resizable-dialog">
        <DialogHeader>
          <DialogTitle>Загрузка данных из Checko</DialogTitle>
          <DialogDescription>
            Загрузка данных о компании по ИНН: {inn}
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-4">
          {error && (
            <div className="text-red-500 text-sm">{error}</div>
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

