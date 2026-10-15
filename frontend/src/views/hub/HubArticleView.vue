<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { marked } from 'marked'
import DOMPurify from 'dompurify'
import HubHeader from '@/components/hub/HubHeader.vue'
import { publicApi } from '@/api'
import { SUPPORT } from '@/constants/hubLinks'

// One Knowledge Base or Help Center article, public before sign-in.
const route = useRoute()
const article = ref<any>(null)
const missing = ref(false)

async function load(slug: string) {
  article.value = null
  missing.value = false
  try {
    article.value = (await publicApi.article(slug)).data
    document.title = `${article.value.title} · Sedna Learning Hub`
  } catch {
    missing.value = true
  }
}
watch(() => route.params.slug as string, s => s && load(s), { immediate: true })

const isKb = computed(() => article.value?.section === 'knowledge-base')
const sectionLink = computed(() => isKb.value ? '/knowledge-base' : '/help-center')
const sectionName = computed(() => isKb.value ? 'KNOWLEDGE BASE' : 'HELP CENTER')

// Markdown, sanitised, with GitHub-style "> [!TIP]" blockquotes turned into callouts
const CALLOUTS: Record<string, string> = { TIP: 'Good to know', NOTE: 'Note', WARNING: 'Watch out for this' }
const html = computed(() => {
  if (!article.value) return ''
  let out = marked.parse(article.value.body, { async: false }) as string
  out = out.replace(/<blockquote>\s*<p>\[!(TIP|NOTE|WARNING)\]\s*/g,
    (_, kind) => `<blockquote class="callout callout-${kind.toLowerCase()}"><p><strong class="callout-head">${CALLOUTS[kind]}</strong><br>`)
  return DOMPurify.sanitize(out, { ADD_ATTR: ['target', 'rel'] })
})
const updated = computed(() => article.value?.updated_at
  ? new Date(article.value.updated_at).toLocaleDateString('en-GB', { day: 'numeric', month: 'long', year: 'numeric' }) : '')
</script>

<template>
  <div class="hub-page">
    <HubHeader />
    <main id="main-content" class="hub-main article-main">
      <template v-if="article">
        <nav aria-label="Breadcrumb" class="hub-breadcrumb">
          <RouterLink to="/">LEARNING HUB</RouterLink><span>/</span>
          <RouterLink :to="sectionLink">{{ sectionName }}</RouterLink><span>/</span>
          <span class="current">{{ article.topic.toUpperCase() }}</span>
        </nav>

        <div class="hub-intro">
          <div class="hub-tags">
            <span class="hub-tag hub-tag--lilac">Sedna VMS</span>
            <span class="hub-tag hub-tag--grey">{{ article.kind }}</span>
            <span v-if="article.is_sample" class="hub-tag sample-tag">Sample, under review</span>
          </div>
          <h1 class="hub-h1 article-h1">{{ article.title }}</h1>
          <p class="hub-lead"><span class="for-you">This is for you if:</span> {{ article.summary }}</p>
        </div>

        <article class="hub-card article-body" v-html="html" />

        <div class="hub-grid after">
          <RouterLink v-if="article.related_path" :to="`/paths/${article.related_path.id}`" class="hub-card hub-card--accent">
            <div class="hub-eyebrow hub-eyebrow--accent">LEARN IT PROPERLY</div>
            <h2 class="hub-h2 small-h">{{ article.related_path.name }}</h2>
            <p class="hub-p">Short lessons and a quiz on this topic. Sign in to start.</p>
            <span class="hub-cta">Open the learning path →</span>
          </RouterLink>
          <section class="hub-card hub-card--warm">
            <div class="hub-eyebrow">STILL STUCK?</div>
            <h2 class="hub-h2 small-h">Contact Sedna VMS Support</h2>
            <p class="hub-p">Log a case with the details in this article and it can be picked up straight away.</p>
            <div class="hub-rows">
              <a :href="SUPPORT.vmsPortal" target="_blank" rel="noopener" class="hub-row hub-row--soft">Log a support case <span class="arrow">↗</span></a>
              <RouterLink to="/help/report-an-issue" class="hub-row">How to report an issue <span class="arrow">→</span></RouterLink>
            </div>
          </section>
        </div>

        <p v-if="updated" class="updated">Last updated {{ updated }}</p>
        <RouterLink :to="sectionLink" class="hub-back">← Back to the {{ isKb ? 'Knowledge Base' : 'Help Center' }}</RouterLink>
      </template>

      <template v-else-if="missing">
        <div class="hub-intro">
          <h1 class="hub-h1">Article not found</h1>
          <p class="hub-lead">It may have moved or been unpublished.</p>
        </div>
        <div class="hub-rows narrow">
          <RouterLink to="/knowledge-base" class="hub-row">Browse the Knowledge Base <span class="arrow">→</span></RouterLink>
          <RouterLink to="/help-center" class="hub-row">Browse the Help Center <span class="arrow">→</span></RouterLink>
        </div>
      </template>
    </main>
  </div>
</template>

<style scoped>
.article-main { max-width: 860px; }
.article-h1 { font-size: 40px; }
.for-you { font-weight: 500; color: #0B0B0F; }
.sample-tag { background: #FBEDC8; color: #633806; }
.small-h { font-size: 22px; }
.after { grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); }
.updated { margin: 0; font-size: 13px; color: #6B6C75; }
.narrow { max-width: 420px; }

.article-body { gap: 0; font-size: 16px; line-height: 1.7; color: #15161B; }
.article-body :deep(> *:first-child) { margin-top: 0; }
.article-body :deep(p) { margin: 0 0 14px; }
.article-body :deep(h2) { font-size: 22px; font-weight: 500; margin: 26px 0 10px; letter-spacing: -0.01em; }
.article-body :deep(ul), .article-body :deep(ol) { margin: 0 0 14px; padding-left: 22px; }
.article-body :deep(li) { margin-bottom: 6px; }
.article-body :deep(strong) { font-weight: 500; color: #0B0B0F; }
.article-body :deep(a) { color: #7A3FE5; }
.article-body :deep(code) { font-family: var(--font-mono); font-size: 14px; background: #F5EEFF; padding: 1px 5px; border-radius: 4px; }
.article-body :deep(blockquote) { margin: 6px 0 16px; padding: 14px 16px; border-radius: 8px; background: #F4F2EE; }
.article-body :deep(blockquote p:last-child) { margin-bottom: 0; }
.article-body :deep(.callout-tip) { background: #D3F4DE; }
.article-body :deep(.callout-note) { background: #ECDEFE; }
.article-body :deep(.callout-warning) { background: #FBE0DE; }
.article-body :deep(.callout-head) { font-family: var(--font-mono); font-size: 12px; letter-spacing: 0.08em; text-transform: uppercase; font-weight: 500; }
@media (max-width: 640px) { .article-h1 { font-size: 32px; } }
</style>
