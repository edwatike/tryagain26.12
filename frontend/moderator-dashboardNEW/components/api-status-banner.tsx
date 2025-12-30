"use client"

import { AlertCircle, ExternalLink } from "lucide-react"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Button } from "@/components/ui/button"

export function ApiStatusBanner() {
  const apiUrl = process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000"

  return (
    <Alert variant="destructive" className="mb-6">
      <AlertCircle className="h-5 w-5" />
      <AlertTitle className="text-lg font-semibold">Backend API недоступен</AlertTitle>
      <AlertDescription className="mt-2 space-y-3">
        <p>
          Не удается подключиться к API по адресу: <code className="bg-destructive/20 px-2 py-1 rounded">{apiUrl}</code>
        </p>

        <div className="space-y-2 text-sm">
          <p className="font-medium">Что нужно сделать:</p>
          <ol className="list-decimal list-inside space-y-1 ml-2">
            <li>Убедитесь, что backend запущен на {apiUrl}</li>
            <li>
              Проверьте, что CORS настроен для{" "}
              <code className="bg-destructive/20 px-1 rounded">http://localhost:3000</code>
            </li>
            <li>
              Или настройте переменную окружения{" "}
              <code className="bg-destructive/20 px-1 rounded">NEXT_PUBLIC_API_BASE_URL</code> в разделе{" "}
              <strong>Vars</strong> в боковой панели
            </li>
          </ol>
        </div>

        <div className="flex gap-2 pt-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => window.location.reload()}
            className="bg-background hover:bg-background/90"
          >
            Обновить страницу
          </Button>
          <Button variant="outline" size="sm" asChild className="bg-background hover:bg-background/90">
            <a href={apiUrl} target="_blank" rel="noopener noreferrer">
              Открыть API
              <ExternalLink className="ml-2 h-3 w-3" />
            </a>
          </Button>
        </div>
      </AlertDescription>
    </Alert>
  )
}
