<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { gamificationApi, analyticsApi } from '@/api'

const gami = ref<any>(null)
const stats = ref<any>(null)
const loading = ref(true)

onMounted(async () => {
  try {
    const [gamiRes, statsRes] = await Promise.all([gamificationApi.me(), analyticsApi.me()])
    gami.value = gamiRes.data
    stats.value = statsRes.data
  } finally {
    loading.value = false
  }
})

function heatmapColor(count: number) {
  if (!count) return 'var(--border)'
  if (count >= 5) return '#6E2BF0'
  if (count >= 3) return 'rgba(110,43,240,.7)'
  if (count >= 2) return 'rgba(110,43,240,.45)'
  return 'rgba(110,43,240,.2)'
}

// Build last 35 days for heatmap display
function buildHeatmap(raw: Record<string, number>) {
  const days: { date: string; count: number }[] = []
  const today = new Date()
  for (let i = 34; i >= 0; i--) {
    const d = new Date(today)
    d.setDate(d.getDate() - i)
    const key = d.toISOString().slice(0, 10)
    days.push({ date: key, count: raw[key] || 0 })
  }
  return days
}
</script>

<template>
  <div class="page-container">
    <div class="page-header">
      <h1>My Progress</h1>
    </div>

    <div v-if="loading" class="loading-state"><i class="ti ti-loader-2 spin" /></div>

    <template v-else-if="gami && stats">
      <!-- Level card -->
      <div class="level-card">
        <div class="level-left">
          <div class="level-num">Level {{ gami.level }}</div>
          <div class="level-name">{{ gami.level_name }}</div>
          <div class="xp-info">{{ gami.xp_total.toLocaleString() }} XP total</div>
        </div>
        <div class="level-right">
          <div class="level-progress-wrap">
            <div class="level-progress-bar">
              <div class="level-progress-fill" :style="{ width: gami.pct_to_next + '%' }" />
            </div>
            <span class="level-pct">{{ gami.pct_to_next }}% to next level</span>
          </div>
        </div>
      </div>

      <!-- Stat cards -->
      <div class="stat-row">
        <div class="stat-card">
          <i class="ti ti-check-circle" style="color: var(--green)" />
          <div class="stat-num">{{ stats.modules_completed }}</div>
          <div class="stat-label">Modules done</div>
        </div>
        <div class="stat-card">
          <i class="ti ti-certificate" style="color: #B26A00" />
          <div class="stat-num">{{ stats.certs_earned }}</div>
          <div class="stat-label">Certificates</div>
        </div>
        <div class="stat-card">
          <i class="ti ti-flame" style="color: #EF4444" />
          <div class="stat-num">{{ gami.streak.current }}</div>
          <div class="stat-label">Day streak</div>
        </div>
        <div class="stat-card">
          <i class="ti ti-award" style="color: var(--purple)" />
          <div class="stat-num">{{ gami.badges.length }}</div>
          <div class="stat-label">Badges</div>
        </div>
      </div>

      <!-- Streak info -->
      <div class="card section">
        <h3><i class="ti ti-flame" /> Learning Streak</h3>
        <div class="streak-grid">
          <div class="streak-item">
            <div class="streak-val">{{ gami.streak.current }}</div>
            <div class="streak-lbl">Current streak</div>
          </div>
          <div class="streak-item">
            <div class="streak-val">{{ gami.streak.longest }}</div>
            <div class="streak-lbl">Longest streak</div>
          </div>
        </div>
      </div>

      <!-- Activity heatmap -->
      <div class="card section">
        <h3><i class="ti ti-calendar-stats" /> Activity — Last 35 Days</h3>
        <div class="heatmap">
          <div
            v-for="day in buildHeatmap(stats.activity_heatmap)"
            :key="day.date"
            class="heatmap-cell"
            :style="{ background: heatmapColor(day.count) }"
            :title="`${day.date}: ${day.count} action${day.count !== 1 ? 's' : ''}`"
          />
        </div>
      </div>

      <!-- Badges -->
      <div class="card section">
        <h3><i class="ti ti-award" /> Badges</h3>
        <div v-if="!gami.badges.length" class="empty-msg">Complete modules to earn your first badge.</div>
        <div v-else class="badges-grid">
          <div v-for="b in gami.badges" :key="b.slug" class="badge-item" :style="{ '--bg': b.bg_color }">
            <div class="badge-icon"><i :class="'ti ' + b.icon" /></div>
            <div class="badge-name">{{ b.name }}</div>
            <div class="badge-desc">{{ b.description }}</div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.page-container { max-width: 720px; margin: 0 auto; padding: 2rem 1rem; display: flex; flex-direction: column; gap: 1.25rem; }
.page-header h1 { font-size: 1.5rem; font-weight: 700; }
.loading-state { text-align: center; padding: 3rem; color: var(--text-muted); }
.spin { animation: spin 1s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

.level-card {
  display: flex; align-items: center; gap: 1.5rem;
  background: var(--purple); color: #fff;
  border-radius: 14px; padding: 1.75rem;
}
.level-num { font-size: 2rem; font-weight: 800; }
.level-name { font-size: 1rem; opacity: .85; }
.xp-info { font-size: .85rem; opacity: .7; margin-top: .25rem; }
.level-right { flex: 1; }
.level-progress-wrap { }
.level-progress-bar { height: 8px; background: rgba(255,255,255,.3); border-radius: 4px; overflow: hidden; margin-bottom: .5rem; }
.level-progress-fill { height: 100%; background: #fff; border-radius: 4px; transition: width .4s; }
.level-pct { font-size: .8rem; opacity: .8; }

.stat-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: .75rem; }
.stat-card { background: var(--surface); border: 1px solid var(--border); border-radius: 10px; padding: 1rem; text-align: center; }
.stat-card i { font-size: 1.4rem; display: block; margin-bottom: .5rem; }
.stat-num { font-size: 1.75rem; font-weight: 700; }
.stat-label { font-size: .8rem; color: var(--text-muted); }

.card.section { background: var(--surface); border: 1px solid var(--border); border-radius: 12px; padding: 1.5rem; }
.card.section h3 { font-size: 1rem; font-weight: 600; margin-bottom: 1.25rem; display: flex; align-items: center; gap: .5rem; }
.card.section h3 i { color: var(--purple); }

.streak-grid { display: flex; gap: 2rem; }
.streak-val { font-size: 2.5rem; font-weight: 700; color: var(--purple); }
.streak-lbl { font-size: .85rem; color: var(--text-muted); }

.heatmap { display: grid; grid-template-columns: repeat(35, 1fr); gap: 3px; }
.heatmap-cell { aspect-ratio: 1; border-radius: 3px; cursor: default; }

.empty-msg { color: var(--text-muted); font-size: .9rem; }
.badges-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(140px, 1fr)); gap: .75rem; }
.badge-item { background: var(--bg); border: 1px solid var(--border); border-radius: 10px; padding: 1rem; text-align: center; }
.badge-icon { width: 44px; height: 44px; border-radius: 50%; background: var(--bg); margin: 0 auto .5rem; display: flex; align-items: center; justify-content: center; font-size: 1.25rem; background-color: var(--bg); }
.badge-name { font-weight: 600; font-size: .9rem; margin-bottom: .2rem; }
.badge-desc { font-size: .8rem; color: var(--text-muted); }

@media (max-width: 600px) {
  .stat-row { grid-template-columns: repeat(2, 1fr); }
  .level-card { flex-direction: column; text-align: center; }
  .heatmap { grid-template-columns: repeat(7, 1fr); }
}
</style>
