<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { teamApi } from '@/api'
import { useAppStore } from '@/stores/app'

const app = useAppStore()
const team = ref<any[]>([])

onMounted(async () => {
  const { data } = await teamApi.list()
  team.value = data
})

const progMap = computed(() => Object.fromEntries(app.pathProgress.map(p => [p.role_id, p])))

function pct(member: any) {
  const entries = app.pathProgress.filter(() => true) // all path progress for org
  return 0 // placeholder — real impl would fetch per-user progress
}
</script>

<template>
  <div class="page">
    <div class="page-header">
      <h1 class="page-title">Team</h1>
      <p class="page-sub">{{ team.length }} members</p>
    </div>

    <div class="table-wrap">
      <table class="team-table">
        <thead>
          <tr>
            <th>Member</th>
            <th>Role</th>
            <th>Status</th>
            <th>Last active</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="m in team" :key="m.id">
            <td>
              <div class="member-cell">
                <div class="avatar" :style="{ background: m.color, width: '32px', height: '32px', fontSize: '13px' }">{{ m.initial }}</div>
                <div>
                  <div class="member-name">{{ m.name }}</div>
                  <div class="member-email">{{ m.email }}</div>
                </div>
              </div>
            </td>
            <td><span class="role-text">{{ m.role ?? '—' }}</span></td>
            <td>
              <span class="status-pill" :style="{
                background: m.status === 'active' ? 'var(--green-bg)' : m.status === 'invited' ? '#FBF1E3' : '#F3F2F6',
                color: m.status === 'active' ? 'var(--green)' : m.status === 'invited' ? 'var(--orange)' : 'var(--text-muted)',
              }">{{ m.status }}</span>
            </td>
            <td class="last-active">{{ m.last_active_at ? new Date(m.last_active_at).toLocaleDateString() : '—' }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<style scoped>
.page { padding: 28px 32px; max-width: 900px; margin: 0 auto; }
.page-header { margin-bottom: 20px; }
.page-title { font-size: 22px; font-weight: 800; letter-spacing: -0.4px; }
.page-sub { font-size: 13px; color: var(--text-muted); margin-top: 3px; }
.table-wrap { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); overflow: hidden; }
.team-table { width: 100%; border-collapse: collapse; font-size: 13px; }
th { padding: 12px 16px; text-align: left; font-size: 11.5px; font-weight: 700; color: var(--text-muted); border-bottom: 1px solid var(--border); background: var(--bg); }
td { padding: 13px 16px; border-bottom: 1px solid var(--border); vertical-align: middle; }
tr:last-child td { border-bottom: none; }
tr:hover td { background: var(--purple-subtle); }
.member-cell { display: flex; align-items: center; gap: 10px; }
.member-name { font-weight: 600; color: var(--text-primary); }
.member-email { font-size: 11.5px; color: var(--text-muted); }
.role-text { font-size: 13px; color: var(--text-secondary); }
.status-pill { font-size: 11px; font-weight: 600; padding: 3px 9px; border-radius: 100px; }
.last-active { color: var(--text-muted); }
</style>
