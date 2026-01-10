"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Navigation } from "@/components/navigation"
import { getParsingRuns, deleteParsingRun } from "@/lib/api-functions"
import { toast } from "sonner"
import { Search, Trash2 } from "lucide-react"
import type { ParsingRunDTO } from "@/lib/types"

export default function ParsingRunsPage() {
  const router = useRouter()
  const [runs, setRuns] = useState<ParsingRunDTO[]>([])
  const [loading, setLoading] = useState(true)
  const [statusFilter, setStatusFilter] = useState<string>("all")
  const [searchQuery, setSearchQuery] = useState("")

  useEffect(() => {
    loadRuns()
  }, [statusFilter])

  async function loadRuns() {
    setLoading(true)
    try {
      const params: any = { limit: 100, sort: "created_at", order: "desc" }
      if (statusFilter !== "all") {
        params.status = statusFilter
      }
      if (searchQuery) {
        params.keyword = searchQuery
      }

      const data = await getParsingRuns(params)
      setRuns(data.runs)
    } catch (error) {
      toast.error("Ошибка загрузки данных")
      console.error("[v0] Error loading runs:", error)
    } finally {
      setLoading(false)
    }
  }

  async function handleDelete(runId: string) {
    if (!confirm("Удалить этот запуск парсинга?")) return

    try {
      await deleteParsingRun(runId)
      toast.success("Запуск удален")
      loadRuns()
    } catch (error) {
      toast.error("Ошибка удаления")
      console.error("[v0] Error deleting run:", error)
    }
  }

  function getStatusBadge(status: string) {
    if (status === "completed") return <Badge variant="default">Завершен</Badge>
    if (status === "running") return <Badge variant="outline">Выполняется</Badge>
    return <Badge variant="destructive">Ошибка</Badge>
  }

  return (
    <div className="min-h-screen bg-background">
      <Navigation />

      <main className="container mx-auto px-6 py-12 max-w-7xl">
        <h1 className="text-4xl font-bold mb-8">Запуски парсинга</h1>

        <Card className="mb-8">
          <div className="p-6">
            <div className="flex flex-col md:flex-row gap-4 mb-6">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Поиск по ключевому слову..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && loadRuns()}
                  className="pl-10"
                />
              </div>
              <div className="flex gap-2">
                <Button variant={statusFilter === "all" ? "default" : "outline"} onClick={() => setStatusFilter("all")}>
                  Все
                </Button>
                <Button
                  variant={statusFilter === "running" ? "default" : "outline"}
                  onClick={() => setStatusFilter("running")}
                >
                  Выполняется
                </Button>
                <Button
                  variant={statusFilter === "completed" ? "default" : "outline"}
                  onClick={() => setStatusFilter("completed")}
                >
                  Завершен
                </Button>
                <Button
                  variant={statusFilter === "failed" ? "default" : "outline"}
                  onClick={() => setStatusFilter("failed")}
                >
                  Ошибка
                </Button>
              </div>
            </div>

            {loading ? (
              <div className="text-center py-12 text-muted-foreground">Загрузка...</div>
            ) : runs.length === 0 ? (
              <div className="text-center py-12 text-muted-foreground">Запуски не найдены</div>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Ключевое слово</TableHead>
                    <TableHead>Статус</TableHead>
                    <TableHead>Дата создания</TableHead>
                    <TableHead>Результаты</TableHead>
                    <TableHead className="text-right">Действия</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {runs.map((run) => (
                    <TableRow
                      key={run.runId}
                      className="cursor-pointer"
                      onClick={() => router.push(`/parsing-runs/${run.runId}`)}
                    >
                      <TableCell className="font-medium">{run.keyword}</TableCell>
                      <TableCell>{getStatusBadge(run.status)}</TableCell>
                      <TableCell>{new Date(run.createdAt).toLocaleString("ru-RU")}</TableCell>
                      <TableCell>{run.resultsCount !== null ? `${run.resultsCount}` : "—"}</TableCell>
                      <TableCell className="text-right">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={(e) => {
                            e.stopPropagation()
                            handleDelete(run.runId)
                          }}
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </div>
        </Card>
      </main>
    </div>
  )
}
