<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { webhooksApi } from '@/api'

const webhooks = ref<any[]>([])
const supportedEvents = ref<string[]>([])
const showAdd = ref(false)

const form = ref({ url: '', secret: '', events: [] as string[], is_active: true })

onMounted(async () => {
  const [hooksRes, eventsRes] = await Promise.all([webhooksApi.list(), webhooksApi.events()])
  webhooks.value = hooksRes.data
  supportedEvents.value = eventsRes.data
})

function openAdd() {
  form.value = { url: '', secret: '', events: [], is_active: true }
  showAdd.value = true
}

async function save() {
  await webhooksApi.create({ url: form.value.url, secret: form.value.secret || undefined, events: form.value.events })
  const { data } = await webhooksApi.list()
  webhooks.value = data
  showAdd.value = false
}

async function toggleActive(w: any) {
  await webhooksApi.update(w.id, { is_active: !w.is_active })
  const { data } = await webhooksApi.list()
  webhooks.value = data
}

async function remove(id: number) {
  if (!confirm('Remove this webhook? It will stop receiving events immediately.')) return
  await webhooksApi.delete(id)
  const { data } = await webhooksApi.list()
  webhooks.value = data
}

function maskUrl(url: string) {
  try {
    const u = new URL(url)
    return `${u.protocol}//${u.host}${u.pathname.slice(0, 12)}…`
  } catch {
    return url
  }
}
</script>

<template>
  <div class="page">
    <div class="page-header">
      <div>
        <h1 class="page-title">Integrations</h1>
        <p class="page-sub">Send Sedna Academy events to Slack, Discord, or any endpoint that accepts an incoming webhook.</p>
      </div>
      <button class="btn btn-primary" @click="openAdd">
        <i class="ti ti-plus" /> Add webhook
      </button>
    </div>

    <div class="hint-card">
      <i class="ti ti-brand-slack" />
      <div>
        <strong>Using Slack?</strong> Create an
        <a href="https://api.slack.com/messaging/webhooks" target="_blank" rel="noopener">Incoming Webhook</a>
        in your Slack workspace and paste the URL below — no other setup needed.
      </div>
    </div>

    <div class="table-wrap">
      <table class="table">
        <thead>
          <tr>
            <th>Endpoint</th>
            <th>Events</th>
            <th>Status</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="w in webhooks" :key="w.id">
            <td class="mono">{{ maskUrl(w.url) }}</td>
            <td>
              <span v-for="e in w.events" :key="e" class="event-badge">{{ e }}</span>
            </td>
            <td>
              <button class="status-toggle" :class="{ active: w.is_active }" @click="toggleActive(w)">
                {{ w.is_active ? 'Active' : 'Paused' }}
              </button>
            </td>
            <td class="actions-cell">
              <button class="icon-btn danger" @click="remove(w.id)" title="Remove"><i class="ti ti-trash" /></button>
            </td>
          </tr>
          <tr v-if="!webhooks.length">
            <td colspan="4" class="empty-row">No webhooks configured yet. Click "Add webhook" to connect Slack or another endpoint.</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Add webhook modal -->
    <div v-if="showAdd" class="modal-overlay" @click.self="showAdd = false">
      <div class="modal">
        <h2 class="modal-title">Add webhook</h2>
        <div class="field">
          <label class="label">URL</label>
          <input v-model="form.url" class="input" placeholder="https://hooks.slack.com/services/..." />
        </div>
        <div class="field">
          <label class="label">Secret <span class="hint">(optional — signs each request with HMAC-SHA256)</span></label>
          <input v-model="form.secret" class="input" placeholder="Leave blank to skip signing" />
        </div>
        <div class="field">
          <label class="label">Events</label>
          <div class="event-check-list">
            <label v-for="e in supportedEvents" :key="e" class="event-check">
              <input type="checkbox" :value="e" v-model="form.events" /> {{ e }}
            </label>
          </div>
        </div>
        <div class="modal-actions">
          <button class="btn btn-ghost" @click="showAdd = false">Cancel</button>
          <button class="btn btn-primary" :disabled="!form.url || !form.events.length" @click="save">Add webhook</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.page { padding: 28px 32px; max-width: 900px; margin: 0 auto; }
.page-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 20px; gap: 16px; }
.page-title { font-size: 22px; font-weight: 800; letter-spacing: -0.4px; }
.page-sub { font-size: 13px; color: var(--text-muted); margin-top: 3px; max-width: 480px; }

.hint-card {
  display: flex; align-items: flex-start; gap: 12px;
  background: var(--purple-subtle); border-radius: 10px;
  padding: 14px 16px; margin-bottom: 20px;
  font-size: 13px; color: var(--text-secondary); line-height: 1.5;
}
.hint-card > i { font-size: 20px; color: var(--purple); flex-shrink: 0; margin-top: 1px; }
.hint-card a { color: var(--purple); font-weight: 600; }

.table-wrap { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); overflow: hidden; }
.table { width: 100%; border-collapse: collapse; font-size: 13px; }
th { padding: 12px 16px; text-align: left; font-size: 11.5px; font-weight: 700; color: var(--text-muted); border-bottom: 1px solid var(--border); background: var(--bg); }
td { padding: 13px 16px; border-bottom: 1px solid var(--border); vertical-align: middle; color: var(--text-secondary); }
tr:last-child td { border-bottom: none; }
.mono { font-family: monospace; font-size: 12.5px; }
.empty-row { color: var(--text-muted); text-align: center; padding: 32px; }
.actions-cell { width: 40px; }

.event-badge {
  display: inline-block; font-size: 10.5px; font-weight: 600;
  background: var(--purple-subtle); color: var(--purple);
  padding: 2px 8px; border-radius: 100px; margin: 2px 4px 2px 0;
}

.status-toggle {
  font-size: 11px; font-weight: 600; padding: 3px 10px; border-radius: 100px;
  border: none; cursor: pointer; background: #F3F2F6; color: var(--text-muted);
}
.status-toggle.active { background: var(--green-bg); color: var(--green); }

.icon-btn { background: none; border: none; color: var(--text-muted); cursor: pointer; padding: 4px 6px; border-radius: 6px; font-size: 14px; }
.icon-btn.danger:hover { color: #D32F2F; background: #FFEBEE; }

.modal-overlay { position: fixed; inset: 0; background: rgba(26,22,34,0.4); display: flex; align-items: center; justify-content: center; z-index: 100; }
.modal { background: var(--surface); border-radius: 14px; padding: 28px; width: 440px; display: flex; flex-direction: column; gap: 16px; box-shadow: 0 24px 64px rgba(26,22,34,0.2); max-height: 85vh; overflow-y: auto; }
.modal-title { font-size: 17px; font-weight: 800; }
.field { display: flex; flex-direction: column; gap: 6px; }
.label { font-size: 13px; font-weight: 600; color: var(--text-secondary); }
.hint { font-weight: 400; color: var(--text-muted); }
.input { padding: 9px 12px; border: 1px solid var(--border); border-radius: 8px; font-size: 14px; outline: none; }
.input:focus { border-color: var(--purple); }
.event-check-list { display: flex; flex-direction: column; gap: 8px; }
.event-check { display: flex; align-items: center; gap: 8px; font-size: 13px; font-family: monospace; cursor: pointer; }
.modal-actions { display: flex; gap: 8px; justify-content: flex-end; margin-top: 4px; }
</style>
