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
        <span class="login-brand">Sedna</span>
        <span class="login-sub">LEARNING HUB</span>
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
        <p class="login-caption">Set a password to join {{ invite!.org_name }} on Sedna Learning Hub.</p>

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
  min-height: 100vh; background: var(--bg);
  display: flex; align-items: center; justify-content: center; padding: 24px;
}
.login-card {
  background: var(--surface); border: 1px solid var(--hairline); border-radius: var(--radius);
  box-shadow: var(--shadow-md); padding: 40px; width: 100%; max-width: 440px;
}
.login-logo { display: flex; align-items: baseline; gap: 10px; margin-bottom: 32px; }
.login-brand { font-size: 22px; font-weight: 500; letter-spacing: -0.02em; }
.login-sub { font-family: var(--font-mono); font-size: 12px; letter-spacing: 0.1em; color: var(--text-muted); }
.login-heading { font-size: 32px; line-height: 1.12; font-weight: 500; letter-spacing: -0.012em; }
.login-caption { font-size: 15px; color: var(--text-secondary); margin-top: 8px; margin-bottom: 28px; }
.login-form { display: flex; flex-direction: column; gap: 18px; }
.field { display: flex; flex-direction: column; gap: 6px; }
.label { font-size: 14px; color: var(--text-secondary); }
.error-msg { font-size: 14px; color: var(--coral); background: var(--coral-bg); padding: 10px 14px; border-radius: var(--radius-sm); }
.login-btn { width: 100%; margin-top: 4px; }
@keyframes spin { to { transform: rotate(360deg); } }
.loading-msg { font-size: 15px; color: var(--text-muted); }
.input:disabled { background: var(--bg); color: var(--text-muted); }
</style>
