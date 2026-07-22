import client from './client'

// ── Auth ──────────────────────────────────────────────
export const authApi = {
  login: (email: string, password: string) =>
    client.post<{ access_token: string }>('/auth/login', { email, password }),
  me: () => client.get('/auth/me'),
}

// ── Paths ─────────────────────────────────────────────
export const pathsApi = {
  list: () => client.get('/paths'),
  get: (id: number) => client.get(`/paths/${id}`),
}

// ── Admin ──────────────────────────────────────────────
export const adminApi = {
  // paths
  listPaths: () => client.get('/admin/paths'),
  createPath: (body: any) => client.post('/admin/paths', body),
  updatePath: (id: number, body: any) => client.patch(`/admin/paths/${id}`, body),
  deletePath: (id: number) => client.delete(`/admin/paths/${id}`),
  // tiers
  listTiers: (pathId: number) => client.get(`/admin/paths/${pathId}/tiers`),
  createTier: (pathId: number, body: any) => client.post(`/admin/paths/${pathId}/tiers`, body),
  updateTier: (tierId: number, body: any) => client.patch(`/admin/tiers/${tierId}`, body),
  deleteTier: (tierId: number) => client.delete(`/admin/tiers/${tierId}`),
  // modules
  listModules: (tierId: number) => client.get(`/admin/tiers/${tierId}/modules`),
  createModule: (tierId: number, body: any) => client.post(`/admin/tiers/${tierId}/modules`, body),
  updateModule: (moduleId: number, body: any) => client.patch(`/admin/modules/${moduleId}`, body),
  deleteModule: (moduleId: number) => client.delete(`/admin/modules/${moduleId}`),
  // quiz
  getModuleQuiz: (moduleId: number) => client.get(`/admin/modules/${moduleId}/quiz`),
  createQuizQuestion: (moduleId: number, body: any) => client.post(`/admin/modules/${moduleId}/quiz/questions`, body),
  updateQuizQuestion: (questionId: number, body: any) => client.patch(`/admin/quiz-questions/${questionId}`, body),
  deleteQuizQuestion: (questionId: number) => client.delete(`/admin/quiz-questions/${questionId}`),
  // releases
  listReleases: () => client.get('/admin/releases'),
  createRelease: (body: any) => client.post('/admin/releases', body),
  updateRelease: (id: number, body: any) => client.patch(`/admin/releases/${id}`, body),
  deleteRelease: (id: number) => client.delete(`/admin/releases/${id}`),
}

// ── Modules ───────────────────────────────────────────
export const modulesApi = {
  browse: (params?: { product?: string; module_type?: string }) =>
    client.get('/modules', { params }),
  get: (id: number) => client.get(`/modules/${id}`),
  byTier: (tierId: number) => client.get('/modules', { params: { tier_id: tierId } }),
}

// ── Progress ──────────────────────────────────────────
export const progressApi = {
  myProgress: () => client.get('/progress/me'),
  myPathProgress: () => client.get('/progress/me/paths'),
  start: (moduleId: number) => client.post(`/progress/modules/${moduleId}/start`),
  complete: (moduleId: number) => client.post(`/progress/modules/${moduleId}/complete`),
}

// ── Certificates ──────────────────────────────────────
export const certsApi = {
  mine: () => client.get('/certificates/me'),
}

// ── Saved ─────────────────────────────────────────────
export const savedApi = {
  list: () => client.get('/saved'),
  save: (moduleId: number) => client.post(`/saved/${moduleId}`),
  unsave: (moduleId: number) => client.delete(`/saved/${moduleId}`),
}

// ── Activity ──────────────────────────────────────────
export const activityApi = {
  list: (limit = 50) => client.get('/activity', { params: { limit } }),
}

// ── Team ──────────────────────────────────────────────
export const teamApi = {
  list: () => client.get('/team'),
  invite: (data: { email: string; name: string; role?: string }) =>
    client.post('/team/invite', data),
  update: (userId: number, data: object) => client.patch(`/team/${userId}`, data),
}

// ── Releases ──────────────────────────────────────────
export const releasesApi = {
  list: (product?: string) => client.get('/releases', { params: product ? { product } : {} }),
}

// ── Settings ──────────────────────────────────────────
export const settingsApi = {
  getNotifications: () => client.get('/settings/notifications'),
  updateNotifications: (data: object) => client.patch('/settings/notifications', data),
}

// ── Quizzes ───────────────────────────────────────────
export const quizzesApi = {
  forModule: (moduleId: number) => client.get(`/quizzes/module/${moduleId}`),
  forTier: (tierId: number) => client.get(`/quizzes/tier/${tierId}`),
  submit: (data: { module_id?: number; tier_id?: number; answers: { question_id: number; option_id: number }[] }) =>
    client.post('/quizzes/attempt', data),
  attempts: (params?: { module_id?: number; tier_id?: number }) =>
    client.get('/quizzes/attempts', { params }),
}

// ── Gamification ──────────────────────────────────────
export const gamificationApi = {
  me: () => client.get('/gamification/me'),
  leaderboard: (limit = 20) => client.get('/gamification/leaderboard', { params: { limit } }),
  badges: () => client.get('/gamification/badges'),
}

// ── Notifications ─────────────────────────────────────
export const notificationsApi = {
  list: (unreadOnly = false) => client.get('/notifications', { params: unreadOnly ? { unread_only: true } : {} }),
  markRead: (id: number) => client.patch(`/notifications/${id}/read`),
  markAllRead: () => client.post('/notifications/read-all'),
}

// ── Analytics ─────────────────────────────────────────
export const analyticsApi = {
  me: () => client.get('/analytics/me'),
  org: () => client.get('/analytics/org'),
}

// ── Social ────────────────────────────────────────────
export const socialApi = {
  getComments: (moduleId: number) => client.get(`/social/modules/${moduleId}/comments`),
  createComment: (moduleId: number, body: string, parent_id?: number) =>
    client.post(`/social/modules/${moduleId}/comments`, { body, parent_id }),
  deleteComment: (commentId: number) => client.delete(`/social/comments/${commentId}`),
  toggleLike: (commentId: number) => client.post(`/social/comments/${commentId}/like`),
}

// ── Compliance ────────────────────────────────────────
export const complianceApi = {
  me: () => client.get('/compliance/me'),
  orgExpiring: (days = 30) => client.get('/compliance/org/expiring', { params: { days } }),
}

// ── Webhooks ──────────────────────────────────────────
export const webhooksApi = {
  list: () => client.get('/webhooks'),
  create: (data: { url: string; events: string[]; secret?: string }) => client.post('/webhooks', data),
  update: (id: number, data: object) => client.patch(`/webhooks/${id}`, data),
  delete: (id: number) => client.delete(`/webhooks/${id}`),
  events: () => client.get('/webhooks/events'),
}
