"use client"

import { useState, useEffect } from "react"
import { useRouter, useSearchParams } from "next/navigation"
import { apiFetch, APIError } from "@/lib/api"
import { ParsingRunDTO } from "@/lib/types"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog"
import { toast } from "sonner"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"

export default function ParsingRunsPage() {
  const router = useRouter()
  const searchParams = useSearchParams()
  
  const [runs, setRuns] = useState<ParsingRunDTO[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [total, setTotal] = useState(0)
  const [limit, setLimit] = useState(100)
  const [offset, setOffset] = useState(0)
  
  // Фильтры и поиск
  const [statusFilter, setStatusFilter] = useState<string>("all")
  const [keywordSearch, setKeywordSearch] = useState<string>("")
  const [sortBy, setSortBy] = useState<string>("created_at")
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc")
  
  // Массовое удаление
  const [selectedRuns, setSelectedRuns] = useState<Set<string>>(new Set())
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [deleteRunId, setDeleteRunId] = useState<string | null>(null)

  useEffect(() => {
    const page = parseInt(searchParams.get("page") || "1", 10)
    const status = searchParams.get("status") || "all"
    const keyword = searchParams.get("keyword") || ""
    const sort = searchParams.get("sort") || "created_at"
    const order = (searchParams.get("order") || "desc") as "asc" | "desc"
    
    setStatusFilter(status)
    setKeywordSearch(keyword)
    setSortBy(sort)
    setSortOrder(order)
    setOffset((page - 1) * limit)
    
    loadRuns(page, status, keyword, sort, order)
  }, [searchParams])

  async function loadRuns(
    page: number = 1,
    status: string = statusFilter,
    keyword: string = keywordSearch,
    sort: string = sortBy,
    order: "asc" | "desc" = sortOrder
  ) {
    try {
      setLoading(true)
      const offset = (page - 1) * limit
      const params = new URLSearchParams({
        limit: limit.toString(),
        offset: offset.toString(),
      })
      
      if (status !== "all") {
        params.append("status", status)
      }
      if (keyword) {
        params.append("keyword", keyword)
      }
      if (sort) {
        params.append("sort", sort)
        params.append("order", order)
      }
      
      const data = await apiFetch<{ runs: ParsingRunDTO[]; total: number; limit: number; offset: number }>(
        `/parsing/runs?${params.toString()}`
      )
      
      const validRuns = (data.runs || []).filter((run) => run && (run.runId || run.run_id))
      
      setRuns(validRuns)
      setTotal(data.total)
      setError(null)
    } catch (err) {
      console.error("Error loading parsing runs:", err)
      if (err instanceof APIError) {
        setError(err.message)
        toast.error(`Ошибка загрузки: ${err.message}`)
      } else {
        const errorMsg = "Ошибка загрузки запусков парсинга"
        setError(errorMsg)
        toast.error(errorMsg)
      }
      setRuns([])
    } finally {
      setLoading(false)
    }
  }

  async function handleDelete(runId: string) {
    const originalRuns = [...runs]
    const runToDelete = runs.find(r => (r.runId || r.run_id) === runId)
    
    // Оптимистичное обновление
    setRuns(runs.filter(r => (r.runId || r.run_id) !== runId))
    setTotal(total - 1)
    setDeleteDialogOpen(false)
    setDeleteRunId(null)

    try {
      await apiFetch(`/parsing/runs/${runId}`, {
        method: "DELETE",
      })
      toast.success(`Запуск парсинга "${runToDelete?.keyword || runId}" успешно удален`)
      // Перезагружаем список для синхронизации
      await loadRuns()
    } catch (err) {
      // Откат при ошибке
      setRuns(originalRuns)
      setTotal(total)
      console.error("Error deleting parsing run:", err)
      if (err instanceof APIError) {
        toast.error(`Ошибка удаления: ${err.message}`)
      } else {
        toast.error("Ошибка удаления запуска парсинга")
      }
    }
  }

  async function handleBulkDelete() {
    if (selectedRuns.size === 0) {
      toast.warning("Выберите записи для удаления")
      return
    }

    const originalRuns = [...runs]
    const runIds = Array.from(selectedRuns)
    const selectedCount = selectedRuns.size
    
    // Оптимистичное обновление
    setRuns(runs.filter(r => {
      const id = r.runId || r.run_id
      return !id || !selectedRuns.has(id)
    }))
    setTotal(total - selectedCount)
    setSelectedRuns(new Set())
    setDeleteDialogOpen(false)

    try {
      // Используем bulk endpoint
      await apiFetch(`/parsing/runs/bulk`, {
        method: "DELETE",
        body: JSON.stringify(runIds),
      })
      toast.success(`Успешно удалено ${selectedCount} запусков парсинга`)
      await loadRuns()
    } catch (err) {
      // Откат при ошибке
      setRuns(originalRuns)
      setTotal(total)
      console.error("Error bulk deleting parsing runs:", err)
      toast.error("Ошибка массового удаления")
    }
  }

  function handleFilterChange() {
    const params = new URLSearchParams()
    params.set("page", "1")
    if (statusFilter !== "all") params.set("status", statusFilter)
    if (keywordSearch) params.set("keyword", keywordSearch)
    if (sortBy) {
      params.set("sort", sortBy)
      params.set("order", sortOrder)
    }
    router.push(`/parsing-runs?${params.toString()}`)
  }

  function handleSort(column: string) {
    // Маппинг frontend колонок на backend поля
    const columnMap: Record<string, string> = {
      "runId": "run_id",
      "keyword": "keyword",
      "status": "status",
      "createdAt": "created_at",
    }
    
    const backendColumn = columnMap[column] || column
    const newOrder = sortBy === backendColumn && sortOrder === "desc" ? "asc" : "desc"
    setSortBy(backendColumn)
    setSortOrder(newOrder)
    const params = new URLSearchParams(searchParams.toString())
    params.set("sort", backendColumn)
    params.set("order", newOrder)
    router.push(`/parsing-runs?${params.toString()}`)
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
      const allIds = runs.map(r => r.runId || r.run_id).filter(Boolean) as string[]
      setSelectedRuns(new Set(allIds))
    }
  }

  function exportToCSV() {
    const headers = ["ID", "Ключевое слово", "Статус", "Результатов", "Создан"]
    const rows = runs.map(run => [
      run.runId || run.run_id || "",
      run.keyword || "",
      run.status || "",
      run.resultsCount?.toString() || "",
      run.createdAt || run.created_at || "",
    ])
    
    const csv = [
      headers.join(","),
      ...rows.map(row => row.map(cell => `"${cell}"`).join(","))
    ].join("\n")
    
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" })
    const link = document.createElement("a")
    const url = URL.createObjectURL(blob)
    link.setAttribute("href", url)
    link.setAttribute("download", `parsing-runs-${new Date().toISOString().split("T")[0]}.csv`)
    link.style.visibility = "hidden"
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    toast.success("Данные экспортированы в CSV")
  }

  function getStatusBadge(status: string) {
    switch (status) {
      case "running":
        return <Badge variant="default">Выполняется</Badge>
      case "completed":
        return <Badge variant="default" className="bg-green-500">Завершен</Badge>
      case "failed":
        return <Badge variant="destructive">Ошибка</Badge>
      default:
        return <Badge variant="outline">{status}</Badge>
    }
  }

  const currentPage = Math.floor(offset / limit) + 1
  const totalPages = Math.ceil(total / limit)

  if (loading && runs.length === 0) {
    return <div>Загрузка...</div>
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex justify-between items-center">
          <CardTitle>История парсинга</CardTitle>
          <div className="flex gap-2">
            <Button variant="outline" onClick={exportToCSV}>
              Экспорт CSV
            </Button>
            {selectedRuns.size > 0 && (
              <AlertDialog open={deleteDialogOpen && !deleteRunId} onOpenChange={setDeleteDialogOpen}>
                <AlertDialogTrigger asChild>
                  <Button variant="destructive">
                    Удалить выбранные ({selectedRuns.size})
                  </Button>
                </AlertDialogTrigger>
                <AlertDialogContent>
                  <AlertDialogHeader>
                    <AlertDialogTitle>Подтверждение удаления</AlertDialogTitle>
                    <AlertDialogDescription>
                      Вы уверены, что хотите удалить {selectedRuns.size} запусков парсинга? 
                      Это действие нельзя отменить.
                    </AlertDialogDescription>
                  </AlertDialogHeader>
                  <AlertDialogFooter>
                    <AlertDialogCancel>Отмена</AlertDialogCancel>
                    <AlertDialogAction onClick={handleBulkDelete}>Удалить</AlertDialogAction>
                  </AlertDialogFooter>
                </AlertDialogContent>
              </AlertDialog>
            )}
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {error && <div className="text-red-500 mb-4">{error}</div>}
        
        {/* Фильтры и поиск */}
        <div className="mb-4 flex gap-4 flex-wrap">
          <Input
            placeholder="Поиск по ключевому слову..."
            value={keywordSearch}
            onChange={(e) => setKeywordSearch(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleFilterChange()}
            className="max-w-xs"
          />
          <Select value={statusFilter} onValueChange={(value) => {
            setStatusFilter(value)
            setTimeout(handleFilterChange, 0)
          }}>
            <SelectTrigger className="w-[180px]">
              <SelectValue placeholder="Статус" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Все статусы</SelectItem>
              <SelectItem value="running">Выполняется</SelectItem>
              <SelectItem value="completed">Завершен</SelectItem>
              <SelectItem value="failed">Ошибка</SelectItem>
            </SelectContent>
          </Select>
          <Button onClick={handleFilterChange}>Применить фильтры</Button>
        </div>
        
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-12">
                <input
                  type="checkbox"
                  checked={selectedRuns.size === runs.length && runs.length > 0}
                  onChange={toggleSelectAll}
                />
              </TableHead>
              <TableHead>
                <button
                  onClick={() => handleSort("runId")}
                  className="hover:underline"
                >
                  ID {sortBy === "run_id" && (sortOrder === "asc" ? "↑" : "↓")}
                </button>
              </TableHead>
              <TableHead>
                <button
                  onClick={() => handleSort("keyword")}
                  className="hover:underline"
                >
                  Ключевое слово {sortBy === "keyword" && (sortOrder === "asc" ? "↑" : "↓")}
                </button>
              </TableHead>
              <TableHead>
                <button
                  onClick={() => handleSort("status")}
                  className="hover:underline"
                >
                  Статус {sortBy === "status" && (sortOrder === "asc" ? "↑" : "↓")}
                </button>
              </TableHead>
              <TableHead>
                <button
                  onClick={() => handleSort("createdAt")}
                  className="hover:underline"
                >
                  Создан {sortBy === "created_at" && (sortOrder === "asc" ? "↑" : "↓")}
                </button>
              </TableHead>
              <TableHead>Результатов</TableHead>
              <TableHead>Действия</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {runs.length === 0 ? (
              <TableRow>
                <TableCell colSpan={7} className="text-center text-muted-foreground">
                  История парсинга пуста
                </TableCell>
              </TableRow>
            ) : (
              runs.map((run) => {
                const runId = run.runId || run.run_id
                if (!runId) {
                  return null
                }
                const isSelected = selectedRuns.has(runId)
                
                return (
                  <TableRow key={runId} className={isSelected ? "bg-muted" : ""}>
                    <TableCell>
                      <input
                        type="checkbox"
                        checked={isSelected}
                        onChange={() => toggleSelectRun(runId)}
                      />
                    </TableCell>
                    <TableCell className="font-mono text-sm">
                      {runId ? `${runId.substring(0, 8)}...` : "—"}
                    </TableCell>
                    <TableCell>{run.keyword || "—"}</TableCell>
                    <TableCell>{getStatusBadge(run.status || "unknown")}</TableCell>
                    <TableCell>
                      {run.createdAt || run.created_at
                        ? new Date(run.createdAt || run.created_at).toLocaleDateString("ru-RU")
                        : "—"}
                    </TableCell>
                    <TableCell>{run.resultsCount ?? "—"}</TableCell>
                    <TableCell>
                      <div className="flex gap-2">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => router.push(`/parsing-runs/${runId}`)}
                        >
                          Открыть
                        </Button>
                        <AlertDialog
                          open={deleteDialogOpen && deleteRunId === runId}
                          onOpenChange={(open) => {
                            setDeleteDialogOpen(open)
                            if (!open) setDeleteRunId(null)
                          }}
                        >
                          <AlertDialogTrigger asChild>
                            <Button
                              variant="destructive"
                              size="sm"
                              onClick={() => {
                                setDeleteRunId(runId)
                                setDeleteDialogOpen(true)
                              }}
                            >
                              Удалить
                            </Button>
                          </AlertDialogTrigger>
                          <AlertDialogContent>
                            <AlertDialogHeader>
                              <AlertDialogTitle>Подтверждение удаления</AlertDialogTitle>
                              <AlertDialogDescription>
                                Вы уверены, что хотите удалить запуск парсинга "{run.keyword || runId}"? 
                                Это действие нельзя отменить.
                              </AlertDialogDescription>
                            </AlertDialogHeader>
                            <AlertDialogFooter>
                              <AlertDialogCancel>Отмена</AlertDialogCancel>
                              <AlertDialogAction onClick={() => handleDelete(runId)}>
                                Удалить
                              </AlertDialogAction>
                            </AlertDialogFooter>
                          </AlertDialogContent>
                        </AlertDialog>
                      </div>
                    </TableCell>
                  </TableRow>
                )
              }).filter(Boolean)
            )}
          </TableBody>
        </Table>
        
        {/* Пагинация */}
        {totalPages > 1 && (
          <div className="mt-4 flex justify-between items-center">
            <div className="text-sm text-muted-foreground">
              Показано {offset + 1}-{Math.min(offset + limit, total)} из {total}
            </div>
            <div className="flex gap-2">
              <Button
                variant="outline"
                disabled={currentPage === 1}
                onClick={() => {
                  const params = new URLSearchParams(searchParams.toString())
                  params.set("page", (currentPage - 1).toString())
                  router.push(`/parsing-runs?${params.toString()}`)
                }}
              >
                Предыдущая
              </Button>
              <span className="px-4 py-2">
                Страница {currentPage} из {totalPages}
              </span>
              <Button
                variant="outline"
                disabled={currentPage === totalPages}
                onClick={() => {
                  const params = new URLSearchParams(searchParams.toString())
                  params.set("page", (currentPage + 1).toString())
                  router.push(`/parsing-runs?${params.toString()}`)
                }}
              >
                Следующая
              </Button>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
