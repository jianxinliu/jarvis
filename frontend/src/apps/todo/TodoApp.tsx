import { useState, useEffect } from 'react'
import { todoApi } from '../../api'
import type { TodoItem, TodoTag, TodoPriority } from '../../types'
import TodoEditor from './TodoEditor'
import QuadrantView from './QuadrantView'
import TagPriorityManager from './TagPriorityManager'
import './TodoApp.css'

function TodoApp() {
  const [activeTab, setActiveTab] = useState<'editor' | 'quadrant' | 'settings'>('editor')
  const [items, setItems] = useState<TodoItem[]>([])
  const [tags, setTags] = useState<TodoTag[]>([])
  const [priorities, setPriorities] = useState<TodoPriority[]>([])
  const [loading, setLoading] = useState(true)
  const [editingItem, setEditingItem] = useState<TodoItem | null>(null)

  // 监听编辑器重置事件
  useEffect(() => {
    const handleReset = () => {
      setEditingItem(null)
    }
    window.addEventListener('todo-editor-reset', handleReset)
    return () => {
      window.removeEventListener('todo-editor-reset', handleReset)
    }
  }, [])

  const loadData = async () => {
    try {
      setLoading(true)
      const [itemsData, tagsData, prioritiesData] = await Promise.all([
        todoApi.getItems(),
        todoApi.getTags(),
        todoApi.getPriorities(),
      ])
      setItems(itemsData)
      setTags(tagsData)
      setPriorities(prioritiesData)
    } catch (error) {
      console.error('加载数据失败:', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [])

  const handleItemChange = () => {
    loadData()
  }

  if (loading) {
    return <div className="todo-app-loading">加载中...</div>
  }

  return (
    <div className="todo-app">
      <div className="todo-tabs">
        <button
          className={`todo-tab ${activeTab === 'editor' ? 'active' : ''}`}
          onClick={() => setActiveTab('editor')}
        >
          事件编辑
        </button>
        <button
          className={`todo-tab ${activeTab === 'quadrant' ? 'active' : ''}`}
          onClick={() => setActiveTab('quadrant')}
        >
          四象限
        </button>
        <button
          className={`todo-tab ${activeTab === 'settings' ? 'active' : ''}`}
          onClick={() => setActiveTab('settings')}
        >
          标签/优先级
        </button>
      </div>

      <div className="todo-content">
        <div className={`todo-tab-content ${activeTab === 'editor' ? 'active' : ''}`}>
          <TodoEditor
            items={items}
            tags={tags}
            priorities={priorities}
            onItemChange={handleItemChange}
            initialItem={editingItem}
          />
        </div>
        <div className={`todo-tab-content ${activeTab === 'quadrant' ? 'active' : ''}`}>
          <QuadrantView
            items={items}
            tags={tags}
            onItemChange={handleItemChange}
            onEditInEditor={async (item) => {
              // 从 API 获取完整数据（包括子任务）
              try {
                const fullItem = await todoApi.getItem(item.id)
                setEditingItem(fullItem)
                // 使用 setTimeout 确保状态更新后再切换 tab
                setTimeout(() => {
                  setActiveTab('editor')
                }, 0)
              } catch (error: any) {
                console.error('获取事件详情失败:', error)
                // 如果 API 失败（404 或其他错误），使用现有数据作为降级方案
                if (error.response?.status === 404) {
                  console.warn('事件不存在，使用现有数据作为降级方案')
                } else {
                  console.warn('API 调用失败，使用现有数据作为降级方案')
                }
                setEditingItem(item)
                setTimeout(() => {
                  setActiveTab('editor')
                }, 0)
              }
            }}
          />
        </div>
        <div className={`todo-tab-content ${activeTab === 'settings' ? 'active' : ''}`}>
          <TagPriorityManager
            tags={tags}
            priorities={priorities}
            onDataChange={loadData}
          />
        </div>
      </div>
    </div>
  )
}

export default TodoApp

