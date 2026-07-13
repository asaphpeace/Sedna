import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { pathsApi, progressApi, activityApi, releasesApi, savedApi, certsApi, gamificationApi } from '@/api'

export const useAppStore = defineStore('app', () => {
  const paths = ref<any[]>([])
  const pathProgress = ref<any[]>([])
  const activity = ref<any[]>([])
  const releases = ref<any[]>([])
  const saved = ref<any[]>([])
  const certs = ref<any[]>([])
  const moduleProgress = ref<Record<number, any>>({})
  const gamification = ref<any>(null)

  // The path with the highest pct that's in progress (> 0 but < 100)
  const resumePath = computed(() => {
    const inProgress = pathProgress.value.filter(p => p.pct > 0 && p.pct < 100)
    if (inProgress.length) return inProgress.reduce((a, b) => b.pct > a.pct ? b : a)
    return pathProgress.value[0] ?? null
  })

  const overallPct = computed(() => {
    if (!pathProgress.value.length) return 0
    return Math.round(pathProgress.value.reduce((sum, p) => sum + p.pct, 0) / pathProgress.value.length)
  })

  async function loadPaths() {
    const { data } = await pathsApi.list()
    paths.value = data
  }

  async function loadPathProgress() {
    const { data } = await progressApi.myPathProgress()
    pathProgress.value = data
  }

  async function loadActivity() {
    const { data } = await activityApi.list()
    activity.value = data
  }

  async function loadReleases() {
    const { data } = await releasesApi.list()
    releases.value = data
  }

  async function loadSaved() {
    const { data } = await savedApi.list()
    saved.value = data
  }

  async function loadCerts() {
    const { data } = await certsApi.mine()
    certs.value = data
  }

  async function loadModuleProgress() {
    const { data } = await progressApi.myProgress()
    moduleProgress.value = Object.fromEntries(data.map((p: any) => [p.module_id, p]))
  }

  async function loadGamification() {
    const { data } = await gamificationApi.me()
    gamification.value = data
  }

  async function bootstrap() {
    await Promise.all([
      loadPaths(), loadPathProgress(), loadActivity(),
      loadReleases(), loadSaved(), loadCerts(), loadModuleProgress(), loadGamification(),
    ])
  }

  return {
    paths, pathProgress, activity, releases, saved, certs, moduleProgress, gamification,
    resumePath, overallPct,
    loadPaths, loadPathProgress, loadActivity, loadReleases,
    loadSaved, loadCerts, loadModuleProgress, loadGamification, bootstrap,
  }
})
