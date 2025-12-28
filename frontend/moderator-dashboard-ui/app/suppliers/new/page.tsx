import { SupplierEditClient } from "../[id]/edit/supplier-edit-client"

export default function NewSupplierPage() {
  // Для создания нового поставщика передаем 0 или null
  // SupplierEditClient должен обрабатывать это как режим создания
  return <SupplierEditClient supplierId={0} />
}







