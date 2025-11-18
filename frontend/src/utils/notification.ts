/**
 * 浏览器通知工具函数
 * 用于在页面打开时显示浏览器通知，尽量通知到宿主系统
 */

interface NotificationOptions {
  title: string
  body?: string
  icon?: string
  badge?: string
  tag?: string
  requireInteraction?: boolean
  silent?: boolean
  onClick?: () => void
}

/**
 * 请求浏览器通知权限
 */
export async function requestNotificationPermission(): Promise<NotificationPermission> {
  if (!('Notification' in window)) {
    console.warn('浏览器不支持通知功能')
    return 'denied'
  }

  if (Notification.permission === 'granted') {
    return 'granted'
  }

  if (Notification.permission === 'denied') {
    console.warn('用户已拒绝通知权限')
    return 'denied'
  }

  // 请求权限
  const permission = await Notification.requestPermission()
  return permission
}

/**
 * 显示浏览器通知
 * @param options 通知选项
 * @returns 通知对象，如果无法显示则返回 null
 */
export async function showNotification(
  options: NotificationOptions
): Promise<Notification | null> {
  // 检查浏览器支持
  if (!('Notification' in window)) {
    console.warn('浏览器不支持通知功能')
    return null
  }

  // 请求权限
  const permission = await requestNotificationPermission()
  if (permission !== 'granted') {
    console.warn('用户未授予通知权限')
    return null
  }

  // 构建通知选项
  // 即使页面可见也显示通知，因为用户可能在其他标签页或窗口
  // 浏览器会自动将通知转发到系统通知中心（如果支持）
  const notificationOptions: NotificationOptions = {
    icon: options.icon || '/icon.svg',
    badge: options.badge || '/icon.svg',
    tag: options.tag || 'jarvis-reminder',
    requireInteraction: options.requireInteraction ?? true, // 默认需要用户交互才关闭，确保通知更持久
    silent: options.silent ?? false,
    ...options,
  }

  try {
    const notification = new Notification(notificationOptions.title, {
      body: notificationOptions.body,
      icon: notificationOptions.icon,
      badge: notificationOptions.badge,
      tag: notificationOptions.tag,
      requireInteraction: notificationOptions.requireInteraction,
      silent: notificationOptions.silent,
    })

    // 设置点击事件
    if (notificationOptions.onClick) {
      notification.onclick = (event) => {
        event.preventDefault()
        // 聚焦到窗口（如果窗口存在）
        if (window) {
          window.focus()
        }
        // 执行自定义点击处理
        notificationOptions.onClick?.()
        // 关闭通知
        notification.close()
      }
    } else {
      // 默认点击行为：聚焦到窗口
      notification.onclick = (event) => {
        event.preventDefault()
        // 聚焦到窗口（如果窗口存在）
        if (window) {
          window.focus()
        }
        notification.close()
      }
    }

    // 设置错误处理
    notification.onerror = (error) => {
      console.error('通知错误:', error)
    }

    // 自动关闭通知（60秒后，给用户更多时间查看）
    // 如果设置了 requireInteraction，通知会一直显示直到用户交互
    setTimeout(() => {
      if (notification) {
        notification.close()
      }
    }, 60000)

    return notification
  } catch (error) {
    console.error('显示通知失败:', error)
    return null
  }
}

/**
 * 显示任务提醒通知
 * @param reminderData 提醒数据
 */
export async function showReminderNotification(reminderData: {
  id: number
  task_id?: number
  subtask_id?: number
  type: string
  content?: string
  time?: string
}): Promise<Notification | null> {
  let reminderType = '提醒'
  if (reminderData.type === 'interval') {
    reminderType = '间隔提醒'
  } else if (reminderData.type === 'daily') {
    reminderType = '每日汇总'
  } else if (reminderData.type === 'subtask') {
    reminderType = '子任务提醒'
  } else if (reminderData.type === 'todo') {
    reminderType = 'TODO 提醒'
  }
  
  const title = `Jarvis ${reminderType}`
  const body = reminderData.content || '您有新的提醒'

  return showNotification({
    title,
    body,
    tag: `reminder-${reminderData.id}`, // 使用唯一 tag，避免重复通知
    requireInteraction: true, // 需要用户交互，确保通知更持久
  })
}

