<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const auth = useAuthStore()
const email = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)

async function submit() {
  error.value = ''
  loading.value = true
  try {
    await auth.login(email.value, password.value)
    router.push('/home')
  } catch {
    error.value = 'Invalid email or password.'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login-page">
    <div class="login-card">
      <!-- Logo -->
      <div class="login-logo">
        <div class="login-logo-icon">
          <svg width="28" height="28" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Sedna Academy logo">
            <defs>
              <mask id="lm">
                <rect width="100" height="100" fill="black"/>
                <rect x="18" y="15" width="46" height="46" rx="7" fill="white"/>
                <rect x="36" y="39" width="46" height="46" rx="7" fill="white"/>
                <rect x="36" y="39" width="14" height="14" fill="black"/>
                <rect x="50" y="53" width="14" height="14" fill="black"/>
              </mask>
            </defs>
            <rect width="100" height="100" fill="#fff" mask="url(#lm)"/>
          </svg>
        </div>
        <div>
          <div class="login-brand">Sedna</div>
          <div class="login-sub">ACADEMY</div>
        </div>
      </div>

      <h1 class="login-heading">Welcome back</h1>
      <p class="login-caption">Sign in to continue learning</p>

      <form @submit.prevent="submit" class="login-form" novalidate>
        <div class="field">
          <label for="login-email" class="label">Email</label>
          <input
            id="login-email"
            v-model="email"
            type="email"
            class="input"
            placeholder="you@company.com"
            required
            autocomplete="email"
            aria-required="true"
          />
        </div>
        <div class="field">
          <label for="login-password" class="label">Password</label>
          <input
            id="login-password"
            v-model="password"
            type="password"
            class="input"
            placeholder="••••••••"
            required
            autocomplete="current-password"
            aria-required="true"
          />
        </div>

        <div v-if="error" class="error-msg">{{ error }}</div>

        <button type="submit" class="btn btn-primary login-btn" :disabled="loading">
          <i v-if="loading" class="ti ti-loader-2" style="animation: spin 0.8s linear infinite" />
          {{ loading ? 'Signing in…' : 'Sign in' }}
        </button>
      </form>
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
.error-msg { font-size: 13px; color: #D32F2F; background: #FFEBEE; padding: 8px 12px; border-radius: 7px; }
.login-btn { width: 100%; justify-content: center; padding: 11px; font-size: 14px; margin-top: 4px; }
@keyframes spin { to { transform: rotate(360deg); } }
</style>
