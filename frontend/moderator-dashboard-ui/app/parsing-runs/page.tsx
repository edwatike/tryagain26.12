"use client"

import { useState, useEffect, useRef } from "react"
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
  const isDeletingRef = useRef(false)
  
  const [runs, setRuns] = useState<ParsingRunDTO[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [total, setTotal] = useState(0)
  const [limit, setLimit] = useState(100)
  const [offset, setOffset] = useState(0)
  const [refreshKey, setRefreshKey] = useState(0)
  
  // Отслеживание изменений runs для диагностики
  useEffect(() => {
    console.log(`[useEffect] runs changed - length: ${runs.length}, total: ${total}, refreshKey: ${refreshKey}`)
  }, [runs, total, refreshKey])
  
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
    // Не загружаем данные, если идет процесс удаления
    if (isDeletingRef.current) {
      return
    }
    
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
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchParams])

  async function loadRuns(
    page: number = 1,
    status: string = statusFilter,
    keyword: string = keywordSearch,
    sort: string = sortBy,
    order: "asc" | "desc" = sortOrder
  ): Promise<void> {
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
      
      // Добавляем уникальный параметр для предотвращения кэширования
      params.append("_t", Date.now().toString())
      
      const data = await apiFetch<{ runs: ParsingRunDTO[]; total: number; limit: number; offset: number }>(
        `/parsing/runs?${params.toString()}`
      )
      
      console.log(`[loadRuns] API response - runs: ${data.runs?.length || 0}, total: ${data.total}`)
      
      const validRuns = (data.runs || []).filter((run) => run && (run.runId || run.run_id))
      
      // Создаем новый массив для гарантированного обновления React
      const newRuns = [...validRuns]
      
      // Логирование перед обновлением состояния
      console.log(`[loadRuns] New data - runs.length: ${newRuns.length}, total: ${data.total}`)
      console.log(`[loadRuns] First 5 run IDs:`, newRuns.slice(0, 5).map(r => r.runId || r.run_id))
      
      // Принудительно обновляем состояние с новыми данными
      // Используем прямую установку, а не функциональное обновление, чтобы гарантировать обновление
      console.log(`[loadRuns] Updating state - runs: ${newRuns.length}, total: ${data.total}`)
      setRuns(newRuns)
      setTotal(data.total)
      setError(null)
      
      // Принудительно обновляем ключ для перерисовки компонента
      setRefreshKey(prev => {
        const newKey = prev + 1
        console.log(`[loadRuns] Refresh key updated: ${prev} -> ${newKey}`)
        return newKey
      })
      
      console.log(`[loadRuns] State update scheduled - runs.length: ${newRuns.length}, total: ${data.total}`)
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
    console.log(`[handleDelete] Called with runId: ${runId}`)
    
    const originalRuns = [...runs]
    const runToDelete = runs.find(r => (r.runId || r.run_id) === runId)
    
    console.log(`[handleDelete] Run to delete:`, runToDelete)
    
    // Закрываем диалог
    setDeleteDialogOpen(false)
    setDeleteRunId(null)
    
    // Устанавливаем флаг удаления
    isDeletingRef.current = true
    
    // Показываем индикатор загрузки
    setLoading(true)

    try {
      console.log(`[handleDelete] Sending DELETE request to /parsing/runs/${runId}`)
      try {
        const deleteResult = await apiFetch(`/parsing/runs/${runId}`, {
          method: "DELETE",
        })
        console.log(`[handleDelete] Delete result:`, deleteResult)
        console.log(`[handleDelete] Delete successful!`)
      } catch (deleteError) {
        console.error(`[handleDelete] Delete error:`, deleteError)
        throw deleteError
      }
      
      // Получаем актуальные параметры из URL для перезагрузки
      let page = parseInt(searchParams.get("page") || "1", 10)
      const status = searchParams.get("status") || "all"
      const keyword = searchParams.get("keyword") || ""
      const sort = searchParams.get("sort") || "created_at"
      const order = (searchParams.get("order") || "desc") as "asc" | "desc"
      
      // Небольшая задержка, чтобы дать серверу время на удаление
      await new Promise(resolve => setTimeout(resolve, 500))
      
      // Если текущая страница стала пустой, переходим на предыдущую
      const currentTotal = total - 1
      const maxPage = Math.ceil(currentTotal / limit)
      if (page > maxPage && maxPage > 0) {
        page = maxPage
        const params = new URLSearchParams(searchParams.toString())
        params.set("page", page.toString())
        router.push(`/parsing-runs?${params.toString()}`)
        // router.push вызовет useEffect, который загрузит данные
      } else {
        // Принудительно перезагружаем данные
        // Сбрасываем флаг перед загрузкой
        isDeletingRef.current = false
        
        console.log(`[handleDelete] Reloading data after delete... (page: ${page})`)
        
        // Обновляем Next.js кэш
        router.refresh()
        
        // Загружаем данные несколько раз для гарантии обновления
        await new Promise(resolve => setTimeout(resolve, 500))
        console.log(`[handleDelete] First reload...`)
        await loadRuns(page, status, keyword, sort, order)
        
        // Дополнительная загрузка для гарантии
        await new Promise(resolve => setTimeout(resolve, 500))
        console.log(`[handleDelete] Second reload...`)
        await loadRuns(page, status, keyword, sort, order)
        
        // Финальная загрузка для гарантии
        await new Promise(resolve => setTimeout(resolve, 500))
        console.log(`[handleDelete] Third reload...`)
        await loadRuns(page, status, keyword, sort, order)
        
        console.log(`[handleDelete] After reloads - runs.length: ${runs.length}, total: ${total}`)
      }
      
      toast.success(`Запуск парсинга "${runToDelete?.keyword || runId}" успешно удален`)
    } catch (err) {
      // Откат при ошибке
      setRuns(originalRuns)
      setTotal(total)
      setLoading(false)
      console.error("Error deleting parsing run:", err)
      if (err instanceof APIError) {
        toast.error(`Ошибка удаления: ${err.message}`)
      } else {
        toast.error("Ошибка удаления запуска парсинга")
      }
    } finally {
      // Снимаем флаг удаления
      isDeletingRef.current = false
    }
  }

  async function handleBulkDelete() {
    console.log(`[handleBulkDelete] Called with ${selectedRuns.size} selected runs`)
    
    if (selectedRuns.size === 0) {
      toast.warning("Выберите записи для удаления")
      return
    }

    const originalRuns = [...runs]
    const runIds = Array.from(selectedRuns)
    const selectedCount = selectedRuns.size
    
    console.log(`[handleBulkDelete] Deleting ${selectedCount} runs:`, runIds.slice(0, 5), '...')
    console.log(`[handleBulkDelete] Current total: ${total}, runs count: ${runs.length}`)
    
    // Закрываем диалог и очищаем выбор
    setSelectedRuns(new Set())
    setDeleteDialogOpen(false)
    
    // Устанавливаем флаг удаления
    isDeletingRef.current = true
    
    // Показываем индикатор загрузки
    setLoading(true)

    try {
      console.log(`[handleBulkDelete] Sending DELETE request to /parsing/runs/bulk`)
      
      // Используем bulk endpoint
      const deleteResponse = await apiFetch<{ deleted: number; total: number; errors?: string[] }>(`/parsing/runs/bulk`, {
        method: "DELETE",
        body: JSON.stringify(runIds),
      })
      
      console.log(`[handleBulkDelete] Delete response:`, deleteResponse)
      console.log(`[handleBulkDelete] Deleted: ${deleteResponse.deleted}, Errors: ${deleteResponse.errors?.length || 0}`)
      
      // Получаем актуальные параметры из URL для перезагрузки
      let page = parseInt(searchParams.get("page") || "1", 10)
      const status = searchParams.get("status") || "all"
      const keyword = searchParams.get("keyword") || ""
      const sort = searchParams.get("sort") || "created_at"
      const order = (searchParams.get("order") || "desc") as "asc" | "desc"
      
      // Небольшая задержка, чтобы дать серверу время на удаление
      await new Promise(resolve => setTimeout(resolve, 800))
      
      // Если текущая страница стала пустой, переходим на предыдущую
      const currentTotal = total - selectedCount
      const maxPage = Math.ceil(currentTotal / limit)
      if (page > maxPage && maxPage > 0) {
        page = maxPage
        const params = new URLSearchParams(searchParams.toString())
        params.set("page", page.toString())
        router.push(`/parsing-runs?${params.toString()}`)
        // router.push вызовет useEffect, который загрузит данные
      } else {
        // Принудительно перезагружаем данные
        // Сбрасываем флаг перед загрузкой
        isDeletingRef.current = false
        
        // Обновляем Next.js кэш
        router.refresh()
        
        // Загружаем данные несколько раз для гарантии обновления
        console.log(`[handleBulkDelete] Reloading data after delete...`)
        await loadRuns(page, status, keyword, sort, order)
        
        // Дополнительная загрузка для гарантии
        await new Promise(resolve => setTimeout(resolve, 500))
        console.log(`[handleBulkDelete] Second reload...`)
        await loadRuns(page, status, keyword, sort, order)
        
        // Финальная загрузка для гарантии
        await new Promise(resolve => setTimeout(resolve, 500))
        console.log(`[handleBulkDelete] Third reload...`)
        const finalData = await loadRuns(page, status, keyword, sort, order)
        
        // Если после всех попыток данные не обновились, принудительно перезагружаем страницу
        await new Promise(resolve => setTimeout(resolve, 500))
        if (typeof window !== 'undefined') {
          console.log(`[handleBulkDelete] Force reloading page...`)
          window.location.reload()
        }
      }
      
      toast.success(`Успешно удалено ${selectedCount} запусков парсинга`)
    } catch (err) {
      // Откат при ошибке
      setRuns(originalRuns)
      setTotal(total)
      setLoading(false)
      console.error("Error bulk deleting parsing runs:", err)
      toast.error("Ошибка массового удаления")
    } finally {
      // Снимаем флаг удаления
      isDeletingRef.current = false
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
            // Обновляем URL сразу с новым значением
            const params = new URLSearchParams()
            params.set("page", "1")
            if (value !== "all") params.set("status", value)
            if (keywordSearch) params.set("keyword", keywordSearch)
            if (sortBy) {
              params.set("sort", sortBy)
              params.set("order", sortOrder)
            }
            router.push(`/parsing-runs?${params.toString()}`)
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
              runs.map((run, index) => {
                const runId = run.runId || run.run_id
                if (!runId) {
                  return null
                }
                const isSelected = selectedRuns.has(runId)
                
                return (
                  <TableRow key={`${runId}-${refreshKey}`} className={isSelected ? "bg-muted" : ""}>
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
