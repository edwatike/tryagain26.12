"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { apiFetch, APIError } from "@/lib/api"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"

export default function ManualParsingPage() {
  const router = useRouter()
  const [keyword, setKeyword] = useState("")
  const [depth, setDepth] = useState(10)
  const [source, setSource] = useState<"google" | "yandex" | "both">("google")
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
      const data = await apiFetch<{ runId: string; keyword: string; status: string }>("/parsing/start", {
        method: "POST",
        body: JSON.stringify({ keyword, depth, source }),
      })
      router.push(`/parsing-runs/${data.runId}`)
    } catch (err) {
      // Log detailed error to console (visible in F12)
      console.error("[Manual Parsing] Error starting parsing:", {
        error: err,
        keyword: keyword,
        depth: depth,
        source: source,
        details: err instanceof APIError ? {
          status: err.status,
          message: err.message,
          data: err.data
        } : err
      })
      
      if (err instanceof APIError) {
        setError(err.message)
        console.error(`[Manual Parsing] API Error ${err.status}:`, err.message, err.data)
      } else {
        const errorMsg = "Ошибка запуска парсинга"
        setError(errorMsg)
        console.error("[Manual Parsing] Unexpected error:", err)
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
          <Label htmlFor="source">Источник поиска</Label>
          <Select
            value={source}
            onValueChange={(value: "google" | "yandex" | "both") => setSource(value)}
            disabled={loading}
          >
            <SelectTrigger id="source">
              <SelectValue placeholder="Выберите источник" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="google">Google</SelectItem>
              <SelectItem value="yandex">Yandex</SelectItem>
              <SelectItem value="both">Google + Yandex</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div>
          <Label htmlFor="depth">Глубина парсинга (количество страниц)</Label>
          <Input
            id="depth"
            type="number"
            value={depth}
            onChange={(e) => setDepth(parseInt(e.target.value) || 1)}
            min={1}
            max={10}
            disabled={loading}
          />
          <p className="text-sm text-muted-foreground mt-1">
            Количество страниц результатов поиска для парсинга (1 страница ≈ 10-20 URL)
          </p>
        </div>

        <Button onClick={handleStart} disabled={loading || !keyword.trim()}>
          {loading ? "Запуск..." : "Запустить парсинг"}
        </Button>
      </CardContent>
    </Card>
  )
}

