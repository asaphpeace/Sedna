<script setup lang="ts">
import { nextTick, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { authApi } from '@/api'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()
const email = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)

// Back to where sign-in was asked for (only same-site paths)
function goBack() {
  const back = typeof route.query.redirect === 'string' && route.query.redirect.startsWith('/') && !route.query.redirect.startsWith('//')
    ? route.query.redirect : '/home'
  router.push(back)
}

async function submit() {
  error.value = ''
  loading.value = true
  try {
    await auth.login(email.value, password.value)
    goBack()
  } catch {
    error.value = 'Invalid email or password.'
  } finally {
    loading.value = false
  }
}

// Google sign-in: shown only when the server has a Google client ID.
// Sedna staff use their sedna.com Google account; invited customers can
// too once their company's domain is switched on.
const googleReady = ref(false)
const googleButton = ref<HTMLElement | null>(null)

function loadGoogleScript(): Promise<void> {
  if ((window as any).google?.accounts?.id) return Promise.resolve()
  return new Promise((resolve, reject) => {
    const tag = document.createElement('script')
    tag.src = 'https://accounts.google.com/gsi/client'
    tag.async = true
    tag.onload = () => resolve()
    tag.onerror = () => reject()
    document.head.appendChild(tag)
  })
}

async function onGoogleCredential(response: { credential: string }) {
  error.value = ''
  loading.value = true
  try {
    await auth.googleSignIn(response.credential)
    goBack()
  } catch (err: any) {
    const d = err?.response?.data?.detail
    error.value = typeof d === 'string' ? d : "Google sign-in didn't work. Try again."
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  try {
    const clientId = (await authApi.config()).data.google_client_id
    if (!clientId) return
    await loadGoogleScript()
    const google = (window as any).google
    google.accounts.id.initialize({ client_id: clientId, callback: onGoogleCredential })
    googleReady.value = true
    await nextTick()
    google.accounts.id.renderButton(googleButton.value, {
      theme: 'outline', size: 'large', text: 'signin_with', shape: 'rectangular', width: 360,
    })
  } catch {
    // No Google sign-in (not configured or blocked): the password form still works
  }
})

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

      <template v-if="googleReady">
        <div ref="googleButton" class="google-btn" />
        <div class="divider"><span>or sign in with email</span></div>
      </template>

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
.google-btn { display: flex; justify-content: center; min-height: 44px; }
.divider { display: flex; align-items: center; gap: 12px; margin: 20px 0; font-size: 13px; color: var(--text-muted); }
.divider::before, .divider::after { content: ''; flex: 1; height: 1px; background: var(--hairline); }
.forgot-link { font-size: 14px; color: var(--purple); }
.forgot-link:hover { text-decoration: underline; }
.error-msg { font-size: 14px; color: var(--coral); background: var(--coral-bg); padding: 10px 14px; border-radius: var(--radius-sm); }
.login-btn { width: 100%; margin-top: 4px; }
@keyframes spin { to { transform: rotate(360deg); } }

/* The Sedna mark: used exactly as supplied — fixed square, never stretched or recoloured */
.brand-mark { width: 32px; height: 32px; flex: none; object-fit: contain; display: block; }
</style>
