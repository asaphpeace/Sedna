import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHistory(),
  scrollBehavior: (to) => (to.hash ? { el: to.hash, top: 16 } : { top: 0 }),
  routes: [
    // Public front door, built from Nassia's Learning Hub design
    { path: '/', component: () => import('@/views/hub/HubHomeView.vue'), meta: { public: true } },
    { path: '/learning', component: () => import('@/views/hub/HubLearningView.vue'), meta: { public: true } },
    { path: '/learning/email', component: () => import('@/views/hub/HubEmailView.vue'), meta: { public: true } },
    { path: '/learning/vms', component: () => import('@/views/hub/HubVmsView.vue'), meta: { public: true } },
    { path: '/login', component: () => import('@/views/LoginView.vue'), meta: { public: true } },
    { path: '/accept-invite', component: () => import('@/views/AcceptInviteView.vue'), meta: { public: true } },
    { path: '/:pathMatch(.*)*', component: () => import('@/views/NotFoundView.vue'), meta: { public: true } },
    {
      path: '/',
      component: () => import('@/components/layout/AppLayout.vue'),
      children: [
        { path: 'home', component: () => import('@/views/HomeView.vue') },
        { path: 'paths', component: () => import('@/views/PathsView.vue') },
        { path: 'paths/:id', component: () => import('@/views/PathDetailView.vue') },
        { path: 'browse', component: () => import('@/views/BrowseView.vue') },
        { path: 'modules/:id', component: () => import('@/views/ModuleView.vue') },
        { path: 'saved', component: () => import('@/views/SavedView.vue') },
        { path: 'whatsnew', component: () => import('@/views/WhatsNewView.vue') },
        { path: 'progress', component: () => import('@/views/ProgressView.vue') },
        { path: 'certs', component: () => import('@/views/CertsView.vue') },
        { path: 'certs/:id', component: () => import('@/views/CertificateView.vue') },
        { path: 'team', component: () => import('@/views/TeamView.vue') },
        { path: 'compliance', component: () => import('@/views/ComplianceView.vue') },
        { path: 'activity', component: () => import('@/views/ActivityView.vue') },
        { path: 'users', component: () => import('@/views/UsersView.vue') },
        { path: 'content', component: () => import('@/views/ContentView.vue') },
        { path: 'settings', component: () => import('@/views/SettingsView.vue') },
        { path: 'quiz', component: () => import('@/views/QuizView.vue') },
        { path: 'leaderboard', component: () => import('@/views/LeaderboardView.vue') },
        { path: 'stats', component: () => import('@/views/LearnerStatsView.vue') },
        { path: 'impact', component: () => import('@/views/ImpactView.vue'), meta: { admin: true } },
        { path: 'analytics', component: () => import('@/views/AnalyticsView.vue'), meta: { admin: true } },
        { path: 'integrations', component: () => import('@/views/IntegrationsView.vue'), meta: { admin: true } },
      ],
    },
  ],
})

router.beforeEach(async (to) => {
  if (to.meta.public) return true
  const auth = useAuthStore()
  const signIn = { path: '/login', query: { redirect: to.fullPath } }
  if (!auth.token) return signIn
  if (!auth.user) {
    try { await auth.fetchMe() } catch { return signIn }
  }
  return true
})

export default router
