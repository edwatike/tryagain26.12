import { SupplierEditClient } from "./supplier-edit-client"

export default function SupplierEditPage({
  params,
}: {
  params: { id: string }
}) {
  return <SupplierEditClient supplierId={parseInt(params.id)} />
}

