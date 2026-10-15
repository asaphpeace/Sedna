<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { authApi, settingsApi } from '@/api'
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

// ── Password ──────────────────────────────────────────
const pw = ref({ current: '', next: '', confirm: '' })
const pwBusy = ref(false)
const pwError = ref('')
const pwDone = ref(false)

async function changePassword() {
  pwError.value = ''
  pwDone.value = false
  if (pw.value.next.length < 8) { pwError.value = 'Your new password needs at least 8 characters.'; return }
  if (pw.value.next !== pw.value.confirm) { pwError.value = "The new passwords don't match."; return }
  pwBusy.value = true
  try {
    await authApi.changePassword(pw.value.current, pw.value.next)
    pw.value = { current: '', next: '', confirm: '' }
    pwDone.value = true
  } catch (e: any) {
    const d = e?.response?.data?.detail
    pwError.value = typeof d === 'string' ? d
      : e?.response?.status === 429 ? 'Too many attempts. Wait a minute and try again.'
      : "Your password couldn't be changed. Try again."
  } finally {
    pwBusy.value = false
  }
}

async function toggle(key: string) {
  settings.value[key] = !settings.value[key]
  await settingsApi.updateNotifications({ [key]: settings.value[key] })
}

const labels: Record<string, { title: string; desc: string }> = {
  weekly_digest:    { title: 'Weekly digest', desc: 'A summary of your team\'s learning activity every Monday.' },
  new_modules:      { title: 'New modules', desc: 'Notifications when new content is added to your paths.' },
  cert_reminders:   { title: 'Certificate reminders', desc: 'Reminders when you\'re close to completing a tier.' },
  product_releases: { title: 'Product releases', desc: 'Release notes for Sedna VMS and Sedna Email.' },
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

    <!-- Password section -->
    <section class="section" aria-labelledby="pw-h">
      <h2 id="pw-h" class="section-title">Password</h2>
      <form class="pw-form" @submit.prevent="changePassword">
        <input type="email" :value="auth.user?.email" autocomplete="username" hidden readonly />
        <label class="pw-field">
          <span>Current password</span>
          <input v-model="pw.current" type="password" class="input" autocomplete="current-password" required />
        </label>
        <label class="pw-field">
          <span>New password <span class="pw-hint">at least 8 characters</span></span>
          <input v-model="pw.next" type="password" class="input" autocomplete="new-password" minlength="8" required />
        </label>
        <label class="pw-field">
          <span>Confirm new password</span>
          <input v-model="pw.confirm" type="password" class="input" autocomplete="new-password" required />
        </label>
        <p v-if="pwError" class="pw-error" role="alert">{{ pwError }}</p>
        <p v-if="pwDone" class="pw-done" role="status">Password changed. Use it next time you sign in.</p>
        <div>
          <button type="submit" class="btn btn-primary" :disabled="pwBusy || !pw.current || !pw.next || !pw.confirm">
            {{ pwBusy ? 'Changing…' : 'Change password' }}
          </button>
        </div>
      </form>
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
.page { padding: 40px 24px 72px; max-width: 600px; margin: 0 auto; }
.page-title { font-size: 40px; line-height: 1.12; font-weight: 500; letter-spacing: -0.012em; margin-bottom: 28px; }
.section { margin-bottom: 32px; }
.section-title { font-size: 20px; font-weight: 500; letter-spacing: -0.012em; margin-bottom: 14px; }
.profile-row { display: flex; align-items: center; gap: 14px; padding: 18px; background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); }
.profile-name { font-size: 15px; font-weight: 500; }
.profile-email { font-size: 14px; color: var(--text-muted); margin-top: 2px; }
.profile-role { font-size: 13px; color: var(--purple); font-weight: 500; margin-top: 4px; }
.notif-list { display: flex; flex-direction: column; gap: 0; background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); overflow: hidden; }
.notif-row { display: flex; align-items: center; justify-content: space-between; gap: 16px; padding: 14px 18px; border-bottom: 1px solid var(--border); }
.notif-row:last-child { border-bottom: none; }
.notif-info { flex: 1; }
.notif-title { font-size: 15px; font-weight: 500; }
.notif-desc { font-size: 13px; color: var(--text-muted); margin-top: 2px; }
.toggle { width: 38px; height: 22px; border-radius: 11px; background: var(--border-mid); cursor: pointer; position: relative; transition: background 0.2s; flex-shrink: 0; }
.toggle--on { background: var(--purple); }
.toggle-knob { position: absolute; top: 3px; left: 3px; width: 16px; height: 16px; border-radius: 50%; background: #fff; transition: left 0.2s; box-shadow: 0 1px 3px rgba(0,0,0,0.2); }
.toggle--on .toggle-knob { left: 19px; }
.pw-form { display: flex; flex-direction: column; gap: 14px; padding: 18px; background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); }
.pw-field { display: flex; flex-direction: column; gap: 6px; font-size: 14px; color: var(--text-secondary); }
.pw-hint { color: var(--text-muted); font-size: 13px; margin-left: 4px; }
.pw-error { font-size: 14px; color: #B0322B; margin: 0; }
.pw-done { font-size: 14px; color: #1F8A5B; margin: 0; }
.logout-btn { color: #B0322B; border-color: #FBE0DE; }
.logout-btn:hover { background: #FBE0DE; border-color: #EF9A9A; }
</style>
