<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { teamApi, orgApi, adminApi } from '@/api'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const canManage = computed(() => auth.user?.is_admin || auth.user?.is_manager)

const team = ref<any[]>([])
const departments = ref<any[]>([])
const selected = ref<Set<number>>(new Set())

onMounted(async () => {
  const { data } = await teamApi.list()
  team.value = data
  if (canManage.value) {
    const { data: depts } = await orgApi.listDepartments()
    departments.value = depts
  }
})

function deptName(id: number | null) {
  if (!id) return '—'
  return departments.value.find((d) => d.id === id)?.name ?? '—'
}

function toggleSelect(id: number) {
  if (selected.value.has(id)) selected.value.delete(id)
  else selected.value.add(id)
  // Set mutations don't trigger Vue reactivity on their own
  selected.value = new Set(selected.value)
}

// ── Department management ────────────────────────────
const showDeptForm = ref(false)
const newDeptName = ref('')

async function addDepartment() {
  if (!newDeptName.value.trim()) return
  await orgApi.createDepartment({ name: newDeptName.value.trim() })
  newDeptName.value = ''
  showDeptForm.value = false
  const { data } = await orgApi.listDepartments()
  departments.value = data
}

async function setUserDepartment(userId: number, deptId: string) {
  await teamApi.update(userId, { department_id: deptId ? Number(deptId) : null })
  const { data } = await teamApi.list()
  team.value = data
  const { data: depts } = await orgApi.listDepartments()
  departments.value = depts
}

async function setManager(deptId: number, managerId: string) {
  const dept = departments.value.find((d) => d.id === deptId)
  await orgApi.updateDepartment(deptId, { name: dept.name, manager_user_id: managerId ? Number(managerId) : null })
  const { data } = await orgApi.listDepartments()
  departments.value = data
}

// ── Assign training ───────────────────────────────────
const showAssignModal = ref(false)
const paths = ref<any[]>([])
const tiers = ref<any[]>([])
const assignForm = ref({ path_id: '', tier_id: '', due_date: '', mandatory: true })
const assigning = ref(false)

async function openAssignModal() {
  if (selected.value.size === 0) return
  showAssignModal.value = true
  if (!paths.value.length) {
    const { data } = await adminApi.listPaths()
    paths.value = data
  }
}

async function onPathChange() {
  tiers.value = []
  assignForm.value.tier_id = ''
  if (!assignForm.value.path_id) return
  const { data } = await adminApi.listTiers(Number(assignForm.value.path_id))
  tiers.value = data
}

async function submitAssignment() {
  if (!assignForm.value.tier_id) return
  assigning.value = true
  try {
    await orgApi.createAssignments({
      user_ids: Array.from(selected.value),
      tier_id: Number(assignForm.value.tier_id),
      due_date: assignForm.value.due_date || null,
      mandatory: assignForm.value.mandatory,
    })
    showAssignModal.value = false
    selected.value = new Set()
    assignForm.value = { path_id: '', tier_id: '', due_date: '', mandatory: true }
  } finally {
    assigning.value = false
  }
}
</script>

<template>
  <div class="page">
    <div class="page-header">
      <h1 class="page-title">Team</h1>
      <p class="page-sub">{{ team.length }} members</p>
    </div>

    <div v-if="canManage" class="toolbar">
      <button class="btn btn-ghost btn-sm" @click="showDeptForm = !showDeptForm">
        <i class="ti ti-building" /> Manage departments
      </button>
      <button class="btn btn-primary btn-sm" :disabled="selected.size === 0" @click="openAssignModal">
        <i class="ti ti-clipboard-list" /> Assign training{{ selected.size ? ` (${selected.size})` : '' }}
      </button>
    </div>

    <div v-if="showDeptForm" class="dept-panel">
      <div class="dept-row" v-for="d in departments" :key="d.id">
        <span class="dept-name">{{ d.name }}</span>
        <span class="dept-count">{{ d.member_count }} members</span>
        <select class="field-input-sm" :value="d.manager_user_id ?? ''" @change="setManager(d.id, ($event.target as HTMLSelectElement).value)">
          <option value="">No manager</option>
          <option v-for="m in team" :key="m.id" :value="m.id">{{ m.name }} (manager)</option>
        </select>
      </div>
      <div class="dept-add-row">
        <input v-model="newDeptName" class="field-input-sm" placeholder="New department name" @keyup.enter="addDepartment" />
        <button class="btn btn-ghost btn-sm" @click="addDepartment">Add</button>
      </div>
    </div>

    <div class="table-wrap">
      <table class="team-table">
        <thead>
          <tr>
            <th v-if="canManage" style="width: 30px"></th>
            <th>Member</th>
            <th>Role</th>
            <th v-if="canManage">Department</th>
            <th>Status</th>
            <th>Last active</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="m in team" :key="m.id">
            <td v-if="canManage">
              <input type="checkbox" :checked="selected.has(m.id)" @change="toggleSelect(m.id)" />
            </td>
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
            <td v-if="canManage">
              <select class="field-input-sm" :value="m.department_id ?? ''" @change="setUserDepartment(m.id, ($event.target as HTMLSelectElement).value)">
                <option value="">{{ deptName(null) }}</option>
                <option v-for="d in departments" :key="d.id" :value="d.id">{{ d.name }}</option>
              </select>
            </td>
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

    <!-- Assign training modal -->
    <div v-if="showAssignModal" class="modal-overlay" @click.self="showAssignModal = false">
      <div class="modal">
        <h3 class="modal-title">Assign training to {{ selected.size }} {{ selected.size === 1 ? 'person' : 'people' }}</h3>

        <label class="field-label">Path</label>
        <select v-model="assignForm.path_id" class="field-input" @change="onPathChange">
          <option value="">Select a path…</option>
          <option v-for="p in paths" :key="p.id" :value="p.id">{{ p.name }}</option>
        </select>

        <template v-if="tiers.length">
          <label class="field-label">Tier</label>
          <select v-model="assignForm.tier_id" class="field-input">
            <option value="">Select a tier…</option>
            <option v-for="t in tiers" :key="t.id" :value="t.id">{{ t.label }} — {{ t.name }}</option>
          </select>
        </template>

        <label class="field-label">Due date <span class="field-hint">(optional)</span></label>
        <input v-model="assignForm.due_date" type="date" class="field-input" />

        <label class="checkbox-row">
          <input v-model="assignForm.mandatory" type="checkbox" /> Mandatory
        </label>

        <div class="modal-actions">
          <button class="btn btn-ghost" @click="showAssignModal = false">Cancel</button>
          <button class="btn btn-primary" :disabled="!assignForm.tier_id || assigning" @click="submitAssignment">
            {{ assigning ? 'Assigning…' : 'Assign' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.page { padding: 28px 32px; max-width: 900px; margin: 0 auto; }
.page-header { margin-bottom: 20px; }
.page-title { font-size: 22px; font-weight: 800; letter-spacing: -0.4px; }
.page-sub { font-size: 13px; color: var(--text-muted); margin-top: 3px; }
.toolbar { display: flex; gap: 8px; margin-bottom: 14px; }
.dept-panel { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 14px 16px; margin-bottom: 14px; display: flex; flex-direction: column; gap: 8px; }
.dept-row { display: flex; align-items: center; gap: 10px; font-size: 13px; }
.dept-name { font-weight: 600; flex: 1; }
.dept-count { color: var(--text-muted); font-size: 12px; }
.dept-add-row { display: flex; gap: 8px; margin-top: 6px; }
.field-input-sm { font-size: 12.5px; padding: 5px 8px; border: 1px solid var(--border); border-radius: 6px; background: var(--bg); }
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

.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.4); display: flex; align-items: center; justify-content: center; z-index: 100; }
.modal { background: var(--surface); border-radius: 14px; padding: 24px; width: 420px; max-width: 90vw; display: flex; flex-direction: column; gap: 4px; }
.modal-title { font-size: 16px; font-weight: 700; margin-bottom: 10px; }
.field-label { font-size: 12.5px; font-weight: 600; color: var(--text-secondary); margin: 10px 0 4px; display: block; }
.field-hint { font-weight: 400; color: var(--text-muted); }
.field-input { width: 100%; padding: 8px 11px; border: 1px solid var(--border); border-radius: 8px; background: var(--bg); font-size: 13px; }
.checkbox-row { display: flex; align-items: center; gap: 8px; font-size: 13px; margin-top: 12px; }
.modal-actions { display: flex; justify-content: flex-end; gap: 8px; margin-top: 18px; }
</style>
