// Single source of truth for product display metadata (label, icon, color).
// Previously duplicated across ~6 view files with inconsistent labels
// (short "VMS"/"Stream"/"Cross" in some, long "Dataloy VMS"/"Sedna Stream"
// in others) — this reconciles that and is also what the Paths page groups
// learning paths by.
export interface ProductMeta {
  label: string       // long form, used for section headers ("Sedna VMS")
  shortLabel: string   // short form, used for chips/pills ("VMS")
  icon: string          // Tabler icon class
  color: string         // foreground color (text/icon)
  bg: string            // background color (chips/badges)
}

export const PRODUCT_META: Record<string, ProductMeta> = {
  vms: {
    label: 'Sedna VMS', shortLabel: 'VMS',
    icon: 'ti-ship', color: '#6E2BF0', bg: '#F1EBFE',
  },
  stream: {
    label: 'Sedna Email', shortLabel: 'Email',
    icon: 'ti-mail', color: '#0B8FB0', bg: '#E3F4F9',
  },
  bridgelabs: {
    label: 'Bridge Labs', shortLabel: 'Bridge Labs',
    icon: 'ti-anchor', color: '#0E9E6E', bg: '#E2F6EC',
  },
}

// Display order for grouped sections (Paths page) and select options (admin editor).
export const PRODUCT_ORDER = ['vms', 'stream', 'bridgelabs'] as const

export function productLabel(product: string): string {
  return PRODUCT_META[product]?.label ?? product
}

export function productShortLabel(product: string): string {
  return PRODUCT_META[product]?.shortLabel ?? product
}
