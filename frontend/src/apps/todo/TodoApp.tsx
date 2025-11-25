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
            onEditInEditor={(item) => {
              // 确保传递完整的 item 对象
              setEditingItem({ ...item })
              // 使用 setTimeout 确保状态更新后再切换 tab
              setTimeout(() => {
                setActiveTab('editor')
              }, 0)
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

