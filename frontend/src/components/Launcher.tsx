import { useEffect, useState, forwardRef } from 'react'
import axios from 'axios'
import ReminderPanel from '../apps/tasks/ReminderPanel'
import QuickRecord, { QuickRecordRef } from './QuickRecord'
import RecentRecords from './RecentRecords'
import type { App, ReminderLog } from '../types'
import './Launcher.css'

interface LauncherProps {
  onLaunchApp: (appId: string) => void
  onManageApps?: () => void
  reminders?: ReminderLog[]
  onUpdateReminders?: () => void
  apps?: App[]
  onRecordAdded?: () => void
}

const Launcher = forwardRef<QuickRecordRef, LauncherProps>(function Launcher(
  { onLaunchApp, onManageApps, reminders = [], onUpdateReminders, apps: appsProp = [], onRecordAdded },
  ref
) {
  const [apps, setApps] = useState<App[]>([])
  const [loading, setLoading] = useState(true)
  const [recordVersion, setRecordVersion] = useState(0)

  useEffect(() => {
    // 如果从 props 传入 apps，直接使用；否则加载
    if (appsProp.length > 0) {
      setApps(appsProp)
      setLoading(false)
    } else {
      loadApps()
    }
  }, [appsProp])

  const loadApps = async () => {
    try {
      const response = await axios.get('/api/apps', {
        params: { enabled_only: true },
      })
      if (response.data && Array.isArray(response.data)) {
        setApps(response.data)
      } else {
        setApps([])
      }
    } catch (error) {
      console.error('加载应用失败:', error)
      setApps([])
    } finally {
      setLoading(false)
    }
  }

  const handleRecordAdded = () => {
    setRecordVersion(v => v + 1)
    if (onRecordAdded) {
      onRecordAdded()
    }
  }

  if (loading) {
    return (
      <div className="launcher">
        <div className="launcher-loading">加载中...</div>
      </div>
    )
  }

  return (
    <div className="launcher">
      <div className="launcher-header">
        <div className="launcher-title-section">
          <img src="/icon.svg" alt="Jarvis" className="launcher-icon" />
          <div>
            <h1>启动台</h1>
            <p>选择应用开始使用</p>
          </div>
        </div>
        {onManageApps && (
          <button className="btn btn-secondary" onClick={onManageApps}>
            应用管理
          </button>
        )}
      </div>

       <div className="launcher-content">
        <div className="launcher-main">
           <QuickRecord ref={ref} onRecordAdded={handleRecordAdded} />
          <div className="apps-grid">
            {apps.map((app) => (
              <div
                key={app.app_id}
                className="app-card"
                onClick={() => onLaunchApp(app.app_id)}
              >
                <div className="app-icon">{app.icon || '📦'}</div>
                <div className="app-name">{app.name}</div>
                {app.description && (
                  <div className="app-description">{app.description}</div>
                )}
                {app.is_builtin && <span className="app-badge">内置</span>}
              </div>
            ))}
          </div>

          {apps.length === 0 && (
            <div className="launcher-empty">
              <p>暂无可用应用</p>
            </div>
          )}
        </div>

        <div className="launcher-sidebar">
          <RecentRecords key={recordVersion} />
          <ReminderPanel 
            reminders={reminders} 
            onUpdate={onUpdateReminders || (() => {})}
            apps={apps}
          />
        </div>
      </div>
    </div>
  )
})

export default Launcher

