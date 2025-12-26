export interface SupplierDTO {
  id: number
  name: string
  inn: string | null
  email: string | null
  domain: string | null
  address: string | null
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
  
  createdAt: string
  updatedAt: string
}

export interface SupplierKeyword {
  keyword: string
  urlCount: number
  runId: string | null
  firstUrl: string | null
}

export interface KeywordDTO {
  id: number
  keyword: string
  createdAt: string
}

export interface BlacklistEntryDTO {
  domain: string
  reason: string | null
  addedBy: string | null
  addedAt: string
  parsingRunId: string | null
}

export interface ParsingRunDTO {
  runId: string
  keyword: string
  status: "running" | "completed" | "failed"
  startedAt: string
  finishedAt: string | null
  error: string | null
  resultsCount: number | null
}

export interface DomainQueueEntryDTO {
  domain: string
  keyword: string
  url: string
  parsingRunId: string | null
  status: string
  createdAt: string
}

