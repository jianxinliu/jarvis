export interface Task {
  id: number
  title: string
  content?: string
  priority: number
  is_active: boolean
  reminder_interval_hours?: number
  end_time?: string
  next_reminder_time?: string
  created_at: string
  updated_at: string
}

export interface TaskCreate {
  title: string
  content?: string
  priority: number
  reminder_interval_hours?: number
  end_time?: string
}

export interface ReminderLog {
  id: number
  task_id: number
  reminder_type: string
  reminder_time: string
  is_read: boolean
  content?: string
}

export interface DailySummary {
  date: string
  tasks: Task[]
  total_count: number
}

export interface WebSocketMessage {
  type: string
  data: any
  timestamp: string
}

export interface RuleCondition {
  field: string
  operator: string
  value: number
  priority?: number
}

export interface RuleGroup {
  conditions: RuleCondition[]
  logic: 'and' | 'or'
  priority?: number
}

export interface FilterRule {
  groups: RuleGroup[]
  logic: 'and' | 'or'
}

export interface LinkData {
  link: string
  ctr?: number
  revenue?: number
  data: Record<string, any>
  matched_groups?: number[]
  matched_rules?: string[]
}

export interface ExcelAnalysisResponse {
  total_rows: number
  matched_count: number
  links: LinkData[]
  columns: string[]
  rule_fields?: string[]
}

export interface App {
  id: number
  app_id: string
  name: string
  description?: string
  icon?: string
  version: string
  author?: string
  route_prefix: string
  frontend_path?: string
  config?: Record<string, any>
  is_enabled: boolean
  is_builtin: boolean
  created_at: string
  updated_at: string
}

