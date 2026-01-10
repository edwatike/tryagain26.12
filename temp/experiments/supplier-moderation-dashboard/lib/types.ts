// Type definitions for supplier data

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

  // Financial data
  revenue?: number | null
  profit?: number | null
  financeYear?: number | null

  // Legal cases
  legalCasesCount?: number | null
  legalCasesSum?: number | null
  legalCasesAsPlaintiff?: number | null
  legalCasesAsDefendant?: number | null

  checkoData?: string | null

  createdAt: string
  updatedAt: string
}

export interface CheckoData {
  rating?: number
  _finances?: Record<string, FinanceYear>
  _legal?: LegalData
  _inspections?: InspectionData
  _enforcements?: EnforcementData
  Учред?: Founder[]
  Руковод?: Leader[]
}

export interface FinanceYear {
  "2110"?: number // Revenue
  "2400"?: number // Profit
}

export interface LegalData {
  asPlaintiff?: number
  asDefendant?: number
  total?: number
  sum?: number
}

export interface InspectionData {
  total?: number
  violations?: number
}

export interface EnforcementData {
  count?: number
}

export interface Founder {
  name: string
  share?: number
}

export interface Leader {
  name: string
  position?: string
}

export interface SupplierKeyword {
  keyword: string
  urlCount: number
}
