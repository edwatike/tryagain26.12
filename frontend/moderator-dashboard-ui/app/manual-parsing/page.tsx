"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { apiFetch, APIError } from "@/lib/api"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"

export default function ManualParsingPage() {
  const router = useRouter()
  const [keyword, setKeyword] = useState("")
  const [maxUrls, setMaxUrls] = useState(10)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function handleStart() {
    if (!keyword.trim()) {
      setError("Введите ключевое слово")
      return
    }

    try {
      setLoading(true)
      setError(null)
      const data = await apiFetch<{ runId: string }>("/parsing/start", {
        method: "POST",
        body: JSON.stringify({ keyword, maxUrls }),
      })
      router.push(`/parsing-runs/${data.runId}`)
    } catch (err) {
      if (err instanceof APIError) {
        setError(err.message)
      } else {
        setError("Ошибка запуска парсинга")
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Ручной парсинг</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {error && <div className="text-red-500">{error}</div>}
        
        <div>
          <Label htmlFor="keyword">Ключевое слово</Label>
          <Input
            id="keyword"
            value={keyword}
            onChange={(e) => setKeyword(e.target.value)}
            placeholder="Например: металлопрокат"
            disabled={loading}
          />
        </div>

        <div>
          <Label htmlFor="maxUrls">Максимум URL</Label>
          <Input
            id="maxUrls"
            type="number"
            value={maxUrls}
            onChange={(e) => setMaxUrls(parseInt(e.target.value) || 10)}
            min={1}
            max={100}
            disabled={loading}
          />
        </div>

        <Button onClick={handleStart} disabled={loading || !keyword.trim()}>
          {loading ? "Запуск..." : "Запустить парсинг"}
        </Button>
      </CardContent>
    </Card>
  )
}

