import request from './request'

export interface User {
  username: string
  role: 'admin' | 'user'
}

export interface CreateUserPayload {
  username: string
  password: string
  role: 'admin' | 'user'
}

export async function fetchUsers() {
  const { data } = await request.get('/users')
  return data as { ok: boolean; users: User[] }
}

export async function createUser(payload: CreateUserPayload) {
  const { data } = await request.post('/users', payload)
  return data as { ok: boolean; message?: string }
}

export async function updateUser(username: string, payload: Partial<CreateUserPayload>) {
  const { data } = await request.put(`/users/${encodeURIComponent(username)}`, payload)
  return data as { ok: boolean; message?: string }
}

export async function deleteUser(username: string) {
  const { data } = await request.delete(`/users/${encodeURIComponent(username)}`)
  return data as { ok: boolean; message?: string }
}
