export interface SubTask {
  id: number
  task_id: number
  title: string
  reminder_time: string
  is_completed: boolean
  is_notified: boolean
  created_at: string
  updated_at: string
}

export interface Task {
  id: number
  title: string
  content?: string
  priority: number
  is_active: boolean
  is_completed: boolean
  reminder_interval_hours?: number
  end_time?: string
  next_reminder_time?: string
  subtasks?: SubTask[]
  created_at: string
  updated_at: string
}

export interface SubTaskCreate {
  title: string
  reminder_time: string
}

export interface TaskCreate {
  title: string
  content?: string
  priority: number
  reminder_interval_hours?: number
  end_time?: string
  subtasks?: SubTaskCreate[]
}

export interface ReminderLog {
  id: number
  task_id: number
  reminder_type: string
  reminder_time: string
  is_read: boolean
  content?: string
  app_id?: string
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
  is_latest_data_match?: boolean
}

export interface ExcelAnalysisResponse {
  total_rows: number
  matched_count: number
  links: LinkData[]
  columns: string[]
  rule_fields?: string[]
  record_id?: number
  no_yesterday_links?: string[]
  offline_links?: string[]
}

export interface AnalysisRecordSummary {
  id: number
  file_name: string
  total_rows: number
  matched_count: number
  days: number
  created_at: string
}

export interface LinkHistoryItem {
  id: number
  analysis_record_id: number
  link: string
  ctr?: number
  revenue?: number
  data: Record<string, any>
  matched_groups?: number[]
  matched_rules?: string[]
  created_at: string
  file_name: string
}

export interface LinkChangeTrend {
  link: string
  records: LinkHistoryItem[]
  ctr_changes: (number | null)[]
  revenue_changes: (number | null)[]
  first_seen: string
  last_seen: string
  appearance_count: number
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

// TODO 应用相关类型
export type TodoQuadrant = 'reminder' | 'record' | 'urgent' | 'important'

export interface TodoTag {
  id: number
  name: string
  color?: string
  created_at: string
  updated_at: string
}

export interface TodoPriority {
  id: number
  name: string
  level: number
  color?: string
  created_at: string
  updated_at: string
}

export interface TodoSubTask {
  id: number
  todo_item_id: number
  title: string
  content?: string
  reminder_time?: string
  is_completed: boolean
  is_notified: boolean
  created_at: string
  updated_at: string
}

export interface TodoSubTaskCreate {
  title: string
  content?: string
  reminder_time?: string
}

export interface TodoItem {
  id: number
  title: string
  content?: string
  quadrant: TodoQuadrant
  priority_id?: number
  priority?: TodoPriority
  due_time?: string
  reminder_time?: string
  reminder_interval_hours?: number
  is_completed: boolean
  is_archived: boolean
  tags: TodoTag[]
  subtasks: TodoSubTask[]
  created_at: string
  updated_at: string
}

export interface TodoItemCreate {
  title: string
  content?: string
  quadrant: TodoQuadrant
  priority_id?: number
  due_time?: string
  reminder_time?: string
  reminder_interval_hours?: number
  tag_ids?: number[]
  subtasks?: TodoSubTaskCreate[]
}

export interface TodoTagCreate {
  name: string
  color?: string
}

export interface TodoPriorityCreate {
  name: string
  level: number
  color?: string
}

