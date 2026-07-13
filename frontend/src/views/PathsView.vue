<script setup lang="ts">
import { ref, computed } from 'vue'
import { useAppStore } from '@/stores/app'

const app = useAppStore()
const filter = ref<'all' | 'customer' | 'internal'>('all')

const paths = computed(() =>
  filter.value === 'all' ? app.paths : app.paths.filter(p => p.audience === filter.value)
)

const progressMap = computed(() =>
  Object.fromEntries(app.pathProgress.map(p => [p.role_id, p]))
)

const iconColor: Record<string, { bg: string; fg: string }> = {
  purple: { bg: '#F1EBFE', fg: '#6E2BF0' },
  orange: { bg: '#FBF1E3', fg: '#B26A00' },
  green:  { bg: '#E2F6EC', fg: '#0E9E6E' },
  blue:   { bg: '#E3F4F9', fg: '#0B8FB0' },
  teal:   { bg: '#E3F4F9', fg: '#0B8FB0' },
  indigo: { bg: '#EEF0FD', fg: '#4338CA' },
}

const prodLabel: Record<string, string> = { vms: 'VMS', stream: 'Stream', cross: 'Cross' }
const prodStyle: Record<string, { bg: string; fg: string }> = {
  vms:    { bg: '#F1EBFE', fg: '#6E2BF0' },
  stream: { bg: '#E3F4F9', fg: '#0B8FB0' },
  cross:  { bg: '#E2F6EC', fg: '#0E9E6E' },
}
</script>

<template>
  <div class="page">
    <div class="page-header">
      <h1 class="page-title">Learning Paths</h1>
      <p class="page-sub">Choose a role-based path and earn your certifications.</p>
    </div>

    <!-- Filter tabs -->
    <div class="tabs">
      <button v-for="t in ['all', 'customer', 'internal']" :key="t"
        class="tab" :class="{ 'tab--active': filter === t }"
        @click="filter = t as any">
        {{ t === 'all' ? 'All paths' : t === 'customer' ? 'Customer roles' : 'Internal roles' }}
      </button>
    </div>

    <div class="paths-grid">
      <RouterLink
        v-for="p in paths" :key="p.id"
        :to="`/paths/${p.id}`"
        class="path-card"
      >
        <div class="path-card-icon" :style="{ background: iconColor[p.color]?.bg ?? '#F1EBFE' }">
          <i :class="['ti', p.icon]" :style="{ color: iconColor[p.color]?.fg ?? '#6E2BF0', fontSize: '22px' }" />
        </div>
        <div class="path-card-body">
          <div class="path-card-name">{{ p.name }}</div>
          <div class="path-card-desc">{{ p.description }}</div>
          <div class="path-card-meta">
            <span v-for="prod in p.products" :key="prod" class="pill" :style="{ background: prodStyle[prod]?.bg, color: prodStyle[prod]?.fg }">
              {{ prodLabel[prod] ?? prod }}
            </span>
            <span class="meta-dot">·</span>
            <span class="meta-text">{{ p.mod_count }} modules</span>
            <span class="meta-dot">·</span>
            <span class="meta-text">{{ p.tier_count }} certs</span>
          </div>
        </div>
        <div class="path-card-progress">
          <template v-if="progressMap[p.id]">
            <div class="pct-label" :style="{ color: progressMap[p.id].pct > 0 ? 'var(--green)' : 'var(--text-muted)' }">
              {{ progressMap[p.id].pct }}%
            </div>
            <div class="progress-bar" style="width: 60px">
              <div class="progress-bar-fill" :style="{ width: progressMap[p.id].pct + '%', background: 'var(--purple)' }" />
            </div>
          </template>
          <span v-else class="not-started">Not started</span>
          <i class="ti ti-chevron-right arrow" />
        </div>
      </RouterLink>
    </div>
  </div>
</template>

<style scoped>
.page { padding: 28px 32px; max-width: 900px; margin: 0 auto; }
.page-header { margin-bottom: 20px; }
.page-title { font-size: 22px; font-weight: 800; letter-spacing: -0.4px; }
.page-sub { font-size: 13px; color: var(--text-muted); margin-top: 3px; }
.tabs { display: flex; gap: 4px; margin-bottom: 20px; }
.tab { padding: 6px 14px; border-radius: 8px; font-size: 13px; font-weight: 500; color: var(--text-secondary); border: 1px solid transparent; }
.tab:hover { background: var(--purple-subtle); }
.tab--active { background: var(--purple-bg); color: var(--purple); font-weight: 600; }
.paths-grid { display: flex; flex-direction: column; gap: 10px; }
.path-card {
  display: flex; align-items: center; gap: 16px;
  padding: 18px 20px;
  background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius);
  text-decoration: none; transition: border-color 0.12s, box-shadow 0.12s;
}
.path-card:hover { border-color: var(--purple); box-shadow: var(--shadow-md); }
.path-card-icon { width: 48px; height: 48px; border-radius: 12px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.path-card-body { flex: 1; }
.path-card-name { font-size: 14.5px; font-weight: 700; color: var(--text-primary); }
.path-card-desc { font-size: 12.5px; color: var(--text-muted); margin-top: 3px; line-height: 1.45; }
.path-card-meta { display: flex; align-items: center; gap: 6px; margin-top: 10px; flex-wrap: wrap; }
.meta-dot { color: var(--border-mid); font-size: 12px; }
.meta-text { font-size: 12px; color: var(--text-muted); }
.path-card-progress { display: flex; flex-direction: column; align-items: flex-end; gap: 6px; flex-shrink: 0; }
.pct-label { font-size: 12px; font-weight: 700; }
.not-started { font-size: 11px; color: var(--text-muted); }
.arrow { font-size: 16px; color: var(--text-muted); margin-top: 4px; }
</style>
