<script setup lang="ts">
import { computed } from 'vue'
import { useAppStore } from '@/stores/app'

const app = useAppStore()

const sorted = computed(() => [...app.pathProgress].sort((a, b) => b.pct - a.pct))

const overall = computed(() => {
  if (!sorted.value.length) return 0
  return Math.round(sorted.value.reduce((s, p) => s + p.pct, 0) / sorted.value.length)
})
</script>

<template>
  <div class="page">
    <div class="page-header">
      <h1 class="page-title">My Progress</h1>
      <p class="page-sub">Overall average: <strong>{{ overall }}%</strong></p>
    </div>

    <div class="paths-list">
      <RouterLink
        v-for="p in sorted" :key="p.role_id"
        :to="`/paths/${p.role_id}`"
        class="path-row"
      >
        <div class="path-info">
          <span class="path-name">{{ p.role_name }}</span>
          <span class="path-pct" :style="{ color: p.pct >= 80 ? 'var(--green)' : p.pct > 0 ? 'var(--purple)' : 'var(--text-muted)' }">
            {{ p.pct === 0 ? 'Not started' : p.pct + '%' }}
          </span>
        </div>
        <div class="progress-bar">
          <div class="progress-bar-fill"
            :style="{ width: p.pct + '%', background: p.pct >= 80 ? 'var(--green)' : 'var(--purple)' }" />
        </div>
        <div class="path-sub">
          {{ p.done_modules }} / {{ p.total_modules }} modules completed ·
          {{ p.earned_certs }} / {{ p.total_certs }} certificates earned
        </div>
      </RouterLink>
    </div>
  </div>
</template>

<style scoped>
.page { padding: 28px 32px; max-width: 700px; margin: 0 auto; }
.page-header { margin-bottom: 28px; }
.page-title { font-size: 22px; font-weight: 800; letter-spacing: -0.4px; }
.page-sub { font-size: 13px; color: var(--text-muted); margin-top: 3px; }
.paths-list { display: flex; flex-direction: column; gap: 0; }
.path-row { display: flex; flex-direction: column; gap: 8px; padding: 20px 0; border-bottom: 1px solid var(--border); text-decoration: none; }
.path-row:last-child { border-bottom: none; }
.path-info { display: flex; justify-content: space-between; align-items: baseline; }
.path-name { font-size: 14px; font-weight: 700; color: var(--text-primary); }
.path-pct { font-size: 13px; font-weight: 700; }
.path-sub { font-size: 12px; color: var(--text-muted); }
</style>
