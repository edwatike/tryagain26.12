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
  const headers: HeadersInit = {
    ...options?.headers,
  }
  
  // Добавляем Content-Type только если есть body и метод не GET
  if (options?.body && options.method !== "GET") {
    headers["Content-Type"] = "application/json"
  } else if (!options?.body && options?.method !== "GET" && options?.method !== "DELETE") {
    headers["Content-Type"] = "application/json"
  }
  
  try {
    const response = await fetch(url, {
      ...options,
      headers,
    })
    
    if (!response.ok) {
      let errorData
      try {
        errorData = await response.json()
      } catch {
        throw new APIError(
          `HTTP ${response.status}: ${response.statusText}`,
          response.status
        )
      }
      throw new APIError(
        errorData.detail || errorData.message || `HTTP ${response.status}`,
        response.status,
        errorData
      )
    }
    
    // Для DELETE запросов без body может не быть JSON ответа
    if (response.status === 204) {
      return {} as T
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
    if (error instanceof APIError) throw error
    if (error instanceof TypeError && error.message.includes("fetch")) {
      throw new APIError("Unable to connect to server", 503)
    }
    throw new APIError("An unexpected error occurred", 500)
  }
}

