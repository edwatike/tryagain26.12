// TypeScript типы для API

export interface ParsingRunDTO {
  runId: string
  keyword: string
  depth?: number
  source?: "google" | "yandex" | "both"
  status: string
  startedAt: string | null
  finishedAt: string | null
  error: string | null
  resultsCount: number | null
  createdAt: string
}

export interface ParsingRunsResponse {
  runs: ParsingRunDTO[]
  total: number
  limit: number
  offset: number
}

export interface DomainQueueEntryDTO {
  domain: string
  keyword: string
  url: string
  parsingRunId: string | null
  status: string
  createdAt: string
}

export interface DomainsQueueResponse {
  entries: DomainQueueEntryDTO[]
  total: number
  limit: number
  offset: number
}

export interface BlacklistEntryDTO {
  domain: string
  reason: string | null
  addedBy: string | null
  addedAt: string | null
  parsingRunId: string | null
}

export interface BlacklistResponse {
  entries: BlacklistEntryDTO[]
  total: number
  limit: number
  offset: number
}

export interface SupplierDTO {
  id: number
  name: string
  inn: string | null
  email: string | null
  domain: string | null
  address: string | null
  type: "supplier" | "reseller"
  createdAt: string
  updatedAt: string
}

export interface SuppliersResponse {
  suppliers: SupplierDTO[]
  total: number
  limit: number
  offset: number
}

export interface ParsingDomainGroup {
  domain: string
  urls: Array<{
    url: string
    keyword: string
    status: string
    createdAt: string
  }>
  totalUrls: number
}
