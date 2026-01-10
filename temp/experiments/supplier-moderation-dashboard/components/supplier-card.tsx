"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Separator } from "@/components/ui/separator"
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion"
import type { SupplierDTO, CheckoData } from "@/lib/types"
import {
  formatCurrency,
  formatDate,
  calculatePercentageChange,
  getRiskLevel,
  getRiskColor,
  getRiskEmoji,
} from "@/lib/format-utils"
import { Edit, Ban, Tag, Globe, Phone, MapPin, Mail, Star } from "lucide-react"
import Link from "next/link"
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from "recharts"

interface SupplierCardProps {
  supplier: SupplierDTO
}

export function SupplierCard({ supplier }: SupplierCardProps) {
  // Parse checkoData if available
  const checkoData: CheckoData | null = supplier.checkoData ? JSON.parse(supplier.checkoData) : null

  const riskLevel = getRiskLevel(supplier.legalCasesAsPlaintiff ?? 0, supplier.legalCasesAsDefendant ?? 0)

  // Prepare financial chart data
  const chartData = prepareChartData(supplier, checkoData)

  // Get previous year data for comparison
  const previousYear = supplier.financeYear ? supplier.financeYear - 1 : null
  const previousYearData = previousYear && checkoData?._finances?.[previousYear.toString()]
  const revenueChange = previousYearData?.["2110"]
    ? calculatePercentageChange(supplier.revenue ?? 0, previousYearData["2110"])
    : ""
  const profitChange = previousYearData?.["2400"]
    ? calculatePercentageChange(supplier.profit ?? 0, previousYearData["2400"])
    : ""

  return (
    <Card className="w-full shadow-lg transition-all duration-300 hover:shadow-xl">
      {/* SECTION 1: HEADER */}
      <CardHeader className="space-y-4">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="flex flex-wrap items-center gap-3">
            <CardTitle className="text-2xl font-bold md:text-3xl">{supplier.name}</CardTitle>
            <Badge
              variant={supplier.type === "supplier" ? "default" : "secondary"}
              className={
                supplier.type === "supplier" ? "bg-green-500 hover:bg-green-600" : "bg-purple-500 hover:bg-purple-600"
              }
            >
              {supplier.type === "supplier" ? "Поставщик" : "Реселлер"}
            </Badge>
            {checkoData?.rating && (
              <Badge variant="outline" className="gap-1">
                <Star className="h-3 w-3 fill-yellow-400 text-yellow-400" />+{checkoData.rating}
              </Badge>
            )}
          </div>
        </div>

        {/* Metadata */}
        <div className="flex flex-wrap items-center gap-4 text-sm text-muted-foreground">
          {supplier.legalAddress && (
            <div className="flex items-center gap-1">
              <MapPin className="h-4 w-4" />
              <span className="line-clamp-1">{supplier.legalAddress}</span>
            </div>
          )}
          {supplier.phone && (
            <a href={`tel:${supplier.phone}`} className="flex items-center gap-1 hover:text-foreground">
              <Phone className="h-4 w-4" />
              <span>{supplier.phone}</span>
            </a>
          )}
          {supplier.website && (
            <a
              href={supplier.website}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1 hover:text-foreground"
            >
              <Globe className="h-4 w-4" />
              <span>Сайт</span>
            </a>
          )}
          {supplier.vk && (
            <a
              href={supplier.vk}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1 hover:text-foreground"
            >
              <span className="font-semibold">VK</span>
            </a>
          )}
          {supplier.telegram && (
            <a
              href={supplier.telegram}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1 hover:text-foreground"
            >
              <span className="font-semibold">TG</span>
            </a>
          )}
        </div>

        {supplier.email && (
          <div className="flex items-center gap-1 text-sm text-muted-foreground">
            <Mail className="h-4 w-4" />
            <a href={`mailto:${supplier.email}`} className="hover:text-foreground">
              {supplier.email}
            </a>
          </div>
        )}

        {/* Company details */}
        <div className="grid grid-cols-2 gap-2 text-xs text-muted-foreground md:grid-cols-4">
          {supplier.inn && (
            <div>
              <span className="font-medium">ИНН:</span> {supplier.inn}
            </div>
          )}
          {supplier.ogrn && (
            <div>
              <span className="font-medium">ОГРН:</span> {supplier.ogrn}
            </div>
          )}
          {supplier.kpp && (
            <div>
              <span className="font-medium">КПП:</span> {supplier.kpp}
            </div>
          )}
          {supplier.registrationDate && (
            <div>
              <span className="font-medium">Дата рег.:</span> {formatDate(supplier.registrationDate)}
            </div>
          )}
        </div>
      </CardHeader>

      <CardContent className="space-y-6">
        {/* SECTION 2: FINANCES */}
        <div className="space-y-4">
          <div className="flex flex-wrap items-baseline gap-4">
            <div>
              <span className="text-sm text-muted-foreground">Выручка: </span>
              <span className="text-lg font-bold">{formatCurrency(supplier.revenue)}</span>
              {revenueChange && (
                <span className={`ml-2 text-sm ${revenueChange.startsWith("+") ? "text-green-600" : "text-red-600"}`}>
                  ({revenueChange})
                </span>
              )}
            </div>
            <div>
              <span className="text-sm text-muted-foreground">Прибыль: </span>
              <span className="text-lg font-bold">{formatCurrency(supplier.profit)}</span>
              {profitChange && (
                <span className={`ml-2 text-sm ${profitChange.startsWith("+") ? "text-green-600" : "text-red-600"}`}>
                  ({profitChange})
                </span>
              )}
            </div>
          </div>

          {chartData.length > 1 && (
            <Accordion type="single" collapsible className="w-full">
              <AccordionItem value="finances" className="border-none">
                <AccordionTrigger className="py-2 text-sm hover:no-underline">
                  <span className="flex items-center gap-2">
                    📊 Финансовая история ({chartData.length} {chartData.length === 1 ? "год" : "года"})
                  </span>
                </AccordionTrigger>
                <AccordionContent>
                  <ResponsiveContainer width="100%" height={250}>
                    <LineChart data={chartData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="year" />
                      <YAxis />
                      <Tooltip formatter={(value: number) => formatCurrency(value)} />
                      <Legend />
                      <Line type="monotone" dataKey="revenue" stroke="#3B82F6" strokeWidth={2} name="Выручка" />
                      <Line type="monotone" dataKey="profit" stroke="#10B981" strokeWidth={2} name="Прибыль" />
                    </LineChart>
                  </ResponsiveContainer>
                </AccordionContent>
              </AccordionItem>
            </Accordion>
          )}
        </div>

        <Separator />

        {/* SECTION 3: RISKS */}
        <div className="space-y-3">
          <h3 className="font-semibold">Риски</h3>

          <div className={`rounded-lg p-3 ${getRiskColor(riskLevel)}`}>
            <div className="flex items-center gap-2">
              <span className="text-lg">{getRiskEmoji(riskLevel)}</span>
              <div className="flex-1">
                <span className="font-medium">Арбитраж: </span>
                <span>
                  Истец {supplier.legalCasesAsPlaintiff ?? 0} | Ответчик {supplier.legalCasesAsDefendant ?? 0}
                </span>
              </div>
            </div>
            {supplier.legalCasesSum && supplier.legalCasesSum > 0 && (
              <div className="ml-7 text-sm">Общая сумма исков: {formatCurrency(supplier.legalCasesSum)}</div>
            )}
          </div>

          {checkoData?._inspections && (
            <div className="rounded-lg bg-yellow-50 p-3 text-yellow-600">
              <div className="flex items-center gap-2">
                <span className="text-lg">🟡</span>
                <div>
                  <span className="font-medium">Проверки: </span>
                  <span>
                    {checkoData._inspections.total ?? 0}
                    {checkoData._inspections.violations ? (
                      <span className="ml-1">({checkoData._inspections.violations} нарушений)</span>
                    ) : null}
                  </span>
                </div>
              </div>
            </div>
          )}

          {checkoData?._enforcements && checkoData._enforcements.count && checkoData._enforcements.count > 0 && (
            <div className="rounded-lg bg-red-50 p-3 text-red-600">
              <div className="flex items-center gap-2">
                <span className="text-lg">🔴</span>
                <div>
                  <span className="font-medium">Исп. производства: </span>
                  <span>{checkoData._enforcements.count} долг</span>
                </div>
              </div>
            </div>
          )}
        </div>

        <Separator />

        {/* SECTION 4: FOUNDERS */}
        {checkoData?.Учред && checkoData.Учред.length > 0 && (
          <>
            <div className="space-y-3">
              <h3 className="font-semibold">Учредители</h3>
              <div className="space-y-2">
                {checkoData.Учред.map((founder, index) => (
                  <div key={index} className="flex items-center gap-2 rounded-md bg-muted/50 p-2 text-sm">
                    <span className="text-lg">👤</span>
                    <span>
                      {founder.name}
                      {founder.share && <span className="ml-2 text-muted-foreground">({founder.share}%)</span>}
                    </span>
                  </div>
                ))}
              </div>
            </div>
            <Separator />
          </>
        )}

        {/* SECTION 5: ACTIONS */}
        <div className="flex flex-wrap gap-3">
          <Button asChild variant="default" className="gap-2">
            <Link href={`/suppliers/${supplier.id}/edit`}>
              <Edit className="h-4 w-4" />
              Редактировать
            </Link>
          </Button>
          <Button variant="destructive" className="gap-2">
            <Ban className="h-4 w-4" />
            Blacklist
          </Button>
          <Button asChild variant="outline" className="gap-2 bg-transparent">
            <Link href={`/suppliers/${supplier.id}/keywords`}>
              <Tag className="h-4 w-4" />
              Ключевые слова
            </Link>
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}

// Helper function to prepare chart data
function prepareChartData(supplier: SupplierDTO, checkoData: CheckoData | null) {
  const data: { year: string; revenue: number; profit: number }[] = []

  // Add historical data from checkoData
  if (checkoData?._finances) {
    const years = Object.keys(checkoData._finances).sort()
    years.forEach((year) => {
      const yearData = checkoData._finances![year]
      data.push({
        year,
        revenue: yearData["2110"] ?? 0,
        profit: yearData["2400"] ?? 0,
      })
    })
  }

  // Add current year data if not already included
  if (supplier.financeYear) {
    const currentYearExists = data.some((d) => d.year === supplier.financeYear!.toString())
    if (!currentYearExists) {
      data.push({
        year: supplier.financeYear.toString(),
        revenue: supplier.revenue ?? 0,
        profit: supplier.profit ?? 0,
      })
    }
  }

  return data.sort((a, b) => a.year.localeCompare(b.year))
}
