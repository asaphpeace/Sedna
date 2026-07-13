<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { settingsApi } from '@/api'
import { useRouter } from 'vue-router'

const auth = useAuthStore()
const router = useRouter()

const settings = ref<Record<string, boolean>>({
  weekly_digest: true,
  new_modules: true,
  cert_reminders: true,
  product_releases: true,
  team_activity: false,
  marketing_emails: false,
})

onMounted(async () => {
  const { data } = await settingsApi.getNotifications()
  settings.value = data
})

async function toggle(key: string) {
  settings.value[key] = !settings.value[key]
  await settingsApi.updateNotifications({ [key]: settings.value[key] })
}

const labels: Record<string, { title: string; desc: string }> = {
  weekly_digest:    { title: 'Weekly digest', desc: 'A summary of your team\'s learning activity every Monday.' },
  new_modules:      { title: 'New modules', desc: 'Notifications when new content is added to your paths.' },
  cert_reminders:   { title: 'Certificate reminders', desc: 'Reminders when you\'re close to completing a tier.' },
  product_releases: { title: 'Product releases', desc: 'Release notes for VMS and Sedna Stream updates.' },
  team_activity:    { title: 'Team activity', desc: 'Real-time notifications when teammates complete modules.' },
  marketing_emails: { title: 'Marketing emails', desc: 'Occasional product news and tips from Sedna.' },
}

function logout() {
  auth.logout()
  router.push('/login')
}
</script>

<template>
  <div class="page">
    <h1 class="page-title">Settings</h1>

    <!-- Profile section -->
    <section class="section">
      <h2 class="section-title">Profile</h2>
      <div class="profile-row">
        <div class="avatar" :style="{ background: auth.user?.color, width: '48px', height: '48px', fontSize: '18px' }">{{ auth.user?.initial }}</div>
        <div>
          <div class="profile-name">{{ auth.user?.name }}</div>
          <div class="profile-email">{{ auth.user?.email }}</div>
          <div class="profile-role">{{ auth.user?.role ?? 'Member' }}</div>
        </div>
      </div>
    </section>

    <!-- Notifications section -->
    <section class="section">
      <h2 class="section-title">Notifications</h2>
      <div class="notif-list">
        <div v-for="(meta, key) in labels" :key="key" class="notif-row">
          <div class="notif-info">
            <div class="notif-title">{{ meta.title }}</div>
            <div class="notif-desc">{{ meta.desc }}</div>
          </div>
          <div class="toggle" :class="{ 'toggle--on': settings[key] }" @click="toggle(key)">
            <div class="toggle-knob" />
          </div>
        </div>
      </div>
    </section>

    <!-- Logout -->
    <section class="section">
      <button class="btn btn-ghost logout-btn" @click="logout">
        <i class="ti ti-logout" /> Sign out
      </button>
    </section>
  </div>
</template>

<style scoped>
.page { padding: 28px 32px; max-width: 600px; margin: 0 auto; }
.page-title { font-size: 22px; font-weight: 800; letter-spacing: -0.4px; margin-bottom: 28px; }
.section { margin-bottom: 32px; }
.section-title { font-size: 14px; font-weight: 700; margin-bottom: 14px; }
.profile-row { display: flex; align-items: center; gap: 14px; padding: 18px; background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); }
.profile-name { font-size: 15px; font-weight: 700; }
.profile-email { font-size: 13px; color: var(--text-muted); margin-top: 2px; }
.profile-role { font-size: 12px; color: var(--purple); font-weight: 600; margin-top: 4px; }
.notif-list { display: flex; flex-direction: column; gap: 0; background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); overflow: hidden; }
.notif-row { display: flex; align-items: center; justify-content: space-between; gap: 16px; padding: 14px 18px; border-bottom: 1px solid var(--border); }
.notif-row:last-child { border-bottom: none; }
.notif-info { flex: 1; }
.notif-title { font-size: 13.5px; font-weight: 600; }
.notif-desc { font-size: 12px; color: var(--text-muted); margin-top: 2px; }
.toggle { width: 38px; height: 22px; border-radius: 11px; background: var(--border-mid); cursor: pointer; position: relative; transition: background 0.2s; flex-shrink: 0; }
.toggle--on { background: var(--purple); }
.toggle-knob { position: absolute; top: 3px; left: 3px; width: 16px; height: 16px; border-radius: 50%; background: #fff; transition: left 0.2s; box-shadow: 0 1px 3px rgba(0,0,0,0.2); }
.toggle--on .toggle-knob { left: 19px; }
.logout-btn { color: #D32F2F; border-color: #FFCDD2; }
.logout-btn:hover { background: #FFEBEE; border-color: #EF9A9A; }
</style>
