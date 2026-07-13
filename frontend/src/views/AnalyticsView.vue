<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { analyticsApi } from '@/api'

const data = ref<any>(null)
const loading = ref(true)
const tab = ref<'overview' | 'learners' | 'content'>('overview')

onMounted(async () => {
  try {
    const res = await analyticsApi.org()
    data.value = res.data
  } finally {
    loading.value = false
  }
})

const atRiskLearners = computed(() =>
  (data.value?.learners ?? []).filter((l: any) => l.at_risk)
)
const topLearners = computed(() =>
  [...(data.value?.learners ?? [])].sort((a: any, b: any) => b.modules_done - a.modules_done).slice(0, 5)
)
</script>

<template>
  <div class="page-container">
    <div class="page-header">
      <h1>Analytics</h1>
      <p class="page-sub">Organisation learning data</p>
    </div>

    <div v-if="loading" class="loading-state"><i class="ti ti-loader-2 spin" /></div>

    <template v-else-if="data">
      <!-- Summary tiles -->
      <div class="tiles">
        <div class="tile">
          <div class="tile-val">{{ data.total_learners }}</div>
          <div class="tile-lbl">Total learners</div>
        </div>
        <div class="tile">
          <div class="tile-val">{{ data.active_last_14_days }}</div>
          <div class="tile-lbl">Active (14 days)</div>
        </div>
        <div class="tile risk" :class="{ 'has-risk': data.at_risk_count > 0 }">
          <div class="tile-val">{{ data.at_risk_count }}</div>
          <div class="tile-lbl">At risk (inactive)</div>
        </div>
        <div class="tile">
          <div class="tile-val">{{ data.org_completion_rate }}%</div>
          <div class="tile-lbl">Org completion rate</div>
        </div>
        <div class="tile">
          <div class="tile-val">{{ data.total_certs }}</div>
          <div class="tile-lbl">Certs earned</div>
        </div>
        <div class="tile">
          <div class="tile-val">{{ data.avg_completions_per_learner }}</div>
          <div class="tile-lbl">Avg modules/learner</div>
        </div>
      </div>

      <!-- Tabs -->
      <div class="tabs">
        <button class="tab-btn" :class="{ active: tab === 'overview' }" @click="tab = 'overview'">Overview</button>
        <button class="tab-btn" :class="{ active: tab === 'learners' }" @click="tab = 'learners'">Learners</button>
        <button class="tab-btn" :class="{ active: tab === 'content' }" @click="tab = 'content'">Content</button>
      </div>

      <!-- Overview tab -->
      <div v-if="tab === 'overview'">
        <div v-if="atRiskLearners.length" class="card risk-card">
          <h3><i class="ti ti-alert-triangle" /> Learners at risk ({{ atRiskLearners.length }})</h3>
          <p class="risk-sub">No activity in the last 14 days. Consider a nudge email.</p>
          <div class="risk-list">
            <div v-for="l in atRiskLearners" :key="l.user_id" class="risk-row">
              <div class="avatar-sm">{{ l.name.split(' ').map((n: string) => n[0]).join('').slice(0,2) }}</div>
              <div class="risk-info">
                <span class="risk-name">{{ l.name }}</span>
                <span class="risk-email">{{ l.email }}</span>
              </div>
              <div class="risk-modules">{{ l.modules_done }} modules</div>
            </div>
          </div>
        </div>

        <div class="card">
          <h3>Top learners</h3>
          <div class="top-learners">
            <div v-for="(l, i) in topLearners" :key="l.user_id" class="top-row">
              <span class="top-rank">#{{ i + 1 }}</span>
              <div class="avatar-sm">{{ l.name.split(' ').map((n: string) => n[0]).join('').slice(0,2) }}</div>
              <span class="top-name">{{ l.name }}</span>
              <span class="top-stat">{{ l.modules_done }} modules · {{ l.certs_earned }} certs</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Learners tab -->
      <div v-if="tab === 'learners'">
        <div class="card">
          <table class="data-table">
            <thead>
              <tr>
                <th>Learner</th>
                <th>Modules</th>
                <th>Certs</th>
                <th>Completion</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="l in data.learners" :key="l.user_id">
                <td>
                  <div class="learner-cell">
                    <div class="avatar-sm">{{ l.name.split(' ').map((n: string) => n[0]).join('').slice(0,2) }}</div>
                    <div>
                      <div class="learner-name">{{ l.name }}</div>
                      <div class="learner-email">{{ l.email }}</div>
                    </div>
                  </div>
                </td>
                <td>{{ l.modules_done }}</td>
                <td>{{ l.certs_earned }}</td>
                <td>
                  <div class="mini-bar">
                    <div class="mini-fill" :style="{ width: l.completion_rate + '%' }" />
                  </div>
                  <span class="mini-pct">{{ l.completion_rate }}%</span>
                </td>
                <td>
                  <span class="pill" :class="l.at_risk ? 'pill-warning' : 'pill-success'">
                    {{ l.at_risk ? 'At risk' : 'Active' }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Content tab -->
      <div v-if="tab === 'content'">
        <div class="card">
          <h3>Top performing modules</h3>
          <div class="module-list">
            <div v-for="m in data.top_modules" :key="m.module_id" class="module-stat-row">
              <span class="module-title">{{ m.title }}</span>
              <div class="module-bar-wrap">
                <div class="module-bar">
                  <div class="module-fill" :style="{ width: m.completion_rate + '%' }" />
                </div>
                <span class="module-pct">{{ m.completion_rate }}%</span>
              </div>
            </div>
          </div>
        </div>
        <div class="card">
          <h3>Lowest completion modules</h3>
          <div class="module-list">
            <div v-for="m in data.bottom_modules" :key="m.module_id" class="module-stat-row">
              <span class="module-title">{{ m.title }}</span>
              <div class="module-bar-wrap">
                <div class="module-bar">
                  <div class="module-fill low" :style="{ width: m.completion_rate + '%' }" />
                </div>
                <span class="module-pct">{{ m.completion_rate }}%</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.page-container { max-width: 900px; margin: 0 auto; padding: 2rem 1rem; display: flex; flex-direction: column; gap: 1.25rem; }
.page-header h1 { font-size: 1.5rem; font-weight: 700; }
.page-sub { color: var(--text-muted); font-size: .9rem; }
.loading-state { text-align: center; padding: 3rem; color: var(--text-muted); }
.spin { animation: spin 1s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

.tiles { display: grid; grid-template-columns: repeat(3, 1fr); gap: .75rem; }
.tile { background: var(--surface); border: 1px solid var(--border); border-radius: 10px; padding: 1.25rem; }
.tile.risk.has-risk { border-color: #EF4444; background: rgba(239,68,68,.05); }
.tile-val { font-size: 2rem; font-weight: 700; color: var(--purple); }
.tile.risk.has-risk .tile-val { color: #EF4444; }
.tile-lbl { font-size: .8rem; color: var(--text-muted); margin-top: .2rem; }

.tabs { display: flex; gap: .5rem; border-bottom: 1px solid var(--border); padding-bottom: 0; }
.tab-btn { background: none; border: none; padding: .6rem 1rem; cursor: pointer; font-size: .9rem; color: var(--text-muted); border-bottom: 2px solid transparent; margin-bottom: -1px; transition: color .15s, border-color .15s; }
.tab-btn.active { color: var(--purple); border-bottom-color: var(--purple); font-weight: 500; }

.card { background: var(--surface); border: 1px solid var(--border); border-radius: 12px; padding: 1.5rem; }
.card h3 { font-size: 1rem; font-weight: 600; margin-bottom: 1rem; display: flex; align-items: center; gap: .5rem; }
.card h3 i { color: var(--purple); }

.risk-card { border-color: #FEF3C7; background: #FFFBEB; }
.risk-card h3 i { color: #D97706; }
.risk-sub { color: #92400E; font-size: .85rem; margin-bottom: 1rem; margin-top: -.5rem; }
.risk-list { display: flex; flex-direction: column; gap: .5rem; }
.risk-row { display: flex; align-items: center; gap: .75rem; padding: .5rem; background: rgba(255,255,255,.6); border-radius: 8px; }
.risk-info { flex: 1; }
.risk-name { font-weight: 500; font-size: .9rem; display: block; }
.risk-email { font-size: .8rem; color: var(--text-muted); }
.risk-modules { font-size: .85rem; color: var(--text-muted); }

.avatar-sm { width: 32px; height: 32px; border-radius: 50%; background: var(--purple); color: #fff; font-size: .7rem; font-weight: 700; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }

.top-learners { display: flex; flex-direction: column; gap: .5rem; }
.top-row { display: flex; align-items: center; gap: .75rem; padding: .5rem 0; border-bottom: 1px solid var(--border); }
.top-row:last-child { border-bottom: none; }
.top-rank { font-weight: 700; color: var(--text-muted); font-size: .85rem; width: 2rem; }
.top-name { flex: 1; font-weight: 500; }
.top-stat { font-size: .85rem; color: var(--text-muted); }

.data-table { width: 100%; border-collapse: collapse; font-size: .875rem; }
.data-table th { text-align: left; padding: .5rem .75rem; color: var(--text-muted); font-size: .8rem; font-weight: 500; border-bottom: 1px solid var(--border); }
.data-table td { padding: .6rem .75rem; border-bottom: 1px solid var(--border); vertical-align: middle; }
.learner-cell { display: flex; align-items: center; gap: .5rem; }
.learner-name { font-weight: 500; }
.learner-email { font-size: .75rem; color: var(--text-muted); }
.mini-bar { height: 4px; background: var(--border); border-radius: 2px; overflow: hidden; width: 80px; display: inline-block; vertical-align: middle; margin-right: .5rem; }
.mini-fill { height: 100%; background: var(--purple); }
.mini-pct { font-size: .8rem; color: var(--text-muted); }

.module-list { display: flex; flex-direction: column; gap: .75rem; }
.module-stat-row { display: flex; align-items: center; gap: 1rem; }
.module-title { flex: 1; font-size: .875rem; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.module-bar-wrap { display: flex; align-items: center; gap: .5rem; flex-shrink: 0; }
.module-bar { width: 120px; height: 6px; background: var(--border); border-radius: 3px; overflow: hidden; }
.module-fill { height: 100%; background: var(--green); border-radius: 3px; }
.module-fill.low { background: #EF4444; }
.module-pct { font-size: .8rem; color: var(--text-muted); width: 3rem; text-align: right; }

@media (max-width: 640px) {
  .tiles { grid-template-columns: repeat(2, 1fr); }
}
</style>
