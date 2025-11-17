import { useEffect, useState, Suspense } from 'react'
import TaskList from '../apps/tasks/TaskList'
import TaskForm from '../apps/tasks/TaskForm'
import ReminderPanel from '../apps/tasks/ReminderPanel'
import { hasAppComponent, getAppComponent } from '../apps/registry'
import type { Task, ReminderLog, App } from '../types'
import { taskApi, reminderApi } from '../api'
import './AppView.css'

interface AppViewProps {
  app: App
  onBack: () => void
  isInTab?: boolean
}

function AppView({ app, onBack, isInTab = false }: AppViewProps) {
  const [tasks, setTasks] = useState<Task[]>([])
  const [reminders, setReminders] = useState<ReminderLog[]>([])
  const [showForm, setShowForm] = useState(false)
  const [editingTask, setEditingTask] = useState<Task | null>(null)
  const [activeTab, setActiveTab] = useState<'tasks' | 'today'>('tasks')

  useEffect(() => {
    if (app.app_id === 'tasks') {
      loadTasks()
      loadReminders()
    } else if (app.app_id === 'excel') {
      loadReminders()
    }
  }, [app.app_id])

  const loadTasks = async () => {
    try {
      const data = await taskApi.getAll()
      setTasks(data)
    } catch (error) {
      console.error('加载任务失败:', error)
    }
  }

  const loadReminders = async () => {
    try {
      const data = await reminderApi.getUnread()
      setReminders(data)
    } catch (error) {
      console.error('加载提醒失败:', error)
    }
  }

  const handleTaskCreated = () => {
    loadTasks()
    setShowForm(false)
    setEditingTask(null)
  }

  const handleTaskUpdated = () => {
    loadTasks()
    setShowForm(false)
    setEditingTask(null)
  }

  const handleTaskDeleted = () => {
    loadTasks()
  }

  const handleEditTask = (task: Task) => {
    setEditingTask(task)
    setShowForm(true)
  }

  const handleTabChange = async (tab: 'tasks' | 'today') => {
    setActiveTab(tab)
    if (tab === 'today') {
      try {
        const data = await taskApi.getToday()
        setTasks(data)
      } catch (error) {
        console.error('加载今日任务失败:', error)
      }
    } else {
      loadTasks()
    }
  }

  // 根据应用ID渲染不同的内容
  const renderAppContent = () => {
    // 特殊处理 tasks 应用（需要额外的状态管理）
    if (app.app_id === 'tasks') {
      return (
        <>
          <div className="tabs">
            <button
              className={activeTab === 'tasks' ? 'active' : ''}
              onClick={() => handleTabChange('tasks')}
            >
              所有任务
            </button>
            <button
              className={activeTab === 'today' ? 'active' : ''}
              onClick={() => handleTabChange('today')}
            >
              今日任务
            </button>
          </div>

          <div className="task-actions">
            <button
              className="btn btn-primary"
              onClick={() => {
                setEditingTask(null)
                setShowForm(true)
              }}
            >
              新建任务
            </button>
          </div>

          {showForm && (
            <TaskForm
              task={editingTask}
              onSave={editingTask ? handleTaskUpdated : handleTaskCreated}
              onCancel={() => {
                setShowForm(false)
                setEditingTask(null)
              }}
            />
          )}

          <TaskList
            tasks={tasks}
            onEdit={handleEditTask}
            onDelete={handleTaskDeleted}
            onUpdate={loadTasks}
          />
        </>
      )
    }

    // 使用注册表加载其他应用组件
    if (hasAppComponent(app.app_id)) {
      const AppComponent = getAppComponent(app.app_id)
      if (AppComponent) {
        return (
          <Suspense fallback={<div className="app-loading">加载中...</div>}>
            <AppComponent />
          </Suspense>
        )
      }
    }

    // 默认：应用未实现前端界面
    return (
      <div className="app-not-found">
        <p>应用 "{app.name}" 的前端界面尚未实现</p>
        <p className="app-route">API 路由: {app.route_prefix}</p>
      </div>
    )
  }

  return (
    <div className="app-view">
      {!isInTab && (
        <div className="app-view-header">
          <button className="btn-back" onClick={onBack}>
            ← 返回启动台
          </button>
          <div className="app-view-title">
            <span className="app-icon">{app.icon || '📦'}</span>
            <div>
              <h1>{app.name}</h1>
              {app.description && <p>{app.description}</p>}
            </div>
          </div>
        </div>
      )}
      {isInTab && (
        <div className="app-view-header">
          <div className="app-view-title">
            <span className="app-icon">{app.icon || '📦'}</span>
            <div>
              <h1>{app.name}</h1>
              {app.description && <p>{app.description}</p>}
            </div>
          </div>
        </div>
      )}

      <div className="app-view-content">
        <div className="main-panel">{renderAppContent()}</div>
        {app.app_id === 'tasks' && (
          <ReminderPanel reminders={reminders} onUpdate={loadReminders} />
        )}
      </div>
    </div>
  )
}

export default AppView

