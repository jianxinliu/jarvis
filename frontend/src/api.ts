import axios from 'axios'
import type { DailySummary, ReminderLog, Task, TaskCreate } from './types'

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

  update: async (id: number, task: Partial<Task>): Promise<Task> => {
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

