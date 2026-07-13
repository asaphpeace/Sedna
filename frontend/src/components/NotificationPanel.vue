<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { notificationsApi } from '@/api'

const router = useRouter()
const open = ref(false)
const data = ref<{ unread_count: number; notifications: any[] }>({ unread_count: 0, notifications: [] })
const loading = ref(false)
const panel = ref<HTMLElement | null>(null)

async function load() {
  loading.value = true
  try {
    const res = await notificationsApi.list()
    data.value = res.data
  } finally {
    loading.value = false
  }
}

function toggle() {
  open.value = !open.value
  if (open.value) load()
}

async function markRead(id: number, link?: string) {
  await notificationsApi.markRead(id)
  const n = data.value.notifications.find(n => n.id === id)
  if (n && !n.is_read) {
    n.is_read = true
    data.value.unread_count = Math.max(0, data.value.unread_count - 1)
  }
  open.value = false
  if (link) router.push(link)
}

async function markAll() {
  await notificationsApi.markAllRead()
  data.value.notifications.forEach(n => n.is_read = true)
  data.value.unread_count = 0
}

function outsideClick(e: MouseEvent) {
  if (panel.value && !panel.value.contains(e.target as Node)) {
    open.value = false
  }
}

function timeAgo(iso: string) {
  const diff = Date.now() - new Date(iso).getTime()
  const m = Math.floor(diff / 60000)
  if (m < 1) return 'just now'
  if (m < 60) return `${m}m ago`
  const h = Math.floor(m / 60)
  if (h < 24) return `${h}h ago`
  return `${Math.floor(h / 24)}d ago`
}

onMounted(async () => {
  document.addEventListener('click', outsideClick)
  await load()
})
onUnmounted(() => document.removeEventListener('click', outsideClick))
</script>

<template>
  <div ref="panel" class="notif-panel">
    <button class="notif-btn" @click.stop="toggle" :aria-label="`Notifications${data.unread_count ? `, ${data.unread_count} unread` : ''}`">
      <i class="ti ti-bell" />
      <span v-if="data.unread_count" class="badge">{{ data.unread_count > 9 ? '9+' : data.unread_count }}</span>
    </button>

    <transition name="fade-drop">
      <div v-if="open" class="dropdown" role="dialog" aria-label="Notifications">
        <div class="dropdown-header">
          <span>Notifications</span>
          <button v-if="data.unread_count" class="mark-all" @click="markAll">Mark all read</button>
        </div>

        <div v-if="loading" class="loading"><i class="ti ti-loader-2 spin" /></div>

        <div v-else-if="!data.notifications.length" class="empty">
          <i class="ti ti-bell-off" />
          <p>All caught up!</p>
        </div>

        <div v-else class="notif-list">
          <div
            v-for="n in data.notifications"
            :key="n.id"
            class="notif-item"
            :class="{ unread: !n.is_read }"
            @click="markRead(n.id, n.link)"
          >
            <div class="notif-icon" :style="{ background: n.icon_color + '20', color: n.icon_color }">
              <i :class="'ti ' + n.icon" />
            </div>
            <div class="notif-content">
              <div class="notif-title">{{ n.title }}</div>
              <div v-if="n.body" class="notif-body">{{ n.body }}</div>
              <div class="notif-time">{{ timeAgo(n.created_at) }}</div>
            </div>
            <div v-if="!n.is_read" class="unread-dot" />
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<style scoped>
.notif-panel { position: relative; }
.notif-btn {
  position: relative; background: none; border: 1px solid var(--border);
  border-radius: 8px; padding: .45rem .6rem; cursor: pointer;
  color: var(--text); font-size: 1.1rem; display: flex; align-items: center;
  transition: background .15s;
}
.notif-btn:hover { background: var(--surface); }
.badge {
  position: absolute; top: -4px; right: -4px;
  background: #EF4444; color: #fff; font-size: .65rem;
  min-width: 16px; height: 16px; border-radius: 8px;
  display: flex; align-items: center; justify-content: center;
  padding: 0 3px; font-weight: 700;
}

.dropdown {
  position: absolute; top: calc(100% + 8px); right: 0;
  width: 340px; background: var(--surface);
  border: 1px solid var(--border); border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0,0,0,.14);
  z-index: 100; overflow: hidden;
}
.dropdown-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: .875rem 1rem; border-bottom: 1px solid var(--border);
  font-weight: 600; font-size: .9rem;
}
.mark-all { background: none; border: none; cursor: pointer; color: var(--purple); font-size: .8rem; }
.loading, .empty { text-align: center; padding: 2rem; color: var(--text-muted); }
.empty i { font-size: 1.5rem; display: block; margin-bottom: .5rem; }
.empty p { font-size: .85rem; }
.spin { animation: spin 1s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

.notif-list { max-height: 360px; overflow-y: auto; }
.notif-item {
  display: flex; align-items: flex-start; gap: .75rem;
  padding: .875rem 1rem; cursor: pointer; transition: background .1s;
  position: relative;
}
.notif-item:hover { background: rgba(0,0,0,.04); }
.notif-item.unread { background: rgba(110,43,240,.04); }
.notif-item + .notif-item { border-top: 1px solid var(--border); }
.notif-icon { width: 36px; height: 36px; border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 1rem; flex-shrink: 0; }
.notif-content { flex: 1; min-width: 0; }
.notif-title { font-size: .875rem; font-weight: 500; line-height: 1.3; }
.notif-body { font-size: .8rem; color: var(--text-muted); margin-top: .15rem; }
.notif-time { font-size: .75rem; color: var(--text-muted); margin-top: .25rem; }
.unread-dot { width: 7px; height: 7px; border-radius: 50%; background: var(--purple); flex-shrink: 0; margin-top: .35rem; }

.fade-drop-enter-active, .fade-drop-leave-active { transition: opacity .15s, transform .15s; }
.fade-drop-enter-from, .fade-drop-leave-to { opacity: 0; transform: translateY(-6px); }
</style>
