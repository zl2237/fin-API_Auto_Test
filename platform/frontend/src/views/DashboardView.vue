<template>
  <div class="page">
    <!-- 顶部导航栏 -->
    <header class="topbar">
      <div class="topbar-inner">
        <div class="topbar-brand">
          <svg class="brand-icon" viewBox="0 0 24 24" fill="none">
            <path d="M9 3H5a2 2 0 00-2 2v4m6-6h10a2 2 0 012 2v4M9 3v18m0 0h10a2 2 0 002-2v-4M9 21H5a2 2 0 01-2-2v-4m0-6v6m18-6v6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          <span class="brand-text">API 测试平台</span>
          <el-tag type="info" size="small" effect="plain">PR Study</el-tag>
        </div>
        <div class="topbar-user">
          <span class="username">{{ auth.username }}</span>
          <el-divider direction="vertical" />
          <el-button type="danger" plain size="small" @click="handleLogout">
            <el-icon><SwitchButton /></el-icon>
            退出
          </el-button>
        </div>
      </div>
    </header>

    <!-- 主内容区 -->
    <div class="main">
      <!-- 左侧配置 -->
      <aside class="sidebar">
        <!-- 环境配置 -->
        <el-card class="cfg-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <el-icon><Monitor /></el-icon>
              <span>环境配置</span>
            </div>
          </template>
          <el-form label-position="top" size="small">
            <el-form-item label="BASE_URL">
              <el-select v-model="form.base_url" placeholder="请选择环境" style="width: 100%">
                <el-option label="TIDB（测试）" value="https://fin-tidb.21eflag.com/" />
                <el-option label="PRE（预发）" value="https://fin-pre.21eflag.com/" />
              </el-select>
            </el-form-item>
            <el-form-item label="LOGIN_URL">
              <el-input v-model="form.login_url" placeholder="/api/home/login/userLogin" clearable />
            </el-form-item>
          </el-form>
        </el-card>

        <!-- 测试账号 -->
        <el-card class="cfg-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <el-icon><User /></el-icon>
              <span>测试账号</span>
            </div>
          </template>
          <el-form label-position="top" size="small">
            <el-form-item label="USERNAME">
              <el-input v-model="form.test_username" placeholder="测试账号" clearable />
            </el-form-item>
            <el-form-item label="PASSWORD">
              <el-input v-model="form.test_password" type="password" show-password placeholder="测试密码" />
            </el-form-item>
            <el-form-item label="USER_ID">
              <el-input v-model="form.order_create_id" placeholder="创建者用户ID" clearable />
            </el-form-item>
          </el-form>
        </el-card>

        <!-- 执行配置 -->
        <el-card class="cfg-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <el-icon><Setting /></el-icon>
              <span>执行配置</span>
            </div>
          </template>
          <el-form label-position="top" size="small">
            <el-form-item label="运行链路">
              <el-select v-model="form.marker" placeholder="请选择" filterable style="width: 100%">
                <el-option
                  v-for="item in markers"
                  :key="item.name"
                  :label="`${item.name} - ${item.description}`"
                  :value="item.name"
                />
              </el-select>
            </el-form-item>
            <el-form-item label="提单号前缀">
              <el-input v-model="form.order_prefix" placeholder="如 lele" clearable />
            </el-form-item>
            <el-form-item label="循环次数">
              <el-input-number v-model="form.loop_count" :min="1" :max="100" style="width: 100%" />
            </el-form-item>
            <el-form-item style="margin-top: 16px">
              <el-button
                type="primary"
                :loading="running"
                :disabled="!form.marker"
                @click="handleRun"
                style="width: 100%"
              >
                <el-icon v-if="!running"><VideoPlay /></el-icon>
                {{ running ? '运行中...' : '开始执行' }}
              </el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </aside>

      <!-- 右侧结果 + 日志 -->
      <main class="content">
        <!-- 执行结果卡片 -->
        <el-card class="result-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <el-icon><DataAnalysis /></el-icon>
              <span>执行结果</span>
            </div>
          </template>

          <!-- 运行中 -->
          <template v-if="running">
            <div class="running-indicator">
              <div class="pulse-ring" />
              <div class="pulse-dot" />
              <span class="running-text">运行中...</span>
              <el-tag v-if="run.marker" type="primary" size="small">{{ run.marker }}</el-tag>
            </div>
          </template>

          <!-- 通过 -->
          <template v-else-if="run.status === 'completed' || run.status === 'success'">
            <div class="result-summary">
              <div class="result-status result-success">
                <el-icon class="status-icon"><CircleCheckFilled /></el-icon>
                <span>全部通过</span>
              </div>
              <div class="stats-grid">
                <div class="stat-card total">
                  <span class="stat-label">总计</span>
                  <span class="stat-value">{{ summary.total }}</span>
                  <span class="stat-meta">{{ run.marker }}</span>
                </div>
                <div class="stat-card passed">
                  <span class="stat-label">Passed</span>
                  <span class="stat-value">{{ summary.passed }}</span>
                  <span class="stat-meta">用例通过</span>
                </div>
                <div class="stat-card failed">
                  <span class="stat-label">Failed</span>
                  <span class="stat-value">{{ summary.failed }}</span>
                  <span class="stat-meta">用例失败</span>
                </div>
                <div class="stat-card skipped">
                  <span class="stat-label">Skipped</span>
                  <span class="stat-value">{{ summary.skipped }}</span>
                  <span class="stat-meta">跳过用例</span>
                </div>
              </div>
              <el-collapse v-if="summary.failed > 0" style="margin-top: 12px">
                <el-collapse-item title="失败用例详情" name="failures">
                  <el-table :data="failedCases" stripe size="small">
                    <el-table-column prop="name" label="用例" min-width="200" show-overflow-tooltip />
                    <el-table-column prop="message" label="原因" min-width="200" show-overflow-tooltip />
                  </el-table>
                </el-collapse-item>
              </el-collapse>
            </div>
          </template>

          <!-- 失败 -->
          <template v-else-if="run.status === 'failed'">
            <div class="result-status result-error">
              <el-icon class="status-icon"><CircleCloseFilled /></el-icon>
              <span>执行失败</span>
            </div>
            <el-alert :title="run.result?.error || 'pytest 退出码非 0'" type="error" :closable="false" />
          </template>

          <!-- 初始 -->
          <template v-else>
            <el-empty description="选择链路并点击「开始执行」" :image-size="80" />
          </template>
        </el-card>

        <!-- 日志卡片 -->
        <el-card class="log-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <el-icon><Document /></el-icon>
              <span>运行日志</span>
              <el-tag v-if="logs.length" type="info" size="small">{{ logs.length }} 行</el-tag>
            </div>
          </template>
          <div class="log-box" ref="logBoxRef">
            <div v-if="logs.length === 0 && !running" class="log-empty">暂无日志</div>
            <div v-for="(line, idx) in logs" :key="idx" class="log-line" :class="logClass(line)">{{ line }}</div>
            <div v-if="running" class="log-cursor">_</div>
          </div>
        </el-card>
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref, onMounted, nextTick, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  Monitor, User, Setting, DataAnalysis, Document,
  VideoPlay, CircleCheckFilled, CircleCloseFilled, SwitchButton
} from '@element-plus/icons-vue'
import request from '@/api/request'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const auth = useAuthStore()
const logBoxRef = ref<HTMLElement>()
const markers = ref<Array<{ name: string; description: string }>>([])

const form = reactive({
  base_url: 'https://fin-tidb.21eflag.com/',
  login_url: '/api/home/login/userLogin',
  test_username: '',
  test_password: '',
  token_field: 'data.token',
  token_type: '',
  auth_header: 'Authorization',
  marker: '',
  order_prefix: 'lele',
  loop_count: 1,
})

const run = reactive<any>({ run_id: '', status: '', marker: '', result: {}, logs: [] })
const logs = ref<string[]>([])
const running = ref(false)

const summary = computed(() => run.result?.summary || {})
const failedCases = computed(() => summary.value.details?.failed || [])

function handleLogout() {
  auth.logout()
  router.push({ name: 'Login' })
}

async function loadMarkers() {
  try {
    const { data } = await request.get('/markers')
    markers.value = data.markers
    if (markers.value.length) {
      form.marker = markers.value[0].name
    }
  } catch (e) {
    ElMessage.error('加载链路失败')
  }
}

async function handleRun() {
  if (!form.base_url || !form.test_username || !form.test_password) {
    ElMessage.warning('请填写 BASE_URL、测试账号和密码')
    return
  }
  if (!form.marker) {
    ElMessage.warning('请选择运行链路')
    return
  }

  running.value = true
  logs.value = []
  run.run_id = ''
  run.status = 'running'
  run.result = {}

  try {
    const { data } = await request.post('/run', {
      base_url: form.base_url,
      login_url: form.login_url,
      test_username: form.test_username,
      test_password: form.test_password,
      token_field: form.token_field,
      token_type: form.token_type,
      auth_header: form.auth_header,
      marker: form.marker,
      order_prefix: form.order_prefix,
      loop_count: form.loop_count,
    })
    if (!data.ok) {
      throw new Error(data.message || '启动失败')
    }
    run.run_id = data.run_id
    run.marker = data.marker
    listenLogs(data.run_id)
  } catch (e: any) {
    ElMessage.error(e?.message || '启动失败')
    run.status = 'failed'
    running.value = false
  }
}

function listenLogs(runId: string) {
  const es = new EventSource(`/api/run/${runId}/logs`)
  es.onmessage = (e) => {
    logs.value.push(e.data)
    nextTick(() => {
      if (logBoxRef.value) {
        logBoxRef.value.scrollTop = logBoxRef.value.scrollHeight
      }
    })
  }
  es.addEventListener('done', async () => {
    es.close()
    running.value = false
    try {
      const resp = await request.get(`/run/${runId}`)
      run.status = resp.data.status === 'failed' ? 'failed' : 'completed'
      run.result = resp.data.result || {}
      run.logs = resp.data.logs || []
    } catch {
      run.status = 'completed'
    }
  })
  es.onerror = () => {
    es.close()
    running.value = false
    if (!run.status) run.status = 'failed'
  }
}

function logClass(line: string) {
  if (line.includes('FAILED') || line.includes('ERROR')) return 'log-fail'
  if (line.includes('PASSED') || line.includes('test session starts') || line.includes('passed')) return 'log-pass'
  if (line.includes('WARNING') || line.includes('WARN')) return 'log-warn'
  if (line.startsWith('=') || line.trim() === '') return 'log-sep'
  return ''
}

onMounted(() => {
  loadMarkers()
})
</script>

<style scoped>
.page {
  min-height: 100vh;
  background: #f0f2f5;
  display: flex;
  flex-direction: column;
}

/* 顶部导航栏 */
.topbar {
  background: linear-gradient(135deg, #1a1a2e, #16213e, #0f3460);
  color: #fff;
  box-shadow: 0 2px 12px rgba(0,0,0,0.3);
  position: sticky;
  top: 0;
  z-index: 100;
}
.topbar-inner {
  max-width: 1600px;
  margin: 0 auto;
  padding: 0 24px;
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.topbar-brand {
  display: flex;
  align-items: center;
  gap: 10px;
}
.brand-icon {
  width: 28px;
  height: 28px;
  color: #667eea;
}
.brand-text {
  font-size: 18px;
  font-weight: 700;
  color: #fff;
  letter-spacing: 1px;
}
.topbar-user {
  display: flex;
  align-items: center;
  gap: 4px;
}
.username {
  font-size: 13px;
  color: rgba(255,255,255,0.7);
}
:deep(.el-divider--vertical) {
  border-color: rgba(255,255,255,0.2);
  margin: 0 8px;
}
:deep(.el-button--danger.is-plain) {
  color: rgba(255,255,255,0.7);
  border-color: rgba(255,255,255,0.2);
  background: transparent;
}
:deep(.el-button--danger.is-plain:hover) {
  color: #fff;
  border-color: rgba(255,255,255,0.5);
}

/* 主内容区 */
.main {
  display: flex;
  gap: 16px;
  max-width: 1600px;
  width: 100%;
  margin: 20px auto;
  padding: 0 16px;
  flex: 1;
  align-items: flex-start;
}

/* 左侧边栏 */
.sidebar {
  width: 340px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.cfg-card {
  border-radius: 12px;
  border: none;
}
:deep(.cfg-card .el-card__header) {
  padding: 12px 16px;
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: #fff;
  border-radius: 12px 12px 0 0;
}
:deep(.cfg-card .el-card__body) {
  padding: 12px 16px 16px;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  font-size: 14px;
}
:deep(.el-form-item__label) {
  font-size: 12px;
  color: #666;
  font-weight: 500;
}

/* 右侧内容 */
.content {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.result-card,
.log-card {
  border-radius: 12px;
  border: none;
}
:deep(.result-card .el-card__header),
:deep(.log-card .el-card__header) {
  padding: 12px 16px;
  background: linear-gradient(135deg, #1a1a2e, #16213e);
  color: #fff;
  border-radius: 12px 12px 0 0;
}
:deep(.result-card .el-card__body),
:deep(.log-card .el-card__body) {
  padding: 16px;
}

/* 运行状态指示器 */
.running-indicator {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 0;
  position: relative;
}
.pulse-ring {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  border: 3px solid #409eff;
  position: absolute;
  left: 0;
  animation: pulse-ring 1.6s cubic-bezier(0.215, 0.61, 0.355, 1) infinite;
}
.pulse-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: #409eff;
  position: absolute;
  left: 12px;
  top: 50%;
  transform: translateY(-50%);
  animation: pulse-dot 1.6s cubic-bezier(0.215, 0.61, 0.355, 1) infinite;
}
@keyframes pulse-ring {
  0% { transform: scale(0.6); opacity: 1; }
  100% { transform: scale(1.4); opacity: 0; }
}
@keyframes pulse-dot {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.6; }
}
.running-text {
  font-size: 14px;
  color: #409eff;
  font-weight: 500;
  margin-left: 44px;
}

/* 结果统计卡片 */
.result-summary {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.result-status {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 16px;
  border-radius: 8px;
  font-size: 15px;
  font-weight: 600;
  margin-bottom: 4px;
}
.result-success {
  background: #f0f9eb;
  color: #67c23a;
}
.result-error {
  background: #fef0f0;
  color: #f56c6c;
}
.status-icon {
  font-size: 20px;
}

/* 统计指标网格 - 中大厂 Dashboard 风格 */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
}
.stat-card {
  background: #fafafa;
  border: 1px solid #f0f0f0;
  border-radius: 8px;
  padding: 14px 16px;
  display: flex;
  flex-direction: column;
  gap: 4px;
  transition: box-shadow 0.2s;
}
.stat-card:hover {
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}
.stat-card.total { border-top: 3px solid #909399; }
.stat-card.passed { border-top: 3px solid #67c23a; }
.stat-card.failed { border-top: 3px solid #f56c6c; }
.stat-card.skipped { border-top: 3px solid #909399; }
.stat-label {
  font-size: 12px;
  color: #909399;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}
.stat-value {
  font-size: 28px;
  font-weight: 700;
  line-height: 1;
}
.stat-card.passed .stat-value { color: #67c23a; }
.stat-card.failed .stat-value { color: #f56c6c; }
.stat-card.total .stat-value { color: #303133; }
.stat-card.skipped .stat-value { color: #909399; }
.stat-meta {
  font-size: 11px;
  color: #c0c4cc;
  margin-top: 2px;
}

/* 日志区 */
.log-box {
  background: #0d1117;
  border-radius: 8px;
  max-height: 380px;
  overflow-y: auto;
  padding: 12px 16px;
  font-family: 'Cascadia Code', 'Fira Code', Consolas, monospace;
  font-size: 12.5px;
  line-height: 1.7;
  border: 1px solid #21262d;
}
.log-empty {
  color: #484f58;
  text-align: center;
  padding: 32px;
}
.log-line {
  white-space: pre-wrap;
  word-break: break-all;
  color: #c9d1d9;
}
.log-cursor {
  color: #58a6ff;
  animation: blink 1s step-end infinite;
}
.log-pass { color: #3fb950; }
.log-fail { color: #f85149; }
.log-warn { color: #d29922; }
.log-sep { color: #484f58; }

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}

:deep(.el-empty__description p) {
  color: #aaa;
}
</style>
