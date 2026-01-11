<template>
  <div class="login-container">
    <div class="background-animation">
      <div class="floating-circle" v-for="i in 6" :key="i" :style="{ 
        '--delay': i * 0.5 + 's',
        '--size': (Math.random() * 200 + 100) + 'px',
        '--x': Math.random() * 100 + '%',
        '--y': Math.random() * 100 + '%'
      }"></div>
    </div>
    
    <div class="login-content fade-in">
      <el-card class="login-card glass-card" shadow="never">
        <div class="editorial-header">
          <span class="date-stamp">公元二零二五</span>
          <h1 class="title">诗云</h1>
          <div class="decorative-line"></div>
        </div>
        
        <el-form :model="form" @submit.prevent="handleLogin" class="login-form">
          <el-form-item>
            <el-input 
              v-model="form.username" 
              placeholder="称 谓" 
              size="large"
              :prefix-icon="User"
              class="modern-input"
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
              class="modern-input"
            />
          </el-form-item>
          
          <el-form-item>
            <el-button 
              type="primary" 
              size="large" 
              :loading="loading"
              @click="handleLogin"
              class="login-btn modern-btn"
            >
              {{ loading ? '登录中...' : '登 录' }}
            </el-button>
          </el-form-item>
        </el-form>

        <div class="actions">
          <router-link to="/register" class="register-link">尚无称谓？前往注册</router-link>
        </div>

        <div class="footer-note">
          <p>荐诗 · 现代语境下的古典回归</p>
        </div>
      </el-card>
    </div>
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
      ElMessage.success('登录成功')
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
  position: relative;
  overflow: hidden;
}

.background-animation {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 0;
  overflow: hidden;
}

.floating-circle {
  position: absolute;
  width: var(--size);
  height: var(--size);
  border-radius: 50%;
  background: radial-gradient(circle at 30% 30%, rgba(166, 27, 27, 0.1), transparent);
  filter: blur(40px);
  animation: float-circle 20s ease-in-out infinite;
  animation-delay: var(--delay);
  left: var(--x);
  top: var(--y);
  transform: translate(-50%, -50%);
}

@keyframes float-circle {
  0%, 100% {
    transform: translate(-50%, -50%) translate(0, 0) scale(1);
  }
  25% {
    transform: translate(-50%, -50%) translate(30px, -30px) scale(1.1);
  }
  50% {
    transform: translate(-50%, -50%) translate(-20px, 20px) scale(0.9);
  }
  75% {
    transform: translate(-50%, -50%) translate(-30px, -20px) scale(1.05);
  }
}

.login-content {
  position: relative;
  z-index: 1;
  width: 100%;
  padding: 40px;
}

.login-card {
  width: 100%;
  max-width: 440px;
  margin: 0 auto;
  border: none !important;
  background: rgba(255, 255, 255, 0.8) !important;
  backdrop-filter: blur(30px);
  -webkit-backdrop-filter: blur(30px);
}

.login-card :deep(.el-card__body) {
  padding: 60px 40px;
}

.editorial-header {
  text-align: center;
  margin-bottom: 60px;
  position: relative;
}

.date-stamp {
  font-size: 14PX;
  letter-spacing: 0.5em;
  color: var(--accent-red);
  display: block;
  margin-bottom: 20px;
  font-weight: 300;
  opacity: 0.8;
}

.title {
  font-family: "Noto Serif SC", serif;
  font-size: 64PX;
  font-weight: 300;
  margin: 0;
  letter-spacing: 0.15em;
  color: var(--modern-black);
  background: linear-gradient(135deg, var(--modern-black) 0%, var(--accent-red) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.decorative-line {
  width: 60px;
  height: 2px;
  background: linear-gradient(90deg, transparent, var(--accent-red), transparent);
  margin: 20px auto 0;
  border-radius: 2px;
}

@media (max-width: 768px) {
  .title { font-size: 48PX; }
}

.login-form {
  margin-top: 40px;
}

.login-form :deep(.el-input__wrapper) {
  background: rgba(255, 255, 255, 0.5) !important;
  border: 1px solid rgba(0, 0, 0, 0.08) !important;
  padding: 14px 20px !important;
  border-radius: 12px !important;
  transition: var(--transition-smooth);
}

.login-form :deep(.el-input__wrapper:hover) {
  background: rgba(255, 255, 255, 0.8) !important;
  border-color: rgba(166, 27, 27, 0.3) !important;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.login-form :deep(.el-input__wrapper.is-focus) {
  background: white !important;
  border-color: var(--accent-red) !important;
  box-shadow: 0 0 0 4px rgba(166, 27, 27, 0.1), 0 4px 12px rgba(0, 0, 0, 0.08) !important;
  transform: translateY(-2px);
}

.login-form :deep(.el-input__inner) {
  text-align: center;
  font-size: 16PX;
  font-weight: 300;
  letter-spacing: 0.1em;
  color: var(--modern-black);
}

.login-form :deep(.el-input__inner::placeholder) {
  color: rgba(0, 0, 0, 0.3);
}

.login-btn {
  width: 100%;
  margin-top: 30px;
  font-size: 14PX;
  letter-spacing: 0.4em;
  height: 52px;
  font-weight: 300;
  text-indent: 0.4em;
  border-radius: 12px !important;
  background: linear-gradient(135deg, var(--accent-red) 0%, var(--accent-red-dark) 100%) !important;
  border: none !important;
  box-shadow: 0 4px 16px rgba(166, 27, 27, 0.3) !important;
  transition: var(--transition-bounce);
}

.login-btn:hover {
  background: linear-gradient(135deg, var(--accent-red-light) 0%, var(--accent-red) 100%) !important;
  box-shadow: 0 8px 24px rgba(166, 27, 27, 0.4) !important;
  transform: translateY(-3px);
}

.login-btn:active {
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(166, 27, 27, 0.3) !important;
}

.actions {
  text-align: center;
  margin-top: 25px;
}

.register-link {
  font-size: 13PX;
  color: #888;
  text-decoration: none;
  letter-spacing: 0.1em;
  transition: all 0.3s;
  position: relative;
  padding: 5px 10px;
}

.register-link::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 50%;
  width: 0;
  height: 1px;
  background: var(--accent-red);
  transition: all 0.3s;
  transform: translateX(-50%);
}

.register-link:hover {
  color: var(--accent-red);
}

.register-link:hover::after {
  width: 100%;
}

.footer-note {
  text-align: center;
  margin-top: 50px;
  opacity: 0.3;
}

.footer-note p {
  font-size: 11PX;
  letter-spacing: 0.4em;
  color: var(--modern-black);
  font-weight: 200;
}
</style>
