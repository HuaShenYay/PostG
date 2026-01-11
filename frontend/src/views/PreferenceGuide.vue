<template>
  <div class="guide-container fade-in">
    <div class="background-animation">
      <div class="floating-circle" v-for="i in 4" :key="i" :style="{ 
        '--delay': i * 0.6 + 's',
        '--size': (Math.random() * 150 + 80) + 'px',
        '--x': Math.random() * 100 + '%',
        '--y': Math.random() * 100 + '%'
      }"></div>
    </div>
    
    <el-card class="guide-card glass-card" shadow="never">
      <div class="editorial-header">
        <span class="date-stamp">公元二零二五</span>
        <h1 class="title">诗心初探</h1>
        <div class="decorative-line"></div>
        <span class="tagline">请选择您偏好的诗歌主题 · 我们将为您量身推荐</span>
      </div>

      <div v-if="loading" class="loading-state">
        <el-icon class="is-loading" :size="40"><Loading /></el-icon>
        <p>正在加载主题...</p>
      </div>

      <div v-else class="topics-grid">
        <div 
          v-for="(keywords, topicId) in topics" 
          :key="topicId"
          class="topic-card"
          :class="{ 'selected': selectedTopics.includes(topicId) }"
          @click="toggleTopic(topicId)"
        >
          <div class="topic-number">主题 {{ topicId + 1 }}</div>
          <div class="topic-keywords">
            <span 
              v-for="(keyword, index) in keywords.slice(0, 5)" 
              :key="index"
              class="keyword-tag"
            >
              {{ keyword }}
            </span>
          </div>
          <div class="select-indicator" v-if="selectedTopics.includes(topicId)">
            <el-icon><Check /></el-icon>
          </div>
        </div>
      </div>

      <div class="guide-actions">
        <el-button 
          type="primary" 
          size="large" 
          :disabled="selectedTopics.length === 0"
          :loading="submitting"
          @click="handleSavePreferences"
          class="save-btn"
        >
          {{ submitting ? '保存中...' : '完成引导' }}
        </el-button>
        <el-button 
          type="default" 
          size="large" 
          @click="handleSkip"
          class="skip-btn"
        >
          跳过
        </el-button>
        <p class="hint-text">至少选择一个主题，或点击跳过直接进入主页</p>
      </div>

      <div class="footer-note">
        <p>荐诗 · 现代语境下的古典回归</p>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Loading, Check } from '@element-plus/icons-vue'
import axios from 'axios'

const router = useRouter()
const route = useRoute()
const loading = ref(true)
const submitting = ref(false)
const topics = ref({})
const selectedTopics = ref([])
const username = ref('')

onMounted(async () => {
  username.value = route.query.username || localStorage.getItem('user')
  if (!username.value) {
    ElMessage.warning('请先登录')
    router.push('/login')
    return
  }
  
  await loadTopics()
})

const loadTopics = async () => {
  try {
    const res = await axios.get('http://127.0.0.1:5000/api/topics')
    topics.value = res.data
  } catch (e) {
    ElMessage.error('加载主题失败')
  } finally {
    loading.value = false
  }
}

const toggleTopic = (topicId) => {
  const index = selectedTopics.value.indexOf(topicId)
  if (index > -1) {
    selectedTopics.value.splice(index, 1)
  } else {
    if (selectedTopics.value.length < 5) {
      selectedTopics.value.push(topicId)
    } else {
      ElMessage.warning('最多选择5个主题')
    }
  }
}

const handleSavePreferences = async () => {
  if (selectedTopics.value.length === 0) {
    ElMessage.warning('请至少选择一个主题')
    return
  }
  
  submitting.value = true
  try {
    const res = await axios.post('http://127.0.0.1:5000/api/save_initial_preferences', {
      username: username.value,
      selected_topics: selectedTopics.value
    })
    
    if (res.data.status === 'success') {
      ElMessage.success('偏好设置成功，即将进入主页')
      setTimeout(() => {
        router.push('/')
      }, 1500)
    } else {
      ElMessage.error(res.data.message)
    }
  } catch (e) {
    ElMessage.error(e.response?.data?.message || '保存失败')
  } finally {
    submitting.value = false
  }
}

const handleSkip = () => {
  ElMessage.info('已跳过偏好设置，系统将为您推荐多样化的诗歌')
  setTimeout(() => {
    router.push('/')
  }, 1000)
}
</script>

<style scoped>
.guide-container {
  min-height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  position: relative;
  overflow: hidden;
  background: var(--gradient-warm);
  background-attachment: fixed;
  padding: 40px 20px;
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
  background: radial-gradient(circle at 30% 30%, rgba(166, 27, 27, 0.08), transparent);
  filter: blur(40px);
  animation: float-circle 25s ease-in-out infinite;
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
    transform: translate(-50%, -50%) translate(20px, -20px) scale(1.1);
  }
  50% {
    transform: translate(-50%, -50%) translate(-15px, 15px) scale(0.9);
  }
  75% {
    transform: translate(-50%, -50%) translate(-20px, -15px) scale(1.05);
  }
}

.guide-card {
  width: 100%;
  max-width: 900px;
  border: none !important;
  background: rgba(255, 255, 255, 0.85) !important;
  backdrop-filter: blur(30px);
  -webkit-backdrop-filter: blur(30px);
  position: relative;
  z-index: 1;
}

.guide-card :deep(.el-card__body) {
  padding: 60px 50px;
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
  font-size: 56PX;
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
  .title { font-size: 40PX; }
}

.tagline {
  font-size: 12PX;
  letter-spacing: 0.2em;
  color: #999;
  margin-top: 15px;
  display: block;
  text-transform: uppercase;
}

.loading-state {
  text-align: center;
  padding: 60px 0;
  color: #999;
}

.loading-state p {
  margin-top: 20px;
  font-size: 14PX;
}

.topics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  gap: 20px;
  margin-bottom: 40px;
}

@media (max-width: 600px) {
  .topics-grid {
    grid-template-columns: 1fr;
  }
}

.topic-card {
  border: 2px solid rgba(0, 0, 0, 0.08);
  border-radius: 16px;
  padding: 24px;
  cursor: pointer;
  transition: var(--transition-smooth);
  position: relative;
  background: rgba(255, 255, 255, 0.6);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
}

.topic-card:hover {
  border-color: var(--accent-red);
  transform: translateY(-4px);
  box-shadow: var(--modern-shadow);
  background: rgba(255, 255, 255, 0.9);
}

.topic-card.selected {
  border-color: var(--accent-red);
  background: linear-gradient(135deg, rgba(166, 27, 27, 0.05) 0%, rgba(255, 255, 255, 0.9) 100%);
  box-shadow: 0 4px 16px rgba(166, 27, 27, 0.15);
}

.topic-number {
  font-size: 14PX;
  color: #999;
  margin-bottom: 16px;
  font-weight: 300;
}

.topic-keywords {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.keyword-tag {
  font-size: 13PX;
  color: var(--modern-black);
  background: rgba(0, 0, 0, 0.04);
  padding: 6px 12px;
  border-radius: 20px;
  transition: all 0.3s ease;
}

.topic-card:hover .keyword-tag,
.topic-card.selected .keyword-tag {
  background: rgba(166, 27, 27, 0.1);
  color: var(--accent-red);
}

.select-indicator {
  position: absolute;
  top: 16px;
  right: 16px;
  width: 28px;
  height: 28px;
  background: var(--accent-red);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  box-shadow: 0 4px 12px rgba(166, 27, 27, 0.3);
}

.guide-actions {
  text-align: center;
  margin-top: 40px;
}

.save-btn {
  width: 100%;
  max-width: 300px;
  background: linear-gradient(135deg, var(--accent-red) 0%, var(--accent-red-dark) 100%);
  border-color: var(--accent-red);
  font-size: 14PX;
  letter-spacing: 0.4em;
  height: 52px;
  font-weight: 300;
  text-indent: 0.4em;
  transition: var(--transition-bounce);
  border-radius: 12px !important;
  box-shadow: 0 4px 16px rgba(166, 27, 27, 0.3) !important;
}

.save-btn:hover:not(:disabled) {
  background: linear-gradient(135deg, var(--accent-red-light) 0%, var(--accent-red) 100%);
  box-shadow: 0 8px 24px rgba(166, 27, 27, 0.4);
  transform: translateY(-3px);
}

.save-btn:active:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(166, 27, 27, 0.3);
}

.save-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.skip-btn {
  width: 100%;
  max-width: 300px;
  margin-top: 16px;
  background: transparent;
  border-color: rgba(0, 0, 0, 0.1);
  color: #999;
  font-size: 14PX;
  letter-spacing: 0.4em;
  height: 52px;
  font-weight: 300;
  text-indent: 0.4em;
  transition: var(--transition-smooth);
  border-radius: 12px !important;
}

.skip-btn:hover {
  border-color: #999;
  color: var(--modern-black);
  background: rgba(0, 0, 0, 0.02);
}

.hint-text {
  font-size: 12PX;
  color: #999;
  margin-top: 16px;
  letter-spacing: 0.1em;
}

.footer-note {
  text-align: center;
  margin-top: 60px;
  opacity: 0.3;
}

.footer-note p {
  font-size: 11PX;
  letter-spacing: 0.4em;
  color: var(--modern-black);
  font-weight: 200;
}
</style>