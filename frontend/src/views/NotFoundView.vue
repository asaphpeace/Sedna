<script setup lang="ts">
import { useRouter } from 'vue-router'
const router = useRouter()
</script>

<template>
  <div class="not-found">
    <div class="not-found-inner">
      <div class="code">404</div>
      <h1>Page not found</h1>
      <p>The page you're looking for doesn't exist or you don't have access to it.</p>
      <div class="actions">
        <button class="btn btn-primary" @click="router.push('/home')">Go home</button>
        <button class="btn btn-ghost" @click="router.back()">Go back</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.not-found {
  min-height: 100vh; display: flex; align-items: center; justify-content: center;
  padding: 2rem;
}
.not-found-inner { text-align: center; max-width: 400px; }
.code { font-size: 6rem; font-weight: 800; color: var(--border); line-height: 1; margin-bottom: 1rem; }
h1 { font-size: 1.5rem; font-weight: 700; margin-bottom: .75rem; }
p { color: var(--text-muted); margin-bottom: 2rem; line-height: 1.6; }
.actions { display: flex; gap: .75rem; justify-content: center; }
</style>
