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
        <span class="login-brand">Sedna</span>
        <span class="login-sub">LEARNING HUB</span>
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
</style>
