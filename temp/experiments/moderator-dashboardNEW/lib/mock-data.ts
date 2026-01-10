import type { ParsingRunDTO, DomainQueueItemDTO, SupplierDTO, BlacklistEntryDTO } from "./types"

// Mock данные для демонстрации
export const mockParsingRuns: ParsingRunDTO[] = [
  {
    runId: "mock-run-1",
    keyword: "кирпич",
    depth: 5,
    source: "both",
    status: "completed",
    createdAt: new Date(Date.now() - 1000 * 60 * 60 * 24).toISOString(),
    completedAt: new Date(Date.now() - 1000 * 60 * 60 * 23).toISOString(),
    resultsCount: 142,
  },
  {
    runId: "mock-run-2",
    keyword: "цемент",
    depth: 5,
    source: "yandex",
    status: "running",
    createdAt: new Date(Date.now() - 1000 * 60 * 30).toISOString(),
    completedAt: null,
    resultsCount: null,
  },
  {
    runId: "mock-run-3",
    keyword: "арматура",
    depth: 3,
    source: "google",
    status: "completed",
    createdAt: new Date(Date.now() - 1000 * 60 * 60 * 48).toISOString(),
    completedAt: new Date(Date.now() - 1000 * 60 * 60 * 47).toISOString(),
    resultsCount: 89,
  },
  {
    runId: "mock-run-4",
    keyword: "труба металлическая",
    depth: 5,
    source: "both",
    status: "completed",
    createdAt: new Date(Date.now() - 1000 * 60 * 60 * 72).toISOString(),
    completedAt: new Date(Date.now() - 1000 * 60 * 60 * 71).toISOString(),
    resultsCount: 215,
  },
]

export const mockDomains: DomainQueueItemDTO[] = [
  {
    domain: "stroymaterialy.ru",
    firstSeenAt: new Date(Date.now() - 1000 * 60 * 60 * 12).toISOString(),
    attempts: 0,
    status: "pending",
  },
  {
    domain: "kirpich-opt.com",
    firstSeenAt: new Date(Date.now() - 1000 * 60 * 60 * 6).toISOString(),
    attempts: 1,
    status: "pending",
  },
]

export const mockSuppliers: SupplierDTO[] = [
  {
    supplierId: "mock-supplier-1",
    name: "СтройМатериалы Плюс",
    domain: "stroymaterialy-plus.ru",
    email: "info@stroymaterialy-plus.ru",
    phone: "+7 (495) 123-45-67",
    createdAt: new Date(Date.now() - 1000 * 60 * 60 * 24).toISOString(),
    moderationStatus: "approved",
    moderatedAt: new Date(Date.now() - 1000 * 60 * 60 * 12).toISOString(),
  },
  {
    supplierId: "mock-supplier-2",
    name: "Кирпич-Опт",
    domain: "kirpich-opt.com",
    email: "zakaz@kirpich-opt.com",
    phone: "+7 (812) 987-65-43",
    createdAt: new Date(Date.now() - 1000 * 60 * 60 * 6).toISOString(),
    moderationStatus: "pending",
    moderatedAt: null,
  },
]

export const mockBlacklist: BlacklistEntryDTO[] = [
  {
    domain: "spam-site.ru",
    reason: "Спам сайт без контактов",
    addedAt: new Date(Date.now() - 1000 * 60 * 60 * 24 * 7).toISOString(),
  },
  {
    domain: "fake-supplier.com",
    reason: "Недостоверная информация",
    addedAt: new Date(Date.now() - 1000 * 60 * 60 * 24 * 3).toISOString(),
  },
]

export const mockStats = {
  domainsInQueue: 47,
  newSuppliers: 23,
  activeRuns: 1,
  blacklistCount: 12,
}
