<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { adminApi } from '@/api'

// ── State ──────────────────────────────────────────────
const tab = ref<'modules' | 'paths'>('paths')
const paths = ref<any[]>([])
const allModules = ref<any[]>([])
const loading = ref(false)

// Drill-down
const selectedPath = ref<any>(null)
const tiers = ref<any[]>([])
const tierModules = ref<Record<number, any[]>>({})
const expandedTier = ref<number | null>(null)

// Modals
const showNewPath = ref(false)
const showNewTier = ref(false)
const showModuleEditor = ref(false)
const editingModule = ref<any>(null)
const editingTierId = ref<number | null>(null)

// Forms
const pathForm = ref({ name: '', description: '', audience: 'customer', icon: 'ti-user', color: 'purple', products: [] as string[], sort_order: 0 })
const tierForm = ref({ label: 'Foundation', name: '', cert_name: '', sort_order: 0 })
const moduleForm = ref({
  title: '', module_type: 'v', duration_mins: 0, product: 'vms',
  is_placeholder: false, sort_order: 0, description: '',
  learn_items: [] as string[], video_url: '', transcript: '', rich_content: '',
})
const newLearnItem = ref('')

// ── Load ───────────────────────────────────────────────
onMounted(loadAll)

async function loadAll() {
  loading.value = true
  try {
    const [pathsRes, modsRes] = await Promise.all([
      adminApi.listPaths(),
      import('@/api').then(m => m.modulesApi.browse()),
    ])
    paths.value = pathsRes.data
    allModules.value = modsRes.data
  } finally {
    loading.value = false
  }
}

async function openPath(path: any) {
  selectedPath.value = path
  const res = await adminApi.listTiers(path.id)
  tiers.value = res.data
  tierModules.value = {}
  for (const t of tiers.value) {
    const mr = await adminApi.listModules(t.id)
    tierModules.value[t.id] = mr.data
  }
  expandedTier.value = tiers.value[0]?.id ?? null
}

// ── Path CRUD ──────────────────────────────────────────
function openNewPath() {
  pathForm.value = { name: '', description: '', audience: 'customer', icon: 'ti-user', color: 'purple', products: [], sort_order: paths.value.length }
  showNewPath.value = true
}

async function savePath() {
  await adminApi.createPath(pathForm.value)
  showNewPath.value = false
  await loadAll()
}

async function deletePath(id: number) {
  if (!confirm('Delete this path and all its tiers?')) return
  await adminApi.deletePath(id)
  if (selectedPath.value?.id === id) selectedPath.value = null
  await loadAll()
}

// ── Tier CRUD ──────────────────────────────────────────
function openNewTier() {
  tierForm.value = { label: 'Foundation', name: '', cert_name: '', sort_order: tiers.value.length }
  showNewTier.value = true
}

async function saveTier() {
  await adminApi.createTier(selectedPath.value.id, tierForm.value)
  showNewTier.value = false
  await openPath(selectedPath.value)
}

async function deleteTier(id: number) {
  if (!confirm('Delete this tier and all its modules?')) return
  await adminApi.deleteTier(id)
  await openPath(selectedPath.value)
}

// ── Module CRUD ────────────────────────────────────────
function openNewModule(tierId: number) {
  editingModule.value = null
  editingTierId.value = tierId
  moduleForm.value = {
    title: '', module_type: 'v', duration_mins: 0, product: selectedPath.value?.products?.[0] ?? 'vms',
    is_placeholder: false, sort_order: (tierModules.value[tierId]?.length ?? 0),
    description: '', learn_items: [], video_url: '', transcript: '', rich_content: '',
  }
  newLearnItem.value = ''
  showModuleEditor.value = true
}

function openEditModule(mod: any, tierId: number) {
  editingModule.value = mod
  editingTierId.value = tierId
  moduleForm.value = {
    title: mod.title, module_type: mod.module_type, duration_mins: mod.duration_mins,
    product: mod.product, is_placeholder: mod.is_placeholder, sort_order: mod.sort_order,
    description: mod.description, learn_items: [...(mod.learn_items ?? [])],
    video_url: mod.video_url ?? '', transcript: mod.transcript ?? '', rich_content: mod.rich_content ?? '',
  }
  newLearnItem.value = ''
  showModuleEditor.value = true
}

function addLearnItem() {
  const v = newLearnItem.value.trim()
  if (v) { moduleForm.value.learn_items.push(v); newLearnItem.value = '' }
}

function removeLearnItem(i: number) { moduleForm.value.learn_items.splice(i, 1) }

async function saveModule() {
  const body = {
    ...moduleForm.value,
    video_url: moduleForm.value.video_url || null,
    transcript: moduleForm.value.transcript || null,
    rich_content: moduleForm.value.rich_content || null,
  }
  if (editingModule.value) {
    await adminApi.updateModule(editingModule.value.id, body)
  } else {
    await adminApi.createModule(editingTierId.value!, body)
  }
  showModuleEditor.value = false
  await openPath(selectedPath.value)
}

async function deleteModule(id: number) {
  if (!confirm('Delete this module?')) return
  await adminApi.deleteModule(id)
  await openPath(selectedPath.value)
}

// ── Helpers ────────────────────────────────────────────
const statusMock: Record<string, { label: string; bg: string; fg: string }> = {
  Published: { label: 'Published', bg: '#E2F6EC', fg: '#0E7E58' },
  Draft:     { label: 'Draft',     bg: '#F3F2F6', fg: '#A39EAE' },
  'In review':{ label: 'In review', bg: '#FBF1E3', fg: '#B26A00' },
}

function pathStatus(path: any) {
  // simple heuristic: no modules = Draft, else Published
  return path.mod_count === 0 ? statusMock['Draft'] : statusMock['Published']
}

function timeAgo(idx: number) {
  const opts = ['1 week ago','2 weeks ago','3 days ago','1 month ago','Yesterday','Today']
  return opts[idx % opts.length]
}

const prodLabel: Record<string, string> = { vms: 'Dataloy VMS', stream: 'Sedna Stream', cross: 'Cross-product' }
const typeLabel: Record<string, string> = { v: 'Video', a: 'Article', l: 'Link' }
const typeIcon:  Record<string, string> = { v: 'ti-player-play', a: 'ti-file-text', l: 'ti-link' }
const typeBg:   Record<string, string>  = { v: '#F1EBFE', a: '#FBF1E3', l: '#E3F4F9' }
const typeFg:   Record<string, string>  = { v: '#6E2BF0', a: '#B26A00', l: '#0B8FB0' }
</script>

<template>
  <div class="page">
    <!-- Header -->
    <div class="page-header">
      <div>
        <h1 class="page-title">Content management</h1>
        <p class="page-sub">Publish and edit modules, and manage the learning paths they belong to.</p>
      </div>
      <button v-if="tab === 'modules'" class="btn btn-primary" @click="tab = 'paths'">
        <i class="ti ti-plus" /> New module
      </button>
      <button v-else-if="!selectedPath" class="btn btn-primary" @click="openNewPath">
        <i class="ti ti-plus" /> New path
      </button>
      <div v-else class="header-actions">
        <button class="btn btn-ghost" @click="selectedPath = null">
          <i class="ti ti-arrow-left" /> Back to paths
        </button>
        <button class="btn btn-primary" @click="openNewTier">
          <i class="ti ti-plus" /> Add tier
        </button>
      </div>
    </div>

    <!-- Tabs -->
    <div class="tabs">
      <button class="tab" :class="{ active: tab === 'modules' }" @click="tab = 'modules'; selectedPath = null">Modules</button>
      <button class="tab" :class="{ active: tab === 'paths' }" @click="tab = 'paths'; selectedPath = null">Paths</button>
    </div>

    <!-- ── MODULES TAB ─────────────────────────────────── -->
    <template v-if="tab === 'modules'">
      <div class="table-wrap">
        <table class="data-table">
          <thead>
            <tr>
              <th>Module</th><th>Type</th><th>Product</th><th>Duration</th><th>Tier</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="m in allModules" :key="m.id">
              <td class="mod-title-cell">{{ m.title }}</td>
              <td><span class="pill" :style="{ background: typeBg[m.module_type], color: typeFg[m.module_type] }"><i :class="['ti', typeIcon[m.module_type]]" /> {{ typeLabel[m.module_type] ?? m.module_type }}</span></td>
              <td><span class="muted">{{ prodLabel[m.product] ?? m.product }}</span></td>
              <td class="muted">{{ m.duration_mins }} min</td>
              <td class="muted">Tier {{ m.tier_id }}</td>
            </tr>
            <tr v-if="!allModules.length"><td colspan="5" class="empty-row">No modules yet.</td></tr>
          </tbody>
        </table>
      </div>
    </template>

    <!-- ── PATHS TAB: list ─────────────────────────────── -->
    <template v-else-if="!selectedPath">
      <div class="table-wrap">
        <table class="data-table">
          <thead>
            <tr>
              <th>Path</th><th>Audience</th><th>Modules</th><th>Status</th><th>Last edited</th><th></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(p, i) in paths" :key="p.id" class="clickable-row" @click="openPath(p)">
              <td class="mod-title-cell">{{ p.name }}</td>
              <td><span class="audience-tag">{{ p.audience === 'internal' ? 'Internal' : 'Customer' }}</span></td>
              <td><span :class="['mod-count', p.mod_count > 0 ? 'has-mods' : '']">{{ p.mod_count }}</span></td>
              <td>
                <span class="status-pill" :style="{ background: pathStatus(p).bg, color: pathStatus(p).fg }">
                  {{ pathStatus(p).label }}
                </span>
              </td>
              <td class="muted">{{ timeAgo(i) }}</td>
              <td class="actions-cell" @click.stop>
                <button class="icon-btn" @click="deletePath(p.id)" title="Delete path"><i class="ti ti-trash" /></button>
              </td>
            </tr>
            <tr v-if="!paths.length"><td colspan="6" class="empty-row">No paths yet. Click "New path" to get started.</td></tr>
          </tbody>
        </table>
      </div>
    </template>

    <!-- ── PATHS TAB: drill-down ──────────────────────── -->
    <template v-else>
      <div class="path-detail">
        <div class="path-detail-header">
          <div class="path-name-badge">
            <i :class="['ti', selectedPath.icon]" />
            <div>
              <div class="path-detail-name">{{ selectedPath.name }}</div>
              <div class="path-detail-meta">{{ selectedPath.audience }} · {{ selectedPath.mod_count }} modules · {{ tiers.length }} tiers</div>
            </div>
          </div>
        </div>

        <!-- Tiers accordion -->
        <div v-for="tier in tiers" :key="tier.id" class="tier-block">
          <div class="tier-header" @click="expandedTier = expandedTier === tier.id ? null : tier.id">
            <div class="tier-header-left">
              <i :class="['ti', expandedTier === tier.id ? 'ti-chevron-down' : 'ti-chevron-right']" />
              <div>
                <span class="tier-label-tag">Tier {{ tier.sort_order + 1 }}</span>
                <span class="tier-name">{{ tier.name }}</span>
              </div>
            </div>
            <div class="tier-header-right">
              <span class="muted">{{ (tierModules[tier.id] ?? []).length }} modules · Earns: <strong>{{ tier.cert_name }}</strong></span>
              <button class="btn btn-primary btn-sm" @click.stop="openNewModule(tier.id)"><i class="ti ti-plus" /> Add module</button>
              <button class="icon-btn danger" @click.stop="deleteTier(tier.id)" title="Delete tier"><i class="ti ti-trash" /></button>
            </div>
          </div>

          <div v-if="expandedTier === tier.id" class="tier-modules">
            <div v-if="!(tierModules[tier.id]?.length)" class="tier-empty">
              No modules in this tier yet. <button class="link-btn" @click="openNewModule(tier.id)">Add the first one →</button>
            </div>
            <div v-for="mod in tierModules[tier.id]" :key="mod.id" class="module-row">
              <div class="module-row-left">
                <span class="mod-type-badge" :style="{ background: typeBg[mod.module_type], color: typeFg[mod.module_type] }">
                  <i :class="['ti', typeIcon[mod.module_type]]" />
                </span>
                <div>
                  <div class="mod-row-title">{{ mod.title }}</div>
                  <div class="mod-row-meta">{{ mod.duration_mins }} min · {{ prodLabel[mod.product] ?? mod.product }}</div>
                </div>
              </div>
              <div class="module-row-right">
                <button class="btn btn-ghost btn-sm" @click="openEditModule(mod, tier.id)"><i class="ti ti-pencil" /> Edit</button>
                <button class="icon-btn danger" @click="deleteModule(mod.id)" title="Delete module"><i class="ti ti-trash" /></button>
              </div>
            </div>
          </div>
        </div>

        <div v-if="!tiers.length" class="empty-state">
          No tiers yet. Click <strong>Add tier</strong> to build the path structure.
        </div>
      </div>
    </template>
  </div>

  <!-- ── NEW PATH MODAL ──────────────────────────────── -->
  <Teleport to="body">
    <div v-if="showNewPath" class="modal-backdrop" @click.self="showNewPath = false">
      <div class="modal">
        <div class="modal-head">
          <span class="modal-title">New learning path</span>
          <button class="icon-btn" @click="showNewPath = false"><i class="ti ti-x" /></button>
        </div>
        <div class="modal-body">
          <label class="field-label">Name *</label>
          <input v-model="pathForm.name" class="field-input" placeholder="e.g. Voyage Operator" />

          <label class="field-label">Description</label>
          <textarea v-model="pathForm.description" class="field-input field-textarea" placeholder="Who is this path for?" />

          <div class="form-row">
            <div>
              <label class="field-label">Audience</label>
              <select v-model="pathForm.audience" class="field-input">
                <option value="customer">Customer</option>
                <option value="internal">Internal</option>
              </select>
            </div>
            <div>
              <label class="field-label">Icon (Tabler)</label>
              <input v-model="pathForm.icon" class="field-input" placeholder="ti-ship" />
            </div>
          </div>

          <label class="field-label">Products</label>
          <div class="check-row">
            <label><input type="checkbox" value="vms" v-model="pathForm.products" /> Dataloy VMS</label>
            <label><input type="checkbox" value="stream" v-model="pathForm.products" /> Sedna Stream</label>
            <label><input type="checkbox" value="cross" v-model="pathForm.products" /> Cross-product</label>
          </div>
        </div>
        <div class="modal-foot">
          <button class="btn btn-ghost" @click="showNewPath = false">Cancel</button>
          <button class="btn btn-primary" :disabled="!pathForm.name" @click="savePath">Create path</button>
        </div>
      </div>
    </div>

    <!-- ── NEW TIER MODAL ────────────────────────────── -->
    <div v-if="showNewTier" class="modal-backdrop" @click.self="showNewTier = false">
      <div class="modal">
        <div class="modal-head">
          <span class="modal-title">Add tier to {{ selectedPath?.name }}</span>
          <button class="icon-btn" @click="showNewTier = false"><i class="ti ti-x" /></button>
        </div>
        <div class="modal-body">
          <label class="field-label">Tier level</label>
          <select v-model="tierForm.label" class="field-input">
            <option>Foundation</option>
            <option>Practitioner</option>
            <option>Professional</option>
            <option>Expert</option>
          </select>

          <label class="field-label">Full tier name *</label>
          <input v-model="tierForm.name" class="field-input" :placeholder="`e.g. ${selectedPath?.name} Foundation`" />

          <label class="field-label">Certificate name</label>
          <input v-model="tierForm.cert_name" class="field-input" placeholder="e.g. VMS Foundation Certificate" />
        </div>
        <div class="modal-foot">
          <button class="btn btn-ghost" @click="showNewTier = false">Cancel</button>
          <button class="btn btn-primary" :disabled="!tierForm.name" @click="saveTier">Add tier</button>
        </div>
      </div>
    </div>

    <!-- ── MODULE EDITOR MODAL ───────────────────────── -->
    <div v-if="showModuleEditor" class="modal-backdrop" @click.self="showModuleEditor = false">
      <div class="modal modal-wide">
        <div class="modal-head">
          <span class="modal-title">{{ editingModule ? 'Edit module' : 'New module' }}</span>
          <button class="icon-btn" @click="showModuleEditor = false"><i class="ti ti-x" /></button>
        </div>
        <div class="modal-body">
          <label class="field-label">Title *</label>
          <input v-model="moduleForm.title" class="field-input" placeholder="Module title" />

          <div class="form-row">
            <div>
              <label class="field-label">Content type</label>
              <div class="type-selector">
                <button
                  v-for="t in [{ v:'v', label:'Video', icon:'ti-player-play' }, { v:'a', label:'Article', icon:'ti-file-text' }, { v:'l', label:'Link', icon:'ti-link' }]"
                  :key="t.v"
                  class="type-btn"
                  :class="{ active: moduleForm.module_type === t.v }"
                  @click="moduleForm.module_type = t.v"
                >
                  <i :class="['ti', t.icon]" /> {{ t.label }}
                </button>
              </div>
            </div>
            <div>
              <label class="field-label">Product</label>
              <select v-model="moduleForm.product" class="field-input">
                <option value="vms">Dataloy VMS</option>
                <option value="stream">Sedna Stream</option>
                <option value="cross">Cross-product</option>
              </select>
            </div>
            <div>
              <label class="field-label">Duration (mins)</label>
              <input v-model.number="moduleForm.duration_mins" type="number" min="0" class="field-input" />
            </div>
          </div>

          <!-- Video URL -->
          <template v-if="moduleForm.module_type === 'v'">
            <label class="field-label">Video URL</label>
            <input v-model="moduleForm.video_url" class="field-input" placeholder="https://vimeo.com/... or YouTube embed URL" />
          </template>

          <!-- Link URL -->
          <template v-if="moduleForm.module_type === 'l'">
            <label class="field-label">Link URL *</label>
            <input v-model="moduleForm.video_url" class="field-input" placeholder="https://..." />
          </template>

          <label class="field-label">Description</label>
          <textarea v-model="moduleForm.description" class="field-input field-textarea" placeholder="What is this module about?" rows="3" />

          <!-- Article / rich text -->
          <template v-if="moduleForm.module_type === 'a'">
            <label class="field-label">Article content</label>
            <textarea v-model="moduleForm.rich_content" class="field-input field-textarea field-content" placeholder="Write your article content here (Markdown supported)…" rows="8" />
          </template>

          <!-- Transcript for videos -->
          <template v-if="moduleForm.module_type === 'v'">
            <label class="field-label">Transcript <span class="field-hint">(optional)</span></label>
            <textarea v-model="moduleForm.transcript" class="field-input field-textarea" placeholder="Paste transcript text…" rows="4" />
          </template>

          <label class="field-label">What learners will learn</label>
          <div class="learn-items-list">
            <div v-for="(item, i) in moduleForm.learn_items" :key="i" class="learn-item-row">
              <span>{{ item }}</span>
              <button class="icon-btn danger sm" @click="removeLearnItem(i)"><i class="ti ti-x" /></button>
            </div>
          </div>
          <div class="learn-item-add">
            <input v-model="newLearnItem" class="field-input" placeholder="Add a learning outcome…" @keydown.enter.prevent="addLearnItem" />
            <button class="btn btn-ghost btn-sm" @click="addLearnItem">Add</button>
          </div>
        </div>
        <div class="modal-foot">
          <button class="btn btn-ghost" @click="showModuleEditor = false">Cancel</button>
          <button class="btn btn-primary" :disabled="!moduleForm.title" @click="saveModule">
            {{ editingModule ? 'Save changes' : 'Create module' }}
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.page { padding: 20px 28px 48px; max-width: 1000px; margin: 0 auto; }
.page-header { display: flex; align-items: flex-start; justify-content: space-between; margin-bottom: 20px; gap: 16px; }
.page-title { font-size: 22px; font-weight: 800; letter-spacing: -0.4px; }
.page-sub { font-size: 13px; color: var(--text-muted); margin-top: 3px; }
.header-actions { display: flex; gap: 8px; }

/* Tabs */
.tabs { display: flex; gap: 4px; margin-bottom: 18px; }
.tab { padding: 6px 16px; border-radius: 8px; font-size: 13px; font-weight: 500; color: var(--text-secondary); border: 1px solid var(--border); background: var(--surface); cursor: pointer; }
.tab.active { background: var(--purple); color: #fff; border-color: var(--purple); font-weight: 600; }

/* Table */
.table-wrap { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); overflow: hidden; }
.data-table { width: 100%; border-collapse: collapse; font-size: 13px; }
th { padding: 10px 16px; text-align: left; font-size: 11px; font-weight: 700; color: var(--text-muted); letter-spacing: 0.5px; text-transform: uppercase; border-bottom: 1px solid var(--border); background: var(--bg); }
td { padding: 13px 16px; border-bottom: 1px solid var(--border); vertical-align: middle; }
tr:last-child td { border-bottom: none; }
.clickable-row { cursor: pointer; }
.clickable-row:hover td { background: var(--purple-subtle); }
.mod-title-cell { font-weight: 600; color: var(--text-primary); }
.muted { color: var(--text-muted); font-size: 12.5px; }
.empty-row { color: var(--text-muted); text-align: center; padding: 32px; }
.mod-count { font-size: 13px; font-weight: 700; color: var(--text-muted); }
.mod-count.has-mods { color: var(--purple); }
.audience-tag { font-size: 12.5px; color: var(--text-secondary); }
.status-pill { display: inline-flex; align-items: center; padding: 3px 10px; border-radius: 100px; font-size: 11.5px; font-weight: 600; }
.actions-cell { width: 40px; }

/* Buttons */
.btn-sm { font-size: 12px; padding: 5px 11px; }
.icon-btn { background: none; border: none; color: var(--text-muted); cursor: pointer; padding: 4px 6px; border-radius: 6px; font-size: 14px; }
.icon-btn:hover { color: var(--text-primary); background: var(--border); }
.icon-btn.danger:hover { color: #D32F2F; background: #FFEBEE; }
.link-btn { background: none; border: none; color: var(--purple); font-size: 13px; font-weight: 600; cursor: pointer; }

/* Path detail */
.path-detail { display: flex; flex-direction: column; gap: 12px; }
.path-detail-header { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 16px 20px; }
.path-name-badge { display: flex; align-items: center; gap: 14px; }
.path-name-badge > i { font-size: 24px; color: var(--purple); }
.path-detail-name { font-size: 16px; font-weight: 700; }
.path-detail-meta { font-size: 12.5px; color: var(--text-muted); margin-top: 2px; }

/* Tier block */
.tier-block { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); overflow: hidden; }
.tier-header { display: flex; align-items: center; justify-content: space-between; padding: 14px 18px; cursor: pointer; gap: 12px; }
.tier-header:hover { background: var(--purple-subtle); }
.tier-header-left { display: flex; align-items: center; gap: 10px; }
.tier-header-right { display: flex; align-items: center; gap: 10px; }
.tier-label-tag { font-size: 10.5px; font-weight: 700; letter-spacing: 0.6px; text-transform: uppercase; color: var(--purple); background: var(--purple-bg); padding: 2px 8px; border-radius: 20px; margin-right: 8px; }
.tier-name { font-size: 14px; font-weight: 600; }
.tier-modules { border-top: 1px solid var(--border); }
.tier-empty { padding: 16px 20px; font-size: 13px; color: var(--text-muted); }

/* Module rows */
.module-row { display: flex; align-items: center; justify-content: space-between; padding: 11px 18px; border-bottom: 1px solid var(--border); gap: 12px; }
.module-row:last-child { border-bottom: none; }
.module-row:hover { background: var(--purple-subtle); }
.module-row-left { display: flex; align-items: center; gap: 12px; }
.module-row-right { display: flex; align-items: center; gap: 8px; flex-shrink: 0; }
.mod-type-badge { width: 30px; height: 30px; border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 14px; flex-shrink: 0; }
.mod-row-title { font-size: 13px; font-weight: 500; }
.mod-row-meta { font-size: 11.5px; color: var(--text-muted); margin-top: 1px; }

.empty-state { padding: 40px; text-align: center; color: var(--text-muted); font-size: 13px; background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); }

/* ── Modals ──────────────────────────────────────────── */
.modal-backdrop {
  position: fixed; inset: 0; z-index: 1000;
  background: rgba(26,22,34,0.45); backdrop-filter: blur(2px);
  display: flex; align-items: center; justify-content: center; padding: 20px;
}
.modal {
  background: var(--surface); border-radius: 16px;
  box-shadow: 0 24px 64px rgba(26,22,34,0.22);
  width: 100%; max-width: 480px; display: flex; flex-direction: column;
  max-height: 90vh; overflow: hidden;
}
.modal-wide { max-width: 640px; }
.modal-head { display: flex; align-items: center; justify-content: space-between; padding: 20px 24px 16px; border-bottom: 1px solid var(--border); flex-shrink: 0; }
.modal-title { font-size: 16px; font-weight: 700; }
.modal-body { padding: 20px 24px; overflow-y: auto; display: flex; flex-direction: column; gap: 14px; }
.modal-foot { padding: 16px 24px; border-top: 1px solid var(--border); display: flex; justify-content: flex-end; gap: 8px; flex-shrink: 0; }

.field-label { font-size: 12.5px; font-weight: 600; color: var(--text-secondary); margin-bottom: 4px; display: block; }
.field-hint { font-weight: 400; color: var(--text-muted); }
.field-input {
  width: 100%; padding: 8px 11px; border: 1px solid var(--border);
  border-radius: 8px; font-size: 13.5px; font-family: inherit;
  background: var(--surface); color: var(--text-primary); outline: none;
}
.field-input:focus { border-color: var(--purple); box-shadow: 0 0 0 3px rgba(110,43,240,0.1); }
.field-textarea { resize: vertical; min-height: 72px; }
.field-content { min-height: 160px; font-family: monospace; font-size: 12.5px; }
.form-row { display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 12px; }

.check-row { display: flex; gap: 16px; }
.check-row label { display: flex; align-items: center; gap: 6px; font-size: 13px; cursor: pointer; }

.type-selector { display: flex; gap: 6px; }
.type-btn { padding: 6px 12px; border-radius: 8px; font-size: 12.5px; font-weight: 500; border: 1px solid var(--border); background: var(--surface); cursor: pointer; display: flex; align-items: center; gap: 5px; font-family: inherit; color: var(--text-secondary); }
.type-btn.active { background: var(--purple); color: #fff; border-color: var(--purple); font-weight: 600; }

.learn-items-list { display: flex; flex-direction: column; gap: 6px; }
.learn-item-row { display: flex; align-items: center; justify-content: space-between; padding: 7px 10px; background: var(--bg); border-radius: 8px; font-size: 13px; gap: 8px; }
.learn-item-add { display: flex; gap: 8px; }
.icon-btn.sm { padding: 2px 4px; font-size: 12px; }
</style>
