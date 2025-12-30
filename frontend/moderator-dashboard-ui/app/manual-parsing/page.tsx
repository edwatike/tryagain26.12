"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { startParsing } from "@/lib/api"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Navigation } from "@/components/navigation"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { toast } from "sonner"

export default function ManualParsingPage() {
  const router = useRouter()
  const [keyword, setKeyword] = useState("")
  const [depth, setDepth] = useState(10)
  const [source, setSource] = useState<"google" | "yandex" | "both">("google")
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function handleStart() {
    if (!keyword.trim()) {
      toast.error("Введите ключевое слово")
      return
    }

    try {
      setLoading(true)
      setError(null)
      const result = await startParsing({
        keyword: keyword.trim(),
        depth,
        source,
      })
      const runId = result.runId || result.run_id || ""
      toast.success(`Парсинг запущен: ${result.keyword}`)
      if (runId) {
        router.push(`/parsing-runs/${runId}`)
      }
    } catch (err) {
      console.error("[Manual Parsing] Error starting parsing:", err)
      toast.error("Ошибка запуска парсинга")
      if (err instanceof Error) {
        setError(err.message)
      } else {
        setError("Ошибка запуска парсинга")
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-background">
      <Navigation />
      <main className="container mx-auto px-6 py-12 max-w-7xl">
        <Card>
          <CardHeader>
            <CardTitle className="text-4xl font-bold">Ручной парсинг</CardTitle>
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
      </main>
    </div>
  )
}

