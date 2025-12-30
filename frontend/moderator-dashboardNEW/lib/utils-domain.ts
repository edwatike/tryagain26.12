// Утилиты для работы с доменами
export function extractRootDomain(url: string): string {
  try {
    // Убираем протокол
    let domain = url.replace(/^https?:\/\//, "").replace(/^www\./, "")

    // Берем только доменную часть (до первого /)
    domain = domain.split("/")[0]

    // Разбиваем на части
    const parts = domain.split(".")

    // Если 2 части или меньше - это уже root domain
    if (parts.length <= 2) {
      return domain
    }

    // Берем последние 2 части (example.com)
    return parts.slice(-2).join(".")
  } catch {
    return url
  }
}

export function groupByDomain(
  entries: Array<{
    domain: string
    url: string
    keyword: string
    status: string
    createdAt: string
  }>,
): Array<{
  domain: string
  urls: Array<{ url: string; keyword: string; status: string; createdAt: string }>
  totalUrls: number
}> {
  const groups = new Map<
    string,
    {
      domain: string
      urls: Array<{ url: string; keyword: string; status: string; createdAt: string }>
      totalUrls: number
    }
  >()

  for (const entry of entries) {
    const rootDomain = extractRootDomain(entry.domain)

    if (!groups.has(rootDomain)) {
      groups.set(rootDomain, {
        domain: rootDomain,
        urls: [],
        totalUrls: 0,
      })
    }

    const group = groups.get(rootDomain)!
    group.urls.push({
      url: entry.url,
      keyword: entry.keyword,
      status: entry.status,
      createdAt: entry.createdAt,
    })
    group.totalUrls++
  }

  return Array.from(groups.values())
}
