"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { apiFetch, APIError } from "@/lib/api"
import { ParsingRunDTO } from "@/lib/types"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"

export default function ParsingRunsPage() {
  const router = useRouter()
  const [runs, setRuns] = useState<ParsingRunDTO[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadRuns()
  }, [])

  async function loadRuns() {
    try {
      setLoading(true)
      const data = await apiFetch<{ runs: ParsingRunDTO[] }>("/parsing/runs?limit=100&offset=0")
      setRuns(data.runs)
      setError(null)
    } catch (err) {
      if (err instanceof APIError) {
        setError(err.message)
      } else {
        setError("Ошибка загрузки запусков парсинга")
      }
    } finally {
      setLoading(false)
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

  return (
    <Card>
      <CardHeader>
        <CardTitle>История парсинга</CardTitle>
      </CardHeader>
      <CardContent>
        {error && <div className="text-red-500 mb-4">{error}</div>}
        
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>ID</TableHead>
              <TableHead>Ключевое слово</TableHead>
              <TableHead>Статус</TableHead>
              <TableHead>Результатов</TableHead>
              <TableHead>Действия</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {runs.map((run) => (
              <TableRow key={run.runId}>
                <TableCell className="font-mono text-sm">{run.runId.substring(0, 8)}...</TableCell>
                <TableCell>{run.keyword}</TableCell>
                <TableCell>{getStatusBadge(run.status)}</TableCell>
                <TableCell>{run.resultsCount ?? "—"}</TableCell>
                <TableCell>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => router.push(`/parsing-runs/${run.runId}`)}
                  >
                    Открыть
                  </Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  )
}

