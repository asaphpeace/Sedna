<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useAppStore } from '@/stores/app'

const props = defineProps<{ title?: string; subtitle?: string }>()

const auth = useAuthStore()
const app = useAppStore()
const router = useRouter()

const greeting = computed(() => {
  const h = new Date().getHours()
  if (h < 12) return 'Good morning'
  if (h < 17) return 'Good afternoon'
  return 'Good evening'
})

const firstName = computed(() => auth.user?.name?.split(' ')[0] ?? '')
const streak = computed(() => app.gamification?.streak?.current ?? 0)
const heroPct = computed(() => app.overallPct)
const weekday = computed(() => new Date().toLocaleDateString('en-GB', { weekday: 'long' }))

const CIRCLE_R = 42
const CIRCLE_C = 2 * Math.PI * CIRCLE_R
const circleOffset = computed(() => CIRCLE_C - (heroPct.value / 100) * CIRCLE_C)

function resumeLearning() {
  if (app.resumePath) router.push(`/paths/${app.resumePath.role_id}`)
  else router.push('/paths')
}
</script>

<template>
  <div class="hero-banner">
    <div class="hero-text">
      <div class="hero-label">
        <template v-if="props.title">{{ props.title }}</template>
        <template v-else>
          {{ weekday.toUpperCase() }}<template v-if="app.resumePath"> · {{ app.resumePath.role_name.toUpperCase() }} PATH</template>
        </template>
      </div>
      <h1 class="hero-heading">
        <template v-if="props.subtitle">{{ props.subtitle }}</template>
        <template v-else>{{ greeting }}, {{ firstName }}</template>
      </h1>
      <p class="hero-sub" v-if="!props.subtitle">
        <template v-if="streak > 0">You're on a {{ streak }}-day learning streak. Pick up where you left off.</template>
        <template v-else>Start learning today to build your streak.</template>
      </p>
      <button class="hero-resume-btn" @click="resumeLearning">
        <span v-if="app.resumePath">Resume: {{ app.resumePath.role_name }} →</span>
        <span v-else>Browse learning paths →</span>
      </button>
    </div>
    <div class="hero-ring" aria-hidden="true">
      <svg viewBox="0 0 100 100" width="120" height="120">
        <circle cx="50" cy="50" :r="CIRCLE_R" fill="none" stroke="rgba(255,255,255,0.12)" stroke-width="8" />
        <circle
          cx="50" cy="50" :r="CIRCLE_R" fill="none"
          stroke="#fff" stroke-width="8" stroke-linecap="round"
          :stroke-dasharray="CIRCLE_C"
          :stroke-dashoffset="circleOffset"
          transform="rotate(-90 50 50)"
          style="transition: stroke-dashoffset 0.6s ease"
        />
        <text x="50" y="46" text-anchor="middle" fill="#fff" font-size="18" font-weight="800" font-family="Hanken Grotesk, sans-serif">{{ heroPct }}%</text>
        <text x="50" y="60" text-anchor="middle" fill="rgba(255,255,255,0.6)" font-size="7.5" font-weight="600" font-family="Hanken Grotesk, sans-serif" letter-spacing="1">PATH PROGRESS</text>
      </svg>
    </div>
    <div class="hero-blob hero-blob-1" />
    <div class="hero-blob hero-blob-2" />
  </div>
</template>

<style scoped>
.hero-banner {
  position: relative; overflow: hidden;
  background: linear-gradient(135deg, #1A0A3C 0%, #2D1060 50%, #1A0A3C 100%);
  border-radius: 16px; padding: 36px 40px;
  display: flex; align-items: center; justify-content: space-between;
  min-height: 170px;
}
.hero-text { flex: 1; position: relative; z-index: 2; }
.hero-label { font-size: 11px; font-weight: 700; letter-spacing: 1.5px; color: rgba(255,255,255,0.55); margin-bottom: 8px; }
.hero-heading { font-size: 30px; font-weight: 800; color: #fff; letter-spacing: -0.5px; line-height: 1.15; margin-bottom: 8px; }
.hero-sub { font-size: 13px; color: rgba(255,255,255,0.65); margin-bottom: 20px; }
.hero-resume-btn {
  display: inline-flex; align-items: center; gap: 6px;
  background: rgba(255,255,255,0.14); border: 1px solid rgba(255,255,255,0.22);
  color: #fff; font-size: 13px; font-weight: 600;
  padding: 9px 20px; border-radius: 10px; cursor: pointer;
  backdrop-filter: blur(4px); font-family: inherit;
  transition: background 0.15s;
}
.hero-resume-btn:hover { background: rgba(255,255,255,0.22); }
.hero-ring { position: relative; z-index: 2; flex-shrink: 0; margin-left: 32px; }
.hero-blob {
  position: absolute; border-radius: 50%; z-index: 1;
  background: radial-gradient(circle, rgba(130,85,242,0.45) 0%, transparent 70%);
}
.hero-blob-1 { width: 260px; height: 260px; right: 60px; top: -80px; }
.hero-blob-2 { width: 180px; height: 180px; right: 180px; bottom: -60px; opacity: 0.6; }
@media (max-width: 768px) {
  .hero-banner { padding: 22px 18px; }
  .hero-heading { font-size: 22px; }
  .hero-ring { display: none; }
}
</style>
