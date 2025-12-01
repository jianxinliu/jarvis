import { useState, useEffect } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { todoApi } from '../../api'
import type { TodoItem, TodoItemCreate, TodoTag, TodoPriority, TodoQuadrant, TodoSubTaskCreate } from '../../types'
import { formatUTC8DateTime } from '../../utils/timezone'
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
  const [subtasksModalItem, setSubtasksModalItem] = useState<TodoItem | null>(null)
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
      // 重新从 API 获取完整数据（包括子任务）
      todoApi.getItem(initialItem.id)
        .then((fullItem) => {
          setEditingItem(fullItem)
          const itemSubtasks = (fullItem.subtasks || []).map((st) => ({
            title: st.title,
            content: st.content || '',
            reminder_time: st.reminder_time ? new Date(st.reminder_time).toISOString().slice(0, 16) : '',
          }))
          setSubtasks(itemSubtasks)
          setFormData({
            title: fullItem.title,
            content: fullItem.content || '',
            quadrant: fullItem.quadrant,
            priority_id: fullItem.priority_id || undefined,
            due_time: fullItem.due_time ? new Date(fullItem.due_time).toISOString().slice(0, 16) : undefined,
            reminder_time: fullItem.reminder_time ? new Date(fullItem.reminder_time).toISOString().slice(0, 16) : undefined,
            reminder_interval_hours: fullItem.reminder_interval_hours || undefined,
            tag_ids: (fullItem.tags || []).map((t) => t.id),
            subtasks: itemSubtasks,
          })
          setShowPreview(false)
        })
        .catch((error: any) => {
          console.error('获取事件详情失败:', error)
          // 如果 API 失败（404 或其他错误），使用现有数据作为降级方案
          if (error.response?.status === 404) {
            console.warn('事件不存在，使用现有数据作为降级方案')
          } else {
            console.warn('API 调用失败，使用现有数据作为降级方案')
          }
          if (initialItem) {
            setEditingItem(initialItem)
            const itemSubtasks = (initialItem.subtasks || []).map((st) => ({
              title: st.title,
              content: st.content || '',
              reminder_time: st.reminder_time ? new Date(st.reminder_time).toISOString().slice(0, 16) : '',
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
        })
    }
  }, [initialItem])

  const handleShowSubtasks = async (item: TodoItem) => {
    // 获取完整的子任务数据
    try {
      const fullItem = await todoApi.getItem(item.id)
      setSubtasksModalItem(fullItem)
    } catch (error: any) {
      console.error('获取子任务失败:', error)
      // 如果 API 失败（404 或其他错误），使用现有数据作为降级方案
      if (error.response?.status === 404) {
        console.warn('事件不存在，使用现有数据作为降级方案')
      } else {
        console.warn('API 调用失败，使用现有数据作为降级方案')
      }
      setSubtasksModalItem(item)
    }
  }

  const handleEdit = async (item: TodoItem) => {
    // 事件列表中的编辑：重新从 API 获取完整数据（包括子任务）
    try {
      const fullItem = await todoApi.getItem(item.id)
      setEditingItem(fullItem)
      setShowPreview(false)
      const itemSubtasks = (fullItem.subtasks || []).map((st) => ({
        title: st.title,
        content: st.content || '',
        reminder_time: st.reminder_time ? new Date(st.reminder_time).toISOString().slice(0, 16) : '',
      }))
      setSubtasks(itemSubtasks)
      setFormData({
        title: fullItem.title,
        content: fullItem.content || '',
        quadrant: fullItem.quadrant,
        priority_id: fullItem.priority_id || undefined,
        due_time: fullItem.due_time ? new Date(fullItem.due_time).toISOString().slice(0, 16) : undefined,
        reminder_time: fullItem.reminder_time ? new Date(fullItem.reminder_time).toISOString().slice(0, 16) : undefined,
        reminder_interval_hours: fullItem.reminder_interval_hours || undefined,
        tag_ids: (fullItem.tags || []).map((t) => t.id),
        subtasks: itemSubtasks,
      })
    } catch (error: any) {
      console.error('获取事件详情失败:', error)
      // 如果 API 失败（404 或其他错误），使用现有数据作为降级方案
      if (error.response?.status === 404) {
        console.warn('事件不存在，使用现有数据作为降级方案')
      } else {
        console.warn('API 调用失败，使用现有数据作为降级方案')
      }
      setEditingItem(item)
      setShowPreview(false)
      const itemSubtasks = (item.subtasks || []).map((st) => ({
        title: st.title,
        content: st.content || '',
        reminder_time: st.reminder_time ? new Date(st.reminder_time).toISOString().slice(0, 16) : '',
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
        subtasks: subtasks
          .filter((st) => st.title.trim()) // 过滤掉空标题的子任务
          .map((st) => ({
            title: st.title,
            content: st.content || undefined,
            reminder_time: st.reminder_time ? new Date(st.reminder_time).toISOString() : undefined,
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
                  setSubtasks([...subtasks, { title: '', content: '', reminder_time: '' }])
                }}
              >
                添加子任务
              </button>
            </div>
            {subtasks.length === 0 ? (
              <div style={{ color: '#999', fontSize: '13px', padding: '8px' }}>暂无子任务</div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                {subtasks.map((subtask, index) => (
                  <div key={index} style={{ border: '1px solid #e0e0e0', borderRadius: '6px', padding: '10px', background: '#fafafa' }}>
                    <div style={{ display: 'flex', gap: '8px', alignItems: 'center', marginBottom: '8px' }}>
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
                        value={subtask.reminder_time || ''}
                        onChange={(e) => {
                          const newSubtasks = [...subtasks]
                          newSubtasks[index].reminder_time = e.target.value
                          setSubtasks(newSubtasks)
                        }}
                        placeholder="提醒时间（可选）"
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
                    <textarea
                      placeholder="子任务内容（支持 Markdown）"
                      value={subtask.content || ''}
                      onChange={(e) => {
                        const newSubtasks = [...subtasks]
                        newSubtasks[index].content = e.target.value
                        setSubtasks(newSubtasks)
                      }}
                      rows={3}
                      style={{ width: '100%', padding: '6px 10px', border: '1px solid #ddd', borderRadius: '4px', fontSize: '13px', fontFamily: 'inherit' }}
                    />
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
                {item.subtasks && item.subtasks.length > 0 && (
                  <span
                    className="tag-badge"
                    style={{ backgroundColor: '#e3f2fd', color: '#1976d2', cursor: 'pointer' }}
                    onClick={() => handleShowSubtasks(item)}
                    title="点击查看子任务"
                  >
                    子任务: {item.subtasks.length}
                  </span>
                )}
              </div>
              {item.content && (
                <div className="item-content">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>{item.content}</ReactMarkdown>
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

      {subtasksModalItem && (
        <div className="edit-modal-overlay" onClick={() => setSubtasksModalItem(null)}>
          <div className="edit-modal" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '600px' }}>
            <h3>子任务列表 - {subtasksModalItem.title}</h3>
            <div style={{ maxHeight: '400px', overflowY: 'auto' }}>
              {subtasksModalItem.subtasks && subtasksModalItem.subtasks.length > 0 ? (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  {subtasksModalItem.subtasks.map((subtask) => (
                    <div
                      key={subtask.id}
                      style={{
                        padding: '10px',
                        border: '1px solid #e0e0e0',
                        borderRadius: '6px',
                        background: subtask.is_completed ? '#f5f5f5' : '#fafafa',
                      }}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: subtask.content ? '6px' : '0' }}>
                        <input type="checkbox" checked={subtask.is_completed} disabled />
                        <span style={{ textDecoration: subtask.is_completed ? 'line-through' : 'none', fontWeight: 500, flex: 1 }}>
                          {subtask.title}
                        </span>
                        {subtask.reminder_time && (
                          <span style={{ color: '#999', fontSize: '12px' }}>
                            {formatUTC8DateTime(subtask.reminder_time)}
                          </span>
                        )}
                      </div>
                      {subtask.content && (
                        <div style={{ marginLeft: '28px', color: '#666', fontSize: '12px', lineHeight: '1.4' }}>
                          <ReactMarkdown remarkPlugins={[remarkGfm]}>{subtask.content}</ReactMarkdown>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                <div style={{ textAlign: 'center', color: '#999', padding: '20px' }}>暂无子任务</div>
              )}
            </div>
            <div className="form-actions" style={{ marginTop: '16px' }}>
              <button className="btn btn-secondary" onClick={() => setSubtasksModalItem(null)}>
                关闭
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default TodoEditor

