<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { teamApi } from '@/api'

const users = ref<any[]>([])
const showInvite = ref(false)
const inviteEmail = ref('')
const inviteName = ref('')
const inviteRole = ref('')

onMounted(async () => {
  const { data } = await teamApi.list()
  users.value = data
})

async function invite() {
  await teamApi.invite({ email: inviteEmail.value, name: inviteName.value, role: inviteRole.value || undefined })
  const { data } = await teamApi.list()
  users.value = data
  showInvite.value = false
  inviteEmail.value = ''
  inviteName.value = ''
  inviteRole.value = ''
}

// ── Edit existing user ───────────────────────────────────
const editingUser = ref<any>(null)
const editForm = ref({ name: '', role: '', status: 'active', is_admin: false })

function openEdit(u: any) {
  editingUser.value = u
  editForm.value = { name: u.name, role: u.role ?? '', status: u.status, is_admin: u.is_admin }
}

async function saveEdit() {
  await teamApi.update(editingUser.value.id, {
    name: editForm.value.name,
    role: editForm.value.role || null,
    status: editForm.value.status,
    is_admin: editForm.value.is_admin,
  })
  const { data } = await teamApi.list()
  users.value = data
  editingUser.value = null
}
</script>

<template>
  <div class="page">
    <div class="page-header">
      <div>
        <h1 class="page-title">User Management</h1>
        <p class="page-sub">{{ users.filter(u => u.status === 'active').length }} active · {{ users.length }} total</p>
      </div>
      <button class="btn btn-primary" @click="showInvite = true">
        <i class="ti ti-user-plus" /> Invite user
      </button>
    </div>

    <!-- Invite modal -->
    <div v-if="showInvite" class="modal-overlay" @click.self="showInvite = false">
      <div class="modal">
        <h2 class="modal-title">Invite user</h2>
        <div class="field">
          <label class="label">Name</label>
          <input v-model="inviteName" class="input" placeholder="Full name" />
        </div>
        <div class="field">
          <label class="label">Email</label>
          <input v-model="inviteEmail" class="input" type="email" placeholder="email@company.com" />
        </div>
        <div class="field">
          <label class="label">Role (optional)</label>
          <input v-model="inviteRole" class="input" placeholder="e.g. Voyage Operator" />
        </div>
        <div class="modal-actions">
          <button class="btn btn-ghost" @click="showInvite = false">Cancel</button>
          <button class="btn btn-primary" @click="invite">Send invite</button>
        </div>
      </div>
    </div>

    <div class="table-wrap">
      <table class="users-table">
        <thead>
          <tr>
            <th>User</th>
            <th>Role</th>
            <th>Paths</th>
            <th>Status</th>
            <th>Last active</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="u in users" :key="u.id">
            <td>
              <div class="member-cell">
                <div class="avatar" :style="{ background: u.color, width: '32px', height: '32px', fontSize: '13px' }">{{ u.initial }}</div>
                <div>
                  <div class="member-name">{{ u.name }}
                    <span v-if="u.is_admin" class="admin-badge">Admin</span>
                  </div>
                  <div class="member-email">{{ u.email }}</div>
                </div>
              </div>
            </td>
            <td>{{ u.role ?? '—' }}</td>
            <td>{{ u.paths ?? 0 }}</td>
            <td>
              <span class="status-pill" :style="{
                background: u.status === 'active' ? 'var(--green-bg)' : u.status === 'invited' ? '#FBF1E3' : '#F3F2F6',
                color: u.status === 'active' ? 'var(--green)' : u.status === 'invited' ? 'var(--orange)' : 'var(--text-muted)',
              }">{{ u.status }}</span>
            </td>
            <td class="muted">{{ u.last_active_at ? new Date(u.last_active_at).toLocaleDateString() : '—' }}</td>
            <td>
              <button class="btn btn-ghost btn-sm" @click="openEdit(u)"><i class="ti ti-pencil" /> Edit</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Edit user modal -->
    <div v-if="editingUser" class="modal-overlay" @click.self="editingUser = null">
      <div class="modal">
        <h2 class="modal-title">Edit {{ editingUser.name }}</h2>
        <div class="field">
          <label class="label">Name</label>
          <input v-model="editForm.name" class="input" placeholder="Full name" />
        </div>
        <div class="field">
          <label class="label">Role</label>
          <input v-model="editForm.role" class="input" placeholder="e.g. Voyage Operator" />
        </div>
        <div class="field">
          <label class="label">Status</label>
          <select v-model="editForm.status" class="input">
            <option value="active">Active</option>
            <option value="invited">Invited</option>
            <option value="inactive">Inactive</option>
          </select>
        </div>
        <div class="field">
          <label class="checkbox-label">
            <input type="checkbox" v-model="editForm.is_admin" />
            Admin — can manage content, users, and settings
          </label>
        </div>
        <div class="modal-actions">
          <button class="btn btn-ghost" @click="editingUser = null">Cancel</button>
          <button class="btn btn-primary" :disabled="!editForm.name" @click="saveEdit">Save changes</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.page { padding: 28px 32px; max-width: 900px; margin: 0 auto; }
.page-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 20px; }
.page-title { font-size: 22px; font-weight: 800; letter-spacing: -0.4px; }
.page-sub { font-size: 13px; color: var(--text-muted); margin-top: 3px; }
.table-wrap { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); overflow: hidden; }
.users-table { width: 100%; border-collapse: collapse; font-size: 13px; }
th { padding: 12px 16px; text-align: left; font-size: 11.5px; font-weight: 700; color: var(--text-muted); border-bottom: 1px solid var(--border); background: var(--bg); }
td { padding: 13px 16px; border-bottom: 1px solid var(--border); vertical-align: middle; color: var(--text-secondary); }
tr:last-child td { border-bottom: none; }
tr:hover td { background: var(--purple-subtle); }
.member-cell { display: flex; align-items: center; gap: 10px; }
.member-name { font-weight: 600; color: var(--text-primary); }
.member-email { font-size: 11.5px; color: var(--text-muted); }
.status-pill { font-size: 11px; font-weight: 600; padding: 3px 9px; border-radius: 100px; }
.muted { color: var(--text-muted); }
/* Modal */
.modal-overlay { position: fixed; inset: 0; background: rgba(26,22,34,0.4); display: flex; align-items: center; justify-content: center; z-index: 100; }
.modal { background: var(--surface); border-radius: 14px; padding: 28px; width: 400px; display: flex; flex-direction: column; gap: 16px; box-shadow: 0 24px 64px rgba(26,22,34,0.2); }
.modal-title { font-size: 17px; font-weight: 800; }
.field { display: flex; flex-direction: column; gap: 6px; }
.label { font-size: 13px; font-weight: 600; color: var(--text-secondary); }
.input { padding: 9px 12px; border: 1px solid var(--border); border-radius: 8px; font-size: 14px; outline: none; }
.input:focus { border-color: var(--purple); }
.modal-actions { display: flex; gap: 8px; justify-content: flex-end; margin-top: 4px; }
.admin-badge { font-size: 10px; font-weight: 700; color: var(--purple); background: var(--purple-subtle); padding: 2px 7px; border-radius: 100px; margin-left: 6px; vertical-align: middle; }
.checkbox-label { display: flex; align-items: center; gap: 8px; font-size: 13px; color: var(--text-secondary); cursor: pointer; }
</style>
