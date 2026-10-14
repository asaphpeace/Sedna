import { onMounted, onUnmounted, type Ref } from 'vue'
import { progressApi } from '@/api'

// Records active time on a lesson for the Learning impact dashboard. Every
// 30 seconds it reports 30 seconds, but only while the tab is visible and the
// learner is actually engaged: they moved, scrolled or typed in the last
// minute, a video or audio player is running, or they're inside an embedded
// video (focus sits in its iframe, where we can't see their clicks).
const TICK_SECS = 30
const IDLE_AFTER_MS = 60_000

export function useLearningTime(moduleId: Ref<number | null>) {
  let lastInteraction = Date.now()
  let timer: ReturnType<typeof setInterval> | null = null
  const events = ['pointermove', 'pointerdown', 'keydown', 'wheel', 'scroll', 'touchstart']

  const touch = () => { lastInteraction = Date.now() }

  function engaged(): boolean {
    if (document.visibilityState !== 'visible') return false
    if (Date.now() - lastInteraction < IDLE_AFTER_MS) return true
    if (document.activeElement?.tagName === 'IFRAME') return true
    return Array.from(document.querySelectorAll('video, audio')).some(m => !(m as HTMLMediaElement).paused)
  }

  function tick() {
    const id = moduleId.value
    if (id && engaged()) progressApi.time(id, TICK_SECS).catch(() => {})
  }

  onMounted(() => {
    events.forEach(e => window.addEventListener(e, touch, { passive: true, capture: true }))
    timer = setInterval(tick, TICK_SECS * 1000)
  })
  onUnmounted(() => {
    events.forEach(e => window.removeEventListener(e, touch, { capture: true }))
    if (timer) clearInterval(timer)
  })
}
