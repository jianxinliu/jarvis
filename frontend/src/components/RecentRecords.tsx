import { useState, useEffect } from 'react'
import { todoApi } from '../api'
import type { TodoItem } from '../types'
import './RecentRecords.css'

interface RecentRecordsProps {
  limit?: number
  onRecordClick?: (item: TodoItem) => void
}

function RecentRecords({ limit = 5, onRecordClick }: RecentRecordsProps) {
  const [records, setRecords] = useState<TodoItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadRecentRecords()
  }, [])

  const loadRecentRecords = async () => {
    try {
      setLoading(true)
      // 获取所有记录象限的待办事项，排除已归档的
      const allRecords = await todoApi.getItems('record', false, true)
      // 按创建时间倒序排序，取前 limit 个
      const sorted = allRecords.sort((a, b) => 
        new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
      ).slice(0, limit)
      setRecords(sorted)
      setError(null)
    } catch (err) {
      console.error('加载最近记录失败:', err)
      setError('加载失败，请重试')
    } finally {
      setLoading(false)
    }
  }

  const formatTime = (dateString: string) => {
    const date = new Date(dateString)
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffMins = Math.floor(diffMs / 60000)
    const diffHours = Math.floor(diffMs / 3600000)
    const diffDays = Math.floor(diffMs / (3600000 * 24))

    if (diffMins < 60) {
      return `${diffMins}分钟前`
    } else if (diffHours < 24) {
      return `${diffHours}小时前`
    } else if (diffDays < 7) {
      return `${diffDays}天前`
    } else {
      return date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
    }
  }

  const handleRecordClick = (item: TodoItem) => {
    if (onRecordClick) {
      onRecordClick(item)
    } else {
      // 默认行为：打开 TODO 应用并定位到该项（未来可以扩展）
      console.log('点击记录:', item)
    }
  }

  if (loading) {
    return (
      <div className="recent-records">
        <h3>最近记录</h3>
        <div className="loading">加载中...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="recent-records">
        <h3>最近记录</h3>
        <div className="error">{error}</div>
      </div>
    )
  }

  if (records.length === 0) {
    return (
      <div className="recent-records">
        <h3>最近记录</h3>
        <div className="empty">暂无记录</div>
      </div>
    )
  }

  return (
    <div className="recent-records">
      <div className="recent-records-header">
        <h3>最近记录</h3>
        <button 
          className="btn-refresh" 
          onClick={loadRecentRecords}
          title="刷新"
        >
          ↻
        </button>
      </div>
      <div className="records-list">
        {records.map(record => (
          <div 
            key={record.id} 
            className="record-item"
            onClick={() => handleRecordClick(record)}
          >
            <div className="record-title">{record.title}</div>
            <div className="record-meta">
              <span className="record-time">{formatTime(record.created_at)}</span>
              {record.tags.length > 0 && (
                <span className="record-tags">
                  {record.tags.map(tag => (
                    <span 
                      key={tag.id} 
                      className="record-tag"
                      style={tag.color ? { borderLeftColor: tag.color } : undefined}
                    >
                      {tag.name}
                    </span>
                  ))}
                </span>
              )}
            </div>
            {record.content && (
              <div className="record-content">{record.content}</div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}

export default RecentRecords