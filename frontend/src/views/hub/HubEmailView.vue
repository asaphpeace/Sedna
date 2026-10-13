<script setup lang="ts">
import { computed, onMounted } from 'vue'
import HubHeader from '@/components/hub/HubHeader.vue'
import { useCatalog, type Course } from '@/composables/useCatalog'
import { SUPPORT } from '@/constants/hubLinks'

// Nassia's "Learning: Sedna Email" screen. The foundations and best practices
// already exist as support.sedna.com articles, so those sections open them;
// Phase 3 brings the articles inside the Hub with progress and quizzes.
const { courses, signedIn, load, match } = useCatalog()
onMounted(load)

const email = computed(() => courses.value.filter(c => c.products?.includes('stream')))
const customer = computed(() => email.value.filter(c => c.audience === 'customer'))
const internal = computed(() => email.value.filter(c => c.audience !== 'customer'))
const find = (keywords: string[]): Course | undefined => match(customer.value, keywords)
const roles = computed(() => [
  { title: 'Charterer', sub: 'Cargoes, positions and negotiation threads', course: find(['charter']) },
  { title: 'Operator', sub: 'Voyage communication and follow-ups', course: find(['operat']) },
])
</script>

<template>
  <div class="hub-page">
    <HubHeader />
    <main id="main-content" class="hub-main">
      <nav aria-label="Breadcrumb" class="hub-breadcrumb">
        <RouterLink to="/">LEARNING HUB</RouterLink><span>/</span>
        <RouterLink to="/learning">LEARNING</RouterLink><span>/</span><span class="current">SEDNA EMAIL</span>
      </nav>
      <div class="hub-intro">
        <h1 class="hub-h1">Sedna Email</h1>
        <p class="hub-lead">Start with the foundations, then follow the onboarding path for your role. Best practices help you shape Sedna Email around how your team works.</p>
      </div>

      <ol class="hub-steps">
        <li class="hub-step">
          <span class="hub-step-num">01</span>
          <div class="hub-step-body">
            <h2 class="hub-step-title">What is Sedna Email</h2>
            <p class="hub-step-desc">Why a shared, intelligent inbox, and what changes from a personal email client.</p>
          </div>
          <span class="hub-tag hub-tag--lilac">Foundations</span>
          <a :href="SUPPORT.whatIsEmail" target="_blank" rel="noopener" class="hub-step-link">Read ↗</a>
        </li>
        <li class="hub-step">
          <span class="hub-step-num">02</span>
          <div class="hub-step-body">
            <h2 class="hub-step-title">Navigate Sedna Email</h2>
            <p class="hub-step-desc">The interface and its spaces: where things live and how to find them.</p>
          </div>
          <span class="hub-tag hub-tag--lilac">Foundations</span>
          <a :href="SUPPORT.levelOne" target="_blank" rel="noopener" class="hub-step-link">Level One ↗</a>
        </li>
        <li class="hub-step">
          <span class="hub-step-num">03</span>
          <div class="hub-step-body">
            <h2 class="hub-step-title">Work with Sedna Email</h2>
            <p class="hub-step-desc">Everyday tasks through real scenarios: threads, tagging, sharing and following up.</p>
          </div>
          <span class="hub-tag hub-tag--sky">Core</span>
          <a :href="SUPPORT.levelTwo" target="_blank" rel="noopener" class="hub-step-link">Level Two ↗</a>
        </li>
        <li class="hub-step hub-step--group">
          <div class="hub-step-head">
            <span class="hub-step-num">04</span>
            <div class="hub-step-body">
              <h2 class="hub-step-title">Onboarding path by role</h2>
              <p class="hub-step-desc">Choose your role for a path built around your daily workflows.</p>
            </div>
            <span class="hub-tag hub-tag--sky">Core</span>
          </div>
          <div class="hub-options">
            <template v-for="r in roles" :key="r.title">
              <RouterLink v-if="r.course" :to="`/paths/${r.course.id}`" class="hub-option">
                <span class="hub-option-title">{{ r.title }}</span>
                <span class="hub-option-sub">{{ r.sub }}</span>
                <span class="hub-option-status">{{ r.course.mod_count }} MODULE{{ r.course.mod_count === 1 ? '' : 'S' }} →</span>
              </RouterLink>
              <div v-else class="hub-option">
                <span class="hub-option-title">{{ r.title }}</span>
                <span class="hub-option-sub">{{ r.sub }}</span>
                <span class="hub-option-status">IN PREPARATION</span>
              </div>
            </template>
            <div class="hub-option hub-option--soon">
              <span class="hub-option-title">More roles</span>
              <span class="hub-option-sub">e.g. Broker, Manager, Admin</span>
            </div>
          </div>
        </li>
        <li class="hub-step">
          <span class="hub-step-num">05</span>
          <div class="hub-step-body">
            <h2 class="hub-step-title">Best practices: make Sedna Email yours</h2>
            <p class="hub-step-desc">Set up views, templates and automation around how your team actually works.</p>
          </div>
          <span class="hub-tag hub-tag--mint">Advanced</span>
          <a :href="SUPPORT.optimise" target="_blank" rel="noopener" class="hub-step-link">Optimise ↗</a>
        </li>
      </ol>

      <section v-if="signedIn && internal.length" class="hub-card">
        <div class="hub-eyebrow">FOR SEDNA TEAMS · ONLY VISIBLE WHEN SIGNED IN</div>
        <h2 class="hub-h2">Internal Sedna Email paths</h2>
        <div class="hub-rows">
          <RouterLink v-for="c in internal" :key="c.id" :to="`/paths/${c.id}`" class="hub-row">
            <span>{{ c.name }} <span class="meta">· {{ c.mod_count }} module{{ c.mod_count === 1 ? '' : 's' }}</span></span><span class="arrow">→</span>
          </RouterLink>
        </div>
      </section>

      <RouterLink to="/learning" class="hub-back">← Back to Learning</RouterLink>
    </main>
  </div>
</template>

<style scoped>
.meta { color: #6B6C75; }
</style>
