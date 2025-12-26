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
  
  try {
    const response = await fetch(url, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...options?.headers,
      },
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
    
    return await response.json()
  } catch (error) {
    if (error instanceof APIError) throw error
    if (error instanceof TypeError && error.message.includes("fetch")) {
      throw new APIError("Unable to connect to server", 503)
    }
    throw new APIError("An unexpected error occurred", 500)
  }
}

