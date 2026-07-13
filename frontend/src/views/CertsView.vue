<script setup lang="ts">
import { computed } from 'vue'
import { useAppStore } from '@/stores/app'

const app = useAppStore()
const certs = computed(() => app.certs)
</script>

<template>
  <div class="page">
    <div class="page-header">
      <h1 class="page-title">Certifications</h1>
      <p class="page-sub">{{ certs.length }} certificate{{ certs.length !== 1 ? 's' : '' }} earned</p>
    </div>

    <div v-if="certs.length === 0" class="empty">
      <i class="ti ti-certificate" style="font-size: 36px; color: var(--border-mid)" />
      <p>No certificates yet — complete all modules in a tier to earn one.</p>
    </div>

    <div v-else class="certs-grid">
      <RouterLink
        v-for="c in certs" :key="c.id"
        :to="`/certs/${c.id}`"
        class="cert-card"
      >
        <div class="cert-seal">
          <i class="ti ti-rosette-discount-check-filled" style="font-size: 28px; color: #fff" />
        </div>
        <div class="cert-body">
          <div class="cert-name">{{ c.cert_name }}</div>
          <div class="cert-tier">{{ c.tier_name }}</div>
          <div class="cert-date">Issued {{ new Date(c.issued_at).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' }) }}</div>
          <div class="cert-cred">No. {{ c.credential_number }}</div>
        </div>
        <div class="cert-arrow"><i class="ti ti-chevron-right" /></div>
      </RouterLink>
    </div>
  </div>
</template>

<style scoped>
.page { padding: 28px 32px; max-width: 800px; margin: 0 auto; }
.page-header { margin-bottom: 20px; }
.page-title { font-size: 22px; font-weight: 800; letter-spacing: -0.4px; }
.page-sub { font-size: 13px; color: var(--text-muted); margin-top: 3px; }
.empty { display: flex; flex-direction: column; align-items: center; gap: 12px; padding: 60px 20px; color: var(--text-muted); font-size: 14px; text-align: center; }
.certs-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 14px; }
.cert-card { display: flex; align-items: center; gap: 16px; padding: 18px 20px; background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); text-decoration: none; transition: border-color 0.12s; }
.cert-card:hover { border-color: var(--purple); }
.cert-seal { width: 52px; height: 52px; border-radius: 50%; background: linear-gradient(135deg, #8255F2, #6E2BF0, #5A1FD6); display: flex; align-items: center; justify-content: center; flex-shrink: 0; box-shadow: 0 4px 12px rgba(110,43,240,0.3); }
.cert-body { flex: 1; }
.cert-name { font-size: 14px; font-weight: 700; color: var(--text-primary); }
.cert-tier { font-size: 12px; color: var(--purple); font-weight: 600; margin-top: 2px; }
.cert-date { font-size: 12px; color: var(--text-muted); margin-top: 6px; }
.cert-cred { font-size: 11px; color: var(--text-muted); font-family: monospace; margin-top: 2px; }
.cert-arrow { color: var(--text-muted); font-size: 16px; }
</style>
