<script setup lang="ts">
import { ref, computed } from 'vue'
import { useAppStore } from '@/stores/app'

const app = useAppStore()
const filter = ref('')

const filtered = computed(() =>
  filter.value ? app.releases.filter((r: any) => r.product === filter.value) : app.releases
)

const prodColor: Record<string, { bg: string; fg: string }> = {
  vms:    { bg: '#ECDEFE', fg: '#7A3FE5' },
  stream: { bg: '#C5D9FE', fg: '#4D2BD3' },
  academy:{ bg: '#FBEDC8', fg: '#633806' },
}
</script>

<template>
  <div class="page">
    <div class="page-header">
      <h1 class="page-title">What's New</h1>
      <p class="page-sub">Latest product updates and new learning content.</p>
    </div>

    <div class="chip-group">
      <button v-for="p in ['', 'vms', 'stream', 'academy']" :key="p"
        class="chip" :class="{ 'chip--active': filter === p }" @click="filter = p">
        {{ p === '' ? 'All' : p === 'vms' ? 'VMS' : p === 'stream' ? 'Stream' : 'Academy' }}
      </button>
    </div>

    <div class="releases">
      <div v-for="r in filtered" :key="r.id" class="release-card">
        <div class="release-meta">
          <span class="release-tag" :style="{ background: prodColor[r.product]?.bg, color: prodColor[r.product]?.fg }">{{ r.tag }}</span>
          <span class="release-date">{{ new Date(r.published_at).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' }) }}</span>
          <span v-if="r.module_count > 0" class="mod-count">{{ r.module_count }} module{{ r.module_count !== 1 ? 's' : '' }}</span>
        </div>
        <h3 class="release-title">{{ r.title }}</h3>
        <p class="release-desc">{{ r.description }}</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.page { padding: 40px 24px 72px; max-width: 760px; margin: 0 auto; }
.page-header { margin-bottom: 32px; }
.page-title { font-size: 40px; line-height: 1.12; font-weight: 500; letter-spacing: -0.012em; }
.page-sub { font-size: 17px; line-height: 1.5; color: var(--text-secondary); margin-top: 8px; }
.chip-group { display: flex; gap: 4px; margin-bottom: 24px; flex-wrap: wrap; }
.chip { padding: 5px 14px; border-radius: 100px; font-size: 14px; font-weight: 500; border: 1px solid var(--border); color: var(--text-secondary); background: var(--surface); }
.chip:hover { background: var(--purple-subtle); }
.chip--active { background: var(--purple-bg); color: var(--purple); border-color: var(--purple-bg); font-weight: 500; }
.releases { display: flex; flex-direction: column; gap: 0; }
.release-card { padding: 20px 0; border-bottom: 1px solid var(--border); }
.release-card:last-child { border-bottom: none; }
.release-meta { display: flex; align-items: center; gap: 10px; margin-bottom: 8px; flex-wrap: wrap; }
.release-tag { font-size: 12.5px; font-weight: 500; padding: 3px 9px; border-radius: 6px; }
.release-date { font-size: 13px; color: var(--text-muted); }
.mod-count { font-size: 13px; color: var(--text-muted); background: var(--bg); padding: 2px 8px; border-radius: 100px; border: 1px solid var(--border); }
.release-title { font-size: 15px; font-weight: 500; margin-bottom: 6px; }
.release-desc { font-size: 15px; color: var(--text-secondary); line-height: 1.55; }
</style>
