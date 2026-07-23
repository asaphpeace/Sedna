<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { orgApi } from '@/api'

const assignments = ref<any[]>([])
const statusFilter = ref('')
const loading = ref(true)

onMounted(async () => {
  const { data } = await orgApi.listAssignments()
  assignments.value = data
  loading.value = false
})

const STATUS_META: Record<string, { label: string; bg: string; fg: string }> = {
  complete: { label: 'Complete', bg: 'var(--green-bg)', fg: 'var(--green)' },
  in_progress: { label: 'In progress', bg: 'var(--purple-subtle)', fg: 'var(--purple)' },
  overdue: { label: 'Overdue', bg: '#FCE8E8', fg: '#C0392B' },
  not_started: { label: 'Not started', bg: '#F3F2F6', fg: 'var(--text-muted)' },
}

const filtered = computed(() =>
  statusFilter.value ? assignments.value.filter((a) => a.status === statusFilter.value) : assignments.value
)

const summary = computed(() => {
  const total = assignments.value.length
  const complete = assignments.value.filter((a) => a.status === 'complete').length
  const overdue = assignments.value.filter((a) => a.status === 'overdue').length
  return { total, complete, overdue, rate: total ? Math.round((complete / total) * 100) : 0 }
})

async function removeAssignment(id: number) {
  await orgApi.deleteAssignment(id)
  assignments.value = assignments.value.filter((a) => a.id !== id)
}
</script>

<template>
  <div class="page">
    <div class="page-header">
      <h1 class="page-title">Compliance</h1>
      <p class="page-sub">Assigned training and completion status across your team.</p>
    </div>

    <div class="summary-row">
      <div class="summary-card">
        <div class="summary-num">{{ summary.total }}</div>
        <div class="summary-label">Assignments</div>
      </div>
      <div class="summary-card">
        <div class="summary-num">{{ summary.rate }}%</div>
        <div class="summary-label">Completion rate</div>
      </div>
      <div class="summary-card" :class="{ warn: summary.overdue > 0 }">
        <div class="summary-num">{{ summary.overdue }}</div>
        <div class="summary-label">Overdue</div>
      </div>
    </div>

    <div class="filters">
      <button class="chip" :class="{ active: statusFilter === '' }" @click="statusFilter = ''">All</button>
      <button v-for="(meta, key) in STATUS_META" :key="key" class="chip" :class="{ active: statusFilter === key }" @click="statusFilter = key">
        {{ meta.label }}
      </button>
    </div>

    <div v-if="loading" class="empty">Loading…</div>
    <div v-else-if="!filtered.length" class="empty">No assignments{{ statusFilter ? ` with status "${STATUS_META[statusFilter].label}"` : '' }} yet.</div>

    <div v-else class="table-wrap">
      <table class="data-table">
        <thead>
          <tr>
            <th>Person</th><th>Training</th><th>Due</th><th>Status</th><th>Progress</th><th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="a in filtered" :key="a.id">
            <td>{{ a.user_name }}</td>
            <td>
              {{ a.role_name }} — {{ a.tier_name }}
              <span v-if="a.mandatory" class="mandatory-tag">Mandatory</span>
            </td>
            <td>{{ a.due_date ?? '—' }}</td>
            <td>
              <span class="status-pill" :style="{ background: STATUS_META[a.status].bg, color: STATUS_META[a.status].fg }">
                {{ STATUS_META[a.status].label }}
              </span>
            </td>
            <td>
              <div class="progress-track"><div class="progress-fill" :style="{ width: a.pct_complete + '%' }" /></div>
            </td>
            <td class="actions-cell">
              <button class="icon-btn" title="Remove assignment" @click="removeAssignment(a.id)"><i class="ti ti-trash" /></button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<style scoped>
.page { padding: 28px 32px; max-width: 1000px; margin: 0 auto; }
.page-header { margin-bottom: 20px; }
.page-title { font-size: 22px; font-weight: 800; letter-spacing: -0.4px; }
.page-sub { font-size: 13px; color: var(--text-muted); margin-top: 3px; }

.summary-row { display: flex; gap: 12px; margin-bottom: 18px; }
.summary-card { flex: 1; background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 16px; }
.summary-card.warn { border-color: #C0392B; }
.summary-num { font-size: 24px; font-weight: 800; }
.summary-label { font-size: 12px; color: var(--text-muted); margin-top: 2px; }

.filters { display: flex; gap: 6px; margin-bottom: 14px; flex-wrap: wrap; }
.chip { font-size: 12.5px; font-weight: 600; padding: 5px 12px; border-radius: 100px; border: 1px solid var(--border); background: var(--surface); cursor: pointer; color: var(--text-secondary); }
.chip.active { background: var(--purple); color: #fff; border-color: var(--purple); }

.empty { padding: 40px; text-align: center; color: var(--text-muted); font-size: 13px; }
.table-wrap { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); overflow: hidden; }
.data-table { width: 100%; border-collapse: collapse; font-size: 13px; }
th { padding: 12px 16px; text-align: left; font-size: 11.5px; font-weight: 700; color: var(--text-muted); border-bottom: 1px solid var(--border); background: var(--bg); }
td { padding: 12px 16px; border-bottom: 1px solid var(--border); vertical-align: middle; }
tr:last-child td { border-bottom: none; }
.mandatory-tag { font-size: 10.5px; font-weight: 700; color: #B26A00; background: #FBF1E3; padding: 2px 7px; border-radius: 100px; margin-left: 6px; }
.status-pill { font-size: 11px; font-weight: 600; padding: 3px 9px; border-radius: 100px; }
.progress-track { width: 100px; height: 5px; border-radius: 100px; background: var(--border); overflow: hidden; }
.progress-fill { height: 100%; background: var(--purple); }
.actions-cell { text-align: right; }
.icon-btn { background: none; border: none; cursor: pointer; color: var(--text-muted); font-size: 15px; padding: 4px; }
.icon-btn:hover { color: #C0392B; }
</style>
