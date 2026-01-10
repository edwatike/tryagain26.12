"use client"

import { useState, useEffect } from "react"
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Label } from "@/components/ui/label"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Navigation } from "@/components/navigation"
import { getBlacklist, addToBlacklist, removeFromBlacklist } from "@/lib/api"
import { getCachedBlacklist, setCachedBlacklist, invalidateBlacklistCache } from "@/lib/cache"
import { toast } from "sonner"
import { Plus, Trash2 } from "lucide-react"
import type { BlacklistEntryDTO } from "@/lib/types"

export default function BlacklistPage() {
  const [entries, setEntries] = useState<BlacklistEntryDTO[]>([])
  const [loading, setLoading] = useState(true)
  const [newDomain, setNewDomain] = useState("")
  const [newReason, setNewReason] = useState("")
  const [addingDomain, setAddingDomain] = useState(false)

  useEffect(() => {
    loadBlacklist()
  }, [])

  async function loadBlacklist() {
    setLoading(true)
    try {
      // Проверяем кэш
      const cached = getCachedBlacklist()
      if (cached) {
        setEntries(cached)
        setLoading(false)
        // Загружаем в фоне для обновления кэша
        getBlacklist({ limit: 1000 })
          .then((data) => {
            setCachedBlacklist(data.entries)
            setEntries(data.entries)
          })
          .catch(() => {
            // Игнорируем ошибки фоновой загрузки
          })
      } else {
        const data = await getBlacklist({ limit: 1000 })
        setEntries(data.entries)
        setCachedBlacklist(data.entries)
      }
    } catch (error) {
      toast.error("Ошибка загрузки данных")
      console.error("Error loading blacklist:", error)
    } finally {
      setLoading(false)
    }
  }

  async function handleAdd() {
    if (!newDomain.trim()) {
      toast.error("Введите домен")
      return
    }

    setAddingDomain(true)
    try {
      await addToBlacklist({ 
        domain: newDomain.trim(),
        reason: newReason.trim() || null
      })
      invalidateBlacklistCache()
      toast.success(`Домен "${newDomain}" добавлен в blacklist`)
      setNewDomain("")
      setNewReason("")
      loadBlacklist()
    } catch (error) {
      toast.error("Ошибка добавления домена")
      console.error("Error adding to blacklist:", error)
    } finally {
      setAddingDomain(false)
    }
  }

  async function handleRemove(domain: string) {
    if (!confirm(`Удалить "${domain}" из blacklist?`)) return

    try {
      await removeFromBlacklist(domain)
      invalidateBlacklistCache()
      toast.success(`Домен "${domain}" удален из blacklist`)
      loadBlacklist()
    } catch (error) {
      toast.error("Ошибка удаления домена")
      console.error("Error removing from blacklist:", error)
    }
  }

  return (
    <div className="min-h-screen bg-background">
      <Navigation />

      <main className="container mx-auto px-6 py-6 max-w-7xl">
        <h1 className="text-4xl font-bold mb-4">Черный список доменов</h1>

        <Card className="mb-4">
          <div className="p-4">
            <div className="space-y-3 mb-4">
              <div>
                <Label htmlFor="domain-input">Домен</Label>
                <Input
                  id="domain-input"
                  placeholder="Введите домен (example.com)"
                  value={newDomain}
                  onChange={(e) => setNewDomain(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && handleAdd()}
                  className="mt-1"
                />
              </div>
              <div>
                <Label htmlFor="reason-input">Причина добавления в черный список (необязательно)</Label>
                <Textarea
                  id="reason-input"
                  placeholder="Укажите причину добавления домена в черный список..."
                  value={newReason}
                  onChange={(e) => setNewReason(e.target.value)}
                  rows={3}
                  className="mt-1"
                />
              </div>
              <Button onClick={handleAdd} disabled={addingDomain}>
                <Plus className="mr-2 h-4 w-4" />
                Добавить
              </Button>
            </div>

            {loading ? (
              <div className="text-center py-12 text-muted-foreground">Загрузка...</div>
            ) : entries.length === 0 ? (
              <div className="text-center py-12 text-muted-foreground">Список пуст</div>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Домен</TableHead>
                    <TableHead>Причина</TableHead>
                    <TableHead>Добавлен</TableHead>
                    <TableHead className="text-right">Действия</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {entries.map((entry) => (
                    <TableRow key={entry.domain}>
                      <TableCell className="font-mono font-medium">{entry.domain}</TableCell>
                      <TableCell>{entry.reason || "—"}</TableCell>
                      <TableCell>{entry.addedAt ? new Date(entry.addedAt).toLocaleString("ru-RU") : "—"}</TableCell>
                      <TableCell className="text-right">
                        <Button variant="ghost" size="sm" onClick={() => handleRemove(entry.domain)}>
                          <Trash2 className="h-4 w-4 text-red-600" />
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
