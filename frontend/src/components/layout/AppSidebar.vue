<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const auth = useAuthStore()

const customerNav = [
  { to: '/home',     icon: 'ti-home',          label: 'Home' },
  { to: '/paths',    icon: 'ti-map',            label: 'My Paths' },
  { to: '/browse',   icon: 'ti-books',          label: 'Browse' },
  { to: '/saved',    icon: 'ti-bookmark',       label: 'Saved' },
  { to: '/whatsnew', icon: 'ti-sparkles',       label: "What's New" },
]

const progressNav = [
  { to: '/progress',    icon: 'ti-chart-line',     label: 'Progress' },
  { to: '/certs',       icon: 'ti-certificate',    label: 'Certifications' },
  { to: '/stats',       icon: 'ti-trophy',         label: 'My Stats' },
  { to: '/leaderboard', icon: 'ti-podium',         label: 'Leaderboard' },
]

const teamNav = [
  { to: '/team',     icon: 'ti-users',          label: 'Team' },
  { to: '/activity', icon: 'ti-activity',       label: 'Activity' },
]

const complianceNav = [
  { to: '/compliance', icon: 'ti-clipboard-check', label: 'Compliance' },
]

const adminNav = [
  { to: '/users',        icon: 'ti-user-cog',     label: 'Users' },
  { to: '/content',      icon: 'ti-layout-grid',  label: 'Content' },
  { to: '/analytics',    icon: 'ti-chart-bar',    label: 'Analytics' },
  { to: '/integrations', icon: 'ti-plug',         label: 'Integrations' },
]

const active = (to: string) =>
  to === '/paths' ? route.path.startsWith('/paths') : route.path === to
</script>

<template>
  <aside class="sidebar">
    <!-- Logo -->
    <div class="logo">
      <div class="logo-icon">
        <svg width="20" height="20" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
          <defs>
            <mask id="sm">
              <rect width="100" height="100" fill="black"/>
              <rect x="18" y="15" width="46" height="46" rx="7" fill="white"/>
              <rect x="36" y="39" width="46" height="46" rx="7" fill="white"/>
              <rect x="36" y="39" width="14" height="14" fill="black"/>
              <rect x="50" y="53" width="14" height="14" fill="black"/>
            </mask>
          </defs>
          <rect width="100" height="100" fill="#fff" mask="url(#sm)"/>
        </svg>
      </div>
      <div>
        <div class="logo-name">Sedna</div>
        <div class="logo-sub">ACADEMY</div>
      </div>
    </div>

    <!-- Nav -->
    <nav class="nav">
      <NavItem v-for="item in customerNav" :key="item.to" v-bind="item" :active="active(item.to)" />

      <div class="nav-section">Progress</div>
      <NavItem v-for="item in progressNav" :key="item.to" v-bind="item" :active="active(item.to)" />

      <div class="nav-section">Team</div>
      <NavItem v-for="item in teamNav" :key="item.to" v-bind="item" :active="active(item.to)" />
      <template v-if="auth.user?.is_admin || auth.user?.is_manager">
        <NavItem v-for="item in complianceNav" :key="item.to" v-bind="item" :active="active(item.to)" />
      </template>

      <template v-if="auth.user?.is_admin">
        <div class="nav-section">Admin</div>
        <NavItem v-for="item in adminNav" :key="item.to" v-bind="item" :active="active(item.to)" />
      </template>
    </nav>

    <!-- User -->
    <RouterLink to="/settings" class="user-row">
      <div class="avatar" :style="{ background: auth.user?.color, width: '30px', height: '30px', fontSize: '12px' }">
        {{ auth.user?.initial }}
      </div>
      <div class="user-info">
        <div class="user-name">{{ auth.user?.name }}</div>
        <div class="user-role">{{ auth.user?.role ?? 'Member' }}</div>
      </div>
      <i class="ti ti-settings user-settings-icon" />
    </RouterLink>
  </aside>
</template>

<script lang="ts">
// Inline NavItem to avoid extra file
import { defineComponent, h } from 'vue'
import { RouterLink } from 'vue-router'

const NavItem = defineComponent({
  props: { to: String, icon: String, label: String, active: Boolean },
  setup(props) {
    return () => h(RouterLink, { to: props.to!, class: ['nav-item', props.active && 'nav-item--active'] }, () => [
      h('i', { class: [props.icon, 'ti'] }),
      h('span', props.label),
      props.active ? h('div', { class: 'nav-bar' }) : null,
    ])
  },
})
export default { components: { NavItem } }
</script>

<style scoped>
.sidebar {
  width: var(--sidebar-w);
  height: 100vh;
  background: var(--surface);
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  position: sticky;
  top: 0;
}
.logo {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 18px 16px 14px;
  border-bottom: 1px solid var(--border);
}
.logo-icon {
  width: 34px; height: 34px;
  background: linear-gradient(135deg, #8255F2, #6E2BF0, #5A1FD6);
  border-radius: 9px;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
}
.logo-name { font-size: 15px; font-weight: 800; letter-spacing: -0.3px; color: var(--text-primary); line-height: 1; }
.logo-sub { font-size: 8px; font-weight: 700; letter-spacing: 2px; text-transform: uppercase; color: var(--text-muted); margin-top: 2px; }
.nav { flex: 1; overflow-y: auto; padding: 10px 8px; display: flex; flex-direction: column; gap: 1px; }
.nav-section { font-size: 10.5px; font-weight: 700; letter-spacing: 0.8px; text-transform: uppercase; color: var(--text-muted); padding: 10px 8px 4px; }

:deep(.nav-item) {
  display: flex; align-items: center; gap: 9px;
  padding: 7px 10px; border-radius: 8px;
  font-size: 13px; font-weight: 500; color: var(--text-secondary);
  position: relative; transition: background 0.1s;
  text-decoration: none;
}
:deep(.nav-item:hover) { background: var(--purple-subtle); color: var(--text-primary); }
:deep(.nav-item--active) { background: var(--purple-bg); color: var(--purple); font-weight: 600; }
:deep(.nav-bar) {
  position: absolute; left: 0; top: 50%; transform: translateY(-50%);
  width: 3px; height: 18px; background: var(--purple); border-radius: 0 2px 2px 0;
}

.user-row {
  display: flex; align-items: center; gap: 9px;
  padding: 12px 14px; border-top: 1px solid var(--border);
  cursor: pointer; text-decoration: none; transition: background 0.1s;
}
.user-row:hover { background: var(--purple-subtle); }
.user-info { flex: 1; overflow: hidden; }
.user-name { font-size: 12.5px; font-weight: 600; color: var(--text-primary); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.user-role { font-size: 11px; color: var(--text-muted); }
.user-settings-icon { font-size: 15px; color: var(--text-muted); }
</style>
