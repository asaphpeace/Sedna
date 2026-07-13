<script setup lang="ts">
import { onMounted, ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import AppSidebar from './AppSidebar.vue'
import HeroBanner from '@/components/HeroBanner.vue'
import NotificationPanel from '@/components/NotificationPanel.vue'
import { useAppStore } from '@/stores/app'

const app = useAppStore()
const router = useRouter()
const route = useRoute()
const sidebarOpen = ref(false)

// Pages that are immersive / full-width — banner would feel intrusive
const NO_BANNER_ROUTES = new Set(['/modules', '/quiz'])
const showBanner = computed(() =>
  !NO_BANNER_ROUTES.has('/' + route.path.split('/')[1])
)

onMounted(() => app.bootstrap())

function toggleSidebar() { sidebarOpen.value = !sidebarOpen.value }
function closeSidebar() { sidebarOpen.value = false }

function resumeLearning() {
  if (app.resumePath) {
    router.push(`/paths/${app.resumePath.role_id}`)
  } else {
    router.push('/paths')
  }
}
</script>

<template>
  <div class="layout">
    <!-- Mobile overlay -->
    <div
      class="sidebar-overlay"
      :class="{ open: sidebarOpen }"
      @click="closeSidebar"
      aria-hidden="true"
    />

    <AppSidebar :class="{ open: sidebarOpen }" @nav="closeSidebar" />

    <div class="content-col">
      <header class="top-bar">
        <button
          class="top-bar-hamburger"
          @click="toggleSidebar"
          aria-label="Toggle navigation menu"
        >
          <i class="ti ti-menu-2" aria-hidden="true" />
        </button>
        <div class="top-bar-right">
          <NotificationPanel />
          <button class="btn btn-primary resume-btn" @click="resumeLearning">
            <i class="ti ti-player-play" />
            Resume learning
          </button>
        </div>
      </header>
      <main class="main" id="main-content">
        <div v-if="showBanner" class="banner-wrap">
          <HeroBanner />
        </div>
        <RouterView />
      </main>
    </div>
  </div>
</template>

<style scoped>
.layout { display: flex; height: 100vh; overflow: hidden; }
.content-col { flex: 1; display: flex; flex-direction: column; overflow: hidden; min-width: 0; }
.top-bar {
  height: 52px; border-bottom: 1px solid var(--border);
  display: flex; align-items: center; justify-content: flex-end;
  padding: 0 1.5rem; background: var(--surface); flex-shrink: 0;
}
.top-bar-right { display: flex; align-items: center; gap: .75rem; }
.resume-btn { font-size: 13px; padding: 7px 16px; }
@media (max-width: 768px) { .resume-btn { display: none; } }
.main { flex: 1; overflow-y: auto; }
.banner-wrap { padding: 24px 28px 0; }
</style>
