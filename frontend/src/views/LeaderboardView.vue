<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { gamificationApi } from '@/api'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const board = ref<any[]>([])
const loading = ref(true)

onMounted(async () => {
  try {
    const res = await gamificationApi.leaderboard(50)
    board.value = res.data
  } finally {
    loading.value = false
  }
})

const medalColors = ['#F59E0B', '#9CA3AF', '#B45309']
</script>

<template>
  <div class="page-container">
    <div class="page-header">
      <h1>Leaderboard</h1>
      <p class="page-sub">Top learners in your organisation this month</p>
    </div>

    <div v-if="loading" class="loading-state">
      <i class="ti ti-loader-2 spin" />
    </div>

    <div v-else class="board-list">
      <div
        v-for="entry in board"
        :key="entry.user_id"
        class="board-row"
        :class="{ 'is-me': entry.is_me }"
      >
        <div class="rank-col">
          <i v-if="entry.rank <= 3" class="ti ti-medal-2" :style="{ color: medalColors[entry.rank - 1] }" />
          <span v-else class="rank-num">{{ entry.rank }}</span>
        </div>
        <div class="avatar-col">
          <div class="avatar" :style="{ background: '#6E2BF0' }">
            {{ entry.name.split(' ').map((n: string) => n[0]).join('').slice(0,2).toUpperCase() }}
          </div>
        </div>
        <div class="info-col">
          <span class="user-name">{{ entry.name }} <span v-if="entry.is_me" class="you-tag">you</span></span>
          <span class="level-label">{{ entry.level_name }}</span>
        </div>
        <div class="xp-col">
          <span class="xp-number">{{ entry.xp_total.toLocaleString() }}</span>
          <span class="xp-label">XP</span>
        </div>
      </div>

      <div v-if="!board.length" class="empty-state">
        <i class="ti ti-users" />
        <p>No learners yet</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.page-container { max-width: 640px; margin: 0 auto; padding: 2rem 1rem; }
.page-header { margin-bottom: 2rem; }
.page-header h1 { font-size: 1.5rem; font-weight: 700; }
.page-sub { color: var(--text-muted); font-size: .9rem; margin-top: .25rem; }
.loading-state { text-align: center; padding: 3rem; color: var(--text-muted); }
.loading-state i { font-size: 2rem; }
.spin { animation: spin 1s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
.empty-state { text-align: center; padding: 3rem; color: var(--text-muted); }
.empty-state i { font-size: 2rem; display: block; margin-bottom: .5rem; }

.board-list { display: flex; flex-direction: column; gap: .5rem; }
.board-row {
  display: flex; align-items: center; gap: 1rem;
  padding: .875rem 1rem; background: var(--surface);
  border: 1px solid var(--border); border-radius: 10px;
  transition: border-color .15s;
}
.board-row.is-me { border-color: var(--purple); background: rgba(110,43,240,.05); }
.rank-col { width: 2rem; text-align: center; font-size: 1.2rem; flex-shrink: 0; }
.rank-num { font-weight: 700; color: var(--text-muted); font-size: .9rem; }
.avatar-col { flex-shrink: 0; }
.avatar {
  width: 38px; height: 38px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: .8rem; font-weight: 700; color: #fff;
}
.info-col { flex: 1; min-width: 0; }
.user-name { font-weight: 600; display: flex; align-items: center; gap: .5rem; }
.level-label { font-size: .8rem; color: var(--text-muted); display: block; }
.you-tag { background: var(--purple); color: #fff; font-size: .65rem; padding: .1rem .35rem; border-radius: 4px; font-weight: 500; }
.xp-col { text-align: right; flex-shrink: 0; }
.xp-number { font-size: 1.1rem; font-weight: 700; color: var(--purple); display: block; }
.xp-label { font-size: .75rem; color: var(--text-muted); }
</style>
