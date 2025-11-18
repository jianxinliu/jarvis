import axios from 'axios'
import type {
  DailySummary,
  ReminderLog,
  Task,
  TaskCreate,
  TodoItem,
  TodoItemCreate,
  TodoTag,
  TodoTagCreate,
  TodoPriority,
  TodoPriorityCreate,
  TodoQuadrant,
} from './types'

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
})

export const taskApi = {
  getAll: async (activeOnly = false): Promise<Task[]> => {
    const response = await api.get('/tasks', { params: { active_only: activeOnly } })
    return response.data
  },

  getToday: async (): Promise<Task[]> => {
    const response = await api.get('/tasks/today')
    return response.data
  },

  getById: async (id: number): Promise<Task> => {
    const response = await api.get(`/tasks/${id}`)
    return response.data
  },

  create: async (task: TaskCreate): Promise<Task> => {
    const response = await api.post('/tasks', task)
    return response.data
  },

  update: async (id: number, task: Partial<TaskCreate & { is_active?: boolean }>): Promise<Task> => {
    const response = await api.put(`/tasks/${id}`, task)
    return response.data
  },

  delete: async (id: number): Promise<void> => {
    await api.delete(`/tasks/${id}`)
  },
}

export const reminderApi = {
  getUnread: async (): Promise<ReminderLog[]> => {
    const response = await api.get('/reminders')
    return response.data
  },

  markAsRead: async (id: number): Promise<void> => {
    await api.post(`/reminders/${id}/read`)
  },

  getDailySummary: async (): Promise<DailySummary> => {
    const response = await api.get('/reminders/daily-summary')
    return response.data
  },
}

export const todoApi = {
  // TODO 项
  getItems: async (quadrant?: TodoQuadrant, includeArchived = false, includeCompleted = true): Promise<TodoItem[]> => {
    const response = await api.get('/todo/items', {
      params: { quadrant, include_archived: includeArchived, include_completed: includeCompleted },
    })
    return response.data
  },

  getItem: async (id: number): Promise<TodoItem> => {
    const response = await api.get(`/todo/items/${id}`)
    return response.data
  },

  create: async (item: TodoItemCreate): Promise<TodoItem> => {
    const response = await api.post('/todo/items', item)
    return response.data
  },

  update: async (id: number, item: Partial<TodoItemCreate & { is_completed?: boolean }>): Promise<TodoItem> => {
    const response = await api.put(`/todo/items/${id}`, item)
    return response.data
  },

  delete: async (id: number): Promise<void> => {
    await api.delete(`/todo/items/${id}`)
  },

  // 标签
  getTags: async (): Promise<TodoTag[]> => {
    const response = await api.get('/todo/tags')
    return response.data
  },

  createTag: async (tag: TodoTagCreate): Promise<TodoTag> => {
    const response = await api.post('/todo/tags', tag)
    return response.data
  },

  updateTag: async (id: number, tag: Partial<TodoTagCreate>): Promise<TodoTag> => {
    const response = await api.put(`/todo/tags/${id}`, tag)
    return response.data
  },

  deleteTag: async (id: number): Promise<void> => {
    await api.delete(`/todo/tags/${id}`)
  },

  // 优先级
  getPriorities: async (): Promise<TodoPriority[]> => {
    const response = await api.get('/todo/priorities')
    return response.data
  },

  createPriority: async (priority: TodoPriorityCreate): Promise<TodoPriority> => {
    const response = await api.post('/todo/priorities', priority)
    return response.data
  },

  updatePriority: async (id: number, priority: Partial<TodoPriorityCreate>): Promise<TodoPriority> => {
    const response = await api.put(`/todo/priorities/${id}`, priority)
    return response.data
  },

  deletePriority: async (id: number): Promise<void> => {
    await api.delete(`/todo/priorities/${id}`)
  },
}

