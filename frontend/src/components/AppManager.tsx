import { useEffect, useState } from 'react'
import axios from 'axios'
import type { App } from '../types'
import './AppManager.css'

function AppManager() {
  const [apps, setApps] = useState<App[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadApps()
  }, [])

  const loadApps = async () => {
    try {
      const response = await axios.get('/api/apps')
      setApps(response.data)
    } catch (error) {
      console.error('加载应用列表失败:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleToggleApp = async (appId: string) => {
    try {
      await axios.post(`/api/apps/${appId}/toggle`)
      loadApps()
    } catch (error) {
      console.error('切换应用状态失败:', error)
      alert('操作失败，请稍后重试')
    }
  }

  const handleReloadApp = async (appId: string) => {
    try {
      await axios.post(`/api/apps/${appId}/reload`)
      alert('应用已重新加载')
      loadApps()
    } catch (error: any) {
      console.error('重新加载应用失败:', error)
      alert(error.response?.data?.detail || '重新加载失败')
    }
  }

  const handleDeleteApp = async (appId: string, isBuiltin: boolean) => {
    if (isBuiltin) {
      alert('不能删除内置应用')
      return
    }

    if (!confirm(`确定要删除应用 "${appId}" 吗？此操作不可恢复。`)) {
      return
    }

    try {
      await axios.delete(`/api/apps/${appId}`)
      loadApps()
    } catch (error: any) {
      console.error('删除应用失败:', error)
      alert(error.response?.data?.detail || '删除失败')
    }
  }

  if (loading) {
    return <div className="app-manager-loading">加载中...</div>
  }

  return (
    <div className="app-manager">
      <div className="app-manager-header">
        <h2>应用管理</h2>
        <p>管理已安装的应用，启用/禁用、重新加载或卸载应用</p>
      </div>

      <div className="apps-table">
        <table>
          <thead>
            <tr>
              <th>应用</th>
              <th>版本</th>
              <th>路由</th>
              <th>状态</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            {apps.map((app) => (
              <tr key={app.app_id}>
                <td>
                  <div className="app-info">
                    <span className="app-icon">{app.icon || '📦'}</span>
                    <div>
                      <div className="app-name-row">
                        <span className="app-name">{app.name}</span>
                        {app.is_builtin && <span className="builtin-badge">内置</span>}
                      </div>
                      {app.description && (
                        <div className="app-desc">{app.description}</div>
                      )}
                    </div>
                  </div>
                </td>
                <td>{app.version}</td>
                <td>
                  <code className="route-code">{app.route_prefix}</code>
                </td>
                <td>
                  <span className={`status-badge ${app.is_enabled ? 'enabled' : 'disabled'}`}>
                    {app.is_enabled ? '已启用' : '已禁用'}
                  </span>
                </td>
                <td>
                  <div className="app-actions">
                    <button
                      className="btn btn-secondary btn-small"
                      onClick={() => handleToggleApp(app.app_id)}
                    >
                      {app.is_enabled ? '禁用' : '启用'}
                    </button>
                    {app.is_enabled && (
                      <button
                        className="btn btn-secondary btn-small"
                        onClick={() => handleReloadApp(app.app_id)}
                      >
                        重新加载
                      </button>
                    )}
                    {!app.is_builtin && (
                      <button
                        className="btn btn-danger btn-small"
                        onClick={() => handleDeleteApp(app.app_id, app.is_builtin)}
                      >
                        删除
                      </button>
                    )}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {apps.length === 0 && (
        <div className="app-manager-empty">
          <p>暂无应用</p>
        </div>
      )}
    </div>
  )
}

export default AppManager

