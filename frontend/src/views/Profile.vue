<template>
  <div class="profile-container">
    <nav class="top-nav glass-card">
      <div class="nav-brand">
        <span class="logo-text">诗云</span>
        <span class="edition-badge">Zen Edition</span>
      </div>
      
      <div class="nav-actions">
        <!-- 搜索 -->
        <div class="nav-btn-card" @click="router.push('/search')" title="Search">
          <n-icon><NSearch /></n-icon>
          <span>搜索</span>
        </div>
        
        <!-- 个人万象 -->
        <div class="nav-btn-card" @click="router.push('/personal-analysis')" title="Personal Analysis">
          <n-icon><NPersonOutline /></n-icon>
          <span>个人万象</span>
        </div>
        
        <!-- 全站万象 -->
        <div class="nav-btn-card" @click="router.push('/global-analysis')" title="Global Analysis">
          <n-icon><NGlobeOutline /></n-icon>
          <span>全站万象</span>
        </div>

        <div class="divider-vertical"></div>

        <!-- User Profile -->
        <div class="user-area">
          <div v-if="currentUser !== '访客'" class="user-greeting" @click="router.push('/profile')" title="个人信息">
            <n-icon class="user-icon"><NPersonOutline /></n-icon>
            <span class="user-name">{{ currentUser }}</span>
          </div>
          <div v-else class="login-prompt" @click="router.push('/login')">
            Login
          </div>
        </div>
      </div>
    </nav>

    <main class="profile-main">
      <div class="profile-card glass-card">
        <!-- 用户信息卡片 -->
        <div class="info-card">
          <div class="avatar-large">
            {{ currentUser.charAt(0) }}
          </div>
          <div class="user-details">
            <h1 class="user-title">{{ currentUser }}</h1>
            <p class="user-subtitle">诗心未泯，墨香犹在</p>
          </div>
        </div>

        <!-- 编辑资料卡片 -->
        <div class="edit-card">
          <div class="card-header">
            <div class="card-icon-wrapper">
              <n-icon class="card-icon"><NPerson /></n-icon>
            </div>
            <h2 class="card-title">编辑资料</h2>
          </div>
          <div class="card-body">
            <p class="card-desc">修改您的称谓和口令</p>
            <div class="form-section">
              <div class="form-item">
                <label class="form-label">称谓</label>
                <n-input v-model:value="formData.username" placeholder="请输入新称谓" round size="large" />
              </div>
              <div class="form-item">
                <label class="form-label">口令</label>
                <n-input v-model:value="formData.password" type="password" show-password-on="click" placeholder="如需更改请输入新口令" round size="large" />
              </div>
              <div class="form-actions">
                <n-button type="primary" round size="large" @click="handleUpdate" :loading="updating">
                  保存修改
                </n-button>
              </div>
            </div>
          </div>
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
  NIcon, 
  useMessage 
} from 'naive-ui'
import { 
  HomeOutline as NHome,
  PersonOutline as NPerson,
  SearchOutline as NSearch,
  GlobeOutline as NGlobeOutline
} from '@vicons/ionicons5'
import axios from 'axios'

const router = useRouter()
const message = useMessage()
const currentUser = ref(localStorage.getItem('user') || '访客')
const updating = ref(false)

const formData = ref({
  username: currentUser.value,
  password: ''
})

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
      message.success('保存成功')
      localStorage.setItem('user', formData.value.username)
      currentUser.value = formData.value.username
      formData.value.password = ''
    } else {
      message.error(res.data.message)
    }
  } catch (e) {
    message.error(e.response?.data?.message || '保存失败')
  } finally {
    updating.value = false
  }
}

onMounted(() => {
  // 页面加载完成后的初始化
})
</script>

<style scoped>
.profile-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #f8fafc 0%, #e0e7ff 100%);
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
  max-width: 900px;
  background: var(--paper-white);
  border-radius: var(--radius-main);
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.1);
  overflow: hidden;
  animation: slideUp 0.6s ease-out;
  border: 1px solid rgba(255, 255, 255, 0.9);
  display: flex;
  flex-direction: column;
  gap: 30px;
  padding: 40px;
}

@keyframes slideUp {
  from { 
    transform: translateY(40px); 
    opacity: 0; 
  }
  to { 
    transform: translateY(0); 
    opacity: 1; 
  }
}

.info-card {
  display: flex;
  align-items: center;
  gap: 30px;
  padding: 35px;
  background: linear-gradient(135deg, var(--cinnabar-red) 0%, #d44c4c 100%);
  border-radius: 20px;
  box-shadow: 0 8px 24px rgba(207, 63, 53, 0.3);
}

.avatar-large {
  width: 100px;
  height: 100px;
  background: rgba(255, 255, 255, 0.3);
  border: 4px solid rgba(255, 255, 255, 0.5);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 48px;
  font-family: "Noto Serif SC", serif;
  font-weight: 700;
  color: white;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.25);
  flex-shrink: 0;
}

.user-details {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.user-title {
  margin: 0;
  font-family: "Noto Serif SC", serif;
  font-size: 36px;
  font-weight: 700;
  color: white;
  letter-spacing: 0.1em;
  text-shadow: 0 3px 8px rgba(0, 0, 0, 0.2);
}

.user-subtitle {
  margin: 0;
  font-size: 16px;
  color: rgba(255, 255, 255, 0.9);
  font-family: "Noto Serif SC", serif;
  font-style: italic;
  letter-spacing: 0.15em;
}



.edit-card {
  background: rgba(255, 255, 255, 0.95);
  border-radius: 20px;
  padding: 0;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  border: 1px solid rgba(0, 0, 0, 0.1);
  transition: all 0.3s var(--ease-smooth);
}

.edit-card:hover {
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.12);
  transform: translateY(-4px);
}

.card-header {
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 30px;
  background: linear-gradient(135deg, rgba(207, 63, 53, 0.05) 0%, rgba(207, 63, 53, 0.02) 100%);
  border-radius: 20px 20px 0 0;
  border-bottom: 1px solid rgba(0, 0, 0, 0.08);
}

.card-icon-wrapper {
  width: 64px;
  height: 64px;
  background: linear-gradient(135deg, var(--cinnabar-red) 0%, #d44c4c 100%);
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 12px rgba(207, 63, 53, 0.25);
}

.card-icon {
  font-size: 32px;
  color: white;
}

.card-title {
  margin: 0;
  font-family: "Noto Serif SC", serif;
  font-size: 24px;
  font-weight: 600;
  color: var(--text-primary);
  letter-spacing: 0.08em;
}

.card-body {
  padding: 35px;
}

.card-desc {
  margin: 0 0 20px;
  font-size: 15px;
  color: var(--text-tertiary);
  line-height: 1.6;
}

.form-section {
  display: flex;
  flex-direction: column;
  gap: 25px;
}

.form-item {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.form-label {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-secondary);
  letter-spacing: 0.05em;
  text-transform: uppercase;
}

.form-item :deep(.n-input) {
  height: 54px;
  font-size: 16px;
  border-radius: 14px;
  transition: all 0.3s var(--ease-smooth);
  border: 1px solid rgba(0, 0, 0, 0.15);
}

.form-item :deep(.n-input:hover) {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12);
  border-color: rgba(207, 63, 53, 0.5);
  transform: translateY(-2px);
}

.form-item :deep(.n-input:focus) {
  box-shadow: 0 0 0 4px rgba(207, 63, 53, 0.25);
  border-color: var(--cinnabar-red);
  transform: translateY(-2px);
}

.form-actions {
  margin-top: 10px;
}

.form-actions :deep(.n-button) {
  height: 54px;
  font-size: 16px;
  font-weight: 600;
  letter-spacing: 0.12em;
  border-radius: 14px;
  transition: all 0.3s var(--ease-smooth);
  background: linear-gradient(135deg, var(--cinnabar-red) 0%, #d44c4c 100%);
  border: none;
}

.form-actions :deep(.n-button:hover) {
  transform: translateY(-3px);
  box-shadow: 0 8px 24px rgba(207, 63, 53, 0.4);
}

.form-actions :deep(.n-button:active) {
  transform: translateY(0);
}



@media (max-width: 768px) {
  .profile-main {
    padding: 20px 15px;
  }
  
  .profile-card {
    max-width: 100%;
    padding: 25px;
  }
  
  .info-card {
    flex-direction: column;
    text-align: center;
    gap: 20px;
    padding: 30px;
  }
  
  .avatar-large {
    width: 80px;
    height: 80px;
    font-size: 40px;
  }
  
  .user-title {
    font-size: 28px;
  }
  

  
  .user-details {
    align-items: center;
  }
  
  .card-header {
    padding: 25px;
  }
  
  .card-body {
    padding: 30px;
  }
  
  .form-item :deep(.n-input) {
    height: 48px;
    font-size: 15px;
  }
  
  .form-actions :deep(.n-button) {
    height: 48px;
    font-size: 15px;
  }
}

@media (max-width: 480px) {
  .profile-card {
    padding: 20px;
  }
  
  .info-card {
    padding: 25px;
  }
  
  .card-header {
    padding: 20px;
  }
  
  .card-body {
    padding: 25px;
  }
  
  .form-section {
    gap: 20px;
  }
}
</style>
