"use client"

import { useState, useEffect } from "react"
import { useRouter, useParams } from "next/navigation"
import { apiFetch, APIError, getDomainsQueue } from "@/lib/api"
import { ParsingRunDTO, DomainQueueEntryDTO } from "@/lib/types"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { toast } from "sonner"
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

export default function ParsingRunDetailPage() {
  const router = useRouter()
  const params = useParams()
  const runId = params?.runId as string

  const [run, setRun] = useState<ParsingRunDTO | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [domains, setDomains] = useState<DomainQueueEntryDTO[]>([])
  const [loadingDomains, setLoadingDomains] = useState(false)

  useEffect(() => {
    if (runId) {
      loadRun()
      loadDomains()
    }
  }, [runId])
  
  useEffect(() => {
    // Reload domains when run status changes to completed
    if (run?.status === "completed" && runId) {
      loadDomains()
    }
  }, [run?.status, runId])

  // Polling для обновления статуса, если парсинг еще выполняется
  useEffect(() => {
    if (!runId || !run) return

    // Если статус "running", обновляем каждые 2 секунды
    if (run.status === "running") {
      const interval = setInterval(() => {
        loadRun()
      }, 2000) // Обновляем каждые 2 секунды

      return () => clearInterval(interval)
    }
  }, [runId, run?.status])

          async function loadRun() {
            try {
              setLoading(true)
              const data = await apiFetch<ParsingRunDTO>(`/parsing/runs/${runId}`)
              setRun(data)
              setError(null)
            } catch (err) {
              // Log detailed error to console (visible in F12)
              console.error("[Parsing Run Detail] Error loading run:", {
                error: err,
                runId: runId,
                details: err instanceof APIError ? {
                  status: err.status,
                  message: err.message,
                  data: err.data
                } : err
              })
              
              if (err instanceof APIError) {
                if (err.status === 404) {
                  setError("Запуск парсинга не найден")
                  toast.error("Запуск парсинга не найден")
                } else {
                  setError(err.message)
                  toast.error(`Ошибка загрузки: ${err.message}`)
                }
              } else {
                const errorMsg = "Ошибка загрузки запуска парсинга"
                setError(errorMsg)
                toast.error(errorMsg)
              }
            } finally {
              setLoading(false)
            }
          }
          
          async function loadDomains() {
            if (!runId) return
            try {
              setLoadingDomains(true)
              const data = await getDomainsQueue({
                parsingRunId: runId,
                limit: 1000
              })
              setDomains(data.entries)
            } catch (err) {
              console.error("[Parsing Run Detail] Error loading domains:", err)
              // Don't show error toast for domains, just log it
            } finally {
              setLoadingDomains(false)
            }
          }

  async function handleDelete() {
    if (!run) return

    const originalRun = run
    setRun(null)
    setDeleteDialogOpen(false)

    try {
      await apiFetch(`/parsing/runs/${runId}`, {
        method: "DELETE",
      })
      toast.success(`Запуск парсинга "${originalRun.keyword || runId}" успешно удален`)
      router.push("/parsing-runs")
    } catch (err) {
      // Откат при ошибке
      setRun(originalRun)
      console.error("Error deleting parsing run:", err)
      if (err instanceof APIError) {
        toast.error(`Ошибка удаления: ${err.message}`)
      } else {
        toast.error("Ошибка удаления запуска парсинга")
      }
    }
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

  if (loading) {
    return <div>Загрузка...</div>
  }

  if (error || !run) {
    return (
      <Card>
        <CardContent className="pt-6">
          <div className="text-red-500">{error || "Запуск парсинга не найден"}</div>
          <Button onClick={() => router.push("/parsing-runs")} className="mt-4">
            Вернуться к списку
          </Button>
        </CardContent>
      </Card>
    )
  }

  const runIdValue = run.runId || run.run_id || runId

  return (
    <Card>
      <CardHeader>
        <div className="flex justify-between items-center">
          <CardTitle>Детали запуска парсинга</CardTitle>
          <div className="flex gap-2">
            <Button variant="outline" onClick={() => router.push("/parsing-runs")}>
              Назад к списку
            </Button>
            <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
              <AlertDialogTrigger asChild>
                <Button variant="destructive">Удалить</Button>
              </AlertDialogTrigger>
              <AlertDialogContent>
                <AlertDialogHeader>
                  <AlertDialogTitle>Подтверждение удаления</AlertDialogTitle>
                  <AlertDialogDescription>
                    Вы уверены, что хотите удалить запуск парсинга "{run.keyword || runIdValue}"? 
                    Это действие нельзя отменить.
                  </AlertDialogDescription>
                </AlertDialogHeader>
                <AlertDialogFooter>
                  <AlertDialogCancel>Отмена</AlertDialogCancel>
                  <AlertDialogAction onClick={handleDelete}>Удалить</AlertDialogAction>
                </AlertDialogFooter>
              </AlertDialogContent>
            </AlertDialog>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <div>
            <label className="text-sm font-medium text-muted-foreground">ID запуска</label>
            <p className="font-mono text-sm">{runIdValue}</p>
          </div>
          
          <div>
            <label className="text-sm font-medium text-muted-foreground">Ключевое слово</label>
            <p>{run.keyword || "—"}</p>
          </div>
          
          <div>
            <label className="text-sm font-medium text-muted-foreground">Статус</label>
            <div className="mt-1">{getStatusBadge(run.status || "unknown")}</div>
          </div>
          
          <div>
            <label className="text-sm font-medium text-muted-foreground">Создан</label>
            <p>
              {run.createdAt || run.created_at
                ? new Date(run.createdAt || run.created_at).toLocaleString("ru-RU")
                : "—"}
            </p>
          </div>
          
          {run.startedAt || run.started_at ? (
            <div>
              <label className="text-sm font-medium text-muted-foreground">Начало выполнения</label>
              <p>
                {new Date(run.startedAt || run.started_at).toLocaleString("ru-RU")}
              </p>
            </div>
          ) : null}
          
          {run.finishedAt || run.finished_at ? (
            <div>
              <label className="text-sm font-medium text-muted-foreground">Завершен</label>
              <p>
                {new Date(run.finishedAt || run.finished_at).toLocaleString("ru-RU")}
              </p>
            </div>
          ) : null}
          
          {run.resultsCount !== null && run.resultsCount !== undefined ? (
            <div>
              <label className="text-sm font-medium text-muted-foreground">Результатов</label>
              <p>{run.resultsCount}</p>
            </div>
          ) : null}
          
          {run.error || run.error_message ? (
            <div>
              <label className="text-sm font-medium text-muted-foreground">Ошибка</label>
              <p className="text-red-500">{run.error || run.error_message || "—"}</p>
            </div>
          ) : null}
          
          {/* Список найденных URL */}
          {run.status === "completed" && domains.length > 0 && (
            <div>
              <label className="text-sm font-medium text-muted-foreground mb-2 block">
                Найденные URL ({domains.length})
              </label>
              <div className="max-h-96 overflow-y-auto border rounded-md p-4 space-y-2">
                {loadingDomains ? (
                  <p className="text-sm text-muted-foreground">Загрузка...</p>
                ) : (
                  domains.map((entry, index) => (
                    <div key={entry.domain || index} className="flex items-start gap-2 p-2 hover:bg-muted rounded">
                      <div className="flex-1 min-w-0">
                        <a
                          href={entry.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-sm text-blue-600 hover:underline break-all"
                        >
                          {entry.url}
                        </a>
                        <p className="text-xs text-muted-foreground mt-1">
                          Домен: {entry.domain}
                        </p>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}
          
          {run.status === "completed" && domains.length === 0 && !loadingDomains && (
            <div>
              <label className="text-sm font-medium text-muted-foreground">Найденные URL</label>
              <p className="text-sm text-muted-foreground">URL не найдены</p>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}


