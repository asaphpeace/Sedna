<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { modulesApi, savedApi } from '@/api'
import { useAppStore } from '@/stores/app'

const app = useAppStore()
const modules = ref<any[]>([])
const product = ref<string>('')
const typeFilter = ref<string>('')
const search = ref('')

onMounted(async () => {
  const { data } = await modulesApi.browse()
  modules.value = data
})

const filtered = computed(() => {
  let m = modules.value
  if (product.value) m = m.filter(x => x.product === product.value)
  if (typeFilter.value) m = m.filter(x => x.module_type === typeFilter.value)
  if (search.value) m = m.filter(x => x.title.toLowerCase().includes(search.value.toLowerCase()))
  return m
})

const savedIds = computed(() => new Set(app.saved.map((s: any) => s.module_id)))

async function toggleSave(m: any) {
  if (savedIds.value.has(m.id)) {
    await savedApi.unsave(m.id)
  } else {
    await savedApi.save(m.id)
  }
  await app.loadSaved()
}

const typeBg: Record<string, string>   = { v: '#F1EBFE', a: '#FBF1E3', l: '#E3F4F9', p: '#FCE8F3', s: '#E2F6EC' }
const typeFg: Record<string, string>   = { v: '#6E2BF0', a: '#B26A00', l: '#0B8FB0', p: '#C2185B', s: '#0E9E6E' }
const typeLabel: Record<string, string>= { v: 'Video', a: 'Article', l: 'Link', p: 'Podcast', s: 'Slides' }
const typeIcon: Record<string, string> = { v: 'ti-player-play', a: 'ti-file-text', l: 'ti-link', p: 'ti-microphone', s: 'ti-presentation' }
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
      <h1 class="page-title">Browse Modules</h1>
      <p class="page-sub">{{ filtered.length }} modules{{ modules.length !== filtered.length ? ` of ${modules.length}` : '' }}</p>
    </div>

    <!-- Filters -->
    <div class="filters">
      <input v-model="search" class="search-input" placeholder="Search modules…" />
      <div class="chip-group">
        <button v-for="p in ['', 'vms', 'stream', 'cross']" :key="p"
          class="chip" :class="{ 'chip--active': product === p }" @click="product = p">
          {{ p === '' ? 'All products' : prodLabel[p] }}
        </button>
      </div>
      <div class="chip-group">
        <button v-for="t in ['', 'v', 'a', 'l', 'p', 's']" :key="t"
          class="chip" :class="{ 'chip--active': typeFilter === t }" @click="typeFilter = t">
          {{ t === '' ? 'All types' : typeLabel[t] }}
        </button>
      </div>
    </div>

    <div class="module-grid">
      <RouterLink
        v-for="m in filtered" :key="m.id"
        :to="`/modules/${m.id}`"
        class="module-card"
      >
        <div class="mod-top">
          <div class="mod-icon" :style="{ background: typeBg[m.module_type] }">
            <i :class="['ti', typeIcon[m.module_type]]" :style="{ color: typeFg[m.module_type], fontSize: '16px' }" />
          </div>
          <button class="save-btn" @click.prevent="toggleSave(m)" :title="savedIds.has(m.id) ? 'Unsave' : 'Save'">
            <i :class="['ti', savedIds.has(m.id) ? 'ti-bookmark-filled' : 'ti-bookmark']" :style="{ color: savedIds.has(m.id) ? 'var(--purple)' : 'var(--text-muted)' }" />
          </button>
        </div>
        <div class="mod-title">{{ m.title }}</div>
        <div class="mod-meta">
          <span class="pill" :style="{ background: prodStyle[m.product]?.bg, color: prodStyle[m.product]?.fg }">{{ prodLabel[m.product] }}</span>
          <span class="dot">·</span>
          <span class="dur">{{ m.duration_mins }} min</span>
        </div>
      </RouterLink>
    </div>
  </div>
</template>

<style scoped>
.page { padding: 28px 32px; max-width: 1100px; margin: 0 auto; }
.page-header { margin-bottom: 20px; }
.page-title { font-size: 22px; font-weight: 800; letter-spacing: -0.4px; }
.page-sub { font-size: 13px; color: var(--text-muted); margin-top: 3px; }
.filters { display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 20px; align-items: center; }
.search-input { padding: 8px 12px; border: 1px solid var(--border); border-radius: 8px; font-size: 13px; outline: none; min-width: 220px; }
.search-input:focus { border-color: var(--purple); }
.chip-group { display: flex; gap: 4px; }
.chip { padding: 5px 12px; border-radius: 100px; font-size: 12.5px; font-weight: 500; border: 1px solid var(--border); color: var(--text-secondary); background: var(--surface); }
.chip:hover { background: var(--purple-subtle); }
.chip--active { background: var(--purple-bg); color: var(--purple); border-color: var(--purple-bg); font-weight: 600; }
.module-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 12px; }
.module-card { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 16px; text-decoration: none; display: flex; flex-direction: column; gap: 10px; transition: border-color 0.12s, box-shadow 0.12s; }
.module-card:hover { border-color: var(--purple); box-shadow: var(--shadow); }
.mod-top { display: flex; justify-content: space-between; align-items: flex-start; }
.mod-icon { width: 36px; height: 36px; border-radius: 9px; display: flex; align-items: center; justify-content: center; }
.save-btn { background: none; border: none; cursor: pointer; padding: 4px; font-size: 16px; }
.mod-title { font-size: 13px; font-weight: 600; color: var(--text-primary); line-height: 1.4; flex: 1; }
.mod-meta { display: flex; align-items: center; gap: 6px; }
.dot { color: var(--border-mid); }
.dur { font-size: 12px; color: var(--text-muted); }
</style>
