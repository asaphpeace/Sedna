import { defineStore } from 'pinia'
import { ref } from 'vue'
import { authApi } from '@/api'

export interface User {
  id: number
  email: string
  name: string
  initial: string
  color: string
  role: string | null
  status: string
  is_admin: boolean
  org_id: number
}

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  const token = ref<string | null>(localStorage.getItem('token'))

  async function login(email: string, password: string) {
    const { data } = await authApi.login(email, password)
    token.value = data.access_token
    localStorage.setItem('token', data.access_token)
    await fetchMe()
  }

  async function fetchMe() {
    const { data } = await authApi.me()
    user.value = data
  }

  function logout() {
    token.value = null
    user.value = null
    localStorage.removeItem('token')
  }

  return { user, token, login, fetchMe, logout }
})
