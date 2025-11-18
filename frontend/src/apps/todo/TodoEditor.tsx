import { useState, useEffect } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { todoApi } from '../../api'
import type { TodoItem, TodoItemCreate, TodoTag, TodoPriority, TodoQuadrant } from '../../types'
import TagMultiSelect from './TagMultiSelect'
import './TodoEditor.css'

interface TodoEditorProps {
  items: TodoItem[]
  tags: TodoTag[]
  priorities: TodoPriority[]
  onItemChange: () => void
}

function TodoEditor({ items, tags, priorities, onItemChange }: TodoEditorProps) {
  const [editingItem, setEditingItem] = useState<TodoItem | null>(null)
  const [localTags, setLocalTags] = useState<TodoTag[]>(tags)
  const [formData, setFormData] = useState<TodoItemCreate>({
    title: '',
    content: '',
    quadrant: 'record',
    priority_id: undefined,
    due_time: undefined,
    reminder_time: undefined,
    tag_ids: [],
  })
  const [saving, setSaving] = useState(false)
  const [showPreview, setShowPreview] = useState(false)

  // 当外部 tags 更新时，同步到本地
  useEffect(() => {
    setLocalTags(tags)
  }, [tags])

  const handleEdit = (item: TodoItem) => {
    setEditingItem(item)
    setShowPreview(false)
    setFormData({
      title: item.title,
      content: item.content || '',
      quadrant: item.quadrant,
      priority_id: item.priority_id || undefined,
      due_time: item.due_time ? new Date(item.due_time).toISOString().slice(0, 16) : undefined,
      reminder_time: item.reminder_time ? new Date(item.reminder_time).toISOString().slice(0, 16) : undefined,
      tag_ids: item.tags.map((t) => t.id),
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
      }

      if (editingItem) {
        await todoApi.update(editingItem.id, submitData)
      } else {
        await todoApi.create(submitData)
      }
      setEditingItem(null)
      setShowPreview(false)
      setFormData({
        title: '',
        content: '',
        quadrant: 'record',
        priority_id: undefined,
        due_time: undefined,
        reminder_time: undefined,
        tag_ids: [],
      })
      onItemChange()
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
        <h2>{editingItem ? '编辑事件' : '新建事件'}</h2>
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
            {editingItem && (
              <button type="button" className="btn btn-secondary" onClick={() => setEditingItem(null)}>
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
        <h2>事件列表</h2>
        <div className="todo-items-list">
          {items.map((item) => (
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
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

export default TodoEditor

