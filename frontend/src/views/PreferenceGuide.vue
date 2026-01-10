<template>
  <div class="guide-container fade-in">
    <el-card class="guide-card" shadow="never">
      <div class="editorial-header">
        <span class="date-stamp">公元二零二五</span>
        <h1 class="title">诗心初探</h1>
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
  background-color: var(--stone-white);
  padding: 40px 20px;
}

.guide-card {
  width: 100%;
  max-width: 900px;
  border: none;
  background: transparent;
}

.guide-card :deep(.el-card__body) {
  padding: 60px 50px;
}

.editorial-header {
  text-align: center;
  margin-bottom: 60px;
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
  font-size: 56PX;
  font-weight: 300;
  margin: 0;
  letter-spacing: 0.15em;
  color: var(--modern-black);
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
  border: 2px solid #e0e0e0;
  border-radius: 12px;
  padding: 24px;
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;
  background: #fff;
}

.topic-card:hover {
  border-color: var(--accent-red);
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(166, 27, 27, 0.1);
}

.topic-card.selected {
  border-color: var(--accent-red);
  background: linear-gradient(135deg, #fff5f5 0%, #fff 100%);
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
  background: #f5f5f5;
  padding: 6px 12px;
  border-radius: 20px;
  transition: all 0.3s ease;
}

.topic-card:hover .keyword-tag,
.topic-card.selected .keyword-tag {
  background: rgba(166, 27, 27, 0.08);
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
}

.guide-actions {
  text-align: center;
  margin-top: 40px;
}

.save-btn {
  width: 100%;
  max-width: 300px;
  background: var(--accent-red);
  border-color: var(--accent-red);
  font-size: 14PX;
  letter-spacing: 0.4em;
  height: 52px;
  font-weight: 300;
  text-indent: 0.4em;
  transition: all 0.5s cubic-bezier(0.16, 1, 0.3, 1);
}

.save-btn:hover:not(:disabled) {
  background: #c52d2d;
  border-color: #c52d2d;
  transform: translateY(-2px);
  box-shadow: 0 5px 15px rgba(166, 27, 27, 0.2);
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
  border-color: #e0e0e0;
  color: #999;
  font-size: 14PX;
  letter-spacing: 0.4em;
  height: 52px;
  font-weight: 300;
  text-indent: 0.4em;
  transition: all 0.3s ease;
}

.skip-btn:hover {
  border-color: #999;
  color: var(--modern-black);
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