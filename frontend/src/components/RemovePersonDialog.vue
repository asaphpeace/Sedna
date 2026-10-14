<script setup lang="ts">
import { ref } from 'vue'
import { teamApi } from '@/api'

// Removal on request (GDPR): the person is anonymised, not deleted, so their
// completed lessons still count in totals without identifying them.
const props = defineProps<{ person: { id: number; name: string; email: string } }>()
const emit = defineEmits<{ close: []; removed: [] }>()

const typed = ref('')
const busy = ref(false)
const error = ref('')

async function remove() {
  busy.value = true
  error.value = ''
  try {
    await teamApi.remove(props.person.id)
    emit('removed')
  } catch (e: any) {
    error.value = e?.response?.data?.detail ?? 'Something went wrong. Nothing was changed.'
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <div class="modal-overlay" @click.self="emit('close')">
    <div class="modal" role="dialog" aria-modal="true" aria-labelledby="remove-title">
      <h2 id="remove-title" class="modal-title">Remove {{ person.name }}?</h2>
      <p class="body">Use this when someone asks for their data to be removed, or leaves for good. It can't be undone.</p>
      <ul class="body">
        <li>Their name, email, comments and settings are erased, and they can no longer sign in.</li>
        <li>Lessons they completed stay as anonymous counts, so learning totals stay accurate.</li>
      </ul>
      <label class="field">
        <span class="label">Type <strong>{{ person.email }}</strong> to confirm</span>
        <input v-model="typed" class="input" autocomplete="off" />
      </label>
      <p v-if="error" class="error">{{ error }}</p>
      <div class="modal-actions">
        <button class="btn btn-ghost" @click="emit('close')">Cancel</button>
        <button class="btn btn-danger" :disabled="typed.trim().toLowerCase() !== person.email.toLowerCase() || busy" @click="remove">
          Remove permanently
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.modal-overlay { position: fixed; inset: 0; background: rgba(11,11,15,0.4); display: flex; align-items: center; justify-content: center; z-index: 100; padding: 16px; }
.modal { background: var(--surface); border-radius: 14px; padding: 28px; width: 440px; max-width: 100%; display: flex; flex-direction: column; gap: 14px; box-shadow: 0 24px 64px rgba(11,11,15,0.2); }
.modal-title { font-size: 17px; font-weight: 500; }
.body { font-size: 14px; color: var(--text-secondary); line-height: 1.55; }
ul.body { padding-left: 18px; display: flex; flex-direction: column; gap: 4px; }
.field { display: flex; flex-direction: column; gap: 6px; }
.label { font-size: 14px; color: var(--text-secondary); }
.label strong { color: var(--text-primary); font-weight: 500; word-break: break-all; }
.error { font-size: 14px; color: #B0322B; }
.modal-actions { display: flex; gap: 8px; justify-content: flex-end; margin-top: 4px; flex-wrap: wrap; }
.btn-danger { background: #B0322B; color: #fff; border: none; }
.btn-danger:disabled { opacity: 0.45; cursor: not-allowed; }
</style>
