<script setup>
import { ref, onMounted } from 'vue'
import NeonButton from '@/shared/components/NeonButton.vue'
import { getServerSettings, saveServerSettings } from '@/shared/utils/settings.js'
import { Settings, Save } from 'lucide-vue-next'

const emit = defineEmits(['navigate'])

const showConfig = ref(false)
const serverUrl = ref('')
const saved = ref(false)

onMounted(async () => {
  const s = await getServerSettings()
  serverUrl.value = s.serverUrl || ''
})

async function handleSave() {
  await saveServerSettings({ serverUrl: serverUrl.value })
  saved.value = true
  setTimeout(() => saved.value = false, 2000)
}

const goToLogin = () => {
  emit('navigate', 'login')
}
</script>

<template>
  <div class="landing-view">
    <div class="hero-section">
      <h1 class="hero-title">
        <span class="title-main">Vibe Workflow</span>
        <span class="title-sub">Copilot</span>
      </h1>

      <p class="hero-desc">
        😎 FastFlow helps non-technical creators
        <br>
        <span class="sub-desc">automate tasks with AI</span>
      </p>

      <div class="config-area">
        <button class="config-toggle" @click="showConfig = !showConfig">
          <Settings size="14" />
          {{ showConfig ? '收起' : '配置服务端地址' }}
        </button>
        <div v-if="showConfig" class="config-panel">
          <input v-model="serverUrl" type="text" placeholder="http://172.19.186.130:8969" class="url-input" />
          <button class="save-btn" @click="handleSave">
            <Save size="13" />
            {{ saved ? '已保存' : '保存' }}
          </button>
        </div>
      </div>

      <div class="cta-group">
        <NeonButton large @click="goToLogin">登录</NeonButton>
      </div>
    </div>
  </div>
</template>

<style scoped>
.landing-view {
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 20px;
  position: relative;
  overflow: hidden;
}

.hero-title {
  font-family: var(--font-mono);
  font-size: 32px;
  margin-bottom: 16px;
  line-height: 1.1;
  letter-spacing: -0.5px;
}

.title-main {
  color: var(--text-primary);
  display: block;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.title-sub {
  color: var(--accent-neon);
  font-size: 32px;
  display: block;
  font-weight: 300;
  text-transform: uppercase;
  letter-spacing: 4px;
  text-shadow: 0 0 10px color-mix(in srgb, var(--accent-neon) 35%, transparent);
}

.hero-desc {
  font-size: 14px;
  color: var(--text-secondary);
  margin-bottom: 20px;
  line-height: 1.6;
  font-weight: 400;
}

.sub-desc {
  font-size: 14px;
  color: var(--text-primary);
  font-weight: 500;
}

/* Config */
.config-area {
  width: 100%;
  max-width: 280px;
  margin: 0 auto 20px;
}

.config-toggle {
  display: flex;
  align-items: center;
  gap: 6px;
  width: 100%;
  padding: 8px 12px;
  background: var(--bg-surface);
  border: 1px solid var(--border-subtle);
  border-radius: 8px;
  color: var(--text-secondary);
  font-size: 12px;
  cursor: pointer;
  transition: color 0.2s;
}

.config-toggle:hover {
  color: var(--text-primary);
}

.config-panel {
  margin-top: 8px;
  padding: 12px;
  background: var(--bg-surface);
  border: 1px solid var(--border-subtle);
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.url-input {
  padding: 8px 10px;
  background: var(--bg-app);
  border: 1px solid var(--border-subtle);
  border-radius: 6px;
  color: var(--text-primary);
  font-size: 12px;
  font-family: var(--font-mono);
  outline: none;
  transition: border-color 0.2s;
}

.url-input:focus {
  border-color: var(--accent-neon);
}

.save-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  padding: 6px 14px;
  background: var(--accent-neon);
  color: #000;
  border: none;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: opacity 0.2s;
}

.save-btn:hover {
  opacity: 0.85;
}

.cta-group {
  margin-top: 0;
}
</style>
