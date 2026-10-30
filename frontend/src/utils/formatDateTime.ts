/**
 * Date and time formatting utilities for Heketon UI.
 * Standardized to Indonesian WIB (Asia/Jakarta) timezone.
 */

export function formatWib(raw?: string | null): string {
  if (!raw) return "-";
  if (raw.includes("—") || raw.includes("Today")) return raw;

  try {
    const d = new Date(raw);
    if (isNaN(d.getTime())) return raw;

    return (
      new Intl.DateTimeFormat("id-ID", {
        day: "numeric",
        month: "short",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
        timeZone: "Asia/Jakarta",
      }).format(d) + " WIB"
    );
  } catch {
    return raw;
  }
}

export function formatWibShort(raw?: string | null): string {
  if (!raw) return "-";
  if (raw.includes("—") || raw.includes("Today")) return raw;

  try {
    const d = new Date(raw);
    if (isNaN(d.getTime())) return raw;

    return (
      new Intl.DateTimeFormat("id-ID", {
        day: "numeric",
        month: "short",
        hour: "2-digit",
        minute: "2-digit",
        timeZone: "Asia/Jakarta",
      }).format(d) + " WIB"
    );
  } catch {
    return raw;
  }
}
