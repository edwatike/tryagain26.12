"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { getSuppliers, deleteSupplier } from "@/lib/api"
import { SupplierDTO } from "@/lib/types"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import { Checkbox } from "@/components/ui/checkbox"
import { Navigation } from "@/components/navigation"
import { toast } from "sonner"
import { Trash2 } from "lucide-react"

export function SuppliersClient() {
  const router = useRouter()
  const [suppliers, setSuppliers] = useState<SupplierDTO[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set())
  const [deleting, setDeleting] = useState(false)

  useEffect(() => {
    loadSuppliers()
  }, [])

  async function loadSuppliers() {
    try {
      setLoading(true)
      const data = await getSuppliers({ limit: 100, offset: 0 })
      setSuppliers(data.suppliers)
      setError(null)
      // Очищаем выбор при загрузке новых данных
      setSelectedIds(new Set())
    } catch (err) {
      toast.error("Ошибка загрузки поставщиков")
      setError("Ошибка загрузки поставщиков")
      console.error("Error loading suppliers:", err)
    } finally {
      setLoading(false)
    }
  }

  function handleToggleSelect(supplierId: number) {
    setSelectedIds((prev) => {
      const newSet = new Set(prev)
      if (newSet.has(supplierId)) {
        newSet.delete(supplierId)
      } else {
        newSet.add(supplierId)
      }
      return newSet
    })
  }

  function handleSelectAll() {
    if (selectedIds.size === suppliers.length) {
      setSelectedIds(new Set())
    } else {
      setSelectedIds(new Set(suppliers.map((s) => s.id)))
    }
  }

  async function handleDeleteSelected() {
    if (selectedIds.size === 0) {
      toast.error("Выберите поставщиков для удаления")
      return
    }

    if (!confirm(`Удалить ${selectedIds.size} поставщик(ов)?`)) {
      return
    }

    try {
      setDeleting(true)
      const deletePromises = Array.from(selectedIds).map((id) => deleteSupplier(id))
      await Promise.all(deletePromises)
      toast.success(`Удалено поставщиков: ${selectedIds.size}`)
      setSelectedIds(new Set())
      await loadSuppliers()
    } catch (err) {
      toast.error("Ошибка удаления поставщиков")
      console.error("Error deleting suppliers:", err)
    } finally {
      setDeleting(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-background">
        <Navigation />
        <main className="container mx-auto px-6 py-6">
          <div className="text-center text-muted-foreground">Загрузка...</div>
        </main>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen bg-background">
        <Navigation />
        <main className="container mx-auto px-6 py-6">
          <div className="text-red-500">Ошибка: {error}</div>
        </main>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-background">
      <Navigation />
      <main className="container mx-auto px-6 py-6 max-w-7xl">
        <Card>
          <CardHeader>
            <div className="flex justify-between items-center">
              <CardTitle className="text-4xl font-bold">Поставщики</CardTitle>
              <div className="flex gap-2">
                {selectedIds.size > 0 && (
                  <Button
                    variant="destructive"
                    onClick={handleDeleteSelected}
                    disabled={deleting}
                    className="gap-2"
                  >
                    <Trash2 className="h-4 w-4" />
                    Удалить выбранные ({selectedIds.size})
                  </Button>
                )}
                <Button onClick={() => router.push("/suppliers/new")}>
                  Добавить поставщика
                </Button>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            {suppliers.length === 0 ? (
              <div className="text-center py-12 text-muted-foreground">Поставщики не найдены</div>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-12">
                      <Checkbox
                        checked={selectedIds.size === suppliers.length && suppliers.length > 0}
                        onCheckedChange={handleSelectAll}
                        aria-label="Выбрать все"
                      />
                    </TableHead>
                    <TableHead>ID</TableHead>
                    <TableHead>Название</TableHead>
                    <TableHead>ИНН</TableHead>
                    <TableHead>Email</TableHead>
                    <TableHead>Домен</TableHead>
                    <TableHead>Тип</TableHead>
                    <TableHead>Действия</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {suppliers.map((supplier) => (
                    <TableRow key={supplier.id}>
                      <TableCell>
                        <Checkbox
                          checked={selectedIds.has(supplier.id)}
                          onCheckedChange={() => handleToggleSelect(supplier.id)}
                          aria-label={`Выбрать ${supplier.name}`}
                        />
                      </TableCell>
                      <TableCell>{supplier.id}</TableCell>
                      <TableCell className="font-medium">{supplier.name}</TableCell>
                      <TableCell>{supplier.inn || "—"}</TableCell>
                      <TableCell>{supplier.email || "—"}</TableCell>
                      <TableCell className="font-mono text-sm">{supplier.domain || "—"}</TableCell>
                      <TableCell>
                        <Badge variant={supplier.type === "supplier" ? "default" : "outline"}>
                          {supplier.type === "supplier" ? "Поставщик" : "Реселлер"}
                        </Badge>
                      </TableCell>
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
            )}
          </CardContent>
        </Card>
      </main>
    </div>
  )
}

