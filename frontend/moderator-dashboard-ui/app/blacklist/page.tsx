"use client"

import { useState, useEffect } from "react"
import { apiFetch, APIError } from "@/lib/api"
import { BlacklistEntryDTO } from "@/lib/types"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"

export default function BlacklistPage() {
  const [entries, setEntries] = useState<BlacklistEntryDTO[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [newDomain, setNewDomain] = useState("")

  useEffect(() => {
    loadBlacklist()
  }, [])

  async function loadBlacklist() {
    try {
      setLoading(true)
      setError(null)
      const data = await apiFetch<{ entries: BlacklistEntryDTO[]; total: number }>("/moderator/blacklist?limit=100&offset=0")
      setEntries(data.entries || [])
      // Если entries пустой, но total > 0, значит проблема с данными
      if ((!data.entries || data.entries.length === 0) && data.total > 0) {
        setError(`В базе данных есть ${data.total} записей, но они не загружены. Проверьте формат данных.`)
      }
    } catch (err) {
      if (err instanceof APIError) {
        setError(err.message)
      } else {
        setError("Ошибка загрузки черного списка")
      }
      console.error("Blacklist load error:", err)
    } finally {
      setLoading(false)
    }
  }

  async function handleAdd() {
    if (!newDomain.trim()) return

    try {
      await apiFetch("/moderator/blacklist", {
        method: "POST",
        body: JSON.stringify({ domain: newDomain }),
      })
      setNewDomain("")
      loadBlacklist()
    } catch (err) {
      if (err instanceof APIError) {
        setError(err.message)
      } else {
        setError("Ошибка добавления в черный список")
      }
    }
  }

  async function handleDelete(domain: string) {
    try {
      await apiFetch(`/moderator/blacklist/${domain}`, {
        method: "DELETE",
      })
      loadBlacklist()
    } catch (err) {
      if (err instanceof APIError) {
        setError(err.message)
      } else {
        setError("Ошибка удаления из черного списка")
      }
    }
  }

  if (loading) {
    return <div>Загрузка...</div>
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Черный список</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {error && <div className="text-red-500">{error}</div>}
        
        <div className="flex gap-2">
          <Input
            value={newDomain}
            onChange={(e) => setNewDomain(e.target.value)}
            placeholder="Введите домен"
            onKeyPress={(e) => e.key === "Enter" && handleAdd()}
          />
          <Button onClick={handleAdd}>Добавить</Button>
        </div>

        {entries.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground">
            Черный список пуст. Добавьте домен, чтобы начать.
          </div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Домен</TableHead>
                <TableHead>Причина</TableHead>
                <TableHead>Добавлен</TableHead>
                <TableHead>Действия</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {entries.map((entry) => (
                <TableRow key={entry.domain}>
                  <TableCell>{entry.domain}</TableCell>
                  <TableCell>{entry.reason || "—"}</TableCell>
                  <TableCell>
                    {entry.addedAt ? new Date(entry.addedAt).toLocaleDateString('ru-RU') : "—"}
                  </TableCell>
                  <TableCell>
                    <Button
                      variant="destructive"
                      size="sm"
                      onClick={() => handleDelete(entry.domain)}
                    >
                      Удалить
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </CardContent>
    </Card>
  )
}

