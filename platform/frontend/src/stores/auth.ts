import { defineStore } from 'pinia'
import { ref } from 'vue'

const TOKEN_KEY = 'platform_token'
const USERNAME_KEY = 'platform_username'
const ROLE_KEY = 'platform_role'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem(TOKEN_KEY) || '')
  const username = ref(localStorage.getItem(USERNAME_KEY) || '')
  const role = ref(localStorage.getItem(ROLE_KEY) || '')

  const isLoggedIn = ref(!!token.value)
  const isAdmin = ref(role.value === 'admin')

  function login(name: string, t: string, userRole: string) {
    token.value = t
    username.value = name
    role.value = userRole
    localStorage.setItem(TOKEN_KEY, t)
    localStorage.setItem(USERNAME_KEY, name)
    localStorage.setItem(ROLE_KEY, userRole)
    isLoggedIn.value = true
    isAdmin.value = userRole === 'admin'
  }

  function logout() {
    token.value = ''
    username.value = ''
    role.value = ''
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(USERNAME_KEY)
    localStorage.removeItem(ROLE_KEY)
    isLoggedIn.value = false
    isAdmin.value = false
  }

  return { token, username, role, isLoggedIn, isAdmin, login, logout }
})
