import { useState } from 'react'
import { taskApi } from '../../api'
import Modal from '../../components/Modal'
import { useModal } from '../../hooks/useModal'
import { formatUTC8DateTime } from '../../utils/timezone'
import type { Task } from '../../types'
import './TaskList.css'

interface TaskListProps {
  tasks: Task[]
  onEdit: (task: Task) => void
  onDelete: (id: number) => void
  onUpdate: () => void
}

function TaskList({ tasks, onEdit, onDelete, onUpdate }: TaskListProps) {
  const [completingId, setCompletingId] = useState<number | null>(null)
  const modal = useModal()

  const handleToggleActive = async (task: Task) => {
    try {
      await taskApi.update(task.id, { is_active: !task.is_active })
      onUpdate()
    } catch (error) {
      console.error('更新任务失败:', error)
      modal.showAlert('更新任务失败', 'error')
    }
  }

  const handleComplete = async (id: number) => {
    modal.showConfirm(
      '确定要标记这个任务为完成吗？',
      () => {
        setCompletingId(id)
        taskApi.delete(id)
          .then(() => {
            onDelete(id)
            setCompletingId(null)
          })
          .catch((error) => {
            console.error('标记任务完成失败:', error)
            modal.showAlert('标记任务完成失败', 'error')
            setCompletingId(null)
          })
      },
      '确认完成'
    )
  }


  const formatDateTime = (dateString?: string) => {
    if (!dateString) return '-'
    return formatUTC8DateTime(dateString)
  }

  if (tasks.length === 0) {
    return (
      <div className="empty-state">
        <p>暂无任务，点击"新建任务"开始吧！</p>
      </div>
    )
  }

  return (
    <div className="task-list">
      {tasks.map((task) => (
        <div
          key={task.id}
          className={`task-item ${!task.is_active ? 'inactive' : ''}`}
        >
          <div className="task-header">
            <div className="task-title-row">
              <span
                className={`priority-badge priority-${task.priority}`}
              >
                P{task.priority}
              </span>
              <h3 className="task-title">{task.title}</h3>
              {!task.is_active && <span className="inactive-label">已暂停</span>}
            </div>
          </div>

          {task.content && <p className="task-content">{task.content}</p>}

          {task.subtasks && task.subtasks.length > 0 && (
            <div className="subtasks-section" style={{ marginTop: '10px', marginBottom: '10px' }}>
              <strong style={{ fontSize: '0.9em', color: '#666' }}>子任务：</strong>
              <ul style={{ margin: '5px 0', paddingLeft: '20px' }}>
                {task.subtasks.map((subtask) => (
                  <li key={subtask.id} style={{ marginBottom: '5px' }}>
                    <span style={{ textDecoration: subtask.is_completed ? 'line-through' : 'none', color: subtask.is_completed ? '#999' : 'inherit' }}>
                      {subtask.title}
                    </span>
                    <span style={{ fontSize: '0.85em', color: '#999', marginLeft: '10px' }}>
                      ({formatUTC8DateTime(subtask.reminder_time)})
                    </span>
                    {subtask.is_completed && (
                      <span style={{ fontSize: '0.85em', color: '#4caf50', marginLeft: '10px' }}>✓</span>
                    )}
                  </li>
                ))}
              </ul>
            </div>
          )}

          <div className="task-meta">
            {task.reminder_interval_hours && (
              <span className="meta-item">
                ⏰ 每 {task.reminder_interval_hours} 小时提醒
              </span>
            )}
            {task.end_time && (
              <span className="meta-item">
                截止: {formatDateTime(task.end_time)}
              </span>
            )}
            {task.next_reminder_time && (
              <span className="meta-item">
                下次提醒: {formatDateTime(task.next_reminder_time)}
              </span>
            )}
          </div>

          <div className="task-actions">
            <button
              className="btn btn-secondary"
              onClick={() => handleToggleActive(task)}
            >
              {task.is_active ? '暂停' : '激活'}
            </button>
            <button
              className="btn btn-secondary"
              onClick={() => onEdit(task)}
            >
              编辑
            </button>
            <button
              className="btn btn-success"
              onClick={() => handleComplete(task.id)}
              disabled={completingId === task.id}
            >
              {completingId === task.id ? '完成中...' : '完成'}
            </button>
          </div>
        </div>
      ))}
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

export default TaskList

