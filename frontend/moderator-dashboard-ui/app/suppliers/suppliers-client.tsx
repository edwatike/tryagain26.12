"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { apiFetch, APIError } from "@/lib/api"
import { SupplierDTO } from "@/lib/types"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"

export function SuppliersClient() {
  const router = useRouter()
  const [suppliers, setSuppliers] = useState<SupplierDTO[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadSuppliers()
  }, [])

  async function loadSuppliers() {
    try {
      setLoading(true)
      const data = await apiFetch<{ suppliers: SupplierDTO[]; total: number }>(
        "/moderator/suppliers?limit=100&offset=0"
      )
      setSuppliers(data.suppliers)
      setError(null)
    } catch (err) {
      if (err instanceof APIError) {
        setError(err.message)
      } else {
        setError("Ошибка загрузки поставщиков")
      }
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return <div>Загрузка...</div>
  }

  if (error) {
    return <div className="text-red-500">Ошибка: {error}</div>
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex justify-between items-center">
          <CardTitle>Поставщики</CardTitle>
          <Button onClick={() => router.push("/suppliers/new")}>
            Добавить поставщика
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>ID</TableHead>
              <TableHead>Название</TableHead>
              <TableHead>ИНН</TableHead>
              <TableHead>Email</TableHead>
              <TableHead>Домен</TableHead>
              <TableHead>Действия</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {suppliers.map((supplier) => (
              <TableRow key={supplier.id}>
                <TableCell>{supplier.id}</TableCell>
                <TableCell>{supplier.name}</TableCell>
                <TableCell>{supplier.inn || "—"}</TableCell>
                <TableCell>{supplier.email || "—"}</TableCell>
                <TableCell>{supplier.domain || "—"}</TableCell>
                <TableCell>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => router.push(`/suppliers/${supplier.id}`)}
                  >
                    Открыть
                  </Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  )
}

