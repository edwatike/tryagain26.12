"use client"

import { useState, useMemo } from "react"
import { Card, CardContent, CardHeader } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Separator } from "@/components/ui/separator"

interface SupplierCardData {
  name: string
  inn: string
  registrationDate: string
  companyStatus: string
  finances: {
    [year: string]: {
      revenue: number
      profit: number
      changeFromPrevious?: string
    }
  }
  risks: {
    arbitration: {
      total: number
      asPlaintiff: number
      asDefendant: number
      sum: number
    }
    inspections: {
      total: number
      violations?: number
    }
    enforcements: {
      count: number
    }
  }
}

interface Verdict {
  level: "low" | "medium" | "high"
  explanation: string
  recommendation: string
}

function calculateVerdict(data: SupplierCardData): Verdict {
  const hasEnforcements = data.risks.enforcements.count > 0
  const hasLargeSum = data.risks.arbitration.sum > 1_000_000_000 // 1 млрд
  const hasManyCases = data.risks.arbitration.asPlaintiff > 0 || data.risks.arbitration.asDefendant > 0
  const hasManyInspections = data.risks.inspections.total > 5

  if (hasEnforcements || hasLargeSum) {
    return {
      level: "high",
      explanation:
        "из-за " +
        (hasEnforcements ? "исполнительных производств" : "") +
        (hasEnforcements && hasLargeSum ? " и " : "") +
        (hasLargeSum ? "большой суммы исков" : ""),
      recommendation: "рассмотреть добавление в blacklist",
    }
  } else if (hasManyInspections || hasManyCases) {
    return {
      level: "medium",
      explanation:
        "из-за " +
        (hasManyInspections ? "количества проверок" : "") +
        (hasManyInspections && hasManyCases ? " и " : "") +
        (hasManyCases ? "судебных споров" : ""),
      recommendation: "усиленный мониторинг",
    }
  } else {
    return {
      level: "low",
      explanation: "ограничений не выявлено",
      recommendation: "стандартный мониторинг",
    }
  }
}

function formatCurrency(value: number): string {
  if (value >= 1_000_000_000_000) {
    return `${(value / 1_000_000_000_000).toFixed(1)} трлн ₽`
  } else if (value >= 1_000_000_000) {
    return `${(value / 1_000_000_000).toFixed(1)} млрд ₽`
  } else if (value >= 1_000_000) {
    return `${(value / 1_000_000).toFixed(1)} млн ₽`
  }
  return `${value.toLocaleString("ru-RU")} ₽`
}

function formatDate(dateString: string): string {
  const date = new Date(dateString)
  return date.toLocaleDateString("ru-RU", { year: "numeric", month: "long", day: "numeric" })
}

export function SupplierCard({ data }: { data: SupplierCardData }) {
  const years = Object.keys(data.finances).sort()
  const [selectedYear, setSelectedYear] = useState<string>(
    years.length > 0 ? years[years.length - 1] : ""
  )
  const verdict = useMemo(() => calculateVerdict(data), [data])

  const selectedFinances = selectedYear && data.finances[selectedYear] 
    ? data.finances[selectedYear] 
    : null

  // Подготовка данных для графика
  const chartData = years.map((year) => ({
    year,
    revenue: data.finances[year].revenue,
    profit: data.finances[year].profit,
  }))

  const maxRevenue = chartData.length > 0 ? Math.max(...chartData.map((d) => d.revenue), 1) : 1
  const minRevenue = chartData.length > 0 ? Math.min(...chartData.map((d) => d.revenue), 0) : 0
  const maxProfit = chartData.length > 0 ? Math.max(...chartData.map((d) => d.profit), 1) : 1
  const minProfit = chartData.length > 0 ? Math.min(...chartData.map((d) => d.profit), 0) : 0

  const chartHeight = 80
  const chartWidth = 400
  const padding = 10

  // Нормализация точек для графика
  const revenuePoints = chartData.length > 1
    ? chartData
        .map((d, i) => {
          const x = padding + (i / (chartData.length - 1)) * (chartWidth - 2 * padding)
          const revenueRange = maxRevenue - minRevenue || 1
          const y = chartHeight - padding - ((d.revenue - minRevenue) / revenueRange) * (chartHeight - 2 * padding)
          return `${x},${y}`
        })
        .join(" ")
    : ""

  const profitPoints = chartData.length > 1
    ? chartData
        .map((d, i) => {
          const x = padding + (i / (chartData.length - 1)) * (chartWidth - 2 * padding)
          const profitRange = maxProfit - minProfit || 1
          const y = chartHeight - padding - ((d.profit - minProfit) / profitRange) * (chartHeight - 2 * padding)
          return `${x},${y}`
        })
        .join(" ")
    : ""

  const verdictColors = {
    low: "bg-green-100 text-green-800 border-green-200",
    medium: "bg-yellow-100 text-yellow-800 border-yellow-200",
    high: "bg-red-100 text-red-800 border-red-200",
  }

  const verdictLabels = {
    low: "низкий",
    medium: "средний",
    high: "высокий",
  }

  return (
    <Card className="w-full shadow-sm">
      <CardHeader className="space-y-3 pb-4">
        <div className="flex items-start justify-between gap-4">
          <div className="space-y-1">
            <h2 className="text-2xl font-semibold leading-tight text-balance">{data.name}</h2>
            <div className="flex flex-wrap items-center gap-2 text-sm text-muted-foreground">
              <span>ИНН: {data.inn}</span>
              <span>•</span>
              <span>{formatDate(data.registrationDate)}</span>
              <span>•</span>
              <span>{data.companyStatus}</span>
            </div>
          </div>
          <Badge variant="secondary" className="shrink-0">
            Поставщик
          </Badge>
        </div>
      </CardHeader>

      <Separator />

      <CardContent className="space-y-6 pt-6">
        {/* Блок "Финансовая история" */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold">Финансовая история</h3>
            {years.length > 0 && (
              <div className="flex items-center gap-2">
                <label htmlFor="year-select" className="text-sm text-muted-foreground">
                  Год:
                </label>
                <Select value={selectedYear} onValueChange={setSelectedYear}>
                  <SelectTrigger id="year-select" className="w-[100px]">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {years.map((year) => (
                      <SelectItem key={year} value={year}>
                        {year}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            )}
          </div>

          {/* График */}
          {chartData.length > 0 && (
            <div className="rounded-lg bg-muted/30 p-4">
              <svg viewBox={`0 0 ${chartWidth} ${chartHeight}`} className="w-full" style={{ maxHeight: "120px" }}>
                {/* Линия выручки */}
                {chartData.length > 1 && (
                  <polyline
                    points={revenuePoints}
                    fill="none"
                    stroke="hsl(var(--chart-2))"
                    strokeWidth="2.5"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                )}

                {/* Линия прибыли */}
                {chartData.length > 1 && (
                  <polyline
                    points={profitPoints}
                    fill="none"
                    stroke={chartData.every((d) => d.profit >= 0) ? "hsl(var(--chart-4))" : "hsl(var(--destructive))"}
                    strokeWidth="1.5"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                )}

                {/* Точки для выбранного года */}
                {chartData.length > 0 && chartData.map((d, i) => {
                  if (d.year === selectedYear) {
                    const x = padding + (i / Math.max(chartData.length - 1, 1)) * (chartWidth - 2 * padding)
                    const revenueRange = maxRevenue - minRevenue || 1
                    const profitRange = maxProfit - minProfit || 1
                    const yRevenue =
                      chartHeight -
                      padding -
                      ((d.revenue - minRevenue) / revenueRange) * (chartHeight - 2 * padding)
                    const yProfit =
                      chartHeight -
                      padding -
                      ((d.profit - minProfit) / profitRange) * (chartHeight - 2 * padding)

                    return (
                      <g key={i}>
                        <circle cx={x} cy={yRevenue} r="4" fill="hsl(var(--chart-2))" />
                        <circle
                          cx={x}
                          cy={yProfit}
                          r="3"
                          fill={d.profit >= 0 ? "hsl(var(--chart-4))" : "hsl(var(--destructive))"}
                        />
                      </g>
                    )
                  }
                  return null
                })}
              </svg>

              <div className="mt-3 flex items-center justify-center gap-6 text-xs text-muted-foreground">
                <div className="flex items-center gap-2">
                  <div className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: "hsl(var(--chart-2))" }} />
                  <span>Выручка</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="h-2 w-2 rounded-full" style={{ backgroundColor: "hsl(var(--chart-4))" }} />
                  <span>Прибыль</span>
                </div>
              </div>
            </div>
          )}

          {/* Детали выбранного года */}
          {selectedFinances && (
            <div className="rounded-lg bg-muted/30 p-4 space-y-2">
              <div className="grid gap-2 sm:grid-cols-3">
                <div>
                  <div className="text-xs text-muted-foreground">Выручка</div>
                  <div className="text-base font-semibold">{formatCurrency(selectedFinances.revenue)}</div>
                </div>
                <div>
                  <div className="text-xs text-muted-foreground">Прибыль</div>
                  <div className="text-base font-semibold">{formatCurrency(selectedFinances.profit)}</div>
                </div>
                <div>
                  <div className="text-xs text-muted-foreground">Изменение к прошлому году</div>
                  <div
                    className={`text-base font-semibold ${selectedFinances.changeFromPrevious?.startsWith("+") ? "text-green-600" : selectedFinances.changeFromPrevious?.startsWith("-") ? "text-red-600" : ""}`}
                  >
                    {selectedFinances.changeFromPrevious || "н/д"}
                  </div>
                </div>
              </div>
            </div>
          )}
          
          {!selectedFinances && years.length === 0 && (
            <div className="rounded-lg bg-muted/30 p-4 text-center text-sm text-muted-foreground">
              Финансовые данные отсутствуют
            </div>
          )}
        </div>

        <Separator />

        {/* Блок "Риски" */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold">Риски</h3>
            <div className="flex items-center gap-2">
              <span className="text-sm text-muted-foreground">Вердикт:</span>
              <Badge variant="outline" className={verdictColors[verdict.level]}>
                {verdictLabels[verdict.level]}
              </Badge>
            </div>
          </div>

          {/* Карточка "Арбитраж" */}
          <div className="rounded-lg bg-muted/30 p-4 space-y-2">
            <h4 className="text-sm font-semibold">Арбитраж</h4>
            <div className="space-y-1 text-sm">
              <div className="text-muted-foreground">
                Дел всего: <span className="font-medium text-foreground">{data.risks.arbitration.total}</span>, истец:{" "}
                <span className="font-medium text-foreground">{data.risks.arbitration.asPlaintiff}</span>, ответчик:{" "}
                <span className="font-medium text-foreground">{data.risks.arbitration.asDefendant}</span>
              </div>
              <div className={data.risks.arbitration.sum > 1_000_000_000 ? "font-semibold text-red-600" : ""}>
                Сумма исков: {formatCurrency(data.risks.arbitration.sum)}
              </div>
              {data.risks.arbitration.asPlaintiff === 0 &&
                data.risks.arbitration.asDefendant === 0 &&
                data.risks.arbitration.total > 0 && (
                  <div className="text-xs text-muted-foreground italic pt-1">
                    Судебные споры не зафиксированы как истец/ответчик, но есть агрегированная сумма исков
                  </div>
                )}
            </div>
          </div>

          {/* Карточка "Проверки и исполнительные производства" */}
          <div className="rounded-lg bg-muted/30 p-4 space-y-2">
            <h4 className="text-sm font-semibold">Проверки и исполнительные производства</h4>
            <div className="space-y-1 text-sm text-muted-foreground">
              <div>
                Проверок: <span className="font-medium text-foreground">{data.risks.inspections.total}</span>
                {data.risks.inspections.violations !== undefined && (
                  <span>
                    , нарушений:{" "}
                    <span className="font-medium text-foreground">{data.risks.inspections.violations}</span>
                  </span>
                )}
              </div>
              <div className={data.risks.enforcements.count > 0 ? "font-semibold text-red-600" : ""}>
                Исполнительных производств: {data.risks.enforcements.count}
              </div>
            </div>
          </div>

          {/* Объяснение вердикта */}
          <div className="text-sm text-muted-foreground">
            Риск {verdictLabels[verdict.level]} {verdict.explanation}
          </div>

          {/* Рекомендация модератора */}
          <div className="text-sm">
            <span className="text-muted-foreground">Рекомендуемое действие модератора:</span>{" "}
            <span className="font-medium">{verdict.recommendation}</span>
          </div>

          {/* Кнопки действий */}
          <div className="flex flex-wrap gap-2 pt-2">
            <Button variant="default" size="sm">
              Редактировать
            </Button>
            <Button variant="destructive" size="sm">
              Добавить в blacklist
            </Button>
            <Button variant="outline" size="sm">
              Ключевые слова
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
