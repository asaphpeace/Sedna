<script setup lang="ts">
import { computed } from 'vue'
import { useAppStore } from '@/stores/app'

const app = useAppStore()

function actionIcon(action: string) {
  return { started: 'ti-player-play', completed: 'ti-check', earned: 'ti-certificate', saved: 'ti-bookmark' }[action] ?? 'ti-activity'
}
function actionBg(action: string) {
  return { started: '#ECDEFE', completed: '#D3F4DE', earned: '#FBEDC8', saved: '#ECDEFE' }[action] ?? '#F1F2F4'
}
function actionFg(action: string) {
  return { started: '#7A3FE5', completed: '#1F8A5B', earned: '#633806', saved: '#7A3FE5' }[action] ?? '#6B6C75'
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
.page { padding: 40px 24px 72px; max-width: 760px; margin: 0 auto; }
.page-header { margin-bottom: 32px; }
.page-title { font-size: 40px; line-height: 1.12; font-weight: 500; letter-spacing: -0.012em; }
.empty { color: var(--text-muted); }
.groups { display: flex; flex-direction: column; gap: 24px; }
.day-label { font-size: 12.5px; font-weight: 500; letter-spacing: 0.5px; text-transform: uppercase; color: var(--text-muted); margin-bottom: 10px; }
.items { display: flex; flex-direction: column; gap: 0; }
.activity-row { display: flex; align-items: center; gap: 10px; padding: 12px 0; border-bottom: 1px solid var(--border); }
.activity-row:last-child { border-bottom: none; }
.act-icon { width: 30px; height: 30px; border-radius: 8px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.act-body { flex: 1; font-size: 14px; color: var(--text-secondary); }
.act-name { font-weight: 500; color: var(--text-primary); }
.act-target { color: var(--purple); font-weight: 500; }
.act-time { font-size: 13px; color: var(--text-muted); white-space: nowrap; flex-shrink: 0; }
</style>
