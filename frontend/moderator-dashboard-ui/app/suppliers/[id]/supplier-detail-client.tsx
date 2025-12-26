"use client"

import { useState, useEffect, useMemo } from "react"
import { useRouter } from "next/navigation"
import { apiFetch, APIError } from "@/lib/api"
import { SupplierDTO, SupplierKeyword } from "@/lib/types"
import { formatCurrency, formatDate } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion"

export function SupplierDetailClient({ supplierId }: { supplierId: number }) {
  const router = useRouter()
  const [supplier, setSupplier] = useState<SupplierDTO | null>(null)
  const [keywords, setKeywords] = useState<SupplierKeyword[]>([])
  const [checkoData, setCheckoData] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadSupplier()
    loadKeywords()
  }, [supplierId])

  useEffect(() => {
    if (supplier?.checkoData) {
      try {
        const parsed = JSON.parse(supplier.checkoData)
        setCheckoData(parsed)
      } catch (e) {
        console.error("Failed to parse checkoData", e)
      }
    }
  }, [supplier])

  async function loadSupplier() {
    try {
      setLoading(true)
      const data = await apiFetch<SupplierDTO>(`/moderator/suppliers/${supplierId}`)
      setSupplier(data)
      setError(null)
    } catch (err) {
      if (err instanceof APIError) {
        setError(err.message)
      } else {
        setError("Ошибка загрузки поставщика")
      }
    } finally {
      setLoading(false)
    }
  }

  async function loadKeywords() {
    try {
      const data = await apiFetch<{ keywords: SupplierKeyword[] }>(
        `/moderator/suppliers/${supplierId}/keywords`
      )
      setKeywords(data.keywords)
    } catch (err) {
      console.error("Failed to load keywords", err)
    }
  }

  const relations = useMemo(() => {
    if (!checkoData) return null
    
    const founders = []
    if (checkoData["Учред"]) {
      founders.push(...(Array.isArray(checkoData["Учред"]) 
        ? checkoData["Учред"] 
        : [checkoData["Учред"]]))
    }
    
    const managers = []
    if (checkoData["Руковод"]) {
      managers.push(...(Array.isArray(checkoData["Руковод"]) 
        ? checkoData["Руковод"] 
        : [checkoData["Руковод"]]))
    }
    
    return {
      "Учредители": founders,
      "Руководители": managers,
    }
  }, [checkoData])

  const financeHistory = useMemo(() => {
    if (!checkoData?._finances) return []
    
    return Object.keys(checkoData._finances)
      .sort()
      .reverse()
      .map(year => ({
        year,
        data: checkoData._finances[year]
      }))
  }, [checkoData])

  if (loading) {
    return <div>Загрузка...</div>
  }

  if (error || !supplier) {
    return <div className="text-red-500">Ошибка: {error || "Поставщик не найден"}</div>
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">{supplier.name}</h1>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => router.push(`/suppliers/${supplierId}/edit`)}>
            Редактировать
          </Button>
          <Button variant="outline" onClick={() => router.push("/suppliers")}>
            Назад
          </Button>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Основная информация</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-sm text-muted-foreground">Тип</p>
              <Badge>{supplier.type}</Badge>
            </div>
            {supplier.companyStatus && (
              <div>
                <p className="text-sm text-muted-foreground">Статус</p>
                <Badge variant="outline">{supplier.companyStatus}</Badge>
              </div>
            )}
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-sm text-muted-foreground">ИНН</p>
              <p>{supplier.inn || "—"}</p>
            </div>
            {supplier.ogrn && (
              <div>
                <p className="text-sm text-muted-foreground">ОГРН</p>
                <p>{supplier.ogrn}</p>
              </div>
            )}
          </div>

          {supplier.email && (
            <div>
              <p className="text-sm text-muted-foreground">Email</p>
              <p>{supplier.email}</p>
            </div>
          )}

          {supplier.phone && (
            <div>
              <p className="text-sm text-muted-foreground">Телефон</p>
              <p>{supplier.phone}</p>
            </div>
          )}

          {supplier.website && (
            <div>
              <p className="text-sm text-muted-foreground">Сайт</p>
              <a href={supplier.website} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">
                {supplier.website}
              </a>
            </div>
          )}
        </CardContent>
      </Card>

      {supplier.revenue !== null && (
        <Card>
          <CardHeader>
            <CardTitle>Финансовые показатели</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-sm text-muted-foreground">Выручка</p>
                <p className="text-lg font-semibold">{formatCurrency(supplier.revenue)}</p>
              </div>
              {supplier.profit !== null && (
                <div>
                  <p className="text-sm text-muted-foreground">Прибыль</p>
                  <p className="text-lg font-semibold">{formatCurrency(supplier.profit)}</p>
                </div>
              )}
            </div>

            {financeHistory.length > 0 && (
              <Accordion>
                <AccordionItem value="finance-history">
                  <AccordionTrigger>
                    Динамика за {financeHistory.length} {financeHistory.length === 1 ? "год" : "лет"}
                  </AccordionTrigger>
                  <AccordionContent>
                    <div className="space-y-4">
                      {financeHistory.map(({ year, data }) => (
                        <Card key={year}>
                          <CardHeader>
                            <CardTitle className="text-lg">{year}</CardTitle>
                          </CardHeader>
                          <CardContent>
                            <div className="grid grid-cols-2 gap-4">
                              {data["2110"] && (
                                <div>
                                  <p className="text-sm text-muted-foreground">Выручка</p>
                                  <p>{formatCurrency(data["2110"])}</p>
                                </div>
                              )}
                              {data["2400"] && (
                                <div>
                                  <p className="text-sm text-muted-foreground">Прибыль</p>
                                  <p>{formatCurrency(data["2400"])}</p>
                                </div>
                              )}
                            </div>
                          </CardContent>
                        </Card>
                      ))}
                    </div>
                  </AccordionContent>
                </AccordionItem>
              </Accordion>
            )}
          </CardContent>
        </Card>
      )}

      {supplier.legalCasesCount !== null && supplier.legalCasesCount > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Судебные дела</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-sm text-muted-foreground">Всего дел</p>
                <p className="text-lg font-semibold">{supplier.legalCasesCount}</p>
              </div>
              {supplier.legalCasesSum !== null && (
                <div>
                  <p className="text-sm text-muted-foreground">Сумма исков</p>
                  <p className="text-lg font-semibold">{formatCurrency(supplier.legalCasesSum)}</p>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {relations && (relations["Учредители"].length > 0 || relations["Руководители"].length > 0) && (
        <Card>
          <CardHeader>
            <CardTitle>Связи компании</CardTitle>
          </CardHeader>
          <CardContent>
            <Accordion>
              {relations["Учредители"].length > 0 && (
                <AccordionItem value="founders">
                  <AccordionTrigger>
                    Учредители ({relations["Учредители"].length})
                  </AccordionTrigger>
                  <AccordionContent>
                    <div className="space-y-2">
                      {relations["Учредители"].map((founder: any, idx: number) => (
                        <Card key={idx}>
                          <CardContent className="pt-4">
                            <p>{founder["Наим"]}</p>
                            {founder["ИНН"] && <p className="text-sm text-muted-foreground">ИНН: {founder["ИНН"]}</p>}
                            {founder["ДоляПроц"] && <Badge>{founder["ДоляПроц"]}%</Badge>}
                          </CardContent>
                        </Card>
                      ))}
                    </div>
                  </AccordionContent>
                </AccordionItem>
              )}
              {relations["Руководители"].length > 0 && (
                <AccordionItem value="managers">
                  <AccordionTrigger>
                    Руководители ({relations["Руководители"].length})
                  </AccordionTrigger>
                  <AccordionContent>
                    <div className="space-y-2">
                      {relations["Руководители"].map((manager: any, idx: number) => (
                        <Card key={idx}>
                          <CardContent className="pt-4">
                            <p>{manager["Наим"]}</p>
                            {manager["Должность"] && <p className="text-sm text-muted-foreground">{manager["Должность"]}</p>}
                          </CardContent>
                        </Card>
                      ))}
                    </div>
                  </AccordionContent>
                </AccordionItem>
              )}
            </Accordion>
          </CardContent>
        </Card>
      )}

      {keywords.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Ключевые слова</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {keywords.map((kw, idx) => (
                <Badge key={idx} variant="outline">
                  {kw.keyword}
                </Badge>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}

