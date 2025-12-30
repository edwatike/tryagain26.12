/**
 * Adapter to convert backend SupplierDTO + CheckoData to SupplierCardData format
 */

interface SupplierDTO {
  id: number
  name: string
  inn?: string | null
  registrationDate?: string | null
  companyStatus?: string | null
  type: "supplier" | "reseller"
  checkoData?: string | null
  // ... other fields
}

interface CheckoData {
  _finances?: Record<string, {
    "2110"?: number // Revenue
    "2400"?: number // Profit
  }>
  _legal?: {
    asPlaintiff?: number
    asDefendant?: number
    total?: number
    sum?: number
  }
  _inspections?: {
    total?: number
    violations?: number
  }
  _enforcements?: {
    count?: number
  }
  Статус?: {
    Наим?: string
  }
  ДатаРег?: string
}

interface SupplierCardData {
  name: string
  inn: string
  registrationDate: string
  companyStatus: string
  finances: {
    [year: string]: {
      revenue: number
      profit: number
      changeFromPrevious?: string
    }
  }
  risks: {
    arbitration: {
      total: number
      asPlaintiff: number
      asDefendant: number
      sum: number
    }
    inspections: {
      total: number
      violations?: number
    }
    enforcements: {
      count: number
    }
  }
}

/**
 * Calculate percentage change between two values
 */
function calculatePercentageChange(current: number, previous: number): string {
  if (!previous || previous === 0) return ""
  const change = ((current - previous) / previous) * 100
  const sign = change > 0 ? "+" : ""
  return `${sign}${change.toFixed(1)}%`
}

/**
 * Convert backend SupplierDTO + CheckoData to SupplierCardData format
 */
export function adaptSupplierDataToCard(
  supplier: SupplierDTO,
  checkoData: CheckoData | null = null
): SupplierCardData {
  // Parse checkoData if it's a string
  let parsedCheckoData: CheckoData | null = checkoData
  if (!parsedCheckoData && supplier.checkoData && typeof supplier.checkoData === "string") {
    try {
      parsedCheckoData = JSON.parse(supplier.checkoData)
    } catch (e) {
      console.error("Failed to parse checkoData:", e)
      parsedCheckoData = null
    }
  }

  // Prepare finances
  const finances: SupplierCardData["finances"] = {}
  
  if (parsedCheckoData?._finances) {
    const financeYears = Object.keys(parsedCheckoData._finances).sort()
    
    financeYears.forEach((year, index) => {
      const yearData = parsedCheckoData!._finances![year]
      const revenue = yearData["2110"] ?? 0
      const profit = yearData["2400"] ?? 0
      
      // Calculate change from previous year
      let changeFromPrevious: string | undefined
      if (index < financeYears.length - 1) {
        const prevYear = financeYears[index + 1]
        const prevYearData = parsedCheckoData!._finances![prevYear]
        const prevRevenue = prevYearData["2110"] ?? 0
        
        if (prevRevenue > 0) {
          changeFromPrevious = calculatePercentageChange(revenue, prevRevenue)
        }
      }
      
      finances[year] = {
        revenue,
        profit,
        changeFromPrevious,
      }
    })
  }

  // Prepare risks
  const risks: SupplierCardData["risks"] = {
    arbitration: {
      total: supplier.legalCasesCount ?? parsedCheckoData?._legal?.total ?? 0,
      asPlaintiff: supplier.legalCasesAsPlaintiff ?? parsedCheckoData?._legal?.asPlaintiff ?? 0,
      asDefendant: supplier.legalCasesAsDefendant ?? parsedCheckoData?._legal?.asDefendant ?? 0,
      sum: supplier.legalCasesSum ?? parsedCheckoData?._legal?.sum ?? 0,
    },
    inspections: {
      total: parsedCheckoData?._inspections?.total ?? 0,
      violations: parsedCheckoData?._inspections?.violations,
    },
    enforcements: {
      count: parsedCheckoData?._enforcements?.count ?? 0,
    },
  }

  return {
    name: supplier.name || "Не указано",
    inn: supplier.inn || "Не указан",
    registrationDate: supplier.registrationDate || parsedCheckoData?.ДатаРег || new Date().toISOString(),
    companyStatus: supplier.companyStatus || parsedCheckoData?.Статус?.Наим || "Не указан",
    finances,
    risks,
  }
}

