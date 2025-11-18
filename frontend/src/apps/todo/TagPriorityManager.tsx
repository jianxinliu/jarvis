import { useState } from 'react'
import { todoApi } from '../../api'
import type { TodoTag, TodoTagCreate, TodoPriority, TodoPriorityCreate } from '../../types'
import './TagPriorityManager.css'

interface TagPriorityManagerProps {
  tags: TodoTag[]
  priorities: TodoPriority[]
  onDataChange: () => void
}

function TagPriorityManager({ tags, priorities, onDataChange }: TagPriorityManagerProps) {
  const [activeTab, setActiveTab] = useState<'tags' | 'priorities'>('tags')
  const [editingTag, setEditingTag] = useState<TodoTag | null>(null)
  const [editingPriority, setEditingPriority] = useState<TodoPriority | null>(null)
  const [tagForm, setTagForm] = useState<TodoTagCreate>({ name: '', color: '#e0e0e0' })
  const [priorityForm, setPriorityForm] = useState<TodoPriorityCreate>({ name: '', level: 1, color: '#666' })

  const handleTagSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      if (editingTag) {
        await todoApi.updateTag(editingTag.id, tagForm)
      } else {
        await todoApi.createTag(tagForm)
      }
      setTagForm({ name: '', color: '#e0e0e0' })
      setEditingTag(null)
      onDataChange()
    } catch (error) {
      console.error('保存标签失败:', error)
      alert('保存失败')
    }
  }

  const handlePrioritySubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      if (editingPriority) {
        await todoApi.updatePriority(editingPriority.id, priorityForm)
      } else {
        await todoApi.createPriority(priorityForm)
      }
      setPriorityForm({ name: '', level: 1, color: '#666' })
      setEditingPriority(null)
      onDataChange()
    } catch (error) {
      console.error('保存优先级失败:', error)
      alert('保存失败')
    }
  }

  const handleDeleteTag = async (id: number) => {
    if (!confirm('确定要删除这个标签吗？')) return
    try {
      await todoApi.deleteTag(id)
      onDataChange()
    } catch (error) {
      console.error('删除失败:', error)
    }
  }

  const handleDeletePriority = async (id: number) => {
    if (!confirm('确定要删除这个优先级吗？')) return
    try {
      await todoApi.deletePriority(id)
      onDataChange()
    } catch (error) {
      console.error('删除失败:', error)
    }
  }

  return (
    <div className="tag-priority-manager">
      <div className="manager-tabs">
        <button
          className={`manager-tab ${activeTab === 'tags' ? 'active' : ''}`}
          onClick={() => setActiveTab('tags')}
        >
          标签管理
        </button>
        <button
          className={`manager-tab ${activeTab === 'priorities' ? 'active' : ''}`}
          onClick={() => setActiveTab('priorities')}
        >
          优先级管理
        </button>
      </div>

      <div className="manager-content">
        {activeTab === 'tags' && (
          <div className="manager-section">
            <h2>标签管理</h2>
            <form onSubmit={handleTagSubmit} className="manager-form">
              <div className="form-group">
                <label>标签名称 *</label>
                <input
                  type="text"
                  value={tagForm.name}
                  onChange={(e) => setTagForm({ ...tagForm, name: e.target.value })}
                  required
                  placeholder="输入标签名称"
                />
              </div>
              <div className="form-group">
                <label>颜色</label>
                <div className="color-input-group">
                  <input
                    type="color"
                    value={tagForm.color || '#e0e0e0'}
                    onChange={(e) => setTagForm({ ...tagForm, color: e.target.value })}
                  />
                  <input
                    type="text"
                    value={tagForm.color || '#e0e0e0'}
                    onChange={(e) => setTagForm({ ...tagForm, color: e.target.value })}
                    placeholder="#e0e0e0"
                  />
                </div>
              </div>
              <div className="form-actions">
                {editingTag && (
                  <button type="button" className="btn btn-secondary" onClick={() => setEditingTag(null)}>
                    取消
                  </button>
                )}
                <button type="submit" className="btn btn-primary">
                  {editingTag ? '更新' : '创建'}
                </button>
              </div>
            </form>

            <div className="items-list">
              <h3>现有标签</h3>
              <div className="items-grid">
                {tags.map((tag) => (
                  <div key={tag.id} className="item-card">
                    <div className="item-preview" style={{ backgroundColor: tag.color || '#e0e0e0' }}>
                      {tag.name}
                    </div>
                    <div className="item-actions">
                      <button className="btn-small" onClick={() => {
                        setEditingTag(tag)
                        setTagForm({ name: tag.name, color: tag.color || '#e0e0e0' })
                      }}>
                        编辑
                      </button>
                      <button className="btn-small btn-danger" onClick={() => handleDeleteTag(tag.id)}>
                        删除
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {activeTab === 'priorities' && (
          <div className="manager-section">
            <h2>优先级管理</h2>
            <form onSubmit={handlePrioritySubmit} className="manager-form">
              <div className="form-group">
                <label>优先级名称 *</label>
                <input
                  type="text"
                  value={priorityForm.name}
                  onChange={(e) => setPriorityForm({ ...priorityForm, name: e.target.value })}
                  required
                  placeholder="输入优先级名称"
                />
              </div>
              <div className="form-row">
                <div className="form-group">
                  <label>级别 *</label>
                  <input
                    type="number"
                    min="1"
                    value={priorityForm.level}
                    onChange={(e) => setPriorityForm({ ...priorityForm, level: parseInt(e.target.value) })}
                    required
                  />
                  <small>数字越小优先级越高</small>
                </div>
                <div className="form-group">
                  <label>颜色</label>
                  <div className="color-input-group">
                    <input
                      type="color"
                      value={priorityForm.color || '#666'}
                      onChange={(e) => setPriorityForm({ ...priorityForm, color: e.target.value })}
                    />
                    <input
                      type="text"
                      value={priorityForm.color || '#666'}
                      onChange={(e) => setPriorityForm({ ...priorityForm, color: e.target.value })}
                      placeholder="#666"
                    />
                  </div>
                </div>
              </div>
              <div className="form-actions">
                {editingPriority && (
                  <button type="button" className="btn btn-secondary" onClick={() => setEditingPriority(null)}>
                    取消
                  </button>
                )}
                <button type="submit" className="btn btn-primary">
                  {editingPriority ? '更新' : '创建'}
                </button>
              </div>
            </form>

            <div className="items-list">
              <h3>现有优先级</h3>
              <div className="items-grid">
                {priorities
                  .sort((a, b) => a.level - b.level)
                  .map((priority) => (
                    <div key={priority.id} className="item-card">
                      <div className="item-preview" style={{ color: priority.color || '#666' }}>
                        {priority.name} (级别 {priority.level})
                      </div>
                      <div className="item-actions">
                        <button
                          className="btn-small"
                          onClick={() => {
                            setEditingPriority(priority)
                            setPriorityForm({
                              name: priority.name,
                              level: priority.level,
                              color: priority.color || '#666',
                            })
                          }}
                        >
                          编辑
                        </button>
                        <button className="btn-small btn-danger" onClick={() => handleDeletePriority(priority.id)}>
                          删除
                        </button>
                      </div>
                    </div>
                  ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default TagPriorityManager

