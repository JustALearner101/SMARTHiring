/**
 * Calendar Timezone & Dynamic Date Helpers
 * Supports WIB (UTC+7), WITA (UTC+8), WIT (UTC+9)
 */

export type IndonesianTimezone = "WIB" | "WITA" | "WIT";

export const TIMEZONE_OFFSETS: Record<IndonesianTimezone, number> = {
  WIB: 7,
  WITA: 8,
  WIT: 9,
};

const MONTH_NAMES_ID = [
  "Jan",
  "Feb",
  "Mar",
  "Apr",
  "May",
  "Jun",
  "Jul",
  "Aug",
  "Sep",
  "Okt",
  "Nov",
  "Des",
];

const DAY_LABELS_ID = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"];

export interface TimezoneParsedResult {
  dateStr: string; // YYYY-MM-DD
  hour: number; // 0 - 23
  minute: number; // 0 - 59
  timeStr: string; // HH:mm
  displayDateTime: string; // YYYY-MM-DD HH:mm
}

/**
 * Parses a UTC ISO string into the specified Indonesian timezone.
 * Returns deterministic date/time representation regardless of client OS locale.
 */
export function parseUtcToTimezone(
  utcIsoString: string,
  tz: IndonesianTimezone
): TimezoneParsedResult {
  if (!utcIsoString) {
    return {
      dateStr: "",
      hour: 0,
      minute: 0,
      timeStr: "00:00",
      displayDateTime: "",
    };
  }

  let s = utcIsoString.trim();
  if (!s.endsWith("Z") && !/[+-]\d{2}:?\d{2}$/.test(s)) {
    s += "Z";
  }

  const date = new Date(s);
  const offsetHours = TIMEZONE_OFFSETS[tz] ?? 7;
  const targetMs = date.getTime() + offsetHours * 3600000;
  const target = new Date(targetMs);

  const year = target.getUTCFullYear();
  const month = String(target.getUTCMonth() + 1).padStart(2, "0");
  const day = String(target.getUTCDate()).padStart(2, "0");
  const hour = target.getUTCHours();
  const minute = target.getUTCMinutes();

  const dateStr = `${year}-${month}-${day}`;
  const timeStr = `${String(hour).padStart(2, "0")}:${String(minute).padStart(2, "0")}`;
  const displayDateTime = `${dateStr} ${timeStr}`;

  return { dateStr, hour, minute, timeStr, displayDateTime };
}

export interface WeekDayInfo {
  label: string;
  dateStr: string; // YYYY-MM-DD
  dayNum: string; // e.g. "26 Okt"
  isFriday: boolean;
  isToday: boolean;
  rawDate: Date;
}

/**
 * Returns midnight Date for Monday of the week containing referenceDate.
 */
export function getMondayOfDate(referenceDate: Date): Date {
  const d = new Date(referenceDate);
  const day = d.getDay();
  const diff = (day === 0 ? -6 : 1) - day;
  d.setDate(d.getDate() + diff);
  d.setHours(0, 0, 0, 0);
  return d;
}

/**
 * Generates 5 work days (Mon - Fri) for the given Monday.
 */
export function getWeekDays(monday: Date): WeekDayInfo[] {
  const today = new Date();
  const todayStr = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, "0")}-${String(today.getDate()).padStart(2, "0")}`;

  const days: WeekDayInfo[] = [];
  for (let i = 0; i < 5; i++) {
    const d = new Date(monday);
    d.setDate(monday.getDate() + i);

    const year = d.getFullYear();
    const month = String(d.getMonth() + 1).padStart(2, "0");
    const day = String(d.getDate()).padStart(2, "0");
    const dateStr = `${year}-${month}-${day}`;
    const dayNum = `${d.getDate()} ${MONTH_NAMES_ID[d.getMonth()]}`;

    days.push({
      label: DAY_LABELS_ID[i],
      dateStr,
      dayNum,
      isFriday: i === 4,
      isToday: dateStr === todayStr,
      rawDate: d,
    });
  }
  return days;
}

/**
 * Formats a Monday date into a friendly week range string, e.g. "26 Okt – 30 Okt 2026"
 */
export function formatWeekRangeLabel(monday: Date): string {
  const friday = new Date(monday);
  friday.setDate(monday.getDate() + 4);

  const startDay = monday.getDate();
  const startMonth = MONTH_NAMES_ID[monday.getMonth()];
  const startYear = monday.getFullYear();

  const endDay = friday.getDate();
  const endMonth = MONTH_NAMES_ID[friday.getMonth()];
  const endYear = friday.getFullYear();

  if (startYear !== endYear) {
    return `${startDay} ${startMonth} ${startYear} – ${endDay} ${endMonth} ${endYear}`;
  }
  if (startMonth !== endMonth) {
    return `${startDay} ${startMonth} – ${endDay} ${endMonth} ${endYear}`;
  }
  return `${startDay} – ${endDay} ${endMonth} ${endYear}`;
}

/**
 * Adds or subtracts weeks from a given date.
 */
export function addWeeks(date: Date, count: number): Date {
  const result = new Date(date);
  result.setDate(result.getDate() + count * 7);
  return result;
}

