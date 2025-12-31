import { useState, useEffect, useRef, useImperativeHandle, forwardRef } from 'react'
import { todoApi } from '../api'
import type { TodoTag } from '../types'
import './QuickRecord.css'

interface QuickRecordProps {
  onRecordAdded?: () => void
  className?: string
}

export interface QuickRecordRef {
  focus: () => void
}

const QuickRecord = forwardRef<QuickRecordRef, QuickRecordProps>(function QuickRecord(
  { onRecordAdded, className = '' },
  ref
) {
  const [title, setTitle] = useState('')
  const [duration, setDuration] = useState('')
  const [selectedTagIds, setSelectedTagIds] = useState<number[]>([])
  const [tags, setTags] = useState<TodoTag[]>([])
  const [loading, setLoading] = useState(false)
  const [expanded, setExpanded] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)

  useImperativeHandle(ref, () => ({
    focus: () => {
      if (inputRef.current) {
        inputRef.current.focus()
        setExpanded(true)
      }
    }
  }))

  useEffect(() => {
    loadTags()
  }, [])

  const loadTags = async () => {
    try {
      const tagsData = await todoApi.getTags()
      setTags(tagsData)
    } catch (error) {
      console.error('加载标签失败:', error)
    }
  }

  const submitRecord = async () => {
    if (!title.trim()) return

    setLoading(true)
    try {
      // 创建新的记录项
      await todoApi.create({
        title: title.trim(),
        content: duration ? `耗时: ${duration}` : '',
        quadrant: 'record', // 默认放在记录象限
        tag_ids: selectedTagIds.length > 0 ? selectedTagIds : undefined,
        // 可以自动设置创建时间为当前时间
      })

      // 重置表单
      setTitle('')
      setDuration('')
      setSelectedTagIds([])
      setExpanded(false)

      // 通知父组件
      if (onRecordAdded) {
        onRecordAdded()
      }
    } catch (error) {
      console.error('记录失败:', error)
      alert('记录失败，请重试')
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    await submitRecord()
  }

  const handleTagToggle = (tagId: number) => {
    if (selectedTagIds.includes(tagId)) {
      setSelectedTagIds(selectedTagIds.filter(id => id !== tagId))
    } else {
      setSelectedTagIds([...selectedTagIds, tagId])
    }
  }

  const handleQuickAdd = () => {
    if (!title.trim()) return
    
    // 如果没有展开，直接提交
    if (!expanded) {
      submitRecord()
    }
  }

  return (
    <div className={`quick-record ${className}`}>
      <form onSubmit={handleSubmit} className="quick-record-form">
        <div className="quick-record-main">
           <input
             type="text"
             value={title}
             onChange={(e) => setTitle(e.target.value)}
             placeholder="记录你今天做了什么..."
             className="quick-record-input"
             ref={inputRef}
             onFocus={() => setExpanded(true)}
             onKeyDown={(e) => {
               if (e.key === 'Enter' && !e.shiftKey) {
                 e.preventDefault()
                 handleQuickAdd()
               }
             }}
           />
          <button
            type="button"
            onClick={() => setExpanded(!expanded)}
            className="quick-record-toggle"
            title={expanded ? '收起选项' : '展开选项'}
          >
            {expanded ? '−' : '+'}
          </button>
        </div>

        {expanded && (
          <div className="quick-record-options">
            <div className="quick-record-option">
              <label>耗时（可选）</label>
              <input
                type="text"
                value={duration}
                onChange={(e) => setDuration(e.target.value)}
                placeholder="例如: 2h, 30min, 1.5h"
                className="quick-record-duration"
              />
            </div>

            {tags.length > 0 && (
              <div className="quick-record-option">
                <label>标签（可选）</label>
                <div className="quick-record-tags">
                  {tags.map(tag => (
                    <button
                      type="button"
                      key={tag.id}
                      className={`quick-record-tag ${selectedTagIds.includes(tag.id) ? 'selected' : ''}`}
                      onClick={() => handleTagToggle(tag.id)}
                      style={tag.color ? { borderLeftColor: tag.color } : undefined}
                    >
                      {tag.name}
                    </button>
                  ))}
                </div>
              </div>
            )}

            <div className="quick-record-actions">
              <button
                type="button"
                onClick={() => {
                  setExpanded(false)
                  setTitle('')
                  setDuration('')
                  setSelectedTagIds([])
                }}
                className="quick-record-cancel"
              >
                取消
              </button>
              <button
                type="submit"
                disabled={!title.trim() || loading}
                className="quick-record-submit"
              >
                {loading ? '记录中...' : '记录'}
              </button>
            </div>
          </div>
        )}

        {!expanded && title.trim() && (
          <button
            type="button"
            onClick={handleQuickAdd}
            disabled={loading}
            className="quick-record-submit-inline"
          >
            {loading ? '记录中...' : '记录'}
          </button>
        )}
      </form>
    </div>
  )
})

export default QuickRecord