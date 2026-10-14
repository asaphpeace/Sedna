<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAppStore } from '@/stores/app'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const app = useAppStore()
const auth = useAuthStore()

const cert = computed(() => app.certs.find((c: any) => c.id === Number(route.params.id)))

const issuedDate = computed(() =>
  cert.value ? new Date(cert.value.issued_at).toLocaleDateString('en-GB', { day: 'numeric', month: 'long', year: 'numeric' }) : ''
)

// Credential in SED-XXX-XXXXXXXX display format
const credId = computed(() => {
  if (!cert.value) return ''
  const n = cert.value.credential_number ?? cert.value.id
  return `SED-CHF-${String(n).toUpperCase()}`
})

const copied = ref(false)
function copyId() {
  navigator.clipboard.writeText(credId.value)
  copied.value = true
  setTimeout(() => copied.value = false, 2000)
}

function downloadPDF() {
  window.print()
}

function shareLinkedIn() {
  const url = `https://www.linkedin.com/profile/add?startTask=CERTIFICATION_NAME&name=${encodeURIComponent(cert.value?.cert_name ?? '')}&organizationName=Sedna+Academy&issueYear=${new Date(cert.value?.issued_at).getFullYear()}&certUrl=${encodeURIComponent(window.location.href)}`
  window.open(url, '_blank')
}

// Tier label like "Support Engineer · Tier 1"
const tierLabel = computed(() => {
  if (!cert.value) return ''
  return `${cert.value.tier_name}`
})
</script>

<template>
  <div class="page">
    <button class="back-btn" @click="router.push('/certs')">
      <i class="ti ti-arrow-left" /> Certificates
    </button>

    <div v-if="!cert" class="empty">Certificate not found.</div>

    <template v-else>
      <!-- Actions bar -->
      <div class="actions-bar">
        <div class="actions-left">
          <div class="cert-title-head">Your certificate</div>
          <div class="cert-cred-line">
            Credential ID <strong>{{ credId }}</strong>
            <button class="copy-btn" @click="copyId" :title="copied ? 'Copied!' : 'Copy ID'">
              <i :class="['ti', copied ? 'ti-check' : 'ti-copy']" />
            </button>
            · verifiable at <span class="verify-link">academy.sedna.com/verify</span>
          </div>
        </div>
        <div class="actions-right">
          <button class="btn btn-ghost action-btn" @click="shareLinkedIn">
            <i class="ti ti-brand-linkedin" style="color:#0A66C2" /> Add to profile
          </button>
          <button class="btn btn-ghost action-btn" @click="copyId">
            <i class="ti ti-share" /> Share
          </button>
          <button class="btn btn-primary action-btn" @click="downloadPDF">
            <i class="ti ti-download" /> Download PDF
          </button>
        </div>
      </div>

      <!-- Certificate document -->
      <div class="cert-wrapper" id="cert-print">
        <div class="cert-card">
          <div class="cert-border">
            <!-- Header -->
            <div class="cert-head">
              <div class="cert-logo-row">
                <img src="/sedna-logo.png" alt="" width="36" height="36" class="cert-logo-mark" />
                <div>
                  <div class="cert-brand">Sedna</div>
                  <div class="cert-brand-sub">LEARNING HUB</div>
                </div>
              </div>
              <div class="cert-cred-block">
                <div class="cert-cred-label">Certificate of Completion</div>
                <div class="cert-cred-num">No. {{ cert.credential_number }}</div>
              </div>
            </div>

            <!-- Body -->
            <div class="cert-body">
              <p class="cert-certify">This is to certify that</p>
              <div class="cert-recipient">{{ cert.recipient }}</div>
              <div class="cert-divider" />
              <p class="cert-completed">has successfully completed all requirements for</p>
              <div class="cert-path-name">{{ cert.cert_name }}</div>
              <div class="cert-sub">{{ tierLabel }}</div>
            </div>

            <!-- Footer -->
            <div class="cert-footer">
              <div class="cert-sig">
                <div class="cert-sig-name">Lucie Phillips</div>
                <div class="cert-sig-line" />
                <div class="cert-sig-title-text">Lucie Phillips</div>
                <div class="cert-sig-role">Chief Operating Officer</div>
              </div>
              <div class="cert-seal-block">
                <div class="cert-seal">
                  <i class="ti ti-rosette-discount-check-filled" style="font-size: 26px; color: #fff" />
                  <div class="cert-verified">VERIFIED</div>
                </div>
                <div class="cert-issued">Issued {{ issuedDate }}</div>
              </div>
              <div class="cert-sig">
                <div class="cert-sig-name">Nassia Katroutsou</div>
                <div class="cert-sig-line" />
                <div class="cert-sig-title-text">Nassia Katroutsou</div>
                <div class="cert-sig-role">Senior Education Manager</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Verifiability footer -->
      <div class="verify-footer">
        <i class="ti ti-shield-check" style="font-size:16px;color:var(--green)" />
        This credential is verifiable and tamper-evident. Anyone with the ID can confirm its authenticity.
      </div>
    </template>
  </div>
</template>

<style scoped>
.page { padding: 40px 24px 72px; max-width: 860px; margin: 0 auto; }
.back-btn { display: flex; align-items: center; gap: 6px; font-size: 13px; font-weight: 500; color: var(--text-secondary); padding: 6px 11px; border-radius: 8px; border: 1px solid var(--border); background: var(--surface); margin-bottom: 20px; cursor: pointer; }
.back-btn:hover { background: var(--purple-subtle); }
.empty { color: var(--text-muted); }

/* Actions bar */
.actions-bar { display: flex; align-items: flex-start; justify-content: space-between; gap: 16px; margin-bottom: 20px; flex-wrap: wrap; }
.actions-left {}
.cert-title-head { font-size: 20px; font-weight: 500; letter-spacing: -0.4px; color: var(--text-primary); }
.cert-cred-line { font-size: 12.5px; color: var(--text-muted); margin-top: 3px; display: flex; align-items: center; gap: 5px; flex-wrap: wrap; }
.cert-cred-line strong { color: var(--text-secondary); font-family: monospace; }
.copy-btn { background: none; border: none; cursor: pointer; color: var(--text-muted); font-size: 13px; padding: 1px 3px; border-radius: 4px; }
.copy-btn:hover { color: var(--purple); }
.verify-link { color: var(--purple); font-weight: 500; }
.actions-right { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.action-btn { font-size: 12.5px; padding: 8px 14px; }

/* Certificate card */
.cert-wrapper { padding: 10px; background: var(--surface); border: 1px solid var(--hairline); border-radius: var(--radius); box-shadow: var(--shadow-md); margin-bottom: 16px; }
.cert-border {
  border: 1px solid var(--lilac); border-radius: var(--radius-md);
  padding: 42px 52px 38px; position: relative; overflow: hidden;
  background: #fff;
}

.cert-head { display: flex; align-items: flex-start; justify-content: space-between; position: relative; margin-bottom: 40px; }
.cert-logo-row { display: flex; align-items: center; gap: 10px; }
/* The Sedna mark exactly as supplied — fixed square, never stretched or recoloured */
.cert-logo-mark { width: 36px; height: 36px; flex: none; object-fit: contain; display: block; }
.cert-brand { font-size: 18px; font-weight: 500; letter-spacing: -0.02em; line-height: 1; }
.cert-brand-sub { font-family: var(--font-mono); font-size: 9.5px; letter-spacing: 0.1em; color: var(--text-muted); margin-top: 4px; }
.cert-cred-block { text-align: right; }
.cert-cred-label { font-family: var(--font-mono); font-size: 10.5px; letter-spacing: 0.1em; text-transform: uppercase; color: var(--text-muted); }
.cert-cred-num { font-size: 11.5px; color: var(--text-muted); margin-top: 4px; font-family: var(--font-mono); }

.cert-body { text-align: center; position: relative; padding: 0 20px; }
.cert-certify { font-size: 14px; color: var(--text-muted); }
.cert-recipient { font-size: 44px; font-weight: 500; color: var(--text-primary); letter-spacing: -0.022em; margin-top: 10px; line-height: 1.08; }
.cert-divider { width: 80px; height: 2px; background: var(--purple-light); margin: 18px auto; border-radius: 2px; }
.cert-completed { font-size: 14px; color: var(--text-muted); margin-top: 4px; }
.cert-path-name { font-size: 26px; font-weight: 500; color: var(--purple); margin-top: 10px; letter-spacing: -0.012em; }
.cert-sub { font-family: var(--font-mono); font-size: 12px; letter-spacing: 0.1em; text-transform: uppercase; color: var(--text-muted); margin-top: 10px; }

.cert-footer { display: flex; align-items: flex-end; justify-content: space-between; gap: 20px; margin-top: 48px; position: relative; }
.cert-sig { text-align: center; min-width: 150px; }
.cert-sig-name { font-size: 26px; font-style: italic; color: var(--text-primary); line-height: 1; height: 32px; font-family: 'Spectral', serif; }
.cert-sig-line { height: 1px; background: var(--border-mid); margin: 6px 0 7px; }
.cert-sig-title-text { font-size: 12.5px; font-weight: 500; color: var(--text-primary); }
.cert-sig-role { font-size: 12px; color: var(--purple); margin-top: 2px; }

.cert-seal-block { display: flex; flex-direction: column; align-items: center; flex-shrink: 0; }
.cert-seal {
  width: 76px; height: 76px; border-radius: 50%;
  background: var(--purple);
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  position: relative;
}
.cert-seal::before { content: ''; position: absolute; inset: 5px; border-radius: 50%; border: 1.5px dashed rgba(255,255,255,0.65); }
.cert-verified { font-family: var(--font-mono); font-size: 6.5px; letter-spacing: 0.1em; color: #fff; margin-top: 2px; }
.cert-issued { font-size: 11px; color: var(--text-muted); margin-top: 9px; }

/* Verify footer */
.verify-footer {
  display: flex; align-items: center; justify-content: center; gap: 7px;
  font-size: 12px; color: var(--text-muted); padding: 10px;
}

/* Print styles */
@media print {
  .back-btn, .actions-bar, .verify-footer { display: none !important; }
  .page { padding: 0; max-width: 100%; }
  .cert-wrapper { box-shadow: none; }
}
</style>
