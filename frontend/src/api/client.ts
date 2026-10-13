import axios from 'axios'

const client = axios.create({ baseURL: '/api' })

client.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

client.interceptors.response.use(
  (r) => r,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('token')
      // Public Hub pages try the signed-in catalogue first and fall back
      // quietly; everywhere else an expired session goes to sign-in
      if (!err.config?.skipAuthRedirect) {
        window.location.href = '/login?redirect=' + encodeURIComponent(window.location.pathname)
      }
    }
    return Promise.reject(err)
  }
)

export default client
