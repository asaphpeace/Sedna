<script setup lang="ts">
import { onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import AppTopBar from './AppTopBar.vue'
import HeroBanner from '@/components/HeroBanner.vue'
import { useAppStore } from '@/stores/app'

const app = useAppStore()
const route = useRoute()

// Only the home page opens with the greeting banner; elsewhere it pushed
// every page's real content below the fold
const showBanner = computed(() => route.path === '/home')

onMounted(() => app.bootstrap())
</script>

<template>
  <div class="layout">
    <AppTopBar />
    <main class="main" id="main-content">
      <div v-if="showBanner" class="banner-wrap">
        <HeroBanner />
      </div>
      <RouterView />
    </main>
  </div>
</template>

<style scoped>
.layout { display: flex; flex-direction: column; height: 100vh; overflow: hidden; }
.main { flex: 1; overflow-y: auto; }
.banner-wrap { max-width: var(--content-max); margin: 0 auto; padding: 40px 24px 0; }
</style>
