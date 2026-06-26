import { defineStore } from 'pinia'
import { ref } from 'vue'

const TOKEN_KEY = 'platform_token'
const USERNAME_KEY = 'platform_username'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem(TOKEN_KEY) || '')
  const username = ref(localStorage.getItem(USERNAME_KEY) || '')
  const isLoggedIn = ref(!!token.value)

  function login(name: string, t: string) {
    token.value = t
    username.value = name
    localStorage.setItem(TOKEN_KEY, t)
    localStorage.setItem(USERNAME_KEY, name)
    isLoggedIn.value = true
  }

  function logout() {
    token.value = ''
    username.value = ''
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(USERNAME_KEY)
    isLoggedIn.value = false
  }

  return { token, username, isLoggedIn, login, logout }
})
