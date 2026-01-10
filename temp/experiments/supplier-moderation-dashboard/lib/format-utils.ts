// Utility functions for formatting data

export function formatCurrency(value: number | null | undefined): string {
  if (!value) return "—"

  const abs = Math.abs(value)

  if (abs >= 1_000_000_000) {
    return `${(value / 1_000_000_000).toFixed(1)} млрд ₽`
  } else if (abs >= 1_000_000) {
    return `${(value / 1_000_000).toFixed(1)} млн ₽`
  } else if (abs >= 1_000) {
    return `${(value / 1_000).toFixed(1)} тыс. ₽`
  }

  return `${value.toLocaleString("ru-RU")} ₽`
}

export function formatDate(dateString: string | null | undefined): string {
  if (!dateString) return "—"

  try {
    const date = new Date(dateString)
    return date.toLocaleDateString("ru-RU", {
      year: "numeric",
      month: "long",
      day: "numeric",
    })
  } catch {
    return "—"
  }
}

export function calculatePercentageChange(current: number, previous: number): string {
  if (!previous) return ""

  const change = ((current - previous) / previous) * 100
  const sign = change > 0 ? "+" : ""

  return `${sign}${change.toFixed(1)}%`
}

export function getRiskLevel(asPlaintiff = 0, asDefendant = 0): "low" | "medium" | "high" {
  if (asDefendant === 0) return "low"

  const ratio = asPlaintiff / asDefendant

  if (ratio > 5) return "low"
  if (ratio > 2) return "medium"
  return "high"
}

export function getRiskColor(level: "low" | "medium" | "high"): string {
  switch (level) {
    case "low":
      return "text-green-600 bg-green-50"
    case "medium":
      return "text-yellow-600 bg-yellow-50"
    case "high":
      return "text-red-600 bg-red-50"
  }
}

export function getRiskEmoji(level: "low" | "medium" | "high"): string {
  switch (level) {
    case "low":
      return "🟢"
    case "medium":
      return "🟡"
    case "high":
      return "🔴"
  }
}
