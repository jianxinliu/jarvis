import { useEffect, useState } from 'react'
import axios from 'axios'
import type { App } from '../types'
import './Launcher.css'

interface LauncherProps {
  onLaunchApp: (appId: string) => void
  onManageApps?: () => void
}

function Launcher({ onLaunchApp, onManageApps }: LauncherProps) {
  const [apps, setApps] = useState<App[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadApps()
  }, [])

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
        <div>
          <h1>启动台</h1>
          <p>选择应用开始使用</p>
        </div>
        {onManageApps && (
          <button className="btn btn-secondary" onClick={onManageApps}>
            应用管理
          </button>
        )}
      </div>

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
  )
}

export default Launcher

