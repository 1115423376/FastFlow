<script setup>
import { computed, ref, onMounted } from 'vue'
import { authService } from '@/shared/services/auth.js'
import { useTheme } from '@/shared/composables/useTheme.js'
import { getExtensionDisplayVersion } from '@/shared/utils/extension-meta.js'
import { getServerSettings, saveServerSettings } from '@/shared/utils/settings.js'
import { 
  Moon, Sun, Monitor, 
  ChevronRight, Shield, Info, LogOut, Server, Save
} from 'lucide-vue-next'

const props = defineProps({
  user: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['logout'])
const { theme, options: themeOptions, setTheme } = useTheme()

const serverUrl = ref('')
const saved = ref(false)

onMounted(async () => {
  const s = await getServerSettings()
  serverUrl.value = s.serverUrl || ''
})

async function handleSaveSettings() {
  await saveServerSettings({ serverUrl: serverUrl.value })
  saved.value = true
  setTimeout(() => saved.value = false, 2000)
}

// 获取头像URL
const avatarUrl = computed(() => props.user.avatar || null)

// 获取显示名称
const displayName = computed(() => props.user.nickname || props.user.username || 'User')

// 获取首字母
const firstLetter = computed(() => {
  const name = displayName.value
  return name ? name.charAt(0).toUpperCase() : 'U'
})

const extensionVersion = computed(() => getExtensionDisplayVersion())

const handleLogout = () => {
  authService.logout()
  emit('logout')
}
</script>

<template>
  <div class="dashboard-view">
    <!-- 用户概览卡片 -->
    <div class="profile-card">
      <div class="avatar-container">
        <img v-if="avatarUrl" :src="avatarUrl" class="avatar-img" alt="User Avatar" />
        <div v-else class="avatar-placeholder">{{ firstLetter }}</div>
      </div>
      
      <div class="user-info">
        <h3 class="username">{{ displayName }}</h3>
        <p class="email">{{ user.email }}</p>
      </div>
    </div>

    <!-- 设置列表组 -->
    <div class="settings-group">
      <h4 class="group-title">通用设置</h4>
      
      <!-- 主题设置 -->
      <div class="setting-item theme-item">
        <div class="setting-left">
          <div class="icon-box">
            <Moon v-if="theme === 'dark'" size="16" />
            <Sun v-else-if="theme === 'light'" size="16" />
            <Monitor v-else size="16" />
          </div>
          <span class="label">外观主题</span>
        </div>
        
        <div class="theme-switcher">
          <button 
            v-for="opt in themeOptions" 
            :key="opt.value"
            class="theme-btn"
            :class="{ active: theme === opt.value }"
            @click="setTheme(opt.value)"
            :title="opt.label"
          >
            <component 
              :is="opt.value === 'dark' ? Moon : (opt.value === 'light' ? Sun : Monitor)" 
              size="14" 
            />
          </button>
        </div>
      </div>

      <!-- 账号安全 (占位) -->
      <div class="setting-item clickable">
        <div class="setting-left">
          <div class="icon-box"><Shield size="16" /></div>
          <span class="label">账号安全</span>
        </div>
        <ChevronRight size="16" class="arrow" />
      </div>

      <!-- 关于版本 -->
      <div class="setting-item">
        <div class="setting-left">
          <div class="icon-box"><Info size="16" /></div>
          <span class="label">关于版本</span>
        </div>
        <span class="value-tag">{{ extensionVersion }}</span>
      </div>
    </div>

    <!-- 服务端地址配置 -->
    <div class="settings-group">
      <h4 class="group-title">服务端地址</h4>
      <div class="server-config">
        <input v-model="serverUrl" type="text" placeholder="http://172.19.186.130:8969" class="url-input" />
        <button class="save-btn" @click="handleSaveSettings">
          <Save size="14" />
          {{ saved ? '已保存' : '保存地址' }}
        </button>
      </div>
    </div>

    <!-- 底部操作 -->
    <div class="action-area">
      <button class="logout-btn-text" @click="handleLogout">
        <LogOut size="16" />
        退出登录
      </button>
    </div>
  </div>
</template>

<style scoped>
.dashboard-view {
  padding: 20px;
  height: 100%;
  display: flex;
  flex-direction: column;
  background-color: var(--bg-app);
  color: var(--text-primary);
  transition: background-color 0.3s, color 0.3s;
}

/* Profile Card */
.profile-card {
  display: flex;
  align-items: center;
  padding: 16px;
  background: var(--bg-surface);
  border: 1px solid var(--border-subtle);
  border-radius: 12px;
  margin-bottom: 24px;
  gap: 16px;
}

.avatar-container {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  border: 2px solid var(--accent-neon);
  overflow: hidden;
  background: var(--accent-neon);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.avatar-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.avatar-placeholder {
  color: #000;
  font-size: 24px;
  font-weight: 700;
  font-family: var(--font-mono);
}

.user-info {
  flex: 1;
  overflow: hidden;
}

.username {
  font-size: 16px;
  font-weight: 600;
  margin: 0 0 4px 0;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.email {
  font-size: 12px;
  color: var(--text-secondary);
  margin: 0;
  font-family: var(--font-mono);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* Settings Group */
.settings-group {
  flex: 1;
}

.group-title {
  font-size: 12px;
  color: var(--text-dim);
  margin: 0 0 12px 4px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.setting-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: var(--bg-surface);
  border-bottom: 1px solid var(--border-subtle);
  height: 48px;
  box-sizing: border-box;
}

.setting-item:first-of-type {
  border-top-left-radius: 12px;
  border-top-right-radius: 12px;
}

.setting-item:last-of-type {
  border-bottom-left-radius: 12px;
  border-bottom-right-radius: 12px;
  border-bottom: none;
}

.setting-item.clickable {
  cursor: pointer;
  transition: background-color 0.2s;
}

.setting-item.clickable:hover {
  background: var(--bg-panel);
}

.setting-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.icon-box {
  color: var(--text-secondary);
  display: flex;
  align-items: center;
}

.label {
  font-size: 14px;
  color: var(--text-primary);
}

.value-tag {
  font-size: 12px;
  color: var(--text-secondary);
  background: var(--bg-app);
  padding: 2px 8px;
  border-radius: 4px;
}

.arrow {
  color: var(--text-dim);
}

/* Theme Switcher */
.theme-switcher {
  display: flex;
  background: var(--bg-app);
  padding: 2px;
  border-radius: 6px;
  border: 1px solid var(--border-subtle);
}

.theme-btn {
  width: 28px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  background: transparent;
  color: var(--text-secondary);
  cursor: pointer;
  border-radius: 4px;
  transition: all 0.2s;
}

.theme-btn:hover {
  color: var(--text-primary);
}

.theme-btn.active {
  background: var(--bg-surface);
  color: var(--accent-neon);
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

/* Server Config */
.server-config {
  background: var(--bg-surface);
  border-radius: 12px;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 10px;
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
  gap: 6px;
  padding: 8px 16px;
  background: var(--accent-neon);
  color: #000;
  border: none;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: opacity 0.2s;
}

.save-btn:hover {
  opacity: 0.85;
}

/* Logout Button */
.action-area {
  margin-top: 24px;
  display: flex;
  justify-content: center;
}

.logout-btn-text {
  display: flex;
  align-items: center;
  gap: 8px;
  background: transparent;
  border: none;
  color: var(--danger);
  font-size: 14px;
  cursor: pointer;
  padding: 8px 16px;
  border-radius: 8px;
  transition: background-color 0.2s;
}

.logout-btn-text:hover {
  background: rgba(255, 59, 48, 0.1);
}
</style>
