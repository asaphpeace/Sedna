<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import HubHeader from '@/components/hub/HubHeader.vue'
import { publicApi } from '@/api'
import { SUPPORT } from '@/constants/hubLinks'

// Knowledge Base (how-tos, explainers) and Help Center (troubleshooting,
// support processes) in the style of Nassia's Hub pages. Public: no sign-in.
const props = defineProps<{ section: 'knowledge-base' | 'help-center' }>()

const copy = computed(() => props.section === 'knowledge-base'
  ? {
      crumb: 'KNOWLEDGE BASE', eyebrow: '01 / REFERENCE', title: 'Knowledge Base',
      lead: 'How things work in Sedna VMS: step-by-step guides and explanations of the parts customers ask about most.',
    }
  : {
      crumb: 'HELP CENTER', eyebrow: '02 / SUPPORT', title: 'Help Center',
      lead: "Fix a problem, make a request, or reach the Support team, with what to include so it's sorted quickly.",
    })

const articles = ref<any[]>([])
const loaded = ref(false)
const query = ref('')

async function load() {
  loaded.value = false
  try {
    articles.value = (await publicApi.articles({ section: props.section })).data
  } finally {
    loaded.value = true
  }
}
onMounted(load)
watch(() => props.section, () => { query.value = ''; load() })

const visible = computed(() => {
  const q = query.value.trim().toLowerCase()
  if (!q) return articles.value
  return articles.value.filter(a => `${a.title} ${a.summary} ${a.topic}`.toLowerCase().includes(q))
})
const groups = computed(() => {
  const by = new Map<string, any[]>()
  for (const a of visible.value) {
    const key = a.topic || 'General'
    by.set(key, [...(by.get(key) ?? []), a])
  }
  return [...by.entries()].map(([topic, items]) => ({ topic, items }))
})
const anySample = computed(() => articles.value.some(a => a.is_sample))
const kindTag = (kind: string) => ({ 'How-to': 'hub-tag--sky', Explainer: 'hub-tag--lilac', Troubleshooting: 'hub-tag--mint', Process: 'hub-tag--grey' } as Record<string, string>)[kind] ?? 'hub-tag--grey'
</script>

<template>
  <div class="hub-page">
    <HubHeader />
    <main id="main-content" class="hub-main">
      <nav aria-label="Breadcrumb" class="hub-breadcrumb">
        <RouterLink to="/">LEARNING HUB</RouterLink><span>/</span><span class="current">{{ copy.crumb }}</span>
      </nav>
      <div class="hub-intro">
        <div class="hub-eyebrow">{{ copy.eyebrow }}</div>
        <h1 class="hub-h1">{{ copy.title }}</h1>
        <p class="hub-lead">{{ copy.lead }}</p>
        <label class="search">
          <span class="sr-only">Search {{ copy.title }}</span>
          <input v-model="query" type="search" class="search-input" :placeholder="section === 'knowledge-base' ? 'e.g. bunkers, laytime, accruals' : 'e.g. pending, slow, new port'" />
        </label>
      </div>

      <p v-if="anySample" class="sample-note" role="note">
        These are sample articles for Sedna VMS, drafted from real support cases and under review by the Education and Support teams.
      </p>

      <div v-if="loaded && groups.length" class="hub-grid">
        <section v-for="g in groups" :key="g.topic" class="hub-card">
          <div class="hub-eyebrow">SEDNA VMS</div>
          <h2 class="hub-h2 topic-h">{{ g.topic }}</h2>
          <div class="hub-rows">
            <RouterLink v-for="a in g.items" :key="a.slug" :to="`/help/${a.slug}`" class="hub-row article-row">
              <span class="row-text">
                <span>{{ a.title }}</span>
                <span class="hub-tag" :class="kindTag(a.kind)">{{ a.kind }}</span>
              </span>
              <span class="arrow">→</span>
            </RouterLink>
          </div>
        </section>
      </div>
      <p v-else-if="loaded && query" class="hub-p">Nothing here matches “{{ query }}”. Try the search on support.sedna.com below.</p>
      <p v-else-if="loaded" class="hub-p">No articles here yet.</p>

      <section class="hub-card hub-card--warm">
        <div class="hub-eyebrow">MORE HELP</div>
        <div class="hub-rows">
          <template v-if="section === 'knowledge-base'">
            <a :href="SUPPORT.vmsDocs" target="_blank" rel="noopener" class="hub-row">Sedna VMS product documentation <span class="arrow">↗</span></a>
            <a :href="SUPPORT.emailDocs" target="_blank" rel="noopener" class="hub-row">Sedna Email articles on support.sedna.com <span class="arrow">↗</span></a>
            <a href="https://api.dataloy.com" target="_blank" rel="noopener" class="hub-row">Sedna VMS API documentation <span class="arrow">↗</span></a>
          </template>
          <template v-else>
            <a :href="SUPPORT.vmsPortal" target="_blank" rel="noopener" class="hub-row hub-row--soft">Log a Sedna VMS support case <span class="arrow">↗</span></a>
            <a :href="SUPPORT.newRequest" target="_blank" rel="noopener" class="hub-row">Contact Sedna Email support <span class="arrow">↗</span></a>
            <a :href="SUPPORT.search(query || 'help')" target="_blank" rel="noopener" class="hub-row">Search support.sedna.com <span class="arrow">↗</span></a>
          </template>
        </div>
      </section>

      <RouterLink to="/" class="hub-back">← Back to the Learning Hub</RouterLink>
    </main>
  </div>
</template>

<style scoped>
.search-input {
  width: 100%; max-width: 560px; min-height: 48px; box-sizing: border-box; border: 1px solid #C2C4CB; border-radius: 8px;
  padding: 0 16px; font-size: 15px; font-family: inherit; background: #FFFFFF; color: #0B0B0F; outline: none;
}
.search-input:focus { border-color: #7A3FE5; box-shadow: 0 0 0 3px #F5EEFF; }
.sample-note { margin: 0; padding: 12px 16px; border-radius: 8px; background: #FBEDC8; color: #633806; font-size: 14px; max-width: 760px; }
.topic-h { font-size: 22px; }
.article-row { min-height: 56px; padding: 10px 14px; gap: 12px; }
.row-text { display: flex; flex-direction: column; align-items: flex-start; gap: 6px; }
.sr-only { position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0 0 0 0); white-space: nowrap; }
</style>
