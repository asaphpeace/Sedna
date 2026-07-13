<script setup lang="ts">
import { computed } from 'vue'
import { useAppStore } from '@/stores/app'

const app = useAppStore()

function actionIcon(action: string) {
  return { started: 'ti-player-play', completed: 'ti-check', earned: 'ti-certificate', saved: 'ti-bookmark' }[action] ?? 'ti-activity'
}
function actionBg(action: string) {
  return { started: '#F1EBFE', completed: '#E2F6EC', earned: '#FBF1E3', saved: '#F1EBFE' }[action] ?? '#F3F2F6'
}
function actionFg(action: string) {
  return { started: '#6E2BF0', completed: '#0E7E58', earned: '#B26A00', saved: '#6E2BF0' }[action] ?? '#A39EAE'
}

function dayLabel(dateStr: string) {
  const d = new Date(dateStr)
  const now = new Date()
  const diff = Math.floor((now.getTime() - d.getTime()) / 86400000)
  if (diff === 0) return 'Today'
  if (diff === 1) return 'Yesterday'
  if (diff < 7) return 'Earlier this week'
  return d.toLocaleDateString('en-GB', { day: 'numeric', month: 'long' })
}

const grouped = computed(() => {
  const groups: Record<string, any[]> = {}
  for (const a of app.activity) {
    const label = dayLabel(a.created_at)
    if (!groups[label]) groups[label] = []
    groups[label].push(a)
  }
  return Object.entries(groups)
})
</script>

<template>
  <div class="page">
    <div class="page-header">
      <h1 class="page-title">Team Activity</h1>
    </div>

    <div v-if="grouped.length === 0" class="empty">No activity yet.</div>

    <div v-else class="groups">
      <div v-for="[day, items] in grouped" :key="day" class="group">
        <div class="day-label">{{ day }}</div>
        <div class="items">
          <div v-for="a in items" :key="a.id" class="activity-row">
            <div class="act-icon" :style="{ background: actionBg(a.action) }">
              <i :class="['ti', actionIcon(a.action)]" :style="{ color: actionFg(a.action), fontSize: '14px' }" />
            </div>
            <div class="avatar" :style="{ background: a.user_color, width: '28px', height: '28px', fontSize: '11px' }">{{ a.user_initial }}</div>
            <div class="act-body">
              <span class="act-name">{{ a.user_name }}</span>
              <span class="act-verb"> {{ a.action }} </span>
              <span class="act-target">{{ a.target_label }}</span>
            </div>
            <div class="act-time">{{ new Date(a.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) }}</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.page { padding: 28px 32px; max-width: 760px; margin: 0 auto; }
.page-header { margin-bottom: 24px; }
.page-title { font-size: 22px; font-weight: 800; letter-spacing: -0.4px; }
.empty { color: var(--text-muted); }
.groups { display: flex; flex-direction: column; gap: 24px; }
.day-label { font-size: 11.5px; font-weight: 700; letter-spacing: 0.5px; text-transform: uppercase; color: var(--text-muted); margin-bottom: 10px; }
.items { display: flex; flex-direction: column; gap: 0; }
.activity-row { display: flex; align-items: center; gap: 10px; padding: 12px 0; border-bottom: 1px solid var(--border); }
.activity-row:last-child { border-bottom: none; }
.act-icon { width: 30px; height: 30px; border-radius: 8px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.act-body { flex: 1; font-size: 13px; color: var(--text-secondary); }
.act-name { font-weight: 600; color: var(--text-primary); }
.act-target { color: var(--purple); font-weight: 500; }
.act-time { font-size: 12px; color: var(--text-muted); white-space: nowrap; flex-shrink: 0; }
</style>
