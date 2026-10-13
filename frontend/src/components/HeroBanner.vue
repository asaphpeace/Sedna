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
  <section class="hero-banner">
    <div class="hero-text">
      <div class="eyebrow hero-label">
        <template v-if="props.title">{{ props.title }}</template>
        <template v-else>
          {{ weekday.toUpperCase() }}<template v-if="app.resumePath"> / {{ app.resumePath.role_name.toUpperCase() }} PATH</template>
        </template>
      </div>
      <h1 class="hero-heading">
        <template v-if="props.subtitle">{{ props.subtitle }}</template>
        <template v-else>{{ greeting }}, {{ firstName }}</template>
      </h1>
      <p class="hero-sub" v-if="!props.subtitle">
        <template v-if="streak > 0">You're on a {{ streak }}-day learning streak. Pick up where you left off.</template>
        <template v-else>Pick a path for your role and start where it makes sense for you.</template>
      </p>
      <button class="btn btn-primary hero-resume-btn" @click="resumeLearning">
        <span v-if="app.resumePath">Resume: {{ app.resumePath.role_name }} →</span>
        <span v-else>Browse learning paths →</span>
      </button>
    </div>
    <div class="hero-ring" aria-hidden="true">
      <svg viewBox="0 0 100 100" width="132" height="132">
        <circle cx="50" cy="50" :r="CIRCLE_R" fill="none" stroke="#ECDEFE" stroke-width="6" />
        <circle
          cx="50" cy="50" :r="CIRCLE_R" fill="none"
          stroke="#7A3FE5" stroke-width="6" stroke-linecap="round"
          :stroke-dasharray="CIRCLE_C"
          :stroke-dashoffset="circleOffset"
          transform="rotate(-90 50 50)"
          style="transition: stroke-dashoffset 0.6s ease"
        />
        <text x="50" y="50" text-anchor="middle" fill="#0B0B0F" font-size="20" font-weight="500" font-family="Helvetica Neue, sans-serif">{{ heroPct }}%</text>
        <text x="50" y="63" text-anchor="middle" fill="#6B6C75" font-size="6.5" font-family="JetBrains Mono, monospace" letter-spacing="0.6">PATH PROGRESS</text>
      </svg>
    </div>
  </section>
</template>

<style scoped>
.hero-banner {
  background: var(--surface); border: 1px solid var(--hairline); border-radius: var(--radius);
  box-shadow: var(--shadow); padding: 40px;
  display: flex; align-items: center; justify-content: space-between; gap: 32px;
}
.hero-text { flex: 1; display: flex; flex-direction: column; align-items: flex-start; gap: 14px; max-width: 760px; }
.hero-heading { font-size: 48px; line-height: 1.12; font-weight: 500; letter-spacing: -0.012em; color: var(--text-primary); }
.hero-sub { font-size: 17px; line-height: 1.5; color: var(--text-secondary); }
.hero-resume-btn { margin-top: 6px; }
.hero-ring { flex-shrink: 0; }
@media (max-width: 768px) {
  .hero-banner { padding: 24px; }
  .hero-heading { font-size: 32px; }
  .hero-ring { display: none; }
}
</style>
