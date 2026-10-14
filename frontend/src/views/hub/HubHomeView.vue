<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import HubHeader from '@/components/hub/HubHeader.vue'
import { useCatalog } from '@/composables/useCatalog'
import { publicApi } from '@/api'
import { SUPPORT } from '@/constants/hubLinks'

// Nassia's "Learning Hub home" screen. The cohorts banner arrives in Phase 5.
const { courses, load } = useCatalog()
onMounted(load)

const query = ref('')
const searched = ref('')
const articleResults = ref<any[]>([])
async function search() {
  searched.value = query.value.trim()
  articleResults.value = searched.value
    ? (await publicApi.articles({ q: searched.value }).catch(() => ({ data: [] }))).data
    : []
}

const results = computed(() => {
  const q = searched.value.toLowerCase()
  if (!q) return []
  return courses.value.filter(c => `${c.name} ${c.description}`.toLowerCase().includes(q))
})
const supportSearchUrl = computed(() => SUPPORT.search(searched.value))
</script>

<template>
  <div class="hub-page">
    <HubHeader />
    <main id="main-content" class="hub-main hub-main--home">
      <div class="hub-intro search-block">
        <div class="hub-eyebrow">SEDNA LEARNING HUB</div>
        <h1 class="hub-h1">Find an answer, get help, or learn a workflow.</h1>
        <form class="search" role="search" @submit.prevent="search">
          <label for="hub-search" class="search-label">Search across the Knowledge Base, Help Center and Learning</label>
          <div class="search-row">
            <input id="hub-search" v-model="query" type="search" class="search-input"
              placeholder="e.g. laytime calculation, shared inbox, bunker invoice" />
            <button type="submit" class="hub-btn">Search</button>
          </div>
        </form>

        <div v-if="searched" class="results" aria-live="polite">
          <div class="hub-eyebrow">LEARNING</div>
          <RouterLink v-for="c in results" :key="c.id" :to="`/paths/${c.id}`" class="hub-row">
            <span>{{ c.name }} <span class="result-meta">· {{ c.mod_count }} module{{ c.mod_count === 1 ? '' : 's' }}</span></span>
            <span class="arrow">→</span>
          </RouterLink>
          <p v-if="!results.length" class="hub-p">No learning paths match “{{ searched }}” yet.</p>
          <div class="hub-eyebrow results-gap">KNOWLEDGE BASE AND HELP CENTER</div>
          <RouterLink v-for="a in articleResults" :key="a.slug" :to="`/help/${a.slug}`" class="hub-row">
            <span>{{ a.title }} <span class="result-meta">· {{ a.kind }}</span></span><span class="arrow">→</span>
          </RouterLink>
          <a :href="supportSearchUrl" target="_blank" rel="noopener" class="hub-row hub-row--soft">
            <span>Search support.sedna.com for “{{ searched }}”</span><span class="arrow">↗</span>
          </a>
        </div>
      </div>

      <div class="hub-grid">
        <section id="kb" class="hub-card">
          <div class="hub-eyebrow">01 / REFERENCE</div>
          <h2 class="hub-h2">Knowledge Base</h2>
          <p class="hub-p">Product documentation: how each feature works, settings, and release notes.</p>
          <div class="hub-rows">
            <a :href="SUPPORT.emailDocs" target="_blank" rel="noopener" class="hub-row">Sedna Email <span class="arrow">↗</span></a>
            <RouterLink to="/knowledge-base" class="hub-row">Sedna VMS <span class="arrow">→</span></RouterLink>
            <a :href="SUPPORT.search('CompassAir')" target="_blank" rel="noopener" class="hub-row">CompassAir <span class="arrow">↗</span></a>
            <a :href="SUPPORT.search('Sedna AI')" target="_blank" rel="noopener" class="hub-row">Sedna AI <span class="arrow">↗</span></a>
          </div>
        </section>

        <section id="help" class="hub-card">
          <div class="hub-eyebrow">02 / SUPPORT</div>
          <h2 class="hub-h2">Help Center</h2>
          <p class="hub-p">Troubleshooting, account and login help, and a direct line to the Support team.</p>
          <div class="hub-rows">
            <a :href="SUPPORT.search('login')" target="_blank" rel="noopener" class="hub-row">Login and access help <span class="arrow">↗</span></a>
            <RouterLink to="/help-center" class="hub-row">Troubleshooting <span class="arrow">→</span></RouterLink>
            <a :href="SUPPORT.requests" target="_blank" rel="noopener" class="hub-row">Track my requests <span class="arrow">↗</span></a>
            <a :href="SUPPORT.newRequest" target="_blank" rel="noopener" class="hub-row hub-row--soft">Contact Support <span class="arrow">↗</span></a>
          </div>
        </section>

        <section class="hub-card hub-card--accent">
          <div class="hub-eyebrow hub-eyebrow--accent">03 / LEARNING</div>
          <h2 class="hub-h2">Learning</h2>
          <p class="hub-p">Guided paths by product and role, from your first login to advanced workflows.</p>
          <div class="hub-rows">
            <RouterLink to="/learning/email" class="hub-row">Sedna Email <span class="arrow">→</span></RouterLink>
            <RouterLink to="/learning/vms" class="hub-row">Sedna VMS <span class="arrow">→</span></RouterLink>
            <RouterLink :to="{ path: '/learning', hash: '#global' }" class="hub-row">Global resources <span class="arrow">→</span></RouterLink>
            <RouterLink to="/learning" class="hub-row hub-row--primary">Start learning <span class="arrow">→</span></RouterLink>
          </div>
        </section>
      </div>
    </main>
  </div>
</template>

<style scoped>
.search-block { gap: 18px; }
.search { display: flex; flex-direction: column; gap: 18px; }
.search-label { font-size: 14px; color: #3A3B42; }
.search-row { display: flex; gap: 8px; flex-wrap: wrap; }
.search-input {
  flex: 1 1 360px; min-height: 48px; box-sizing: border-box; border: 1px solid #C2C4CB; border-radius: 8px;
  padding: 0 16px; font-size: 15px; font-family: inherit; background: #FFFFFF; color: #0B0B0F; outline: none;
}
.search-input:focus { border-color: #7A3FE5; box-shadow: 0 0 0 3px #F5EEFF; }
.results { display: flex; flex-direction: column; gap: 8px; }
.results-gap { margin-top: 10px; }
.result-meta { color: #6B6C75; }
</style>
