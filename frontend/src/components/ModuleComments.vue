<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { socialApi } from '@/api'
import { useAuthStore } from '@/stores/auth'

const props = defineProps<{ moduleId: number }>()
const auth = useAuthStore()

type Comment = {
  id: number; body: string; author_name: string; author_id: number
  like_count: number; liked_by_me: boolean; created_at: string; replies: Comment[]
}

const comments = ref<Comment[]>([])
const loading = ref(true)
const newBody = ref('')
const replyTo = ref<{ id: number; name: string } | null>(null)
const submitting = ref(false)

onMounted(load)

async function load() {
  loading.value = true
  try {
    const res = await socialApi.getComments(props.moduleId)
    comments.value = res.data
  } finally {
    loading.value = false
  }
}

async function submit() {
  if (!newBody.value.trim()) return
  submitting.value = true
  try {
    await socialApi.createComment(props.moduleId, newBody.value.trim(), replyTo.value?.id)
    newBody.value = ''
    replyTo.value = null
    await load()
  } finally {
    submitting.value = false
  }
}

async function toggleLike(comment: Comment) {
  const res = await socialApi.toggleLike(comment.id)
  comment.liked_by_me = res.data.liked
  comment.like_count = res.data.like_count
}

async function deleteComment(id: number) {
  if (!confirm('Delete this comment?')) return
  await socialApi.deleteComment(id)
  await load()
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
</script>

<template>
  <div class="comments-section">
    <h3 class="comments-heading">
      <i class="ti ti-message-circle" />
      Discussion
      <span v-if="comments.length" class="count">{{ comments.length }}</span>
    </h3>

    <!-- New comment box -->
    <div class="compose">
      <div v-if="replyTo" class="reply-notice">
        Replying to {{ replyTo.name }}
        <button class="cancel-reply" @click="replyTo = null">
          <i class="ti ti-x" />
        </button>
      </div>
      <textarea
        v-model="newBody"
        :placeholder="replyTo ? `Reply to ${replyTo.name}…` : 'Share a question or insight…'"
        rows="3"
        class="comment-input"
        @keydown.ctrl.enter="submit"
      />
      <div class="compose-footer">
        <span class="hint">Ctrl+Enter to submit</span>
        <button class="btn btn-primary btn-sm" :disabled="!newBody.trim() || submitting" @click="submit">
          <i v-if="submitting" class="ti ti-loader-2 spin" />
          Post
        </button>
      </div>
    </div>

    <div v-if="loading" class="loading"><i class="ti ti-loader-2 spin" /></div>

    <div v-else-if="!comments.length" class="empty">
      <i class="ti ti-message-off" />
      <p>No comments yet. Be the first!</p>
    </div>

    <div v-else class="comment-list">
      <div v-for="c in comments" :key="c.id" class="comment-thread">
        <!-- Top-level comment -->
        <div class="comment">
          <div class="comment-avatar">{{ c.author_name.split(' ').map(n => n[0]).join('').slice(0,2) }}</div>
          <div class="comment-body-wrap">
            <div class="comment-meta">
              <span class="comment-author">{{ c.author_name }}</span>
              <span class="comment-time">{{ timeAgo(c.created_at) }}</span>
            </div>
            <p class="comment-body">{{ c.body }}</p>
            <div class="comment-actions">
              <button class="action-btn" :class="{ liked: c.liked_by_me }" @click="toggleLike(c)">
                <i class="ti ti-heart" />
                <span v-if="c.like_count">{{ c.like_count }}</span>
              </button>
              <button class="action-btn" @click="replyTo = { id: c.id, name: c.author_name }">
                <i class="ti ti-corner-down-right" /> Reply
              </button>
              <button v-if="c.author_id === auth.user?.id || auth.user?.is_admin" class="action-btn danger" @click="deleteComment(c.id)">
                <i class="ti ti-trash" />
              </button>
            </div>
          </div>
        </div>

        <!-- Replies -->
        <div v-if="c.replies?.length" class="replies">
          <div v-for="r in c.replies" :key="r.id" class="comment reply">
            <div class="comment-avatar sm">{{ r.author_name.split(' ').map(n => n[0]).join('').slice(0,2) }}</div>
            <div class="comment-body-wrap">
              <div class="comment-meta">
                <span class="comment-author">{{ r.author_name }}</span>
                <span class="comment-time">{{ timeAgo(r.created_at) }}</span>
              </div>
              <p class="comment-body">{{ r.body }}</p>
              <div class="comment-actions">
                <button class="action-btn" :class="{ liked: r.liked_by_me }" @click="toggleLike(r)">
                  <i class="ti ti-heart" />
                  <span v-if="r.like_count">{{ r.like_count }}</span>
                </button>
                <button v-if="r.author_id === auth.user?.id || auth.user?.is_admin" class="action-btn danger" @click="deleteComment(r.id)">
                  <i class="ti ti-trash" />
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.comments-section { margin-top: 2.5rem; }
.comments-heading { font-size: 1rem; font-weight: 600; display: flex; align-items: center; gap: .5rem; margin-bottom: 1.25rem; }
.comments-heading i { color: var(--purple); }
.count { background: var(--border); border-radius: 10px; padding: .1rem .45rem; font-size: .75rem; font-weight: 500; color: var(--text-muted); }

.compose { background: var(--surface); border: 1px solid var(--border); border-radius: 10px; overflow: hidden; margin-bottom: 1.5rem; }
.reply-notice { display: flex; align-items: center; justify-content: space-between; padding: .5rem .75rem; background: rgba(110,43,240,.07); font-size: .85rem; color: var(--purple); }
.cancel-reply { background: none; border: none; cursor: pointer; color: var(--text-muted); padding: 2px; display: flex; align-items: center; }
.comment-input { width: 100%; padding: .875rem 1rem; border: none; background: transparent; resize: none; font-family: inherit; font-size: .9rem; color: var(--text); outline: none; }
.compose-footer { display: flex; align-items: center; justify-content: space-between; padding: .5rem .75rem; border-top: 1px solid var(--border); }
.hint { font-size: .75rem; color: var(--text-muted); }

.loading, .empty { text-align: center; padding: 2rem; color: var(--text-muted); }
.empty i { font-size: 1.5rem; display: block; margin-bottom: .5rem; }
.spin { animation: spin 1s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

.comment-list { display: flex; flex-direction: column; gap: 1rem; }
.comment-thread { }
.comment { display: flex; gap: .75rem; }
.comment-avatar { width: 36px; height: 36px; border-radius: 50%; background: var(--purple); color: #fff; font-size: .75rem; font-weight: 700; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.comment-avatar.sm { width: 28px; height: 28px; font-size: .65rem; }
.comment-body-wrap { flex: 1; min-width: 0; }
.comment-meta { display: flex; align-items: center; gap: .5rem; margin-bottom: .3rem; }
.comment-author { font-weight: 600; font-size: .875rem; }
.comment-time { font-size: .75rem; color: var(--text-muted); }
.comment-body { font-size: .9rem; line-height: 1.5; margin: 0; }
.comment-actions { display: flex; align-items: center; gap: .25rem; margin-top: .5rem; }
.action-btn { background: none; border: none; cursor: pointer; display: flex; align-items: center; gap: .25rem; color: var(--text-muted); font-size: .8rem; padding: .25rem .4rem; border-radius: 4px; transition: color .15s, background .15s; }
.action-btn:hover { background: rgba(0,0,0,.06); color: var(--text); }
.action-btn.liked { color: #EF4444; }
.action-btn.danger:hover { color: #EF4444; }
.replies { margin-left: 2.75rem; margin-top: .75rem; display: flex; flex-direction: column; gap: .75rem; padding-left: 1rem; border-left: 2px solid var(--border); }
</style>
