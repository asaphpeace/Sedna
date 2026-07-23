<script setup lang="ts">
import { computed } from 'vue'
import { useAppStore } from '@/stores/app'
import { savedApi } from '@/api'
import { PRODUCT_META, productShortLabel } from '@/constants/products'

const app = useAppStore()
const items = computed(() => app.saved)

async function unsave(moduleId: number) {
  await savedApi.unsave(moduleId)
  await app.loadSaved()
}

const typeIcon: Record<string, string> = { v: 'ti-player-play', a: 'ti-file-text', l: 'ti-link', p: 'ti-microphone', s: 'ti-presentation' }
const typeBg: Record<string, string>   = { v: '#F1EBFE', a: '#FBF1E3', l: '#E3F4F9', p: '#FCE8F3', s: '#E2F6EC' }
const typeFg: Record<string, string>   = { v: '#6E2BF0', a: '#B26A00', l: '#0B8FB0', p: '#C2185B', s: '#0E9E6E' }
</script>

<template>
  <div class="page">
    <div class="page-header">
      <h1 class="page-title">Saved Modules</h1>
      <p class="page-sub">{{ items.length }} saved</p>
    </div>
    <div v-if="items.length === 0" class="empty">
      <i class="ti ti-bookmark" style="font-size: 32px; color: var(--border-mid)" />
      <p>No saved modules yet — bookmark modules while browsing to find them here.</p>
    </div>
    <div v-else class="list">
      <RouterLink
        v-for="s in items" :key="s.module_id"
        :to="`/modules/${s.module_id}`"
        class="row"
      >
        <div class="row-icon" :style="{ background: typeBg[s.module_type] }">
          <i :class="['ti', typeIcon[s.module_type]]" :style="{ color: typeFg[s.module_type], fontSize: '14px' }" />
        </div>
        <div class="row-body">
          <div class="row-title">{{ s.title }}</div>
          <div class="row-meta">
            <span class="pill" :style="{ background: PRODUCT_META[s.product]?.bg, color: PRODUCT_META[s.product]?.color }">{{ productShortLabel(s.product) }}</span>
            · {{ s.role_name }} · {{ s.tier_name }} · {{ s.duration_mins }} min
          </div>
        </div>
        <div class="row-saved">Saved {{ new Date(s.saved_at).toLocaleDateString() }}</div>
        <button class="unsave-btn" @click.prevent="unsave(s.module_id)" title="Remove">
          <i class="ti ti-bookmark-filled" style="color: var(--purple)" />
        </button>
      </RouterLink>
    </div>
  </div>
</template>

<style scoped>
.page { padding: 28px 32px; max-width: 800px; margin: 0 auto; }
.page-header { margin-bottom: 20px; }
.page-title { font-size: 22px; font-weight: 800; letter-spacing: -0.4px; }
.page-sub { font-size: 13px; color: var(--text-muted); margin-top: 3px; }
.empty { display: flex; flex-direction: column; align-items: center; gap: 12px; padding: 60px 20px; color: var(--text-muted); font-size: 14px; text-align: center; }
.list { display: flex; flex-direction: column; gap: 0; }
.row { display: flex; align-items: center; gap: 14px; padding: 14px 0; border-bottom: 1px solid var(--border); text-decoration: none; }
.row:last-child { border-bottom: none; }
.row-icon { width: 36px; height: 36px; border-radius: 9px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.row-body { flex: 1; }
.row-title { font-size: 13.5px; font-weight: 600; color: var(--text-primary); }
.row-meta { font-size: 12px; color: var(--text-muted); margin-top: 4px; display: flex; align-items: center; gap: 5px; flex-wrap: wrap; }
.row-saved { font-size: 12px; color: var(--text-muted); white-space: nowrap; flex-shrink: 0; }
.unsave-btn { background: none; border: none; cursor: pointer; font-size: 17px; padding: 4px; flex-shrink: 0; }
</style>
