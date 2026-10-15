<script setup lang="ts">
import { ref } from 'vue'
import { authApi } from '@/api'

// Ask for a reset link. The answer is the same whether or not the email has
// an account, so we never say which.
const email = ref(typeof history.state?.email === 'string' ? history.state.email : '')
const sent = ref(false)
const error = ref('')
const sending = ref(false)

async function submit() {
  error.value = ''
  if (!/^\S+@\S+\.\S+$/.test(email.value.trim())) {
    error.value = 'Enter the email address you sign in with.'
    return
  }
  sending.value = true
  try {
    await authApi.forgotPassword(email.value.trim())
    sent.value = true
  } catch (err: any) {
    const code = err?.response?.status
    error.value = code === 422 ? "That doesn't look like a valid email address. Check it and try again."
      : code === 429 ? 'Too many requests. Wait a minute, then try again.'
      : 'Something went wrong. Try again in a moment.'
  } finally {
    sending.value = false
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

      <template v-if="sent">
        <h1 class="login-heading">Check your email</h1>
        <p class="login-caption">
          If there's an account for <strong>{{ email.trim() }}</strong>, we've sent a link to choose a new password.
          It expires in 1 hour. Nothing there after a few minutes? Check your spam folder, or ask your Sedna contact.
        </p>
        <RouterLink to="/login" class="btn btn-primary login-btn">Back to sign in</RouterLink>
      </template>

      <template v-else>
        <h1 class="login-heading">Forgot your password?</h1>
        <p class="login-caption">Enter your email and we'll send you a link to choose a new one.</p>

        <form @submit.prevent="submit" class="login-form" novalidate>
          <div class="field">
            <label for="forgot-email" class="label">Email</label>
            <input
              id="forgot-email" v-model="email" type="email" class="input"
              placeholder="you@company.com" required autocomplete="email" aria-required="true"
            />
          </div>

          <div v-if="error" class="error-msg" role="alert">{{ error }}</div>

          <button type="submit" class="btn btn-primary login-btn" :disabled="sending">
            <i v-if="sending" class="ti ti-loader-2" style="animation: spin 0.8s linear infinite" />
            {{ sending ? 'Sending…' : 'Send reset link' }}
          </button>
        </form>
        <RouterLink to="/login" class="back-link">← Back to sign in</RouterLink>
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
