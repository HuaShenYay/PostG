<template>
  <div class="login-container">
    <el-card class="login-card" shadow="never">
      <div class="editorial-header">
        <span class="date-stamp">公元二零二五</span>
        <h1 class="title">诗云</h1>
        <span class="tagline">基于 LDA-CF 的诗歌推荐系统</span>
      </div>
      
      <el-form :model="form" @submit.prevent="handleLogin" class="login-form">
        <el-form-item>
          <el-input 
            v-model="form.username" 
            placeholder="称 谓" 
            size="large"
            :prefix-icon="User"
          />
        </el-form-item>
        <el-form-item>
          <el-input 
            v-model="form.password" 
            type="password" 
            placeholder="口 令" 
            size="large"
            :prefix-icon="Lock"
            show-password
          />
        </el-form-item>
        
        <el-form-item>
          <el-button 
            type="primary" 
            size="large" 
            :loading="loading"
            @click="handleLogin"
            class="login-btn"
          >
            {{ loading ? '入梦中...' : '入 梦' }}
          </el-button>
        </el-form-item>
      </el-form>

      <div class="footer-note">
        <p>诗云 · 现代语境下的古典回归</p>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Lock } from '@element-plus/icons-vue'
import axios from 'axios'

const router = useRouter()
const loading = ref(false)
const form = reactive({
  username: '',
  password: ''
})

const handleLogin = async () => {
  if (!form.username || !form.password) {
    ElMessage.warning('请完整填写')
    return
  }
  
  loading.value = true
  try {
    const res = await axios.post('http://127.0.0.1:5000/api/login', {
      username: form.username,
      password: form.password
    })
    
    if (res.data.status === 'success') {
      localStorage.setItem('user', form.username)
      ElMessage.success('入梦成功')
      router.push('/')
    } else {
      ElMessage.error(res.data.message)
    }
  } catch (e) {
    ElMessage.error(e.response?.data?.message || '连接失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background-color: var(--stone-white);
  padding: 40px;
}

.login-card {
  width: 100%;
  max-width: 440px;
  border: none;
  background: transparent;
}

.login-card :deep(.el-card__body) {
  padding: 60px 40px;
}

.editorial-header {
  text-align: center;
  margin-bottom: 80px;
}

.date-stamp {
  font-size: 14PX;
  letter-spacing: 0.5em;
  color: var(--accent-red);
  display: block;
  margin-bottom: 20px;
  font-weight: 300;
}

.title {
  font-family: "Noto Serif SC", serif;
  font-size: 64PX;
  font-weight: 300;
  margin: 0;
  letter-spacing: 0.15em;
  color: var(--modern-black);
}

@media (max-width: 768px) {
  .title { font-size: 48PX; }
}

.tagline {
  font-size: 12PX;
  letter-spacing: 0.2em;
  color: #999;
  margin-top: 15px;
  display: block;
  text-transform: uppercase;
}

.login-form {
  margin-top: 60px;
}

.login-form :deep(.el-input__wrapper) {
  border-radius: 0;
  box-shadow: none;
  border-bottom: 0.5px solid var(--line-gray);
  background: transparent;
  padding: 12px 0;
}

.login-form :deep(.el-input__wrapper:hover),
.login-form :deep(.el-input__wrapper.is-focus) {
  box-shadow: none;
  border-bottom-color: var(--accent-red); /* 改为主题色 */
}

.login-form :deep(.el-input__inner) {
  text-align: center;
  font-size: 16PX;
  font-weight: 300;
  letter-spacing: 0.1em;
}

.login-btn {
  width: 100%;
  margin-top: 40px;
  border-radius: 0;
  background: var(--accent-red); /* 改为主题色 */
  border-color: var(--accent-red);
  font-size: 14PX;
  letter-spacing: 0.4em;
  height: 52px;
  font-weight: 300;
  text-indent: 0.4em;
  transition: all 0.5s cubic-bezier(0.16, 1, 0.3, 1);
}

.login-btn:hover {
  background: #c52d2d; /* 稍微淡化的主题色 */
  border-color: #c52d2d;
  transform: translateY(-2px);
  box-shadow: 0 5px 15px rgba(166, 27, 27, 0.2);
}

.footer-note {
  text-align: center;
  margin-top: 100px;
  opacity: 0.3;
}

.footer-note p {
  font-size: 11PX;
  letter-spacing: 0.4em;
  color: var(--modern-black);
  font-weight: 200;
}
</style>
