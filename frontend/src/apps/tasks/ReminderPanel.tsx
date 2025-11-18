import { useCallback, useEffect, useState } from 'react'
import { reminderApi } from '../../api'
import Modal from '../../components/Modal'
import { useModal } from '../../hooks/useModal'
import { formatUTC8DateTime } from '../../utils/timezone'
import type { ReminderLog, DailySummary } from '../../types'
import './ReminderPanel.css'

interface ReminderPanelProps {
  reminders: ReminderLog[]
  onUpdate: () => void
}

function ReminderPanel({ reminders, onUpdate }: ReminderPanelProps) {
  const [dailySummary, setDailySummary] = useState<DailySummary | null>(null)
  const [showSummary, setShowSummary] = useState(false)
  const modal = useModal()

  const loadDailySummary = useCallback(async () => {
    try {
      const data = await reminderApi.getDailySummary()
      setDailySummary(data)
    } catch (error) {
      console.error('加载每日汇总失败:', error)
    }
  }, [])

  useEffect(() => {
    loadDailySummary()
  }, [loadDailySummary])

  const handleMarkAsRead = async (id: number) => {
    try {
      await reminderApi.markAsRead(id)
      onUpdate()
    } catch (error) {
      console.error('标记已读失败:', error)
      modal.showAlert('标记已读失败', 'error')
    }
  }

  const formatDateTime = (dateString: string) => {
    return formatUTC8DateTime(dateString)
  }

  return (
    <div className="reminder-panel">
      <h2>提醒中心</h2>

      <div className="panel-section">
        <div className="section-header">
          <h3>每日汇总</h3>
          <button
            className="btn-toggle"
            onClick={() => setShowSummary(!showSummary)}
          >
            {showSummary ? '收起' : '展开'}
          </button>
        </div>
        {showSummary && dailySummary && (
          <div className="daily-summary">
            <p className="summary-date">日期: {dailySummary.date}</p>
            <p className="summary-count">
              共 {dailySummary.total_count} 项任务
            </p>
            <div className="summary-tasks">
              {dailySummary.tasks.map((task) => (
                <div key={task.id} className="summary-task">
                  <span className={`priority priority-${task.priority}`}>P{task.priority}</span>
                  <span className="title">{task.title}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      <div className="panel-section">
        <h3>未读提醒 ({reminders.length})</h3>
        {reminders.length === 0 ? (
          <p className="empty-reminders">暂无未读提醒</p>
        ) : (
          <div className="reminder-list">
            {reminders.map((reminder) => (
              <div
                key={reminder.id}
                className={`reminder-item ${reminder.reminder_type}`}
              >
                <div className="reminder-header">
                  <span className="reminder-type">
                    {reminder.reminder_type === 'interval'
                      ? '间隔提醒'
                      : '每日汇总'}
                  </span>
                  <span className="reminder-time">
                    {formatDateTime(reminder.reminder_time)}
                  </span>
                </div>
                {reminder.content && (
                  <p className="reminder-content">{reminder.content}</p>
                )}
                <button
                  className="btn btn-secondary btn-small"
                  onClick={() => handleMarkAsRead(reminder.id)}
                >
                  标记已读
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
      <Modal
        isOpen={modal.isOpen}
        onClose={modal.hide}
        title={modal.title}
        message={modal.message}
        type={modal.options.type}
        showCancel={modal.options.showCancel}
        onConfirm={modal.options.onConfirm}
        confirmText={modal.options.confirmText}
        cancelText={modal.options.cancelText}
      />
    </div>
  )
}

export default ReminderPanel

