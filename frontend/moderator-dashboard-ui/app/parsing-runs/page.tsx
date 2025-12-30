"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Checkbox } from "@/components/ui/checkbox"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Navigation } from "@/components/navigation"
import { getParsingRuns, deleteParsingRun, deleteParsingRunsBulk } from "@/lib/api"
import { toast } from "sonner"
import { Search, Trash2 } from "lucide-react"
import type { ParsingRunDTO } from "@/lib/types"

export default function ParsingRunsPage() {
  const router = useRouter()
  const [runs, setRuns] = useState<ParsingRunDTO[]>([])
  const [loading, setLoading] = useState(true)
  const [statusFilter, setStatusFilter] = useState<string>("all")
  const [searchQuery, setSearchQuery] = useState("")
  const [selectedRuns, setSelectedRuns] = useState<Set<string>>(new Set())

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
      console.error("Error loading runs:", error)
    } finally {
      setLoading(false)
    }
  }

  async function handleDelete(runId: string) {
    if (!confirm("Удалить этот запуск парсинга?")) return

    try {
      await deleteParsingRun(runId)
      toast.success("Запуск удален")
      setSelectedRuns(new Set())
      loadRuns()
    } catch (error) {
      toast.error("Ошибка удаления")
      console.error("Error deleting run:", error)
    }
  }

  async function handleBulkDelete() {
    if (selectedRuns.size === 0) return
    if (!confirm(`Удалить ${selectedRuns.size} запусков парсинга?`)) return

    try {
      const runIds = Array.from(selectedRuns)
      const result = await deleteParsingRunsBulk(runIds)
      toast.success(`Удалено ${result.deleted} из ${result.total} запусков`)
      setSelectedRuns(new Set())
      loadRuns()
    } catch (error) {
      toast.error("Ошибка массового удаления")
      console.error("Error bulk deleting runs:", error)
    }
  }

  function toggleSelectRun(runId: string) {
    const newSelected = new Set(selectedRuns)
    if (newSelected.has(runId)) {
      newSelected.delete(runId)
    } else {
      newSelected.add(runId)
    }
    setSelectedRuns(newSelected)
  }

  function toggleSelectAll() {
    if (selectedRuns.size === runs.length) {
      setSelectedRuns(new Set())
    } else {
      const allRunIds = runs.map((run) => run.runId || run.run_id || "").filter(Boolean)
      setSelectedRuns(new Set(allRunIds))
    }
  }

  const allSelected = runs.length > 0 && selectedRuns.size === runs.length
  const someSelected = selectedRuns.size > 0 && selectedRuns.size < runs.length

  function getStatusBadge(status: string) {
    if (status === "completed") return <Badge variant="default" className="bg-green-600 hover:bg-green-700 text-white">Завершен</Badge>
    if (status === "running") return <Badge variant="outline">Выполняется</Badge>
    return <Badge variant="destructive" className="bg-red-600 hover:bg-red-700 text-white">Ошибка</Badge>
  }

  return (
    <div className="min-h-screen bg-background">
      <Navigation />

      <main className="container mx-auto px-6 py-6 max-w-7xl">
        <h1 className="text-4xl font-bold mb-4">Запуски парсинга</h1>

        <Card className="mb-4">
          <div className="p-4">
            {selectedRuns.size > 0 && (
              <div className="mb-3 flex items-center justify-between bg-muted/50 p-3 rounded-md">
                <span className="text-sm text-muted-foreground">
                  Выбрано: {selectedRuns.size}
                </span>
                <Button variant="destructive" size="sm" onClick={handleBulkDelete}>
                  <Trash2 className="mr-2 h-4 w-4" />
                  Удалить выбранные
                </Button>
              </div>
            )}
            <div className="flex flex-col md:flex-row gap-2 mb-3">
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
                    <TableHead className="w-12">
                      <Checkbox
                        checked={allSelected}
                        onCheckedChange={toggleSelectAll}
                        onClick={(e) => e.stopPropagation()}
                      />
                    </TableHead>
                    <TableHead>Ключевое слово</TableHead>
                    <TableHead>Статус</TableHead>
                    <TableHead>Дата создания</TableHead>
                    <TableHead>Результаты</TableHead>
                    <TableHead className="text-right">Действия</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {runs.map((run) => {
                    const runId = run.runId || run.run_id || ""
                    const createdAt = run.createdAt || run.created_at || ""
                    const isSelected = selectedRuns.has(runId)
                    return (
                      <TableRow
                        key={runId}
                        className="cursor-pointer"
                        onClick={() => runId && router.push(`/parsing-runs/${runId}`)}
                      >
                        <TableCell onClick={(e) => e.stopPropagation()}>
                          <Checkbox
                            checked={isSelected}
                            onCheckedChange={() => toggleSelectRun(runId)}
                            onClick={(e) => e.stopPropagation()}
                          />
                        </TableCell>
                        <TableCell className="font-medium">{run.keyword}</TableCell>
                        <TableCell>{getStatusBadge(run.status)}</TableCell>
                        <TableCell>{createdAt ? new Date(createdAt).toLocaleString("ru-RU") : "—"}</TableCell>
                        <TableCell>{run.resultsCount !== null && run.resultsCount !== undefined ? `${run.resultsCount}` : "—"}</TableCell>
                        <TableCell className="text-right" onClick={(e) => e.stopPropagation()}>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={(e) => {
                              e.stopPropagation()
                              if (runId) handleDelete(runId)
                            }}
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </TableCell>
                      </TableRow>
                    )
                  })}
                </TableBody>
              </Table>
            )}
          </div>
        </Card>
      </main>
    </div>
  )
}
