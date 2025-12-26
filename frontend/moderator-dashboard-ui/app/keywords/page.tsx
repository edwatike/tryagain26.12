"use client"

import { useState, useEffect } from "react"
import { apiFetch, APIError } from "@/lib/api"
import { KeywordDTO } from "@/lib/types"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"

export default function KeywordsPage() {
  const [keywords, setKeywords] = useState<KeywordDTO[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [newKeyword, setNewKeyword] = useState("")

  useEffect(() => {
    loadKeywords()
  }, [])

  async function loadKeywords() {
    try {
      setLoading(true)
      const data = await apiFetch<{ keywords: KeywordDTO[] }>("/keywords")
      setKeywords(data.keywords)
      setError(null)
    } catch (err) {
      if (err instanceof APIError) {
        setError(err.message)
      } else {
        setError("Ошибка загрузки ключевых слов")
      }
    } finally {
      setLoading(false)
    }
  }

  async function handleAdd() {
    if (!newKeyword.trim()) return

    try {
      await apiFetch("/keywords", {
        method: "POST",
        body: JSON.stringify({ keyword: newKeyword }),
      })
      setNewKeyword("")
      loadKeywords()
    } catch (err) {
      if (err instanceof APIError) {
        setError(err.message)
      } else {
        setError("Ошибка добавления ключевого слова")
      }
    }
  }

  async function handleDelete(id: number) {
    try {
      await apiFetch(`/keywords/${id}`, {
        method: "DELETE",
      })
      loadKeywords()
    } catch (err) {
      if (err instanceof APIError) {
        setError(err.message)
      } else {
        setError("Ошибка удаления ключевого слова")
      }
    }
  }

  if (loading) {
    return <div>Загрузка...</div>
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Ключевые слова</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {error && <div className="text-red-500">{error}</div>}
        
        <div className="flex gap-2">
          <Input
            value={newKeyword}
            onChange={(e) => setNewKeyword(e.target.value)}
            placeholder="Введите ключевое слово"
            onKeyPress={(e) => e.key === "Enter" && handleAdd()}
          />
          <Button onClick={handleAdd}>Добавить</Button>
        </div>

        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>ID</TableHead>
              <TableHead>Ключевое слово</TableHead>
              <TableHead>Действия</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {keywords.map((keyword) => (
              <TableRow key={keyword.id}>
                <TableCell>{keyword.id}</TableCell>
                <TableCell>{keyword.keyword}</TableCell>
                <TableCell>
                  <Button
                    variant="destructive"
                    size="sm"
                    onClick={() => handleDelete(keyword.id)}
                  >
                    Удалить
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

