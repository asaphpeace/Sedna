<script setup lang="ts">
import { computed, onMounted } from 'vue'
import HubHeader from '@/components/hub/HubHeader.vue'
import { useCatalog, type Course } from '@/composables/useCatalog'

// Nassia's "Learning: Sedna VMS" screen. Cards open a customer course once
// one with real content exists; until then they say so.
const { courses, signedIn, load, match } = useCatalog()
onMounted(load)

const vms = computed(() => courses.value.filter(c => c.products?.includes('vms')))
const customer = computed(() => vms.value.filter(c => c.audience === 'customer'))
const internal = computed(() => vms.value.filter(c => c.audience !== 'customer'))

const find = (keywords: string[]): Course | undefined => match(customer.value, keywords)
const roles = computed(() => [
  { title: 'Chartering', sub: 'Estimates and fixtures', course: find(['charter']) },
  { title: 'Trading', sub: 'Positions and P&L', course: find(['trading', 'trader']) },
  { title: 'Operations', sub: 'Voyage execution', course: find(['operat']) },
  { title: 'Accounting', sub: 'Invoices and settlement', course: find(['account']) },
])
const functions = computed(() => [
  { code: '4.A', title: 'VMS Invoicing', course: find(['invoic']) },
  { code: '4.B', title: 'Bunkers Management', course: find(['bunker']) },
  { code: '4.C', title: 'Laytime Calculations', course: find(['laytime']) },
])
const whatIs = computed(() => find(['what is', 'introduction']))
const navigate = computed(() => find(['navigat']))
</script>

<template>
  <div class="hub-page">
    <HubHeader />
    <main id="main-content" class="hub-main">
      <nav aria-label="Breadcrumb" class="hub-breadcrumb">
        <RouterLink to="/">LEARNING HUB</RouterLink><span>/</span>
        <RouterLink to="/learning">LEARNING</RouterLink><span>/</span><span class="current">SEDNA VMS</span>
      </nav>
      <div class="hub-intro">
        <h1 class="hub-h1">Sedna VMS</h1>
        <p class="hub-lead">Learn the system, follow the onboarding path for your role, then go deeper into the VMS functions you use every day.</p>
      </div>

      <ol class="hub-steps">
        <li class="hub-step">
          <span class="hub-step-num">01</span>
          <div class="hub-step-body">
            <h2 class="hub-step-title">What is Sedna VMS</h2>
            <p class="hub-step-desc">How voyages, estimates and financials connect, and where the VMS fits in Sedna.</p>
          </div>
          <span class="hub-tag hub-tag--lilac">Foundations</span>
          <RouterLink v-if="whatIs" :to="`/paths/${whatIs.id}`" class="hub-step-link">{{ whatIs.mod_count }} module{{ whatIs.mod_count === 1 ? '' : 's' }} →</RouterLink>
          <span v-else class="hub-step-meta">In preparation</span>
        </li>
        <li class="hub-step">
          <span class="hub-step-num">02</span>
          <div class="hub-step-body">
            <h2 class="hub-step-title">Navigate VMS</h2>
            <p class="hub-step-desc">Menus, views and records: how to move around and find what you need.</p>
          </div>
          <span class="hub-tag hub-tag--lilac">Foundations</span>
          <RouterLink v-if="navigate" :to="`/paths/${navigate.id}`" class="hub-step-link">{{ navigate.mod_count }} module{{ navigate.mod_count === 1 ? '' : 's' }} →</RouterLink>
          <span v-else class="hub-step-meta">In preparation</span>
        </li>
        <li class="hub-step hub-step--group">
          <div class="hub-step-head">
            <span class="hub-step-num">03</span>
            <div class="hub-step-body">
              <h2 class="hub-step-title">Onboarding path by role</h2>
              <p class="hub-step-desc">Choose your role for a path built around your daily workflows in the VMS.</p>
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
              <span class="hub-option-sub">Added as needed</span>
            </div>
          </div>
        </li>
        <li class="hub-step hub-step--group">
          <div class="hub-step-head">
            <span class="hub-step-num">04</span>
            <div class="hub-step-body">
              <h2 class="hub-step-title">Function paths</h2>
              <p class="hub-step-desc">Deep dives into one VMS function each, for anyone who owns that work.</p>
            </div>
            <span class="hub-tag hub-tag--mint">Advanced</span>
          </div>
          <div class="hub-options hub-options--wide">
            <template v-for="f in functions" :key="f.code">
              <RouterLink v-if="f.course" :to="`/paths/${f.course.id}`" class="hub-option">
                <span class="hub-eyebrow">{{ f.code }}</span>
                <span class="hub-option-title">{{ f.title }}</span>
                <span class="hub-option-status">{{ f.course.mod_count }} MODULE{{ f.course.mod_count === 1 ? '' : 'S' }} →</span>
              </RouterLink>
              <div v-else class="hub-option">
                <span class="hub-eyebrow">{{ f.code }}</span>
                <span class="hub-option-title">{{ f.title }}</span>
                <span class="hub-option-status">IN PREPARATION</span>
              </div>
            </template>
            <div class="hub-option hub-option--soon">
              <span class="hub-eyebrow">COMING NEXT</span>
              <span class="hub-option-title">Next function</span>
            </div>
          </div>
        </li>
      </ol>

      <section v-if="signedIn && internal.length" class="hub-card staff">
        <div class="hub-eyebrow">FOR SEDNA TEAMS · ONLY VISIBLE WHEN SIGNED IN</div>
        <h2 class="hub-h2">Internal VMS paths</h2>
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
.hub-options--wide { grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); }
.meta { color: #6B6C75; }
</style>
