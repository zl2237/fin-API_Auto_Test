<template>
  <div class="page">
    <!-- 左侧可折叠导航栏 -->
    <aside class="sidebar" :class="{ collapsed: sidebarCollapsed }">
      <!-- 折叠按钮 -->
      <button class="sidebar-toggle" @click="sidebarCollapsed = !sidebarCollapsed">
        <el-icon><Fold v-if="!sidebarCollapsed" /><Expand v-else /></el-icon>
      </button>

      <!-- 品牌区 -->
      <div class="sidebar-brand">
        <svg class="brand-icon" viewBox="0 0 24 24" fill="none">
          <path d="M9 3H5a2 2 0 00-2 2v4m6-6h10a2 2 0 012 2v4M9 3v18m0 0h10a2 2 0 002-2v-4M9 21H5a2 2 0 01-2-2v-4m0-6v6m18-6v6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        <span class="brand-text">API 测试平台</span>
      </div>

      <!-- 用户信息 -->
      <div class="sidebar-user">
        <el-tag type="info" size="small" effect="plain">PR Study</el-tag>
        <span class="username">{{ auth.username }}</span>
        <el-button type="danger" plain size="small" @click="handleLogout">
          <el-icon><SwitchButton /></el-icon>
          <span v-show="!sidebarCollapsed">退出</span>
        </el-button>
      </div>

      <!-- 导航菜单 -->
      <el-menu
        :default-active="$route.path"
        class="sidebar-menu"
        :collapse="sidebarCollapsed"
        :collapse-transition="false"
        router
      >
        <el-menu-item index="/">
          <el-icon><HomeFilled /></el-icon>
          <template #title>首页概览</template>
        </el-menu-item>
        <el-sub-menu index="logistics">
          <template #title>
            <el-icon><Connection /></el-icon>
            <span>物流系统</span>
          </template>
          <el-menu-item index="/logistics/link-test">
            <el-icon><Connection /></el-icon>
            <span>链路测试</span>
          </el-menu-item>
          <el-menu-item index="/logistics/document-upload">
            <el-icon><Files /></el-icon>
            <span>单证上传</span>
          </el-menu-item>
          <el-menu-item index="/logistics/approval-config">
            <el-icon><EditPen /></el-icon>
            <span>审批流配置</span>
          </el-menu-item>
        </el-sub-menu>
        <el-menu-item index="/platform/users">
          <el-icon><UserIcon /></el-icon>
          <template #title>用户管理</template>
        </el-menu-item>
      </el-menu>
    </aside>

    <!-- 主内容区 -->
    <div class="main">
      <div class="user-manage-container">
        <div class="page-header">
          <h1>用户管理</h1>
          <el-button type="primary" @click="openCreateDialog">新增用户</el-button>
        </div>

        <el-card shadow="never">
          <el-table :data="users" stripe style="width: 100%">
            <el-table-column prop="username" label="账号" min-width="180" />
            <el-table-column prop="role" label="角色" min-width="140">
              <template #default="{ row }">
                <el-tag :type="row.role === 'admin' ? 'warning' : 'info'">
                  {{ row.role === 'admin' ? '管理员' : '普通用户' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="220" fixed="right">
              <template #default="{ row }">
                <el-button size="small" type="primary" link @click="openEditDialog(row)">
                  编辑
                </el-button>
                <el-popconfirm title="确认删除该账号？" @confirm="handleDelete(row.username)">
                  <template #reference>
                    <el-button size="small" type="danger" link :disabled="isCurrentUser(row.username)">
                      删除
                    </el-button>
                  </template>
                </el-popconfirm>
              </template>
            </el-table-column>
          </el-table>
        </el-card>

        <el-dialog v-model="dialogVisible" :title="dialogMode === 'create' ? '新增用户' : '编辑用户'" width="420px">
          <el-form :model="form" label-width="80px">
            <el-form-item label="账号" required>
              <el-input v-model="form.username" :disabled="dialogMode === 'edit'" />
            </el-form-item>
            <el-form-item v-if="dialogMode === 'create'" label="密码" required>
              <el-input v-model="form.password" type="password" show-password />
            </el-form-item>
            <el-form-item v-if="dialogMode === 'edit'" label="新密码">
              <el-input v-model="form.password" type="password" show-password placeholder="留空不修改" />
            </el-form-item>
            <el-form-item label="角色" required>
              <el-select v-model="form.role" style="width: 100%">
                <el-option label="管理员" value="admin" />
                <el-option label="普通用户" value="user" />
              </el-select>
            </el-form-item>
          </el-form>
          <template #footer>
            <el-button @click="dialogVisible = false">取消</el-button>
            <el-button type="primary" :loading="loading" :disabled="!canSubmit" @click="handleSubmit">
              确定
            </el-button>
          </template>
        </el-dialog>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  Expand, Fold, SwitchButton, Files, EditPen, Connection, HomeFilled, User as UserIcon
} from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'
import request from '@/api/request'
import type { User } from '@/api/users'

const router = useRouter()
const auth = useAuthStore()
const users = ref<User[]>([])
const dialogVisible = ref(false)
const dialogMode = ref<'create' | 'edit'>('create')
const loading = ref(false)
const sidebarCollapsed = ref(false)
const form = reactive<{ username: string; password: string; role: string }>({
  username: '',
  password: '',
  role: 'user',
})

const isCurrentUser = (username: string) => username === auth.username
const canSubmit = computed(() => {
  const usernameOk = form.username.trim().length > 0 && form.username !== auth.username
  const passwordOk = dialogMode.value === 'create' ? form.password.trim().length > 0 : true
  return usernameOk && passwordOk && ['admin', 'user'].includes(form.role)
})

async function loadUsers() {
  try {
    const { data } = await request.get('/users')
    if (!data?.ok) {
      throw new Error(data?.message || '加载失败')
    }
    users.value = (data as any).users || []
  } catch (e: any) {
    ElMessage.error(e?.message || '加载用户失败')
  }
}

function openCreateDialog() {
  dialogMode.value = 'create'
  Object.assign(form, { username: '', password: '', role: 'user' })
  dialogVisible.value = true
}

function openEditDialog(user: User) {
  dialogMode.value = 'edit'
  Object.assign(form, { username: user.username, password: '', role: user.role })
  dialogVisible.value = true
}

async function handleSubmit() {
  loading.value = true
  try {
    if (dialogMode.value === 'create') {
      const { data } = await request.post('/users', {
        username: form.username.trim(),
        password: form.password.trim(),
        role: form.role,
      })
      if (!data?.ok) {
        throw new Error(data?.message || '创建失败')
      }
      ElMessage.success('创建成功')
    } else {
      const payload: any = { role: form.role }
      if (form.password.trim()) {
        Object.assign(payload, { password: form.password.trim() })
      }
      const { data } = await request.put(`/users/${encodeURIComponent(form.username)}`, payload)
      if (!data?.ok) {
        throw new Error(data?.message || '更新失败')
      }
      ElMessage.success('更新成功')
    }
    dialogVisible.value = false
    await loadUsers()
  } catch (e: any) {
    ElMessage.error(e?.message || '操作失败')
  } finally {
    loading.value = false
  }
}

async function handleDelete(username: string) {
  const { data } = await request.delete(`/users/${encodeURIComponent(username)}`)
  if (!data?.ok) {
    ElMessage.error(data?.message || '删除失败')
    return
  }
  ElMessage.success('删除成功')
  await loadUsers()
}

function handleLogout() {
  auth.logout()
  router.push({ name: 'Login' })
}

onMounted(loadUsers)
</script>

<style scoped>
.page {
  min-height: 100vh;
  background: #f0f2f5;
}

/* 左侧边栏 */
.sidebar {
  width: 280px;
  min-height: 100vh;
  background: linear-gradient(180deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
  color: #fff;
  display: flex;
  flex-direction: column;
  position: fixed;
  left: 0;
  top: 0;
  z-index: 100;
  transition: width 0.3s ease;
  overflow-x: hidden;
}
.sidebar.collapsed {
  width: 64px;
}

/* 折叠按钮 */
.sidebar-toggle {
  position: absolute;
  top: 12px;
  right: -12px;
  width: 24px;
  height: 24px;
  background: #1a1a2e;
  border: 1px solid rgba(255,255,255,0.2);
  border-radius: 50%;
  color: #fff;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 101;
  transition: all 0.2s;
}
.sidebar-toggle:hover {
  background: #667eea;
  border-color: #667eea;
}

/* 品牌区 */
.sidebar-brand {
  padding: 16px;
  display: flex;
  align-items: center;
  gap: 10px;
  border-bottom: 1px solid rgba(255,255,255,0.1);
}
.collapsed .sidebar-brand {
  justify-content: center;
  padding: 16px 8px;
}
.brand-icon {
  width: 28px;
  height: 28px;
  color: #667eea;
  flex-shrink: 0;
}
.brand-text {
  font-size: 16px;
  font-weight: 700;
  color: #fff;
  letter-spacing: 1px;
  white-space: nowrap;
  overflow: hidden;
}
.collapsed .brand-text {
  display: none;
}

/* 用户区 */
.sidebar-user {
  padding: 12px 16px;
  display: flex;
  align-items: center;
  gap: 8px;
  border-bottom: 1px solid rgba(255,255,255,0.1);
}
.collapsed .sidebar-user {
  flex-direction: column;
  padding: 12px 8px;
  gap: 8px;
}
.username {
  font-size: 13px;
  color: rgba(255,255,255,0.7);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
:deep(.el-tag--info) {
  background: rgba(255,255,255,0.1);
  border-color: rgba(255,255,255,0.2);
  color: #fff;
}
:deep(.el-button--danger.is-plain) {
  color: rgba(255,255,255,0.7);
  border-color: rgba(255,255,255,0.2);
  background: transparent;
  padding: 6px 8px;
}
:deep(.el-button--danger.is-plain:hover) {
  color: #fff;
  border-color: rgba(255,255,255,0.5);
  background: rgba(245,108,108,0.2);
}

/* 导航菜单 */
.sidebar-menu {
  background: transparent;
  border-right: none;
}
:deep(.el-menu) {
  background: transparent;
}
:deep(.el-menu-item),
:deep(.el-sub-menu__title) {
  color: rgba(255,255,255,0.85);
  height: 44px;
  line-height: 44px;
}
:deep(.el-menu-item:hover),
:deep(.el-sub-menu__title:hover) {
  background: rgba(102,126,234,0.2);
  color: #fff;
}
:deep(.el-menu-item.is-active) {
  background: linear-gradient(90deg, #667eea, #764ba2);
  color: #fff;
}
:deep(.el-sub-menu .el-menu-item) {
  padding-left: 48px !important;
  height: 40px;
  line-height: 40px;
}
:deep(.el-sub-menu__title) {
  height: 44px;
  line-height: 44px;
}

/* 主内容区 */
.main {
  flex: 1;
  margin-left: 280px;
  padding: 20px 24px;
  transition: margin-left 0.3s ease;
}
.user-manage-container {
  max-width: 1200px;
  margin: 0 auto;
  width: 100%;
}
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}
.page-header h1 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
}
</style>
