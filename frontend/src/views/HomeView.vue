<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useAppStore } from '@/stores/app'
import { orgApi } from '@/api'

const app = useAppStore()
const topPaths = computed(() => app.pathProgress.slice(0, 3))
const recentActivity = computed(() => app.activity.slice(0, 5))
const recentReleases = computed(() => app.releases.slice(0, 3))

// Assigned (pushed) training is distinct from self-directed browsing —
// only show the card at all once we know whether there's anything in it.
const assignments = ref<any[]>([])
onMounted(async () => {
  try {
    const { data } = await orgApi.myAssignments()
    assignments.value = data.filter((a: any) => a.status !== 'complete')
  } catch {
    assignments.value = []
  }
})

function dueLabel(a: any) {
  if (!a.due_date) return null
  const days = Math.ceil((new Date(a.due_date).getTime() - Date.now()) / 86400000)
  if (a.status === 'overdue' || days < 0) return { text: `Overdue by ${Math.abs(days)}d`, urgent: true }
  if (days === 0) return { text: 'Due today', urgent: true }
  if (days <= 7) return { text: `Due in ${days}d`, urgent: true }
  return { text: `Due ${a.due_date}`, urgent: false }
}

const prodColor: Record<string, { bg: string; fg: string; label: string }> = {
  vms:    { bg: '#F1EBFE', fg: '#6E2BF0', label: 'VMS' },
  stream: { bg: '#E3F4F9', fg: '#0B8FB0', label: 'Stream' },
  cross:  { bg: '#E2F6EC', fg: '#0E9E6E', label: 'Cross' },
  academy:{ bg: '#FBF1E3', fg: '#B26A00', label: 'Academy' },
}

function actionIcon(action: string) {
  return { started: 'ti-player-play', completed: 'ti-check', earned: 'ti-certificate', saved: 'ti-bookmark' }[action] ?? 'ti-activity'
}
function actionIconBg(action: string) {
  return { started: '#F1EBFE', completed: '#E2F6EC', earned: '#FBF1E3', saved: '#F1EBFE' }[action] ?? '#F3F2F6'
}
function actionIconFg(action: string) {
  return { started: '#6E2BF0', completed: '#0E7E58', earned: '#B26A00', saved: '#6E2BF0' }[action] ?? '#A39EAE'
}
</script>

<template>
  <div class="page">

    <!-- Assigned to you (mandatory/pushed training, separate from self-directed browsing) -->
    <section v-if="assignments.length" class="card assigned-card">
      <div class="section-head">
        <span class="section-title">Assigned to you</span>
      </div>
      <div class="assigned-list">
        <RouterLink v-for="a in assignments" :key="a.id" :to="`/paths/${a.role_id ?? ''}`" class="assigned-row">
          <div class="assigned-body">
            <span class="assigned-name">{{ a.role_name }} — {{ a.tier_name }}</span>
            <span v-if="a.mandatory" class="mandatory-tag">Mandatory</span>
          </div>
          <span v-if="dueLabel(a)" class="due-tag" :class="{ urgent: dueLabel(a)!.urgent }">{{ dueLabel(a)!.text }}</span>
        </RouterLink>
      </div>
    </section>

    <div class="grid">
      <!-- My Paths progress -->
      <section class="card">
        <div class="section-head">
          <span class="section-title">My Learning Paths</span>
          <RouterLink to="/paths" class="see-all">View all <i class="ti ti-arrow-right" /></RouterLink>
        </div>
        <div v-if="topPaths.length === 0" class="empty">No paths started yet — <RouterLink to="/paths">browse paths</RouterLink></div>
        <div v-else class="path-list">
          <RouterLink
            v-for="p in topPaths" :key="p.role_id"
            :to="`/paths/${p.role_id}`"
            class="path-row"
          >
            <div class="path-info">
              <span class="path-name">{{ p.role_name }}</span>
              <span class="path-pct">{{ p.pct }}%</span>
            </div>
            <div class="progress-bar">
              <div class="progress-bar-fill" :style="{ width: p.pct + '%', background: p.pct >= 80 ? 'var(--green)' : 'var(--purple)' }" />
            </div>
            <div class="path-meta">{{ p.done_modules }}/{{ p.total_modules }} modules · {{ p.earned_certs }}/{{ p.total_certs }} certs</div>
          </RouterLink>
        </div>
      </section>

      <!-- Recent activity -->
      <section class="card">
        <div class="section-head">
          <span class="section-title">Recent Activity</span>
          <RouterLink to="/activity" class="see-all">View all <i class="ti ti-arrow-right" /></RouterLink>
        </div>
        <div v-if="recentActivity.length === 0" class="empty">No activity yet</div>
        <div v-else class="activity-list">
          <div v-for="a in recentActivity" :key="a.id" class="activity-row">
            <div class="avatar" :style="{ background: a.user_color, width: '28px', height: '28px', fontSize: '11px' }">{{ a.user_initial }}</div>
            <div class="act-body">
              <span class="act-name">{{ a.user_name }}</span>
              <span class="act-text"> {{ a.action }} </span>
              <span class="act-target">{{ a.target_label }}</span>
            </div>
            <div class="act-icon" :style="{ background: actionIconBg(a.action) }">
              <i :class="['ti', actionIcon(a.action)]" :style="{ color: actionIconFg(a.action) }" />
            </div>
          </div>
        </div>
      </section>

      <!-- What's new -->
      <section class="card span-2">
        <div class="section-head">
          <span class="section-title">What's New</span>
          <RouterLink to="/whatsnew" class="see-all">See all releases <i class="ti ti-arrow-right" /></RouterLink>
        </div>
        <div class="releases-list">
          <div v-for="r in recentReleases" :key="r.id" class="release-row">
            <div class="release-tag" :style="{ background: prodColor[r.product]?.bg, color: prodColor[r.product]?.fg }">{{ r.tag }}</div>
            <div class="release-body">
              <div class="release-title">{{ r.title }}</div>
              <div class="release-desc">{{ r.description }}</div>
            </div>
            <div class="release-date">{{ new Date(r.published_at).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' }) }}</div>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<style scoped>
.page { padding: 24px 28px 40px; max-width: 1100px; margin: 0 auto; }
.grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
.span-2 { grid-column: span 2; }
.section-head { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; }
.section-title { font-size: 14px; font-weight: 700; }
.see-all { font-size: 12px; color: var(--purple); font-weight: 600; display: flex; align-items: center; gap: 3px; }
.empty { font-size: 13px; color: var(--text-muted); }

/* Path rows */
.path-list { display: flex; flex-direction: column; gap: 14px; }
.path-row { display: flex; flex-direction: column; gap: 6px; text-decoration: none; }
.path-info { display: flex; justify-content: space-between; }
.path-name { font-size: 13px; font-weight: 600; color: var(--text-primary); }
.path-pct { font-size: 12px; color: var(--text-muted); }
.path-meta { font-size: 11px; color: var(--text-muted); }

/* Activity */
.activity-list { display: flex; flex-direction: column; gap: 12px; }
.activity-row { display: flex; align-items: center; gap: 10px; }
.act-body { flex: 1; font-size: 12.5px; color: var(--text-secondary); }
.act-name { font-weight: 600; color: var(--text-primary); }
.act-text { }
.act-target { color: var(--purple); font-weight: 500; }
.act-icon { width: 28px; height: 28px; border-radius: 7px; display: flex; align-items: center; justify-content: center; font-size: 13px; flex-shrink: 0; }

/* Releases */
.releases-list { display: flex; flex-direction: column; gap: 0; }
.release-row { display: flex; align-items: flex-start; gap: 14px; padding: 14px 0; border-bottom: 1px solid var(--border); }
.release-row:last-child { border-bottom: none; }
.release-tag { font-size: 11px; font-weight: 700; padding: 3px 9px; border-radius: 6px; white-space: nowrap; flex-shrink: 0; margin-top: 2px; }
.release-body { flex: 1; }
.release-title { font-size: 13.5px; font-weight: 600; }
.release-desc { font-size: 12.5px; color: var(--text-muted); margin-top: 3px; line-height: 1.45; }
.release-date { font-size: 11.5px; color: var(--text-muted); white-space: nowrap; flex-shrink: 0; }

/* Assigned to you */
.assigned-card { margin-bottom: 20px; border: 1px solid var(--purple); }
.assigned-list { display: flex; flex-direction: column; gap: 0; }
.assigned-row { display: flex; align-items: center; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid var(--border); text-decoration: none; }
.assigned-row:last-child { border-bottom: none; }
.assigned-body { display: flex; align-items: center; gap: 8px; }
.assigned-name { font-size: 13px; font-weight: 600; color: var(--text-primary); }
.mandatory-tag { font-size: 10.5px; font-weight: 700; color: #B26A00; background: #FBF1E3; padding: 2px 7px; border-radius: 100px; }
.due-tag { font-size: 12px; font-weight: 600; color: var(--text-muted); }
.due-tag.urgent { color: #C0392B; }
</style>
