"use client"

import { useState, useEffect } from "react"
import { SupplierCard } from "@/components/supplier-card"
import { adaptSupplierDataToCard } from "@/lib/data-adapter"
import { fetchSupplier, fetchSuppliers, type SupplierDTO } from "@/lib/api-client"

// Пример данных для тестирования (fallback)
const mockSupplierData = {
  name: 'ООО "Пример Компании"',
  inn: "1234567890",
  registrationDate: "2010-05-15",
  companyStatus: "Действующая",
  finances: {
    "2020": { revenue: 100000000, profit: 10000000, changeFromPrevious: "+5.2%" },
    "2021": { revenue: 120000000, profit: 15000000, changeFromPrevious: "+20.0%" },
    "2022": { revenue: 150000000, profit: 18000000, changeFromPrevious: "+25.0%" },
    "2023": { revenue: 180000000, profit: 20000000, changeFromPrevious: "+20.0%" },
    "2024": { revenue: 200000000, profit: 25000000, changeFromPrevious: "+11.1%" },
  },
  risks: {
    arbitration: {
      total: 201,
      asPlaintiff: 0,
      asDefendant: 0,
      sum: 352800000000,
    },
    inspections: {
      total: 15,
      violations: 3,
    },
    enforcements: {
      count: 0,
    },
  },
}

export default function Page() {
  const [supplierData, setSupplierData] = useState(mockSupplierData)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [supplierId, setSupplierId] = useState<number | null>(null)

  // Fetch suppliers list on mount
  useEffect(() => {
    async function loadSuppliers() {
      try {
        setLoading(true)
        const suppliers = await fetchSuppliers()
        
        if (suppliers.length > 0) {
          // Use first supplier with Checko data, or first supplier
          const supplierWithChecko = suppliers.find(s => s.checkoData) || suppliers[0]
          setSupplierId(supplierWithChecko.id)
          
          // Adapt supplier data to card format
          const checkoData = supplierWithChecko.checkoData 
            ? JSON.parse(supplierWithChecko.checkoData) 
            : null
          
          const adaptedData = adaptSupplierDataToCard(supplierWithChecko, checkoData)
          setSupplierData(adaptedData)
        }
      } catch (err) {
        console.error("Failed to load suppliers:", err)
        setError(err instanceof Error ? err.message : "Ошибка загрузки данных")
        // Keep mock data as fallback
      } finally {
        setLoading(false)
      }
    }
    
    loadSuppliers()
  }, [])

  // Load specific supplier when ID changes
  useEffect(() => {
    if (!supplierId) return
    
    async function loadSupplier() {
      try {
        setLoading(true)
        const supplier = await fetchSupplier(supplierId)
        
        const checkoData = supplier.checkoData 
          ? JSON.parse(supplier.checkoData) 
          : null
        
        const adaptedData = adaptSupplierDataToCard(supplier, checkoData)
        setSupplierData(adaptedData)
      } catch (err) {
        console.error("Failed to load supplier:", err)
        setError(err instanceof Error ? err.message : "Ошибка загрузки данных")
      } finally {
        setLoading(false)
      }
    }
    
    loadSupplier()
  }, [supplierId])

  if (loading) {
    return (
      <div className="min-h-screen bg-background p-4 md:p-8">
        <div className="mx-auto max-w-4xl">
          <div className="text-center py-8">Загрузка данных...</div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen bg-background p-4 md:p-8">
        <div className="mx-auto max-w-4xl">
          <div className="text-center py-8 text-destructive">
            Ошибка: {error}
            <div className="mt-4 text-sm text-muted-foreground">
              Используются тестовые данные
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-background p-4 md:p-8">
      <div className="mx-auto max-w-4xl">
        <SupplierCard data={supplierData} />
      </div>
    </div>
  )
}
