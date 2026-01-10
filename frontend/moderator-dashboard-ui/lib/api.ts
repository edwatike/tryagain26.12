import type {
  SupplierDTO,
  KeywordDTO,
  SupplierKeyword,
  BlacklistEntryDTO,
  ParsingRunDTO,
  DomainQueueEntryDTO,
  ParsingLogsDTO,
  INNExtractionBatchResponse,
  CometExtractBatchResponse,
  CometStatusResponse,
  DomainParserBatchResponse,
  DomainParserStatusResponse,
} from "./types"

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

/**
 * Выполняет API запрос с retry механизмом.
 * Повторяет запрос до 3 раз при временных ошибках (503, 504, network errors).
 */
export async function apiFetchWithRetry<T>(
  endpoint: string,
  options?: RequestInit,
  retries: number = 3
): Promise<T> {
  for (let attempt = 0; attempt < retries; attempt++) {
    try {
      return await apiFetch<T>(endpoint, options)
    } catch (error) {
      // Если это последняя попытка, пробрасываем ошибку
      if (attempt === retries - 1) {
        throw error
      }

      // Retry только для временных ошибок
      if (error instanceof APIError) {
        // Не повторяем для клиентских ошибок (4xx), кроме 408 (timeout)
        if (error.status >= 400 && error.status < 500 && error.status !== 408) {
          throw error
        }
        // Повторяем для серверных ошибок (5xx) и timeout (408)
        if (error.status >= 500 || error.status === 408 || error.status === 503 || error.status === 504) {
          const delay = 1000 * (attempt + 1) // Экспоненциальная задержка: 1s, 2s, 3s
          console.log(`[API Retry] Attempt ${attempt + 1}/${retries} failed, retrying in ${delay}ms...`)
          await new Promise((resolve) => setTimeout(resolve, delay))
          continue
        }
      }

      // Retry для network errors (TypeError с fetch)
      if (error instanceof TypeError && error.message.includes("fetch")) {
        const delay = 1000 * (attempt + 1)
        console.log(`[API Retry] Network error, retrying in ${delay}ms...`)
        await new Promise((resolve) => setTimeout(resolve, delay))
        continue
      }

      // Для других ошибок не повторяем
      throw error
    }
  }

  throw new APIError("Max retries exceeded", 500)
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
      
      // Разные уровни логирования для разных статусов
      // 404 - ожидаемая ошибка (ресурс не найден), логируем как warning
      // 400 - ожидаемая ошибка (неверный запрос), логируем как warning
      // 500+ - реальная ошибка сервера, логируем как error
      if (response.status === 404 || response.status === 400) {
        console.warn(`[API] ${response.status} ${errorMessage}:`, {
          endpoint: endpoint,
          url: url
        })
      } else {
        console.error(`[API Error] ${response.status}:`, {
          message: errorMessage,
          data: errorData,
          url: url,
          endpoint: endpoint
        })
      }
      
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
    // Если это APIError, не логируем здесь - уже залогировано выше (строка 116)
    if (error instanceof APIError) {
      throw error
    }
    
    // Логируем только неожиданные ошибки
    if (error instanceof TypeError && error.message.includes("fetch")) {
      const connectionError = new APIError("Unable to connect to server. Please ensure the backend is running.", 503)
      console.error("[API Fetch] Connection error:", connectionError.message)
      throw connectionError
    }
    
    // Логируем только действительно неожиданные ошибки
    console.error("[API Fetch] Unexpected error:", {
      error: error,
      url: url,
      endpoint: endpoint,
      errorType: error instanceof Error ? error.constructor.name : typeof error,
      errorMessage: error instanceof Error ? error.message : String(error)
    })
    
    const unexpectedError = new APIError("An unexpected error occurred", 500)
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

// Parsing runs API
export async function getParsingRuns(params?: {
  limit?: number
  offset?: number
  status?: string
  keyword?: string
  sort?: string
  order?: "asc" | "desc"
}): Promise<{
  runs: ParsingRunDTO[]
  total: number
  limit: number
  offset: number
}> {
  const queryParams = new URLSearchParams()
  if (params?.limit) queryParams.append("limit", params.limit.toString())
  if (params?.offset) queryParams.append("offset", params.offset.toString())
  if (params?.status) queryParams.append("status", params.status)
  if (params?.keyword) queryParams.append("keyword", params.keyword)
  if (params?.sort) queryParams.append("sort", params.sort)
  if (params?.order) queryParams.append("order", params.order)
  
  const queryString = queryParams.toString()
  return apiFetch<{
    runs: ParsingRunDTO[]
    total: number
    limit: number
    offset: number
  }>(`/parsing/runs${queryString ? `?${queryString}` : ""}`)
}

export async function getParsingRun(runId: string): Promise<ParsingRunDTO> {
  return apiFetch<ParsingRunDTO>(`/parsing/runs/${runId}`)
}

export async function getParsingLogs(runId: string): Promise<{ run_id: string; parsing_logs: ParsingLogsDTO }> {
  const url = `${API_BASE_URL}/parsing/runs/${runId}/logs`
  
  try {
    const response = await fetch(url, {
      method: "GET",
      headers: {
        "Content-Type": "application/json; charset=utf-8",
      },
    })
    
    if (!response.ok) {
      // Для 404 ошибки не логируем в консоль - это нормальная ситуация, если run еще не создан
      if (response.status === 404) {
        throw new APIError("Parsing run not found", 404, {})
      }
      
      // Для других ошибок логируем
      let errorData
      try {
        errorData = await response.json()
      } catch {
        const text = await response.text().catch(() => response.statusText)
        throw new APIError(
          `HTTP ${response.status}: ${response.statusText}`,
          response.status,
          { text }
        )
      }
      
      const errorMessage = errorData.detail || errorData.message || errorData.error || `HTTP ${response.status}`
      console.error(`[API Error] ${response.status}:`, {
        message: errorMessage,
        data: errorData,
        url: url,
        endpoint: `/parsing/runs/${runId}/logs`
      })
      
      throw new APIError(
        errorMessage,
        response.status,
        errorData
      )
    }
    
    // Парсим JSON ответ
    const contentType = response.headers.get("content-type")
    if (contentType && contentType.includes("application/json")) {
      return await response.json()
    }
    
    // Если нет JSON, возвращаем пустой объект
    const text = await response.text()
    if (text) {
      try {
        return JSON.parse(text) as { run_id: string; parsing_logs: ParsingLogsDTO }
      } catch {
        return { run_id: runId, parsing_logs: {} as ParsingLogsDTO }
      }
    }
    return { run_id: runId, parsing_logs: {} as ParsingLogsDTO }
  } catch (error) {
    // Если это APIError с 404, пробрасываем его дальше без логирования
    if (error instanceof APIError && error.status === 404) {
      throw error
    }
    
    // Для других ошибок логируем
    console.error("[API Fetch] Unexpected error:", {
      error: error,
      url: url,
      endpoint: `/parsing/runs/${runId}/logs`,
      errorType: error instanceof Error ? error.constructor.name : typeof error,
      errorMessage: error instanceof Error ? error.message : String(error)
    })
    throw error
  }
}

// Suppliers API
export async function getSuppliers(params?: {
  limit?: number
  offset?: number
  type?: string
}): Promise<{
  suppliers: SupplierDTO[]
  total: number
  limit: number
  offset: number
}> {
  const queryParams = new URLSearchParams()
  if (params?.limit) queryParams.append("limit", params.limit.toString())
  if (params?.offset) queryParams.append("offset", params.offset.toString())
  if (params?.type) queryParams.append("type", params.type)
  
  const queryString = queryParams.toString()
  return apiFetch<{
    suppliers: SupplierDTO[]
    total: number
    limit: number
    offset: number
  }>(`/moderator/suppliers${queryString ? `?${queryString}` : ""}`)
}

// Blacklist API
export async function getBlacklist(params?: {
  limit?: number
  offset?: number
}): Promise<{
  entries: BlacklistEntryDTO[]
  total: number
  limit: number
  offset: number
}> {
  const queryParams = new URLSearchParams()
  if (params?.limit) queryParams.append("limit", params.limit.toString())
  if (params?.offset) queryParams.append("offset", params.offset.toString())
  
  const queryString = queryParams.toString()
  return apiFetch<{
    entries: BlacklistEntryDTO[]
    total: number
    limit: number
    offset: number
  }>(`/moderator/blacklist${queryString ? `?${queryString}` : ""}`)
}

export async function addToBlacklist(data: {
  domain: string
  reason?: string | null
  addedBy?: string | null
  parsingRunId?: string | null
}): Promise<BlacklistEntryDTO> {
  return apiFetch<BlacklistEntryDTO>("/moderator/blacklist", {
    method: "POST",
    body: JSON.stringify(data),
  })
}

export async function removeFromBlacklist(domain: string): Promise<void> {
  return apiFetch<void>(`/moderator/blacklist/${encodeURIComponent(domain)}`, {
    method: "DELETE",
  })
}

// Parsing API
export async function startParsing(data: {
  keyword: string
  depth: number
  source: "google" | "yandex" | "both"
}): Promise<ParsingRunDTO> {
  return apiFetch<ParsingRunDTO>("/parsing/start", {
    method: "POST",
    body: JSON.stringify(data),
  })
}

export async function deleteParsingRun(runId: string): Promise<void> {
  return apiFetch<void>(`/parsing/runs/${runId}`, {
    method: "DELETE",
  })
}

export async function deleteParsingRunsBulk(runIds: string[]): Promise<{
  deleted: number
  total: number
  errors?: string[]
}> {
  return apiFetch<{
    deleted: number
    total: number
    errors?: string[]
  }>("/parsing/runs/bulk", {
    method: "DELETE",
    body: JSON.stringify(runIds),
  })
}

// Checko API
export interface CheckoDataResponse {
  name?: string | null
  ogrn?: string | null
  kpp?: string | null
  okpo?: string | null
  companyStatus?: string | null
  registrationDate?: string | null
  legalAddress?: string | null
  phone?: string | null
  website?: string | null
  vk?: string | null
  telegram?: string | null
  authorizedCapital?: number | null
  revenue?: number | null
  profit?: number | null
  financeYear?: number | null
  legalCasesCount?: number | null
  legalCasesSum?: number | null
  legalCasesAsPlaintiff?: number | null
  legalCasesAsDefendant?: number | null
  checkoData: string
}

export async function getCheckoData(inn: string, forceRefresh?: boolean): Promise<CheckoDataResponse> {
  const params = new URLSearchParams()
  if (forceRefresh) {
    params.append("force_refresh", "true")
  }
  const queryString = params.toString()
  const url = `/moderator/checko/${inn}${queryString ? `?${queryString}` : ""}`
  return apiFetch<CheckoDataResponse>(url)
}

// Suppliers API
export async function createSupplier(data: {
  name: string
  inn?: string | null
  email?: string | null
  domain?: string | null
  address?: string | null
  type: "supplier" | "reseller"
  // Checko fields
  ogrn?: string | null
  kpp?: string | null
  okpo?: string | null
  companyStatus?: string | null
  registrationDate?: string | null
  legalAddress?: string | null
  phone?: string | null
  website?: string | null
  vk?: string | null
  telegram?: string | null
  authorizedCapital?: number | null
  revenue?: number | null
  profit?: number | null
  financeYear?: number | null
  legalCasesCount?: number | null
  legalCasesSum?: number | null
  legalCasesAsPlaintiff?: number | null
  legalCasesAsDefendant?: number | null
  checkoData?: string | null
}): Promise<SupplierDTO> {
  return apiFetch<SupplierDTO>("/moderator/suppliers", {
    method: "POST",
    body: JSON.stringify(data),
  })
}

export async function updateSupplier(
  supplierId: number,
  data: {
    name?: string
    inn?: string | null
    email?: string | null
    domain?: string | null
    address?: string | null
    type?: "supplier" | "reseller"
    // Checko fields
    ogrn?: string | null
    kpp?: string | null
    okpo?: string | null
    companyStatus?: string | null
    registrationDate?: string | null
    legalAddress?: string | null
    phone?: string | null
    website?: string | null
    vk?: string | null
    telegram?: string | null
    authorizedCapital?: number | null
    revenue?: number | null
    profit?: number | null
    financeYear?: number | null
    legalCasesCount?: number | null
    legalCasesSum?: number | null
    legalCasesAsPlaintiff?: number | null
    legalCasesAsDefendant?: number | null
    checkoData?: string | null
  }
): Promise<SupplierDTO> {
  return apiFetch<SupplierDTO>(`/moderator/suppliers/${supplierId}`, {
    method: "PUT",
    body: JSON.stringify(data),
  })
}

export async function deleteSupplier(supplierId: number): Promise<void> {
  return apiFetch<void>(`/moderator/suppliers/${supplierId}`, {
    method: "DELETE",
  })
}

// Keywords API
export async function getKeywords(): Promise<{
  keywords: KeywordDTO[]
}> {
  return apiFetch<{
    keywords: KeywordDTO[]
  }>("/keywords")
}

export async function createKeyword(keyword: string): Promise<KeywordDTO> {
  return apiFetch<KeywordDTO>("/keywords", {
    method: "POST",
    body: JSON.stringify({ keyword }),
  })
}

export async function deleteKeyword(keywordId: number): Promise<void> {
  return apiFetch<void>(`/keywords/${keywordId}`, {
    method: "DELETE",
  })
}

// INN Extraction API
export async function extractINNBatch(domains: string[]): Promise<INNExtractionBatchResponse> {
  return apiFetch<INNExtractionBatchResponse>("/inn-extraction/extract-batch", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ domains }),
  })
}

// Comet Extraction API
export async function startCometExtractBatch(runId: string, domains: string[]): Promise<CometExtractBatchResponse> {
  return apiFetch<CometExtractBatchResponse>("/comet/extract-batch", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ runId, domains }),
  })
}

export async function getCometStatus(runId: string, cometRunId: string): Promise<CometStatusResponse> {
  const q = new URLSearchParams({ cometRunId }).toString()
  return apiFetch<CometStatusResponse>(`/comet/status/${runId}?${q}`)
}

// Domain Parser API
export async function startDomainParserBatch(runId: string, domains: string[]): Promise<DomainParserBatchResponse> {
  return apiFetch<DomainParserBatchResponse>("/domain-parser/extract-batch", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ runId, domains }),
  })
}

export async function getDomainParserStatus(parserRunId: string): Promise<DomainParserStatusResponse> {
  return apiFetch<DomainParserStatusResponse>(`/domain-parser/status/${parserRunId}`)
}

