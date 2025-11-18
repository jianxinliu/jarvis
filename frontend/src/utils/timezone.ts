/**
 * 时区工具函数 - 统一使用 UTC+8 时区
 */

/**
 * UTC+8 时区偏移（毫秒）
 */
const UTC_PLUS_8_OFFSET = 8 * 60 * 60 * 1000

/**
 * 将 UTC 时间字符串转换为 UTC+8 时区的 Date 对象
 * @param utcString UTC 时间字符串（ISO 格式）
 * @returns UTC+8 时区的 Date 对象
 */
export function parseUTC8(utcString: string): Date {
  const date = new Date(utcString)
  // 如果字符串没有时区信息，假设是 UTC+8 时区
  if (!utcString.includes('Z') && !utcString.includes('+') && !utcString.includes('-', 10)) {
    // 没有时区信息，直接返回（假设已经是 UTC+8）
    return date
  }
  // 有时区信息，转换为 UTC+8
  return new Date(date.getTime() + UTC_PLUS_8_OFFSET - date.getTimezoneOffset() * 60 * 1000)
}

/**
 * 格式化日期时间为 UTC+8 时区的字符串
 * @param date 日期对象或日期字符串
 * @param options 格式化选项
 * @returns 格式化后的字符串
 */
export function formatUTC8(
  date: Date | string,
  options: Intl.DateTimeFormatOptions = {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    timeZone: 'Asia/Shanghai', // UTC+8
  }
): string {
  const dateObj = typeof date === 'string' ? new Date(date) : date
  return dateObj.toLocaleString('zh-CN', {
    ...options,
    timeZone: 'Asia/Shanghai', // UTC+8
  })
}

/**
 * 格式化日期为 UTC+8 时区的字符串（仅日期）
 * @param date 日期对象或日期字符串
 * @returns 格式化后的日期字符串
 */
export function formatUTC8Date(date: Date | string): string {
  return formatUTC8(date, {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    timeZone: 'Asia/Shanghai',
  })
}

/**
 * 格式化时间为 UTC+8 时区的字符串（仅时间）
 * @param date 日期对象或日期字符串
 * @returns 格式化后的时间字符串
 */
export function formatUTC8Time(date: Date | string): string {
  return formatUTC8(date, {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    timeZone: 'Asia/Shanghai',
  })
}

/**
 * 格式化日期时间为 UTC+8 时区的完整字符串（日期 + 时间）
 * @param date 日期对象或日期字符串
 * @returns 格式化后的完整字符串
 */
export function formatUTC8DateTime(date: Date | string): string {
  return formatUTC8(date, {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    timeZone: 'Asia/Shanghai',
  })
}

/**
 * 获取当前 UTC+8 时区的时间
 * @returns 当前 UTC+8 时区的 Date 对象
 */
export function nowUTC8(): Date {
  const now = new Date()
  // 转换为 UTC+8 时区
  const utc8Time = new Date(now.getTime() + UTC_PLUS_8_OFFSET - now.getTimezoneOffset() * 60 * 1000)
  return utc8Time
}

