"use client"

import { useState, useEffect } from "react"
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Navigation } from "@/components/navigation"
import { getSuppliers } from "@/lib/api-functions"
import { toast } from "sonner"
import { Search } from "lucide-react"
import type { SupplierDTO } from "@/lib/types"

export default function SuppliersPage() {
  const [suppliers, setSuppliers] = useState<SupplierDTO[]>([])
  const [loading, setLoading] = useState(true)
  const [typeFilter, setTypeFilter] = useState<string>("all")
  const [searchQuery, setSearchQuery] = useState("")

  useEffect(() => {
    loadSuppliers()
  }, [typeFilter])

  async function loadSuppliers() {
    setLoading(true)
    try {
      const params: any = { limit: 100 }
      if (typeFilter !== "all") {
        params.type = typeFilter
      }

      const data = await getSuppliers(params)
      let filtered = data.suppliers

      if (searchQuery) {
        const query = searchQuery.toLowerCase()
        filtered = filtered.filter(
          (s) =>
            s.name.toLowerCase().includes(query) ||
            s.inn?.toLowerCase().includes(query) ||
            s.email?.toLowerCase().includes(query) ||
            s.domain?.toLowerCase().includes(query),
        )
      }

      setSuppliers(filtered)
    } catch (error) {
      toast.error("Ошибка загрузки данных")
      console.error("[v0] Error loading suppliers:", error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-background">
      <Navigation />

      <main className="container mx-auto px-6 py-12 max-w-7xl">
        <h1 className="text-4xl font-bold mb-8">Поставщики</h1>

        <Card className="mb-8">
          <div className="p-6">
            <div className="flex flex-col md:flex-row gap-4 mb-6">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Поиск по названию, ИНН, email..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && loadSuppliers()}
                  className="pl-10"
                />
              </div>
              <div className="flex gap-2">
                <Button variant={typeFilter === "all" ? "default" : "outline"} onClick={() => setTypeFilter("all")}>
                  Все
                </Button>
                <Button
                  variant={typeFilter === "supplier" ? "default" : "outline"}
                  onClick={() => setTypeFilter("supplier")}
                >
                  Поставщики
                </Button>
                <Button
                  variant={typeFilter === "reseller" ? "default" : "outline"}
                  onClick={() => setTypeFilter("reseller")}
                >
                  Реселлеры
                </Button>
              </div>
            </div>

            {loading ? (
              <div className="text-center py-12 text-muted-foreground">Загрузка...</div>
            ) : suppliers.length === 0 ? (
              <div className="text-center py-12 text-muted-foreground">Поставщики не найдены</div>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Название</TableHead>
                    <TableHead>ИНН</TableHead>
                    <TableHead>Email</TableHead>
                    <TableHead>Домен</TableHead>
                    <TableHead>Тип</TableHead>
                    <TableHead>Создан</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {suppliers.map((supplier) => (
                    <TableRow key={supplier.id}>
                      <TableCell className="font-medium">{supplier.name}</TableCell>
                      <TableCell>{supplier.inn || "—"}</TableCell>
                      <TableCell>{supplier.email || "—"}</TableCell>
                      <TableCell className="font-mono text-sm">{supplier.domain || "—"}</TableCell>
                      <TableCell>
                        <Badge variant={supplier.type === "supplier" ? "default" : "outline"}>
                          {supplier.type === "supplier" ? "Поставщик" : "Реселлер"}
                        </Badge>
                      </TableCell>
                      <TableCell>{new Date(supplier.createdAt).toLocaleDateString("ru-RU")}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </div>
        </Card>
      </main>
    </div>
  )
}
