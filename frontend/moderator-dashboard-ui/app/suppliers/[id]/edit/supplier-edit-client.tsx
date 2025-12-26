"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { apiFetch, APIError } from "@/lib/api"
import { SupplierDTO } from "@/lib/types"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { CheckoInfoDialog } from "@/components/checko-info-dialog"

export function SupplierEditClient({ supplierId }: { supplierId: number }) {
  const router = useRouter()
  const [supplier, setSupplier] = useState<SupplierDTO | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [formData, setFormData] = useState({
    name: "",
    inn: "",
    email: "",
    domain: "",
    address: "",
    type: "supplier" as "supplier" | "reseller",
  })

  useEffect(() => {
    loadSupplier()
  }, [supplierId])

  async function loadSupplier() {
    try {
      setLoading(true)
      const data = await apiFetch<SupplierDTO>(`/moderator/suppliers/${supplierId}`)
      setSupplier(data)
      setFormData({
        name: data.name || "",
        inn: data.inn || "",
        email: data.email || "",
        domain: data.domain || "",
        address: data.address || "",
        type: data.type || "supplier",
      })
      setError(null)
    } catch (err) {
      if (err instanceof APIError) {
        setError(err.message)
      } else {
        setError("Ошибка загрузки поставщика")
      }
    } finally {
      setLoading(false)
    }
  }

  async function handleSave() {
    try {
      setSaving(true)
      await apiFetch(`/moderator/suppliers/${supplierId}`, {
        method: "PUT",
        body: JSON.stringify(formData),
      })
      router.push(`/suppliers/${supplierId}`)
    } catch (err) {
      if (err instanceof APIError) {
        setError(err.message)
      } else {
        setError("Ошибка сохранения")
      }
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return <div>Загрузка...</div>
  }

  if (error || !supplier) {
    return <div className="text-red-500">Ошибка: {error || "Поставщик не найден"}</div>
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">Редактирование поставщика</h1>
        <Button variant="outline" onClick={() => router.back()}>
          Отмена
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Основная информация</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <Label htmlFor="name">Название</Label>
            <Input
              id="name"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            />
          </div>

          <div>
            <div className="flex items-center gap-2">
              <div className="flex-1">
                <Label htmlFor="inn">ИНН</Label>
                <Input
                  id="inn"
                  value={formData.inn}
                  onChange={(e) => setFormData({ ...formData, inn: e.target.value })}
                />
              </div>
              <div className="pt-6">
                <CheckoInfoDialog
                  inn={formData.inn}
                  onDataLoaded={(data) => {
                    setFormData({ ...formData, ...data })
                  }}
                />
              </div>
            </div>
          </div>

          <div>
            <Label htmlFor="email">Email</Label>
            <Input
              id="email"
              type="email"
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
            />
          </div>

          <div>
            <Label htmlFor="domain">Домен</Label>
            <Input
              id="domain"
              value={formData.domain}
              onChange={(e) => setFormData({ ...formData, domain: e.target.value })}
            />
          </div>

          <div>
            <Label htmlFor="address">Адрес</Label>
            <Input
              id="address"
              value={formData.address}
              onChange={(e) => setFormData({ ...formData, address: e.target.value })}
            />
          </div>

          <div>
            <Label htmlFor="type">Тип</Label>
            <select
              id="type"
              value={formData.type}
              onChange={(e) => setFormData({ ...formData, type: e.target.value as "supplier" | "reseller" })}
              className="w-full rounded-md border border-input bg-background px-3 py-2"
            >
              <option value="supplier">Поставщик</option>
              <option value="reseller">Реселлер</option>
            </select>
          </div>

          <div className="flex gap-2">
            <Button onClick={handleSave} disabled={saving}>
              {saving ? "Сохранение..." : "Сохранить"}
            </Button>
            <Button variant="outline" onClick={() => router.back()}>
              Отмена
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

