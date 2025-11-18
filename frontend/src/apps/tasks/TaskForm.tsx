import { useEffect, useState } from 'react'
import { taskApi } from '../../api'
import Modal from '../../components/Modal'
import { useModal } from '../../hooks/useModal'
import type { Task, TaskCreate, SubTaskCreate } from '../../types'
import './TaskForm.css'

interface TaskFormProps {
  task?: Task | null
  onSave: () => void
  onCancel: () => void
}

function TaskForm({ task, onSave, onCancel }: TaskFormProps) {
  const [formData, setFormData] = useState<TaskCreate>({
    title: '',
    content: '',
    priority: 1,
    reminder_interval_hours: undefined,
    end_time: undefined,
    subtasks: [],
  })
  const [saving, setSaving] = useState(false)
  const modal = useModal()

  useEffect(() => {
    if (task) {
      setFormData({
        title: task.title,
        content: task.content || '',
        priority: task.priority,
        reminder_interval_hours: task.reminder_interval_hours,
        end_time: task.end_time
          ? new Date(task.end_time).toISOString().slice(0, 16)
          : undefined,
        subtasks: task.subtasks?.map((st) => ({
          title: st.title,
          reminder_time: new Date(st.reminder_time).toISOString().slice(0, 16),
        })) || [],
      })
    }
  }, [task])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!formData.title.trim()) {
      modal.showAlert('请输入任务标题', 'warning')
      return
    }

    setSaving(true)
    try {
      const submitData: TaskCreate = {
        ...formData,
        end_time: formData.end_time
          ? new Date(formData.end_time).toISOString()
          : undefined,
        subtasks: formData.subtasks?.map((st) => ({
          title: st.title,
          reminder_time: new Date(st.reminder_time).toISOString(),
        })),
      }

      if (task) {
        await taskApi.update(task.id, submitData)
      } else {
        await taskApi.create(submitData)
      }
      onSave()
    } catch (error) {
      console.error('保存任务失败:', error)
      modal.showAlert('保存任务失败', 'error')
    } finally {
      setSaving(false)
    }
  }

  const addSubtask = () => {
    const newSubtask: SubTaskCreate = {
      title: '',
      reminder_time: new Date().toISOString().slice(0, 16),
    }
    setFormData({
      ...formData,
      subtasks: [...(formData.subtasks || []), newSubtask],
    })
  }

  const removeSubtask = (index: number) => {
    const newSubtasks = [...(formData.subtasks || [])]
    newSubtasks.splice(index, 1)
    setFormData({ ...formData, subtasks: newSubtasks })
  }

  const updateSubtask = (index: number, field: 'title' | 'reminder_time', value: string) => {
    const newSubtasks = [...(formData.subtasks || [])]
    newSubtasks[index] = { ...newSubtasks[index], [field]: value }
    setFormData({ ...formData, subtasks: newSubtasks })
  }

  return (
    <div className="task-form-overlay">
      <div className="task-form">
        <h2>{task ? '编辑任务' : '新建任务'}</h2>
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="title">任务标题 *</label>
            <input
              id="title"
              type="text"
              value={formData.title}
              onChange={(e) =>
                setFormData({ ...formData, title: e.target.value })
              }
              required
              placeholder="请输入任务标题"
            />
          </div>

          <div className="form-group">
            <label htmlFor="content">任务内容/提醒内容</label>
            <textarea
              id="content"
              value={formData.content}
              onChange={(e) =>
                setFormData({ ...formData, content: e.target.value })
              }
              rows={4}
              placeholder="请输入任务内容或提醒内容"
            />
          </div>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="priority">优先级</label>
              <select
                id="priority"
                value={formData.priority}
                onChange={(e) =>
                  setFormData({ ...formData, priority: parseInt(e.target.value) })
                }
              >
                <option value={1}>1 - 最高</option>
                <option value={2}>2 - 高</option>
                <option value={3}>3 - 中</option>
                <option value={4}>4 - 低</option>
                <option value={5}>5 - 最低</option>
              </select>
            </div>

            <div className="form-group">
              <label htmlFor="reminder_interval">提醒间隔（小时）</label>
              <input
                id="reminder_interval"
                type="number"
                min="1"
                value={formData.reminder_interval_hours || ''}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    reminder_interval_hours: e.target.value
                      ? parseInt(e.target.value)
                      : undefined,
                  })
                }
                placeholder="不设置"
              />
            </div>
          </div>

          <div className="form-group">
            <label htmlFor="end_time">结束时间</label>
            <input
              id="end_time"
              type="datetime-local"
              value={formData.end_time || ''}
              onChange={(e) =>
                setFormData({ ...formData, end_time: e.target.value })
              }
            />
          </div>

          <div className="form-group">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
              <label>子任务（定时提醒）</label>
              <button
                type="button"
                className="btn btn-secondary btn-small"
                onClick={addSubtask}
              >
                + 添加子任务
              </button>
            </div>
            {formData.subtasks && formData.subtasks.length > 0 && (
              <div className="subtasks-list">
                {formData.subtasks.map((subtask, index) => (
                  <div key={index} className="subtask-item" style={{ display: 'flex', gap: '10px', marginBottom: '10px', alignItems: 'flex-start' }}>
                    <div style={{ flex: 1 }}>
                      <input
                        type="text"
                        placeholder="子任务标题"
                        value={subtask.title}
                        onChange={(e) => updateSubtask(index, 'title', e.target.value)}
                        style={{ width: '100%', marginBottom: '5px' }}
                      />
                      <input
                        type="datetime-local"
                        value={subtask.reminder_time}
                        onChange={(e) => updateSubtask(index, 'reminder_time', e.target.value)}
                        style={{ width: '100%' }}
                      />
                    </div>
                    <button
                      type="button"
                      className="btn btn-danger btn-small"
                      onClick={() => removeSubtask(index)}
                    >
                      删除
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="form-actions">
            <button type="button" className="btn btn-secondary" onClick={onCancel}>
              取消
            </button>
            <button type="submit" className="btn btn-primary" disabled={saving}>
              {saving ? '保存中...' : '保存'}
            </button>
          </div>
        </form>
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

export default TaskForm

