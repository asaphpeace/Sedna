<script setup lang="ts">
import { onMounted } from 'vue'
import HubHeader from '@/components/hub/HubHeader.vue'
import { useCatalog } from '@/composables/useCatalog'
import { SUPPORT } from '@/constants/hubLinks'

// Nassia's "Learning" screen
const { load } = useCatalog()
onMounted(load)
</script>

<template>
  <div class="hub-page">
    <HubHeader />
    <main id="main-content" class="hub-main">
      <nav aria-label="Breadcrumb" class="hub-breadcrumb">
        <RouterLink to="/">LEARNING HUB</RouterLink><span>/</span><span class="current">LEARNING</span>
      </nav>
      <div class="hub-intro">
        <h1 class="hub-h1">Learn Sedna your way.</h1>
        <p class="hub-lead">Pick your product, then follow the path for your role. Global resources apply to every product.</p>
      </div>

      <div class="hub-grid">
        <RouterLink to="/learning/email" class="hub-card">
          <div class="hub-eyebrow">PRODUCT</div>
          <h2 class="hub-h2">Sedna Email</h2>
          <p class="hub-p">From your first login to making the shared inbox work for your team.</p>
          <div class="hub-tags">
            <span class="hub-tag hub-tag--lilac">5 sections</span>
            <span class="hub-tag hub-tag--sky">Paths by role</span>
          </div>
          <span class="hub-cta">Open Sedna Email learning →</span>
        </RouterLink>

        <RouterLink to="/learning/vms" class="hub-card">
          <div class="hub-eyebrow">PRODUCT</div>
          <h2 class="hub-h2">Sedna VMS</h2>
          <p class="hub-p">Voyage management by role, plus deep-dive paths for each VMS function.</p>
          <div class="hub-tags">
            <span class="hub-tag hub-tag--lilac">4 sections</span>
            <span class="hub-tag hub-tag--sky">Paths by role</span>
            <span class="hub-tag hub-tag--mint">Function paths</span>
          </div>
          <span class="hub-cta">Open Sedna VMS learning →</span>
        </RouterLink>

        <section id="global" class="hub-card hub-card--warm">
          <div class="hub-eyebrow">FOR ALL CUSTOMERS</div>
          <h2 class="hub-h2">Global resources</h2>
          <p class="hub-p">Shared foundations that apply across every Sedna product.</p>
          <div class="hub-rows">
            <a :href="SUPPORT.search('glossary')" target="_blank" rel="noopener" class="hub-row">Terminology and glossary <span class="arrow">↗</span></a>
            <a :href="SUPPORT.getToKnowSedna" target="_blank" rel="noopener" class="hub-row">How Sedna works: one platform <span class="arrow">↗</span></a>
            <RouterLink to="/whatsnew" class="hub-row">What's new: release highlights <span class="arrow">→</span></RouterLink>
            <span class="hub-row hub-row--muted">Workshops and live sessions <span class="hub-tag hub-tag--grey">Coming soon</span></span>
          </div>
        </section>
      </div>
    </main>
  </div>
</template>
