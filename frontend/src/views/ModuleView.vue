<script setup lang="ts">
import { ref, onMounted, watch, computed, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { marked } from 'marked'
import DOMPurify from 'dompurify'
import { modulesApi, progressApi, savedApi, quizzesApi } from '@/api'
import { useAppStore } from '@/stores/app'
import ModuleComments from '@/components/ModuleComments.vue'
import { productLabel } from '@/constants/products'

marked.setOptions({ breaks: true, gfm: true })

const route = useRoute()
const router = useRouter()
const app = useAppStore()

const module = ref<any>(null)
const tierModules = ref<any[]>([])
const hasQuiz = ref(false)
const activeTab = ref<'overview' | 'transcript' | 'resources' | 'notes'>('overview')

// Opened from the admin Content panel's "Preview" button — renders the
// module exactly as a learner would see it, but must not mutate the
// viewer's own progress/history (they may be an admin, not the learner).
const isPreview = computed(() => route.query.preview === '1')

async function loadModule(id: number) {
  // Vue Router reuses this component instance when navigating between
  // /modules/:id routes, so this must run on every id change, not just on
  // mount — otherwise clicking another lesson updates the URL but the
  // screen (video, title, completion state) stays frozen on the old module.
  module.value = null
  activeTab.value = 'overview'
  justCompleted.value = false

  const { data } = await modulesApi.get(id)
  module.value = data
  if (!isPreview.value) {
    await progressApi.start(data.id)
    await app.loadModuleProgress()
  }
  await checkQuiz(id)

  if (data.tier_id) {
    try {
      const res = await modulesApi.byTier(data.tier_id)
      tierModules.value = res.data
    } catch {
      tierModules.value = []
    }
  } else {
    tierModules.value = []
  }
}

onMounted(() => loadModule(Number(route.params.id)))
watch(
  () => route.params.id,
  (id) => { if (id) loadModule(Number(id)) }
)

const prog = computed(() => app.moduleProgress[Number(route.params.id)])
const isDone = computed(() => prog.value?.state === 'done')
const savedIds = computed(() => new Set(app.saved.map((s: any) => s.module_id)))

// Find the path progress for this module's path. The module response
// carries its own role_id (stamped on by the backend from its tier) —
// match that directly against app.pathProgress rather than searching
// app.paths, which only holds summary counts (no nested tiers/modules).
const pathProg = computed(() => {
  if (!module.value) return null
  return app.pathProgress.find((p: any) => p.role_id === module.value.role_id)
    ?? app.pathProgress[0] ?? null
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

async function checkQuiz(moduleId: number) {
  try {
    const res = await quizzesApi.forModule(moduleId)
    hasQuiz.value = res.data.length > 0
  } catch {
    hasQuiz.value = false
  }
}

// The module immediately after the current one in this tier's list, or
// null if the current module is the last one in the tier.
const nextModule = computed(() => {
  if (!module.value || !tierModules.value.length) return null
  const idx = tierModules.value.findIndex((m: any) => m.id === module.value.id)
  if (idx === -1 || idx === tierModules.value.length - 1) return null
  return tierModules.value[idx + 1]
})

function goToNextModule() {
  if (nextModule.value) router.push(`/modules/${nextModule.value.id}`)
}

const completing = ref(false)
const justCompleted = ref(false)

async function markDone() {
  completing.value = true
  try {
    await progressApi.complete(Number(route.params.id))
    await app.loadModuleProgress()
    await app.loadPathProgress()
    await app.loadGamification()
    // Brief, deliberate pause before revealing "next lesson" — long enough
    // to read as an acknowledgement, short enough not to feel like a wait.
    await new Promise((r) => setTimeout(r, 1800))
    justCompleted.value = true
  } finally {
    completing.value = false
  }
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

const TYPE_ICON: Record<string, string> = { v: 'ti-player-play', a: 'ti-file-text', l: 'ti-link', p: 'ti-microphone', s: 'ti-presentation' }
const TYPE_LABEL: Record<string, string> = { v: 'Video', a: 'Article', l: 'Link', p: 'Podcast', s: 'Slides' }
const TYPE_PILL_BG: Record<string, string> = { v: '#F1EBFE', a: '#FBF1E3', l: '#E3F4F9', p: '#FCE8F3', s: '#E2F6EC' }
const TYPE_PILL_FG: Record<string, string> = { v: '#6E2BF0', a: '#B26A00', l: '#0B8FB0', p: '#C2185B', s: '#0E9E6E' }

function moduleIcon(type: string) {
  return TYPE_ICON[type] ?? 'ti-file-text'
}

function moduleDoneState(mod: any) {
  return app.moduleProgress[mod.id]?.state === 'done'
}

// "Autoplay" — a toggle in the tier-list rail — controls both whether a
// video starts playing as soon as its lesson opens, and whether finishing
// a video auto-advances to the next lesson in the tier.
const AUTOPLAY_STORAGE_KEY = 'sedna:autoplayEnabled'
const autoplayEnabled = ref(localStorage.getItem(AUTOPLAY_STORAGE_KEY) !== 'false')
watch(autoplayEnabled, (v) => localStorage.setItem(AUTOPLAY_STORAGE_KEY, String(v)))

// Recognise YouTube and Google Drive share links and convert them to their
// embeddable iframe form. Anything else is assumed to be a direct video file
// URL and is handed straight to a <video> tag.
//
// Autoplay-on-open: YouTube gets autoplay=1 (browsers require mute=1 to
// allow autoplay without a user gesture — a platform constraint, not a
// choice; the player's own controls let the learner unmute). The <video>
// tag mirrors this via the autoplay/muted attributes below. Google Drive's
// /preview embed has no documented autoplay parameter, so Drive-hosted
// videos may not reliably autoplay — a known limitation of that embed.
//
// Auto-advance-on-end: only possible for YouTube (via the IFrame Player
// API, wired up in bindYouTubePlayer) and direct <video> files (native
// `ended` event). Drive's embed exposes no playback-state API at all, so
// auto-advance cannot work for Drive-hosted videos.
const videoEmbed = computed(() => {
  const url: string | null = module.value?.video_url
  if (!url) return null

  const yt = url.match(
    /(?:youtube\.com\/(?:watch\?.*?v=|embed\/|shorts\/)|youtu\.be\/)([\w-]{11})/
  )
  if (yt) {
    const params = new URLSearchParams({ rel: '0', enablejsapi: '1' })
    if (autoplayEnabled.value) { params.set('autoplay', '1'); params.set('mute', '1') }
    return { kind: 'iframe' as const, provider: 'youtube' as const, src: `https://www.youtube.com/embed/${yt[1]}?${params}` }
  }

  // Handles /file/d/<id>/view, /open?id=<id>, and /uc?id=<id> share link forms.
  // Note: the file must be shared as "Anyone with the link can view" in Drive,
  // or this will embed an access-denied page instead of the video.
  const drive = url.match(/drive\.google\.com\/(?:file\/d\/|open\?id=|uc\?id=)([\w-]+)/)
  if (drive) return { kind: 'iframe' as const, provider: 'drive' as const, src: `https://drive.google.com/file/d/${drive[1]}/preview` }

  return { kind: 'video' as const, provider: 'file' as const, src: url }
})

function onVideoEnded() {
  if (autoplayEnabled.value) goToNextModule()
}

// ── YouTube IFrame Player API (auto-advance on end) ─────
declare global {
  interface Window {
    YT: any
    onYouTubeIframeAPIReady?: () => void
  }
}

let ytPlayer: any = null
let ytApiPromise: Promise<void> | null = null

function loadYouTubeApi(): Promise<void> {
  if (window.YT?.Player) return Promise.resolve()
  if (ytApiPromise) return ytApiPromise
  ytApiPromise = new Promise((resolve) => {
    const prevCallback = window.onYouTubeIframeAPIReady
    window.onYouTubeIframeAPIReady = () => { prevCallback?.(); resolve() }
    if (!document.querySelector('script[src="https://www.youtube.com/iframe_api"]')) {
      const tag = document.createElement('script')
      tag.src = 'https://www.youtube.com/iframe_api'
      document.head.appendChild(tag)
    }
  })
  return ytApiPromise
}

async function bindYouTubePlayer() {
  if (videoEmbed.value?.provider !== 'youtube') return
  await loadYouTubeApi()
  await nextTick()
  const el = document.getElementById('yt-iframe')
  if (!el) return
  ytPlayer = new window.YT.Player('yt-iframe', {
    events: {
      onStateChange: (e: any) => {
        if (e.data === window.YT.PlayerState.ENDED && autoplayEnabled.value) {
          goToNextModule()
        }
      },
    },
  })
}

watch(videoEmbed, (v) => {
  if (v?.provider === 'youtube') bindYouTubePlayer()
}, { immediate: true })

// Article content is authored as Markdown in the admin editor — render it
// properly (headings, lists, bold/italic, links, code, quotes) rather than
// dumping raw text into flat paragraphs, and sanitize before injecting.
const articleHtml = computed(() => {
  const text = module.value?.rich_content
  if (!text) return ''
  return DOMPurify.sanitize(marked.parse(text, { async: false }) as string)
})

const CIRCLE_R = 22
const CIRCLE_C = 2 * Math.PI * CIRCLE_R
const circleOffset = computed(() => CIRCLE_C - (pathPct.value / 100) * CIRCLE_C)
</script>

<template>
  <div class="page">
    <div v-if="!module" class="loading">Loading…</div>

    <template v-else>
      <div v-if="isPreview" class="preview-banner">
        <i class="ti ti-eye" /> Previewing as admin — this won't affect your own progress or history.
      </div>

      <!-- Two-column layout -->
      <div class="mod-layout">

        <!-- LEFT: main content -->
        <div class="mod-main">

          <template v-if="module.module_type === 'v' || module.module_type === 'l'">
            <!-- Real embedded video (YouTube, Google Drive, or direct file) -->
            <div v-if="videoEmbed" class="video-wrap video-wrap-real">
              <iframe
                v-if="videoEmbed.kind === 'iframe'"
                :key="videoEmbed.src"
                :id="videoEmbed.provider === 'youtube' ? 'yt-iframe' : undefined"
                class="video-embed"
                :src="videoEmbed.src"
                title="Module video"
                frameborder="0"
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
                allowfullscreen
              />
              <video
                v-else
                :key="videoEmbed.src"
                class="video-embed"
                :src="videoEmbed.src"
                :autoplay="autoplayEnabled"
                :muted="autoplayEnabled"
                playsinline
                controls
                @ended="onVideoEnded"
              />
            </div>

            <!-- Placeholder player (no video attached) -->
            <div v-else class="video-wrap">
              <div class="video-inner">
                <div class="video-badge">
                  {{ productLabel(module.product).toUpperCase() }} · VIDEO
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
          </template>

          <!-- Podcast -->
          <div v-else-if="module.module_type === 'p'" class="video-wrap video-wrap-real podcast-wrap">
            <div v-if="module.video_url" class="podcast-player">
              <div class="podcast-icon"><i class="ti ti-microphone" /></div>
              <audio class="podcast-audio" :src="module.video_url" :autoplay="autoplayEnabled" controls @ended="onVideoEnded" />
            </div>
            <div v-else class="video-inner">
              <div class="video-badge">{{ productLabel(module.product).toUpperCase() }} · PODCAST</div>
              <div class="video-play-btn"><i class="ti ti-microphone" /></div>
            </div>
          </div>

          <!-- Slides -->
          <div v-else-if="module.module_type === 's'" class="video-wrap video-wrap-real">
            <iframe
              v-if="module.video_url"
              class="video-embed"
              :src="module.video_url"
              title="Module slides"
              frameborder="0"
              allowfullscreen
            />
            <div v-else class="video-inner">
              <div class="video-badge">{{ productLabel(module.product).toUpperCase() }} · SLIDES</div>
              <div class="video-play-btn"><i class="ti ti-presentation" /></div>
            </div>
          </div>

          <!-- Article banner (no video console for text content) -->
          <div v-else class="article-banner">
            <div class="article-banner-icon"><i class="ti ti-file-text" /></div>
            <div class="article-banner-label">
              {{ productLabel(module.product).toUpperCase() }} · ARTICLE
            </div>
          </div>

          <!-- Title + actions -->
          <div class="mod-header">
            <div class="mod-title-row">
              <h1 class="mod-title">{{ module.title }}</h1>
              <div v-if="!isPreview" class="mod-actions">
                <button class="btn btn-ghost save-btn" @click="toggleSave">
                  <i :class="['ti', savedIds.has(Number(route.params.id)) ? 'ti-bookmark-filled' : 'ti-bookmark']" />
                  {{ savedIds.has(Number(route.params.id)) ? 'Saved' : 'Save' }}
                </button>
                <button v-if="completing" class="btn btn-primary" disabled>
                  <i class="ti ti-loader-2" style="animation: spin 0.8s linear infinite" /> Marking complete…
                </button>
                <button v-else-if="!isDone" class="btn btn-primary" @click="markDone">
                  <i class="ti ti-circle-check" /> Mark complete
                </button>
                <template v-else>
                  <div class="done-badge">
                    <i class="ti ti-circle-check-filled" /> Completed
                  </div>
                  <button v-if="justCompleted && nextModule" class="btn btn-primary next-lesson-btn" @click="goToNextModule">
                    Next lesson <i class="ti ti-arrow-right" />
                  </button>
                  <div v-else-if="justCompleted" class="tier-done-badge">
                    <i class="ti ti-confetti" /> Tier complete
                  </div>
                </template>
              </div>
            </div>
            <div class="mod-meta-row">
              <span class="pill" :style="{ background: TYPE_PILL_BG[module.module_type] ?? '#FBF1E3', color: TYPE_PILL_FG[module.module_type] ?? '#B26A00' }">
                <i :class="['ti', moduleIcon(module.module_type)]" />
                {{ TYPE_LABEL[module.module_type] ?? 'Article' }}
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

            <div
              v-if="module.module_type === 'a' && articleHtml"
              class="article-body"
              v-html="articleHtml"
            />

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
          <div v-else-if="activeTab === 'transcript' && module.transcript" class="tab-content">
            <div class="article-body">
              <p v-for="(para, i) in module.transcript.split(/\n\s*\n/)" :key="i">{{ para }}</p>
            </div>
          </div>
          <div v-else-if="activeTab === 'transcript'" class="tab-content tab-empty">
            <i class="ti ti-file-text tab-empty-icon" />
            <p>No transcript has been added for this module yet.</p>
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
          <div v-if="!isPreview" class="rail-progress-card">
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
              <button
                type="button"
                class="rail-autoplay"
                :class="{ active: autoplayEnabled }"
                @click="autoplayEnabled = !autoplayEnabled"
                :title="autoplayEnabled ? 'Autoplay is on — click to turn off' : 'Autoplay is off — click to turn on'"
              >
                <i class="ti ti-player-track-next" /> Autoplay
              </button>
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
.preview-banner {
  display: flex; align-items: center; gap: 8px;
  background: var(--purple-subtle); color: var(--purple);
  font-size: 13px; font-weight: 600;
  padding: 10px 28px;
}

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
.video-wrap-real { border-radius: 12px; overflow: hidden; }
.video-embed { display: block; width: 100%; aspect-ratio: 16 / 9; border: 0; background: #000; }
.podcast-wrap.video-wrap-real { border-radius: 12px; }
.podcast-player {
  display: flex; flex-direction: column; align-items: center; gap: 18px;
  padding: 40px 28px; background: linear-gradient(160deg, #1A0A3C 0%, #0F0A1A 60%);
}
.podcast-icon {
  width: 64px; height: 64px; border-radius: 50%;
  background: rgba(255,255,255,0.14);
  display: flex; align-items: center; justify-content: center;
  font-size: 26px; color: #fff;
}
.podcast-audio { width: 100%; max-width: 460px; }
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

/* ── Article banner (replaces video console for text modules) ──────────── */
.article-banner {
  background: linear-gradient(160deg, #1A0A3C 0%, #0F0A1A 60%);
  border-radius: 12px;
  padding: 28px;
  display: flex;
  align-items: center;
  gap: 12px;
}
.article-banner-icon {
  width: 44px; height: 44px; border-radius: 50%;
  background: rgba(255,255,255,0.14);
  display: flex; align-items: center; justify-content: center;
  font-size: 20px; color: #fff; flex-shrink: 0;
}
.article-banner-label {
  font-size: 12px; font-weight: 700; letter-spacing: 0.6px;
  color: rgba(255,255,255,0.75);
}

/* ── Article body ──────────────────────────────────────────
   Content is injected via v-html (rendered Markdown), so scoped styles
   can't reach it directly — :deep() targets the injected elements. */
.article-body {
  font-size: 15px;
  color: var(--text-primary);
  line-height: 1.75;
  max-width: 680px;
}
.article-body :deep(> *:first-child) { margin-top: 0; }
.article-body :deep(> *:last-child) { margin-bottom: 0; }

.article-body :deep(p) { margin: 0 0 16px; }

.article-body :deep(h1),
.article-body :deep(h2),
.article-body :deep(h3) {
  font-weight: 800;
  letter-spacing: -0.3px;
  color: var(--text-primary);
  margin: 32px 0 12px;
  line-height: 1.3;
}
.article-body :deep(h1) { font-size: 22px; }
.article-body :deep(h2) { font-size: 18px; }
.article-body :deep(h3) { font-size: 15.5px; }

.article-body :deep(ul),
.article-body :deep(ol) {
  margin: 0 0 16px;
  padding-left: 22px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.article-body :deep(li) { line-height: 1.6; }
.article-body :deep(li > ul),
.article-body :deep(li > ol) { margin: 6px 0 0; }

.article-body :deep(strong) { font-weight: 700; color: var(--text-primary); }
.article-body :deep(em) { font-style: italic; }

.article-body :deep(a) {
  color: var(--purple);
  font-weight: 600;
  text-decoration: none;
  border-bottom: 1px solid rgba(110,43,240,0.35);
}
.article-body :deep(a:hover) { border-bottom-color: var(--purple); }

.article-body :deep(blockquote) {
  margin: 0 0 16px;
  padding: 10px 16px;
  border-left: 3px solid var(--purple);
  background: var(--purple-subtle);
  border-radius: 0 8px 8px 0;
  color: var(--text-secondary);
}
.article-body :deep(blockquote p) { margin-bottom: 0; }

.article-body :deep(code) {
  font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
  font-size: 13px;
  background: var(--purple-subtle);
  color: var(--purple);
  padding: 2px 6px;
  border-radius: 5px;
}
.article-body :deep(pre) {
  margin: 0 0 16px;
  padding: 14px 16px;
  background: #1A1622;
  border-radius: 10px;
  overflow-x: auto;
}
.article-body :deep(pre code) {
  background: none;
  color: #E8E3F5;
  padding: 0;
  font-size: 13px;
  line-height: 1.6;
}

.article-body :deep(hr) {
  border: none;
  border-top: 1px solid var(--border);
  margin: 28px 0;
}

.article-body :deep(img) {
  max-width: 100%;
  border-radius: 10px;
  margin: 8px 0 16px;
}

.article-body :deep(table) {
  width: 100%;
  border-collapse: collapse;
  margin: 0 0 16px;
  font-size: 13.5px;
}
.article-body :deep(th),
.article-body :deep(td) {
  text-align: left;
  padding: 8px 12px;
  border: 1px solid var(--border);
}
.article-body :deep(th) { background: var(--surface); font-weight: 700; }

/* ── Module header ────────────────────────────────────── */
.mod-header { padding: 20px 28px 0; }
.mod-title-row { display: flex; align-items: flex-start; justify-content: space-between; gap: 16px; margin-bottom: 10px; }
.mod-title { font-size: 20px; font-weight: 800; letter-spacing: -0.4px; line-height: 1.3; flex: 1; }
.mod-actions { display: flex; gap: 8px; align-items: center; flex-shrink: 0; }
.save-btn { font-size: 13px; }
.done-badge { display: flex; align-items: center; gap: 5px; font-size: 13.5px; font-weight: 600; color: var(--green); }
.next-lesson-btn { font-size: 13px; animation: fade-in-up 0.25s ease; }
.tier-done-badge {
  display: flex; align-items: center; gap: 5px;
  font-size: 12.5px; font-weight: 600; color: var(--purple);
  animation: fade-in-up 0.25s ease;
}
@keyframes spin { to { transform: rotate(360deg); } }
@keyframes fade-in-up { from { opacity: 0; transform: translateY(4px); } to { opacity: 1; transform: translateY(0); } }
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
.rail-autoplay {
  font-size: 11px; color: var(--text-muted); display: flex; align-items: center; gap: 3px;
  background: none; border: none; cursor: pointer; padding: 3px 6px; border-radius: 6px;
  transition: background 0.1s, color 0.1s;
}
.rail-autoplay:hover { background: var(--purple-subtle); }
.rail-autoplay.active { color: var(--purple); font-weight: 600; }

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
