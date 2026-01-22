<template>
  <div class="profile-container">
    <nav class="top-nav glass-card">
      <div class="nav-brand" @click="router.push('/')" style="cursor: pointer;">
        <span class="logo-text">诗云</span>
        <span class="edition-badge">Zen Edition</span>
      </div>
      <div class="nav-actions">
        <div class="nav-btn-card" @click="router.push('/')">
          <n-icon><NHome /></n-icon>
          <span>归园</span>
        </div>
      </div>
    </nav>

    <main class="profile-main">
      <div class="profile-card glass-card">
        <div class="profile-header">
          <div class="avatar-circle">
            {{ currentUser.charAt(0) }}
          </div>
          <div class="header-info">
            <h2>{{ currentUser }}</h2>
            <p>诗心未泯，墨香犹在</p>
          </div>
        </div>

        <div class="profile-body">
          <n-tabs type="line" animated>
            <n-tab-pane name="basic" tab="基本修缮">
              <div class="form-section">
                <div class="form-item">
                  <label>称谓 (Username)</label>
                  <n-input v-model:value="formData.username" placeholder="请输入新称谓" round />
                </div>
                <div class="form-item">
                  <label>口令 (Password)</label>
                  <n-input v-model:value="formData.password" type="password" show-password-on="click" placeholder="如需更改请输入新口令" round />
                </div>
                <div class="form-actions">
                  <n-button type="primary" round block @click="handleUpdate" :loading="updating">
                    保存修缮
                  </n-button>
                </div>
              </div>
            </n-tab-pane>
            <n-tab-pane name="stats" tab="诗缘往迹">
              <div class="stats-grid">
                <div class="stat-item">
                   <div class="stat-value">{{ reviews.length }}</div>
                   <div class="stat-label">雅评数</div>
                </div>
                <div class="stat-item">
                   <div class="stat-value">{{ preferenceCount }}</div>
                   <div class="stat-label">偏好主题</div>
                </div>
              </div>
            </n-tab-pane>
          </n-tabs>
        </div>

        <div class="profile-footer">
          <div class="divider"></div>
          <n-button quaternary round block type="error" @click="handleLogout" class="logout-btn">
            <template #icon><n-icon><NLogOut /></n-icon></template>
            离席
          </n-button>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { 
  NInput, 
  NButton, 
  NTabs, 
  NTabPane, 
  NIcon, 
  useMessage 
} from 'naive-ui'
import { 
  HomeOutline as NHome,
  LogOutOutline as NLogOut,
  PersonOutline as NPerson
} from '@vicons/ionicons5'
import axios from 'axios'

const router = useRouter()
const message = useMessage()
const currentUser = ref(localStorage.getItem('user') || '访客')
const reviews = ref([])
const preferenceCount = ref(0)
const updating = ref(false)

const formData = ref({
  username: currentUser.value,
  password: ''
})

const fetchUserData = async () => {
  if (currentUser.value === '访客') return
  try {
    const res = await axios.get(`http://127.0.0.1:5000/api/user_preference/${currentUser.value}`)
    if (res.data.preference) {
      preferenceCount.value = res.data.preference.length
    }
    
    // Fetch user reviews count - we can use an existing endpoint or add a simple one
    // For now we'll just mock or use the preference as a proxy
  } catch (e) {
    console.error(e)
  }
}

const handleUpdate = async () => {
  if (!formData.value.username) {
    message.error('称谓不可为空')
    return
  }
  
  updating.value = true
  try {
    const res = await axios.post('http://127.0.0.1:5000/api/user/update', {
      old_username: currentUser.value,
      new_username: formData.value.username,
      new_password: formData.value.password || null
    })
    
    if (res.data.status === 'success') {
      message.success('修缮成功')
      localStorage.setItem('user', formData.value.username)
      currentUser.value = formData.value.username
      formData.value.password = ''
    } else {
      message.error(res.data.message)
    }
  } catch (e) {
    message.error(e.response?.data?.message || '修缮失败')
  } finally {
    updating.value = false
  }
}

const handleLogout = () => {
  localStorage.removeItem('user')
  router.push('/login')
}

onMounted(() => {
  fetchUserData()
})
</script>

<style scoped>
.profile-container {
  min-height: 100vh;
  background: var(--gradient-bg);
  display: flex;
  flex-direction: column;
}

.profile-main {
  flex: 1;
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 40px 20px;
}

.profile-card {
  width: 100%;
  max-width: 480px;
  background: var(--paper-white);
  border-radius: var(--radius-main);
  box-shadow: 0 10px 30px rgba(0,0,0,0.1);
  overflow: hidden;
  animation: slideUp 0.5s ease-out;
}

@keyframes slideUp {
  from { transform: translateY(20px); opacity: 0; }
  to { transform: translateY(0); opacity: 1; }
}

.profile-header {
  padding: 40px 30px;
  background: linear-gradient(135deg, var(--cinnabar-red), #d44c4c);
  color: white;
  display: flex;
  align-items: center;
  gap: 20px;
}

.avatar-circle {
  width: 70px;
  height: 70px;
  background: rgba(255,255,255,0.2);
  border: 2px solid rgba(255,255,255,0.4);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 32px;
  font-family: "Noto Serif SC", serif;
  font-weight: bold;
}

.header-info h2 {
  margin: 0;
  font-family: "Noto Serif SC", serif;
  font-size: 24px;
}

.header-info p {
  margin: 5px 0 0;
  opacity: 0.8;
  font-size: 14px;
}

.profile-body {
  padding: 30px;
}

.form-section {
  padding-top: 10px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.form-item label {
  display: block;
  margin-bottom: 8px;
  font-size: 14px;
  color: var(--ink-black);
  opacity: 0.7;
}

.stats-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 15px;
  padding: 20px 0;
}

.stat-item {
  background: rgba(0,0,0,0.03);
  padding: 20px;
  border-radius: 12px;
  text-align: center;
}

.stat-value {
  font-size: 24px;
  font-weight: bold;
  color: var(--cinnabar-red);
  margin-bottom: 4px;
}

.stat-label {
  font-size: 12px;
  color: #888;
}

.profile-footer {
  padding: 0 30px 30px;
}

.divider {
  height: 1px;
  background: rgba(0,0,0,0.06);
  margin-bottom: 20px;
}

.logout-btn {
  font-weight: 500;
}
</style>
