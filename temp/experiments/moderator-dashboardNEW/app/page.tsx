"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Label } from "@/components/ui/label"
import { Navigation } from "@/components/navigation"
import { getParsingRuns, getDomainsQueue, getBlacklist, getSuppliers, startParsing } from "@/lib/api-functions"
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

  useEffect(() => {
    loadDashboardData()
  }, [])

  async function loadDashboardData() {
    const [domainsData, suppliersData, runsData, blacklistData] = await Promise.all([
      getDomainsQueue({ limit: 1 }),
      getSuppliers({ limit: 1 }),
      getParsingRuns({ status: "running", limit: 1 }),
      getBlacklist({ limit: 1 }),
    ])

    const recentRunsData = await getParsingRuns({ limit: 10, sort: "created_at", order: "desc" })

    setStats({
      domainsInQueue: domainsData.total,
      newSuppliers: suppliersData.total,
      activeRuns: runsData.total,
      blacklistCount: blacklistData.total,
    })
    setRecentRuns(recentRunsData.runs)
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
      toast.success(`Парсинг запущен: ${result.keyword}`)
      setKeyword("")
      setDepth(5)
      setSource("both")
      loadDashboardData()
      router.push(`/parsing-runs/${result.runId}`)
    } catch (error) {
      toast.error("Ошибка запуска парсинга")
      console.error("Error starting parsing:", error)
    } finally {
      setLoading(false)
    }
  }

  const exampleKeywords = ["кирпич", "цемент", "труба", "арматура"]

  return (
    <div className="min-h-screen bg-background">
      <Navigation />

      <main className="container mx-auto px-6 py-12 max-w-7xl">
        {/* Новый парсинг */}
        <div className="mb-16">
          <h1 className="text-5xl font-bold mb-8 text-balance">Запустить новый парсинг</h1>

          <Card className="border-2">
            <CardContent className="pt-8 space-y-6">
              <div className="grid gap-6">
                <div>
                  <Label htmlFor="keyword" className="text-base mb-2 block">
                    Ключевое слово
                  </Label>
                  <Input
                    id="keyword"
                    placeholder="Введите ключевое слово..."
                    value={keyword}
                    onChange={(e) => setKeyword(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && handleStartParsing()}
                    className="text-lg h-14"
                  />
                  <div className="flex gap-2 flex-wrap mt-3">
                    <span className="text-sm text-muted-foreground">Примеры:</span>
                    {exampleKeywords.map((word) => (
                      <Button key={word} variant="outline" size="sm" onClick={() => setKeyword(word)}>
                        {word}
                      </Button>
                    ))}
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <Label htmlFor="depth" className="text-base mb-2 block">
                      Глубина парсинга
                    </Label>
                    <Input
                      id="depth"
                      type="number"
                      min={1}
                      max={10}
                      value={depth}
                      onChange={(e) => setDepth(Number.parseInt(e.target.value) || 1)}
                      className="text-lg h-14"
                    />
                    <p className="text-sm text-muted-foreground mt-2">От 1 до 10 страниц результатов</p>
                  </div>

                  <div>
                    <Label className="text-base mb-2 block">Источник</Label>
                    <div className="flex gap-2">
                      <Button
                        variant={source === "google" ? "default" : "outline"}
                        onClick={() => setSource("google")}
                        className="flex-1 h-14 text-base"
                      >
                        Google
                      </Button>
                      <Button
                        variant={source === "yandex" ? "default" : "outline"}
                        onClick={() => setSource("yandex")}
                        className="flex-1 h-14 text-base"
                      >
                        Яндекс
                      </Button>
                      <Button
                        variant={source === "both" ? "default" : "outline"}
                        onClick={() => setSource("both")}
                        className="flex-1 h-14 text-base"
                      >
                        Оба
                      </Button>
                    </div>
                  </div>
                </div>
              </div>

              <Button onClick={handleStartParsing} disabled={loading} size="lg" className="w-full h-14 text-lg">
                <Play className="mr-2 h-5 w-5" />
                Запустить парсинг
              </Button>
            </CardContent>
          </Card>
        </div>

        {/* Метрики */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-16">
          <Card>
            <CardHeader>
              <CardTitle className="text-sm font-medium text-muted-foreground uppercase tracking-wide">
                В очереди
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-7xl font-bold mb-2">{stats.domainsInQueue}</div>
              <div className="text-sm text-muted-foreground">доменов</div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-sm font-medium text-muted-foreground uppercase tracking-wide">Новые</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-7xl font-bold mb-2 text-green-600">{stats.newSuppliers}</div>
              <div className="text-sm text-muted-foreground">поставщиков</div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-sm font-medium text-muted-foreground uppercase tracking-wide">
                Активных
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-7xl font-bold mb-2 text-blue-600">{stats.activeRuns}</div>
              <div className="text-sm text-muted-foreground">парсингов</div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-sm font-medium text-muted-foreground uppercase tracking-wide">
                Blacklist
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-7xl font-bold mb-2 text-red-600">{stats.blacklistCount}</div>
              <div className="text-sm text-muted-foreground">доменов</div>
            </CardContent>
          </Card>
        </div>

        {/* Последние запуски */}
        <div className="mb-16">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-bold">Последние запуски</h2>
            <Button variant="ghost" onClick={() => router.push("/parsing-runs")}>
              Все запуски
              <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
          </div>

          {recentRuns.length === 0 ? (
            <Card>
              <CardContent className="py-12 text-center text-muted-foreground">Нет запусков парсинга</CardContent>
            </Card>
          ) : (
            <div className="flex gap-4 overflow-x-auto pb-4">
              {recentRuns.map((run) => (
                <Card
                  key={run.runId}
                  className="min-w-[280px] cursor-pointer hover:border-primary transition-colors"
                  onClick={() => router.push(`/parsing-runs/${run.runId}`)}
                >
                  <CardContent className="pt-6">
                    <div className="flex items-start justify-between mb-3">
                      <div className="font-semibold text-lg">{run.keyword}</div>
                      <Badge
                        variant={
                          run.status === "completed" ? "default" : run.status === "running" ? "outline" : "destructive"
                        }
                      >
                        {run.status === "completed" ? "✓" : run.status === "running" ? "⏳" : "✗"}
                      </Badge>
                    </div>
                    <div className="text-sm text-muted-foreground">
                      {new Date(run.createdAt).toLocaleDateString("ru-RU", {
                        day: "numeric",
                        month: "short",
                      })}
                    </div>
                    {run.resultsCount !== null && (
                      <div className="text-sm font-medium mt-2">{run.resultsCount} результатов</div>
                    )}
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </div>

        {/* CTA кнопки */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Button
            variant="outline"
            size="lg"
            className="h-24 text-lg justify-start bg-transparent"
            onClick={() => router.push("/parsing-runs")}
          >
            <TrendingUp className="mr-3 h-6 w-6" />
            Обработать очередь
          </Button>

          <Button
            variant="outline"
            size="lg"
            className="h-24 text-lg justify-start bg-transparent"
            onClick={() => router.push("/suppliers")}
          >
            <AlertCircle className="mr-3 h-6 w-6" />
            Проверить новых
          </Button>

          <Button
            variant="outline"
            size="lg"
            className="h-24 text-lg justify-start bg-transparent"
            onClick={() => router.push("/blacklist")}
          >
            <Ban className="mr-3 h-6 w-6" />
            Управление Blacklist
          </Button>
        </div>
      </main>
    </div>
  )
}
