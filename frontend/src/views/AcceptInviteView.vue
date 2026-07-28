<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { authApi } from '@/api'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const token = String(route.query.token ?? '')
const invite = ref<{ name: string; email: string; org_name: string } | null>(null)
const loadError = ref('')
const loadingInvite = ref(true)

const password = ref('')
const confirmPassword = ref('')
const submitError = ref('')
const submitting = ref(false)

onMounted(async () => {
  if (!token) {
    loadError.value = 'This invite link is missing its token.'
    loadingInvite.value = false
    return
  }
  try {
    const { data } = await authApi.getInvite(token)
    invite.value = data
  } catch (err: any) {
    loadError.value = err?.response?.data?.detail || 'This invite link is invalid or has expired.'
  } finally {
    loadingInvite.value = false
  }
})

async function submit() {
  submitError.value = ''
  if (password.value.length < 8) {
    submitError.value = 'Password must be at least 8 characters.'
    return
  }
  if (password.value !== confirmPassword.value) {
    submitError.value = 'Passwords do not match.'
    return
  }
  submitting.value = true
  try {
    await auth.acceptInvite(token, password.value)
    router.push('/home')
  } catch (err: any) {
    submitError.value = err?.response?.data?.detail || 'Could not set your password. Try again.'
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="login-page">
    <div class="login-card">
      <div class="login-logo">
        <div class="login-logo-icon">
          <svg width="28" height="28" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Sedna Academy logo">
            <defs>
              <mask id="am">
                <rect width="100" height="100" fill="black"/>
                <rect x="18" y="15" width="46" height="46" rx="7" fill="white"/>
                <rect x="36" y="39" width="46" height="46" rx="7" fill="white"/>
                <rect x="36" y="39" width="14" height="14" fill="black"/>
                <rect x="50" y="53" width="14" height="14" fill="black"/>
              </mask>
            </defs>
            <rect width="100" height="100" fill="#fff" mask="url(#am)"/>
          </svg>
        </div>
        <div>
          <div class="login-brand">Sedna</div>
          <div class="login-sub">ACADEMY</div>
        </div>
      </div>

      <div v-if="loadingInvite" class="loading-msg">Checking your invite…</div>

      <template v-else-if="loadError">
        <h1 class="login-heading">Invite not valid</h1>
        <p class="login-caption">{{ loadError }}</p>
        <RouterLink to="/login" class="btn btn-primary login-btn" style="text-align:center; display:block;">
          Go to sign in
        </RouterLink>
      </template>

      <template v-else>
        <h1 class="login-heading">Welcome, {{ invite!.name.split(' ')[0] }}</h1>
        <p class="login-caption">Set a password to join {{ invite!.org_name }} on Sedna Academy.</p>

        <form @submit.prevent="submit" class="login-form" novalidate>
          <div class="field">
            <label class="label">Email</label>
            <input class="input" :value="invite!.email" disabled />
          </div>
          <div class="field">
            <label for="invite-password" class="label">Password</label>
            <input
              id="invite-password" v-model="password" type="password" class="input"
              placeholder="At least 8 characters" required autocomplete="new-password"
            />
          </div>
          <div class="field">
            <label for="invite-confirm" class="label">Confirm password</label>
            <input
              id="invite-confirm" v-model="confirmPassword" type="password" class="input"
              placeholder="••••••••" required autocomplete="new-password"
            />
          </div>

          <div v-if="submitError" class="error-msg">{{ submitError }}</div>

          <button type="submit" class="btn btn-primary login-btn" :disabled="submitting">
            <i v-if="submitting" class="ti ti-loader-2" style="animation: spin 0.8s linear infinite" />
            {{ submitting ? 'Setting up your account…' : 'Set password & join' }}
          </button>
        </form>
      </template>
    </div>
  </div>
</template>

<style scoped>
.login-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #6E2BF0 0%, #4A1AB0 100%);
  display: flex; align-items: center; justify-content: center;
  padding: 24px;
}
.login-card {
  background: #fff;
  border-radius: 16px;
  padding: 40px 36px;
  width: 100%;
  max-width: 400px;
  box-shadow: 0 24px 64px rgba(26,22,34,0.25);
}
.login-logo { display: flex; align-items: center; gap: 12px; margin-bottom: 28px; }
.login-logo-icon {
  width: 46px; height: 46px;
  background: linear-gradient(135deg, #8255F2, #6E2BF0, #5A1FD6);
  border-radius: 12px;
  display: flex; align-items: center; justify-content: center;
}
.login-brand { font-size: 20px; font-weight: 800; letter-spacing: -0.3px; }
.login-sub { font-size: 9px; font-weight: 700; letter-spacing: 2.5px; text-transform: uppercase; color: var(--text-muted); margin-top: 2px; }
.login-heading { font-size: 22px; font-weight: 800; letter-spacing: -0.4px; }
.login-caption { font-size: 13px; color: var(--text-muted); margin-top: 4px; margin-bottom: 28px; }
.loading-msg { font-size: 13px; color: var(--text-muted); }
.login-form { display: flex; flex-direction: column; gap: 16px; }
.field { display: flex; flex-direction: column; gap: 6px; }
.label { font-size: 13px; font-weight: 600; color: var(--text-secondary); }
.input {
  padding: 9px 12px;
  border: 1px solid var(--border);
  border-radius: 8px;
  font-size: 14px;
  outline: none;
  transition: border-color 0.15s;
}
.input:focus { border-color: var(--purple); box-shadow: 0 0 0 3px rgba(110,43,240,0.1); }
.input:disabled { background: var(--bg); color: var(--text-muted); }
.error-msg { font-size: 13px; color: #D32F2F; background: #FFEBEE; padding: 8px 12px; border-radius: 7px; }
.login-btn { width: 100%; justify-content: center; padding: 11px; font-size: 14px; margin-top: 4px; }
@keyframes spin { to { transform: rotate(360deg); } }
</style>
