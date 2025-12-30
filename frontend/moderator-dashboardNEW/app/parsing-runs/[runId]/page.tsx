"use client"

import { useState, useEffect } from "react"
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
import { Navigation } from "@/components/navigation"
import { getParsingRun, getDomainsQueue, getBlacklist, addToBlacklist, createSupplier } from "@/lib/api-functions"
import { groupByDomain, extractRootDomain } from "@/lib/utils-domain"
import { toast } from "sonner"
import { ArrowLeft, ExternalLink } from "lucide-react"
import type { ParsingDomainGroup } from "@/lib/types"

export default function ParsingRunDetailsPage({ params }: { params: { runId: string } }) {
  const router = useRouter()
  const [run, setRun] = useState<any>(null)
  const [groups, setGroups] = useState<ParsingDomainGroup[]>([])
  const [loading, setLoading] = useState(true)
  const [supplierDialogOpen, setSupplierDialogOpen] = useState(false)
  const [selectedDomain, setSelectedDomain] = useState("")
  const [supplierForm, setSupplierForm] = useState({
    name: "",
    inn: "",
    email: "",
    domain: "",
    address: "",
    type: "supplier" as "supplier" | "reseller",
  })

  useEffect(() => {
    loadData()
  }, [params.runId])

  async function loadData() {
    setLoading(true)
    try {
      const [runData, domainsData, blacklistData] = await Promise.all([
        getParsingRun(params.runId),
        getDomainsQueue({ parsingRunId: params.runId, limit: 1000 }),
        getBlacklist({ limit: 1000 }),
      ])

      setRun(runData)

      // Фильтрация blacklist
      const blacklistedDomains = new Set(blacklistData.entries.map((e) => e.domain))
      const filtered = domainsData.entries.filter((entry) => {
        const rootDomain = extractRootDomain(entry.domain)
        return !blacklistedDomains.has(rootDomain)
      })

      // Группировка
      const grouped = groupByDomain(filtered)
      setGroups(grouped)
    } catch (error) {
      toast.error("Ошибка загрузки данных")
      console.error("[v0] Error loading data:", error)
    } finally {
      setLoading(false)
    }
  }

  async function handleAddToBlacklist(domain: string) {
    if (!confirm(`Добавить "${domain}" в blacklist?`)) return

    try {
      await addToBlacklist({ domain, parsingRunId: params.runId })
      toast.success(`Домен "${domain}" добавлен в blacklist`)
      loadData()
    } catch (error) {
      toast.error("Ошибка добавления в blacklist")
      console.error("[v0] Error adding to blacklist:", error)
    }
  }

  function openSupplierDialog(domain: string, type: "supplier" | "reseller") {
    setSelectedDomain(domain)
    setSupplierForm({
      name: "",
      inn: "",
      email: "",
      domain: domain,
      address: "",
      type: type,
    })
    setSupplierDialogOpen(true)
  }

  async function handleCreateSupplier() {
    if (!supplierForm.name.trim()) {
      toast.error("Укажите название")
      return
    }

    try {
      await createSupplier(supplierForm)
      toast.success(`${supplierForm.type === "supplier" ? "Поставщик" : "Реселлер"} создан`)
      setSupplierDialogOpen(false)
      router.push("/suppliers")
    } catch (error) {
      toast.error("Ошибка создания")
      console.error("[v0] Error creating supplier:", error)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-background">
        <Navigation />
        <main className="container mx-auto px-6 py-12">
          <div className="text-center text-muted-foreground">Загрузка...</div>
        </main>
      </div>
    )
  }

  if (!run) {
    return (
      <div className="min-h-screen bg-background">
        <Navigation />
        <main className="container mx-auto px-6 py-12">
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

  return (
    <div className="min-h-screen bg-background">
      <Navigation />

      <main className="container mx-auto px-6 py-12 max-w-7xl">
        <Button variant="ghost" onClick={() => router.back()} className="mb-6">
          <ArrowLeft className="mr-2 h-4 w-4" />
          Назад
        </Button>

        {/* Summary */}
        <Card className="mb-8">
          <CardHeader>
            <div className="flex items-start justify-between">
              <div>
                <CardTitle className="text-4xl mb-4">{run.keyword}</CardTitle>
                <div className="flex items-center gap-4 text-sm text-muted-foreground">
                  <span>Создан: {new Date(run.createdAt).toLocaleString("ru-RU")}</span>
                  {run.finishedAt && <span>Завершен: {new Date(run.finishedAt).toLocaleString("ru-RU")}</span>}
                </div>
              </div>
              {getStatusBadge(run.status)}
            </div>
          </CardHeader>
          {run.resultsCount !== null && (
            <CardContent>
              <div className="text-5xl font-bold">{run.resultsCount}</div>
              <div className="text-sm text-muted-foreground">результатов найдено</div>
            </CardContent>
          )}
        </Card>

        {/* Results Accordion */}
        <Card>
          <CardHeader>
            <CardTitle>Результаты парсинга ({groups.length} доменов)</CardTitle>
          </CardHeader>
          <CardContent>
            {groups.length === 0 ? (
              <div className="text-center py-12 text-muted-foreground">
                Результаты не найдены или все домены в blacklist
              </div>
            ) : (
              <Accordion type="multiple" className="w-full">
                {groups.map((group) => (
                  <AccordionItem key={group.domain} value={group.domain}>
                    <AccordionTrigger>
                      <div className="flex items-center gap-3">
                        <span className="font-mono font-semibold text-lg">{group.domain}</span>
                        <Badge variant="outline">{group.totalUrls} URL</Badge>
                      </div>
                    </AccordionTrigger>
                    <AccordionContent>
                      <div className="space-y-4 pt-2">
                        {/* Список URL */}
                        <div className="space-y-2 max-h-60 overflow-y-auto">
                          {group.urls.map((urlEntry, idx) => (
                            <div key={idx} className="text-sm flex items-center gap-2 hover:bg-accent/50 p-2 rounded">
                              <a
                                href={urlEntry.url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="text-blue-600 hover:underline flex-1 flex items-center gap-2"
                              >
                                {urlEntry.url}
                                <ExternalLink className="h-3 w-3" />
                              </a>
                            </div>
                          ))}
                        </div>

                        {/* Действия */}
                        <div className="flex gap-3 pt-4 border-t">
                          <Button variant="destructive" size="sm" onClick={() => handleAddToBlacklist(group.domain)}>
                            <Badge className="mr-2 h-4 w-4" />
                            Add to Blacklist
                          </Button>
                          <Button
                            size="sm"
                            className="bg-green-600 hover:bg-green-700 text-white"
                            onClick={() => openSupplierDialog(group.domain, "supplier")}
                          >
                            Создать поставщика
                          </Button>
                          <Button
                            size="sm"
                            className="bg-purple-600 hover:bg-purple-700 text-white"
                            onClick={() => openSupplierDialog(group.domain, "reseller")}
                          >
                            Создать реселлера
                          </Button>
                        </div>
                      </div>
                    </AccordionContent>
                  </AccordionItem>
                ))}
              </Accordion>
            )}
          </CardContent>
        </Card>
      </main>

      {/* Supplier Dialog */}
      <Dialog open={supplierDialogOpen} onOpenChange={setSupplierDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{supplierForm.type === "supplier" ? "Создать поставщика" : "Создать реселлера"}</DialogTitle>
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
              <Label htmlFor="inn">ИНН</Label>
              <Input
                id="inn"
                value={supplierForm.inn}
                onChange={(e) => setSupplierForm({ ...supplierForm, inn: e.target.value })}
                placeholder="1234567890"
              />
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
            <Button variant="outline" onClick={() => setSupplierDialogOpen(false)}>
              Отмена
            </Button>
            <Button onClick={handleCreateSupplier}>Создать</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
