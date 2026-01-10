/**
 * API client for fetching supplier data from backend
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000"

export interface SupplierDTO {
  id: number
  name: string
  inn?: string | null
  registrationDate?: string | null
  companyStatus?: string | null
  type: "supplier" | "reseller"
  checkoData?: string | null
  legalCasesCount?: number | null
  legalCasesSum?: number | null
  legalCasesAsPlaintiff?: number | null
  legalCasesAsDefendant?: number | null
}

/**
 * Fetch supplier by ID from backend
 */
export async function fetchSupplier(supplierId: number): Promise<SupplierDTO> {
  const response = await fetch(`${API_BASE_URL}/moderator/suppliers/${supplierId}`)
  
  if (!response.ok) {
    throw new Error(`Failed to fetch supplier: ${response.statusText}`)
  }
  
  return response.json()
}

/**
 * Fetch all suppliers from backend
 */
export async function fetchSuppliers(): Promise<SupplierDTO[]> {
  const response = await fetch(`${API_BASE_URL}/moderator/suppliers?limit=1000`)
  
  if (!response.ok) {
    throw new Error(`Failed to fetch suppliers: ${response.statusText}`)
  }
  
  const data = await response.json()
  return data.items || []
}


