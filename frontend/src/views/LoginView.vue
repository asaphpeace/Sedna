<script setup lang="ts">
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const route = useRoute()
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
    // Back to where sign-in was asked for (only same-site paths)
    const back = typeof route.query.redirect === 'string' && route.query.redirect.startsWith('/') && !route.query.redirect.startsWith('//')
      ? route.query.redirect : '/home'
    router.push(back)
  } catch {
    error.value = 'Invalid email or password.'
  } finally {
    loading.value = false
  }
}

// Carry the typed email over without putting it in the URL
function forgot() {
  router.push({ path: '/forgot-password', state: { email: email.value.trim() } })
}
</script>

<template>
  <div class="login-page">
    <div class="login-card">
      <!-- Logo -->
      <RouterLink to="/" class="login-logo" aria-label="Back to the Learning Hub">
        <img src="/sedna-logo.png" alt="" width="32" height="32" class="brand-mark" />
        <span class="login-brand">Sedna</span>
        <span class="login-sub">LEARNING HUB</span>
      </RouterLink>

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
          <div class="label-row">
            <label for="login-password" class="label">Password</label>
            <RouterLink to="/forgot-password" class="forgot-link" @click.prevent="forgot">Forgot password?</RouterLink>
          </div>
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
.login-logo { display: flex; align-items: center; gap: 10px; margin-bottom: 32px; color: var(--text-primary); }
.login-brand { font-size: 22px; font-weight: 500; letter-spacing: -0.02em; }
.login-sub { font-family: var(--font-mono); font-size: 12px; letter-spacing: 0.1em; color: var(--text-muted); }
.login-heading { font-size: 32px; line-height: 1.12; font-weight: 500; letter-spacing: -0.012em; }
.login-caption { font-size: 15px; color: var(--text-secondary); margin-top: 8px; margin-bottom: 28px; }
.login-form { display: flex; flex-direction: column; gap: 18px; }
.field { display: flex; flex-direction: column; gap: 6px; }
.label { font-size: 14px; color: var(--text-secondary); }
.label-row { display: flex; align-items: baseline; justify-content: space-between; gap: 12px; }
.forgot-link { font-size: 14px; color: var(--purple); }
.forgot-link:hover { text-decoration: underline; }
.error-msg { font-size: 14px; color: var(--coral); background: var(--coral-bg); padding: 10px 14px; border-radius: var(--radius-sm); }
.login-btn { width: 100%; margin-top: 4px; }
@keyframes spin { to { transform: rotate(360deg); } }

/* The Sedna mark: used exactly as supplied — fixed square, never stretched or recoloured */
.brand-mark { width: 32px; height: 32px; flex: none; object-fit: contain; display: block; }
</style>
