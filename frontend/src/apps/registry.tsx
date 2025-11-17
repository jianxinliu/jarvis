/**
 * 应用组件注册表
 * 
 * 新增应用时，在此文件中注册应用的前端组件
 * 
 * 注意：
 * - tasks 应用需要特殊处理（有复杂的状态管理），不在此注册表中
 * - 其他应用可以在此注册，组件必须是默认导出
 */

import { lazy, ComponentType } from 'react'

// 应用组件映射表
// 组件必须是默认导出（export default）
const appComponents: Record<string, () => Promise<{ default: ComponentType<any> }>> = {
  excel: () => import('./excel/ExcelAnalyzer'),
  // 在此添加新应用的组件：
  // myapp: () => import('./myapp/MyAppComponent'),
}

/**
 * 获取应用的组件（懒加载）
 * 
 * @param appId 应用ID
 * @returns 应用组件或 null
 */
export function getAppComponent(appId: string): ComponentType<any> | null {
  const loader = appComponents[appId]
  if (!loader) {
    return null
  }
  
  // 使用 lazy 加载组件
  return lazy(loader) as ComponentType<any>
}

/**
 * 检查应用是否有前端组件
 * 
 * @param appId 应用ID
 * @returns 是否有组件
 */
export function hasAppComponent(appId: string): boolean {
  return appId in appComponents
}

/**
 * 注册应用组件
 * 
 * @param appId 应用ID
 * @param componentLoader 组件加载器函数，返回 Promise<{ default: ComponentType }>
 * 
 * @example
 * ```typescript
 * registerAppComponent('myapp', () => import('./myapp/MyAppComponent'))
 * ```
 */
export function registerAppComponent(
  appId: string,
  componentLoader: () => Promise<{ default: ComponentType<any> }>
): void {
  appComponents[appId] = componentLoader
}

/**
 * 获取所有已注册的应用ID列表
 * 
 * @returns 应用ID列表
 */
export function getRegisteredAppIds(): string[] {
  return Object.keys(appComponents)
}

