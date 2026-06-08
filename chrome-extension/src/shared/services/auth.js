import { cache } from '@/shared/utils/cache.js'
import { AUTH_PASSWORD_AES_KEY } from '@/extension/protocol/auth-protocol.js'
import { backendClient } from '@/extension/runtime/backend-client.js'
import CryptoJS from 'crypto-js'

export const AUTH_EXPIRED_EVENT = 'auth-expired'
export const AUTHORIZATION_KEY = 'Authorization'
export const USER_INFO_KEY = 'userInfo'
export const TOKEN_REFRESH_THRESHOLD_MS = 24 * 60 * 60 * 1000 // 24 hours before expiry

// 统一清理本地认证信息
function clearAuthStorage(reason = 'unknown') {
  console.warn(`[FastFlow] 清除登录状态，原因: ${reason}`)
  cache.remove(AUTHORIZATION_KEY)
  cache.remove(USER_INFO_KEY)
}

// 通知登录过期（供 UI 做跳转）
function notifyAuthExpired() {
  window.dispatchEvent(new CustomEvent(AUTH_EXPIRED_EVENT))
}

function buildApiError(result, fallbackMessage) {
  const error = new Error(result?.message || fallbackMessage)
  error.code = result?.code
  error.fieldErrors = result?.data?.fieldErrors || {}
  return error
}

// AES 加密函数
function encryptPassword(password) {
  const key = CryptoJS.enc.Utf8.parse(AUTH_PASSWORD_AES_KEY)
  const srcs = CryptoJS.enc.Utf8.parse(password)
  const encrypted = CryptoJS.AES.encrypt(srcs, key, {
    mode: CryptoJS.mode.ECB,
    padding: CryptoJS.pad.Pkcs7
  })
  return encrypted.toString()
}

export const authService = {
  async login(email, password) {
    try {
      // 对密码进行加密
      const encryptedPassword = encryptPassword(password)

      const response = await backendClient.request({
        service: 'api',
        path: '/fastflow/api/v1/auth/login',
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: {
          email: email, 
          password: encryptedPassword 
        }
      })

      const result = response.data

      if (!response.ok || !result || result.code !== 200) {
        throw buildApiError(result, '登录失败，请检查账号密码')
      }
      
      // 登录成功，处理返回数据
      // 后端返回结构: { code: 200, data: { token: '...', userInfo: { ... } }, message: 'success' }
      const { token, userInfo } = result.data
      
      // 存储到 chrome.storage.local（由 cache.js 统一入口兜底）
      await cache.set(AUTHORIZATION_KEY, token)
      await cache.set(USER_INFO_KEY, userInfo)
      
      return userInfo
    } catch (error) {
      console.error('[FastFlow] Login error:', error)
      throw error
    }
  },

  async refreshToken() {
    const token = await cache.get(AUTHORIZATION_KEY)
    if (!token) {
      throw new Error('No token to refresh')
    }

    try {
      const response = await backendClient.request({
        service: 'api',
        path: '/fastflow/api/v1/auth/refresh',
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': token
        }
      })

      const result = response.data

      if (!response.ok || !result || result.code !== 200) {
        throw new Error(result?.message || 'Token refresh failed')
      }

      const { token: newToken, userInfo } = result.data
      await cache.set(AUTHORIZATION_KEY, newToken)
      await cache.set(USER_INFO_KEY, userInfo)

      return userInfo
    } catch (error) {
      console.error('[FastFlow] Token refresh error:', error)
      throw error
    }
  },

  async checkLogin() {
    const token = await cache.get(AUTHORIZATION_KEY)
    if (!token) {
      const err = new Error('Missing token')
      err.status = 401
      console.warn('[FastFlow] 登录状态已过期或未登录，已退出登录并清理本地缓存')
      clearAuthStorage('token_missing')
      notifyAuthExpired()
      throw err
    }

    const response = await backendClient.request({
      service: 'api',
      path: '/fastflow/api/v1/auth/checkLogin',
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': token
      }
    })

    const result = response.data || null

    // 网络错误（status=0）或服务端不可达：不清理 token，保留登录状态
    if (response.status === 0) {
      const err = new Error('网络不可达，无法校验登录状态')
      err.status = 0
      err.isNetworkError = true
      console.warn('[FastFlow] 网络不可达，保留本地登录状态')
      throw err
    }

    // 认证失败（401/403）：清理 token
    if (response.status === 401 || response.status === 403) {
      const err = new Error((result && result.message) || '登录状态已过期')
      err.status = response.status
      console.warn('[FastFlow] 登录状态已过期或未登录，已退出登录并清理本地缓存')
      clearAuthStorage('auth_failed_401_403')
      notifyAuthExpired()
      throw err
    }

    // 其他错误（500 等）：不清理 token
    if (!response.ok || (result && result.code !== 200)) {
      const err = new Error((result && result.message) || '校验登录状态失败')
      err.status = response.status
      console.warn('[FastFlow] 校验登录状态失败，保留本地登录状态')
      throw err
    }

    return result ? result.data : null
  },

  async register(data) {
    try {
      const encryptedPassword = encryptPassword(data.password)
      const response = await backendClient.request({
        service: 'api',
        path: '/fastflow/api/v1/auth/register',
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: {
          username: data.username,
          email: data.email,
          password: encryptedPassword,
          inviteCode: data.inviteCode
        }
      })
      const result = response.data
      if (!response.ok || !result || result.code !== 200) {
        throw buildApiError(result, '注册失败')
      }
      return result.data
    } catch (error) {
      console.error('[FastFlow] Register error:', error)
      throw error
    }
  },

  logout() {
    // 清除本地存储的 Token 和用户信息
    clearAuthStorage('user_logout')
  },

  async getCurrentUser() {
    return await cache.get(USER_INFO_KEY)
  },
  
  async getToken() {
    return await cache.get(AUTHORIZATION_KEY)
  },

  async shouldRefreshToken() {
    const token = await cache.get(AUTHORIZATION_KEY)
    if (!token) return false

    try {
      const payload = JSON.parse(atob(token.split('.')[1]))
      const expireTime = payload.expire_time || (payload.exp * 1000)
      const timeUntilExpiry = expireTime - Date.now()
      return timeUntilExpiry < TOKEN_REFRESH_THRESHOLD_MS && timeUntilExpiry > 0
    } catch {
      return false
    }
  },

  getAuthExpiredEventName() {
    return AUTH_EXPIRED_EVENT
  }
}
