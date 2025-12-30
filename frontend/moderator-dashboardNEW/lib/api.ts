// API client для взаимодействия с backend
const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000"

export class APIError extends Error {
  constructor(
    message: string,
    public status?: number,
    public detail?: string,
  ) {
    super(message)
    this.name = "APIError"
  }
}

export let isApiAvailable = true

export async function apiFetch<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`

  try {
    const response = await fetch(url, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...options?.headers,
      },
    })

    isApiAvailable = true

    if (!response.ok) {
      let detail = `HTTP ${response.status}`
      try {
        const errorData = await response.json()
        detail = errorData.detail || detail
      } catch {
        // Ignore JSON parse errors
      }
      throw new APIError(`Request failed: ${detail}`, response.status, detail)
    }

    if (response.status === 204) {
      return null as T
    }

    return await response.json()
  } catch (error) {
    if (error instanceof TypeError && error.message.includes("fetch")) {
      isApiAvailable = false
    }

    if (error instanceof APIError) {
      throw error
    }
    throw new APIError(`Network error: ${(error as Error).message}`)
  }
}

export function getApiBaseUrl(): string {
  return API_BASE_URL
}
