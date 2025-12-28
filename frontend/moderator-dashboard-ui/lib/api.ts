import { DomainQueueEntryDTO } from "./types"

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000"

export class APIError extends Error {
  constructor(
    message: string,
    public status: number,
    public data?: unknown,
  ) {
    super(message)
    this.name = "APIError"
  }
}

export async function apiFetch<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`
  
  // Для DELETE запросов с body нужно явно указать Content-Type
  const headers: Record<string, string> = {
    ...(options?.headers as Record<string, string> || {}),
  }
  
  // Добавляем Content-Type только если есть body и метод не GET
  // Используем charset=utf-8 для корректной обработки кириллицы (из HANDOFF.md)
  if (options?.body && options.method !== "GET") {
    headers["Content-Type"] = "application/json; charset=utf-8"
  } else if (!options?.body && options?.method !== "GET" && options?.method !== "DELETE") {
    headers["Content-Type"] = "application/json; charset=utf-8"
  }
  
  try {
    const response = await fetch(url, {
      ...options,
      headers,
    })
    
    // Для DELETE запросов со статусом 204 (No Content) возвращаем пустой объект
    // Для статуса 200 с body - парсим JSON (например, bulk delete возвращает {deleted, total})
    if (response.status === 204 && options?.method === "DELETE") {
      console.log(`[API Fetch] Success: ${response.status} for ${endpoint}`)
      return {} as T
    }
    
    if (!response.ok) {
      let errorData
      try {
        errorData = await response.json()
      } catch {
        const text = await response.text().catch(() => response.statusText)
        // Log to console for debugging
        console.error(`[API Error] ${response.status} ${response.statusText}:`, text)
        throw new APIError(
          `HTTP ${response.status}: ${response.statusText}`,
          response.status,
          { text }
        )
      }
      
      // Extract detailed error message
      const errorMessage = errorData.detail || errorData.message || errorData.error || `HTTP ${response.status}`
      
      // Log detailed error to console for debugging (F12)
      console.error(`[API Error] ${response.status}:`, {
        message: errorMessage,
        data: errorData,
        url: url,
        endpoint: endpoint
      })
      
      throw new APIError(
        errorMessage,
        response.status,
        errorData
      )
    }
    
    // Пытаемся получить JSON, если есть
    const contentType = response.headers.get("content-type")
    if (contentType && contentType.includes("application/json")) {
      return await response.json()
    }
    
    // Если нет JSON, возвращаем пустой объект
    const text = await response.text()
    if (text) {
      try {
        return JSON.parse(text) as T
      } catch {
        return {} as T
      }
    }
    return {} as T
  } catch (error) {
    // Log all errors to console (visible in F12)
    console.error("[API Fetch] Unexpected error:", {
      error: error,
      url: url,
      endpoint: endpoint,
      errorType: error instanceof Error ? error.constructor.name : typeof error,
      errorMessage: error instanceof Error ? error.message : String(error)
    })
    
    if (error instanceof APIError) throw error
    if (error instanceof TypeError && error.message.includes("fetch")) {
      const connectionError = new APIError("Unable to connect to server. Please ensure the backend is running.", 503)
      console.error("[API Fetch] Connection error:", connectionError.message)
      throw connectionError
    }
    const unexpectedError = new APIError("An unexpected error occurred", 500)
    console.error("[API Fetch] Unexpected error:", unexpectedError.message, error)
    throw unexpectedError
  }
}

// Domains queue API
export async function getDomainsQueue(params?: {
  limit?: number
  offset?: number
  status?: string
  keyword?: string
  parsingRunId?: string
}): Promise<{
  entries: DomainQueueEntryDTO[]
  total: number
  limit: number
  offset: number
}> {
  const queryParams = new URLSearchParams()
  if (params?.limit) queryParams.append("limit", params.limit.toString())
  if (params?.offset) queryParams.append("offset", params.offset.toString())
  if (params?.status) queryParams.append("status", params.status)
  if (params?.keyword) queryParams.append("keyword", params.keyword)
  if (params?.parsingRunId) queryParams.append("parsingRunId", params.parsingRunId)
  
  const queryString = queryParams.toString()
  return apiFetch<{
    entries: DomainQueueEntryDTO[]
    total: number
    limit: number
    offset: number
  }>(`/domains/queue${queryString ? `?${queryString}` : ""}`)
}

