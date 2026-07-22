<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { pathsApi } from '@/api'
import { useAppStore } from '@/stores/app'

const route = useRoute()
const router = useRouter()
const app = useAppStore()
const role = ref<any>(null)
const collapsed = ref<Record<number, boolean>>({})

onMounted(async () => {
  const { data } = await pathsApi.get(Number(route.params.id))
  role.value = data
})

const tierStateMeta = (tier: any) => {
  const prog = app.pathProgress.find(p => p.role_id === role.value?.id)
  if (!prog) return { label: 'Not started', bg: '#F3F2F6', fg: '#A39EAE' }
  const tierIdx = role.value?.tiers?.indexOf(tier)
  const tierDone = tier.modules.every((m: any) => app.moduleProgress[m.id]?.state === 'done')
  if (tierDone) return { label: 'Completed', bg: '#E2F6EC', fg: '#0E7E58' }
  const hasProg = tier.modules.some((m: any) => app.moduleProgress[m.id])
  if (hasProg || tierIdx === 0) return { label: 'In progress', bg: '#F1EBFE', fg: '#6E2BF0' }
  return { label: 'Locked', bg: '#F3F2F6', fg: '#A39EAE' }
}

const modState = (m: any) => app.moduleProgress[m.id]?.state ?? 'not_started'

const typeIcon: Record<string, string> = { v: 'ti-player-play', a: 'ti-file-text', l: 'ti-link', p: 'ti-microphone', s: 'ti-presentation' }
const typeBg: Record<string, string>   = { v: '#F1EBFE', a: '#FBF1E3', l: '#E3F4F9', p: '#FCE8F3', s: '#E2F6EC' }
const typeFg: Record<string, string>   = { v: '#6E2BF0', a: '#B26A00', l: '#0B8FB0', p: '#C2185B', s: '#0E9E6E' }
const prodLabel: Record<string, string> = { vms: 'VMS', stream: 'Stream', cross: 'Cross' }
const prodStyle: Record<string, { bg: string; fg: string }> = {
  vms:    { bg: '#F1EBFE', fg: '#6E2BF0' },
  stream: { bg: '#E3F4F9', fg: '#0B8FB0' },
  cross:  { bg: '#E2F6EC', fg: '#0E9E6E' },
}
</script>

<template>
  <div class="page">
    <button class="back-btn" @click="router.push('/paths')">
      <i class="ti ti-arrow-left" /> Paths
    </button>

    <div v-if="!role" class="loading">Loading…</div>

    <template v-else>
      <div class="hero">
        <h1 class="hero-title">{{ role.name }}</h1>
        <p class="hero-desc">{{ role.description }}</p>
        <div class="hero-meta">
          <span class="pill" :style="{ background: '#F3F2F6', color: '#5F5A6B' }">
            {{ role.audience === 'internal' ? 'Internal — Sedna Staff' : 'Customer Role' }}
          </span>
          <span v-for="prod in role.products" :key="prod" class="pill" :style="{ background: prodStyle[prod]?.bg, color: prodStyle[prod]?.fg }">
            {{ prodLabel[prod] ?? prod }}
          </span>
          <span class="meta-dot">·</span>
          <span class="meta-text">{{ role.tiers.reduce((a: number, t: any) => a + t.modules.length, 0) }} modules</span>
        </div>
      </div>

      <!-- Tiers -->
      <div class="tiers">
        <div v-for="(tier, idx) in role.tiers" :key="tier.id" class="tier">
          <div class="tier-header" @click="collapsed[idx] = !collapsed[idx]">
            <div class="tier-num">{{ idx + 1 }}</div>
            <div class="tier-info">
              <div class="tier-name">{{ tier.label }} — {{ tier.name }}</div>
              <div class="tier-sub">{{ tier.modules.length }} modules · Earns: {{ tier.cert_name }}</div>
            </div>
            <div class="tier-pill" :style="{ background: tierStateMeta(tier).bg, color: tierStateMeta(tier).fg }">
              {{ tierStateMeta(tier).label }}
            </div>
            <i class="ti ti-chevron-down tier-chev" :style="{ transform: collapsed[idx] ? 'rotate(-90deg)' : 'rotate(0)' }" />
          </div>

          <div v-if="!collapsed[idx]" class="module-list">
            <RouterLink
              v-for="(m, mi) in tier.modules" :key="m.id"
              :to="`/modules/${m.id}`"
              class="module-row"
            >
              <div class="mod-seq">{{ mi + 1 }}</div>
              <div class="mod-type-icon" :style="{ background: typeBg[m.module_type] }">
                <i :class="['ti', typeIcon[m.module_type]]" :style="{ color: typeFg[m.module_type], fontSize: '13px' }" />
              </div>
              <div class="mod-body">
                <span class="mod-title">{{ m.title }}</span>
                <span class="mod-meta">
                  <span class="pill" :style="{ background: prodStyle[m.product]?.bg, color: prodStyle[m.product]?.fg }">{{ prodLabel[m.product] }}</span>
                  · {{ m.duration_mins }} min
                </span>
              </div>
              <div class="mod-state">
                <i v-if="modState(m) === 'done'" class="ti ti-circle-check-filled" style="color: var(--green); font-size: 18px;" />
                <i v-else-if="modState(m) === 'in_progress'" class="ti ti-circle-half-2" style="color: var(--purple); font-size: 18px;" />
                <i v-else class="ti ti-circle" style="color: var(--border-mid); font-size: 18px;" />
              </div>
            </RouterLink>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.page { padding: 28px 32px; max-width: 800px; margin: 0 auto; }
.back-btn { display: flex; align-items: center; gap: 6px; font-size: 13px; font-weight: 600; color: var(--text-secondary); padding: 6px 11px; border-radius: 8px; border: 1px solid var(--border); background: var(--surface); margin-bottom: 20px; cursor: pointer; }
.back-btn:hover { background: var(--purple-subtle); }
.loading { color: var(--text-muted); }
.hero { margin-bottom: 28px; }
.hero-title { font-size: 24px; font-weight: 800; letter-spacing: -0.5px; }
.hero-desc { font-size: 14px; color: var(--text-secondary); margin-top: 6px; line-height: 1.5; }
.hero-meta { display: flex; align-items: center; gap: 7px; margin-top: 14px; flex-wrap: wrap; }
.meta-dot { color: var(--border-mid); }
.meta-text { font-size: 13px; color: var(--text-muted); }
.tiers { display: flex; flex-direction: column; gap: 12px; }
.tier { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); overflow: hidden; }
.tier-header { display: flex; align-items: center; gap: 14px; padding: 16px 18px; cursor: pointer; }
.tier-header:hover { background: var(--purple-subtle); }
.tier-num { width: 28px; height: 28px; border-radius: 50%; background: var(--purple); color: #fff; display: flex; align-items: center; justify-content: center; font-size: 13px; font-weight: 700; flex-shrink: 0; }
.tier-info { flex: 1; }
.tier-name { font-size: 14px; font-weight: 700; }
.tier-sub { font-size: 12px; color: var(--text-muted); margin-top: 2px; }
.tier-pill { font-size: 11.5px; font-weight: 600; padding: 3px 10px; border-radius: 100px; }
.tier-chev { font-size: 16px; color: var(--text-muted); transition: transform 0.2s; }
.module-list { border-top: 1px solid var(--border); }
.module-row { display: flex; align-items: center; gap: 12px; padding: 12px 18px; border-bottom: 1px solid var(--border); text-decoration: none; transition: background 0.1s; }
.module-row:last-child { border-bottom: none; }
.module-row:hover { background: var(--purple-subtle); }
.mod-seq { width: 20px; font-size: 11.5px; color: var(--text-muted); font-weight: 600; text-align: center; flex-shrink: 0; }
.mod-type-icon { width: 28px; height: 28px; border-radius: 7px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.mod-body { flex: 1; display: flex; flex-direction: column; gap: 4px; }
.mod-title { font-size: 13px; font-weight: 500; color: var(--text-primary); }
.mod-meta { display: flex; align-items: center; gap: 6px; font-size: 11.5px; color: var(--text-muted); }
.mod-state { flex-shrink: 0; }
</style>
