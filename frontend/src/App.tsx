import { useEffect, useState } from 'react'
import Launcher from './components/Launcher'
import AppView from './components/AppView'
import AppManager from './components/AppManager'
import useWebSocket from './hooks/useWebSocket'
import type { App } from './types'
import './App.css'

type ViewMode = 'launcher' | 'app' | 'manager'

function App() {
  const [viewMode, setViewMode] = useState<ViewMode>('launcher')
  const [currentApp, setCurrentApp] = useState<App | null>(null)

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
      alert('加载应用失败，请稍后重试')
    }
  }

  const loadReminders = async () => {
    try {
      const { reminderApi } = await import('./api')
      const data = await reminderApi.getUnread()
      // 显示浏览器通知
      if (Notification.permission === 'granted' && data.length > 0) {
        new Notification('Jarvis 提醒', {
          body: data[0].content || '您有新的提醒',
          icon: '/vite.svg',
        })
      }
    } catch (error) {
      console.error('加载提醒失败:', error)
    }
  }

  const { connectWebSocket, disconnectWebSocket } = useWebSocket((message) => {
    if (message.type === 'reminder') {
      // 收到新的提醒，刷新提醒列表
      loadReminders()
    }
  })

  useEffect(() => {
    connectWebSocket()

    // 请求通知权限
    if ('Notification' in window && Notification.permission === 'default') {
      Notification.requestPermission()
    }

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
        <Launcher onLaunchApp={handleLaunchApp} onManageApps={handleManageApps} />
      </div>
    </div>
  )
}

export default App

