<script setup lang="ts">
// The demo stack (port 5176) runs on fictional data; say so on every page
const isDemo = import.meta.env.VITE_DEMO === '1'
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

// The header from Nassia's Hub screens. "My cohorts" waits for Phase 5.
const route = useRoute()
const auth = useAuthStore()
const onLearning = () => route.path.startsWith('/learning')
const onKb = () => route.path === '/knowledge-base'
const onHelp = () => route.path === '/help-center'
</script>

<template>
  <header class="hub-header">
    <div class="hub-header-inner">
      <RouterLink to="/" class="brand">
        <img src="/sedna-logo.png" alt="" width="32" height="32" class="brand-mark" />
        <span class="brand-name">Sedna</span>
        <span class="brand-sub">LEARNING HUB</span>
        <span v-if="isDemo" class="demo-tag" title="Fictional companies and learners for demonstrations">DEMO DATA</span>
      </RouterLink>
      <nav aria-label="Hub" class="nav">
        <RouterLink to="/knowledge-base" class="nav-link" :class="{ current: onKb() }" :aria-current="onKb() ? 'page' : undefined">Knowledge Base</RouterLink>
        <RouterLink to="/help-center" class="nav-link" :class="{ current: onHelp() }" :aria-current="onHelp() ? 'page' : undefined">Help Center</RouterLink>
        <RouterLink to="/learning" class="nav-link" :class="{ current: onLearning() }" :aria-current="onLearning() ? 'page' : undefined">Learning</RouterLink>
      </nav>
      <RouterLink v-if="auth.user" to="/home" class="user" title="Go to my learning">
        <span class="avatar-dot">{{ auth.user.initial }}</span>
        <span>{{ auth.user.name }}</span>
      </RouterLink>
      <!-- While a saved session is still loading, show neither (no "Sign in" flash) -->
      <RouterLink v-else-if="!auth.token" :to="{ path: '/login', query: { redirect: route.fullPath } }" class="sign-in">Sign in</RouterLink>
      <span v-else class="user-pending" aria-hidden="true" />
    </div>
  </header>
</template>

<style scoped>
.hub-header { background: #FFFFFF; border-bottom: 1px solid rgba(0,0,0,0.08); padding: 0 24px; }
.hub-header-inner {
  max-width: 1180px; margin: 0 auto; display: flex; flex-wrap: wrap; align-items: center;
  justify-content: space-between; gap: 16px; min-height: 72px;
}
.brand { text-decoration: none; color: #0B0B0F; display: flex; align-items: center; gap: 10px; min-height: 44px; }
.brand-name { font-size: 22px; font-weight: 500; letter-spacing: -0.02em; }
.brand-sub { font-family: var(--font-mono); font-size: 12px; letter-spacing: 0.1em; color: #6B6C75; }
.nav { display: flex; flex-wrap: wrap; gap: 24px; font-size: 15px; }
.nav-link { text-decoration: none; color: #3A3B42; min-height: 44px; display: inline-flex; align-items: center; }
.nav-link:hover { color: #0B0B0F; }
.nav-link.current { color: #7A3FE5; font-weight: 500; }
.user { display: flex; align-items: center; gap: 10px; font-size: 14px; color: #3A3B42; text-decoration: none; min-height: 44px; }
.user:hover { color: #0B0B0F; }
.avatar-dot {
  width: 32px; height: 32px; border-radius: 999px; background: #ECDEFE; color: #4B1FA8;
  display: inline-flex; align-items: center; justify-content: center; font-weight: 500;
}
.sign-in {
  background: #7A3FE5; color: #FFFFFF; border-radius: 8px; padding: 0 18px; min-height: 44px;
  display: inline-flex; align-items: center; font-size: 15px; font-weight: 500; text-decoration: none;
}
.sign-in:hover { background: #4B1FA8; }
.user-pending { width: 120px; min-height: 44px; }
@media (max-width: 640px) { .nav { order: 3; width: 100%; gap: 18px; } }

/* The Sedna mark: used exactly as supplied — fixed square, never stretched or recoloured */
.brand-mark { width: 32px; height: 32px; flex: none; object-fit: contain; display: block; }
.demo-tag { font-family: var(--font-mono); font-size: 11px; letter-spacing: 0.08em; background: #FBEDC8; color: #633806; padding: 3px 8px; border-radius: 4px; }
@media (max-width: 480px) { .brand:has(.demo-tag) .brand-sub { display: none; } }
</style>
