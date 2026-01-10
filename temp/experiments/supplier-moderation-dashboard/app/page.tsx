import { SupplierCard } from "@/components/supplier-card"
import type { SupplierDTO } from "@/lib/types"

// Example data for demonstration
const exampleSupplier: SupplierDTO = {
  id: 1,
  name: 'ООО "СТД ПЕТРОВИЧ"',
  inn: "7802348846",
  type: "supplier",
  email: "info@petrovich.ru",
  domain: "petrovich.ru",
  address: "г. Санкт-Петербург",
  ogrn: "1027802497020",
  kpp: "780201001",
  okpo: "12345678",
  companyStatus: "Действующая",
  registrationDate: "2002-08-27T00:00:00.000Z",
  legalAddress: "г. Санкт-Петербург, ул. Примерная, д. 1",
  phone: "+7 (812) 123-45-67",
  website: "https://petrovich.ru",
  vk: "https://vk.com/petrovich",
  telegram: "https://t.me/petrovich",
  authorizedCapital: 10000000,
  revenue: 147500000000,
  profit: 9700000000,
  financeYear: 2024,
  legalCasesCount: 1136,
  legalCasesSum: 5600000000,
  legalCasesAsPlaintiff: 1063,
  legalCasesAsDefendant: 73,
  checkoData: JSON.stringify({
    rating: 553,
    _finances: {
      "2021": {
        "2110": 105000000000,
        "2400": 7800000000,
      },
      "2022": {
        "2110": 118000000000,
        "2400": 8500000000,
      },
      "2023": {
        "2110": 125000000000,
        "2400": 9300000000,
      },
    },
    _inspections: {
      total: 372,
      violations: 20,
    },
    _enforcements: {
      count: 1,
    },
    Учред: [
      { name: "Иванов Иван Иванович", share: 50 },
      { name: "Петров Петр Петрович", share: 25 },
      { name: "Сидоров Сидор Сидорович", share: 25 },
    ],
  }),
  createdAt: "2024-01-01T00:00:00.000Z",
  updatedAt: "2024-12-29T00:00:00.000Z",
}

export default function Page() {
  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="mb-2 text-4xl font-bold text-balance">Модерация поставщиков</h1>
        <p className="text-muted-foreground text-pretty">Детальная информация о поставщике с данными из Checko API</p>
      </div>

      <SupplierCard supplier={exampleSupplier} />
    </div>
  )
}
