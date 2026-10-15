<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { authApi } from '@/api'
import { useAuthStore } from '@/stores/auth'

// Opened from the reset email: choose a new password, then go straight in.
const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const token = String(route.query.token ?? '')
const checking = ref(true)
const invalid = ref(false)
const password = ref('')
const confirmPassword = ref('')
const error = ref('')
const saving = ref(false)

onMounted(async () => {
  if (!token) {
    invalid.value = true
  } else {
    try {
      await authApi.checkReset(token)
    } catch {
      invalid.value = true
    }
  }
  checking.value = false
})

async function submit() {
  error.value = ''
  if (password.value.length < 8) {
    error.value = 'Password must be at least 8 characters.'
    return
  }
  if (password.value !== confirmPassword.value) {
    error.value = 'Passwords do not match.'
    return
  }
  saving.value = true
  try {
    await auth.resetPassword(token, password.value)
    router.push('/home')
  } catch (err: any) {
    const d = err?.response?.data?.detail
    error.value = typeof d === 'string' ? d : 'Could not set your password. Try again.'
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <div class="login-page">
    <div class="login-card">
      <RouterLink to="/" class="login-logo" aria-label="Back to the Learning Hub">
        <img src="/sedna-logo.png" alt="" width="32" height="32" class="brand-mark" />
        <span class="login-brand">Sedna</span>
        <span class="login-sub">LEARNING HUB</span>
      </RouterLink>

      <div v-if="checking" class="loading-msg">Checking your link…</div>

      <template v-else-if="invalid">
        <h1 class="login-heading">Link not valid</h1>
        <p class="login-caption">This reset link is invalid, has already been used, or has expired. Links last 1 hour.</p>
        <RouterLink to="/forgot-password" class="btn btn-primary login-btn">Send a new link</RouterLink>
        <RouterLink to="/login" class="back-link">← Back to sign in</RouterLink>
      </template>

      <template v-else>
        <h1 class="login-heading">Choose a new password</h1>
        <p class="login-caption">You'll be signed in once it's saved.</p>

        <form @submit.prevent="submit" class="login-form" novalidate>
          <div class="field">
            <label for="reset-password" class="label">New password</label>
            <input
              id="reset-password" v-model="password" type="password" class="input"
              placeholder="At least 8 characters" required autocomplete="new-password"
            />
          </div>
          <div class="field">
            <label for="reset-confirm" class="label">Confirm new password</label>
            <input
              id="reset-confirm" v-model="confirmPassword" type="password" class="input"
              placeholder="••••••••" required autocomplete="new-password"
            />
          </div>

          <div v-if="error" class="error-msg" role="alert">{{ error }}</div>

          <button type="submit" class="btn btn-primary login-btn" :disabled="saving">
            <i v-if="saving" class="ti ti-loader-2" style="animation: spin 0.8s linear infinite" />
            {{ saving ? 'Saving…' : 'Save and sign in' }}
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
.login-logo { display: flex; align-items: center; gap: 10px; margin-bottom: 32px; color: var(--text-primary); }
.login-brand { font-size: 22px; font-weight: 500; letter-spacing: -0.02em; }
.login-sub { font-family: var(--font-mono); font-size: 12px; letter-spacing: 0.1em; color: var(--text-muted); }
.login-heading { font-size: 32px; line-height: 1.12; font-weight: 500; letter-spacing: -0.012em; }
.login-caption { font-size: 15px; color: var(--text-secondary); margin-top: 8px; margin-bottom: 28px; }
.login-form { display: flex; flex-direction: column; gap: 18px; }
.field { display: flex; flex-direction: column; gap: 6px; }
.label { font-size: 14px; color: var(--text-secondary); }
.error-msg { font-size: 14px; color: var(--coral); background: var(--coral-bg); padding: 10px 14px; border-radius: var(--radius-sm); }
.login-btn { width: 100%; margin-top: 4px; text-align: center; display: block; }
.back-link { display: inline-block; margin-top: 20px; font-size: 14px; color: var(--purple); }
.back-link:hover { text-decoration: underline; }
.loading-msg { font-size: 15px; color: var(--text-muted); }
@keyframes spin { to { transform: rotate(360deg); } }

/* The Sedna mark: used exactly as supplied — fixed square, never stretched or recoloured */
.brand-mark { width: 32px; height: 32px; flex: none; object-fit: contain; display: block; }
</style>
