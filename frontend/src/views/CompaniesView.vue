<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { companiesApi } from '@/api'
import RemovePersonDialog from '@/components/RemovePersonDialog.vue'
import { useAuthStore } from '@/stores/auth'

// Sedna admins set up customer companies and invite their people. Each
// company only ever sees itself; its own admin manages it from Users.
const auth = useAuthStore()
const companies = ref<any[]>([])
const selected = ref<any>(null)
const people = ref<any[]>([])
const loadingPeople = ref(false)

async function loadCompanies() {
  const { data } = await companiesApi.list()
  companies.value = data
  if (selected.value) selected.value = data.find((c: any) => c.id === selected.value.id) ?? null
}
onMounted(loadCompanies)

async function open(c: any) {
  selected.value = c
  loadingPeople.value = true
  try {
    people.value = (await companiesApi.users(c.id)).data
  } finally {
    loadingPeople.value = false
  }
}

// ── Add a company ─────────────────────────────────────────
const adding = ref(false)
const newName = ref('')
const addError = ref('')
async function addCompany() {
  addError.value = ''
  try {
    const { data } = await companiesApi.create(newName.value.trim())
    adding.value = false
    newName.value = ''
    await loadCompanies()
    await open(companies.value.find(c => c.id === data.id))
  } catch (e: any) {
    addError.value = e?.response?.data?.detail ?? "That company couldn't be added."
  }
}

// ── Invite someone ────────────────────────────────────────
const invite = ref({ email: '', name: '', role: '', is_admin: false })
const inviting = ref(false)
const inviteError = ref('')
const invited = ref('')
async function sendInvite() {
  inviteError.value = ''
  invited.value = ''
  inviting.value = true
  try {
    await companiesApi.invite(selected.value.id, { ...invite.value, role: invite.value.role || undefined })
    invited.value = `Invite sent to ${invite.value.email}.`
    invite.value = { email: '', name: '', role: '', is_admin: false }
    await open(selected.value)
    await loadCompanies()
  } catch (e: any) {
    const d = e?.response?.data?.detail
    inviteError.value = typeof d === 'string' ? d : 'Check the email address and name, then try again.'
  } finally {
    inviting.value = false
  }
}

// ── Remove on request ─────────────────────────────────────
const removing = ref<any>(null)
async function afterRemove() {
  removing.value = null
  await open(selected.value)
  await loadCompanies()
}
</script>

<template>
  <div class="page">
    <div class="page-header head-row">
      <div>
        <h1 class="page-title">Companies</h1>
        <p class="page-sub">Set up customer companies and invite their people. Each company sees only its own learners.</p>
      </div>
      <button class="btn btn-primary" @click="adding = true"><i class="ti ti-plus" /> Add company</button>
    </div>

    <form v-if="adding" class="card add" @submit.prevent="addCompany">
      <label class="field">
        <span class="label">Company name</span>
        <input v-model="newName" class="input" placeholder="e.g. Aldermoor Tankers" required minlength="2" />
      </label>
      <p v-if="addError" class="error">{{ addError }}</p>
      <div class="actions">
        <button type="button" class="btn btn-ghost" @click="adding = false; addError = ''">Cancel</button>
        <button type="submit" class="btn btn-primary" :disabled="newName.trim().length < 2">Add company</button>
      </div>
    </form>

    <div class="card table-card">
      <div class="table-wrap">
        <table>
          <thead><tr><th>Company</th><th>Type</th><th class="num">People</th><th class="num">Admins</th><th /></tr></thead>
          <tbody>
            <tr v-for="c in companies" :key="c.id" :class="{ current: selected?.id === c.id }" @click="open(c)">
              <td><button class="row-link" @click.stop="open(c)">{{ c.name }}</button></td>
              <td><span class="tag" :class="c.kind">{{ c.kind === 'sedna' ? 'Sedna staff' : 'Customer' }}</span></td>
              <td class="num">{{ c.people }}</td>
              <td class="num">{{ c.admins }}</td>
              <td class="num chev"><i class="ti ti-chevron-right" /></td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <section v-if="selected" class="card company" aria-labelledby="company-h">
      <h2 id="company-h" class="company-h">{{ selected.name }}</h2>

      <form class="invite" @submit.prevent="sendInvite">
        <h3 class="sub-h">Invite someone</h3>
        <div class="invite-fields">
          <label class="field">
            <span class="label">Email</span>
            <input v-model="invite.email" type="email" class="input" required />
          </label>
          <label class="field">
            <span class="label">Name</span>
            <input v-model="invite.name" class="input" required />
          </label>
          <label class="field">
            <span class="label">Role <span class="muted">(optional)</span></span>
            <input v-model="invite.role" class="input" placeholder="e.g. Operator" />
          </label>
        </div>
        <label class="check">
          <input v-model="invite.is_admin" type="checkbox" />
          <span>
            Company admin
            <span class="muted">— {{ selected.kind === 'sedna' ? 'can manage content, people and settings' : 'can invite and manage people in ' + selected.name }}</span>
          </span>
        </label>
        <p v-if="inviteError" class="error">{{ inviteError }}</p>
        <p v-if="invited" class="ok" role="status">{{ invited }}</p>
        <div class="actions">
          <button type="submit" class="btn btn-primary" :disabled="inviting || !invite.email || !invite.name">Send invite</button>
        </div>
      </form>

      <h3 class="sub-h">People</h3>
      <div class="table-wrap">
        <table>
          <thead><tr><th>Name</th><th>Email</th><th>Access</th><th>Status</th><th /></tr></thead>
          <tbody>
            <tr v-for="p in people" :key="p.id">
              <td>{{ p.name }}</td>
              <td class="muted">{{ p.email }}</td>
              <td>{{ p.is_admin ? 'Admin' : 'Learner' }}</td>
              <td><span class="status" :class="p.status">{{ p.status === 'active' ? 'Active' : p.status === 'invited' ? 'Invited' : 'Inactive' }}</span></td>
              <td class="num">
                <button v-if="p.id !== auth.user?.id" class="btn btn-ghost btn-sm" @click="removing = p">Remove</button>
              </td>
            </tr>
            <tr v-if="!loadingPeople && !people.length"><td colspan="5" class="empty">Nobody here yet. Invite their first admin above.</td></tr>
          </tbody>
        </table>
      </div>
    </section>

    <RemovePersonDialog v-if="removing" :person="removing" @close="removing = null" @removed="afterRemove" />
  </div>
</template>

<style scoped>
.page { padding: 40px 24px 72px; max-width: var(--content-max); margin: 0 auto; display: flex; flex-direction: column; gap: 16px; }
.head-row { display: flex; align-items: flex-end; justify-content: space-between; gap: 16px; flex-wrap: wrap; margin-bottom: 8px; }
.add { display: flex; flex-direction: column; gap: 12px; max-width: 520px; }
.field { display: flex; flex-direction: column; gap: 6px; flex: 1 1 200px; }
.label { font-size: 14px; color: var(--text-secondary); }
.actions { display: flex; gap: 8px; justify-content: flex-end; flex-wrap: wrap; }
.error { font-size: 14px; color: #B0322B; }
.ok { font-size: 14px; color: #1F8A5B; }
.muted { color: var(--text-secondary); }

.table-card { padding: 8px 0; }
.table-wrap { overflow-x: auto; }
table { width: 100%; border-collapse: collapse; font-size: 15px; }
th { text-align: left; font-weight: 500; color: var(--text-secondary); font-size: 13px; padding: 10px 16px; border-bottom: 1px solid var(--border); white-space: nowrap; }
td { padding: 12px 16px; border-bottom: 1px solid var(--border); }
tr:last-child td { border-bottom: none; }
tbody tr { cursor: pointer; }
.company tbody tr { cursor: default; }
tbody tr:hover, tr.current { background: #FAFAF8; }
tr.current .row-link { color: var(--purple); }
.num { text-align: right; white-space: nowrap; }
.chev { color: var(--text-secondary); }
.row-link { background: none; border: none; padding: 0; font: inherit; color: var(--text-primary); cursor: pointer; text-align: left; min-height: 32px; }
.tag { font-size: 12px; padding: 2px 8px; border-radius: 4px; white-space: nowrap; }
.tag.sedna { background: #ECDEFE; color: #4B1FA8; }
.tag.customer { background: #C5D9FE; color: #1E3A8A; }
.status { font-size: 12px; padding: 2px 8px; border-radius: 4px; background: #F1F2F4; color: #3A3B42; }
.status.active { background: #D3F4DE; color: #1F6B45; }
.status.invited { background: #FBEDC8; color: #633806; }
.empty { color: var(--text-secondary); text-align: center; padding: 24px; }

.company { display: flex; flex-direction: column; gap: 16px; }
.company-h { font-size: 24px; font-weight: 500; }
.sub-h { font-size: 15px; font-weight: 500; }
.invite { display: flex; flex-direction: column; gap: 12px; padding-bottom: 20px; border-bottom: 1px solid var(--border); }
.invite-fields { display: flex; gap: 12px; flex-wrap: wrap; }
.check { display: flex; gap: 10px; align-items: flex-start; font-size: 14px; min-height: 44px; }
.check input { margin-top: 3px; }
</style>
