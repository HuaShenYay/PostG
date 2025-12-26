<template>
  <div class="login-container">
    <div class="center-box fade-in">
      <h1 class="title vertical-text">诗云</h1>
      <div class="stamp">阅</div>
      
      <div class="form-area">
        <div class="input-group">
          <input v-model="username" type="text" placeholder="称谓 (User ID)" class="ink-input" @keyup.enter="handleLogin" />
        </div>
        <div class="input-group">
          <input v-model="password" type="password" placeholder="口令 (Password)" class="ink-input" @keyup.enter="handleLogin" />
        </div>
        
        <button @click="handleLogin" :disabled="loading" class="ink-btn primary" style="width: 100%; margin-top: 20px;">
          {{ loading ? '入梦中...' : '入 梦' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'

const router = useRouter()
const username = ref('')
const password = ref('')
const loading = ref(false)

const handleLogin = async () => {
  if (!username.value || !password.value) return alert('请填写完整信息');
  
  loading.value = true
  try {
    const res = await axios.post('http://127.0.0.1:5000/api/login', {
      username: username.value,
      password: password.value
    })
    
    if (res.data.status === 'success') {
      localStorage.setItem('user', username.value);
      router.push('/');
    } else {
      alert(res.data.message);
    }
  } catch (e) {
    alert(e.response?.data?.message || '无法连接到诗云世界');
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-container {
  height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background-image: radial-gradient(circle at 50% 50%, #fdfbf7 0%, #f0ece2 100%);
}

.center-box {
  text-align: center;
  position: relative;
  padding: 60px;
}

.title {
  font-size: 4rem;
  height: 200px;
  display: inline-block;
  margin-bottom: 20px;
  color: var(--ink-black);
  /* 竖排 */
  writing-mode: vertical-rl;
  text-orientation: upright;
}

.stamp {
  position: absolute;
  top: 40px;
  right: 40px;
  width: 40px;
  height: 40px;
  background: var(--seal-red);
  color: white;
  display: flex;
  justify-content: center;
  align-items: center;
  border-radius: 4px;
  font-size: 1.2rem;
  box-shadow: 2px 2px 4px rgba(0,0,0,0.2);
}

.form-area {
  margin-top: 40px;
  width: 300px;
}

.input-group {
  margin-bottom: 20px;
}

.ink-input {
  width: 100%;
  text-align: center;
}
</style>
