<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { analyticsApi } from '@/api'

// Learning impact: Nassia's Reach and Health view across every company.
// The smallest unit of value is a completed lesson.
const period = ref('quarter')
const audience = ref('all')
const orgId = ref<string>('')
const product = ref<string>('')

const data = ref<any>(null)
const loading = ref(true)
const failed = ref(false)

async function load() {
  loading.value = true
  failed.value = false
  try {
    const res = await analyticsApi.impact({
      period: period.value,
      audience: audience.value,
      org_id: orgId.value || undefined,
      product: product.value || undefined,
    })
    data.value = res.data
  } catch {
    failed.value = true
  } finally {
    loading.value = false
  }
}
onMounted(load)
watch([period, audience, orgId, product], load)

const fmtDate = (iso: string) => new Date(iso + 'T00:00:00').toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })
const range = computed(() => data.value
  ? `${fmtDate(data.value.period.start)} – ${fmtDate(data.value.period.end)}, compared with ${fmtDate(data.value.period.previous_start)} – ${fmtDate(data.value.period.previous_end)}`
  : '')

function fmtTime(mins: number): string {
  if (!mins) return '0 h'
  if (mins < 60) return `${mins} min`
  const h = mins / 60
  return `${h < 10 ? h.toFixed(1) : Math.round(h)} h`
}

function change(m: { value: number; previous: number }): { text: string; dir: 'up' | 'down' | 'flat' } {
  if (m.value === m.previous) return { text: 'No change', dir: 'flat' }
  if (!m.previous) return { text: 'New this period', dir: 'up' }
  const pct = Math.round(((m.value - m.previous) / m.previous) * 100)
  return { text: `${pct > 0 ? '▲' : '▼'} ${Math.abs(pct)}% vs previous`, dir: pct > 0 ? 'up' : 'down' }
}

const cards = computed(() => {
  if (!data.value) return []
  const h = data.value.headline
  return [
    { key: 'people', value: h.people.value, label: 'People who completed a lesson', change: change(h.people) },
    { key: 'lessons', value: h.lessons.value, label: 'Lessons completed', change: change(h.lessons) },
    {
      key: 'time', value: fmtTime(h.tracked_minutes.value), label: 'Time spent learning', change: change(h.tracked_minutes),
      note: `≈ ${fmtTime(h.estimated_minutes.value)} by lesson length`,
    },
    { key: 'certs', value: h.certificates.value, label: 'Certificates issued', change: change(h.certificates) },
    { key: 'active', value: h.active.value, label: 'Active learners', change: change(h.active) },
  ]
})

const trendMax = computed(() => Math.max(1, ...(data.value?.trend ?? []).map((t: any) => t.staff + t.customer)))
const monthLabel = (m: string) => new Date(m + '-01T00:00:00').toLocaleDateString('en-GB', { month: 'short' })

// ── CSV export ───────────────────────────────────────────
function download(name: string, header: string[], rows: (string | number | null)[][]) {
  const esc = (v: string | number | null) => {
    const s = v == null ? '' : String(v)
    return /[",\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s
  }
  const csv = [header, ...rows].map(r => r.map(esc).join(',')).join('\n')
  const url = URL.createObjectURL(new Blob([csv], { type: 'text/csv' }))
  const a = Object.assign(document.createElement('a'), { href: url, download: `${name}-${data.value.period.start}-to-${data.value.period.end}.csv` })
  a.click()
  URL.revokeObjectURL(url)
}
const exportCompanies = () => download('learning-impact-companies',
  ['Company', 'Type', 'Users', 'Active learners', 'Coverage %', 'Lessons completed', 'Certificates', 'Minutes learning'],
  data.value.companies.map((c: any) => [c.name, c.kind === 'sedna' ? 'Sedna staff' : 'Customer', c.users, c.active, c.coverage, c.lessons, c.certificates, c.tracked_minutes]))
const exportPaths = () => download('learning-impact-paths',
  ['Path', 'Audience', 'Lessons', 'Started', 'Finished', 'Completion %', 'Median days to finish', 'Minutes learning', 'Drop-off lesson', 'Learners stopped there'],
  data.value.paths.map((p: any) => [p.name, p.audience, p.lessons, p.started, p.finished, p.completion_rate, p.median_days, p.tracked_minutes, p.dropoff?.title ?? '', p.dropoff?.learners ?? '']))
const exportIdle = () => download('learning-impact-idle-learners',
  ['Learner', 'Company', 'Unfinished paths', 'Days idle'],
  data.value.attention.idle_learners.map((l: any) => [l.name, l.company, l.paths.join('; '), l.days_idle]))
</script>

<template>
  <div class="page">
    <div class="page-header">
      <div class="eyebrow">LEARNING IMPACT</div>
      <h1 class="page-title">Learning impact</h1>
      <p class="page-sub">How many people learned, what they finished, and where they get stuck — across Sedna and every customer.</p>
    </div>

    <div class="filters" role="group" aria-label="Filters">
      <label class="filter">
        <span>Period</span>
        <select v-model="period" class="input">
          <option value="month">This month</option>
          <option value="quarter">This quarter</option>
          <option value="last_quarter">Last quarter</option>
          <option value="12m">Last 12 months</option>
        </select>
      </label>
      <label class="filter">
        <span>Audience</span>
        <select v-model="audience" class="input">
          <option value="all">Everyone</option>
          <option value="staff">Sedna staff</option>
          <option value="customer">Customers</option>
        </select>
      </label>
      <label class="filter">
        <span>Company</span>
        <select v-model="orgId" class="input">
          <option value="">All companies</option>
          <option v-for="c in data?.filters.companies ?? []" :key="c.id" :value="String(c.id)">{{ c.name }}{{ c.kind === 'sedna' ? ' (Sedna)' : '' }}</option>
        </select>
      </label>
      <label class="filter">
        <span>Product</span>
        <select v-model="product" class="input">
          <option value="">All products</option>
          <option value="vms">Sedna VMS</option>
          <option value="stream">Sedna Email</option>
        </select>
      </label>
    </div>

    <p v-if="failed" class="notice">The numbers couldn't be loaded. Try again in a moment.</p>
    <div v-else-if="loading && !data" class="notice">Loading…</div>

    <template v-if="data">
      <p class="range" :class="{ dim: loading }">{{ range }}</p>

      <!-- ── Reach ─────────────────────────────── -->
      <section class="section" :class="{ dim: loading }" aria-labelledby="reach-h">
        <h2 id="reach-h" class="section-h">Reach</h2>
        <div class="cards">
          <div v-for="c in cards" :key="c.key" class="card stat">
            <div class="stat-value">{{ c.value }}</div>
            <div class="stat-label">{{ c.label }}</div>
            <div class="stat-change" :class="c.change.dir">{{ c.change.text }}</div>
            <div v-if="c.note" class="stat-note">{{ c.note }}</div>
          </div>
        </div>

        <div class="card">
          <div class="card-head">
            <h3 class="card-h">Lessons completed by month</h3>
            <div class="legend">
              <span><i class="swatch staff" />Sedna staff</span>
              <span><i class="swatch customer" />Customers</span>
            </div>
          </div>
          <div class="trend" role="img" :aria-label="'Lessons completed by month: ' + data.trend.map((t: any) => `${monthLabel(t.month)} ${t.staff + t.customer}`).join(', ')">
            <div v-for="t in data.trend" :key="t.month" class="trend-col">
              <div class="trend-total">{{ t.staff + t.customer || '' }}</div>
              <div class="trend-bar">
                <div class="seg customer" :style="{ height: (t.customer / trendMax * 100) + '%' }" />
                <div class="seg staff" :style="{ height: (t.staff / trendMax * 100) + '%' }" />
              </div>
              <div class="trend-month">{{ monthLabel(t.month) }}</div>
            </div>
          </div>
        </div>

        <div class="card">
          <div class="card-head">
            <h3 class="card-h">By company</h3>
            <button class="btn btn-ghost btn-sm" :disabled="!data.companies.length" @click="exportCompanies">
              <i class="ti ti-download" /> Export CSV
            </button>
          </div>
          <div class="table-wrap">
            <table>
              <thead>
                <tr><th>Company</th><th class="num">Users</th><th class="num">Active</th><th class="num">Coverage</th><th class="num">Lessons</th><th class="num">Certificates</th><th class="num">Time</th></tr>
              </thead>
              <tbody>
                <tr v-for="c in data.companies" :key="c.org_id">
                  <td>{{ c.name }} <span v-if="c.kind === 'sedna'" class="tag">Sedna staff</span></td>
                  <td class="num">{{ c.users }}</td>
                  <td class="num">{{ c.active }}</td>
                  <td class="num">{{ c.coverage }}%</td>
                  <td class="num">{{ c.lessons }}</td>
                  <td class="num">{{ c.certificates }}</td>
                  <td class="num">{{ fmtTime(c.tracked_minutes) }}</td>
                </tr>
                <tr v-if="!data.companies.length"><td colspan="7" class="empty">No learners in this selection.</td></tr>
              </tbody>
            </table>
          </div>
        </div>
      </section>

      <!-- ── Health ────────────────────────────── -->
      <section class="section" :class="{ dim: loading }" aria-labelledby="health-h">
        <h2 id="health-h" class="section-h">Health</h2>
        <div class="card">
          <div class="card-head">
            <h3 class="card-h">Paths, all time</h3>
            <button class="btn btn-ghost btn-sm" :disabled="!data.paths.length" @click="exportPaths">
              <i class="ti ti-download" /> Export CSV
            </button>
          </div>
          <div class="table-wrap">
            <table>
              <thead>
                <tr><th>Path</th><th class="num">Started</th><th class="num">Finished</th><th class="num">Median time to finish</th><th class="num">Time spent</th><th>Where people stop</th></tr>
              </thead>
              <tbody>
                <tr v-for="p in data.paths" :key="p.path_id">
                  <td>
                    <RouterLink :to="`/paths/${p.path_id}`">{{ p.name }}</RouterLink>
                    <span class="tag" :class="p.audience">{{ p.audience === 'customer' ? 'Customer' : 'Staff' }}</span>
                  </td>
                  <td class="num">{{ p.started }}</td>
                  <td class="num">{{ p.finished }} <span class="muted">({{ p.completion_rate }}%)</span></td>
                  <td class="num">{{ p.median_days == null ? '—' : `${p.median_days} day${p.median_days === 1 ? '' : 's'}` }}</td>
                  <td class="num">{{ fmtTime(p.tracked_minutes) }}</td>
                  <td>
                    <template v-if="p.dropoff">{{ p.dropoff.title }} <span class="muted">· {{ p.dropoff.learners }} stopped</span></template>
                    <span v-else class="muted">Nobody stuck</span>
                  </td>
                </tr>
                <tr v-if="!data.paths.length"><td colspan="6" class="empty">Nobody has started a path in this selection yet.</td></tr>
              </tbody>
            </table>
          </div>
        </div>

        <div class="card attention">
          <div class="card-head">
            <h3 class="card-h">Needs attention</h3>
            <button class="btn btn-ghost btn-sm" :disabled="!data.attention.idle_learners.length" @click="exportIdle">
              <i class="ti ti-download" /> Export CSV
            </button>
          </div>
          <p class="att-line">
            <strong>{{ data.attention.paths.length }}</strong> path{{ data.attention.paths.length === 1 ? '' : 's' }} where fewer than 20% of starters finish
            <template v-if="data.attention.paths.length">: {{ data.attention.paths.map((p: any) => p.name).join(', ') }}</template>
          </p>
          <p class="att-line">
            <strong>{{ data.attention.idle_learners.length }}</strong> learner{{ data.attention.idle_learners.length === 1 ? '' : 's' }} with an unfinished path and nothing for {{ data.attention.idle_days }}+ days
          </p>
          <div v-if="data.attention.idle_learners.length" class="table-wrap">
            <table>
              <thead><tr><th>Learner</th><th>Company</th><th>Unfinished</th><th class="num">Idle</th></tr></thead>
              <tbody>
                <tr v-for="l in data.attention.idle_learners" :key="l.user_id">
                  <td>{{ l.name }}</td>
                  <td>{{ l.company }}</td>
                  <td>{{ l.paths.join(', ') }}</td>
                  <td class="num">{{ l.days_idle }} days</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </section>

      <p class="method">
        A lesson counts when it's marked complete; placeholder outlines never count. Time spent counts only while a lesson
        is open, visible and in use, and has been recorded since 13 Oct 2026. The estimate beside it adds up the length of
        each lesson completed.
      </p>
    </template>
  </div>
</template>

<style scoped>
.page { padding: 40px 24px 72px; max-width: var(--content-max); margin: 0 auto; }
.page-header { margin-bottom: 24px; }
.filters { display: flex; flex-wrap: wrap; gap: 12px; margin-bottom: 12px; }
.filter { display: flex; flex-direction: column; gap: 6px; font-size: 13px; color: var(--text-secondary); min-width: 170px; flex: 1 1 170px; max-width: 240px; }
.filter .input { min-height: 44px; }
.range { font-size: 14px; color: var(--text-secondary); margin: 0 0 32px; }
.notice { font-size: 15px; color: var(--text-secondary); padding: 24px 0; }
.dim { opacity: 0.55; transition: opacity 0.15s; }

.section { margin-bottom: 48px; display: flex; flex-direction: column; gap: 16px; }
.section-h { font-size: 28px; font-weight: 500; letter-spacing: -0.01em; }

.cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(190px, 1fr)); gap: 12px; }
.stat { display: flex; flex-direction: column; gap: 4px; padding: 20px; }
.stat-value { font-size: 36px; font-weight: 500; letter-spacing: -0.02em; line-height: 1.1; }
.stat-label { font-size: 14px; color: var(--text-secondary); }
.stat-change { font-family: var(--font-mono); font-size: 12px; margin-top: 8px; color: var(--text-secondary); }
.stat-change.up { color: #1F8A5B; }
.stat-change.down { color: #B0322B; }
.stat-note { font-size: 13px; color: var(--text-secondary); }

.card-head { display: flex; align-items: center; justify-content: space-between; gap: 12px; flex-wrap: wrap; margin-bottom: 16px; }
.card-h { font-size: 17px; font-weight: 500; }
.legend { display: flex; gap: 16px; font-size: 13px; color: var(--text-secondary); }
.legend span { display: inline-flex; align-items: center; gap: 6px; }
.swatch { width: 10px; height: 10px; border-radius: 2px; display: inline-block; }
.swatch.staff, .seg.staff { background: #7A3FE5; }
.swatch.customer, .seg.customer { background: #C5D9FE; }

.trend { display: flex; align-items: flex-end; gap: 12px; height: 180px; }
.trend-col { flex: 1; display: flex; flex-direction: column; align-items: center; gap: 6px; height: 100%; }
.trend-total { font-size: 13px; color: var(--text-secondary); min-height: 18px; }
.trend-bar { flex: 1; width: 100%; max-width: 56px; display: flex; flex-direction: column-reverse; background: #F4F4F6; border-radius: 4px; overflow: hidden; }
.seg { width: 100%; }
.trend-month { font-family: var(--font-mono); font-size: 12px; color: var(--text-secondary); }

.table-wrap { overflow-x: auto; }
table { width: 100%; border-collapse: collapse; font-size: 14px; }
th { text-align: left; font-weight: 500; color: var(--text-secondary); font-size: 13px; padding: 8px 12px; border-bottom: 1px solid var(--border); white-space: nowrap; }
td { padding: 12px; border-bottom: 1px solid var(--border); vertical-align: top; }
tr:last-child td { border-bottom: none; }
.num { text-align: right; white-space: nowrap; }
.muted { color: var(--text-secondary); }
.empty { color: var(--text-secondary); text-align: center; padding: 24px; }
td a { color: var(--text-primary); text-decoration: none; }
td a:hover { color: var(--purple); }
.tag { font-size: 12px; padding: 2px 8px; border-radius: 4px; background: #ECDEFE; color: #4B1FA8; margin-left: 6px; white-space: nowrap; }
.tag.customer { background: #C5D9FE; color: #1E3A8A; }
.tag.internal { background: #F1F2F4; color: #3A3B42; }

.attention { border-color: #FBEDC8; }
.att-line { font-size: 15px; margin-bottom: 8px; }
.method { font-size: 13px; color: var(--text-secondary); max-width: 720px; line-height: 1.6; }

@media (max-width: 640px) {
  .filter { max-width: none; }
  .stat-value { font-size: 30px; }
}
</style>
