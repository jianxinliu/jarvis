import { useState, useEffect, useCallback } from 'react'
import AppView from './AppView'
import type { App } from '../types'
import './TabContainer.css'

interface TabContainerProps {
  onBackToLauncher: () => void
  onTabsChange?: (hasTabs: boolean) => void
}

interface Tab {
  app: App
  id: string
}

function TabContainer({ onBackToLauncher, onTabsChange }: TabContainerProps) {
  const [tabs, setTabs] = useState<Tab[]>([])
  const [activeTabId, setActiveTabId] = useState<string | null>(null)

  // 从 URL 或本地存储恢复 tabs
  useEffect(() => {
    const savedTabs = localStorage.getItem('jarvis_tabs')
    const savedActiveTab = localStorage.getItem('jarvis_active_tab')
    
    if (savedTabs) {
      try {
        const parsedTabs = JSON.parse(savedTabs) as Tab[]
        setTabs(parsedTabs)
        if (savedActiveTab && parsedTabs.some(t => t.id === savedActiveTab)) {
          setActiveTabId(savedActiveTab)
        } else if (parsedTabs.length > 0) {
          setActiveTabId(parsedTabs[0].id)
        }
      } catch (error) {
        console.error('恢复 tabs 失败:', error)
      }
    }
  }, [])

  // 保存 tabs 到本地存储，并通知父组件
  useEffect(() => {
    if (tabs.length > 0) {
      localStorage.setItem('jarvis_tabs', JSON.stringify(tabs))
    } else {
      localStorage.removeItem('jarvis_tabs')
    }
    onTabsChange?.(tabs.length > 0)
  }, [tabs, onTabsChange])

  // 保存当前激活的 tab
  useEffect(() => {
    if (activeTabId) {
      localStorage.setItem('jarvis_active_tab', activeTabId)
    } else {
      localStorage.removeItem('jarvis_active_tab')
    }
  }, [activeTabId])

  // 从 URL 加载应用（用于直接访问 /app/{appId}）
  useEffect(() => {
    const path = window.location.pathname
    if (path.startsWith('/app/')) {
      const appId = path.replace('/app/', '').split('/')[0]
      if (appId && !tabs.some(t => t.app.app_id === appId)) {
        handleLaunchApp(appId)
      }
    }
  }, [])

  const handleLaunchApp = useCallback(async (appId: string) => {
    // 检查是否已经打开
    const existingTab = tabs.find(t => t.app.app_id === appId)
    if (existingTab) {
      setActiveTabId(existingTab.id)
      window.history.pushState({ appId }, '', `/app/${appId}`)
      return
    }

    try {
      const response = await fetch(`/api/apps/${appId}`)
      if (!response.ok) {
        throw new Error('加载应用信息失败')
      }
      const app: App = await response.json()
      
      const newTab: Tab = {
        app,
        id: `${appId}-${Date.now()}`,
      }
      
      setTabs(prev => [...prev, newTab])
      setActiveTabId(newTab.id)
      window.history.pushState({ appId }, '', `/app/${appId}`)
    } catch (error) {
      console.error('加载应用信息失败:', error)
      alert('加载应用失败，请稍后重试')
    }
  }, [tabs])

  // 暴露给全局，让 Launcher 可以调用
  useEffect(() => {
    ;(window as any).jarvisLaunchApp = handleLaunchApp
    return () => {
      delete (window as any).jarvisLaunchApp
    }
  }, [handleLaunchApp])

  const handleCloseTab = useCallback((tabId: string) => {
    setTabs(prev => {
      const newTabs = prev.filter(t => t.id !== tabId)
      
      // 如果关闭的是当前激活的 tab，切换到其他 tab
      if (tabId === activeTabId) {
        if (newTabs.length > 0) {
          // 优先切换到相邻的 tab
          const closedIndex = prev.findIndex(t => t.id === tabId)
          const newActiveIndex = closedIndex > 0 ? closedIndex - 1 : 0
          setActiveTabId(newTabs[newActiveIndex]?.id || null)
          
          // 更新 URL
          if (newTabs[newActiveIndex]) {
            window.history.pushState(
              { appId: newTabs[newActiveIndex].app.app_id },
              '',
              `/app/${newTabs[newActiveIndex].app.app_id}`
            )
          }
        } else {
          setActiveTabId(null)
          window.history.pushState({}, '', '/')
        }
      }
      
      return newTabs
    })
  }, [activeTabId])

  const handleTabClick = useCallback((tabId: string) => {
    setActiveTabId(tabId)
    const tab = tabs.find(t => t.id === tabId)
    if (tab) {
      window.history.pushState({ appId: tab.app.app_id }, '', `/app/${tab.app.app_id}`)
    }
  }, [tabs])

  const activeTab = tabs.find(t => t.id === activeTabId)

  // 如果没有 tabs，显示启动台
  if (tabs.length === 0) {
    return null
  }

  return (
    <div className="tab-container">
      <div className="tab-header">
        <div className="tab-list">
          {tabs.map(tab => (
            <div
              key={tab.id}
              className={`tab-item ${tab.id === activeTabId ? 'active' : ''}`}
              onClick={() => handleTabClick(tab.id)}
            >
              <span className="tab-icon">{tab.app.icon || '📦'}</span>
              <span className="tab-title">{tab.app.name}</span>
              <button
                className="tab-close"
                onClick={(e) => {
                  e.stopPropagation()
                  handleCloseTab(tab.id)
                }}
                title="关闭"
              >
                ×
              </button>
            </div>
          ))}
        </div>
        <button className="btn-back" onClick={onBackToLauncher} title="返回启动台">
          ← 启动台
        </button>
      </div>

      <div className="tab-content">
        {activeTab && (
          <AppView
            app={activeTab.app}
            onBack={onBackToLauncher}
            isInTab={true}
          />
        )}
      </div>
    </div>
  )
}

export default TabContainer

