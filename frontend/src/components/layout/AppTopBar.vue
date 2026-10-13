<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import NotificationPanel from '@/components/NotificationPanel.vue'

// The design's header: wordmark, a few top-level sections, user on the right.
// Sections with several pages get a second row of tabs underneath.
type Item = { to: string; label: string }
type Section = { key: string; label: string; items: Item[]; show?: () => boolean }

const route = useRoute()
const auth = useAuthStore()
const menuOpen = ref(false)

// Computed so the Compliance and Admin entries follow the user once it loads
const sections = computed<Section[]>(() => [
  { key: 'home', label: 'Home', items: [{ to: '/home', label: 'Home' }] },
  {
    key: 'learning', label: 'Learning', items: [
      { to: '/paths', label: 'My paths' },
      { to: '/browse', label: 'Browse' },
      { to: '/saved', label: 'Saved' },
      { to: '/whatsnew', label: "What's new" },
    ],
  },
  {
    key: 'progress', label: 'Progress', items: [
      { to: '/progress', label: 'Progress' },
      { to: '/certs', label: 'Certificates' },
      { to: '/stats', label: 'My stats' },
      { to: '/leaderboard', label: 'Leaderboard' },
    ],
  },
  {
    key: 'team', label: 'Team', items: [
      { to: '/team', label: 'Team' },
      { to: '/activity', label: 'Activity' },
      ...((auth.user?.is_admin || auth.user?.is_manager) ? [{ to: '/compliance', label: 'Compliance' }] : []),
    ],
  },
  {
    key: 'admin', label: 'Admin', show: () => !!auth.user?.is_admin, items: [
      { to: '/users', label: 'Users' },
      { to: '/content', label: 'Content' },
      { to: '/analytics', label: 'Analytics' },
      { to: '/integrations', label: 'Integrations' },
    ],
  },
])

const visibleSections = computed(() => sections.value.filter(s => !s.show || s.show()))

// Which section owns the current page (module, quiz and certificate pages
// belong to the section the learner came from conceptually)
const PREFIX_SECTION: Record<string, string> = {
  modules: 'learning', quiz: 'learning', paths: 'learning', certs: 'progress', settings: '',
}
const activeSection = computed(() => {
  const first = route.path.split('/')[1] ?? ''
  if (first in PREFIX_SECTION) return PREFIX_SECTION[first]
  return visibleSections.value.find(s => s.items.some(i => i.to === '/' + first))?.key ?? ''
})
const subItems = computed(() => {
  const s = visibleSections.value.find(x => x.key === activeSection.value)
  return s && s.items.length > 1 ? s.items : []
})
const isActiveItem = (to: string) =>
  to === '/paths' ? route.path.startsWith('/paths') : to === '/certs' ? route.path.startsWith('/certs') : route.path === to

watch(() => route.path, () => { menuOpen.value = false })
</script>

<template>
  <header class="topbar">
    <div class="topbar-inner">
      <RouterLink to="/home" class="brand" aria-label="Sedna Learning Hub home">
        <span class="brand-name">Sedna</span>
        <span class="brand-sub">LEARNING HUB</span>
      </RouterLink>

      <nav class="sections" aria-label="Main">
        <RouterLink
          v-for="s in visibleSections" :key="s.key" :to="s.items[0].to"
          class="section-link" :class="{ active: activeSection === s.key }"
          :aria-current="activeSection === s.key ? 'page' : undefined"
        >{{ s.label }}</RouterLink>
      </nav>

      <div class="right">
        <NotificationPanel />
        <RouterLink to="/settings" class="user" :class="{ active: route.path === '/settings' }">
          <span class="user-avatar">{{ auth.user?.initial }}</span>
          <span class="user-name">{{ auth.user?.name }}</span>
        </RouterLink>
        <button class="menu-btn" :aria-expanded="menuOpen" aria-label="Open menu" @click="menuOpen = !menuOpen">
          <i class="ti" :class="menuOpen ? 'ti-x' : 'ti-menu-2'" aria-hidden="true" />
        </button>
      </div>
    </div>

    <nav v-if="subItems.length" class="subnav" aria-label="Section">
      <div class="subnav-inner">
        <RouterLink
          v-for="i in subItems" :key="i.to" :to="i.to"
          class="sub-link" :class="{ active: isActiveItem(i.to) }"
          :aria-current="isActiveItem(i.to) ? 'page' : undefined"
        >{{ i.label }}</RouterLink>
      </div>
    </nav>

    <!-- Small screens: every page in one panel -->
    <div v-if="menuOpen" class="mobile-menu">
      <div v-for="s in visibleSections" :key="s.key" class="mobile-group">
        <div class="eyebrow">{{ s.label }}</div>
        <RouterLink v-for="i in s.items" :key="i.to" :to="i.to" class="mobile-link" :class="{ active: isActiveItem(i.to) }">{{ i.label }}</RouterLink>
      </div>
      <RouterLink to="/settings" class="mobile-link">Settings</RouterLink>
    </div>
  </header>
</template>

<style scoped>
.topbar { background: var(--surface); border-bottom: 1px solid var(--hairline); flex-shrink: 0; position: relative; z-index: 50; }
.topbar-inner {
  max-width: var(--content-max); margin: 0 auto; padding: 0 24px;
  min-height: 72px; display: flex; align-items: center; justify-content: space-between; gap: 16px;
}
.brand { display: flex; align-items: center; gap: 10px; min-height: 44px; color: var(--text-primary); }
.brand-name { font-size: 22px; font-weight: 500; letter-spacing: -0.02em; }
.brand-sub { font-family: var(--font-mono); font-size: 12px; letter-spacing: 0.1em; color: var(--text-muted); }

.sections { display: flex; gap: 24px; font-size: 15px; }
.section-link { color: var(--text-secondary); min-height: 44px; display: inline-flex; align-items: center; }
.section-link:hover { color: var(--text-primary); }
.section-link.active { color: var(--purple); font-weight: 500; }

.right { display: flex; align-items: center; gap: 12px; }
.user { display: flex; align-items: center; gap: 10px; font-size: 14px; color: var(--text-secondary); min-height: 44px; }
.user:hover .user-name, .user.active .user-name { color: var(--text-primary); }
.user-avatar {
  width: 32px; height: 32px; border-radius: 999px; background: var(--purple-bg); color: var(--purple-dark);
  display: inline-flex; align-items: center; justify-content: center; font-weight: 500;
}
.menu-btn { display: none; width: 44px; height: 44px; border-radius: var(--radius-sm); border: 1px solid var(--border); font-size: 20px; color: var(--text-primary); align-items: center; justify-content: center; }

.subnav { border-top: 1px solid var(--hairline); }
.subnav-inner { max-width: var(--content-max); margin: 0 auto; padding: 0 24px; display: flex; gap: 24px; overflow-x: auto; }
.sub-link {
  font-size: 14px; color: var(--text-secondary); min-height: 44px; display: inline-flex; align-items: center;
  border-bottom: 2px solid transparent; white-space: nowrap;
}
.sub-link:hover { color: var(--text-primary); }
.sub-link.active { color: var(--purple); border-bottom-color: var(--purple); font-weight: 500; }

.mobile-menu { display: none; }

@media (max-width: 900px) {
  .sections, .user-name { display: none; }
  .menu-btn { display: inline-flex; }
  .mobile-menu {
    display: flex; flex-direction: column; gap: 16px; padding: 16px 24px 24px;
    border-top: 1px solid var(--hairline); background: var(--surface);
  }
  .mobile-group { display: flex; flex-direction: column; gap: 2px; }
  .mobile-group .eyebrow { margin-bottom: 4px; }
  .mobile-link { min-height: 44px; display: flex; align-items: center; font-size: 15px; color: var(--text-secondary); }
  .mobile-link.active { color: var(--purple); font-weight: 500; }
}
</style>
