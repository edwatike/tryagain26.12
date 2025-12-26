import { SupplierDetailClient } from "./supplier-detail-client"

export default function SupplierDetailPage({
  params,
}: {
  params: { id: string }
}) {
  return <SupplierDetailClient supplierId={parseInt(params.id)} />
}

