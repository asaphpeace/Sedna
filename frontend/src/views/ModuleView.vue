<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { modulesApi, progressApi, savedApi, quizzesApi } from '@/api'
import { useAppStore } from '@/stores/app'
import ModuleComments from '@/components/ModuleComments.vue'

const route = useRoute()
const router = useRouter()
const app = useAppStore()

const module = ref<any>(null)
const tierModules = ref<any[]>([])
const hasQuiz = ref(false)
const activeTab = ref<'overview' | 'transcript' | 'resources' | 'notes'>('overview')

onMounted(async () => {
  const { data } = await modulesApi.get(Number(route.params.id))
  module.value = data
  await progressApi.start(data.id)
  await app.loadModuleProgress()
  await checkQuiz()
  // Load sibling modules in the same tier
  if (data.tier_id) {
    try {
      const res = await modulesApi.byTier(data.tier_id)
      tierModules.value = res.data
    } catch {
      tierModules.value = []
    }
  }
})

const prog = computed(() => app.moduleProgress[Number(route.params.id)])
const isDone = computed(() => prog.value?.state === 'done')
const savedIds = computed(() => new Set(app.saved.map((s: any) => s.module_id)))

// Find the path progress for this module's path
const pathProg = computed(() => {
  if (!module.value) return null
  return app.pathProgress.find((p: any) =>
    app.paths.find((r: any) => r.id === p.role_id)
  ) ?? app.pathProgress[0] ?? null
})

const pathName = computed(() => pathProg.value?.role_name ?? '')
const pathPct = computed(() => pathProg.value?.pct ?? 0)

// Next cert to earn in this path
const nextCert = computed(() => {
  if (!pathProg.value) return ''
  const earned = pathProg.value.earned_certs
  const total = pathProg.value.total_certs
  return earned < total ? `${pathName.value} Level ${earned + 1}` : 'All certs earned!'
})

async function checkQuiz() {
  try {
    const res = await quizzesApi.forModule(Number(route.params.id))
    hasQuiz.value = res.data.length > 0
  } catch {
    hasQuiz.value = false
  }
}

async function markDone() {
  await progressApi.complete(Number(route.params.id))
  await app.loadModuleProgress()
  await app.loadPathProgress()
  await app.loadGamification()
}

async function toggleSave() {
  const id = Number(route.params.id)
  if (savedIds.value.has(id)) {
    await savedApi.unsave(id)
  } else {
    await savedApi.save(id)
  }
  await app.loadSaved()
}

const prodLabel: Record<string, string> = { vms: 'Dataloy VMS', stream: 'Sedna Stream', cross: 'Cross-product' }
const prodStyle: Record<string, { bg: string; fg: string }> = {
  vms:    { bg: '#F1EBFE', fg: '#6E2BF0' },
  stream: { bg: '#E3F4F9', fg: '#0B8FB0' },
  cross:  { bg: '#E2F6EC', fg: '#0E9E6E' },
}

function moduleIcon(type: string) {
  return type === 'v' ? 'ti-player-play' : 'ti-file-text'
}

function moduleDoneState(mod: any) {
  return app.moduleProgress[mod.id]?.state === 'done'
}

const CIRCLE_R = 22
const CIRCLE_C = 2 * Math.PI * CIRCLE_R
const circleOffset = computed(() => CIRCLE_C - (pathPct.value / 100) * CIRCLE_C)
</script>

<template>
  <div class="page">
    <div v-if="!module" class="loading">Loading…</div>

    <template v-else>
      <!-- Two-column layout -->
      <div class="mod-layout">

        <!-- LEFT: main content -->
        <div class="mod-main">

          <!-- Video / article player -->
          <div class="video-wrap">
            <div class="video-inner">
              <div class="video-badge">
                {{ (prodLabel[module.product] ?? module.product).toUpperCase() }} ·
                {{ module.module_type === 'v' ? 'VIDEO' : 'ARTICLE' }}
              </div>
              <div class="video-play-btn">
                <i class="ti ti-player-play-filled" />
              </div>
              <div class="video-resume" v-if="prog?.pct_complete > 0 && prog?.pct_complete < 100">
                Resume at {{ Math.floor((module.duration_mins * (prog.pct_complete / 100)) * 60 / 60) }}:{{ String(Math.floor((module.duration_mins * (prog.pct_complete / 100) % 1) * 60)).padStart(2,'0') }}
              </div>
            </div>

            <!-- Fake progress bar -->
            <div class="video-controls">
              <div class="vc-left">
                <button class="vc-btn" aria-label="Play"><i class="ti ti-player-play" /></button>
                <button class="vc-btn" aria-label="Skip"><i class="ti ti-player-track-next" /></button>
                <button class="vc-btn" aria-label="Volume"><i class="ti ti-volume" /></button>
                <span class="vc-time">0:00 / {{ module.duration_mins }}:00</span>
              </div>
              <div class="vc-right">
                <button class="vc-btn vc-speed">1.0x</button>
                <button class="vc-btn" aria-label="Subtitles"><i class="ti ti-subtitles" /></button>
                <button class="vc-btn" aria-label="Settings"><i class="ti ti-settings" /></button>
                <button class="vc-btn" aria-label="Fullscreen"><i class="ti ti-maximize" /></button>
              </div>
            </div>
            <div class="video-seekbar">
              <div class="video-seekbar-fill" :style="{ width: (prog?.pct_complete ?? 0) + '%' }" />
            </div>
          </div>

          <!-- Title + actions -->
          <div class="mod-header">
            <div class="mod-title-row">
              <h1 class="mod-title">{{ module.title }}</h1>
              <div class="mod-actions">
                <button class="btn btn-ghost save-btn" @click="toggleSave">
                  <i :class="['ti', savedIds.has(Number(route.params.id)) ? 'ti-bookmark-filled' : 'ti-bookmark']" />
                  {{ savedIds.has(Number(route.params.id)) ? 'Saved' : 'Save' }}
                </button>
                <button v-if="!isDone" class="btn btn-primary" @click="markDone">
                  <i class="ti ti-circle-check" /> Mark complete
                </button>
                <div v-else class="done-badge">
                  <i class="ti ti-circle-check-filled" /> Completed
                </div>
              </div>
            </div>
            <div class="mod-meta-row">
              <span class="pill" :style="{ background: module.module_type === 'v' ? '#F1EBFE' : '#FBF1E3', color: module.module_type === 'v' ? '#6E2BF0' : '#B26A00' }">
                <i :class="['ti', moduleIcon(module.module_type)]" />
                {{ module.module_type === 'v' ? 'Video' : 'Article' }}
              </span>
              <span class="meta-sep">·</span>
              <span class="mod-dur"><i class="ti ti-clock" /> {{ module.duration_mins }} min</span>
              <span class="meta-sep">·</span>
              <span class="mod-tier-label">Tier {{ tierModules.length ? '1' : '—' }} · Onboarded</span>
            </div>
          </div>

          <!-- Tabs -->
          <div class="mod-tabs">
            <button
              v-for="tab in ['overview','transcript','resources','notes'] as const"
              :key="tab"
              class="tab-btn"
              :class="{ active: activeTab === tab }"
              @click="activeTab = tab"
            >
              {{ tab === 'notes' ? 'My notes' : tab.charAt(0).toUpperCase() + tab.slice(1) }}
            </button>
          </div>

          <!-- Tab: Overview -->
          <div v-if="activeTab === 'overview'" class="tab-content">
            <div v-if="module.description" class="mod-desc">
              <p>{{ module.description }}</p>
            </div>

            <div v-if="module.learn_items?.length" class="learn-section">
              <h2 class="section-h">What you'll learn</h2>
              <div class="learn-grid">
                <div v-for="item in module.learn_items" :key="item" class="learn-item">
                  <i class="ti ti-check" style="color: var(--purple); flex-shrink:0" /> {{ item }}
                </div>
              </div>
            </div>

            <!-- Quiz CTA -->
            <div v-if="hasQuiz" class="quiz-cta">
              <div class="quiz-cta-left">
                <i class="ti ti-help-circle" />
                <div>
                  <div class="quiz-cta-title">Test your knowledge</div>
                  <div class="quiz-cta-sub">Take the quiz to earn XP and unlock your certificate faster</div>
                </div>
              </div>
              <RouterLink :to="`/quiz?module_id=${module.id}`" class="btn btn-primary">Start quiz</RouterLink>
            </div>

            <!-- Discussion -->
            <ModuleComments :module-id="module.id" />
          </div>

          <!-- Tab: Transcript -->
          <div v-else-if="activeTab === 'transcript'" class="tab-content tab-empty">
            <i class="ti ti-file-text tab-empty-icon" />
            <p>Transcript not available for this module.</p>
          </div>

          <!-- Tab: Resources -->
          <div v-else-if="activeTab === 'resources'" class="tab-content tab-empty">
            <i class="ti ti-link tab-empty-icon" />
            <p>No additional resources attached to this module.</p>
          </div>

          <!-- Tab: Notes -->
          <div v-else-if="activeTab === 'notes'" class="tab-content">
            <div class="notes-compose">
              <i class="ti ti-pencil" style="font-size:17px;color:var(--text-muted)" />
              <span style="flex:1;font-size:13px;color:var(--text-muted)">Add a note…</span>
              <span class="notes-add-btn">Add note</span>
            </div>
            <p class="tab-empty-text">Your notes for this module will appear here.</p>
          </div>

        </div><!-- /mod-main -->

        <!-- RIGHT RAIL -->
        <aside class="mod-rail">

          <!-- Progress card -->
          <div class="rail-progress-card">
            <div class="rpc-blob" />
            <div class="rpc-inner">
              <div class="rpc-ring">
                <svg viewBox="0 0 56 56" width="58" height="58">
                  <circle cx="28" cy="28" :r="CIRCLE_R" fill="none" stroke="rgba(255,255,255,0.14)" stroke-width="6" />
                  <circle
                    cx="28" cy="28" :r="CIRCLE_R" fill="none"
                    stroke="#6E2BF0" stroke-width="6"
                    stroke-linecap="round"
                    :stroke-dasharray="CIRCLE_C"
                    :stroke-dashoffset="circleOffset"
                    transform="rotate(-90 28 28)"
                    style="transition: stroke-dashoffset 0.5s ease"
                  />
                  <text x="28" y="32" text-anchor="middle" fill="#fff" font-size="11" font-weight="800" font-family="Hanken Grotesk, sans-serif">{{ pathPct }}%</text>
                </svg>
              </div>
              <div class="rpc-text">
                <div class="rpc-path-name">{{ pathName }} path</div>
                <div class="rpc-sub">Keep going to earn</div>
                <div class="rpc-cert">{{ nextCert }}</div>
              </div>
            </div>
          </div>

          <!-- In this tier -->
          <div class="rail-card">
            <div class="rail-card-head">
              <span class="rail-card-title">In this tier</span>
              <span class="rail-autoplay"><i class="ti ti-player-track-next" /> Autoplay</span>
            </div>
            <div class="tier-list">
              <div
                v-for="m in tierModules"
                :key="m.id"
                class="tier-item"
                :class="{ current: m.id === module.id }"
                @click="router.push(`/modules/${m.id}`)"
              >
                <div class="tier-icon" :class="moduleDoneState(m) ? 'done' : m.id === module.id ? 'active' : 'default'">
                  <i v-if="moduleDoneState(m)" class="ti ti-check" />
                  <i v-else-if="m.id === module.id" class="ti ti-player-play-filled" />
                  <span v-else style="font-size:11px;font-weight:700">{{ tierModules.indexOf(m) + 1 }}</span>
                </div>
                <div class="tier-item-body">
                  <div class="tier-item-title" :class="{ 'text-purple': m.id === module.id }">{{ m.title }}</div>
                  <div class="tier-item-meta">
                    <i :class="['ti', moduleIcon(m.module_type)]" /> {{ m.duration_mins }} min
                  </div>
                </div>
              </div>
              <!-- Empty state if no tier modules loaded -->
              <div v-if="!tierModules.length" class="tier-empty">No other modules in this tier</div>
            </div>
          </div>

          <!-- Chapters (from learn_items as proxy) -->
          <div class="rail-card" v-if="module.learn_items?.length">
            <div class="rail-card-head">
              <span class="rail-card-title">Chapters</span>
            </div>
            <div class="chapter-list">
              <div
                v-for="(item, idx) in module.learn_items.slice(0, 8)"
                :key="idx"
                class="chapter-row"
              >
                <span class="chapter-dot" :class="{ active: idx === 0 }" />
                <span class="chapter-label" :class="{ 'chapter-active': idx === 0 }">{{ item }}</span>
                <span class="chapter-time">{{ (idx * Math.floor(module.duration_mins / (module.learn_items.length || 1))).toString().padStart(1,'0') }}:00</span>
              </div>
            </div>
          </div>

        </aside><!-- /mod-rail -->
      </div><!-- /mod-layout -->
    </template>
  </div>
</template>

<style scoped>
.page { padding: 0; max-width: 100%; background: var(--bg); }
.loading { padding: 40px 32px; color: var(--text-muted); }

/* ── Two-column layout ────────────────────────────────── */
.mod-layout {
  display: flex;
  gap: 0;
  align-items: flex-start;
  min-height: 100%;
}
.mod-main {
  flex: 1;
  min-width: 0;
  padding: 0 0 48px;
  border-right: 1px solid var(--border);
}
.mod-rail {
  width: 320px;
  flex-shrink: 0;
  padding: 16px 20px;
  display: flex;
  flex-direction: column;
  gap: 14px;
  position: sticky;
  top: 0;
  max-height: 100vh;
  overflow-y: auto;
}

/* ── Video player ─────────────────────────────────────── */
.video-wrap {
  background: #0F0A1A;
  margin-bottom: 0;
}
.video-inner {
  position: relative;
  aspect-ratio: 16/9;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(160deg, #1A0A3C 0%, #0F0A1A 60%);
}
.video-badge {
  position: absolute; top: 14px; left: 16px;
  background: rgba(255,255,255,0.12);
  color: rgba(255,255,255,0.75);
  font-size: 10.5px; font-weight: 700; letter-spacing: 0.8px;
  padding: 4px 10px; border-radius: 20px; backdrop-filter: blur(4px);
}
.video-play-btn {
  width: 64px; height: 64px; border-radius: 50%;
  background: rgba(255,255,255,0.18); border: 2px solid rgba(255,255,255,0.35);
  display: flex; align-items: center; justify-content: center;
  font-size: 26px; color: #fff; cursor: pointer;
  transition: background 0.15s;
}
.video-play-btn:hover { background: rgba(255,255,255,0.28); }
.video-resume {
  position: absolute; bottom: 14px;
  font-size: 12px; color: rgba(255,255,255,0.6);
}
.video-seekbar {
  height: 3px; background: rgba(255,255,255,0.15); cursor: pointer;
}
.video-seekbar-fill { height: 100%; background: var(--purple); }
.video-controls {
  display: flex; align-items: center; justify-content: space-between;
  padding: 8px 14px; background: #0F0A1A;
}
.vc-left, .vc-right { display: flex; align-items: center; gap: 4px; }
.vc-btn {
  background: none; border: none; color: rgba(255,255,255,0.7);
  font-size: 15px; padding: 5px; border-radius: 6px; cursor: pointer; font-family: inherit;
}
.vc-btn:hover { color: #fff; background: rgba(255,255,255,0.08); }
.vc-speed { font-size: 12px; font-weight: 700; padding: 4px 8px; border: 1px solid rgba(255,255,255,0.2); border-radius: 6px; }
.vc-time { font-size: 12px; color: rgba(255,255,255,0.55); font-variant-numeric: tabular-nums; margin-left: 6px; }

/* ── Module header ────────────────────────────────────── */
.mod-header { padding: 20px 28px 0; }
.mod-title-row { display: flex; align-items: flex-start; justify-content: space-between; gap: 16px; margin-bottom: 10px; }
.mod-title { font-size: 20px; font-weight: 800; letter-spacing: -0.4px; line-height: 1.3; flex: 1; }
.mod-actions { display: flex; gap: 8px; align-items: center; flex-shrink: 0; }
.save-btn { font-size: 13px; }
.done-badge { display: flex; align-items: center; gap: 5px; font-size: 13.5px; font-weight: 600; color: var(--green); }
.mod-meta-row { display: flex; align-items: center; gap: 7px; font-size: 12.5px; color: var(--text-muted); flex-wrap: wrap; }
.meta-sep { color: var(--border-mid); }
.mod-dur, .mod-tier-label { display: flex; align-items: center; gap: 4px; }
.pill { display: inline-flex; align-items: center; gap: 4px; padding: 3px 9px; border-radius: 100px; font-size: 11.5px; font-weight: 600; }

/* ── Tabs ─────────────────────────────────────────────── */
.mod-tabs {
  display: flex; gap: 0; padding: 0 28px;
  border-bottom: 1px solid var(--border);
  margin-top: 16px;
}
.tab-btn {
  padding: 10px 0; margin-right: 24px;
  font-size: 13px; font-weight: 500; color: var(--text-muted);
  border: none; background: none; cursor: pointer;
  border-bottom: 2px solid transparent; margin-bottom: -1px;
  transition: color 0.12s, border-color 0.12s;
}
.tab-btn.active { color: var(--text-primary); font-weight: 600; border-bottom-color: var(--purple); }
.tab-btn:hover:not(.active) { color: var(--text-secondary); }

/* ── Tab content ──────────────────────────────────────── */
.tab-content { padding: 24px 28px; display: flex; flex-direction: column; gap: 24px; }
.mod-desc { font-size: 14px; color: var(--text-secondary); line-height: 1.65; }

.section-h { font-size: 14px; font-weight: 700; margin-bottom: 14px; }
.learn-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
.learn-item { display: flex; align-items: flex-start; gap: 8px; font-size: 13px; color: var(--text-secondary); line-height: 1.45; }

.tab-empty { align-items: center; justify-content: center; min-height: 180px; color: var(--text-muted); text-align: center; }
.tab-empty-icon { font-size: 32px; margin-bottom: 8px; color: var(--border-mid); display: block; }
.tab-empty-text { font-size: 13px; color: var(--text-muted); }
.notes-compose { display: flex; align-items: center; gap: 10px; border: 1px solid var(--border); border-radius: 12px; padding: 12px 14px; }
.notes-add-btn { font-size: 11.5px; font-weight: 700; color: #fff; background: var(--purple); padding: 5px 12px; border-radius: 8px; cursor: pointer; }

.quiz-cta {
  display: flex; align-items: center; justify-content: space-between; gap: 1rem;
  background: rgba(110,43,240,.07); border: 1px solid rgba(110,43,240,.22);
  border-radius: 12px; padding: 1.1rem 1.3rem;
}
.quiz-cta-left { display: flex; align-items: center; gap: 12px; }
.quiz-cta-left > i { font-size: 28px; color: var(--purple); flex-shrink: 0; }
.quiz-cta-title { font-weight: 600; font-size: 13.5px; }
.quiz-cta-sub { font-size: 12px; color: var(--text-muted); margin-top: 2px; }

/* ── Right rail ───────────────────────────────────────── */
.rail-progress-card {
  background: #1A1622; border-radius: 15px; padding: 18px;
  position: relative; overflow: hidden;
}
.rpc-blob {
  position: absolute; right: -30px; top: -30px;
  width: 140px; height: 140px; border-radius: 50%;
  background: radial-gradient(circle at 40% 40%, rgba(110,43,240,0.5), rgba(110,43,240,0) 70%);
}
.rpc-inner { position: relative; display: flex; align-items: center; gap: 14px; }
.rpc-ring { flex-shrink: 0; }
.rpc-text {}
.rpc-path-name { font-size: 13px; font-weight: 700; color: #fff; }
.rpc-sub { font-size: 11.5px; color: rgba(255,255,255,0.55); margin-top: 2px; }
.rpc-cert { font-size: 11.5px; font-weight: 600; color: #B79CFF; margin-top: 1px; }

.rail-card {
  background: var(--surface); border: 1px solid var(--border);
  border-radius: 15px; overflow: hidden;
}
.rail-card-head {
  display: flex; align-items: center; justify-content: space-between;
  padding: 14px 16px 10px;
}
.rail-card-title { font-size: 12.5px; font-weight: 700; }
.rail-autoplay { font-size: 11px; color: var(--text-muted); display: flex; align-items: center; gap: 3px; }

/* Tier list */
.tier-list { display: flex; flex-direction: column; }
.tier-item {
  display: flex; align-items: center; gap: 11px;
  padding: 10px 16px; border-top: 1px solid #F4F3F6;
  cursor: pointer; transition: background 0.1s;
}
.tier-item:hover { background: #FBFAFC; }
.tier-item.current { background: var(--purple-subtle); }
.tier-icon {
  width: 24px; height: 24px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center; flex-shrink: 0; font-size: 13px;
}
.tier-icon.done { background: var(--green); color: #fff; }
.tier-icon.active { background: var(--purple); color: #fff; }
.tier-icon.default { background: var(--border); color: var(--text-muted); }
.tier-item-body { flex: 1; min-width: 0; }
.tier-item-title { font-size: 12.5px; font-weight: 500; line-height: 1.35; color: var(--text-primary); }
.tier-item-title.text-purple { color: var(--purple); font-weight: 600; }
.tier-item-meta { font-size: 10.5px; color: var(--text-muted); margin-top: 1px; display: flex; align-items: center; gap: 3px; }
.tier-empty { padding: 12px 16px; font-size: 12.5px; color: var(--text-muted); }

/* Chapters */
.chapter-list { display: flex; flex-direction: column; padding: 4px 8px 10px; }
.chapter-row { display: flex; align-items: center; gap: 11px; padding: 8px 8px; border-radius: 8px; cursor: pointer; transition: background 0.1s; }
.chapter-row:hover { background: #FBFAFC; }
.chapter-dot { width: 8px; height: 8px; border-radius: 50%; background: var(--border-mid); flex-shrink: 0; }
.chapter-dot.active { background: var(--purple); }
.chapter-label { flex: 1; font-size: 12.5px; color: var(--text-secondary); line-height: 1.35; }
.chapter-active { color: var(--text-primary); font-weight: 600; }
.chapter-time { font-size: 11px; color: var(--text-muted); font-variant-numeric: tabular-nums; }

/* ── Responsive ───────────────────────────────────────── */
@media (max-width: 900px) {
  .mod-layout { flex-direction: column; }
  .mod-main { border-right: none; }
  .mod-rail { width: 100%; position: static; max-height: none; border-top: 1px solid var(--border); }
  .learn-grid { grid-template-columns: 1fr; }
}
</style>
