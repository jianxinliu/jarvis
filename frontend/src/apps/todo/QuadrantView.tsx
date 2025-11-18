import { useState, useMemo } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { todoApi } from '../../api'
import type { TodoItem, TodoTag, TodoPriority, TodoQuadrant } from '../../types'
import { formatUTC8DateTime } from '../../utils/timezone'
import './QuadrantView.css'

interface QuadrantViewProps {
  items: TodoItem[]
  tags: TodoTag[]
  priorities: TodoPriority[]
  onItemChange: () => void
}

function QuadrantView({ items, tags, priorities, onItemChange }: QuadrantViewProps) {
  const [selectedTag, setSelectedTag] = useState<number | null>(null)
  const [editingItem, setEditingItem] = useState<TodoItem | null>(null)

  const quadrants = [
    { key: 'reminder' as TodoQuadrant, label: '提醒', icon: '⏰', color: '#ff9800' },
    { key: 'record' as TodoQuadrant, label: '记录', icon: '📝', color: '#4caf50' },
    { key: 'urgent' as TodoQuadrant, label: '紧急', icon: '🔥', color: '#f44336' },
    { key: 'important' as TodoQuadrant, label: '重要', icon: '⭐', color: '#2196f3' },
  ]

  const filteredItems = useMemo(() => {
    if (selectedTag === null) return items
    return items.filter((item) => item.tags.some((tag) => tag.id === selectedTag))
  }, [items, selectedTag])

  const itemsByQuadrant = useMemo(() => {
    const result: Record<TodoQuadrant, TodoItem[]> = {
      reminder: [],
      record: [],
      urgent: [],
      important: [],
    }
    filteredItems
      .filter((item) => !item.is_completed && !item.is_archived)
      .forEach((item) => {
        result[item.quadrant].push(item)
      })
    
    // 对记录象限按 tag 分组
    if (result.record.length > 0) {
      result.record.sort((a, b) => {
        const aTagNames = a.tags.map((t) => t.name).join(',')
        const bTagNames = b.tags.map((t) => t.name).join(',')
        return aTagNames.localeCompare(bTagNames)
      })
    }
    
    // 对提醒象限按截止时间排序
    result.reminder.sort((a, b) => {
      if (!a.due_time && !b.due_time) return 0
      if (!a.due_time) return 1
      if (!b.due_time) return -1
      return new Date(a.due_time).getTime() - new Date(b.due_time).getTime()
    })
    
    // 对紧急象限按优先级和截止时间排序
    result.urgent.sort((a, b) => {
      const priorityDiff = (a.priority?.level || 999) - (b.priority?.level || 999)
      if (priorityDiff !== 0) return priorityDiff
      if (!a.due_time && !b.due_time) return 0
      if (!a.due_time) return 1
      if (!b.due_time) return -1
      return new Date(a.due_time).getTime() - new Date(b.due_time).getTime()
    })
    
    return result
  }, [filteredItems])

  const handleToggleComplete = async (item: TodoItem) => {
    try {
      await todoApi.update(item.id, { is_completed: !item.is_completed })
      onItemChange()
    } catch (error) {
      console.error('更新失败:', error)
    }
  }

  const handleEdit = (item: TodoItem) => {
    setEditingItem(item)
  }

  const handleDelete = async (id: number) => {
    if (!confirm('确定要删除吗？')) return
    try {
      await todoApi.delete(id)
      onItemChange()
    } catch (error) {
      console.error('删除失败:', error)
    }
  }

  return (
    <div className="quadrant-view">
      <div className="quadrant-filters">
        <div className="filter-section">
          <label>按标签筛选：</label>
          <div className="tag-filters">
            <button
              className={`tag-filter ${selectedTag === null ? 'active' : ''}`}
              onClick={() => setSelectedTag(null)}
            >
              全部
            </button>
            {tags.map((tag) => (
              <button
                key={tag.id}
                className={`tag-filter ${selectedTag === tag.id ? 'active' : ''}`}
                onClick={() => setSelectedTag(tag.id)}
                style={{ backgroundColor: selectedTag === tag.id ? tag.color || '#e0e0e0' : 'transparent' }}
              >
                {tag.name}
              </button>
            ))}
          </div>
        </div>
      </div>

      <div className="quadrant-grid">
        {quadrants.map((quadrant) => (
          <div
            key={quadrant.key}
            className="quadrant-panel"
            style={{
              borderTopColor: quadrant.key === 'reminder' || quadrant.key === 'record' ? quadrant.color : 'transparent',
              borderBottomColor: quadrant.key === 'urgent' || quadrant.key === 'important' ? quadrant.color : 'transparent',
              borderLeftColor: quadrant.key === 'reminder' || quadrant.key === 'urgent' ? quadrant.color : 'transparent',
              borderRightColor: quadrant.key === 'record' || quadrant.key === 'important' ? quadrant.color : 'transparent',
              '--quadrant-color': quadrant.color,
            } as React.CSSProperties}
          >
            <div className="quadrant-header" style={{ backgroundColor: `${quadrant.color}15` }}>
              <span className="quadrant-icon">{quadrant.icon}</span>
              <h2>{quadrant.label}</h2>
              <span className="quadrant-count">{itemsByQuadrant[quadrant.key].length}</span>
            </div>
            <div className="quadrant-items">
              {itemsByQuadrant[quadrant.key].length === 0 ? (
                <div className="empty-quadrant">暂无事项</div>
              ) : (
                (() => {
                  // 记录象限按 tag 分组显示
                  if (quadrant.key === 'record') {
                    const groupedByTag: Record<string, TodoItem[]> = {}
                    itemsByQuadrant[quadrant.key].forEach((item) => {
                      if (item.tags.length === 0) {
                        const key = '无标签'
                        if (!groupedByTag[key]) groupedByTag[key] = []
                        groupedByTag[key].push(item)
                      } else {
                        item.tags.forEach((tag) => {
                          if (!groupedByTag[tag.name]) groupedByTag[tag.name] = []
                          // 避免重复添加
                          if (!groupedByTag[tag.name].some((i) => i.id === item.id)) {
                            groupedByTag[tag.name].push(item)
                          }
                        })
                      }
                    })
                    return Object.entries(groupedByTag)
                      .sort(([a], [b]) => a.localeCompare(b))
                      .map(([tagName, items]) => (
                        <div key={tagName} className="tag-group">
                          <div className="tag-group-header">
                            <span className="tag-group-name">{tagName}</span>
                            <span className="tag-group-count">{items.length}</span>
                          </div>
                          {items.map((item) => renderQuadrantItem(item))}
                        </div>
                      ))
                  }
                  return itemsByQuadrant[quadrant.key].map((item) => renderQuadrantItem(item))
                })()
              )}
            </div>
          </div>
        ))}
      </div>

      {editingItem && (
        <div className="edit-modal-overlay" onClick={() => setEditingItem(null)}>
          <div className="edit-modal" onClick={(e) => e.stopPropagation()}>
            <h3>快速编辑</h3>
            <div className="edit-form">
              <div className="form-group">
                <label>标题</label>
                <input
                  type="text"
                  defaultValue={editingItem.title}
                  onBlur={(e) => {
                    if (e.target.value !== editingItem.title) {
                      todoApi.update(editingItem.id, { title: e.target.value }).then(() => onItemChange())
                    }
                  }}
                />
              </div>
              <div className="form-group">
                <label>完成状态</label>
                <label className="checkbox-label">
                  <input
                    type="checkbox"
                    defaultChecked={editingItem.is_completed}
                    onChange={(e) => {
                      todoApi.update(editingItem.id, { is_completed: e.target.checked }).then(() => onItemChange())
                    }}
                  />
                  <span>已完成</span>
                </label>
              </div>
              <div className="form-actions">
                <button className="btn btn-secondary" onClick={() => setEditingItem(null)}>
                  关闭
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )

  function renderQuadrantItem(item: TodoItem) {
    // 根据象限设置颜色
    const quadrantColor = quadrants.find((q) => q.key === item.quadrant)?.color || '#666'
    return (
      <div key={item.id} className="quadrant-item" style={{ '--quadrant-color': quadrantColor } as React.CSSProperties}>
        <div className="item-checkbox">
          <input
            type="checkbox"
            checked={item.is_completed}
            onChange={() => handleToggleComplete(item)}
          />
        </div>
        <div className="item-content-wrapper">
          <div className="item-title-row">
            <h4>{item.title}</h4>
            <div className="item-actions">
              <button className="btn-small" onClick={() => handleEdit(item)}>
                编辑
              </button>
              <button className="btn-small btn-danger" onClick={() => handleDelete(item.id)}>
                删除
              </button>
            </div>
          </div>
          {item.content && (
            <div className="item-content">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>{item.content}</ReactMarkdown>
            </div>
          )}
          <div className="item-meta">
            {item.priority && (
              <span className="meta-badge priority" style={{ color: item.priority.color || '#666' }}>
                {item.priority.name}
              </span>
            )}
            {item.tags.map((tag) => (
              <span key={tag.id} className="meta-badge tag" style={{ backgroundColor: tag.color || '#e0e0e0' }}>
                {tag.name}
              </span>
            ))}
            {item.due_time && (
              <span className="meta-badge time">
                截止: {formatUTC8DateTime(item.due_time)}
              </span>
            )}
            {item.reminder_time && (
              <span className="meta-badge time">
                提醒: {formatUTC8DateTime(item.reminder_time)}
              </span>
            )}
          </div>
        </div>
      </div>
    )
  }
}

export default QuadrantView

