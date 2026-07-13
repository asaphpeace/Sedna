<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { quizzesApi } from '@/api'

const route = useRoute()
const router = useRouter()

const moduleId = route.query.module_id ? Number(route.query.module_id) : undefined
const tierId = route.query.tier_id ? Number(route.query.tier_id) : undefined

type Option = { id: number; text: string }
type Question = { id: number; question: string; explanation: string; options: Option[] }
type Explanation = { correct_option_id: number; explanation: string }

const questions = ref<Question[]>([])
const current = ref(0)
const selected = ref<Record<number, number>>({})
const result = ref<{
  score: number; passed: boolean; pass_mark: number; correct: number; total: number
  xp_awarded: number; new_badges: string[]; cert_earned: boolean; explanations: Record<number, Explanation>
} | null>(null)
const loading = ref(true)
const submitting = ref(false)
const showExplanation = ref(false)

onMounted(async () => {
  try {
    const res = moduleId
      ? await quizzesApi.forModule(moduleId)
      : await quizzesApi.forTier(tierId!)
    questions.value = res.data
  } finally {
    loading.value = false
  }
})

const q = computed(() => questions.value[current.value])
const progress = computed(() => Math.round(((current.value) / questions.value.length) * 100))
const allAnswered = computed(() => questions.value.every(q => selected.value[q.id] !== undefined))

function select(optionId: number) {
  if (result.value) return
  selected.value[q.value.id] = optionId
  showExplanation.value = false
}

function next() {
  showExplanation.value = false
  if (current.value < questions.value.length - 1) {
    current.value++
  }
}

function prev() {
  showExplanation.value = false
  if (current.value > 0) current.value--
}

async function submit() {
  submitting.value = true
  try {
    const answers = Object.entries(selected.value).map(([qid, oid]) => ({
      question_id: Number(qid),
      option_id: oid,
    }))
    const res = await quizzesApi.submit({ module_id: moduleId, tier_id: tierId, answers })
    result.value = res.data
  } finally {
    submitting.value = false
  }
}

function getOptionState(qId: number, optId: number) {
  if (!result.value) {
    return selected.value[qId] === optId ? 'selected' : 'idle'
  }
  const exp = result.value.explanations[qId]
  if (!exp) return 'idle'
  if (optId === exp.correct_option_id) return 'correct'
  if (selected.value[qId] === optId && optId !== exp.correct_option_id) return 'wrong'
  return 'idle'
}
</script>

<template>
  <div class="quiz-container">
    <div v-if="loading" class="loading-state">
      <i class="ti ti-loader-2 spin" />
    </div>

    <div v-else-if="!questions.length" class="empty-state">
      <i class="ti ti-question-mark" />
      <p>No quiz questions available for this module yet.</p>
      <button class="btn btn-primary" @click="router.back()">Go back</button>
    </div>

    <!-- Results screen -->
    <div v-else-if="result" class="result-screen">
      <div class="result-card" :class="result.passed ? 'passed' : 'failed'">
        <div class="result-icon">
          <i :class="result.passed ? 'ti ti-trophy' : 'ti ti-refresh'" />
        </div>
        <h2>{{ result.passed ? 'Quiz Passed!' : 'Not quite there' }}</h2>
        <div class="score-display">{{ result.score }}<span>%</span></div>
        <p class="score-sub">{{ result.correct }} / {{ result.total }} correct · pass mark {{ result.pass_mark }}%</p>
        <div v-if="result.xp_awarded" class="xp-badge">+{{ result.xp_awarded }} XP</div>
        <div v-if="result.cert_earned" class="cert-notice">
          <i class="ti ti-certificate" /> Certificate earned!
        </div>
        <div v-if="result.new_badges?.length" class="badge-notice">
          <i class="ti ti-award" /> New badge{{ result.new_badges.length > 1 ? 's' : '' }}!
        </div>
      </div>

      <div class="review-section">
        <h3>Review answers</h3>
        <div v-for="(q, i) in questions" :key="q.id" class="review-item">
          <div class="review-q">{{ i + 1 }}. {{ q.question }}</div>
          <div class="review-options">
            <div
              v-for="opt in q.options"
              :key="opt.id"
              class="review-opt"
              :class="getOptionState(q.id, opt.id)"
            >
              <i :class="getOptionState(q.id, opt.id) === 'correct' ? 'ti ti-check' : getOptionState(q.id, opt.id) === 'wrong' ? 'ti ti-x' : 'ti ti-minus'" />
              {{ opt.text }}
            </div>
          </div>
          <div v-if="result.explanations[q.id]?.explanation" class="review-explanation">
            <i class="ti ti-info-circle" />
            {{ result.explanations[q.id].explanation }}
          </div>
        </div>
      </div>

      <div class="result-actions">
        <button class="btn btn-ghost" @click="router.back()">Back to module</button>
        <button v-if="!result.passed" class="btn btn-primary" @click="() => { result = null; current = 0; selected = {} }">
          Try again
        </button>
      </div>
    </div>

    <!-- Quiz taking screen -->
    <div v-else class="quiz-screen">
      <div class="quiz-header">
        <button class="btn-icon" @click="router.back()"><i class="ti ti-arrow-left" /></button>
        <div class="quiz-progress-bar">
          <div class="quiz-progress-fill" :style="{ width: progress + '%' }" />
        </div>
        <span class="quiz-counter">{{ current + 1 }} / {{ questions.length }}</span>
      </div>

      <div class="question-card">
        <p class="question-text">{{ q.question }}</p>
        <div class="options-list">
          <button
            v-for="opt in q.options"
            :key="opt.id"
            class="option-btn"
            :class="{ selected: selected[q.id] === opt.id }"
            @click="select(opt.id)"
          >
            <span class="option-dot" />
            {{ opt.text }}
          </button>
        </div>
      </div>

      <div class="quiz-nav">
        <button class="btn btn-ghost" :disabled="current === 0" @click="prev">Previous</button>
        <div class="dots">
          <span
            v-for="(_, i) in questions"
            :key="i"
            class="dot"
            :class="{ active: i === current, answered: selected[questions[i].id] !== undefined }"
            @click="current = i"
          />
        </div>
        <button
          v-if="current < questions.length - 1"
          class="btn btn-primary"
          :disabled="selected[q.id] === undefined"
          @click="next"
        >
          Next
        </button>
        <button
          v-else
          class="btn btn-primary"
          :disabled="!allAnswered || submitting"
          @click="submit"
        >
          <i v-if="submitting" class="ti ti-loader-2 spin" />
          Submit quiz
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.quiz-container { max-width: 680px; margin: 0 auto; padding: 2rem 1rem; }
.loading-state, .empty-state { text-align: center; padding: 4rem; color: var(--text-muted); }
.loading-state i, .empty-state i { font-size: 2rem; display: block; margin-bottom: 1rem; }
.spin { animation: spin 1s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

.quiz-header { display: flex; align-items: center; gap: 1rem; margin-bottom: 2rem; }
.quiz-progress-bar { flex: 1; height: 6px; background: var(--border); border-radius: 3px; overflow: hidden; }
.quiz-progress-fill { height: 100%; background: var(--purple); border-radius: 3px; transition: width .3s; }
.quiz-counter { font-size: .85rem; color: var(--text-muted); white-space: nowrap; }

.question-card { background: var(--surface); border: 1px solid var(--border); border-radius: 12px; padding: 2rem; margin-bottom: 1.5rem; }
.question-text { font-size: 1.15rem; font-weight: 600; margin-bottom: 1.5rem; line-height: 1.5; }
.options-list { display: flex; flex-direction: column; gap: .75rem; }
.option-btn {
  display: flex; align-items: center; gap: .75rem;
  padding: .875rem 1rem; border: 1.5px solid var(--border);
  border-radius: 8px; background: transparent; cursor: pointer;
  text-align: left; font-size: .95rem; color: var(--text);
  transition: border-color .15s, background .15s;
}
.option-btn:hover { border-color: var(--purple); background: rgba(110,43,240,.06); }
.option-btn.selected { border-color: var(--purple); background: rgba(110,43,240,.1); color: var(--purple); font-weight: 500; }
.option-dot { width: 18px; height: 18px; border-radius: 50%; border: 2px solid currentColor; flex-shrink: 0; }
.option-btn.selected .option-dot { background: var(--purple); border-color: var(--purple); }

.quiz-nav { display: flex; align-items: center; justify-content: space-between; gap: 1rem; }
.dots { display: flex; gap: .4rem; flex: 1; justify-content: center; }
.dot { width: 8px; height: 8px; border-radius: 50%; background: var(--border); cursor: pointer; transition: background .15s; }
.dot.active { background: var(--purple); }
.dot.answered { background: rgba(110,43,240,.4); }
.dot.active.answered { background: var(--purple); }

/* Result screen */
.result-screen { display: flex; flex-direction: column; gap: 2rem; }
.result-card { text-align: center; background: var(--surface); border: 1px solid var(--border); border-radius: 16px; padding: 2.5rem; }
.result-card.passed { border-color: var(--green); }
.result-card.failed { border-color: var(--border); }
.result-icon { font-size: 3rem; margin-bottom: 1rem; }
.result-card.passed .result-icon { color: var(--green); }
.result-card.failed .result-icon { color: var(--text-muted); }
.result-card h2 { font-size: 1.5rem; margin-bottom: .5rem; }
.score-display { font-size: 4rem; font-weight: 700; color: var(--purple); line-height: 1; }
.score-display span { font-size: 2rem; }
.score-sub { color: var(--text-muted); margin-top: .25rem; }
.xp-badge { display: inline-block; background: var(--purple); color: #fff; padding: .25rem .75rem; border-radius: 20px; font-size: .85rem; margin-top: 1rem; }
.cert-notice, .badge-notice { margin-top: .75rem; color: var(--green); font-weight: 500; }
.cert-notice i, .badge-notice i { margin-right: .25rem; }

.review-section h3 { font-size: 1.1rem; margin-bottom: 1rem; }
.review-item { background: var(--surface); border: 1px solid var(--border); border-radius: 10px; padding: 1.25rem; margin-bottom: 1rem; }
.review-q { font-weight: 500; margin-bottom: .75rem; }
.review-options { display: flex; flex-direction: column; gap: .4rem; margin-bottom: .75rem; }
.review-opt { display: flex; align-items: center; gap: .5rem; padding: .4rem .6rem; border-radius: 6px; font-size: .9rem; }
.review-opt.correct { background: rgba(14,158,110,.12); color: var(--green); }
.review-opt.wrong { background: rgba(239,68,68,.1); color: #EF4444; }
.review-opt i { font-size: .85rem; flex-shrink: 0; }
.review-explanation { font-size: .875rem; color: var(--text-muted); padding: .5rem .75rem; background: rgba(0,0,0,.04); border-radius: 6px; display: flex; gap: .5rem; }
.review-explanation i { color: var(--purple); flex-shrink: 0; margin-top: 2px; }

.result-actions { display: flex; gap: 1rem; justify-content: center; }
.btn-icon { background: none; border: 1px solid var(--border); border-radius: 8px; padding: .5rem; cursor: pointer; color: var(--text); display: flex; align-items: center; }
</style>
