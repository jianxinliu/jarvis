import { useState, useRef, useEffect } from 'react'
import { todoApi } from '../../api'
import type { TodoTag, TodoTagCreate } from '../../types'
import { useModal } from '../../hooks/useModal'
import Modal from '../../components/Modal'
import './TagMultiSelect.css'

interface TagMultiSelectProps {
  tags: TodoTag[]
  selectedTagIds: number[]
  onChange: (tagIds: number[]) => void
  onTagCreated?: (tag: TodoTag) => void
}

function TagMultiSelect({ tags, selectedTagIds, onChange, onTagCreated }: TagMultiSelectProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [searchTerm, setSearchTerm] = useState('')
  const [isCreating, setIsCreating] = useState(false)
  const [newTagName, setNewTagName] = useState('')
  const dropdownRef = useRef<HTMLDivElement>(null)
  const modal = useModal()

  // 点击外部关闭下拉框
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false)
        setSearchTerm('')
        setIsCreating(false)
        setNewTagName('')
      }
    }

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside)
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [isOpen])

  // 过滤标签
  const filteredTags = tags.filter((tag) =>
    tag.name.toLowerCase().includes(searchTerm.toLowerCase())
  )

  // 检查是否有匹配的标签
  const hasMatchingTag = filteredTags.length > 0
  const canCreateNew = searchTerm.trim() && !hasMatchingTag && !isCreating

  // 切换标签选择
  const toggleTag = (tagId: number) => {
    if (selectedTagIds.includes(tagId)) {
      onChange(selectedTagIds.filter((id) => id !== tagId))
    } else {
      onChange([...selectedTagIds, tagId])
    }
  }

  // 创建新标签
  const handleCreateTag = async () => {
    if (!newTagName.trim()) return

    try {
      const newTag: TodoTagCreate = {
        name: newTagName.trim(),
        color: '#e0e0e0', // 默认颜色
      }
      const createdTag = await todoApi.createTag(newTag)
      onChange([...selectedTagIds, createdTag.id])
      // 通知父组件新标签已创建，但不刷新整个页面
      if (onTagCreated) {
        onTagCreated(createdTag)
      }
      setNewTagName('')
      setIsCreating(false)
      setSearchTerm('')
      modal.showAlert('标签创建成功', 'success')
    } catch (error) {
      console.error('创建标签失败:', error)
      modal.showAlert('创建标签失败', 'error')
    }
  }

  // 获取选中的标签
  const selectedTags = tags.filter((tag) => selectedTagIds.includes(tag.id))

  return (
    <div className="tag-multi-select" ref={dropdownRef}>
      <div className="tag-selector-input" onClick={() => setIsOpen(!isOpen)}>
        <div className="selected-tags">
          {selectedTags.length > 0 ? (
            selectedTags.map((tag) => (
              <span key={tag.id} className="selected-tag" style={{ backgroundColor: tag.color || '#e0e0e0' }}>
                {tag.name}
                <button
                  type="button"
                  className="tag-remove"
                  onClick={(e) => {
                    e.stopPropagation()
                    onChange(selectedTagIds.filter((id) => id !== tag.id))
                  }}
                >
                  ×
                </button>
              </span>
            ))
          ) : (
            <span className="placeholder">选择标签...</span>
          )}
        </div>
        <span className="dropdown-arrow">{isOpen ? '▲' : '▼'}</span>
      </div>

      {isOpen && (
        <div className="tag-dropdown">
          <div className="tag-search">
            <input
              type="text"
              placeholder="搜索或创建标签..."
              value={searchTerm}
              onChange={(e) => {
                setSearchTerm(e.target.value)
                setIsCreating(false)
              }}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && canCreateNew) {
                  setNewTagName(searchTerm)
                  setIsCreating(true)
                }
              }}
              autoFocus
            />
          </div>

          {isCreating ? (
            <div className="tag-create-form">
              <input
                type="text"
                placeholder="输入新标签名称"
                value={newTagName}
                onChange={(e) => setNewTagName(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    handleCreateTag()
                  } else if (e.key === 'Escape') {
                    setIsCreating(false)
                    setNewTagName('')
                  }
                }}
                autoFocus
              />
              <div className="tag-create-actions">
                <button type="button" className="btn-create" onClick={handleCreateTag}>
                  创建
                </button>
                <button
                  type="button"
                  className="btn-cancel"
                  onClick={() => {
                    setIsCreating(false)
                    setNewTagName('')
                  }}
                >
                  取消
                </button>
              </div>
            </div>
          ) : (
            <>
              {filteredTags.length > 0 && (
                <div className="tag-list">
                  {filteredTags.map((tag) => (
                    <label key={tag.id} className="tag-option">
                      <input
                        type="checkbox"
                        checked={selectedTagIds.includes(tag.id)}
                        onChange={() => toggleTag(tag.id)}
                      />
                      <span className="tag-option-label" style={{ backgroundColor: tag.color || '#e0e0e0' }}>
                        {tag.name}
                      </span>
                    </label>
                  ))}
                </div>
              )}

              {canCreateNew && (
                <div className="tag-create-hint">
                  <button
                    type="button"
                    className="btn-create-new"
                    onClick={() => {
                      setNewTagName(searchTerm)
                      setIsCreating(true)
                    }}
                  >
                    + 创建标签 "{searchTerm}"
                  </button>
                </div>
              )}

              {!hasMatchingTag && !canCreateNew && searchTerm && (
                <div className="tag-empty">未找到匹配的标签</div>
              )}
            </>
          )}
        </div>
      )}

      <Modal
        isOpen={modal.isOpen}
        onClose={modal.hide}
        title={modal.title}
        message={modal.message}
        type={modal.options.type || 'info'}
        showCancel={modal.options.showCancel}
        onConfirm={modal.options.onConfirm}
        confirmText={modal.options.confirmText}
        cancelText={modal.options.cancelText}
      />
    </div>
  )
}

export default TagMultiSelect

