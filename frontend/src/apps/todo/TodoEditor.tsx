import { useState, useEffect } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { todoApi } from '../../api'
import type { TodoItem, TodoItemCreate, TodoTag, TodoPriority, TodoQuadrant, TodoSubTaskCreate } from '../../types'
import TagMultiSelect from './TagMultiSelect'
import './TodoEditor.css'

interface TodoEditorProps {
  items: TodoItem[]
  tags: TodoTag[]
  priorities: TodoPriority[]
  onItemChange: () => void
  initialItem?: TodoItem | null
}

function TodoEditor({ items, tags, priorities, onItemChange, initialItem }: TodoEditorProps) {
  const [editingItem, setEditingItem] = useState<TodoItem | null>(null)
  const [localTags, setLocalTags] = useState<TodoTag[]>(tags)
  const [showCompleted, setShowCompleted] = useState(false)
  const [formData, setFormData] = useState<TodoItemCreate>({
    title: '',
    content: '',
    quadrant: 'record',
    priority_id: undefined,
    due_time: undefined,
    reminder_time: undefined,
    reminder_interval_hours: undefined,
    tag_ids: [],
    subtasks: [],
  })
  const [subtasks, setSubtasks] = useState<TodoSubTaskCreate[]>([])
  const [saving, setSaving] = useState(false)
  const [showPreview, setShowPreview] = useState(false)

  // 当外部 tags 更新时，同步到本地
  useEffect(() => {
    setLocalTags(tags)
  }, [tags])

  // 当 initialItem 变化时，更新编辑状态（仅用于从四象限跳转过来的情况）
  useEffect(() => {
    if (initialItem) {
      setEditingItem(initialItem)
      const itemSubtasks = (initialItem.subtasks || []).map((st) => ({
        title: st.title,
        reminder_time: new Date(st.reminder_time).toISOString().slice(0, 16),
      }))
      setSubtasks(itemSubtasks)
      setFormData({
        title: initialItem.title,
        content: initialItem.content || '',
        quadrant: initialItem.quadrant,
        priority_id: initialItem.priority_id || undefined,
        due_time: initialItem.due_time ? new Date(initialItem.due_time).toISOString().slice(0, 16) : undefined,
        reminder_time: initialItem.reminder_time ? new Date(initialItem.reminder_time).toISOString().slice(0, 16) : undefined,
        reminder_interval_hours: initialItem.reminder_interval_hours || undefined,
        tag_ids: (initialItem.tags || []).map((t) => t.id),
        subtasks: itemSubtasks,
      })
      setShowPreview(false)
    }
  }, [initialItem])

  const handleEdit = (item: TodoItem) => {
    // 事件列表中的编辑：直接在表单中编辑
    setEditingItem(item)
    setShowPreview(false)
    const itemSubtasks = (item.subtasks || []).map((st) => ({
      title: st.title,
      reminder_time: new Date(st.reminder_time).toISOString().slice(0, 16),
    }))
    setSubtasks(itemSubtasks)
    setFormData({
      title: item.title,
      content: item.content || '',
      quadrant: item.quadrant,
      priority_id: item.priority_id || undefined,
      due_time: item.due_time ? new Date(item.due_time).toISOString().slice(0, 16) : undefined,
      reminder_time: item.reminder_time ? new Date(item.reminder_time).toISOString().slice(0, 16) : undefined,
      reminder_interval_hours: item.reminder_interval_hours || undefined,
      tag_ids: (item.tags || []).map((t) => t.id),
      subtasks: itemSubtasks,
    })
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!formData.title.trim()) {
      alert('请输入标题')
      return
    }

    setSaving(true)
    try {
      const submitData: TodoItemCreate = {
        ...formData,
        due_time: formData.due_time ? new Date(formData.due_time).toISOString() : undefined,
        reminder_time: formData.reminder_time ? new Date(formData.reminder_time).toISOString() : undefined,
        subtasks: subtasks.map((st) => ({
          title: st.title,
          reminder_time: new Date(st.reminder_time).toISOString(),
        })),
      }

      const itemToUpdate = editingItem || initialItem
      if (itemToUpdate) {
        await todoApi.update(itemToUpdate.id, submitData)
      } else {
        await todoApi.create(submitData)
      }
      setEditingItem(null)
      setShowPreview(false)
      setSubtasks([])
      setFormData({
        title: '',
        content: '',
        quadrant: 'record',
        priority_id: undefined,
        due_time: undefined,
        reminder_time: undefined,
        reminder_interval_hours: undefined,
        tag_ids: [],
        subtasks: [],
      })
      onItemChange()
      // 清除 initialItem（通过父组件）
      if (initialItem) {
        // 通知父组件清除 initialItem
        window.dispatchEvent(new CustomEvent('todo-editor-reset'))
      }
    } catch (error) {
      console.error('保存失败:', error)
      alert('保存失败')
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async (id: number) => {
    if (!confirm('确定要删除吗？')) return
    try {
      await todoApi.delete(id)
      onItemChange()
    } catch (error) {
      console.error('删除失败:', error)
      alert('删除失败')
    }
  }

  const quadrants: { value: TodoQuadrant; label: string }[] = [
    { value: 'reminder', label: '提醒' },
    { value: 'record', label: '记录' },
    { value: 'urgent', label: '紧急' },
    { value: 'important', label: '重要' },
  ]

  return (
    <div className="todo-editor">
      <div className="editor-form-container">
        <h2>{editingItem || initialItem ? '编辑事件' : '新建事件'}</h2>
        <form onSubmit={handleSubmit} className="todo-form">
          <div className="form-group">
            <label>标题 *</label>
            <input
              type="text"
              value={formData.title}
              onChange={(e) => setFormData({ ...formData, title: e.target.value })}
              required
              placeholder="输入事件标题"
            />
          </div>

          <div className="form-group">
            <label>象限 *</label>
            <select
              value={formData.quadrant}
              onChange={(e) => setFormData({ ...formData, quadrant: e.target.value as TodoQuadrant })}
              required
            >
              {quadrants.map((q) => (
                <option key={q.value} value={q.value}>
                  {q.label}
                </option>
              ))}
            </select>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>优先级</label>
              <select
                value={formData.priority_id || ''}
                onChange={(e) =>
                  setFormData({ ...formData, priority_id: e.target.value ? parseInt(e.target.value) : undefined })
                }
              >
                <option value="">无</option>
                {priorities.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name} (级别 {p.level})
                  </option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label>标签</label>
              <TagMultiSelect
                tags={localTags}
                selectedTagIds={formData.tag_ids || []}
                onChange={(tagIds) => setFormData({ ...formData, tag_ids: tagIds })}
                onTagCreated={(newTag) => {
                  // 将新标签添加到本地标签列表，不刷新整个页面
                  // 这样可以防止正在编辑的内容丢失
                  setLocalTags([...localTags, newTag])
                }}
              />
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>截止时间</label>
              <input
                type="datetime-local"
                value={formData.due_time || ''}
                onChange={(e) => setFormData({ ...formData, due_time: e.target.value })}
              />
            </div>

            <div className="form-group">
              <label>提醒时间</label>
              <input
                type="datetime-local"
                value={formData.reminder_time || ''}
                onChange={(e) => setFormData({ ...formData, reminder_time: e.target.value })}
              />
            </div>
          </div>

          <div className="form-group">
            <label>提醒间隔（小时）</label>
            <input
              type="number"
              min="1"
              value={formData.reminder_interval_hours || ''}
              onChange={(e) =>
                setFormData({
                  ...formData,
                  reminder_interval_hours: e.target.value ? parseInt(e.target.value) : undefined,
                })
              }
              placeholder="设置后会自动按间隔提醒"
            />
          </div>

          <div className="form-group">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
              <label>子任务</label>
              <button
                type="button"
                className="btn btn-secondary btn-small"
                onClick={() => {
                  setSubtasks([...subtasks, { title: '', reminder_time: new Date().toISOString().slice(0, 16) }])
                }}
              >
                添加子任务
              </button>
            </div>
            {subtasks.length === 0 ? (
              <div style={{ color: '#999', fontSize: '13px', padding: '8px' }}>暂无子任务</div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {subtasks.map((subtask, index) => (
                  <div key={index} style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                    <input
                      type="text"
                      placeholder="子任务标题"
                      value={subtask.title}
                      onChange={(e) => {
                        const newSubtasks = [...subtasks]
                        newSubtasks[index].title = e.target.value
                        setSubtasks(newSubtasks)
                      }}
                      style={{ flex: 1, padding: '6px 10px', border: '1px solid #ddd', borderRadius: '4px' }}
                    />
                    <input
                      type="datetime-local"
                      value={subtask.reminder_time}
                      onChange={(e) => {
                        const newSubtasks = [...subtasks]
                        newSubtasks[index].reminder_time = e.target.value
                        setSubtasks(newSubtasks)
                      }}
                      style={{ padding: '6px 10px', border: '1px solid #ddd', borderRadius: '4px' }}
                    />
                    <button
                      type="button"
                      className="btn btn-secondary btn-small"
                      onClick={() => {
                        setSubtasks(subtasks.filter((_, i) => i !== index))
                      }}
                    >
                      删除
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="form-group">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
              <label>内容（Markdown）</label>
              <button
                type="button"
                className="btn btn-secondary btn-small"
                onClick={() => setShowPreview(!showPreview)}
              >
                {showPreview ? '编辑' : '预览'}
              </button>
            </div>
            {showPreview ? (
              <div className="markdown-preview">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>{formData.content || '*暂无内容*'}</ReactMarkdown>
              </div>
            ) : (
              <textarea
                value={formData.content}
                onChange={(e) => setFormData({ ...formData, content: e.target.value })}
                rows={8}
                placeholder="支持 Markdown 格式"
              />
            )}
          </div>

          <div className="form-actions">
            {(editingItem || initialItem) && (
              <button
                type="button"
                className="btn btn-secondary"
                onClick={() => {
                  setEditingItem(null)
                  if (initialItem) {
                    window.dispatchEvent(new CustomEvent('todo-editor-reset'))
                  }
                  setFormData({
                    title: '',
                    content: '',
                    quadrant: 'record',
                    priority_id: undefined,
                    due_time: undefined,
                    reminder_time: undefined,
                    reminder_interval_hours: undefined,
                    tag_ids: [],
                    subtasks: [],
                  })
                  setSubtasks([])
                }}
              >
                取消
              </button>
            )}
            <button type="submit" className="btn btn-primary" disabled={saving}>
              {saving ? '保存中...' : '保存'}
            </button>
          </div>
        </form>
      </div>

      <div className="editor-list-container">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
          <h2>事件列表</h2>
          <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
            <input
              type="checkbox"
              checked={showCompleted}
              onChange={(e) => setShowCompleted(e.target.checked)}
            />
            <span>显示已完成</span>
          </label>
        </div>
        <div className="todo-items-list">
          {items
            .filter((item) => showCompleted || !item.is_completed)
            .map((item) => (
            <div key={item.id} className={`todo-item-card ${item.is_completed ? 'completed' : ''}`}>
              <div className="item-header">
                <h3>{item.title}</h3>
                <div className="item-actions">
                  <button className="btn-icon" onClick={() => handleEdit(item)}>
                    编辑
                  </button>
                  <button className="btn-icon btn-danger" onClick={() => handleDelete(item.id)}>
                    删除
                  </button>
                </div>
              </div>
              <div className="item-meta">
                <span className={`quadrant-badge quadrant-${item.quadrant}`}>
                  {quadrants.find((q) => q.value === item.quadrant)?.label}
                </span>
                {item.priority && (
                  <span className="priority-badge" style={{ color: item.priority.color || '#666' }}>
                    {item.priority.name}
                  </span>
                )}
                {item.tags.map((tag) => (
                  <span key={tag.id} className="tag-badge" style={{ backgroundColor: tag.color || '#e0e0e0' }}>
                    {tag.name}
                  </span>
                ))}
              </div>
              {item.content && (
                <div className="item-content">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>{item.content}</ReactMarkdown>
                </div>
              )}
              {item.subtasks && item.subtasks.length > 0 && (
                <div className="item-subtasks" style={{ marginTop: '8px', paddingTop: '8px', borderTop: '1px solid #eee' }}>
                  <div style={{ fontSize: '12px', fontWeight: 500, marginBottom: '4px', color: '#666' }}>子任务：</div>
                  {item.subtasks.map((subtask) => (
                    <div
                      key={subtask.id}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '8px',
                        fontSize: '12px',
                        color: subtask.is_completed ? '#999' : '#333',
                        textDecoration: subtask.is_completed ? 'line-through' : 'none',
                      }}
                    >
                      <input type="checkbox" checked={subtask.is_completed} disabled />
                      <span>{subtask.title}</span>
                      <span style={{ color: '#999', fontSize: '11px' }}>
                        ({new Date(subtask.reminder_time).toLocaleString('zh-CN')})
                      </span>
                    </div>
                  ))}
                </div>
              )}
              {item.reminder_interval_hours && (
                <div style={{ marginTop: '4px', fontSize: '11px', color: '#666' }}>
                  提醒间隔: {item.reminder_interval_hours} 小时
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

export default TodoEditor

