import { ref, computed } from 'vue'
import { authApi, pathsApi, publicApi } from '@/api'
import { useAuthStore } from '@/stores/auth'

export interface Course {
  id: number
  name: string
  description: string
  audience: 'customer' | 'internal' | string
  products: string[]
  mod_count: number
  tier_count: number
}

// Courses for the public Hub pages. Signed-in people get everything they can
// open (including internal staff courses); visitors get the public catalogue.
export function useCatalog() {
  const auth = useAuthStore()
  const courses = ref<Course[]>([])
  const loaded = ref(false)

  async function load() {
    if (auth.token) {
      try {
        // Quiet calls: an expired session just falls back to the public view
        if (!auth.user) auth.user = (await authApi.meQuiet()).data
        courses.value = (await pathsApi.listQuiet()).data
        loaded.value = true
        return
      } catch {
        auth.logout()
      }
    }
    courses.value = (await publicApi.catalog()).data
    loaded.value = true
  }

  const signedIn = computed(() => !!auth.user)
  const forProduct = (p: string) => courses.value.filter(c => c.products?.includes(p))

  // First course whose name matches any keyword (role and function cards)
  function match(list: Course[], keywords: string[]) {
    return list.find(c => keywords.some(k => c.name.toLowerCase().includes(k.toLowerCase())))
  }

  return { courses, loaded, signedIn, load, forProduct, match }
}
