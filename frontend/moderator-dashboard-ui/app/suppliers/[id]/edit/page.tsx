import { SupplierEditClient } from "./supplier-edit-client"

export default async function SupplierEditPage({
  params,
}: {
  params: Promise<{ id: string }>
}) {
  const { id } = await params
  const supplierId = parseInt(id, 10)
  
  // Проверяем, что ID валиден
  if (isNaN(supplierId) || supplierId <= 0) {
    return (
      <div className="text-red-500 p-4">
        Ошибка: Неверный ID поставщика
      </div>
    )
  }
  
  return <SupplierEditClient supplierId={supplierId} />
}

