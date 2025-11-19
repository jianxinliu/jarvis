import { useEffect, useState, useCallback } from 'react'
import Launcher from './components/Launcher'
import AppView from './components/AppView'
import AppManager from './components/AppManager'
import Modal from './components/Modal'
import useWebSocket from './hooks/useWebSocket'
import { useModal } from './hooks/useModal'
import { requestNotificationPermission, showReminderNotification } from './utils/notification'
import { reminderApi } from './api'
import axios from 'axios'
import type { App, ReminderLog } from './types'
import './App.css'

type ViewMode = 'launcher' | 'app' | 'manager'

function App() {
  const [viewMode, setViewMode] = useState<ViewMode>('launcher')
  const [currentApp, setCurrentApp] = useState<App | null>(null)
  const [reminders, setReminders] = useState<ReminderLog[]>([])
  const [apps, setApps] = useState<App[]>([])
  const modal = useModal()

  // 加载应用列表
  const loadApps = useCallback(async () => {
    try {
      const response = await axios.get('/api/apps', {
        params: { enabled_only: true },
      })
      if (response.data && Array.isArray(response.data)) {
        setApps(response.data)
      }
    } catch (error) {
      console.error('加载应用列表失败:', error)
    }
  }, [])

  useEffect(() => {
    loadApps()
  }, [loadApps])

  // 加载提醒列表
  const loadReminders = useCallback(async () => {
    try {
      const data = await reminderApi.getUnread()
      setReminders(data)
    } catch (error) {
      console.error('加载提醒失败:', error)
    }
  }, [])

  // 初始化时加载提醒
  useEffect(() => {
    loadReminders()
    // 定期刷新提醒列表（每30秒）
    const interval = setInterval(loadReminders, 30000)
    return () => clearInterval(interval)
  }, [loadReminders])

  // 从URL路径加载应用
  useEffect(() => {
    const path = window.location.pathname
    if (path.startsWith('/app/')) {
      const appId = path.replace('/app/', '').split('/')[0]
      if (appId) {
        loadApp(appId)
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const loadApp = async (appId: string) => {
    try {
      const response = await fetch(`/api/apps/${appId}`)
      if (!response.ok) {
        throw new Error('加载应用信息失败')
      }
      const app: App = await response.json()
      setCurrentApp(app)
      setViewMode('app')
      window.history.pushState({ appId }, '', `/app/${appId}`)
    } catch (error) {
      console.error('加载应用失败:', error)
      modal.showAlert('加载应用失败，请稍后重试', 'error')
    }
  }

  const { connectWebSocket, disconnectWebSocket } = useWebSocket(async (message) => {
    if (message.type === 'reminder' && message.data) {
      // 收到新的提醒，直接显示浏览器通知
      await showReminderNotification(message.data)
      // 刷新提醒列表
      loadReminders()
    }
  })

  useEffect(() => {
    connectWebSocket()

    // 请求通知权限（页面加载时主动请求）
    requestNotificationPermission().then((permission) => {
      if (permission === 'granted') {
        console.log('浏览器通知权限已授予')
      } else if (permission === 'denied') {
        console.warn('用户已拒绝浏览器通知权限')
      }
    })

    return () => {
      disconnectWebSocket()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const handleLaunchApp = async (appId: string) => {
    await loadApp(appId)
  }

  const handleBackToLauncher = () => {
    setViewMode('launcher')
    setCurrentApp(null)
    // 恢复URL路径
    window.history.pushState({}, '', '/')
  }

  const handleManageApps = () => {
    setViewMode('manager')
  }

  if (viewMode === 'manager') {
    return (
      <div className="app">
        <header className="app-header">
          <div>
            <h1>Jarvis</h1>
            <p>操作系统式应用平台</p>
          </div>
        </header>

        <div className="app-content">
          <div className="main-panel">
            <button className="btn btn-secondary" onClick={() => setViewMode('launcher')}>
              ← 返回启动台
            </button>
            <AppManager />
          </div>
        </div>
      </div>
    )
  }

  if (viewMode === 'app' && currentApp) {
    return (
      <div className="app">
        <header className="app-header">
          <div>
            <h1>Jarvis</h1>
            <p>操作系统式应用平台</p>
          </div>
        </header>

        <div className="app-content">
          <AppView app={currentApp} onBack={handleBackToLauncher} />
        </div>
      </div>
    )
  }

  return (
    <div className="app">
      <header className="app-header">
        <div>
          <h1>Jarvis</h1>
          <p>操作系统式应用平台</p>
        </div>
      </header>

      <div className="app-content">
        <Launcher 
          onLaunchApp={handleLaunchApp} 
          onManageApps={handleManageApps}
          reminders={reminders}
          onUpdateReminders={loadReminders}
          apps={apps}
        />
      </div>
      <Modal
        isOpen={modal.isOpen}
        onClose={modal.hide}
        title={modal.title}
        message={modal.message}
        type={modal.options.type}
        showCancel={modal.options.showCancel}
        onConfirm={modal.options.onConfirm}
        confirmText={modal.options.confirmText}
        cancelText={modal.options.cancelText}
      />
    </div>
  )
}

export default App

