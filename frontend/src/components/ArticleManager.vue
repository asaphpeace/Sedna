<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { articlesApi } from '@/api'

// Knowledge Base and Help Center articles: Sedna admins write, review and
// publish them here. Published articles are public on the Hub.
const articles = ref<any[]>([])
const loading = ref(true)

async function load() {
  loading.value = true
  try {
    articles.value = (await articlesApi.list()).data
  } finally {
    loading.value = false
  }
}
onMounted(load)

const blank = () => ({
  title: '', slug: '', summary: '', section: 'knowledge-base', kind: 'How-to', product: 'vms',
  topic: '', body: '', related_path_id: null, is_published: false, is_sample: false, sort_order: 0,
})
const editing = ref<any>(null)
const form = ref<any>(blank())
const saving = ref(false)
const error = ref('')

function openNew() {
  editing.value = { id: null }
  form.value = blank()
  error.value = ''
}
function openEdit(a: any) {
  editing.value = a
  const { id, updated_at, ...rest } = a
  form.value = { ...blank(), ...rest }
  error.value = ''
}

async function save() {
  saving.value = true
  error.value = ''
  try {
    if (editing.value.id) await articlesApi.update(editing.value.id, form.value)
    else await articlesApi.create(form.value)
    editing.value = null
    await load()
  } catch (e: any) {
    const d = e?.response?.data?.detail
    error.value = typeof d === 'string' ? d : 'Check the title and fields, then try again.'
  } finally {
    saving.value = false
  }
}

async function togglePublish(a: any) {
  const { id, updated_at, ...rest } = a
  await articlesApi.update(id, { ...rest, is_published: !a.is_published })
  await load()
}

async function remove(a: any) {
  if (!confirm(`Delete "${a.title}"? This can't be undone.`)) return
  await articlesApi.remove(a.id)
  await load()
}

const sectionLabel = (s: string) => s === 'help-center' ? 'Help Center' : 'Knowledge Base'
const status = (a: any) => !a.is_published ? 'Draft' : a.is_sample ? 'Published · sample' : 'Published'
const sorted = computed(() => [...articles.value].sort((a, b) =>
  a.section.localeCompare(b.section) || a.sort_order - b.sort_order || a.title.localeCompare(b.title)))
</script>

<template>
  <div class="am">
    <div class="am-bar">
      <p class="muted">Articles appear on the public Knowledge Base and Help Center once published. Untick “sample” after Support has checked one.</p>
      <button class="btn btn-primary" @click="openNew"><i class="ti ti-plus" /> New article</button>
    </div>

    <div class="table-wrap">
      <table class="data-table">
        <thead><tr><th>Article</th><th>Section</th><th>Type</th><th>Status</th><th /></tr></thead>
        <tbody>
          <tr v-for="a in sorted" :key="a.id">
            <td class="mod-title-cell">
              <button class="link-title" @click="openEdit(a)">{{ a.title }}</button>
              <div class="muted small">{{ a.topic || 'No topic' }}</div>
            </td>
            <td>{{ sectionLabel(a.section) }}</td>
            <td>{{ a.kind }}</td>
            <td><span class="status" :class="{ draft: !a.is_published, sample: a.is_published && a.is_sample }">{{ status(a) }}</span></td>
            <td class="actions">
              <a v-if="a.is_published" :href="`/help/${a.slug}`" target="_blank" rel="noopener" class="btn btn-ghost btn-sm"><i class="ti ti-eye" /> View</a>
              <button class="btn btn-ghost btn-sm" @click="togglePublish(a)">{{ a.is_published ? 'Unpublish' : 'Publish' }}</button>
              <button class="icon-btn danger" title="Delete article" @click="remove(a)"><i class="ti ti-trash" /></button>
            </td>
          </tr>
          <tr v-if="!loading && !articles.length"><td colspan="5" class="empty-row">No articles yet. Click "New article" to write the first one.</td></tr>
        </tbody>
      </table>
    </div>

    <Teleport to="body">
      <div v-if="editing" class="modal-backdrop" @click.self="editing = null">
        <div class="modal am-modal" role="dialog" aria-modal="true" aria-labelledby="am-title">
          <div class="modal-head">
            <span id="am-title" class="modal-title">{{ editing.id ? 'Edit article' : 'New article' }}</span>
            <button class="icon-btn" aria-label="Close" @click="editing = null"><i class="ti ti-x" /></button>
          </div>
          <div class="modal-body">
            <label class="field-label" for="am-t">Title *</label>
            <input id="am-t" v-model="form.title" class="field-input" placeholder="e.g. Freight still shows as pending after invoicing" />

            <label class="field-label" for="am-s">This is for you if…</label>
            <input id="am-s" v-model="form.summary" class="field-input" placeholder="One sentence describing the reader's situation" />

            <div class="form-row">
              <div>
                <label class="field-label" for="am-sec">Section</label>
                <select id="am-sec" v-model="form.section" class="field-input">
                  <option value="knowledge-base">Knowledge Base</option>
                  <option value="help-center">Help Center</option>
                </select>
              </div>
              <div>
                <label class="field-label" for="am-k">Type</label>
                <select id="am-k" v-model="form.kind" class="field-input">
                  <option>How-to</option><option>Explainer</option><option>Troubleshooting</option><option>Process</option>
                </select>
              </div>
              <div>
                <label class="field-label" for="am-top">Topic</label>
                <input id="am-top" v-model="form.topic" class="field-input" placeholder="e.g. Bunkers" />
              </div>
            </div>

            <label class="field-label" for="am-b">Article (Markdown)</label>
            <textarea id="am-b" v-model="form.body" class="field-input am-body" placeholder="## Check these first&#10;&#10;1. …" />
            <p class="muted small">Use ## for headings and “&gt; [!TIP]” for a highlighted tip.</p>

            <div class="checks">
              <label><input v-model="form.is_published" type="checkbox" /> Published (public on the Hub)</label>
              <label><input v-model="form.is_sample" type="checkbox" /> Sample, under review (shows a label to readers)</label>
            </div>
            <p v-if="error" class="error">{{ error }}</p>
          </div>
          <div class="modal-foot">
            <button class="btn btn-ghost" @click="editing = null">Cancel</button>
            <button class="btn btn-primary" :disabled="!form.title || saving" @click="save">{{ editing.id ? 'Save changes' : 'Create article' }}</button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<style scoped>
.am { display: flex; flex-direction: column; gap: 16px; }
.am-bar { display: flex; align-items: center; justify-content: space-between; gap: 16px; flex-wrap: wrap; }
.am-bar p { margin: 0; max-width: 620px; }
.muted { color: var(--text-secondary); font-size: 14px; }
.small { font-size: 13px; }
.link-title { background: none; border: none; padding: 0; font: inherit; font-weight: 500; color: var(--text-primary); cursor: pointer; text-align: left; }
.link-title:hover { color: var(--purple); }
.status { font-size: 12.5px; padding: 3px 10px; border-radius: 100px; background: #D3F4DE; color: #1F8A5B; white-space: nowrap; }
.status.draft { background: #F1F2F4; color: #6B6C75; }
.status.sample { background: #FBEDC8; color: #633806; }
.actions { display: flex; gap: 6px; justify-content: flex-end; align-items: center; flex-wrap: wrap; }
.am-modal { width: 760px; max-width: calc(100vw - 32px); }
.am-body { min-height: 300px; font-family: var(--font-mono); font-size: 13px; line-height: 1.6; }
.checks { display: flex; flex-direction: column; gap: 8px; font-size: 14px; margin-top: 8px; }
.checks label { display: flex; gap: 8px; align-items: center; min-height: 32px; }
.error { color: #B0322B; font-size: 14px; }
</style>
