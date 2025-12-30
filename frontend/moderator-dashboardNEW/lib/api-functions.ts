// API функции для работы с backend
import { apiFetch } from "./api"
import type {
  ParsingRunsResponse,
  ParsingRunDTO,
  DomainsQueueResponse,
  BlacklistResponse,
  BlacklistEntryDTO,
  SuppliersResponse,
  SupplierDTO,
} from "./types"
import { mockParsingRuns, mockDomains, mockSuppliers, mockBlacklist, mockStats } from "./mock-data"

// Parsing Runs
export async function getParsingRuns(params?: {
  limit?: number
  offset?: number
  status?: string
  keyword?: string
  sort?: string
  order?: string
}): Promise<ParsingRunsResponse> {
  try {
    const queryParams = new URLSearchParams()
    if (params?.limit) queryParams.set("limit", params.limit.toString())
    if (params?.offset) queryParams.set("offset", params.offset.toString())
    if (params?.status) queryParams.set("status", params.status)
    if (params?.keyword) queryParams.set("keyword", params.keyword)
    if (params?.sort) queryParams.set("sort", params.sort)
    if (params?.order) queryParams.set("order", params.order)

    return await apiFetch<ParsingRunsResponse>(`/parsing/runs?${queryParams.toString()}`)
  } catch (error) {
    // Fallback to mock data
    let runs = [...mockParsingRuns]

    if (params?.status) {
      runs = runs.filter((r) => r.status === params.status)
    }
    if (params?.keyword) {
      runs = runs.filter((r) => r.keyword.toLowerCase().includes(params.keyword!.toLowerCase()))
    }

    const limit = params?.limit || 10
    const offset = params?.offset || 0

    return {
      runs: runs.slice(offset, offset + limit),
      total: runs.length,
    }
  }
}

export async function getParsingRun(runId: string): Promise<ParsingRunDTO> {
  try {
    return await apiFetch<ParsingRunDTO>(`/parsing/runs/${runId}`)
  } catch (error) {
    // Fallback to mock data
    const run = mockParsingRuns.find((r) => r.runId === runId)
    if (!run) throw new Error("Запуск не найден")
    return run
  }
}

export async function startParsing(data: {
  keyword: string
  depth: number
  source: "google" | "yandex" | "both"
}): Promise<ParsingRunDTO> {
  try {
    return await apiFetch<ParsingRunDTO>("/parsing/start", {
      method: "POST",
      body: JSON.stringify(data),
    })
  } catch (error) {
    // Fallback: create mock run
    const newRun: ParsingRunDTO = {
      runId: `mock-run-${Date.now()}`,
      keyword: data.keyword,
      depth: data.depth,
      source: data.source,
      status: "running",
      createdAt: new Date().toISOString(),
      completedAt: null,
      resultsCount: null,
    }
    mockParsingRuns.unshift(newRun)
    return newRun
  }
}

export async function deleteParsingRun(runId: string): Promise<void> {
  try {
    return await apiFetch<void>(`/parsing/runs/${runId}`, {
      method: "DELETE",
    })
  } catch (error) {
    // Fallback: remove from mock data
    const index = mockParsingRuns.findIndex((r) => r.runId === runId)
    if (index !== -1) {
      mockParsingRuns.splice(index, 1)
    }
  }
}

// Domains Queue
export async function getDomainsQueue(params?: {
  limit?: number
  offset?: number
  status?: string
  keyword?: string
  parsingRunId?: string
}): Promise<DomainsQueueResponse> {
  try {
    const queryParams = new URLSearchParams()
    if (params?.limit) queryParams.set("limit", params.limit.toString())
    if (params?.offset) queryParams.set("offset", params.offset.toString())
    if (params?.status) queryParams.set("status", params.status)
    if (params?.keyword) queryParams.set("keyword", params.keyword)
    if (params?.parsingRunId) queryParams.set("parsingRunId", params.parsingRunId)

    return await apiFetch<DomainsQueueResponse>(`/domains/queue?${queryParams.toString()}`)
  } catch (error) {
    // Fallback to mock data
    return {
      domains: mockDomains,
      total: mockStats.domainsInQueue,
    }
  }
}

// Blacklist
export async function getBlacklist(params?: {
  limit?: number
  offset?: number
}): Promise<BlacklistResponse> {
  try {
    const queryParams = new URLSearchParams()
    if (params?.limit) queryParams.set("limit", params.limit.toString())
    if (params?.offset) queryParams.set("offset", params.offset.toString())

    return await apiFetch<BlacklistResponse>(`/moderator/blacklist?${queryParams.toString()}`)
  } catch (error) {
    // Fallback to mock data
    return {
      entries: mockBlacklist,
      total: mockStats.blacklistCount,
    }
  }
}

export async function addToBlacklist(data: {
  domain: string
  reason?: string | null
  addedBy?: string | null
  parsingRunId?: string | null
}): Promise<BlacklistEntryDTO> {
  try {
    return await apiFetch<BlacklistEntryDTO>("/moderator/blacklist", {
      method: "POST",
      body: JSON.stringify(data),
    })
  } catch (error) {
    // Fallback: add to mock data
    const newEntry: BlacklistEntryDTO = {
      domain: data.domain,
      reason: data.reason || null,
      addedAt: new Date().toISOString(),
    }
    mockBlacklist.unshift(newEntry)
    return newEntry
  }
}

export async function removeFromBlacklist(domain: string): Promise<void> {
  try {
    return await apiFetch<void>(`/moderator/blacklist/${encodeURIComponent(domain)}`, {
      method: "DELETE",
    })
  } catch (error) {
    // Fallback: remove from mock data
    const index = mockBlacklist.findIndex((e) => e.domain === domain)
    if (index !== -1) {
      mockBlacklist.splice(index, 1)
    }
  }
}

// Suppliers
export async function getSuppliers(params?: {
  limit?: number
  offset?: number
  type?: string
}): Promise<SuppliersResponse> {
  try {
    const queryParams = new URLSearchParams()
    if (params?.limit) queryParams.set("limit", params.limit.toString())
    if (params?.offset) queryParams.set("offset", params.offset.toString())
    if (params?.type) queryParams.set("type", params.type)

    return await apiFetch<SuppliersResponse>(`/moderator/suppliers?${queryParams.toString()}`)
  } catch (error) {
    // Fallback to mock data
    return {
      suppliers: mockSuppliers,
      total: mockStats.newSuppliers,
    }
  }
}

export async function createSupplier(data: {
  name: string
  inn?: string | null
  email?: string | null
  domain?: string | null
  address?: string | null
  type: "supplier" | "reseller"
}): Promise<SupplierDTO> {
  try {
    return await apiFetch<SupplierDTO>("/moderator/suppliers", {
      method: "POST",
      body: JSON.stringify(data),
    })
  } catch (error) {
    // Fallback: create mock supplier
    const newSupplier: SupplierDTO = {
      supplierId: `mock-supplier-${Date.now()}`,
      name: data.name,
      domain: data.domain || null,
      email: data.email || null,
      phone: null,
      createdAt: new Date().toISOString(),
      moderationStatus: "pending",
      moderatedAt: null,
    }
    mockSuppliers.unshift(newSupplier)
    return newSupplier
  }
}
